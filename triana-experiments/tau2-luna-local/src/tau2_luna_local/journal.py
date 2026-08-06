from __future__ import annotations

import hashlib
import json
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TextIO

from .constants import EVENT_DOMAIN, EVENT_SCHEMA
from .serde import canonical_bytes


class EventJournal:
    """A durable, append-only, domain-separated event hash chain."""

    def __init__(self, path: Path, *, timestamp_ns: Callable[[], int] = time.time_ns) -> None:
        self.path = path
        self._timestamp_ns = timestamp_ns
        self._stream: TextIO | None = None
        self._sequence = 0
        self._previous_hash: str | None = None

    def __enter__(self) -> EventJournal:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("x", encoding="utf-8")
        return self

    def append(self, event_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        if self._stream is None:
            raise RuntimeError("event journal is not open")
        self._sequence += 1
        record: dict[str, Any] = {
            "schema_version": EVENT_SCHEMA,
            "sequence": self._sequence,
            "event_name": event_name,
            "timestamp_ns": self._timestamp_ns(),
            "previous_event_hash": self._previous_hash,
            "payload": payload,
        }
        record["event_hash"] = hashlib.sha256(EVENT_DOMAIN + canonical_bytes(record)).hexdigest()
        self._stream.write(canonical_bytes(record).decode("utf-8") + "\n")
        self._stream.flush()
        os.fsync(self._stream.fileno())
        self._previous_hash = str(record["event_hash"])
        return record

    def __exit__(self, _type: object, _value: object, _traceback: object) -> None:
        if self._stream is not None:
            self._stream.flush()
            self._stream.close()
            self._stream = None


def verify_event_chain(path: Path) -> dict[str, Any]:
    previous: str | None = None
    count = 0
    try:
        with path.open(encoding="utf-8") as stream:
            for expected_sequence, line in enumerate(stream, start=1):
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("event is not an object")
                actual_hash = record.get("event_hash")
                unhashed = dict(record)
                unhashed.pop("event_hash", None)
                expected_hash = hashlib.sha256(EVENT_DOMAIN + canonical_bytes(unhashed)).hexdigest()
                if record.get("sequence") != expected_sequence:
                    raise ValueError("non-monotonic or duplicate sequence")
                if record.get("previous_event_hash") != previous:
                    raise ValueError("previous hash mismatch")
                if actual_hash != expected_hash:
                    raise ValueError("event hash mismatch")
                previous = actual_hash
                count += 1
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return {"valid": False, "event_count": count, "reason": str(exc)}
    return {"valid": True, "event_count": count, "last_event_hash": previous}
