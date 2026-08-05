"""Category signal values."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.types.signals.base import (
    SignalEntities,
    SignalObservation,
    SignalValue,
)


@dataclass(frozen=True, slots=True)
class CategoryStats:
    count: int
    distribution: dict[str, int]


@dataclass(slots=True)
class CategoryValue(SignalValue):
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
    ) -> CategoryValue:
        return cls(
            observations=(
                SignalObservation(
                    value=value,
                    session_id=session_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    span_ids=span_ids,
                    entities=entities or {},
                ),
            )
        )

    @classmethod
    def aggregate(cls, values: tuple[CategoryValue, ...]) -> CategoryValue:
        return cls(
            observations=tuple(
                observation
                for value in values
                for observation in value.observations
            )
        )

    def get_stats(self) -> CategoryStats:
        distribution: dict[str, int] = {}
        for observation in self.observations:
            distribution[observation.value] = distribution.get(observation.value, 0) + 1
        return CategoryStats(
            count=sum(distribution.values()),
            distribution=distribution,
        )


__all__ = ["CategoryStats", "CategoryValue"]
