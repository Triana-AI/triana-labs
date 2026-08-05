"""Route frozen measurements without coupling Diff V0 to one eval vendor."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from agentagon.core.types.json import JsonObject, JsonValue
from agentagon.evals.models import (
    EvidenceReference,
    ExecutorKind,
    MeasurementDefinition,
    MeasurementResult,
    MeasurementResultStatus,
)


@dataclass(frozen=True, slots=True)
class EvaluationInput:
    normalized_trace: JsonValue = None
    output: JsonValue = None
    initial_world: JsonValue = None
    final_world: JsonValue = None
    external_results: JsonObject = field(default_factory=dict)
    evidence: tuple[EvidenceReference, ...] = ()


class EvaluatorAdapter(Protocol):
    def __call__(
        self,
        definition: MeasurementDefinition,
        evaluation_input: EvaluationInput,
    ) -> MeasurementResult: ...


Evaluator = EvaluatorAdapter


class EvaluatorRegistry:
    def __init__(self) -> None:
        self._evaluators: dict[tuple[ExecutorKind, str | None], EvaluatorAdapter] = {}

    def register(
        self,
        kind: ExecutorKind,
        evaluator: EvaluatorAdapter,
        *,
        evaluator_version: str | None = None,
    ) -> None:
        key = (kind, evaluator_version)
        if key in self._evaluators:
            raise ValueError(
                f"Evaluator already registered for {kind.value}@{evaluator_version or '*'}"
            )
        self._evaluators[key] = evaluator

    def evaluate(
        self,
        definition: MeasurementDefinition,
        evaluation_input: EvaluationInput,
    ) -> MeasurementResult:
        evaluator = self._evaluators.get(
            (definition.executor, definition.evaluator_version)
        ) or self._evaluators.get((definition.executor, None))
        if evaluator is None:
            return MeasurementResult(
                measurement_id=definition.measurement_id,
                measurement_version=definition.version,
                status=MeasurementResultStatus.UNSUPPORTED,
                reason=(
                    f"No evaluator registered for {definition.executor.value}"
                    f"@{definition.evaluator_version}"
                ),
                evidence=evaluation_input.evidence,
            )
        try:
            result = evaluator(definition, evaluation_input)
        except Exception as error:  # Evaluator failures are data, not runner crashes.
            return MeasurementResult(
                measurement_id=definition.measurement_id,
                measurement_version=definition.version,
                status=MeasurementResultStatus.EXECUTION_ERROR,
                reason=f"{type(error).__name__}: {error}",
                evidence=evaluation_input.evidence,
            )
        if result.measurement_id != definition.measurement_id:
            raise ValueError("Evaluator returned a result for the wrong measurement")
        if result.measurement_version != definition.version:
            raise ValueError(
                "Evaluator returned a result for the wrong measurement version"
            )
        return result


__all__ = [
    "EvaluationInput",
    "Evaluator",
    "EvaluatorAdapter",
    "EvaluatorRegistry",
]
