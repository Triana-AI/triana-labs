from __future__ import annotations

import io
import json
from typing import Any, BinaryIO

from .models import ParsedImport, SourceValidationError

HRAI_NORMALIZED_TRACE_V2 = "hrai-normalized-trace-v2-parser-v1"
_ALLOWED_STATUSES = frozenset({"COMPLETED", "HARNESS_ERROR"})


def parse_hrai_normalized_traces(stream: BinaryIO) -> ParsedImport:
    physical_count = 0
    usable_count = 0
    status_counts: dict[str, int] = {}
    record_ids: list[str] = []
    seen_ids: set[str] = set()

    text = io.TextIOWrapper(stream, encoding="utf-8", errors="strict", newline="")
    try:
        for line_number, raw_line in enumerate(text, start=1):
            if not raw_line.strip():
                raise SourceValidationError(f"blank JSONL record at line {line_number}")
            try:
                record: Any = json.loads(raw_line)
            except json.JSONDecodeError as error:
                raise SourceValidationError(
                    f"invalid JSON at line {line_number}: {error.msg}"
                ) from error
            if not isinstance(record, dict):
                raise SourceValidationError(f"record {line_number} is not an object")
            if record.get("schema_version") != "normalized-trace-v2":
                raise SourceValidationError(
                    f"record {line_number} has unsupported schema_version"
                )
            record_id = record.get("case_id")
            if not isinstance(record_id, str) or not record_id.strip():
                raise SourceValidationError(f"record {line_number} has invalid case_id")
            if record_id in seen_ids:
                raise SourceValidationError(f"duplicate case_id {record_id!r}")
            status = record.get("status")
            if status not in _ALLOWED_STATUSES:
                raise SourceValidationError(
                    f"record {line_number} has unsupported status {status!r}"
                )
            turns = record.get("turns")
            if not isinstance(turns, list):
                raise SourceValidationError(f"record {line_number} has invalid turns")
            if status == "COMPLETED" and not turns:
                raise SourceValidationError(
                    f"completed record {line_number} has no conversation turns"
                )

            seen_ids.add(record_id)
            record_ids.append(record_id)
            physical_count += 1
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == "COMPLETED":
                usable_count += 1
    except UnicodeDecodeError as error:
        raise SourceValidationError("source is not valid UTF-8") from error
    finally:
        text.detach()

    if physical_count == 0:
        raise SourceValidationError("source contains no JSONL records")

    return ParsedImport(
        physical_record_count=physical_count,
        usable_conversation_count=usable_count,
        source_status_counts=dict(sorted(status_counts.items())),
        record_ids=tuple(record_ids),
    )
