"""Signal-related core types."""

from agentagon.core.types.signals.analysis import Analysis
from agentagon.core.types.signals.base import (
    Signal,
    SignalEntities,
    SignalObservation,
    SignalSummaries,
    SignalValue,
)
from agentagon.core.types.signals.bool import BoolStats, BoolValue
from agentagon.core.types.signals.category import (
    CategoryStats,
    CategoryValue,
)
from agentagon.core.types.signals.context import (
    CohortSignalCallback,
    CohortSignalContext,
    ParentSignalCallback,
    SignalContext,
    SignalRunResult,
    SessionSignalCallback,
    SessionSignalContext,
    SpanSignalCallback,
)
from agentagon.core.types.signals.decimal import DecimalStats, DecimalValue
from agentagon.core.types.signals.string import StringStats, StringValue


__all__ = [
    "Analysis",
    "BoolStats",
    "BoolValue",
    "CategoryStats",
    "CategoryValue",
    "CohortSignalCallback",
    "CohortSignalContext",
    "DecimalStats",
    "DecimalValue",
    "ParentSignalCallback",
    "Signal",
    "SignalContext",
    "SignalEntities",
    "SignalObservation",
    "SignalRunResult",
    "SignalSummaries",
    "SignalValue",
    "SessionSignalCallback",
    "SessionSignalContext",
    "SpanSignalCallback",
    "StringStats",
    "StringValue",
]
