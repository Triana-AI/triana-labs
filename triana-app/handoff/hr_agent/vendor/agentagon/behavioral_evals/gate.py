"""Compile discovered measurements into the existing release gate.

A discovered Measurement needs to run, unmodified, on a baseline trace set and a
candidate trace set and report the delta — the same paired_diff/paired_case_diff
machinery already used for hand-authored measurements
(agentagon/measurement_promotion/paired_gate.py). This module is the adapter: it
compiles CATEGORICAL/PERCENT measurements (STATIC and EVAL) into
FrozenMeasurementDefinition + NATIVE_SIGNAL/PINNED_SEMANTIC_JUDGE executors, the
same frozen-artifact shape paired_gate already understands, so nothing downstream
of compilation needs to know a measurement came from behavioral_evals.

NUMERIC STATIC measurements (mean/median/stdev) have no NATIVE_SIGNAL equivalent —
that engine only classifies a trace into one of a closed label set, it does not
aggregate continuous numbers. Those are diffed directly via
``numeric_paired_diff``, reusing ``compute_state_measurement`` on both trace sets
rather than forcing an awkward fit into the label-classification engine.
"""

from __future__ import annotations

from typing import Any, Iterable

from agentagon.evals.trace_bundle import NormalizedTraceBundle
from agentagon.exploration_v1.llm import StructuredModel
from agentagon.measurement_promotion.bundle import BUNDLE_SCHEMA_VERSION, bundle_hash, validate_measurement_bundle
from agentagon.measurement_promotion.compiler import compile_measurement
from agentagon.measurement_promotion.paired_gate import paired_diff
from agentagon.measurement_promotion.population import PopulationClassifier, compile_population_classifier
from agentagon.measurement_promotion.state_signal import compute_state_measurement

from .contracts import Measurement, MeasurementKind, ValueType
from .event_signals import EVENT_SIGNAL_FORMULAS, compute_event_signal_measurement
from .prompts import EXECUTOR_JUDGE_SYSTEM, EXECUTOR_JUDGE_VERSION

GLOBAL_CLASSIFIER = PopulationClassifier(
    population_id="GLOBAL",
    population_label="All observed traces",
    include_terms=(),
    exclude_terms=(),
    minimum_matches=0,
    unknown_on_empty=False,
)


class NotGateCompatible(ValueError):
    """A measurement cannot be compiled into paired_gate's label-classification engine."""


def build_native_signal_program(measurement: Measurement) -> dict[str, Any]:
    """A map_to_label program that reads measurement.state_field and returns the
    matching uppercased label. Boolean fields (label_set == ("TRUE","FALSE"), the
    state-schema inspector's convention) compare against Python bool True/False;
    every other label compares as a case-insensitive string, matching how
    build_state_schema_profile's discovered categorical value_set is used elsewhere.
    """
    if measurement.executor.formula_ref in EVENT_SIGNAL_FORMULAS:
        raise NotGateCompatible(
            f"{measurement.id}: event-signal formula {measurement.executor.formula_ref!r} reads the raw "
            "event/tool-call sequence directly and has no NATIVE_SIGNAL field-path equivalent"
        )
    labels = [label.upper() for label in measurement.executor.label_set]
    if not labels:
        raise NotGateCompatible(f"{measurement.id}: STATIC measurement has no label set to compile")
    cases = [{"values": _match_values(label), "label": label} for label in labels]
    return {
        "op": "map_to_label",
        "labels": labels,
        "default": labels[-1],
        "cases": cases,
        "value": {"op": "field", "path": measurement.state_field},
    }


def _match_values(label: str) -> list[Any]:
    if label in ("TRUE", "FALSE"):
        return [label == "TRUE"]
    return [label]


