"""Scrappy release gate: apply one frozen measurement bundle to two trace sets.

Given a frozen bundle and two normalized trace sets (baseline + candidate for
the SAME cases under a code/model/harness change), re-apply every measurement to
both sides and report the per-measurement delta. This is the release gate: the
measurements are frozen, so any change in the numbers is a change in the agent,
not a change in the ruler.

No verdict is emitted. Directional words (IMPROVED/REGRESSED) require confirmed
expected direction, which V0 does not have — so this reports CHANGED/UNCHANGED
plus the distributions, unknowns both sides, and evidence.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from agentagon.evals.trace_bundle import NormalizedTraceBundle
from agentagon.exploration_v1.llm import StructuredModel

from .bundle import execute_native_signal_bundle
from .semantic_runtime import execute_semantic_bundle


def _rate(distribution: dict[str, int]) -> dict[str, float]:
    total = sum(distribution.values())
    if total == 0:
        return {}
    return {label: round(count / total, 4) for label, count in distribution.items()}


def _index(results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["proposal_id"]): row for row in results}


def _execute_bundle_rows(
    bundle: dict[str, Any],
    traces: list[NormalizedTraceBundle],
    model: StructuredModel | None,
    *,
    semantic_workers: int,
) -> dict[str, dict[str, Any]]:
    """Run every definition in `bundle` against `traces`, indexed by proposal_id.

    Shared by `paired_diff` (aggregate distributions only) and
    `paired_case_diff` (needs the `per_trace_results` each row also carries).
    """
    rows: dict[str, dict[str, Any]] = {}
    native = execute_native_signal_bundle(bundle, traces)
    rows.update(_index(native["results"]))
    has_semantic = any(row.get("executor") != "NATIVE_SIGNAL" for row in bundle["definitions"])
    if has_semantic:
        if model is None:
            raise ValueError(
                "Bundle has PINNED_SEMANTIC_JUDGE measurements; a model is required"
            )
        semantic = execute_semantic_bundle(
            bundle, traces, model, semantic_workers=semantic_workers
        )
        rows.update(_index(semantic["results"]))
    return rows


def paired_diff(
    bundle: dict[str, Any],
    baseline_traces: Iterable[NormalizedTraceBundle],
    candidate_traces: Iterable[NormalizedTraceBundle],
    model: StructuredModel | None = None,
    *,
    semantic_workers: int = 4,
) -> dict[str, Any]:
    """Re-apply the frozen bundle to both sides and diff each measurement.

    `model` is required only if the bundle contains PINNED_SEMANTIC_JUDGE
    definitions; NATIVE_SIGNAL definitions run without it.
    """
    baseline_list = list(baseline_traces)
    candidate_list = list(candidate_traces)

    baseline_rows = _execute_bundle_rows(bundle, baseline_list, model, semantic_workers=semantic_workers)
    candidate_rows = _execute_bundle_rows(bundle, candidate_list, model, semantic_workers=semantic_workers)

    diffs = []
    for row in bundle["definitions"]:
        proposal_id = str(row["proposal_id"])
        base = baseline_rows.get(proposal_id, {})
        cand = candidate_rows.get(proposal_id, {})
        base_dist = base.get("distribution", {})
        cand_dist = cand.get("distribution", {})
        labels = sorted(set(base_dist) | set(cand_dist))
        base_rate = _rate(base_dist)
        cand_rate = _rate(cand_dist)
        delta = {
            label: round(cand_rate.get(label, 0.0) - base_rate.get(label, 0.0), 4)
            for label in labels
        }
        changed = any(abs(value) > 0 for value in delta.values()) or (
            base_dist != cand_dist
        )
        diffs.append(
            {
                "proposal_id": proposal_id,
                "name": row.get("name") or proposal_id,
                "executor": row.get("executor", "PINNED_SEMANTIC_JUDGE"),
                "finding": "CHANGED" if changed else "UNCHANGED",
                "baseline": {
                    "distribution": base_dist,
                    "rate": base_rate,
                    "evaluable": base.get("evaluable", 0),
                    "unknown": base.get("unknown", 0),
                },
                "candidate": {
                    "distribution": cand_dist,
                    "rate": cand_rate,
                    "evaluable": cand.get("evaluable", 0),
                    "unknown": cand.get("unknown", 0),
                },
                "delta_rate": delta,
            }
        )

    return {
        "schema_version": "release-gate-paired-diff-v0.1",
        "bundle_hash": bundle["bundle_hash"],
        "baseline_traces": len(baseline_list),
        "candidate_traces": len(candidate_list),
        "measurements": diffs,
    }


_UNKNOWN = "UNKNOWN"

CASE_TRANSITION_SAME = "SAME"
CASE_TRANSITION_CHANGED = "CHANGED"
CASE_TRANSITION_BASELINE_ONLY_EVALUABLE = "BASELINE_ONLY_EVALUABLE"
CASE_TRANSITION_CANDIDATE_ONLY_EVALUABLE = "CANDIDATE_ONLY_EVALUABLE"
CASE_TRANSITION_BOTH_UNKNOWN = "BOTH_UNKNOWN"


def _case_values(
    per_trace_results: list[dict[str, Any]], trace_to_case: dict[str, str]
) -> dict[str, str]:
    """Map case_id -> uppercased label for one side's per-trace results.

    A case absent from `per_trace_results` (semantic route: classified OUT of
    the measurement's population; native route: never happens, every trace
    gets a row) has no entry here and is treated as unknown by the caller.
    """
    values: dict[str, str] = {}
    for row in per_trace_results:
        case_id = trace_to_case.get(str(row.get("evidence_id")))
        if case_id is None:
            continue
        raw = str(row.get("value", "ABSTAIN")).upper()
        values[case_id] = _UNKNOWN if raw == "ABSTAIN" else raw
    return values


def _classify_transition(baseline_value: str, candidate_value: str) -> str:
    base_known = baseline_value != _UNKNOWN
    cand_known = candidate_value != _UNKNOWN
    if not base_known and not cand_known:
        return CASE_TRANSITION_BOTH_UNKNOWN
    if not base_known:
        return CASE_TRANSITION_CANDIDATE_ONLY_EVALUABLE
    if not cand_known:
        return CASE_TRANSITION_BASELINE_ONLY_EVALUABLE
    return CASE_TRANSITION_SAME if baseline_value == candidate_value else CASE_TRANSITION_CHANGED


def paired_case_diff(
    bundle: dict[str, Any],
    baseline_traces: Iterable[NormalizedTraceBundle],
    candidate_traces: Iterable[NormalizedTraceBundle],
    model: StructuredModel | None = None,
    *,
    semantic_workers: int = 4,
) -> dict[str, Any]:
    """Case-level pairing on top of `paired_diff`'s aggregate distributions.

    Pairs baseline and candidate traces by `case_id` (the stable key across a
    release change; the composite `trace_id` differs by trial/session, so it
    cannot be used for pairing -- verified 1:1 case_id uniqueness on the real
    run_200 vs run_200_codefix HR AI corpora, 185 and 189 completed traces
    respectively, zero duplicates either side). Cases present on only one
    side are reported explicitly via `baseline_only_case_ids` /
    `candidate_only_case_ids`, never silently dropped -- this is what makes
    the 185 vs 189 asymmetry visible instead of averaged away.

    For each measurement, every PAIRED case is classified as one of SAME,
    CHANGED, BASELINE_ONLY_EVALUABLE, CANDIDATE_ONLY_EVALUABLE, or
    BOTH_UNKNOWN (see `_classify_transition`), and every FROM->TO label pair
    is tallied into `transition_matrix`. `changed_cases` lists every CHANGED
    case's {case_id, baseline_value, candidate_value}, capped at 50;
    `changed_case_count` always reports the true total.
    """
    baseline_list = list(baseline_traces)
    candidate_list = list(candidate_traces)

    baseline_by_case = {tb.case_id: tb for tb in baseline_list}
    candidate_by_case = {tb.case_id: tb for tb in candidate_list}
    baseline_case_ids = set(baseline_by_case)
    candidate_case_ids = set(candidate_by_case)
    paired_case_ids = sorted(baseline_case_ids & candidate_case_ids)
    baseline_only_case_ids = sorted(baseline_case_ids - candidate_case_ids)
    candidate_only_case_ids = sorted(candidate_case_ids - baseline_case_ids)

    baseline_trace_to_case = {tb.trace_id: tb.case_id for tb in baseline_list}
    candidate_trace_to_case = {tb.trace_id: tb.case_id for tb in candidate_list}

    baseline_rows = _execute_bundle_rows(bundle, baseline_list, model, semantic_workers=semantic_workers)
    candidate_rows = _execute_bundle_rows(bundle, candidate_list, model, semantic_workers=semantic_workers)

    measurements = []
    for definition in bundle["definitions"]:
        proposal_id = str(definition["proposal_id"])
        base_row = baseline_rows.get(proposal_id, {})
        cand_row = candidate_rows.get(proposal_id, {})

        base_values = _case_values(base_row.get("per_trace_results", []), baseline_trace_to_case)
        cand_values = _case_values(cand_row.get("per_trace_results", []), candidate_trace_to_case)

        transition_matrix: Counter[str] = Counter()
        classification_counts: Counter[str] = Counter()
        changed_cases: list[dict[str, Any]] = []
        for case_id in paired_case_ids:
            base_value = base_values.get(case_id, _UNKNOWN)
            cand_value = cand_values.get(case_id, _UNKNOWN)
            transition_matrix[f"{base_value}->{cand_value}"] += 1
            classification = _classify_transition(base_value, cand_value)
            classification_counts[classification] += 1
            if classification == CASE_TRANSITION_CHANGED:
                changed_cases.append(
                    {
                        "case_id": case_id,
                        "baseline_value": base_value,
                        "candidate_value": cand_value,
                    }
                )

        measurements.append(
            {
                "proposal_id": proposal_id,
                "name": definition.get("name") or proposal_id,
                "executor": definition.get("executor", "PINNED_SEMANTIC_JUDGE"),
                "paired_case_count": len(paired_case_ids),
                "transition_matrix": dict(sorted(transition_matrix.items())),
                "classification_counts": dict(sorted(classification_counts.items())),
                "changed_case_count": len(changed_cases),
                "changed_cases": changed_cases[:50],
            }
        )

    return {
        "schema_version": "release-gate-paired-case-diff-v0.1",
        "bundle_hash": bundle["bundle_hash"],
        "baseline_traces": len(baseline_list),
        "candidate_traces": len(candidate_list),
        "paired_case_count": len(paired_case_ids),
        "baseline_only_case_ids": baseline_only_case_ids,
        "candidate_only_case_ids": candidate_only_case_ids,
        "measurements": measurements,
    }
