"""Proposer + executor for the behavioral-evals pipeline.

Runnable-but-gated: on today's non-enriched HR AI traces, STATIC measurements and any
EVAL measurement the proposer can ground in trace text (typically GOAL_CORRECTNESS)
execute for real; TOOL_CALL_RELIABILITY, PERFORMANCE_UNDER_LOAD, and FAULT_TOLERANCE come
back as COVERAGE_GAP because ``contract.has_enriched_traces()`` is False. Once enriched
traces (tool I/O + sub-agent spans + timestamps) land, the same code path populates all
six dimensions — nothing here special-cases "not ready yet". agent_looping (under
PERFORMANCE_UNDER_LOAD) is the one exception that already executes for real on
non-enriched traces: it reads the raw tool-call sequence directly via ``event_signals``,
not a state field, so it needs no timestamps or tool results.
"""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
from typing import Any

from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle
from agentagon.exploration_v1.llm import CachedLiteLLMModel, StructuredModel
from agentagon.measurement_promotion.population import PopulationClassifier, compile_population_classifier
from agentagon.measurement_promotion.state_signal import build_state_schema_profile, compute_state_measurement

from .contracts import (
    BehavioralEvalsInput,
    CoverageGap,
    CoverageMap,
    Dimension,
    Measurement,
    MeasurementKind,
    MeasurementResult,
    StaticAgentContext,
    ValueType,
    build_coverage_map,
)
from .event_signals import (
    EVENT_SIGNAL_FORMULAS,
    EVENT_SIGNAL_STATE_FIELD,
    compute_event_signal_measurement,
    event_availability_profile,
)
from .prompts import (
    EXECUTOR_JUDGE_SYSTEM,
    EXECUTOR_JUDGE_VERSION,
    PINNED_JUDGE_MODEL_ID,
    PROPOSER_SYSTEM,
    PROPOSER_VERSION,
    parse_judge_results,
    parse_proposals,
    reconcile_static_measurements,
)


def propose_measurements(
    model: StructuredModel, contract: BehavioralEvalsInput
) -> tuple[list[Measurement], CoverageMap, list[dict[str, str]]]:
    """Ask the pinned proposer model for measurements across all five dimensions.

    Returns (measurements, coverage_map, rejections). Raises ValueError if the
    model's response leaves a dimension neither populated nor gapped — see
    ``build_coverage_map``.
    """
    payload = _proposer_payload(contract)
    raw = model.complete_json(
        stage="behavioral-evals-proposals",
        prompt_version=PROPOSER_VERSION,
        system=PROPOSER_SYSTEM,
        payload=payload,
    )
    measurements, gaps, shape_rejections = parse_proposals(raw)
    measurements, schema_rejections = reconcile_static_measurements(
        measurements, contract.state_schema_profile
    )
    rejections = shape_rejections + schema_rejections
    gaps, gap_rejections = _drop_gaps_for_populated_dimensions(measurements, gaps)
    rejections = rejections + gap_rejections
    gaps = _backfill_emptied_dimensions(measurements, gaps, schema_rejections)
    coverage_map = build_coverage_map(measurements, gaps)
    return measurements, coverage_map, rejections


def _drop_gaps_for_populated_dimensions(
    measurements: list[Measurement], gaps: list[CoverageGap]
) -> tuple[list[CoverageGap], list[dict[str, str]]]:
    """A dimension like PERFORMANCE_UNDER_LOAD now covers several independent
    sub-concerns (e.g. agent_looping vs. latency-under-load) — the proposer is
    explicitly told it may populate one sub-concern while naming a gap for another.
    build_coverage_map's one-populated-or-one-gap-per-dimension invariant predates that
    split and would raise on this legitimate case, so a gap whose dimension the model
    also populated is dropped here (the populated measurement already proves the
    dimension isn't a hole) rather than crashing the whole proposal."""
    populated_dimensions = {measurement.dimension for measurement in measurements}
    kept: list[CoverageGap] = []
    dropped: list[dict[str, str]] = []
    for gap in gaps:
        if gap.dimension in populated_dimensions:
            dropped.append(
                {"id": f"coverage_gap:{gap.dimension.value}", "reason": "DIMENSION_ALREADY_POPULATED"}
            )
            continue
        kept.append(gap)
    return kept, dropped


