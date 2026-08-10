"""Deterministically project PreviewTrace JSONL through bounded redaction."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, cast

from triana_labs.contracts.traces import (
    LineRejection,
    parse_and_validate_line,
    validate_trace,
)

JsonObject = dict[str, Any]

_STRUCTURED_ORDER_IDENTIFIER = re.compile(
    r"(?=[A-Z0-9_-]{6,64}\Z)(?=[A-Z0-9_-]*[A-Z])(?=[A-Z0-9_-]*\d)"
    r"[A-Z0-9][A-Z0-9_-]*",
    re.IGNORECASE,
)
_ORDER_IDENTIFIER_KEY_PARTS = {
    "awb",
    "id",
    "identifier",
    "order",
    "reference",
    "shipment",
    "ticket",
    "tracking",
}
_PATTERNS: tuple[tuple[str, re.Pattern[str], int | None], ...] = (
    (
        "EMAIL",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        None,
    ),
    ("URL", re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE), None),
    ("IP", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), None),
    (
        "PHONE",
        re.compile(
            r"(?<![\w-])(?:\+\d[\d .()\-]{7,}\d|"
            r"\d{2,4}[ .()\-]\d{2,4}(?:[ .()\-]\d{2,4})+)(?![\w-])"
        ),
        None,
    ),
    (
        "BLITZ_IDENTIFIER",
        re.compile(r"(?<!\w)(?:GS|N[MN])\d{9,}(?!\w)", re.IGNORECASE),
        None,
    ),
    (
        "ORDER_ID",
        re.compile(
            r"\b(?:order|delivery|tracking|ticket|awb|shipment|reference|ref)\b"
            r"(?:\s+(?:id|number|no\.?))?\s*[:#-]?\s*"
            r"(?=[A-Z0-9_-]{5,}\b)(?=[A-Z0-9_-]*(?:\d|-))"
            r"[A-Z0-9][A-Z0-9_-]{4,}\b",
            re.IGNORECASE,
        ),
        None,
    ),
    (
        "ADDRESS",
        re.compile(
            r"\b(?:"
            r"(?:house|flat|plot)\s+"
            r"(?:(?:no\.?|number|#)\s*)?\d+[A-Z]?\s*,?\s*"
            r"(?:[A-Z0-9][A-Za-z0-9.'-]*\s*,?\s*){0,8}?"
            r"(?:colony|apartment|nagar|building|society|sector(?:\s+\d+[A-Z]?)?|"
            r"lane|road|street)"
            r"|\d+[A-Z]?\s+(?:[A-Z][A-Za-z.'-]*\s+){1,8}"
            r"(?:lane|road|street|sector\s+\d+[A-Z]?|phase\s+\d+[A-Z]?)"
            r")(?:\s+\d{6,})?\b",
            re.IGNORECASE,
        ),
        None,
    ),
    (
        "ADDRESS",
        re.compile(
            r"\b(?:near|opposite|behind)\s+"
            r"(?:[A-Z][A-Za-z.'-]*\s+){1,6}"
            r"(?:hospital|mall|school|college|university|temple|mosque|church|"
            r"bank|park|station|airport|hotel|market|store|office|tower|bridge|"
            r"circle|chowk|bus\s+stop)\b",
            re.IGNORECASE,
        ),
        None,
    ),
    ("HANDLE", re.compile(r"(?<!\w)@[A-Z0-9_.-]{2,}", re.IGNORECASE), None),
    ("POSTAL_CODE", re.compile(r"(?<!\d)\d{6}(?!\d)"), None),
    ("LONG_NUMBER", re.compile(r"(?<![\w.])\d{5,}(?![\w.])"), None),
    (
        "PERSON",
        re.compile(
            r"\b(?:my name is|i am|this is|name\s*(?::|-)\s*)\s*"
            r"([A-Z][A-Za-z.'-]*(?:\s+[A-Z][A-Za-z.'-]*){0,2})",
            re.IGNORECASE,
        ),
        1,
    ),
)
_PLACEHOLDER = re.compile(r"REDACTED_[A-Z_]+_\d+")
_LANGSMITH_SESSION_PREFIX = "langsmith://session/"
_TRIANA_LANGSMITH_TRACE_ID = re.compile(
    r"langsmith-session-[0-9A-F]{32}", re.IGNORECASE
)
_STRUCTURAL_EVENT_FIELDS = {"event_kind", "result_state", "terminal_state"}
_STRUCTURAL_EVENT_IDENTITY_FIELDS = {"call_id"}
_PSEUDONYMIZED_EXTERNAL_IDENTITY_CATEGORIES = {
    "LONG_NUMBER",
    "PHONE",
    "POSTAL_CODE",
}


@dataclass(frozen=True)
class RedactionFailure(Exception):
    """Carry one content-free refusal reason to the CLI boundary."""

    reason_code: str


@dataclass
class _Redactor:
    tokens: dict[tuple[str, str], str]
    next_ids: Counter[str]
    category_counts: Counter[str]

    @classmethod
    def create(cls) -> _Redactor:
        return cls(tokens={}, next_ids=Counter(), category_counts=Counter())

    def text(self, value: str) -> str:
        result = value
        for category, pattern, capture_group in _PATTERNS:
            replace = partial(
                self._replace, category=category, capture_group=capture_group
            )
            result = pattern.sub(replace, result)
        return result

    def _replace(
        self, match: re.Match[str], category: str, capture_group: int | None
    ) -> str:
        sensitive = match.group(capture_group or 0)
        token = self._token(category, sensitive)
        if capture_group is None:
            return token
        start, end = match.span(capture_group)
        base = match.start()
        whole = match.group(0)
        return whole[: start - base] + token + whole[end - base :]

    def _token(self, category: str, sensitive: str) -> str:
        key = (category, sensitive.casefold())
        token = self.tokens.get(key)
        if token is None:
            self.next_ids[category] += 1
            token = f"REDACTED_{category}_{self.next_ids[category]}"
            self.tokens[key] = token
        self.category_counts[category] += 1
        return token

    def value(self, value: Any, *, structured_order_identifier: bool = False) -> Any:
        if isinstance(value, str):
            if (
                structured_order_identifier
                and not _PLACEHOLDER.fullmatch(value)
                and _STRUCTURED_ORDER_IDENTIFIER.fullmatch(value)
            ):
                return self.text(f"order id {value}")
            return self.text(value)
        if isinstance(value, list):
            return [
                self.value(
                    item,
                    structured_order_identifier=structured_order_identifier,
                )
                for item in value
            ]
        if isinstance(value, dict):
            projected: JsonObject = {}
            for key, item in value.items():
                redacted_key = self.text(key)
                if redacted_key in projected:
                    raise RedactionFailure("REDACTION_OUTPUT_INVALID")
                projected[redacted_key] = self.value(
                    item,
                    structured_order_identifier=_is_order_identifier_key(key),
                )
            return projected
        return value


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if lf else b"")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _walk_strings(item)]
    if isinstance(value, dict):
        return [
            text for key, item in value.items() for text in (key, *_walk_strings(item))
        ]
    return []


def _is_order_identifier_key(key: str) -> bool:
    parts = {part for part in re.split(r"[^a-z0-9]+", key.casefold()) if part}
    return bool(parts & _ORDER_IDENTIFIER_KEY_PARTS)


def _count_structured_order_residuals(
    value: Any,
    counts: Counter[str],
    *,
    structured_order_identifier: bool = False,
    structural_event: bool = False,
) -> None:
    if isinstance(value, str):
        if (
            structured_order_identifier
            and not _PLACEHOLDER.fullmatch(value)
            and _STRUCTURED_ORDER_IDENTIFIER.fullmatch(value)
        ):
            counts["ORDER_ID"] += 1
        return
    if isinstance(value, list):
        for item in value:
            _count_structured_order_residuals(
                item,
                counts,
                structured_order_identifier=structured_order_identifier,
            )
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _count_structured_order_residuals(
                item,
                counts,
                structured_order_identifier=(
                    key not in _STRUCTURAL_EVENT_IDENTITY_FIELDS or not structural_event
                )
                and _is_order_identifier_key(key),
            )


def _residual_counts(traces: list[JsonObject]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for trace in traces:
        for text in _walk_strings(trace["events"]):
            _count_residuals(text, _PATTERNS, counts)
        for event in cast(list[JsonObject], trace["events"]):
            _count_structured_order_residuals(
                event,
                counts,
                structural_event=True,
            )
        for identity_key in ("trace_id", "source_trace_id"):
            identity = cast(str, trace[identity_key])
            _count_residuals(identity, _identity_patterns(identity), counts)
    return dict(sorted((key, count) for key, count in counts.items() if count))


def _count_residuals(
    text: str,
    patterns: tuple[tuple[str, re.Pattern[str], int | None], ...],
    counts: Counter[str],
) -> None:
    candidate = _PLACEHOLDER.sub("|", text)
    for category, pattern, _capture_group in patterns:
        counts[category] += len(tuple(pattern.finditer(candidate)))


def _identity_patterns(
    identity: str,
) -> tuple[tuple[str, re.Pattern[str], int | None], ...]:
    excluded_categories = {"ADDRESS", "BLITZ_IDENTIFIER", "ORDER_ID"}
    if (
        identity.startswith(_LANGSMITH_SESSION_PREFIX)
        and len(identity) > len(_LANGSMITH_SESSION_PREFIX)
    ) or _TRIANA_LANGSMITH_TRACE_ID.fullmatch(identity):
        excluded_categories.update({"POSTAL_CODE", "LONG_NUMBER"})
    return tuple(
        pattern for pattern in _PATTERNS if pattern[0] not in excluded_categories
    )


def _project_external_identity(identity: str, redactor: _Redactor) -> str:
    residuals: Counter[str] = Counter()
    _count_residuals(identity, _identity_patterns(identity), residuals)
    detected = {category for category, count in residuals.items() if count}
    if detected and detected <= _PSEUDONYMIZED_EXTERNAL_IDENTITY_CATEGORIES:
        return redactor.text(identity)
    return identity


def _project_trace(trace: JsonObject, redactor: _Redactor) -> JsonObject:
    projected = cast(JsonObject, dict(trace))
    for identity_key in ("trace_id", "source_trace_id"):
        projected[identity_key] = _project_external_identity(
            cast(str, trace[identity_key]), redactor
        )
    projected_events: list[JsonObject] = []
    for raw_event in cast(list[JsonObject], trace["events"]):
        event: JsonObject = {}
        for key, value in raw_event.items():
            if key in _STRUCTURAL_EVENT_FIELDS:
                event[key] = value
            else:
                event[key] = redactor.value(value)
        projected_events.append(event)
    projected["events"] = projected_events
    try:
        return validate_trace(projected).value
    except LineRejection as error:
        raise RedactionFailure("REDACTION_OUTPUT_INVALID") from error


def _load(source: bytes) -> list[JsonObject]:
    lines = source.splitlines()
    if not lines:
        raise RedactionFailure("REDACTION_INPUT_INVALID")
    traces: list[JsonObject] = []
    trace_ids: set[str] = set()
    source_ids: set[str] = set()
    for index, line in enumerate(lines):
        try:
            trace = parse_and_validate_line(line, first_line=index == 0).value
        except LineRejection as error:
            raise RedactionFailure("REDACTION_INPUT_INVALID") from error
        trace_id = cast(str, trace["trace_id"])
        source_id = cast(str, trace["source_trace_id"])
        if trace_id in trace_ids or source_id in source_ids:
            raise RedactionFailure("REDACTION_INPUT_INVALID")
        trace_ids.add(trace_id)
        source_ids.add(source_id)
        traces.append(trace)
    return traces


def _write_temporary(path: Path, payload: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def redact_preview_traces(
    source_path: Path, output_path: Path, audit_path: Path
) -> JsonObject:
    """Validate and publish a projection pair with handled-failure rollback."""

    if (
        source_path in {output_path, audit_path}
        or output_path == audit_path
        or output_path.exists()
        or audit_path.exists()
    ):
        raise RedactionFailure("REDACTION_PUBLICATION_REFUSED")
    try:
        source = source_path.read_bytes()
    except OSError as error:
        raise RedactionFailure("REDACTION_INPUT_INVALID") from error
    traces = _load(source)
    redactor = _Redactor.create()
    projected = [_project_trace(trace, redactor) for trace in traces]
    residuals = _residual_counts(projected)
    if residuals:
        raise RedactionFailure("REDACTION_RESIDUAL_IDENTIFIER")

    output = b"".join(_canonical(trace, lf=True) for trace in projected)
    input_event_count = sum(len(cast(list[Any], trace["events"])) for trace in traces)
    output_event_count = sum(
        len(cast(list[Any], trace["events"])) for trace in projected
    )
    audit: JsonObject = {
        "artifact_kind": "behavior_map_redaction_audit_v0",
        "schema_version": 0,
        "source_sha256": _sha256(source),
        "output_sha256": _sha256(output),
        "input_trace_count": len(traces),
        "output_trace_count": len(projected),
        "input_event_count": input_event_count,
        "output_event_count": output_event_count,
        "category_counts": dict(sorted(redactor.category_counts.items())),
        "residual_detector_counts": {},
        "warning": (
            "Deterministic pattern redaction is a bounded projection; it does not "
            "authorize provider egress or replace human privacy review."
        ),
    }
    audit_payload = _canonical(audit, lf=True)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        output_temporary = _write_temporary(output_path, output)
        try:
            audit_temporary = _write_temporary(audit_path, audit_payload)
        except BaseException:
            output_temporary.unlink(missing_ok=True)
            raise
        try:
            os.replace(output_temporary, output_path)
            try:
                os.replace(audit_temporary, audit_path)
            except BaseException:
                output_path.unlink(missing_ok=True)
                raise
        finally:
            output_temporary.unlink(missing_ok=True)
            audit_temporary.unlink(missing_ok=True)
    except RedactionFailure:
        raise
    except OSError as error:
        raise RedactionFailure("REDACTION_PUBLICATION_REFUSED") from error
    return audit
