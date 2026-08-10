#!/usr/bin/env python3
"""Deterministic local trace onboarding for Triana Preview."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

JsonObject = dict[str, Any]

_MAX_SOURCE_BYTES = 16 * 1024 * 1024
_MAX_LINE_BYTES = 1024 * 1024
_MAX_LINES = 1_000
_MAX_PREVIEWS = 3
_MAX_SAFE_INTEGER = 9_007_199_254_740_991
_ALLOWED_EVENTS = {
    "SYSTEM_VISIBLE_MESSAGE",
    "USER_MESSAGE",
    "ASSISTANT_MESSAGE",
    "TOOL_CALL",
    "TOOL_RESULT",
    "TERMINAL",
}
_MESSAGE_EVENTS = {
    "SYSTEM_VISIBLE_MESSAGE",
    "USER_MESSAGE",
    "ASSISTANT_MESSAGE",
}
_PRIVACY_CLASSES = {
    "SYNTHETIC",
    "OWNER_AUTHORIZED_REAL_DATA_CANARY",
    "CUSTOMER_AUTHORIZED_TRACE_DATA",
}
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
_SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_IMAGE_DIGEST = re.compile(r"^\S+@sha256:[0-9a-f]{64}$")
_KNOWN_STRUCTURAL_KEYS = {
    "arguments",
    "call_id",
    "content",
    "contract_kind",
    "error_code",
    "event_kind",
    "events",
    "is_final",
    "messages",
    "metadata",
    "privacy_class",
    "priority",
    "result",
    "result_state",
    "role",
    "schema_version",
    "sequence",
    "session_id",
    "source_trace_id",
    "tenant",
    "terminal_state",
    "tool_name",
    "trace_id",
}


class Refusal(Exception):
    """A content-free refusal at the onboarding boundary."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _emit(value: JsonObject) -> None:
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True))


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "unknown"


def _read_regular(path: Path, *, empty_reason: str) -> bytes:
    try:
        details = path.lstat()
    except OSError as error:
        raise Refusal("TRACE_SOURCE_INVALID") from error
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISREG(details.st_mode):
        raise Refusal("TRACE_SOURCE_UNSAFE")
    if details.st_size <= 0:
        raise Refusal(empty_reason)
    if details.st_size > _MAX_SOURCE_BYTES:
        raise Refusal("TRACE_SOURCE_INVALID")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            payload = stream.read(_MAX_SOURCE_BYTES + 1)
    except OSError as error:
        raise Refusal("TRACE_SOURCE_UNSAFE") from error
    if not payload or len(payload) > _MAX_SOURCE_BYTES:
        raise Refusal(empty_reason if not payload else "TRACE_SOURCE_INVALID")
    return payload


class _DuplicateKey(ValueError):
    pass


