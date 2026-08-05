"""Decimal signal values."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

from agentagon.core.stats import nearest_rank_percentile
from agentagon.core.types.signals.base import (
    SignalEntities,
    SignalObservation,
    SignalValue,
)


@dataclass(frozen=True, slots=True)
class DecimalStats:
    count: int
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    p90: float | None = None
    p95: float | None = None
    unit: str | None = None


@dataclass(slots=True)
class DecimalValue(SignalValue):
    observations: tuple[SignalObservation[float], ...] = field(default_factory=tuple)
    unit: str | None = None

    def __post_init__(self) -> None:
        self.observations = tuple(self.observations)

    @classmethod
    def from_value(
        cls,
        value: float,
        *,
        unit: str | None = None,
        session_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        span_ids: tuple[str, ...] = (),
        entities: SignalEntities | None = None,
    ) -> DecimalValue:
        value = float(value)
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
            ),
            unit=unit,
        )

    @classmethod
    def aggregate(cls, values: tuple[DecimalValue, ...]) -> DecimalValue:
        observations = tuple(
            observation
            for value in values
            for observation in value.observations
        )
        unit = next((value.unit for value in values if value.unit is not None), None)
        return cls(observations=observations, unit=unit)

    def get_stats(self) -> DecimalStats:
        raw_values = sorted(observation.value for observation in self.observations)
        if not raw_values:
            return DecimalStats(count=0, unit=self.unit)
        count = len(raw_values)
        median_value = float(median(raw_values))
        return DecimalStats(
            count=count,
            unit=self.unit,
            min=raw_values[0],
            max=raw_values[-1],
            mean=sum(raw_values) / count,
            median=median_value,
            p90=nearest_rank_percentile(raw_values, 90),
            p95=nearest_rank_percentile(raw_values, 95),
        )


__all__ = ["DecimalStats", "DecimalValue"]
