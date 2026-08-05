"""Portable deterministic measurements over normalized trace bundles."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from agentagon.core.types.json import canonical_json
from agentagon.evals.evaluators import EvaluationInput, Evaluator
from agentagon.evals.models import (
    EvidenceReference,
    ExecutorKind,
    MeasurementDefinition,
    MeasurementDirection,
    MeasurementMaturity,
    MeasurementResult,
    MeasurementResultStatus,
    MeasurementValueType,
)
from agentagon.evals.trace_bundle import (
    EventKind,
    NormalizedTraceBundle,
    parse_trace_bundle,
)


MetricFunction = Callable[[NormalizedTraceBundle], bool | float | str]


def default_mechanical_measurements() -> tuple[MeasurementDefinition, ...]:
    return (
        _definition("user_turn_count", "User turn count", MeasurementValueType.NUMBER),
        _definition(
            "agent_turn_count", "Agent turn count", MeasurementValueType.NUMBER
        ),
        _definition("tool_call_count", "Tool call count", MeasurementValueType.NUMBER),
        _definition(
            "tool_error_present",
            "Tool error present",
            MeasurementValueType.BOOLEAN,
            MeasurementDirection.LOWER_BETTER,
        ),
        _definition(
            "repeated_identical_tool_call",
            "Repeated identical tool call",
            MeasurementValueType.BOOLEAN,
            MeasurementDirection.LOWER_BETTER,
        ),
        _definition(
            "workflow_step_count", "Workflow step count", MeasurementValueType.NUMBER
        ),
        _definition("artifact_count", "Artifact count", MeasurementValueType.NUMBER),
        _definition(
            "runtime_seconds",
            "Runtime seconds",
            MeasurementValueType.NUMBER,
            MeasurementDirection.LOWER_BETTER,
        ),
        _definition(
            "estimated_cost",
            "Estimated cost",
            MeasurementValueType.NUMBER,
            MeasurementDirection.LOWER_BETTER,
        ),
    )


def native_trace_evaluator() -> Evaluator:
    functions: dict[str, MetricFunction] = {
        "user_turn_count": lambda trace: float(_event_count(trace, EventKind.USER)),
        "agent_turn_count": lambda trace: float(_event_count(trace, EventKind.AGENT)),
        "tool_call_count": lambda trace: float(_event_count(trace, EventKind.TOOL)),
        "tool_error_present": _tool_error_present,
        "repeated_identical_tool_call": _repeated_identical_tool_call,
        "workflow_step_count": lambda trace: float(
            _event_count(trace, EventKind.WORKFLOW)
        ),
        "artifact_count": lambda trace: float(len(trace.artifact_refs)),
        "runtime_seconds": _runtime_seconds,
        "estimated_cost": _estimated_cost,
    }

    def evaluate(
        definition: MeasurementDefinition,
        evaluation_input: EvaluationInput,
    ) -> MeasurementResult:
        function = functions.get(definition.measurement_id)
        evidence = evaluation_input.evidence
        if function is None:
            return MeasurementResult(
                definition.measurement_id,
                definition.version,
                MeasurementResultStatus.UNSUPPORTED,
                reason="No native deterministic implementation for this measurement",
                evidence=evidence,
            )
        try:
            trace = parse_trace_bundle(evaluation_input.normalized_trace)
            value = function(trace)
        except NotEvaluable as error:
            return MeasurementResult(
                definition.measurement_id,
                definition.version,
                MeasurementResultStatus.NOT_EVALUABLE,
                reason=str(error),
                evidence=evidence,
            )
        return MeasurementResult(
            definition.measurement_id,
            definition.version,
            MeasurementResultStatus.OK,
            value=value,
            eligible_count=1,
            evaluable_count=1,
            evidence=(
                *evidence,
                EvidenceReference(
                    kind="NORMALIZED_TRACE",
                    trace_id=trace.trace_id,
                    case_id=trace.case_id,
                    trial_id=trace.trial_id,
                    artifact_path=trace.source_path,
                ),
            ),
        )

    return evaluate


class NotEvaluable(RuntimeError):
    pass


def _definition(
    measurement_id: str,
    name: str,
    value_type: MeasurementValueType,
    direction: MeasurementDirection = MeasurementDirection.NEUTRAL,
) -> MeasurementDefinition:
    return MeasurementDefinition(
        measurement_id=measurement_id,
        version="native-v1",
        name=name,
        criterion=f"Calculate {name.lower()} from ordered normalized events.",
        executor=ExecutorKind.DETERMINISTIC,
        value_type=value_type,
        maturity=MeasurementMaturity.DEFAULT,
        evaluator_version="native-trace-v1",
        direction=direction,
    )


def _event_count(trace: NormalizedTraceBundle, kind: EventKind) -> int:
    return sum(event.kind is kind for event in trace.events)


def _tool_error_present(trace: NormalizedTraceBundle) -> bool:
    for event in trace.events:
        if event.kind is not EventKind.TOOL:
            continue
        status = str(event.data.get("status", "")).lower()
        if event.data.get("error") not in (None, "", False) or status in {
            "error",
            "failed",
            "failure",
            "timeout",
        }:
            return True
    return False


def _repeated_identical_tool_call(trace: NormalizedTraceBundle) -> bool:
    calls = Counter(
        (
            event.name,
            canonical_json(event.data.get("arguments")),
        )
        for event in trace.events
        if event.kind is EventKind.TOOL
        and str(event.data.get("phase", "call")).lower() not in {"result", "response"}
    )
    return any(count > 1 for count in calls.values())


def _runtime_seconds(trace: NormalizedTraceBundle) -> float:
    if trace.execution.runtime_seconds is None:
        raise NotEvaluable("execution.runtime_seconds is missing")
    return trace.execution.runtime_seconds


def _estimated_cost(trace: NormalizedTraceBundle) -> float:
    if trace.execution.estimated_cost is None:
        raise NotEvaluable("execution.estimated_cost is missing")
    return trace.execution.estimated_cost


__all__ = ["default_mechanical_measurements", "native_trace_evaluator"]
