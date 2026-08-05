"""String signal values."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.types.signals.base import (
    SignalEntities,
    SignalObservation,
    SignalValue,
)


@dataclass(frozen=True, slots=True)
class StringStats:
    count: int
    unique_count: int
    distribution: dict[str, int]


@dataclass(slots=True)
class StringValue(SignalValue):
    observations: tuple[SignalObservation[str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self.observations = tuple(self.observations)

    @classmethod
    def from_value(
        cls,
        value: str,
        *,
        session_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        span_ids: tuple[str, ...] = (),
        entities: SignalEntities | None = None,
    ) -> StringValue:
        return cls(
            observations=(
                SignalObservation(
                    value=str(value),
                    session_id=session_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    span_ids=span_ids,
                    entities=entities or {},
                ),
            )
        )

    @classmethod
    def aggregate(cls, values: tuple[StringValue, ...]) -> StringValue:
        return cls(
            observations=tuple(
                observation
                for value in values
                for observation in value.observations
            )
        )

    def get_stats(self) -> StringStats:
        distribution: dict[str, int] = {}
        for observation in self.observations:
            distribution[observation.value] = distribution.get(observation.value, 0) + 1
        return StringStats(
            count=sum(distribution.values()),
            unique_count=len(distribution),
            distribution=distribution,
        )


__all__ = ["StringStats", "StringValue"]
