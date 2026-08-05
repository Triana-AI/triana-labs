"""Behavioral-evals measurement pipeline — replaces goal_observables measurement discovery.

Flow:

    exploration_v1 (populations/facets/profile)         [PINNED MODEL + CODE]
    measurement_discovery_v2.build_behavior_evidence_map [CODE, feeds Behavior tab]
    measurement_promotion.state_signal (state schema)    [CODE]
    static_context (system prompt, rubric, tool schemas) [SUPPLIED, load_static_context()]
    trace bundles (enriched, once available)              [ADAPTER]
        v
    BehavioralEvalsInput                                  [contracts.py]
        v
    propose_measurements()  -- ONE STRONG-MODEL CALL       [pipeline.py + prompts.py]
        |  authors Measurement objects across the six fixed dimensions
        |  (GOAL_CORRECTNESS / TOOL_CALL_RELIABILITY / PERFORMANCE_UNDER_LOAD /
        |   FAULT_TOLERANCE / TRACE_OBSERVABILITY / SAFETY), data-driven count, no cap
        |  a dimension with no confident measurement becomes a typed CoverageGap
        v
    CoverageMap                                            [contracts.py]
        v
    execute_measurements()  -- STATIC: no LLM (state_signal). EVAL: pinned judge.
        |                                                  [pipeline.py]
        v
    run_behavioral_evals() -> result dict                  [pipeline.py]
        |
        +--> render_behavioral_evals_report()               [report.py, the Measurements tab]
        +--> gate.build_bundle() / gate.run_release_gate()   [gate.py, baseline vs candidate]

Runnable-but-gated: on today's non-enriched HR AI traces, run_behavioral_evals executes
STATIC measurements (including agent_looping, which reads the raw tool-call sequence
directly and needs no enriched fields) and any EVAL measurement groundable in trace text
(typically GOAL_CORRECTNESS, task_evasion, and the SAFETY measurements); TOOL_CALL_RELIABILITY,
PERFORMANCE_UNDER_LOAD's latency/cost sub-concern, and FAULT_TOLERANCE come back as
COVERAGE_GAP because BehavioralEvalsInput.has_enriched_traces() is False. The same call
populates all six once enriched traces (tool I/O + sub-agent spans + timestamps) land.

Unlike the old goal_observables/slate_v3 pipelines this replaces, there is no vague
"unknown" bucket: a measurement that cannot be confidently computed from available
evidence is dropped at discovery time by the proposer (a whole dimension with no
supporting data becomes a typed COVERAGE_GAP naming exactly what evidence is missing,
e.g. "needs tool I/O", "needs load runs" — a per-dimension gap, not a per-trace catch-all).
Per measurement, MeasurementResult still distinguishes two honestly-named exclusion
counts alongside n: ``not_applicable`` (a trace outside the measurement's scoped
population — never evidence of anything) and ``abstained`` (an in-scope trace the
executor genuinely could not produce a value for). See contracts.MeasurementResult.

Static measurements are deterministic formulas over fields the state-schema
inspector (agentagon.measurement_promotion.state_signal, reused as-is) already
discovered in captured state. Eval measurements are a frozen rubric + fixed
label set run by a pinned judge model. Both are frozen once proposed — they do
not silently change definition between releases. Both also compile into the
existing release gate (gate.py) for baseline-vs-candidate diffing, reusing
measurement_promotion.paired_gate unmodified.

The Understanding tab and Behavior/cluster tab are unaffected: they are built
from exploration_v1 and measurement_discovery_v2.build_behavior_evidence_map
respectively, neither of which this package touches. See
internal/DELETION_MANIFEST_behavioral_evals.md for what this pipeline replaces
and why.
"""

from .contracts import (
    BehavioralEvalsInput,
    CoverageGap,
    CoverageMap,
    Dimension,
    DisplayKind,
    Executor,
    Measurement,
    MeasurementKind,
    MeasurementResult,
    StaticAgentContext,
    ValueType,
    build_coverage_map,
)
from .pipeline import (
    build_bedrock_model,
    build_input_contract,
    execute_measurements,
    load_static_context,
    propose_measurements,
    run_behavioral_evals,
)
from .frozen_labels import (
    FrozenLabelModel,
    RecordingModel,
    load_frozen_labels,
    merge_frozen_labels,
    write_frozen_labels,
)
from .prompts import reconcile_static_measurements
from .report import render_behavioral_evals_diff_report, render_behavioral_evals_report

__all__ = [
    "BehavioralEvalsInput",
    "CoverageGap",
    "CoverageMap",
    "Dimension",
    "DisplayKind",
    "Executor",
    "FrozenLabelModel",
    "Measurement",
    "MeasurementKind",
    "MeasurementResult",
    "RecordingModel",
    "StaticAgentContext",
    "ValueType",
    "build_coverage_map",
    "build_bedrock_model",
    "build_input_contract",
    "execute_measurements",
    "load_frozen_labels",
    "load_static_context",
    "merge_frozen_labels",
    "propose_measurements",
    "reconcile_static_measurements",
    "render_behavioral_evals_diff_report",
    "render_behavioral_evals_report",
    "run_behavioral_evals",
    "write_frozen_labels",
]