def _backfill_emptied_dimensions(
    measurements: list[Measurement], gaps: list[CoverageGap], schema_rejections: list[dict[str, str]]
) -> list[CoverageGap]:
    """If reconcile_static_measurements dropped every measurement a dimension had, that
    dimension now has neither a measurement nor a gap — synthesize one rather than
    letting build_coverage_map raise for a hole the model didn't originally leave."""
    if not schema_rejections:
        return gaps
    covered = {measurement.dimension for measurement in measurements}
    gapped = {gap.dimension for gap in gaps}
    missing = set(Dimension) - covered - gapped
    return gaps + [
        CoverageGap(
            dimension=dimension,
            needs="a state field grounded in the discovered schema",
            reason="every measurement proposed for this dimension referenced a state field "
            "that does not match the schema inspector's discovered fields",
        )
        for dimension in missing
    ]


def _proposer_payload(contract: BehavioralEvalsInput) -> dict[str, Any]:
    return {
        "agent_profile": contract.profile,
        "populations": [
            {key: row.get(key) for key in ("population_id", "label", "definition", "kind")}
            for row in contract.populations
        ],
        "behavior_clusters": contract.behavior_clusters,
        "state_schema_profile": _compact_state_schema(contract.state_schema_profile),
        "static_context": {
            "system_prompt": contract.static_context.system_prompt,
            "rubric": contract.static_context.rubric,
            "tool_schemas": list(contract.static_context.tool_schemas),
        },
        "has_enriched_traces": contract.has_enriched_traces(),
        "event_signal_state_field": EVENT_SIGNAL_STATE_FIELD,
        "available_event_signal_formulas": sorted(EVENT_SIGNAL_FORMULAS),
        "event_signal_availability": event_availability_profile(contract.trace_bundles),
    }


def _compact_state_schema(state_schema_profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "numeric_fields": [
            {"path": row["path"], "n": row["n"], "min": row["min"], "max": row["max"], "mean": row["mean"]}
            for row in state_schema_profile.get("numeric_fields", [])
        ],
        "categorical_fields": [
            {"path": row["path"], "value_set": row["value_set"]}
            for row in state_schema_profile.get("categorical_fields", [])
        ],
        "boolean_fields": [
            {"path": row["path"]} for row in state_schema_profile.get("boolean_fields", [])
        ],
    }


def build_input_contract(
    *,
    exploration: dict[str, Any],
    behavior_map: dict[str, Any],
    bundles: tuple[NormalizedTraceBundle, ...],
    static_context: StaticAgentContext,
) -> BehavioralEvalsInput:
    """Assemble a BehavioralEvalsInput from exploration_v1 + measurement_discovery_v2 output.

    Reuses the same generic state-schema inspector goal_observables already relies on
    (agentagon.measurement_promotion.state_signal) so STATIC measurements are grounded
    in fields code actually discovered, not fields the model invented.
    """
    return BehavioralEvalsInput(
        profile=exploration["agent_profile"],
        populations=exploration["populations"],
        behavior_clusters=behavior_map,
        state_schema_profile=build_state_schema_profile(bundles),
        static_context=static_context,
        trace_bundles=bundles,
    )


