"""Validate the closed LABS-01 Observer bundle consumed by Corpus Intelligence."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

from triana_labs.contracts.traces import (
    EVENT_KINDS,
    PRIVACY_CLASSES,
    LineRejection,
    parse_and_validate_line,
)

JsonObject = dict[str, Any]

_MIB = 1024 * 1024
_ARTIFACTS = {
    "corpus_profile.json": _MIB,
    "corpus_profile.md": _MIB,
    "normalized_traces.jsonl": 16 * _MIB,
    "rejected_traces.jsonl": 16 * _MIB,
}
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_SAFE_INTEGER = 9_007_199_254_740_991


class InputFailure(Exception):
    """Carry a content-free input refusal reason."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class _InvalidJson(ValueError):
    pass


def read_bundle(manifest_path: Path) -> tuple[bytes, JsonObject, list[JsonObject]]:
    """Return exact manifest bytes, validated manifest, and normalized traces."""

    manifest_bytes = _read_manifest(manifest_path)
    manifest = _parse_object(manifest_bytes, "MANIFEST_INVALID")
    _validate_manifest(manifest)
    if manifest["privacy_class"] == "OWNER_AUTHORIZED_REAL_DATA_CANARY":
        _require_private_path(manifest_path.parent)
    if (
        manifest["input_count"]
        != manifest["accepted_count"] + manifest["rejected_count"]
    ):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    payloads = {
        name: _read_artifact(manifest_path.parent / name, limit)
        for name, limit in _ARTIFACTS.items()
    }
    for name, payload in payloads.items():
        if _digest(payload) != manifest["artifacts"][name]:
            raise InputFailure("CORPUS_INTEGRITY_FAILED")
    traces = _parse_traces(payloads["normalized_traces.jsonl"])
    if any(trace["privacy_class"] != manifest["privacy_class"] for trace in traces):
        raise InputFailure("PRIVACY_CLASS_MISMATCH")
    if len(traces) != manifest["accepted_count"]:
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if not traces:
        raise InputFailure("EMPTY_CORPUS")
    _validate_profile(
        payloads["corpus_profile.json"],
        manifest,
        traces,
        payloads["rejected_traces.jsonl"],
    )
    return manifest_bytes, manifest, traces


def _read_manifest(path: Path) -> bytes:
    try:
        parent = path.parent.lstat()
        metadata = path.lstat()
    except OSError as error:
        raise InputFailure("INPUT_READ_FAILED") from error
    if (
        path.parent.is_symlink()
        or not stat.S_ISDIR(parent.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
    ):
        raise InputFailure("INPUT_READ_FAILED")
    if metadata.st_size > _MIB:
        raise InputFailure("INPUT_TOO_LARGE")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise InputFailure("INPUT_READ_FAILED") from error
    if len(payload) > _MIB:
        raise InputFailure("INPUT_TOO_LARGE")
    return payload


def _read_artifact(path: Path, limit: int) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise InputFailure("CORPUS_INTEGRITY_FAILED") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if metadata.st_size > limit:
        raise InputFailure("INPUT_TOO_LARGE")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise InputFailure("CORPUS_INTEGRITY_FAILED") from error
    if len(payload) > limit:
        raise InputFailure("INPUT_TOO_LARGE")
    return payload


def _parse_object(payload: bytes, reason: str) -> JsonObject:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise InputFailure(reason)
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=Decimal,
            parse_constant=_reject_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        _InvalidJson,
        RecursionError,
    ) as error:
        raise InputFailure(reason) from error
    if _depth(value) > 32 or not isinstance(value, dict):
        raise InputFailure(reason)
    return cast(JsonObject, value)


def _unique_object(pairs: list[tuple[str, Any]]) -> JsonObject:
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise _InvalidJson
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    raise _InvalidJson


def _depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_depth(item) for item in value), default=0)
    return 0


def _validate_manifest(value: JsonObject) -> None:
    keys = {
        "accepted_count",
        "artifact_kind",
        "artifacts",
        "case_generation_eligible_count",
        "input_count",
        "privacy_class",
        "rejected_count",
        "schema_version",
    }
    if set(value) != keys or value.get("artifact_kind") != "corpus_manifest":
        raise InputFailure("MANIFEST_INVALID")
    if value.get("schema_version") != 1 or type(value.get("schema_version")) is not int:
        raise InputFailure("MANIFEST_INVALID")
    if value.get("privacy_class") not in PRIVACY_CLASSES:
        if isinstance(value.get("privacy_class"), str):
            raise InputFailure("UNSUPPORTED_PRIVACY_CLASS")
        raise InputFailure("MANIFEST_INVALID")
    counts = [
        value.get("input_count"),
        value.get("accepted_count"),
        value.get("rejected_count"),
        value.get("case_generation_eligible_count"),
    ]
    if not all(type(item) is int and 0 <= item <= _SAFE_INTEGER for item in counts):
        raise InputFailure("MANIFEST_INVALID")
    artifacts = value.get("artifacts")
    if (
        not isinstance(artifacts, dict)
        or set(artifacts) != set(_ARTIFACTS)
        or not all(
            isinstance(item, str) and _DIGEST.fullmatch(item)
            for item in artifacts.values()
        )
    ):
        raise InputFailure("MANIFEST_INVALID")


