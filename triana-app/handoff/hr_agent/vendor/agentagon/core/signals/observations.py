"""Helpers for working with signal observations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from agentagon.core.types.signals import Signal, SignalValue


SignalOrValue = Signal | SignalValue


def signal_observations(signal_or_value: SignalOrValue) -> tuple[Any, ...]:
    value = _signal_value(signal_or_value)
    observations = getattr(value, "observations", ())
    return tuple(observations)


def observation_key(observation: object) -> tuple[str | None, str | None]:
    return (
        getattr(observation, "trace_id", None),
        getattr(observation, "span_id", None),
    )


def sorted_observations(observations: Iterable[object]) -> list[object]:
    return sorted(
        observations,
        key=lambda observation: (
            str(getattr(observation, "trace_id", "") or ""),
            str(getattr(observation, "span_id", "") or ""),
        ),
    )


def observation_numeric_value(observation: object) -> float | None:
    value = getattr(observation, "value", None)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def observation_numeric_values(observations: tuple[object, ...]) -> tuple[float, ...]:
    return tuple(
        numeric_value
        for observation in observations
        for numeric_value in (observation_numeric_value(observation),)
        if numeric_value is not None
    )


def numeric_observations_by_key(
    value: SignalValue | None,
) -> dict[tuple[str | None, str | None], float]:
    if value is None:
        return {}
    return {
        observation_key(observation): numeric_value
        for observation in signal_observations(value)
        for numeric_value in (observation_numeric_value(observation),)
        if numeric_value is not None
    }


def numeric_signal_total(value: SignalValue | None) -> float:
    if value is None:
        return 0.0
    return sum(observation_numeric_values(signal_observations(value)))


def sort_numeric_observations_desc(
    observations: tuple[object, ...],
) -> tuple[object, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda observation: (
                -float(observation_numeric_value(observation) or 0),
                str(getattr(observation, "trace_id", "") or ""),
                str(getattr(observation, "span_id", "") or ""),
            ),
        )
    )


def numeric_observations_at_or_above(
    observations: tuple[object, ...],
    threshold: float,
) -> tuple[object, ...]:
    return tuple(
        observation
        for observation in sort_numeric_observations_desc(observations)
        if (observation_numeric_value(observation) or 0.0) >= threshold
    )


def _signal_value(signal_or_value: SignalOrValue) -> SignalValue:
    if isinstance(signal_or_value, Signal):
        return signal_or_value.value
    return signal_or_value


__all__ = [
    "SignalOrValue",
    "numeric_observations_at_or_above",
    "numeric_observations_by_key",
    "numeric_signal_total",
    "observation_key",
    "observation_numeric_value",
    "observation_numeric_values",
    "signal_observations",
    "sort_numeric_observations_desc",
    "sorted_observations",
]
