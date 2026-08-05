"""Generic state-field discovery and deterministic aggregation.

The semantic pipeline only ever asked a model to classify *text* into
Boolean/categorical labels. But a trace's captured state
(``state_after_ref`` and any structured observable nested inside it, e.g. a
list of decision/evaluation records) frequently carries numeric score fields
and low-cardinality enum fields that a developer would want to compare across
releases. Nothing in the proposer could see those fields, so they were never
proposed.

This module adds two deterministic, agent-agnostic pieces:

1. :func:`build_state_schema_profile` walks the captured state across the whole
   corpus and enumerates every observable leaf path *by inferred type*
   (NUMERIC / CATEGORICAL / BOOLEAN), with no knowledge of any specific field
   name. High-cardinality free-text and identifier fields are deliberately
   dropped — they are not release-comparable dimensions.

2. :func:`compute_state_measurement` computes a proposed state-field
   measurement without any model call: a numeric summary (n / mean / median /
   stdev / min / max) for a NUMBER measurement, or a label distribution for a
   categorical / boolean measurement, bucketing any value outside a declared
   allowed set as ``INVALID``.

Field paths use the same dotted, ``[]``-for-list grammar the NATIVE_SIGNAL
resolver understands, so a discovered path is directly computable through
:func:`agentagon.measurement_promotion.native_signal` with no translation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
import statistics
from typing import Any

from agentagon.evals.trace_bundle import NormalizedTraceBundle

from .native_signal import ABSENT, _bundle_context, _resolve_path

STATE_SCHEMA_VERSION = "state-schema-profile-v0.1"
STATE_EXECUTOR = "NATIVE_STATE_AGGREGATE"

DEFAULT_MAX_CATEGORICAL_CARDINALITY = 12
DEFAULT_STATE_ROOT = "state_after"
_INVALID_LABEL = "INVALID"


def build_state_schema_profile(
    bundles: tuple[NormalizedTraceBundle, ...],
    *,
    root: str = DEFAULT_STATE_ROOT,
    max_categorical_cardinality: int = DEFAULT_MAX_CATEGORICAL_CARDINALITY,
    max_sample_values: int = 8,
) -> dict[str, Any]:
    """Enumerate observable state leaf fields across the corpus by inferred type.

    Classification is purely structural: a leaf path is NUMERIC when every
    observed value at that path is a real number (never a bool), BOOLEAN when
    every value is a bool, CATEGORICAL when every value is a string and the
    distinct count is within ``max_categorical_cardinality``. Any path whose
    values are mixed-type, or a high-cardinality string (free text, ids), is
    excluded and only surfaced in the ``excluded`` summary. No field name is
    ever special-cased.
    """
    values_by_path: defaultdict[str, list[Any]] = defaultdict(list)
    for bundle in bundles:
        _walk(_state_root_value(bundle, root), root, values_by_path)

    numeric: list[dict[str, Any]] = []
    categorical: list[dict[str, Any]] = []
    boolean: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for path, values in sorted(values_by_path.items()):
        inferred = _classify_path(path, values, max_categorical_cardinality, max_sample_values)
        bucket = {
            "NUMERIC": numeric,
            "CATEGORICAL": categorical,
            "BOOLEAN": boolean,
            "EXCLUDED": excluded,
        }[inferred["type"]]
        bucket.append(inferred)

    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "root": root,
        "max_categorical_cardinality": max_categorical_cardinality,
        "field_count": len(numeric) + len(categorical) + len(boolean),
        "numeric_fields": numeric,
        "categorical_fields": categorical,
        "boolean_fields": boolean,
        "excluded_fields": excluded,
    }


def _state_root_value(bundle: NormalizedTraceBundle, root: str) -> Any:
    if root == "state_after":
        return bundle.state_after_ref
    if root == "state_before":
        return bundle.state_before_ref
    raise ValueError(f"unsupported state root: {root!r}")


def _walk(value: Any, path: str, out: defaultdict[str, list[Any]]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _walk(child, f"{path}.{key}", out)
    elif isinstance(value, list):
        for item in value:
            _walk(item, f"{path}[]", out)
    elif value is not None:
        out[path].append(value)


def _classify_path(
    path: str, values: list[Any], max_categorical_cardinality: int, max_sample_values: int
) -> dict[str, Any]:
    n = len(values)
    # bool is a subclass of int, so it must be checked before the numeric test.
    if values and all(isinstance(v, bool) for v in values):
        counts = Counter("TRUE" if v else "FALSE" for v in values)
        return {
            "path": path,
            "type": "BOOLEAN",
            "n": n,
            "value_set": ["TRUE", "FALSE"],
            "observed_counts": dict(counts),
        }
    if values and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values):
        floats = [float(v) for v in values]
        return {
            "path": path,
            "type": "NUMERIC",
            "n": n,
            "min": min(floats),
            "max": max(floats),
            "mean": round(statistics.fmean(floats), 4),
            "sample_values": _sample(values, max_sample_values),
        }
    if values and all(isinstance(v, str) for v in values):
        distinct = sorted(set(values))
        if len(distinct) <= max_categorical_cardinality:
            return {
                "path": path,
                "type": "CATEGORICAL",
                "n": n,
                "cardinality": len(distinct),
                "value_set": distinct,
            }
        return {
            "path": path,
            "type": "EXCLUDED",
            "n": n,
            "reason": "HIGH_CARDINALITY_STRING",
            "cardinality": len(distinct),
        }
    return {"path": path, "type": "EXCLUDED", "n": n, "reason": "MIXED_OR_UNSUPPORTED_TYPE"}


def _sample(values: list[Any], limit: int) -> list[Any]:
    seen: list[Any] = []
    for value in values:
        if value not in seen:
            seen.append(value)
        if len(seen) >= limit:
            break
    return seen


def compute_state_measurement(
    spec: dict[str, Any], bundles: tuple[NormalizedTraceBundle, ...]
) -> dict[str, Any]:
    """Deterministically evaluate a state-field measurement over a bundle set.

    ``spec`` must carry ``state_field`` (a discovered path), ``value_type``
    (``NUMBER`` for a numeric aggregate, ``BOOLEAN``/``CATEGORY`` for a label
    distribution), and, for label distributions, an allowed ``categories`` set.
    Bundles are assumed pre-filtered to the measurement's population.
    """
    path = str(spec["state_field"])
    value_type = str(spec["value_type"]).upper()
    per_bundle = _collect_field_values(bundles, path)
    eligible = len(per_bundle)
    if value_type == "NUMBER":
        return _numeric_result(per_bundle, eligible)
    allowed = [str(label).upper() for label in spec.get("categories", [])]
    return _distribution_result(per_bundle, eligible, allowed)


def _collect_field_values(
    bundles: tuple[NormalizedTraceBundle, ...], path: str
) -> list[tuple[NormalizedTraceBundle, list[Any]]]:
    per_bundle: list[tuple[NormalizedTraceBundle, list[Any]]] = []
    for bundle in bundles:
        resolved = _resolve_path(path, _bundle_context(bundle))
        if resolved is ABSENT:
            per_bundle.append((bundle, []))
        elif isinstance(resolved, list):
            per_bundle.append((bundle, [item for item in resolved if item is not ABSENT]))
        else:
            per_bundle.append((bundle, [resolved]))
    return per_bundle


def _numeric_result(
    per_bundle: list[tuple[NormalizedTraceBundle, list[Any]]], eligible: int
) -> dict[str, Any]:
    sample: list[float] = []
    contributing: list[NormalizedTraceBundle] = []
    for bundle, values in per_bundle:
        numeric = [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
        if numeric:
            contributing.append(bundle)
            sample.extend(numeric)
    n = len(sample)
    summary = {
        "n": n,
        "contributing_traces": len(contributing),
        "mean": round(statistics.fmean(sample), 4) if sample else None,
        "median": round(statistics.median(sample), 4) if sample else None,
        "stdev": round(statistics.stdev(sample), 4) if n >= 2 else 0.0,
        "min": min(sample) if sample else None,
        "max": max(sample) if sample else None,
    }
    return {
        "value_type": "NUMBER",
        "numeric_summary": summary,
        "distribution": {},
        "eligible": eligible,
        "evaluable": n,
        "unknown": eligible - len(contributing),
        "evidence_ids": [bundle.trace_id for bundle in contributing][:30],
    }


def _distribution_result(
    per_bundle: list[tuple[NormalizedTraceBundle, list[Any]]], eligible: int, allowed: list[str]
) -> dict[str, Any]:
    allowed_set = set(allowed)
    counts: Counter[str] = Counter()
    contributing: list[NormalizedTraceBundle] = []
    for bundle, values in per_bundle:
        matched = False
        for value in values:
            label = ("TRUE" if value else "FALSE") if isinstance(value, bool) else str(value).upper()
            counts[label if label in allowed_set else _INVALID_LABEL] += 1
            matched = True
        if matched:
            contributing.append(bundle)
    distribution = dict(sorted((label.lower(), count) for label, count in counts.items()))
    evaluable = sum(counts.values())
    return {
        "value_type": "CATEGORY",
        "numeric_summary": None,
        "distribution": distribution,
        "eligible": eligible,
        "evaluable": evaluable,
        "unknown": eligible - len(contributing),
        "evidence_ids": [bundle.trace_id for bundle in contributing][:30],
    }
