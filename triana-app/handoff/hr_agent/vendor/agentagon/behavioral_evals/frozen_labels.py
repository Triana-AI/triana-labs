"""Offline, byte-identical reproduction for the release-gate EVAL judge path.

The gate's EVAL measurements execute through
``measurement_promotion.semantic_runtime._judge_omit_contract`` (see gate.py and
``semantic_runtime.execute_semantic_bundle``), which calls a live judge model via
``StructuredModel.complete_json(stage=f"release-gate-eval-{measurement_id}", ...)``.
A fresh clone with no cached judge calls re-judges from scratch and the EVAL numbers
drift release to release. This module lets a live run's exact labels be frozen to a
committed JSON file and replayed later with zero model calls.

Frozen shape: ``{measurement_id: {trace_id: label}}``. A trace_id absent from the
frozen set for a measurement is honestly ``ABSTAIN`` when replayed -- never a live
call, never silently dropped from the denominator (same "omit means abstain"
semantics `_judge_omit_contract` already applies to a live model's own omissions).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_STAGE_PREFIX = "release-gate-eval-"


def _measurement_id_from_stage(stage: str) -> str:
    return stage.removeprefix(_STAGE_PREFIX)


class FrozenLabelModel:
    """StructuredModel stand-in that replays frozen labels instead of calling a model.

    Only understands the release-gate EVAL stage naming
    (``release-gate-eval-<measurement_id>``, set by
    ``semantic_runtime._judge_omit_contract``). A trace_id the frozen set has no label
    for is simply left out of "results" -- the omit-contract parsing on the other end
    already turns that into an honest abstain.
    """

    model_id = "frozen-labels"

    def __init__(self, labels: dict[str, dict[str, str]]):
        self._labels = labels
        self.calls = 0
        self.cache_hits = 0  # never a real call; mirrors CachedLiteLLMModel's usage() shape

    def complete_json(
        self, *, stage: str, prompt_version: str, system: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self.calls += 1
        labels_for_measurement = self._labels.get(_measurement_id_from_stage(stage), {})
        results = []
        for trace in payload.get("traces", []):
            evidence_id = str(trace.get("evidence_id"))
            label = labels_for_measurement.get(evidence_id)
            if label is not None:
                results.append({"evidence_id": evidence_id, "value": label, "reason": "frozen-label"})
        return {"results": results}

    def usage(self) -> dict[str, int | str]:
        return {"model_id": self.model_id, "calls": self.calls, "cache_hits": 0, "input_tokens": 0, "output_tokens": 0}


class RecordingModel:
    """Wraps a live model, recording every non-abstain release-gate EVAL label it
    returns into ``self.labels`` (``{measurement_id: {trace_id: label}}``) so a live
    run can be frozen to a committed JSON afterward. Delegates every other attribute
    (``calls``, ``cache_hits``, ``model_id``, ``usage()``, ...) to the wrapped model.
    """

    def __init__(self, inner: Any):
        self._inner = inner
        self.labels: dict[str, dict[str, str]] = {}

    def complete_json(
        self, *, stage: str, prompt_version: str, system: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        response = self._inner.complete_json(
            stage=stage, prompt_version=prompt_version, system=system, payload=payload
        )
        if not stage.startswith(_STAGE_PREFIX) or not isinstance(response, dict):
            return response
        bucket = self.labels.setdefault(_measurement_id_from_stage(stage), {})
        for row in response.get("results", []):
            if not isinstance(row, dict):
                continue
            evidence_id = str(row.get("evidence_id") or "")
            value = str(row.get("value") or "").upper()
            if evidence_id and value and value != "ABSTAIN":
                bucket[evidence_id] = value
        return response

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def load_frozen_labels(path: Path) -> dict[str, dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_frozen_labels(path: Path, labels: dict[str, dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(labels, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def merge_frozen_labels(
    existing: dict[str, dict[str, str]], new: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    """New labels win per (measurement_id, trace_id); everything else is kept."""
    merged = {measurement_id: dict(trace_labels) for measurement_id, trace_labels in existing.items()}
    for measurement_id, trace_labels in new.items():
        merged.setdefault(measurement_id, {}).update(trace_labels)
    return merged