def _parse_traces(payload: bytes) -> list[JsonObject]:
    lines = _physical_lines(payload)
    if len(lines) > 1_000 or any(size > _MIB for _, size in lines):
        raise InputFailure("INPUT_TOO_LARGE")
    traces: list[JsonObject] = []
    trace_ids: set[str] = set()
    source_ids: set[str] = set()
    for index, (line, _) in enumerate(lines):
        if line.endswith(b"\r"):
            line = line[:-1]
        try:
            validated = parse_and_validate_line(line, first_line=index == 0)
        except LineRejection as error:
            raise InputFailure("CORPUS_INTEGRITY_FAILED") from error
        trace_id = cast(str, validated.value["trace_id"])
        source_id = cast(str, validated.value["source_trace_id"])
        if trace_id in trace_ids or source_id in source_ids:
            raise InputFailure("CORPUS_INTEGRITY_FAILED")
        trace_ids.add(trace_id)
        source_ids.add(source_id)
        traces.append(validated.value)
    return traces


def _physical_lines(payload: bytes) -> list[tuple[bytes, int]]:
    if not payload:
        return []
    parts = payload.split(b"\n")
    final_lf = payload.endswith(b"\n")
    if final_lf:
        parts.pop()
    return [
        (line, len(line) + int(index < len(parts) - 1 or final_lf))
        for index, line in enumerate(parts)
    ]


def _validate_profile(
    payload: bytes,
    manifest: JsonObject,
    traces: list[JsonObject],
    rejected_payload: bytes,
) -> None:
    profile = _parse_object(payload, "CORPUS_INTEGRITY_FAILED")
    keys = {
        "accepted_count",
        "artifact_kind",
        "case_generation_eligible_count",
        "distress_analysis",
        "event_kind_counts",
        "input_count",
        "language_analysis",
        "rejected_count",
        "rejection_code_counts",
        "schema_version",
        "terminal_state_counts",
        "tool_call_counts",
    }
    if manifest["privacy_class"] != "SYNTHETIC":
        keys.add("privacy_class")
    if set(profile) != keys:
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    fixed = {
        "artifact_kind": "corpus_profile",
        "schema_version": 1,
        "input_count": manifest["input_count"],
        "accepted_count": manifest["accepted_count"],
        "rejected_count": manifest["rejected_count"],
        "case_generation_eligible_count": manifest["case_generation_eligible_count"],
        "language_analysis": "NOT_EVALUATED",
        "distress_analysis": "NOT_EVALUATED",
        **(
            {"privacy_class": manifest["privacy_class"]}
            if manifest["privacy_class"] != "SYNTHETIC"
            else {}
        ),
    }
    if not all(
        type(profile.get(key)) is int
        for key in (
            "input_count",
            "accepted_count",
            "rejected_count",
            "case_generation_eligible_count",
        )
    ):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if not all(
        _is_count_map(profile.get(key))
        for key in (
            "event_kind_counts",
            "terminal_state_counts",
            "tool_call_counts",
            "rejection_code_counts",
        )
    ):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if any(profile.get(key) != expected for key, expected in fixed.items()):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    event_counts: Counter[str] = Counter({key: 0 for key in EVENT_KINDS})
    terminal_counts: Counter[str] = Counter(
        {key: 0 for key in ("ABORTED", "ERROR", "SUCCESS")}
    )
    tool_counts: Counter[str] = Counter()
    eligible = 0
    for trace in traces:
        user_seen = False
        trace_eligible = False
        for event in cast(list[JsonObject], trace["events"]):
            kind = cast(str, event["event_kind"])
            event_counts[kind] += 1
            if kind == "USER_MESSAGE":
                user_seen = True
            elif user_seen and kind in {"ASSISTANT_MESSAGE", "TOOL_CALL"}:
                trace_eligible = True
            if kind == "TERMINAL":
                terminal_counts[cast(str, event["terminal_state"])] += 1
            elif kind == "TOOL_CALL":
                tool_counts[cast(str, event["tool_name"])] += 1
        eligible += int(trace_eligible)
    if eligible != manifest["case_generation_eligible_count"]:
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if profile["event_kind_counts"] != dict(sorted(event_counts.items())):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if profile["terminal_state_counts"] != dict(sorted(terminal_counts.items())):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    if profile["tool_call_counts"] != dict(sorted(tool_counts.items())):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    _validate_rejections(
        rejected_payload, profile, cast(int, manifest["rejected_count"])
    )


def _validate_rejections(
    payload: bytes, profile: JsonObject, expected_count: int
) -> None:
    counts: Counter[str] = Counter()
    lines = _physical_lines(payload)
    if len(lines) != expected_count:
        raise InputFailure("CORPUS_INTEGRITY_FAILED")
    for line, _ in lines:
        record = _parse_object(line, "CORPUS_INTEGRITY_FAILED")
        if set(record) != {"code", "json_pointer", "line_number", "safe_message"}:
            raise InputFailure("CORPUS_INTEGRITY_FAILED")
        code = record.get("code")
        if not isinstance(code, str):
            raise InputFailure("CORPUS_INTEGRITY_FAILED")
        counts[code] += 1
    if profile["rejection_code_counts"] != dict(sorted(counts.items())):
        raise InputFailure("CORPUS_INTEGRITY_FAILED")


def _is_count_map(value: Any) -> bool:
    return isinstance(value, dict) and all(
        isinstance(key, str) and type(count) is int and 0 <= count <= _SAFE_INTEGER
        for key, count in value.items()
    )


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _require_private_path(path: Path) -> None:
    try:
        private_root = Path("/private/tmp").resolve(strict=True)
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise InputFailure("INPUT_READ_FAILED") from error
    package_root = Path(__file__).resolve().parents[3]
    if private_root not in resolved.parents or (
        resolved == package_root or package_root in resolved.parents
    ):
        raise InputFailure("UNSUPPORTED_PRIVACY_CLASS")
