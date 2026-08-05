"""Analysis state attached to trace and span models."""

from __future__ import annotations

from dataclasses import dataclass, field

from agentagon.core.types.signals.base import Signal, SignalSummaries


@dataclass(slots=True)
class Analysis:
    signals: tuple[Signal, ...] = ()
    signal_summaries: SignalSummaries = field(default_factory=dict)


__all__ = ["Analysis"]
