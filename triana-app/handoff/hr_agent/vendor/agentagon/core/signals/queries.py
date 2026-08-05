"""Helpers for querying computed signal state."""

from __future__ import annotations

from typing import Any

from agentagon.core.signals.observations import SignalOrValue, signal_observations
from agentagon.core.span import Span
from agentagon.core.trace import Trace
from agentagon.core.types.signals import Signal, SignalSummaries, SignalValue


def get_span_signal(span: Span, signal_name: str) -> Signal | None:
    return next(
        (signal for signal in span.analysis.signals if signal.name == signal_name),
        None,
    )


def get_trace_signal(trace: Trace, signal_name: str) -> Signal | None:
    return next(
        (signal for signal in trace.analysis.signals if signal.name == signal_name),
        None,
    )


def get_summary_signal(
    summary_map: SignalSummaries,
    entity_id: str,
    signal_name: str,
) -> SignalValue | None:
    return summary_map.get(entity_id, {}).get(signal_name)


def signal_scalar_value(signal_or_value: SignalOrValue) -> Any:
    observations = signal_observations(signal_or_value)
    if len(observations) != 1:
        return None
    return getattr(observations[0], "value", None)


def signal_numeric_value(signal_or_value: SignalOrValue | None) -> float | None:
    if signal_or_value is None:
        return None
    value = signal_scalar_value(signal_or_value)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def span_signal_numeric_value(span: Span, signal_name: str) -> float | None:
    return signal_numeric_value(get_span_signal(span, signal_name))


def trace_signal_numeric_value(trace: Trace, signal_name: str) -> float | None:
    return signal_numeric_value(get_trace_signal(trace, signal_name))


def signal_string_value(signal_or_value: SignalOrValue | None) -> str | None:
    if signal_or_value is None:
        return None
    value = signal_scalar_value(signal_or_value)
    return str(value) if value is not None else None


def span_signal_string_value(span: Span, signal_name: str) -> str | None:
    return signal_string_value(get_span_signal(span, signal_name))


def trace_span_signal_numeric_sum(trace: Trace, signal_name: str) -> float | None:
    values = tuple(
        signal_numeric_value(signal)
        for span in trace.spans
        for signal in (get_span_signal(span, signal_name),)
        if signal is not None
    )
    numeric_values = tuple(value for value in values if value is not None)
    return sum(numeric_values) if numeric_values else None


__all__ = [
    "get_span_signal",
    "get_summary_signal",
    "get_trace_signal",
    "signal_numeric_value",
    "signal_scalar_value",
    "signal_string_value",
    "span_signal_numeric_value",
    "span_signal_string_value",
    "trace_signal_numeric_value",
    "trace_span_signal_numeric_sum",
]