def _compiler_spec(measurement: Measurement) -> dict[str, Any]:
    population_ids = [measurement.population_id or "GLOBAL"]
    if measurement.kind is MeasurementKind.STATIC:
        if measurement.value_type is ValueType.NUMERIC:
            raise NotGateCompatible(
                f"{measurement.id}: NUMERIC STATIC measurements are not NATIVE_SIGNAL-compatible; "
                "use numeric_paired_diff instead"
            )
        return {
            "value_type": "CATEGORY",
            "categories": [label.upper() for label in measurement.executor.label_set],
            "population_ids": population_ids,
            "observable_definition": measurement.definition,
            "executor": "NATIVE_SIGNAL",
            "executor_parameters": {"state_field": measurement.state_field, "formula_ref": measurement.executor.formula_ref},
            "proposal_id": measurement.id,
            "title": measurement.title,
            "required_evidence": ["OBSERVED_STATE"],
            "slot_id": measurement.dimension.value,
            "variant_id": measurement.id,
        }
    return {
        "value_type": "CATEGORY",
        "categories": [label.upper() for label in measurement.executor.label_set],
        "population_ids": population_ids,
        "observable_definition": measurement.executor.rubric,
        "executor": "PINNED_SEMANTIC_JUDGE",
        "executor_parameters": {"prompt_version": measurement.executor.prompt_version},
        "proposal_id": measurement.id,
        "title": measurement.title,
        "required_evidence": ["TRACE_TEXT"],
        "slot_id": measurement.dimension.value,
        "variant_id": measurement.id,
    }


def compile_definitions(
    measurements: list[Measurement], populations: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[Measurement]]:
    """Split measurements into (gate-compatible compiled definitions, excluded).

    ``excluded`` is everything not compiled: NUMERIC STATIC measurements (route
    through ``numeric_paired_diff`` instead) and any measurement whose
    population_id falls outside the supplied catalog (skipped, not crashed).
    Definitions are FrozenMeasurementDefinition.to_dict() plus, for STATIC rows,
    an embedded native_signal_program."""
    populations_by_id = {str(row["population_id"]): row for row in populations}
    classifiers = _classifiers_for(measurements, populations)
    definitions: list[dict[str, Any]] = []
    excluded: list[Measurement] = []
    for measurement in measurements:
        population_id = measurement.population_id or "GLOBAL"
        if population_id != "GLOBAL" and population_id not in populations_by_id:
            # Proposer referenced a population outside the supplied catalog; skip rather
            # than crash compile_measurement's unknown-population check.
            excluded.append(measurement)
            continue
        if measurement.executor.formula_ref in EVENT_SIGNAL_FORMULAS:
            # Event-signal STATIC measurements (e.g. agent_looping) read the raw event/
            # tool-call sequence directly; NATIVE_SIGNAL only resolves field paths, so
            # there is no program to compile. Excluded here, same as a NUMERIC STATIC
            # measurement, rather than reaching build_native_signal_program's guard below.
            excluded.append(measurement)
            continue
        try:
            spec = _compiler_spec(measurement)
        except NotGateCompatible:
            excluded.append(measurement)
            continue
        definition = compile_measurement(
            spec,
            author_kind="AUTO_DISCOVERED",
            population_catalog=populations,
            supporting_examples=[],
            evaluator_version=(
                "deterministic-v1" if measurement.kind is MeasurementKind.STATIC else EXECUTOR_JUDGE_VERSION
            ),
            population_classifier=classifiers[population_id].to_dict(),
        ).to_dict()
        definition["proposal_id"] = measurement.id
        if measurement.kind is MeasurementKind.STATIC:
            definition["executor"] = "NATIVE_SIGNAL"
            definition["native_signal_program"] = build_native_signal_program(measurement)
        definitions.append(definition)
    return definitions, excluded


def _classifiers_for(
    measurements: list[Measurement], populations: list[dict[str, Any]]
) -> dict[str, PopulationClassifier]:
    populations_by_id = {str(row["population_id"]): row for row in populations}
    classifiers = {"GLOBAL": GLOBAL_CLASSIFIER}
    for measurement in measurements:
        population_id = measurement.population_id
        if population_id and population_id not in classifiers:
            population = populations_by_id.get(population_id)
            if population is not None:
                classifiers[population_id] = compile_population_classifier(population)
            else:
                classifiers[population_id] = GLOBAL_CLASSIFIER
    return classifiers


