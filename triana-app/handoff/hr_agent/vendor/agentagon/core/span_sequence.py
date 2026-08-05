"""Helpers for ordered span sequences."""

from __future__ import annotations

from collections.abc import Iterable

from agentagon.core.span import Span, SpanType


def span_sort_key(span: Span) -> tuple[bool, float, str]:
    return (
        span.started_at is None,
        span.started_at or 0.0,
        span.span_id,
    )


def serial_adjacent_tool_pairs(spans: Iterable[Span]) -> tuple[tuple[Span, Span], ...]:
    pairs: list[tuple[Span, Span]] = []
    previous_tool: Span | None = None
    for span in sorted(spans, key=span_sort_key):
        if span.span_type is not SpanType.TOOL:
            previous_tool = None
            continue
        if previous_tool is not None and _is_serial_adjacent_pair(previous_tool, span):
            pairs.append((previous_tool, span))
        previous_tool = span
    return tuple(pairs)


def _is_serial_adjacent_pair(previous: Span, current: Span) -> bool:
    if previous.ended_at is None or current.started_at is None:
        return False
    return current.started_at >= previous.ended_at


__all__ = ["serial_adjacent_tool_pairs", "span_sort_key"]
