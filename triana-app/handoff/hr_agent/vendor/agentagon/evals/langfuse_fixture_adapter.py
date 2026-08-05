"""Offline adapter for a directory of committed Langfuse trace fixtures.

Mirrors the interface of ``experiments/hr_ai_seed/adapter_v1.py::HrAiSimulatedTrafficAdapter``
(a ``.load()`` returning an object with a ``.bundles`` tuple) so runners can consume a fixture
corpus the same way they consume the HR AI export, but sourced from real Langfuse traces via
``agentagon.evals.langfuse_source.observations_to_bundle`` instead. Pure/offline: no network
calls, no credentials.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from agentagon.evals.langfuse_source import observations_to_bundle
from agentagon.evals.trace_bundle import NormalizedTraceBundle


@dataclass(frozen=True, slots=True)
class LangfuseFixtureCorpus:
    bundles: tuple[NormalizedTraceBundle, ...]


class LangfuseFixtureAdapter:
    """Loads every ``*.json`` raw-trace fixture in ``directory`` into normalized bundles."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def load(self) -> LangfuseFixtureCorpus:
        bundles = [
            observations_to_bundle(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(self._directory.glob("*.json"))
        ]
        bundles.sort(key=lambda bundle: bundle.trace_id)
        return LangfuseFixtureCorpus(bundles=tuple(bundles))


__all__ = ["LangfuseFixtureAdapter", "LangfuseFixtureCorpus"]