def build_bundle(
    measurements: list[Measurement],
    populations: list[dict[str, Any]],
    *,
    model_id: str = "behavioral-evals",
) -> tuple[dict[str, Any], list[Measurement]]:
    """Assemble a measurement-bundle-v0.1 bundle paired_gate.paired_diff can execute.

    Returns (bundle, excluded_numeric_measurements). ``baseline_labels`` entries are
    empty — these measurements were never discovery-time-executed against a fixed
    corpus, and paired_diff/paired_case_diff re-run each side fresh regardless.
    """
    definitions, excluded = compile_definitions(measurements, populations)
    if not definitions:
        raise ValueError("no gate-compatible measurements to bundle")
    classifiers = _classifiers_for(measurements, populations)
    population_ids = {population_id for row in definitions for population_id in row["population_ids"]}
    bundle = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "source_hash": "behavioral-evals",
        "source_result_hash": "behavioral-evals",
        "authority": "PROPOSED_OPINION",
        "proposal_ids": [row["proposal_id"] for row in definitions],
        "definitions": definitions,
        "populations": {
            population_id: row
            for population_id, row in {str(pop["population_id"]): pop for pop in populations}.items()
            if population_id in population_ids
        },
        "population_classifiers": {
            population_id: classifiers[population_id].to_dict() for population_id in sorted(population_ids)
        },
        "evaluator": {
            "executor": "PINNED_SEMANTIC_JUDGE",
            "evaluator_version": EXECUTOR_JUDGE_VERSION,
            "model": model_id,
            "system_prompt": EXECUTOR_JUDGE_SYSTEM,
            "system_prompt_hash": __import__("hashlib").sha256(EXECUTOR_JUDGE_SYSTEM.encode("utf-8")).hexdigest(),
            "result_contract": {
                "required_fields": ["evidence_id", "value", "reason"],
                "unknown_label": "ABSTAIN",
                "quote_policy": "NONE",
            },
        },
        "baseline_labels": {row["proposal_id"]: [] for row in definitions},
        "execution_boundary": {
            "ready": "STRUCTURED_LABEL_AGGREGATION",
            "pending": "RAW_TRACE_TO_STRUCTURED_LABEL_EXECUTION",
            "discovery_allowed": False,
        },
    }
    bundle = bundle | {"bundle_hash": bundle_hash(bundle)}
    validate_measurement_bundle(bundle)
    return bundle, excluded


def numeric_paired_diff(
    measurement: Measurement,
    baseline_traces: Iterable[NormalizedTraceBundle],
    candidate_traces: Iterable[NormalizedTraceBundle],
) -> dict[str, Any]:
    """Before/after delta for a NUMERIC STATIC measurement, bypassing NATIVE_SIGNAL."""
    if measurement.value_type is not ValueType.NUMERIC or measurement.kind is not MeasurementKind.STATIC:
        raise NotGateCompatible(f"{measurement.id} is not a NUMERIC STATIC measurement")
    spec = {"state_field": measurement.state_field, "value_type": "NUMBER", "categories": []}
    baseline = compute_state_measurement(spec, tuple(baseline_traces))
    candidate = compute_state_measurement(spec, tuple(candidate_traces))
    base_mean = (baseline["numeric_summary"] or {}).get("mean")
    cand_mean = (candidate["numeric_summary"] or {}).get("mean")
    delta_mean = (cand_mean - base_mean) if base_mean is not None and cand_mean is not None else None
    return {
        "proposal_id": measurement.id,
        "name": measurement.title,
        "executor": "NUMERIC_STATE_AGGREGATE",
        "baseline": {"numeric_summary": baseline["numeric_summary"], "n": baseline["evaluable"]},
        "candidate": {"numeric_summary": candidate["numeric_summary"], "n": candidate["evaluable"]},
        "delta_mean": delta_mean,
    }


