"""Boolean signal values."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.types.signals.base import (
    SignalEntities,
    SignalObservation,
    SignalValue,
)


@dataclass(frozen=True, slots=True)
class BoolStats:
    count: int
    true_count: int
    false_count: int
    true_probability: float | None = None


@dataclass(slots=True)
class BoolValue(SignalValue):
    observations: tuple[SignalObservation[bool], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        self.observations = tuple(self.observations)

    @classmethod
    def from_value(
        cls,
        value: bool,
        *,
        session_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        span_ids: tuple[str, ...] = (),
        entities: SignalEntities | None = None,
    ) -> BoolValue:
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
    def aggregate(cls, values: tuple[BoolValue, ...]) -> BoolValue:
        return cls(
            observations=tuple(
                observation
                for value in values
                for observation in value.observations
            )
        )

    def get_stats(self) -> BoolStats:
        values = tuple(observation.value for observation in self.observations)
        true_count = sum(1 for value in values if value)
        false_count = len(values) - true_count
        count = len(values)
        return BoolStats(
            count=count,
            true_count=true_count,
            false_count=false_count,
            true_probability=true_count / count if count else None,
        )


__all__ = ["BoolStats", "BoolValue"]
