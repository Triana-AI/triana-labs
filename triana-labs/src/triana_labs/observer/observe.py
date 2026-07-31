"""Local orchestration for the synthetic-only LABS-01 Trace Observer."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from triana_labs.contracts.traces import (
    EVENT_KINDS,
    TERMINAL_STATES,
    LineRejection,
    parse_and_validate_line,
)
from triana_labs.observer.render import compact_json, render_markdown

JsonObject = dict[str, Any]

_MAX_INPUT_BYTES = 16 * 1024 * 1024
_MAX_LINE_BYTES = 1024 * 1024
_MAX_LINES = 1_000


@dataclass(frozen=True)
class ObserveFailure(Exception):
    """Safe fatal refusal with a stable public reason and exit status."""

    reason_code: str
    exit_code: int


@dataclass(frozen=True)
class ObserveResult:
    """Completed corpus accounting and its user-facing outcome."""

    input_count: int
    accepted_count: int
    rejected_count: int
    case_generation_eligible_count: int
    outcome: str


def observe(input_path: Path, output_path: Path) -> ObserveResult:
    """Observe a bounded local synthetic corpus and atomically publish artifacts."""

    _validate_output_boundary(output_path)
    payload = _read_input(input_path)
    lines = _physical_lines(payload)
    if len(lines) > _MAX_LINES:
        raise ObserveFailure("TOO_MANY_LINES", 3)

    accepted: list[JsonObject] = []
    rejected: list[JsonObject] = []
    seen_trace_ids: set[str] = set()
    seen_source_ids: set[str] = set()
    eligible_count = 0

    for line_number, (line, raw_size) in enumerate(lines, start=1):
        if raw_size > _MAX_LINE_BYTES:
            rejected.append(LineRejection("LINE_TOO_LARGE").as_record(line_number))
            continue
        if line.endswith(b"\r"):
            line = line[:-1]
        try:
            validated = parse_and_validate_line(line, first_line=line_number == 1)
            trace_id = cast(str, validated.value["trace_id"])
            source_id = cast(str, validated.value["source_trace_id"])
            if trace_id in seen_trace_ids:
                raise LineRejection("DUPLICATE_TRACE_ID", "/trace_id")
            if source_id in seen_source_ids:
                raise LineRejection("DUPLICATE_SOURCE_TRACE_ID", "/source_trace_id")
        except LineRejection as rejection:
            rejected.append(rejection.as_record(line_number))
            continue
        accepted.append(validated.value)
        seen_trace_ids.add(trace_id)
        seen_source_ids.add(source_id)
        eligible_count += int(validated.case_generation_eligible)

    profile = _build_profile(
        input_count=len(lines),
        accepted=accepted,
        rejected=rejected,
        eligible_count=eligible_count,
    )
    _publish_bundle(output_path, accepted, rejected, profile)
    rejected_count = len(rejected)
    if not lines:
        outcome = "EMPTY_CORPUS"
    elif rejected_count:
        outcome = "COMPLETED_WITH_REJECTIONS"
    else:
        outcome = "COMPLETED"
    return ObserveResult(
        input_count=len(lines),
        accepted_count=len(accepted),
        rejected_count=rejected_count,
        case_generation_eligible_count=eligible_count,
        outcome=outcome,
    )


def _validate_output_boundary(output_path: Path) -> None:
    if os.path.lexists(output_path):
        raise ObserveFailure("OUTPUT_ALREADY_EXISTS", 2)
    parent = output_path.parent
    try:
        parent_stat = parent.lstat()
    except OSError as error:
        raise ObserveFailure("OUTPUT_PARENT_MISSING", 2) from error
    if parent.is_symlink() or not stat.S_ISDIR(parent_stat.st_mode):
        raise ObserveFailure("OUTPUT_PARENT_MISSING", 2)


def _read_input(input_path: Path) -> bytes:
    try:
        input_stat = input_path.lstat()
    except FileNotFoundError as error:
        raise ObserveFailure("INPUT_READ_FAILED", 2) from error
    except OSError as error:
        raise ObserveFailure("INPUT_READ_FAILED", 2) from error
    if stat.S_ISLNK(input_stat.st_mode):
        raise ObserveFailure("INPUT_SYMLINK_FORBIDDEN", 2)
    if not stat.S_ISREG(input_stat.st_mode):
        raise ObserveFailure("INPUT_NOT_REGULAR_FILE", 2)
    if input_stat.st_size > _MAX_INPUT_BYTES:
        raise ObserveFailure("INPUT_TOO_LARGE", 3)
    if input_stat.st_mode & (stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH) == 0:
        raise ObserveFailure("INPUT_READ_FAILED", 2)
    try:
        payload = input_path.read_bytes()
    except OSError as error:
        raise ObserveFailure("INPUT_READ_FAILED", 2) from error
    if len(payload) > _MAX_INPUT_BYTES:
        raise ObserveFailure("INPUT_TOO_LARGE", 3)
    return payload


def _physical_lines(payload: bytes) -> list[tuple[bytes, int]]:
    if not payload:
        return []
    parts = payload.split(b"\n")
    has_final_lf = payload.endswith(b"\n")
    if has_final_lf:
        parts.pop()
    return [
        (line, len(line) + int(index < len(parts) - 1 or has_final_lf))
        for index, line in enumerate(parts)
    ]


def _build_profile(
    *,
    input_count: int,
    accepted: list[JsonObject],
    rejected: list[JsonObject],
    eligible_count: int,
) -> JsonObject:
    event_counts = Counter({kind: 0 for kind in EVENT_KINDS})
    terminal_counts = Counter({state: 0 for state in TERMINAL_STATES})
    tool_counts: Counter[str] = Counter()
    for trace in accepted:
        for event in cast(list[JsonObject], trace["events"]):
            kind = cast(str, event["event_kind"])
            event_counts[kind] += 1
            if kind == "TOOL_CALL":
                tool_counts[cast(str, event["tool_name"])] += 1
            elif kind == "TERMINAL":
                terminal_counts[cast(str, event["terminal_state"])] += 1
    rejection_counts = Counter(cast(str, record["code"]) for record in rejected)
    return {
        "artifact_kind": "corpus_profile",
        "schema_version": 1,
        "input_count": input_count,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "case_generation_eligible_count": eligible_count,
        "event_kind_counts": dict(sorted(event_counts.items())),
        "tool_call_counts": dict(sorted(tool_counts.items())),
        "terminal_state_counts": dict(sorted(terminal_counts.items())),
        "rejection_code_counts": dict(sorted(rejection_counts.items())),
        "language_analysis": "NOT_EVALUATED",
        "distress_analysis": "NOT_EVALUATED",
    }


def _publish_bundle(
    output_path: Path,
    accepted: list[JsonObject],
    rejected: list[JsonObject],
    profile: JsonObject,
) -> None:
    normalized_bytes = b"".join(compact_json(trace) for trace in accepted)
    rejected_bytes = b"".join(compact_json(record) for record in rejected)
    profile_bytes = compact_json(profile)
    markdown_bytes = render_markdown(profile)
    artifacts = {
        "normalized_traces.jsonl": normalized_bytes,
        "rejected_traces.jsonl": rejected_bytes,
        "corpus_profile.json": profile_bytes,
        "corpus_profile.md": markdown_bytes,
    }
    manifest = {
        "artifact_kind": "corpus_manifest",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "input_count": profile["input_count"],
        "accepted_count": profile["accepted_count"],
        "rejected_count": profile["rejected_count"],
        "case_generation_eligible_count": profile["case_generation_eligible_count"],
        "artifacts": {
            name: f"sha256:{hashlib.sha256(payload).hexdigest()}"
            for name, payload in artifacts.items()
        },
    }
    artifacts["manifest.json"] = compact_json(manifest)
    _write_atomically(output_path, artifacts)


def _write_atomically(output_path: Path, artifacts: dict[str, bytes]) -> None:
    parent = output_path.parent
    try:
        parent_mode = parent.stat().st_mode
    except OSError as error:
        raise ObserveFailure("OUTPUT_WRITE_FAILED", 7) from error
    if parent_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0:
        raise ObserveFailure("OUTPUT_WRITE_FAILED", 7)
    temporary: Path | None = None
    try:
        temporary = Path(
            tempfile.mkdtemp(prefix=f".{output_path.name}.tmp-", dir=parent)
        )
        for name, payload in artifacts.items():
            (temporary / name).write_bytes(payload)
        if os.path.lexists(output_path):
            raise OSError
        temporary.rename(output_path)
    except Exception as error:
        if temporary is not None and temporary.exists():
            try:
                shutil.rmtree(temporary)
            except OSError as cleanup_error:
                raise ObserveFailure("INTERNAL_INVARIANT_FAILED", 70) from cleanup_error
        raise ObserveFailure("OUTPUT_WRITE_FAILED", 7) from error
