"""Canonical deterministic fact compilation for Labs report projections."""

from triana_labs.report.compiler import (
    AnalysisFact,
    CompiledAnalysis,
    RejectedEvidence,
    ReportCompilationError,
    compile_hrai_normalized_trace_v2,
)

__all__ = [
    "AnalysisFact",
    "CompiledAnalysis",
    "RejectedEvidence",
    "ReportCompilationError",
    "compile_hrai_normalized_trace_v2",
]
