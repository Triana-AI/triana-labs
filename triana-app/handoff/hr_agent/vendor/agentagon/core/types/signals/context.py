"""Signal execution context and callback types."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypeAlias

from agentagon.core.types.json import JsonValue
from agentagon.core.types.signals.base import Signal, SignalSummaries

if TYPE_CHECKING:
    from agentagon.core.entities import EntityRegistry, SpanEntity
    from agentagon.core.session import Session
    from agentagon.core.span import Span
    from agentagon.judges.types import JudgeClient
    from agentagon.signals.prompt_context import SessionSignalState


@dataclass(slots=True)
class SignalContext:
    session_id: str
    trace_id: str
    span_id: str
    registry: EntityRegistry
    entity: SpanEntity
    is_root: bool = False
    initial_user_input: JsonValue = None
    judge_client: JudgeClient | None = None
    session_signal_state: SessionSignalState | None = None


@dataclass(slots=True)
class SessionSignalContext:
    session_id: str
    registry: EntityRegistry
    initial_user_input: JsonValue = None
    judge_client: JudgeClient | None = None
    session_signal_state: SessionSignalState | None = None


@dataclass(slots=True)
class CohortSignalContext:
    sessions: tuple[Session, ...]
    registry: EntityRegistry


@dataclass(slots=True)
class SignalRunResult:
    sessions: tuple[Session, ...] = ()
    cohort_signals: tuple[Signal, ...] = ()
    cohort_signal_summaries: SignalSummaries = field(default_factory=dict)


SpanSignalCallback: TypeAlias = Callable[["Span", SignalContext], tuple[Signal, ...]]
ParentSignalCallback: TypeAlias = Callable[
    ["Span", tuple["Span", ...], SignalContext],
    tuple[Signal, ...],
]
SessionSignalCallback: TypeAlias = Callable[
    ["Session", SessionSignalContext],
    tuple[Signal, ...],
]
CohortSignalCallback: TypeAlias = Callable[[CohortSignalContext], tuple[Signal, ...]]


__all__ = [
    "CohortSignalCallback",
    "CohortSignalContext",
    "ParentSignalCallback",
    "SignalContext",
    "SignalRunResult",
    "SessionSignalCallback",
    "SessionSignalContext",
    "SpanSignalCallback",
]