def load_static_context(root: Path | None = None) -> StaticAgentContext:
    """Read the HR AI system prompt / rubric procedure / tool schemas snapshot if it exists.

    Looks under experiments/hr_ai_seed/static_context/ for hr_ai_system_prompt.txt,
    hr_ai_rubric.txt, and hr_ai_tool_schemas.json — captured verbatim from the live
    hr_ai agent source (src/prompts/evaluation.py:STABLE_INSTRUCTIONS, the skill
    markdown files + ats.py, and the 19 LangChain tool schemas via args_schema; see
    SOURCE_MANIFEST.json alongside them for exact source paths + hashes). If absent,
    returns a sparse StaticAgentContext — the proposer then has no instruction/rubric/
    tool-schema evidence to ground TOOL_CALL_RELIABILITY or quality-judge measurements
    on, and those stay coverage gaps rather than being guessed at.
    """
    base = (root or Path(__file__).resolve().parents[2]) / "experiments/hr_ai_seed/static_context"
    system_prompt_path = base / "hr_ai_system_prompt.txt"
    rubric_path = base / "hr_ai_rubric.txt"
    tool_schemas_path = base / "hr_ai_tool_schemas.json"
    system_prompt = (
        system_prompt_path.read_text(encoding="utf-8") if system_prompt_path.is_file() else None
    )
    rubric = rubric_path.read_text(encoding="utf-8") if rubric_path.is_file() else None
    tool_schemas: tuple[dict[str, Any], ...] = ()
    if tool_schemas_path.is_file():
        raw = json.loads(tool_schemas_path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            tool_schemas = tuple(row for row in raw if isinstance(row, dict))
    return StaticAgentContext(system_prompt=system_prompt, rubric=rubric, tool_schemas=tool_schemas)


def build_bedrock_model(
    cache_dir: Path,
    *,
    model_id: str = PINNED_JUDGE_MODEL_ID,
    aws_region_name: str = "ap-south-1",
    aws_profile: str = "akarsh-deepprobe",
    timeout: int = 45,
) -> CachedLiteLLMModel:
    """Construct the pinned Bedrock proposer/judge model, clearing stale AWS_* env first
    (a leftover access key/session token silences the intended AWS_PROFILE)."""
    for stale in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        os.environ.pop(stale, None)
    os.environ["AWS_PROFILE"] = aws_profile
    return CachedLiteLLMModel(
        model_id, cache_dir, provider="bedrock", aws_region_name=aws_region_name, timeout=timeout
    )


# --- executor ----------------------------------------------------------------------


def execute_measurements(
    measurements: list[Measurement],
    trace_bundles: tuple[NormalizedTraceBundle, ...],
    model: StructuredModel | None,
    *,
    populations: list[dict[str, Any]] = (),
    semantic_workers: int = 2,
    judge_batch_size: int = 15,
) -> list[MeasurementResult]:
    """Compute every measurement's value over trace_bundles.

    STATIC measurements never call ``model`` (they reuse
    ``measurement_promotion.state_signal.compute_state_measurement``, or, for the pinned
    event-derived formulas like AGENT_LOOPING_RATE, ``event_signals.
    compute_event_signal_measurement`` — either way no LLM). EVAL measurements call
    ``model`` with the frozen rubric. ``model`` may be ``None`` only if every measurement
    is STATIC.

    Every measurement is first scoped to its population (``measurement.population_id``);
    traces outside that scope are counted in the result's ``not_applicable``, never in
    ``n`` and never lumped into a vague "unknown". Of the traces left in scope, any the
    executor still could not produce a value for (missing field, judge abstained) are
    counted in ``abstained`` — the only place a genuine "couldn't tell" count lives.
    """
    classifier_cache: dict[str, PopulationClassifier] = {}
    populations_by_id = {str(row["population_id"]): row for row in populations}
    results: list[MeasurementResult] = []
    total = len(trace_bundles)
    for measurement in measurements:
        scoped = _scope_to_population(measurement, trace_bundles, populations_by_id, classifier_cache)
        not_applicable = total - len(scoped)
        if measurement.kind is MeasurementKind.STATIC:
            results.append(_execute_static(measurement, scoped, not_applicable=not_applicable))
        else:
            if model is None:
                raise ValueError(f"measurement {measurement.id} is EVAL but no model was supplied")
            results.append(
                _execute_eval(
                    measurement,
                    scoped,
                    model,
                    semantic_workers=semantic_workers,
                    batch_size=judge_batch_size,
                    not_applicable=not_applicable,
                )
            )
    return results


def _scope_to_population(
    measurement: Measurement,
    trace_bundles: tuple[NormalizedTraceBundle, ...],
    populations_by_id: dict[str, dict[str, Any]],
    classifier_cache: dict[str, PopulationClassifier],
) -> tuple[NormalizedTraceBundle, ...]:
    if measurement.population_id is None:
        return trace_bundles
    population = populations_by_id.get(measurement.population_id)
    if population is None:
        # An unresolvable population reference behaves like GLOBAL rather than silently
        # dropping every trace — the measurement still runs, just unscoped.
        return trace_bundles
    classifier = classifier_cache.get(measurement.population_id)
    if classifier is None:
        classifier = compile_population_classifier(population)
        classifier_cache[measurement.population_id] = classifier
    return tuple(
        bundle for bundle in trace_bundles if classifier.classify(_classifier_text(bundle)) == "IN"
    )


def _classifier_text(bundle: NormalizedTraceBundle) -> str:
    parts = [
        event.content if isinstance(event.content, str) else json.dumps(event.content, default=str)
        for event in bundle.events
        if event.kind is EventKind.USER
    ]
    return " ".join(parts)[:4000]


def _execute_static(
    measurement: Measurement, bundles: tuple[NormalizedTraceBundle, ...], *, not_applicable: int = 0
) -> MeasurementResult:
    formula_ref = measurement.executor.formula_ref or ""
    if formula_ref in EVENT_SIGNAL_FORMULAS:
        computed = compute_event_signal_measurement(formula_ref, bundles)
    else:
        spec = {
            "state_field": measurement.state_field,
            "value_type": "NUMBER" if measurement.value_type is ValueType.NUMERIC else "CATEGORY",
            "categories": list(measurement.executor.label_set),
        }
        computed = compute_state_measurement(spec, bundles)
    n = int(computed["evaluable"])
    # state_signal's own "unknown" count is trace-based and exact (a NUMERIC field can
    # resolve to several values per trace, so len(bundles) - n is not reliable there);
    # the event-signal path has no such field, one value per bundle always, so it falls
    # back to the exact len(bundles) - n. Either way this becomes our honestly-named
    # "abstained" — an in-scope trace the executor still could not produce a value for.
    abstained = int(computed.get("unknown", len(bundles) - n))
    evidence_ids = tuple(computed["evidence_ids"])
    if computed["value_type"] == "NUMBER":
        return MeasurementResult(
            measurement_id=measurement.id,
            dimension=measurement.dimension,
            kind=measurement.kind,
            value_type=measurement.value_type,
            n=n,
            numeric_summary=computed["numeric_summary"],
            evidence_ids=evidence_ids,
            not_applicable=not_applicable,
            abstained=abstained,
        )
    distribution = dict(computed["distribution"])
    rate = None
    if measurement.value_type is ValueType.PERCENT and n:
        rate = distribution.get("true", 0) / n
    return MeasurementResult(
        measurement_id=measurement.id,
        dimension=measurement.dimension,
        kind=measurement.kind,
        value_type=measurement.value_type,
        n=n,
        distribution=distribution,
        rate=rate,
        evidence_ids=evidence_ids,
        not_applicable=not_applicable,
        abstained=abstained,
    )


def _execute_eval(
    measurement: Measurement,
    bundles: tuple[NormalizedTraceBundle, ...],
    model: StructuredModel,
    *,
    semantic_workers: int,
    batch_size: int,
    not_applicable: int = 0,
) -> MeasurementResult:
    if not bundles:
        return MeasurementResult(
            measurement_id=measurement.id,
            dimension=measurement.dimension,
            kind=measurement.kind,
            value_type=measurement.value_type,
            n=0,
            distribution={},
            not_applicable=not_applicable,
        )
    units = [{"evidence_id": bundle.trace_id, "compact_evidence": _compact_trace_evidence(bundle)} for bundle in bundles]
    batches = [units[index : index + batch_size] for index in range(0, len(units), max(1, batch_size))]

    def judge(batch: list[dict[str, str]]) -> dict[str, str]:
        payload = {
            "rubric": measurement.executor.rubric,
            "label_set": list(measurement.executor.label_set),
            "traces": batch,
        }
        try:
            response = model.complete_json(
                stage=f"behavioral-evals-execute-{measurement.id}",
                prompt_version=measurement.executor.prompt_version or EXECUTOR_JUDGE_VERSION,
                system=EXECUTOR_JUDGE_SYSTEM,
                payload=payload,
            )
        except (json.JSONDecodeError, RuntimeError):
            # A malformed/failed model response excludes this batch's traces from the
            # denominator; it must never crash the whole executor or invent a value.
            return {}
        requested = {str(row["evidence_id"]) for row in batch}
        return parse_judge_results(response, measurement.executor.label_set, requested)

    values: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
        for partial in pool.map(judge, batches):
            values.update(partial)

    counts = Counter(values.values())
    n = len(values)
    distribution = dict(sorted((label.lower(), count) for label, count in counts.items()))
    rate = None
    if measurement.value_type is ValueType.PERCENT and n and distribution:
        leading_label = max(distribution.items(), key=lambda item: item[1])[0]
        rate = distribution[leading_label] / n
    return MeasurementResult(
        measurement_id=measurement.id,
        dimension=measurement.dimension,
        kind=measurement.kind,
        value_type=measurement.value_type,
        n=n,
        distribution=distribution,
        rate=rate,
        evidence_ids=tuple(sorted(values))[:10],
        not_applicable=not_applicable,
        abstained=len(bundles) - n,
    )


def _compact_trace_evidence(bundle: NormalizedTraceBundle) -> str:
    """Deliberately independent of measurement_promotion.semantic_runtime's
    compact_trace_evidence — that module imports goal_observables (deprecated),
    and this package should not pick up that coupling just to format trace text."""
    user_lines: list[str] = []
    agent_lines: list[str] = []
    tools: list[str] = []
    for event in bundle.events:
        content = event.content if isinstance(event.content, str) else json.dumps(event.content, sort_keys=True, default=str)
        if event.kind is EventKind.USER:
            user_lines.append(content[:500])
        elif event.kind is EventKind.AGENT:
            agent_lines.append(content[:800])
        elif event.kind is EventKind.TOOL:
            tools.append(f"{event.name}: {content[:300]}")
    compact = "\n".join(
        [
            "USER: " + " | ".join(user_lines[:4]),
            "AGENT: " + " | ".join(agent_lines[-3:]),
            "TOOLS/ACTIONS: " + " | ".join(tools[:20]),
            "STATE AFTER: " + json.dumps(bundle.state_after_ref, sort_keys=True, default=str)[:1800],
            f"EXECUTION: {bundle.execution.status.value}",
            "TRACE BOUNDARY: complete normalized trace evidence for this imported run",
        ]
    )
    return compact[:6000]


# --- full run ------------------------------------------------------------------------


def run_behavioral_evals(contract: BehavioralEvalsInput, model: StructuredModel) -> dict[str, Any]:
    """propose_measurements() -> execute_measurements() -> assembled result dict.

    Runs end to end on whatever traces the contract carries. Dimensions that need
    enriched traces (see BehavioralEvalsInput.requires_enriched_traces) come back
    as COVERAGE_GAP rather than erroring when has_enriched_traces() is False —
    the caller does not need to branch on trace readiness.
    """
    measurements, coverage_map, rejections = propose_measurements(model, contract)
    results = execute_measurements(
        measurements, contract.trace_bundles, model, populations=contract.populations
    )
    return {
        "schema_version": "behavioral-evals-result-v0.1",
        "agent_profile": contract.profile,
        "trace_count": len(contract.trace_bundles),
        "has_enriched_traces": contract.has_enriched_traces(),
        "measurements": [measurement.to_dict() for measurement in measurements],
        "results": {result.measurement_id: result.to_dict() for result in results},
        "coverage_map": coverage_map.to_dict(),
        "rejections": rejections,
    }
