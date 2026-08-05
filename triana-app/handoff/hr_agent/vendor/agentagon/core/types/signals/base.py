"""Base signal value and signal models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Self, TypeAlias, TypeVar


ObservationValue = TypeVar("ObservationValue")
SignalEntities: TypeAlias = dict[str, set[str]]


@dataclass(frozen=True, slots=True)
class SignalObservation(Generic[ObservationValue]):
    value: ObservationValue
    session_id: str | None = field(default=None, compare=False)
    trace_id: str | None = None
    span_id: str | None = None
    span_ids: tuple[str, ...] = ()
    entities: SignalEntities = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "span_ids", tuple(self.span_ids))
        _validate_provenance(self.trace_id, self.span_id, self.span_ids)


@dataclass(slots=True)
class SignalValue:
    """Base type for typed signal values."""

    @classmethod
    def aggregate(cls, values: tuple[Self, ...]) -> Self:
        raise NotImplementedError(f"{cls.__name__} does not implement aggregate()")

    def get_stats(self) -> object:
        raise NotImplementedError(
            f"{type(self).__name__} does not implement get_stats()"
        )


@dataclass(slots=True)
class Signal:
    name: str
    description: str
    value: SignalValue
    signal_subject_id: str | None = None
    entities: SignalEntities = field(default_factory=dict)

SignalSummaries: TypeAlias = dict[str, dict[str, SignalValue]]


def _validate_provenance(
    trace_id: str | None,
    span_id: str | None,
    span_ids: tuple[str, ...],
) -> None:
    has_span_provenance = span_id is not None or bool(span_ids)
    if trace_id is None and has_span_provenance:
        raise ValueError("Signal provenance with span ids must include trace_id")


__all__ = [
    "Signal",
    "SignalEntities",
    "SignalObservation",
    "SignalSummaries",
    "SignalValue",
]
