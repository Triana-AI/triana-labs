"""Provider-neutral release-evaluation contracts."""

from agentagon.evals.adapters import (
    TraceAdapter,
    TraceAdapterRegistry,
    TraceAdapterResult,
    default_trace_adapter_registry,
)
from agentagon.evals.comparator import compare_release_run
from agentagon.evals.bundle_compiler import compile_release_run
from agentagon.evals.identity import (
    AgentVersionInputs,
    build_material_change,
    resolve_agent_version,
)
from agentagon.evals.evaluators import EvaluatorAdapter
from agentagon.evals.manifest import create_release_run

from agentagon.evals.models import (
    AgentVersion,
    CaseTrialKey,
    ComparisonStatus,
    DiffRow,
    EvidenceReference,
    ExecutionGap,
    ExecutionGapKind,
    ExecutionStatus,
    ExecutorKind,
    MaterialChange,
    MeasurementDefinition,
    MeasurementDirection,
    MeasurementMaturity,
    MeasurementResult,
    MeasurementResultStatus,
    MeasurementValueType,
    PairOutcome,
    ReleaseDiff,
    ReleaseRun,
    ReleaseRunKind,
    ReleaseSide,
    ResetPolicy,
    SideOutcome,
)
from agentagon.evals.output import write_release_artifacts
from agentagon.evals.trace_bundle import (
    load_trace_bundles,
    load_trace_bundles_with_gaps,
    parse_trace_bundle,
)

__all__ = [
    "AgentVersion",
    "AgentVersionInputs",
    "CaseTrialKey",
    "ComparisonStatus",
    "DiffRow",
    "EvidenceReference",
    "EvaluatorAdapter",
    "ExecutionGap",
    "ExecutionGapKind",
    "ExecutionStatus",
    "ExecutorKind",
    "MaterialChange",
    "MeasurementDefinition",
    "MeasurementDirection",
    "MeasurementMaturity",
    "MeasurementResult",
    "MeasurementResultStatus",
    "MeasurementValueType",
    "PairOutcome",
    "ReleaseDiff",
    "ReleaseRun",
    "ReleaseRunKind",
    "ReleaseSide",
    "ResetPolicy",
    "SideOutcome",
    "TraceAdapter",
    "TraceAdapterRegistry",
    "TraceAdapterResult",
    "build_material_change",
    "compare_release_run",
    "compile_release_run",
    "create_release_run",
    "default_trace_adapter_registry",
    "resolve_agent_version",
    "load_trace_bundles",
    "load_trace_bundles_with_gaps",
    "parse_trace_bundle",
    "write_release_artifacts",
]
