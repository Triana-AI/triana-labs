"""Strict scalar domains from the Slice 0A wire contract."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, StringConstraints, WithJsonSchema

MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _utf8_bounded(value: str, maximum: int, *, allow_lf: bool = False) -> str:
    encoded = value.encode("utf-8")
    if not 1 <= len(encoded) <= maximum:
        raise ValueError("string length is outside its UTF-8 byte domain")
    for character in value:
        codepoint = ord(character)
        if (codepoint < 32 and not (allow_lf and character == "\n")) or (
            127 <= codepoint <= 159
        ):
            raise ValueError("string contains a forbidden control character")
    return value


def _safe_label(value: str) -> str:
    return _utf8_bounded(value, 256)


def _external_id(value: str) -> str:
    return _utf8_bounded(value, 512)


def _statement(value: str) -> str:
    return _utf8_bounded(value, 4096, allow_lf=True)


def _local_content(value: str) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) > 1_048_576:
        raise ValueError("local content exceeds its UTF-8 byte domain")
    for character in value:
        codepoint = ord(character)
        if (codepoint < 32 and character != "\n") or 127 <= codepoint <= 159:
            raise ValueError("local content contains a forbidden control character")
    return value


_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")


def _canonical_decimal(value: str) -> str:
    if len(value.encode("ascii", errors="ignore")) != len(value) or len(value) > 128:
        raise ValueError("decimal is outside its ASCII domain")
    if not _DECIMAL.fullmatch(value) or value == "-0":
        raise ValueError("decimal is not canonical")
    return value


_TIMESTAMP = re.compile(
    r"(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T"
    r"(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
    r"\.(?P<millisecond>[0-9]{3})Z\Z"
)


def _timestamp(value: str) -> str:
    match = _TIMESTAMP.fullmatch(value)
    if match is None or match.group("second") == "60":
        raise ValueError("timestamp is not canonical UTC milliseconds")
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("timestamp is not a valid calendar time") from error
    return value


_POINTER_TOKEN = re.compile(r"(?:[^~]|~[01])*\Z")


def _json_pointer(value: str) -> str:
    if len(value.encode("utf-8")) > 1024:
        raise ValueError("JSON Pointer is too long")
    if value and (
        not value.startswith("/")
        or any(_POINTER_TOKEN.fullmatch(part) is None for part in value[1:].split("/"))
    ):
        raise ValueError("JSON Pointer is invalid")
    return value


_FIXED_RATE = re.compile(r"(?:0\.[0-9]{6}|1\.000000)\Z")
_FIXED_MOVEMENT = re.compile(r"-?(?:0\.[0-9]{6}|1\.000000)\Z")


def _fixed_rate(value: str) -> str:
    if _FIXED_RATE.fullmatch(value) is None:
        raise ValueError("fixed rate is outside 0.000000..1.000000")
    return value


def _fixed_movement(value: str) -> str:
    if _FIXED_MOVEMENT.fullmatch(value) is None or value == "-0.000000":
        raise ValueError("fixed movement is outside -1.000000..1.000000")
    return value


SafeId = Annotated[
    str,
    StringConstraints(
        strict=True,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$",
    ),
]
ExternalId = Annotated[
    str, StringConstraints(strict=True), AfterValidator(_external_id)
]
SafeCode = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^[A-Z][A-Z0-9_]{0,63}$"),
]
SafeLabel = Annotated[str, StringConstraints(strict=True), AfterValidator(_safe_label)]
StatementText = Annotated[
    str, StringConstraints(strict=True), AfterValidator(_statement)
]
LocalContent = Annotated[
    str, StringConstraints(strict=True), AfterValidator(_local_content)
]
CanonicalDecimal = Annotated[
    str, StringConstraints(strict=True), AfterValidator(_canonical_decimal)
]
Timestamp = Annotated[str, StringConstraints(strict=True), AfterValidator(_timestamp)]
JsonPointer = Annotated[
    str, StringConstraints(strict=True), AfterValidator(_json_pointer)
]
FixedRate = Annotated[
    str,
    StringConstraints(strict=True),
    AfterValidator(_fixed_rate),
    WithJsonSchema(
        {"type": "string", "pattern": r"^(?:0\.[0-9]{6}|1\.000000)$"},
        mode="validation",
    ),
]
FixedMovement = Annotated[
    str,
    StringConstraints(strict=True),
    AfterValidator(_fixed_movement),
    WithJsonSchema(
        {
            "type": "string",
            "pattern": (
                r"^(?:-1\.000000|-0\.(?!000000)[0-9]{6}|"
                r"0\.[0-9]{6}|1\.000000)$"
            ),
        },
        mode="validation",
    ),
]
Digest = Annotated[
    str,
    StringConstraints(strict=True),
    WithJsonSchema(
        {"type": "string", "pattern": r"^sha256:[0-9a-f]{64}$"},
        mode="validation",
    ),
]
SafeInt = Annotated[int, Field(strict=True, ge=0, le=MAX_SAFE_INTEGER)]
PositiveInt = Annotated[int, Field(strict=True, ge=1, le=MAX_SAFE_INTEGER)]
Index = SafeInt
DurationMs = SafeInt
SchemaVersion = Literal[1]
