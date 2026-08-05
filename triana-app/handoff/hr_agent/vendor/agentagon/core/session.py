"""Session data model and trace grouping helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from agentagon.core.span import Span
from agentagon.core.trace import Trace, TraceUser
from agentagon.core.types.json import JsonObject
from agentagon.core.types.signals import Analysis


@dataclass(slots=True)
class Session:
    session_id: str = ""
    traces: tuple[Trace, ...] = ()
    spans: tuple[Span, ...] = ()
    started_at: float | None = None
    ended_at: float | None = None
    user: TraceUser | None = None
    metadata: JsonObject = field(default_factory=dict)
    analysis: Analysis = field(default_factory=Analysis)

    def __post_init__(self) -> None:
        self.traces = tuple(self.traces)
        if not self.spans:
            self.spans = tuple(span for trace in self.traces for span in trace.spans)
        else:
            self.spans = tuple(self.spans)

def sessions_from_traces(traces: Iterable[Trace]) -> tuple[Session, ...]:
    grouped: dict[str, list[Trace]] = {}
    for trace in traces:
        grouped.setdefault(_session_id_for_trace(trace), []).append(trace)

    sessions = tuple(
        _session_from_traces(session_id, tuple(sorted(traces, key=_trace_sort_key)))
        for session_id, traces in grouped.items()
    )
    return tuple(sorted(sessions, key=_session_sort_key))


def _session_id_for_trace(trace: Trace) -> str:
    session_id = trace.user.session_id if trace.user is not None else None
    if session_id:
        return session_id
    return trace.trace_id


def _session_from_traces(session_id: str, traces: tuple[Trace, ...]) -> Session:
    spans = tuple(span for trace in traces for span in trace.spans)
    starts = [
        value
        for trace in traces
        for value in (trace.started_at,)
        if value is not None
    ]
    ends = [
        value
        for trace in traces
        for value in (trace.ended_at,)
        if value is not None
    ]
    if not starts:
        starts = [span.started_at for span in spans if span.started_at is not None]
    if not ends:
        ends = [span.ended_at for span in spans if span.ended_at is not None]
    user = next((trace.user for trace in traces if trace.user is not None), None)
    metadata: JsonObject = {
        "trace_ids": [trace.trace_id for trace in traces],
        "trace_count": len(traces),
        "span_count": len(spans),
    }
    return Session(
        session_id=session_id,
        traces=traces,
        spans=spans,
        started_at=min(starts, default=None),
        ended_at=max(ends, default=None),
        user=user,
        metadata=metadata,
    )


def _trace_sort_key(trace: Trace) -> tuple[bool, float, str]:
    return (
        trace.started_at is None,
        trace.started_at or 0.0,
        trace.trace_id,
    )


def _session_sort_key(session: Session) -> tuple[bool, float, str]:
    return (
        session.started_at is None,
        session.started_at or 0.0,
        session.session_id,
    )


__all__ = ["Session", "sessions_from_traces"]