def event_signal_paired_diff(
    measurement: Measurement,
    baseline_traces: Iterable[NormalizedTraceBundle],
    candidate_traces: Iterable[NormalizedTraceBundle],
) -> dict[str, Any]:
    """Before/after delta for a CATEGORICAL/PERCENT event-signal STATIC measurement
    (e.g. agent_looping_rate), bypassing NATIVE_SIGNAL the same way numeric_paired_diff
    bypasses it for NUMERIC STATIC measurements. Returns a row shaped like paired_gate's
    own CATEGORY rows (before _rename_unknown_to_not_applicable), so it slots into
    run_release_gate's regular measurements list -- the diff renderer downstream needs
    no event-signal-specific branch."""
    if measurement.executor.formula_ref not in EVENT_SIGNAL_FORMULAS:
        raise NotGateCompatible(f"{measurement.id} is not an event-signal measurement")
    baseline = compute_event_signal_measurement(measurement.executor.formula_ref, tuple(baseline_traces))
    candidate = compute_event_signal_measurement(measurement.executor.formula_ref, tuple(candidate_traces))

    def _side(computed: dict[str, Any]) -> dict[str, Any]:
        n = computed["evaluable"]
        side: dict[str, Any] = {"evaluable": n, "distribution": computed["distribution"]}
        if measurement.value_type is ValueType.PERCENT:
            side["rate"] = {"true": (computed["distribution"].get("true", 0) / n) if n else None}
        return side

    return {
        "proposal_id": measurement.id,
        "finding": "CHANGED" if baseline["distribution"] != candidate["distribution"] else "UNCHANGED",
        "baseline": _side(baseline),
        "candidate": _side(candidate),
    }


def _rename_unknown_to_not_applicable(row: dict[str, Any]) -> dict[str, Any]:
    """paired_gate.paired_diff (shared infra used well beyond behavioral_evals) still
    reports its excluded-trace count under the key "unknown". At this package's own
    output boundary that name is misleading — the traces it counts were excluded because
    they fell outside the measurement's compiled population scope or the executor
    genuinely could not classify them, never because behavioral_evals itself doesn't know
    what happened. Rename it here rather than in the shared engine, whose "unknown" key is
    depended on elsewhere (goal_observables, slate_v3, release_runtime)."""
    renamed = dict(row)
    for side in ("baseline", "candidate"):
        if side in renamed and isinstance(renamed[side], dict) and "unknown" in renamed[side]:
            side_copy = dict(renamed[side])
            side_copy["not_applicable"] = side_copy.pop("unknown")
            renamed[side] = side_copy
    return renamed


def run_release_gate(
    measurements: list[Measurement],
    populations: list[dict[str, Any]],
    baseline_traces: Iterable[NormalizedTraceBundle],
    candidate_traces: Iterable[NormalizedTraceBundle],
    model: StructuredModel | None,
    *,
    model_id: str = "behavioral-evals",
    semantic_workers: int = 4,
) -> dict[str, Any]:
    """End-to-end: compile measurements, run paired_diff for CATEGORY/PERCENT
    measurements, run numeric_paired_diff for each excluded NUMERIC measurement.
    Any other excluded measurement (unresolvable population) is reported by id in
    ``skipped_measurement_ids``, not silently dropped."""
    if not measurements:
        return {"measurements": [], "numeric_measurements": [], "skipped_measurement_ids": []}
    baseline_list = list(baseline_traces)
    candidate_list = list(candidate_traces)
    definitions, excluded = compile_definitions(measurements, populations)
    diff_measurements: list[dict[str, Any]] = []
    bundle_hash_value: str | None = None
    if definitions:
        bundle, _ = build_bundle(measurements, populations, model_id=model_id)
        bundle_hash_value = bundle["bundle_hash"]
        diff = paired_diff(bundle, baseline_list, candidate_list, model, semantic_workers=semantic_workers)
        diff_measurements = [_rename_unknown_to_not_applicable(row) for row in diff["measurements"]]
    numeric_measurements = [
        measurement
        for measurement in excluded
        if measurement.value_type is ValueType.NUMERIC and measurement.kind is MeasurementKind.STATIC
    ]
    numeric = [numeric_paired_diff(measurement, baseline_list, candidate_list) for measurement in numeric_measurements]
    event_signal_measurements = [
        measurement for measurement in excluded if measurement.executor.formula_ref in EVENT_SIGNAL_FORMULAS
    ]
    diff_measurements.extend(
        event_signal_paired_diff(measurement, baseline_list, candidate_list)
        for measurement in event_signal_measurements
    )
    routed = numeric_measurements + event_signal_measurements
    skipped_ids = [measurement.id for measurement in excluded if measurement not in routed]
    return {
        "bundle_hash": bundle_hash_value,
        "measurements": diff_measurements,
        "numeric_measurements": numeric,
        "skipped_measurement_ids": skipped_ids,
    }
