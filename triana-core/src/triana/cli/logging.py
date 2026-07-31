"""Allowlist-only terminal JSONL logging."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from triana import __version__
from triana.core.errors import TrianaError


def timestamp() -> str:
    now = datetime.now(UTC)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _serialize_event(event: dict[str, Any]) -> str:
    """Serialize an already allowlisted event; kept separate for fail-closed tests."""
    return json.dumps(event, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def _write_line(line: str) -> None:
    sys.stderr.write(line + "\n")
    sys.stderr.flush()


@dataclass(frozen=True, slots=True)
class _PreparedTerminal:
    line: str
    correlation_id: str
    serialization_succeeded: bool


def _fallback_line(correlation_id: str) -> str:
    try:
        event_timestamp = timestamp()
    except Exception:  # noqa: BLE001 - fallback must not leak logging failures
        event_timestamp = "1970-01-01T00:00:00.000Z"
    event = {
        "timestamp": event_timestamp,
        "event_name": "triana.logging.rejected",
        "severity": "ERROR",
        "service": "triana-cli",
        "service_version": __version__,
        "command": "logging",
        "outcome": "REJECTED",
        "correlation_id": correlation_id,
        "duration_ms": 0,
        "code": "LOG_REDACTION_FAILED",
        "reason_code": "LOG_REDACTION_FAILED",
        "safe_message": "Terminal logging failed safely.",
    }
    return json.dumps(event, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def prepare_terminal(
    *,
    event_name: str,
    command: str,
    outcome: str,
    correlation_id: str,
    duration_ms: int,
    error: TrianaError | None = None,
    record_hash: str | None = None,
) -> _PreparedTerminal:
    try:
        event: dict[str, Any] = {
            "timestamp": timestamp(),
            "event_name": event_name,
            "severity": (
                "INFO"
                if outcome == "SUCCEEDED"
                else "ERROR"
                if error is not None and error.exit_code == 70
                else "WARN"
            ),
            "service": "triana-cli",
            "service_version": __version__,
            "command": command,
            "outcome": outcome,
            "correlation_id": correlation_id,
            "duration_ms": duration_ms,
        }
        if error is not None:
            event.update(error.public_fields())
            event["reason_code"] = error.code
        if record_hash is not None:
            event["record_hash"] = record_hash
        return _PreparedTerminal(
            line=_serialize_event(event),
            correlation_id=correlation_id,
            serialization_succeeded=True,
        )
    except Exception:  # noqa: BLE001 - unsafe event is suppressed
        return _PreparedTerminal(
            line=_fallback_line(correlation_id),
            correlation_id=correlation_id,
            serialization_succeeded=False,
        )


def emit_prepared(prepared: _PreparedTerminal) -> bool:
    """Emit one prepared line; never reintroduce the suppressed unsafe event."""
    try:
        _write_line(prepared.line)
    except Exception:  # noqa: BLE001 - logging cannot escape the CLI boundary
        try:
            if prepared.serialization_succeeded:
                _write_line(_fallback_line(prepared.correlation_id))
        except Exception:  # noqa: BLE001, S110 - logging cannot escape boundary
            pass
        return False
    return prepared.serialization_succeeded


def emit_terminal(
    *,
    event_name: str,
    command: str,
    outcome: str,
    correlation_id: str,
    duration_ms: int,
    error: TrianaError | None = None,
    record_hash: str | None = None,
) -> bool:
    prepared = prepare_terminal(
        event_name=event_name,
        command=command,
        outcome=outcome,
        correlation_id=correlation_id,
        duration_ms=duration_ms,
        error=error,
        record_hash=record_hash,
    )
    return emit_prepared(prepared)
