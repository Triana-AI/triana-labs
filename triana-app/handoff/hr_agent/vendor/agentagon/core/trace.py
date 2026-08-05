"""Core trace data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from agentagon.core.types.signals import Analysis
from agentagon.core.types.json import JsonObject
from agentagon.core.span import Span


class TraceProvider(StrEnum):
    UNKNOWN = "unknown"
    BRAINTRUST = "braintrust"

    @classmethod
    def from_value(cls, value: str | TraceProvider) -> TraceProvider:
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            return cls.UNKNOWN


@dataclass(slots=True)
class TraceUser:
    user_id: str | None = None
    email: str | None = None
    session_id: str | None = None
    message_id: str | None = None
    source: str = ""
    source_fields: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Trace:
    trace_id: str = ""
    spans: tuple[Span, ...] = ()
    provider: TraceProvider = TraceProvider.UNKNOWN
    started_at: float | None = None
    ended_at: float | None = None
    metadata: JsonObject = field(default_factory=dict)
    user: TraceUser | None = None
    analysis: Analysis = field(default_factory=Analysis)


__all__ = ["Trace", "TraceProvider", "TraceUser"]
