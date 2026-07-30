"""Strict raw UTF-8 JSON and resource boundary."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from triana.core.errors import TrianaError

MAX_INPUT_BYTES = 16_777_216
MAX_DEPTH = 64
MAX_STRING_BYTES = 1_048_576
COLLECTION_LIMITS = {
    "events": 10_000,
    "trials": 1_000,
    "assertion_results": 1_000,
    "customer_evaluator_results": 1_000,
    "gaps": 1_000,
    "record_gaps": 1_000,
    "entries": 1_000,
    "source_evidence": 100,
    "messages": 100,
    "applicability_conditions": 100,
    "expected_behavior": 100,
    "prohibited_behavior": 100,
    "allowed_alternatives": 100,
    "evidence_references": 100,
    "unresolved_difference_references": 100,
    "evidence_requirements": 100,
    "reason_codes": 100,
    "gap_ids": 100,
    "components": 8,
    "capabilities": 9,
    "flags": 3,
    "pattern_flags": 3,
}


@dataclass(frozen=True, slots=True)
class NonIntegerNumber:
    lexeme: str


class DuplicateKeyError(ValueError):
    pass


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError
        result[key] = value
    return result


def _resource_walk(
    value: Any,
    depth: int = 1,
    field: str | None = None,
    *,
    opaque: bool = False,
) -> None:
    if depth > MAX_DEPTH:
        raise TrianaError("NESTING_TOO_DEEP", "JSON nesting exceeds the limit.")
    if isinstance(value, str):
        try:
            encoded = value.encode("utf-8")
        except UnicodeEncodeError as error:
            raise TrianaError(
                "INVALID_UTF8", "Input contains invalid Unicode."
            ) from error
        if len(encoded) > MAX_STRING_BYTES:
            raise TrianaError("STRING_TOO_LARGE", "A decoded string exceeds the limit.")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            try:
                key_bytes = key.encode("utf-8")
            except UnicodeEncodeError as error:
                raise TrianaError(
                    "INVALID_UTF8", "An object key contains invalid Unicode."
                ) from error
            if len(key_bytes) > MAX_STRING_BYTES:
                raise TrianaError(
                    "STRING_TOO_LARGE", "An object key exceeds the limit."
                )
            child_opaque = (
                opaque
                or (key == "arguments" and value.get("event_kind") == "TOOL_CALL")
                or (
                    key == "result"
                    and value.get("event_kind") == "TOOL_RESULT"
                    and value.get("result_state") == "SUCCEEDED"
                )
            )
            _resource_walk(
                item,
                depth + int(isinstance(item, (dict, list))),
                key,
                opaque=child_opaque,
            )
        return
    if isinstance(value, list):
        if (
            not opaque
            and field in COLLECTION_LIMITS
            and len(value) > COLLECTION_LIMITS[field]
        ):
            raise TrianaError("COLLECTION_TOO_LARGE", "A collection exceeds its limit.")
        for item in value:
            _resource_walk(
                item,
                depth + int(isinstance(item, (dict, list))),
                opaque=opaque,
            )


def parse_json(raw: bytes) -> Any:
    """Parse bytes without coercion, duplicate keys, or resource ambiguity."""
    if len(raw) > MAX_INPUT_BYTES:
        raise TrianaError("INPUT_TOO_LARGE", "Input exceeds the byte limit.")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise TrianaError("BOM_FORBIDDEN", "A UTF-8 BOM is not allowed.")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise TrianaError("INVALID_UTF8", "Input is not valid UTF-8.") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object,
            parse_float=NonIntegerNumber,
            parse_int=lambda lexeme: (
                NonIntegerNumber(lexeme) if lexeme == "-0" else int(lexeme)
            ),
            parse_constant=NonIntegerNumber,
        )
    except DuplicateKeyError as error:
        raise TrianaError(
            "DUPLICATE_JSON_KEY", "Input contains a duplicate object key."
        ) from error
    except (json.JSONDecodeError, ValueError) as error:
        raise TrianaError("MALFORMED_JSON", "Input is not valid JSON.") from error
    _resource_walk(value)
    return value
