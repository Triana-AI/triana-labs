"""Account for and publish a local synthetic PreviewTrace JSONL corpus.

This is the corpus boundary between adapter-emitted JSONL and the five LABS-01
artifacts. It owns files, physical lines, cross-line identity, and outcome selection;
profile aggregation and publication are delegated to their owning modules.
"""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from triana_labs.contracts.traces import (
    LineRejection,
    parse_and_validate_line,
)
from triana_labs.observer.profile import build_profile
from triana_labs.observer.publication import PublicationFailure, publish_bundle

JsonObject = dict[str, Any]

_MAX_INPUT_BYTES = 16 * 1024 * 1024
_MAX_LINE_BYTES = 1024 * 1024
_MAX_LINES = 1_000
_CANARY = "OWNER_AUTHORIZED_REAL_DATA_CANARY"


@dataclass(frozen=True)
class ObserveFailure(Exception):
    """Carry a safe fatal corpus refusal and its stable CLI exit status."""

    reason_code: str
    exit_code: int


@dataclass(frozen=True)
class ObserveResult:
    """Hold completed corpus counts and the non-semantic CLI outcome."""

    input_count: int
    accepted_count: int
    rejected_count: int
    case_generation_eligible_count: int
    outcome: str


def observe(input_path: Path, output_path: Path) -> ObserveResult:
    """Account for every input line and atomically publish the five artifacts.

    Fatal file/resource refusals raise :class:`ObserveFailure` without a target
    directory. Per-line rejections remain evidence inside a completed bundle.
    """

    # Output refusal is checked before reading input so the command never performs
    # corpus work when it cannot honor the new-directory/no-overwrite contract. Fatal
    # boundary failures publish nothing; after boundaries pass, every physical line
    # is accounted exactly once as accepted or rejected.

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
    privacy_class: str | None = None

    for line_number, (line, raw_size) in enumerate(lines, start=1):
        # Raw size includes the original line ending. CR is removed only after the
        # limit is decided, making LF, CRLF, and missing-final-LF accounting explicit.
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
            if rejection.code == "UNSUPPORTED_PRIVACY_CLASS":
                raise ObserveFailure(rejection.code, 4) from rejection
            rejected.append(rejection.as_record(line_number))
            continue
        trace_privacy = cast(str, validated.value["privacy_class"])
        if privacy_class is not None and trace_privacy != privacy_class:
            raise ObserveFailure("PRIVACY_CLASS_MISMATCH", 4)
        privacy_class = trace_privacy
        # IDs are reserved only after complete line validation. A rejected line can
        # therefore never prevent a later valid trace from using either identifier.
        accepted.append(validated.value)
        seen_trace_ids.add(trace_id)
        seen_source_ids.add(source_id)
        eligible_count += int(validated.case_generation_eligible)

    profile = build_profile(
        input_count=len(lines),
        accepted=accepted,
        rejected=rejected,
        eligible_count=eligible_count,
    )
    try:
        effective_privacy = privacy_class or "SYNTHETIC"
        if effective_privacy == _CANARY:
            _require_private_path(output_path)
            profile["privacy_class"] = effective_privacy
        publish_bundle(
            output_path, accepted, rejected, profile, privacy_class=effective_privacy
        )
    except PublicationFailure as failure:
        raise ObserveFailure(failure.reason_code, failure.exit_code) from failure
    # The outcome describes corpus accounting, not agent quality. Partial success and
    # an empty corpus still publish inspectable evidence and deliberately exit nonzero
    # at the CLI boundary.
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
    """Require a new target beneath an existing real parent directory."""

    # Existing targets are never merged or replaced. The immediate parent must be a
    # real local directory because later atomic publication uses a private sibling.
    if os.path.lexists(output_path):
        raise ObserveFailure("OUTPUT_ALREADY_EXISTS", 2)
    parent = output_path.parent
    try:
        parent_stat = parent.lstat()
    except OSError as error:
        raise ObserveFailure("OUTPUT_PARENT_MISSING", 2) from error
    if parent.is_symlink() or not stat.S_ISDIR(parent_stat.st_mode):
        raise ObserveFailure("OUTPUT_PARENT_MISSING", 2)


def _require_private_path(path: Path) -> None:
    """Require a not-yet-created artifact root beneath ``/private/tmp``."""

    private_root = Path("/private/tmp").resolve(strict=True)
    resolved = path.parent.resolve(strict=True) / path.name
    package_root = Path(__file__).resolve().parents[3]
    if private_root not in resolved.parents or (
        resolved == package_root or package_root in resolved.parents
    ):
        raise ObserveFailure("UNSUPPORTED_PRIVACY_CLASS", 4)


def _read_input(input_path: Path) -> bytes:
    """Read a path observed as a bounded regular file at the boundary check."""

    # The observed lstat mode rejects a symlink, device, or directory before open.
    # Size is checked both before and after the read so growth during that interval
    # cannot return a payload above the 16 MiB cap.
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
    """Return LF-defined lines paired with their original byte sizes."""

    # Splitting is defined over LF bytes rather than text lines: a final LF terminates
    # the preceding line but does not create an extra empty line, while interior blank
    # lines remain first-class rejected inputs with one-based positions.
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
