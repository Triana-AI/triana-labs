"""Local-only persistence boundary for Trace-to-Eval engine artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from triana_labs.trace_to_eval import (
    append_human_ruling,
    read_human_rulings,
    run_trace_to_eval,
)
from triana_labs.trace_to_eval.adapters import prepare_evidence_manifest

JsonObject = dict[str, Any]


class LocalTraceToEvalService:
    """Expose one content-addressed local artifact root to the operator API."""

    def __init__(self, root: Path, *, semantic_model: Any = None) -> None:
        self._root = root
        self._semantic_model = semantic_model

    def run(
        self,
        manifest_path: str | None = None,
        *,
        source_path: str | None = None,
        source_kind: str | None = None,
    ) -> JsonObject:
        selected = manifest_path if manifest_path is not None else source_path
        if selected is None:
            raise ValueError("SOURCE_UNAVAILABLE")
        manifest = Path(selected)
        try:
            identity = hashlib.sha256(
                manifest.read_bytes() + (source_kind or "manifest").encode("utf-8")
            ).hexdigest()
        except OSError as error:
            raise ValueError("MANIFEST_UNAVAILABLE") from error
        output = self._root / identity
        if source_path is not None:
            if not source_kind:
                raise ValueError("SOURCE_KIND_REQUIRED")
            manifest = prepare_evidence_manifest(
                source_path,
                output / "prepared",
                source_kind=source_kind,
                semantic_model_id=(
                    cast(str, self._semantic_model.model_id)
                    if self._semantic_model is not None
                    else None
                ),
            )
        report = run_trace_to_eval(
            manifest,
            output,
            semantic_model=self._semantic_model,
        )
        queue = _read_canonical_object(output / "review_queue.json")
        return {
            "artifact_kind": "trace_to_eval_run_receipt_v0",
            "schema_version": 0,
            "report": report,
            "review_queue": queue,
        }

    def get_report(self, report_id: str) -> JsonObject:
        output, report = self._find_report(report_id)
        del output
        return report

    def get_review_state(self, report_id: str) -> JsonObject:
        output, _ = self._find_report(report_id)
        queue = _read_canonical_object(output / "review_queue.json")
        rulings = read_human_rulings(output, report_id)
        current: dict[str, JsonObject] = {}
        for ruling in rulings:
            item_id = ruling.get("item_id")
            if not isinstance(item_id, str):
                raise ValueError("LOCAL_ARTIFACT_INVALID")
            current[item_id] = ruling
        return {
            "artifact_kind": "trace_to_eval_review_state_v0",
            "schema_version": 0,
            "report_id": report_id,
            "review_queue": queue,
            "current_rulings": [current[key] for key in sorted(current)],
        }

    def append_ruling(self, report_id: str, ruling: Mapping[str, Any]) -> JsonObject:
        output, _ = self._find_report(report_id)
        return append_human_ruling(output, ruling)

    def get_conversation(self, report_id: str, trace_id: str) -> JsonObject:
        output, _ = self._find_report(report_id)
        artifact = _read_canonical_object(output / "conversations.json")
        if (
            artifact.get("artifact_kind") != "trace_to_eval_conversations_v0"
            or artifact.get("report_id") != report_id
        ):
            raise ValueError("CONVERSATION_ARTIFACT_INVALID")
        conversations = artifact.get("conversations")
        if not isinstance(conversations, list):
            raise ValueError("CONVERSATION_ARTIFACT_INVALID")
        conversation = next(
            (
                item
                for item in conversations
                if isinstance(item, dict) and item.get("trace_id") == trace_id
            ),
            None,
        )
        if conversation is None:
            raise KeyError(trace_id)
        return {
            "artifact_kind": "trace_to_eval_conversation_v0",
            "schema_version": 0,
            "report_id": report_id,
            "conversation": conversation,
        }

    def _find_report(self, report_id: str) -> tuple[Path, JsonObject]:
        if not report_id.startswith("sha256:") or len(report_id) != 71:
            raise KeyError(report_id)
        if not self._root.exists():
            raise KeyError(report_id)
        for path in sorted(self._root.glob("*/trace_to_eval_report.json")):
            report = _read_canonical_object(path)
            if report.get("report_id") == report_id:
                return path.parent, report
        raise KeyError(report_id)


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _read_canonical_object(path: Path) -> JsonObject:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("LOCAL_ARTIFACT_INVALID") from error
    if not isinstance(value, dict) or raw != _canonical(value):
        raise ValueError("LOCAL_ARTIFACT_INVALID")
    return cast(JsonObject, value)


__all__ = ["LocalTraceToEvalService"]