class _NonFinite(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> JsonObject:
    value: JsonObject = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey
        value[key] = item
    return value


def _reject_nonfinite(_: str) -> None:
    raise _NonFinite


def _json_depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((_json_depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((_json_depth(item) for item in value), default=0)
    return 0


def _physical_lines(payload: bytes, *, reason: str) -> list[bytes]:
    # JSONL uses LF as its only record separator. A CR is accepted only as the
    # companion byte immediately before LF, never as a standalone boundary.
    lines = payload.split(b"\n")
    ended_with_lf = lines[-1] == b""
    if ended_with_lf:
        lines.pop()
    if not lines or len(lines) > _MAX_LINES:
        raise Refusal(reason)
    bounded: list[bytes] = []
    for index, raw in enumerate(lines):
        raw_size = len(raw) + int(index < len(lines) - 1 or ended_with_lf)
        if raw_size > _MAX_LINE_BYTES:
            raise Refusal(reason)
        line = raw
        if line.endswith(b"\r"):
            line = line[:-1]
        bounded.append(line)
    return bounded


def _parse_json_line(raw: bytes, *, first_line: bool, reason: str) -> Any:
    if first_line and raw.startswith(b"\xef\xbb\xbf"):
        raise Refusal(reason)
    try:
        text = raw.decode("utf-8", errors="strict")
        if not text.strip():
            raise ValueError
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_float=Decimal,
            parse_constant=_reject_nonfinite,
        )
        if _json_depth(value) > 32:
            raise ValueError
        return value
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        RecursionError,
        _DuplicateKey,
        _NonFinite,
        ValueError,
    ) as error:
        raise Refusal(reason) from error


def _json_lines(payload: bytes, *, reason: str) -> list[Any]:
    return [
        _parse_json_line(line, first_line=index == 0, reason=reason)
        for index, line in enumerate(_physical_lines(payload, reason=reason))
    ]


def _walk_shape(
    value: Any,
    path: str,
    shapes: dict[str, Counter[str]],
    *,
    redacted_keys: list[int],
    depth: int = 0,
) -> None:
    if depth > 20:
        return
    shapes[path or "$"].update([_type_name(value)])
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            projected = key if key in _KNOWN_STRUCTURAL_KEYS else "[REDACTED_KEY]"
            redacted_keys[0] += int(projected != key)
            child_path = f"{path}.{projected}" if path else projected
            _walk_shape(
                child,
                child_path,
                shapes,
                redacted_keys=redacted_keys,
                depth=depth + 1,
            )
    elif isinstance(value, list):
        for child in value[:100]:
            _walk_shape(
                child,
                f"{path}[]",
                shapes,
                redacted_keys=redacted_keys,
                depth=depth + 1,
            )


def _structural_summary(payload: bytes) -> JsonObject:
    values = _json_lines(payload, reason="TRACE_SOURCE_INVALID")
    roots: Counter[str] = Counter()
    shapes: dict[str, Counter[str]] = defaultdict(Counter)
    redacted_keys = [0]
    for value in values:
        roots.update([_type_name(value)])
        _walk_shape(value, "", shapes, redacted_keys=redacted_keys)
    return {
        "physical_line_count": len(values),
        "root_types": dict(sorted(roots.items())),
        "field_shapes": [
            {"path": path, "types": dict(sorted(types.items()))}
            for path, types in sorted(shapes.items())
        ],
        "redacted_key_count": redacted_keys[0],
    }


def _contains_control(value: str, *, allow_lf: bool) -> bool:
    return any(
        (code < 32 and not (allow_lf and code == 10)) or 127 <= code <= 159
        for code in map(ord, value)
    )


def _bounded_text(value: Any, *, minimum: int, maximum: int, allow_lf: bool) -> bool:
    if not isinstance(value, str) or _contains_control(value, allow_lf=allow_lf):
        return False
    try:
        size = len(value.encode("utf-8"))
    except UnicodeEncodeError:
        return False
    return minimum <= size <= maximum


def _safe_id(value: Any) -> bool:
    return isinstance(value, str) and _SAFE_ID.fullmatch(value) is not None


def _safe_code(value: Any) -> bool:
    return isinstance(value, str) and _SAFE_CODE.fullmatch(value) is not None


def _opaque_json(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, str):
        return _bounded_text(value, minimum=0, maximum=65_536, allow_lf=True)
    if type(value) is int:
        return -_MAX_SAFE_INTEGER <= value <= _MAX_SAFE_INTEGER
    if isinstance(value, Decimal):
        return False
    if isinstance(value, list):
        return all(_opaque_json(item) for item in value)
    if isinstance(value, dict):
        return all(
            _bounded_text(key, minimum=0, maximum=65_536, allow_lf=True)
            and _opaque_json(item)
            for key, item in value.items()
        )
    return False


def _validate_tool_result(event: JsonObject) -> None:
    state = event.get("result_state")
    if state == "SUCCEEDED":
        valid = set(event) == {
            "sequence",
            "event_kind",
            "call_id",
            "result_state",
            "result",
        } and _opaque_json(event.get("result"))
    elif state == "ERROR":
        valid = set(event) == {
            "sequence",
            "event_kind",
            "call_id",
            "result_state",
            "error_code",
        } and _safe_code(event.get("error_code"))
    else:
        valid = False
    if not valid or not _safe_id(event.get("call_id")):
        raise Refusal("PREVIEWTRACE_INVALID")


def _validate_terminal(event: JsonObject) -> None:
    state = event.get("terminal_state")
    if not isinstance(state, str):
        valid = False
    elif state == "SUCCESS":
        valid = set(event) == {"sequence", "event_kind", "terminal_state"}
    elif state in {"ERROR", "ABORTED"}:
        valid = set(event) == {
            "sequence",
            "event_kind",
            "terminal_state",
            "reason_code",
        } and _safe_code(event.get("reason_code"))
    else:
        valid = False
    if not valid:
        raise Refusal("PREVIEWTRACE_INVALID")


def _validate_event(event: Any) -> None:
    if not isinstance(event, dict):
        raise Refusal("PREVIEWTRACE_INVALID")
    sequence = event.get("sequence")
    if type(sequence) is not int or not 0 <= sequence <= _MAX_SAFE_INTEGER:
        raise Refusal("PREVIEWTRACE_INVALID")
    kind = event.get("event_kind")
    if not isinstance(kind, str) or kind not in _ALLOWED_EVENTS:
        raise Refusal("PREVIEWTRACE_INVALID")
    if kind in {"USER_MESSAGE", "SYSTEM_VISIBLE_MESSAGE"}:
        if set(event) != {"sequence", "event_kind", "content"} or not _bounded_text(
            event.get("content"), minimum=1, maximum=65_536, allow_lf=True
        ):
            raise Refusal("PREVIEWTRACE_INVALID")
    elif kind == "ASSISTANT_MESSAGE":
        if (
            set(event) != {"sequence", "event_kind", "content", "is_final"}
            or not _bounded_text(
                event.get("content"), minimum=0, maximum=65_536, allow_lf=True
            )
            or type(event.get("is_final")) is not bool
        ):
            raise Refusal("PREVIEWTRACE_INVALID")
    elif kind == "TOOL_CALL":
        if (
            set(event)
            != {"sequence", "event_kind", "call_id", "tool_name", "arguments"}
            or not _safe_id(event.get("call_id"))
            or not _safe_id(event.get("tool_name"))
            or not _opaque_json(event.get("arguments"))
        ):
            raise Refusal("PREVIEWTRACE_INVALID")
    elif kind == "TOOL_RESULT":
        _validate_tool_result(event)
    else:
        _validate_terminal(event)


def _validate_relationships(events: list[JsonObject]) -> None:
    calls: set[str] = set()
    results: set[str] = set()
    final_count = 0
    terminal_indices: list[int] = []
    for index, event in enumerate(events):
        if event["sequence"] != index:
            raise Refusal("PREVIEWTRACE_INVALID")
        kind = event["event_kind"]
        if kind == "TOOL_CALL":
            call_id = event["call_id"]
            if call_id in calls:
                raise Refusal("PREVIEWTRACE_INVALID")
            calls.add(call_id)
        elif kind == "TOOL_RESULT":
            call_id = event["call_id"]
            if call_id not in calls or call_id in results:
                raise Refusal("PREVIEWTRACE_INVALID")
            results.add(call_id)
        elif kind == "ASSISTANT_MESSAGE" and event["is_final"] is True:
            final_count += 1
        elif kind == "TERMINAL":
            terminal_indices.append(index)
    if final_count > 1 or len(terminal_indices) > 1:
        raise Refusal("PREVIEWTRACE_INVALID")
    if terminal_indices and terminal_indices[0] != len(events) - 1:
        raise Refusal("PREVIEWTRACE_INVALID")


def _validate_trace(value: Any, trace_ids: set[str], source_ids: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != {
        "contract_kind",
        "schema_version",
        "privacy_class",
        "trace_id",
        "source_trace_id",
        "events",
    }:
        raise Refusal("PREVIEWTRACE_INVALID")
    if (
        value["contract_kind"] != "preview_trace"
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
        or not isinstance(value["privacy_class"], str)
        or value["privacy_class"] not in _PRIVACY_CLASSES
        or not _safe_id(value["trace_id"])
        or not _bounded_text(
            value["source_trace_id"], minimum=1, maximum=512, allow_lf=False
        )
    ):
        raise Refusal("PREVIEWTRACE_INVALID")
    events = value["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 1_000:
        raise Refusal("PREVIEWTRACE_INVALID")
    for event in events:
        _validate_event(event)
    _validate_relationships(events)
    trace_id = value["trace_id"]
    source_id = value["source_trace_id"]
    if trace_id in trace_ids or source_id in source_ids:
        raise Refusal("PREVIEWTRACE_INVALID")
    trace_ids.add(trace_id)
    source_ids.add(source_id)


def _validated_traces(payload: bytes) -> list[JsonObject]:
    values = _json_lines(payload, reason="PREVIEWTRACE_INVALID")
    trace_ids: set[str] = set()
    source_ids: set[str] = set()
    privacy_class: str | None = None
    for value in values:
        _validate_trace(value, trace_ids, source_ids)
        current_privacy = value["privacy_class"]
        if privacy_class is not None and current_privacy != privacy_class:
            raise Refusal("PRIVACY_CLASS_MISMATCH")
        privacy_class = current_privacy
    return [value for value in values if isinstance(value, dict)]


def _private_write(path: Path, payload: bytes) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as error:
        raise Refusal("ADAPTER_OUTPUT_INVALID") from error


def _inspect(source: Path) -> JsonObject:
    payload = _read_regular(source, empty_reason="TRACE_SOURCE_INVALID")
    return {"outcome": "COMPLETED", **_structural_summary(payload)}


def _validate(source: Path, output: Path) -> JsonObject:
    if output.exists() or output.is_symlink():
        raise Refusal("ADAPTER_OUTPUT_INVALID")
    payload = _read_regular(source, empty_reason="ADAPTER_OUTPUT_INVALID")
    traces = _validated_traces(payload)
    _private_write(output, payload)
    return {
        "outcome": "COMPLETED",
        "trace_count": len(traces),
        "source_sha256": _sha256(payload),
    }


def _scaffold(source: Path, output: Path) -> JsonObject:
    if output.exists() or output.is_symlink():
        raise Refusal("ADAPTER_OUTPUT_INVALID")
    payload = _read_regular(source, empty_reason="TRACE_SOURCE_INVALID")
    summary = _structural_summary(payload)
    asset = Path(__file__).resolve().parent.parent / "assets" / "adapter.py.template"
    try:
        adapter = asset.read_bytes()
        output.mkdir(parents=True, mode=0o700)
        output.chmod(0o700)
        _private_write(output / "adapter.py", adapter)
        contract: JsonObject = {
            "artifact_kind": "triana_adapter_contract_v0",
            "schema_version": 0,
            "status": "IMPLEMENTATION_REQUIRED",
            "source_sha256": _sha256(payload),
            "source_structure": summary,
            "target_contract": "PreviewTrace v1",
            "rules": [
                "Map only source facts.",
                "Do not invent missing roles, content, tool links, or timestamps.",
                "Validate the output before running Triana Preview.",
            ],
        }
        _private_write(
            output / "adapter-contract.json",
            (json.dumps(contract, separators=(",", ":"), sort_keys=True) + "\n").encode(
                "utf-8"
            ),
        )
    except Refusal:
        raise
    except OSError as error:
        raise Refusal("ADAPTER_OUTPUT_INVALID") from error
    return {
        "outcome": "SCAFFOLDED",
        "status": "IMPLEMENTATION_REQUIRED",
        "source_sha256": _sha256(payload),
    }


def _preview(source: Path) -> JsonObject:
    payload = _read_regular(source, empty_reason="ADAPTER_OUTPUT_INVALID")
    traces = _validated_traces(payload)
    previews: list[JsonObject] = []
    for index, trace in enumerate(traces[:_MAX_PREVIEWS], 1):
        events: list[JsonObject] = []
        for event in trace["events"]:
            row: JsonObject = {
                "sequence": event["sequence"],
                "event_kind": event["event_kind"],
            }
            if event["event_kind"] in _MESSAGE_EVENTS:
                row["content"] = "[REDACTED]"
            if event["event_kind"] in {"TOOL_CALL", "TOOL_RESULT"}:
                row["tool_evidence"] = "[REDACTED]"
            events.append(row)
        previews.append({"trace_ordinal": index, "events": events})
    return {
        "outcome": "COMPLETED",
        "trace_count": len(traces),
        "previews": previews,
    }


def _release(path: Path) -> tuple[str, str]:
    payload = _read_regular(path, empty_reason="RELEASE_UNPUBLISHED")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Refusal("RELEASE_UNPUBLISHED") from error
    if (
        not isinstance(value, dict)
        or value.get("artifact_kind") != "triana_preview_release_manifest_v0"
        or value.get("schema_version") != 0
        or value.get("publication_state") != "PUBLISHED"
    ):
        raise Refusal("RELEASE_UNPUBLISHED")
    image = value.get("image")
    if not isinstance(image, str) or _IMAGE_DIGEST.fullmatch(image) is None:
        raise Refusal("RELEASE_IMAGE_NOT_DIGEST_PINNED")
    return image, _sha256(payload)


def _docker_command(
    source: Path,
    output: Path,
    agent: str,
    release_manifest: Path,
) -> JsonObject:
    payload = _read_regular(source, empty_reason="ADAPTER_OUTPUT_INVALID")
    _validated_traces(payload)
    try:
        output_details = output.lstat()
    except OSError as error:
        raise Refusal("ADAPTER_OUTPUT_INVALID") from error
    if stat.S_ISLNK(output_details.st_mode) or not stat.S_ISDIR(output_details.st_mode):
        raise Refusal("ADAPTER_OUTPUT_INVALID")
    try:
        agent_bytes = agent.encode("utf-8")
    except UnicodeEncodeError as error:
        raise Refusal("AGENT_DESCRIPTION_INVALID") from error
    agent_lines = agent.split("\n")
    if (
        not 1 <= len(agent_lines) <= 3
        or any(not line.strip() for line in agent_lines)
        or len(agent_bytes) > 2_000
    ):
        raise Refusal("AGENT_DESCRIPTION_INVALID")
    image, manifest_hash = _release(release_manifest)
    source_path = source.resolve()
    output_path = output.resolve()
    argv = [
        "docker",
        "run",
        "--rm",
        "--mount",
        f"type=bind,src={source_path},dst=/triana/input/traces.jsonl,readonly",
        "--mount",
        f"type=bind,src={output_path},dst=/triana/output",
        image,
        "analyze",
        "--traces",
        "/triana/input/traces.jsonl",
        "--agent",
        agent,
        "--output",
        "/triana/output",
        "--confirm-authorized-traces",
    ]
    return {
        "outcome": "READY",
        "docker_argv": argv,
        "image": image,
        "release_manifest_sha256": manifest_hash,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onboard.py")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "preview"):
        command = commands.add_parser(name)
        command.add_argument("--source", required=True)
        command.add_argument("--confirm-authorized-traces", action="store_true")
    validate = commands.add_parser("validate")
    validate.add_argument("--source", required=True)
    validate.add_argument("--output", required=True)
    validate.add_argument("--confirm-authorized-traces", action="store_true")
    scaffold = commands.add_parser("scaffold")
    scaffold.add_argument("--source", required=True)
    scaffold.add_argument("--output-dir", required=True)
    scaffold.add_argument("--confirm-authorized-traces", action="store_true")
    docker = commands.add_parser("docker-command")
    docker.add_argument("--source", required=True)
    docker.add_argument("--output-dir", required=True)
    docker.add_argument("--agent", required=True)
    docker.add_argument("--release-manifest", required=True)
    docker.add_argument("--confirm-authorized-traces", action="store_true")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parsed = _parser().parse_args(arguments)
    try:
        if not parsed.confirm_authorized_traces:
            raise Refusal("TRACE_AUTHORIZATION_REQUIRED")
        source = Path(parsed.source)
        if parsed.command == "inspect":
            result = _inspect(source)
        elif parsed.command == "validate":
            result = _validate(source, Path(parsed.output))
        elif parsed.command == "scaffold":
            result = _scaffold(source, Path(parsed.output_dir))
        elif parsed.command == "preview":
            result = _preview(source)
        else:
            result = _docker_command(
                source,
                Path(parsed.output_dir),
                parsed.agent,
                Path(parsed.release_manifest),
            )
        _emit(result)
        return 0
    except Refusal as error:
        _emit({"outcome": "REJECTED", "reason_code": error.reason_code})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
