from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .constants import (
    BUNDLE_FILES,
    NON_SUCCESS_IF_MISSING,
    REQUIRED_TELEMETRY,
    TELEMETRY_STATES,
)
from .journal import verify_event_chain
from .serde import artifact_identity


def _reason(reasons: list[dict[str, str]], code: str, detail: str) -> None:
    reasons.append({"code": code, "detail": detail})


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("event is not an object")
            events.append(value)
    return events


def verify_bundle(run_dir: Path | str, *, secret_values: Iterable[str] = ()) -> dict[str, Any]:
    root = Path(run_dir)
    reasons: list[dict[str, str]] = []
    telemetry: dict[str, Any] = {}
    artifact_hashes: dict[str, Any] = {}

    if not root.is_dir():
        _reason(reasons, "RUN_DIRECTORY_INVALID", f"not a directory: {root}")
        return {
            "valid": False,
            "reasons": reasons,
            "telemetry": telemetry,
            "artifact_hashes": artifact_hashes,
        }

    present = {path.name for path in root.iterdir()}
    for name in sorted(BUNDLE_FILES - present):
        _reason(reasons, "REQUIRED_ARTIFACT_MISSING", name)
    for name in sorted(present - BUNDLE_FILES):
        _reason(reasons, "UNEXPECTED_ARTIFACT", name)

    secrets = tuple(secret.encode("utf-8") for secret in secret_values if secret)
    for path in sorted((path for path in root.iterdir() if path.is_file()), key=lambda item: item.name):
        data = path.read_bytes()
        if any(secret in data for secret in secrets):
            _reason(reasons, "SECRET_REFLECTION", path.name)

    manifest: dict[str, Any] = {}
    manifest_path = root / "manifest.json"
    if manifest_path.is_file():
        try:
            loaded = _load_json(manifest_path)
            if not isinstance(loaded, dict):
                raise ValueError("manifest is not an object")
            manifest = loaded
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            _reason(reasons, "MANIFEST_INVALID", str(exc))

    declared_artifacts = manifest.get("artifacts", {})
    if isinstance(declared_artifacts, dict):
        for name, declared in declared_artifacts.items():
            path = root / name
            if name not in BUNDLE_FILES or name == "manifest.json":
                _reason(reasons, "MANIFEST_ARTIFACT_INVALID", str(name))
                continue
            if not path.is_file():
                continue
            actual = artifact_identity(path)
            artifact_hashes[name] = actual
            if (
                not isinstance(declared, dict)
                or declared.get("sha256") != actual["sha256"]
                or declared.get("size") != actual["size"]
            ):
                _reason(reasons, "ARTIFACT_HASH_MISMATCH", str(name))
    else:
        _reason(reasons, "MANIFEST_INVALID", "artifacts must be an object")

    events_path = root / "events.jsonl"
    if events_path.is_file():
        chain = verify_event_chain(events_path)
        if not chain.get("valid"):
            _reason(reasons, "EVENT_CHAIN_INVALID", str(chain.get("reason", "unknown chain error")))
        try:
            events = _read_events(events_path)
            attempts: dict[str, dict[str, int]] = {}
            for event in events:
                event_name = event.get("event_name")
                payload = event.get("payload", {})
                if event_name not in {"model.request", "model.response", "model.error"} or not isinstance(
                    payload, dict
                ):
                    continue
                call_id = payload.get("call_id")
                if not isinstance(call_id, str) or not call_id:
                    _reason(reasons, "MODEL_CALL_ID_INVALID", str(call_id))
                    continue
                counts = attempts.setdefault(call_id, {"request": 0, "terminal": 0})
                if event_name == "model.request":
                    counts["request"] += 1
                else:
                    counts["terminal"] += 1
            for call_id, counts in attempts.items():
                if counts["request"] != 1:
                    _reason(reasons, "MODEL_REQUEST_INVALID", call_id)
                if counts["terminal"] == 0:
                    _reason(reasons, "MODEL_TERMINAL_MISSING", call_id)
                elif counts["terminal"] != 1:
                    _reason(reasons, "MODEL_TERMINAL_INVALID", call_id)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            if not any(reason["code"] == "EVENT_CHAIN_INVALID" for reason in reasons):
                _reason(reasons, "EVENT_CHAIN_INVALID", str(exc))

    completeness_path = root / "completeness.json"
    if completeness_path.is_file():
        try:
            completeness = _load_json(completeness_path)
            if not isinstance(completeness, dict) or not isinstance(completeness.get("telemetry"), dict):
                raise ValueError("completeness telemetry must be an object")
            telemetry = completeness["telemetry"]
            for field in REQUIRED_TELEMETRY:
                classification = telemetry.get(field)
                if (
                    not isinstance(classification, dict)
                    or classification.get("state") not in TELEMETRY_STATES
                ):
                    _reason(reasons, "TELEMETRY_FIELD_UNCLASSIFIED", field)
            for field in NON_SUCCESS_IF_MISSING:
                classification = telemetry.get(field)
                if isinstance(classification, dict) and classification.get("state") != "CAPTURED":
                    _reason(reasons, "REQUIRED_OBSERVABLE_NOT_CAPTURED", field)
            for field, classification in telemetry.items():
                if isinstance(classification, dict) and classification.get("state") == "INVALID":
                    _reason(reasons, "TELEMETRY_INVALID", str(field))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            _reason(reasons, "COMPLETENESS_INVALID", str(exc))

    report = {
        "valid": not reasons,
        "reasons": reasons,
        "telemetry": telemetry,
        "artifact_hashes": artifact_hashes,
    }
    return report
