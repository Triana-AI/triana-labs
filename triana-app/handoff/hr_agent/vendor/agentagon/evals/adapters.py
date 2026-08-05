"""Plug-in boundaries for trace normalization and evaluator execution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from agentagon.evals.models import ExecutionGap, ResetPolicy
from agentagon.evals.trace_bundle import (
    NormalizedTraceBundle,
    load_trace_bundles_with_gaps,
)


@dataclass(frozen=True, slots=True)
class TraceAdapterResult:
    adapter_version: str
    bundles: tuple[NormalizedTraceBundle, ...]
    gaps: tuple[ExecutionGap, ...]
    source_path: str


class TraceAdapter(Protocol):
    @property
    def adapter_version(self) -> str: ...

    def load(
        self,
        path: Path,
        *,
        default_reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT,
    ) -> TraceAdapterResult: ...


class NormalizedJsonlTraceAdapter:
    adapter_version = "normalized-jsonl-v1"

    def load(
        self,
        path: Path,
        *,
        default_reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT,
    ) -> TraceAdapterResult:
        bundles, gaps = load_trace_bundles_with_gaps(
            path,
            default_reset_policy=default_reset_policy,
        )
        return TraceAdapterResult(
            adapter_version=self.adapter_version,
            bundles=bundles,
            gaps=gaps,
            source_path=str(path),
        )


class TraceAdapterRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, TraceAdapter] = {}

    def register(self, adapter: TraceAdapter) -> None:
        version = adapter.adapter_version
        if not version:
            raise ValueError("Trace adapters require a non-empty version")
        if version in self._adapters:
            raise ValueError(f"Trace adapter already registered: {version}")
        self._adapters[version] = adapter

    def get(self, adapter_version: str) -> TraceAdapter:
        try:
            return self._adapters[adapter_version]
        except KeyError as error:
            available = ", ".join(sorted(self._adapters)) or "none"
            raise ValueError(
                f"Unknown trace adapter {adapter_version!r}; available: {available}"
            ) from error

    @property
    def versions(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))


def default_trace_adapter_registry() -> TraceAdapterRegistry:
    registry = TraceAdapterRegistry()
    registry.register(NormalizedJsonlTraceAdapter())
    return registry


__all__ = [
    "NormalizedJsonlTraceAdapter",
    "TraceAdapter",
    "TraceAdapterRegistry",
    "TraceAdapterResult",
    "default_trace_adapter_registry",
]
