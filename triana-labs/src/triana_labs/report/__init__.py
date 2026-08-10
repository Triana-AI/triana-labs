"""Canonical deterministic fact compilation for Labs report projections."""

from triana_labs.report.compiler import (
    AnalysisFact,
    CompiledAnalysis,
    RejectedEvidence,
    ReportCompilationError,
    compile_hrai_normalized_trace_v2,
    compile_preview_trace_v1,
)

__all__ = [
    "AnalysisFact",
    "CompiledAnalysis",
    "RejectedEvidence",
    "ReportCompilationError",
    "compile_hrai_normalized_trace_v2",
    "compile_preview_trace_v1",
]
