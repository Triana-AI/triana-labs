"""Core span data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from agentagon.core.types.signals import Analysis
from agentagon.core.types.json import JsonObject, JsonValue


class SpanType(StrEnum):
    UNKNOWN = "unknown"
    TASK = "task"
    AGENT = "agent"
    LLM = "llm"
    TOOL = "tool"
    SCORE = "score"
    AUTOMATION = "automation"
    FACET = "facet"
    CLASSIFIER = "classifier"
    FUNCTION = "function"
    EVAL = "eval"
    PREPROCESSOR = "preprocessor"

    @classmethod
    def from_value(cls, value: Any) -> SpanType:
        if isinstance(value, cls):
            return value
        if not isinstance(value, str):
            return cls.UNKNOWN
        try:
            return cls(value.strip().lower())
        except ValueError:
            return cls.UNKNOWN


@dataclass(slots=True)
class Span:
    """Provider-normalized span.

    ``started_at`` and ``ended_at`` are Unix epoch seconds, not milliseconds.
    Durations derived from them are seconds until a signal converts units.
    """

    span_id: str = ""
    trace_id: str = ""
    parent_span_ids: tuple[str, ...] = ()
    is_root: bool = False
    name: str = ""
    span_type: SpanType = SpanType.UNKNOWN
    purpose: str | None = None
    started_at: float | None = None
    ended_at: float | None = None
    input: JsonValue = None
    output: JsonValue = None
    expected: JsonValue = None
    error: JsonValue = None
    metadata: JsonObject = field(default_factory=dict)
    metrics: JsonObject = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    raw_span: JsonObject = field(default_factory=dict)
    
    # Agentagon internals
    analysis: Analysis = field(default_factory=Analysis)


__all__ = ["Span", "SpanType"]
