"""Closed JSON, hashing, configuration, and bounded-value primitives."""

from __future__ import annotations

import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

Json = dict[str, Any]
PREFIX = b"triana.labs.case-factory.v1."
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$")
LOCAL_KEY = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
SAFE_CODE = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
SECRET_PATTERNS = (
    re.compile(
        rb"(?i)(api[_-]?key|authorization|bearer|password|secret)\s*[:=]\s*\S{8,}"
    ),
    re.compile(rb"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
    re.compile(rb"(?i)\bsk-[A-Za-z0-9_-]{16,}\b"),
)
ID_PREFIX = {
    "citation": "citation-",
    "claim": "claim-",
    "persona": "persona-",
    "intent": "intent-",
    "turn-policy": "turn-policy-",
    "case": "case-",
    "attempt": "attempt-",
    "duplicate-cluster": "duplicate-cluster-",
    "blind-item": "blind-",
}


class Invalid(ValueError):
    pass


def canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def domain_hash(kind: str, value: Any) -> str:
    digest = hashlib.sha256(PREFIX + kind.encode() + b"\0" + canonical(value))
    return f"sha256:{digest.hexdigest()}"


def byte_hash(kind: str, payload: bytes) -> str:
    digest = hashlib.sha256(PREFIX + kind.encode() + b"\0" + payload)
    return f"sha256:{digest.hexdigest()}"


def artifact_hash(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def compact_id(kind: str, value: Any) -> str:
    return ID_PREFIX[kind] + domain_hash(kind, value)[7:23]


def strict_json(payload: bytes, *, allow_decimal: bool = False) -> Any:
    if payload.startswith(b"\xef\xbb\xbf"):
        raise Invalid
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_float=Decimal if allow_decimal else _reject_float,
            parse_constant=_reject_float,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, Invalid) as error:
        raise Invalid from error
    if depth(value) > 32:
        raise Invalid
    return value


def _unique(pairs: list[tuple[str, Any]]) -> Json:
    result: Json = {}
    for key, value in pairs:
        if key in result:
            raise Invalid
        result[key] = value
    return result


def _reject_float(_: str) -> Decimal:
    raise Invalid


def depth(value: Any) -> int:
    if isinstance(value, dict):
        return 1 + max((depth(item) for item in value.values()), default=0)
    if isinstance(value, list):
        return 1 + max((depth(item) for item in value), default=0)
    return 0


def bounded_text(value: Any, maximum: int, *, empty: bool = False) -> bool:
    if not isinstance(value, str):
        return False
    if any(
        (ord(char) < 32 and char != "\n") or 127 <= ord(char) <= 159 for char in value
    ):
        return False
    try:
        size = len(value.encode())
    except UnicodeError:
        return False
    return (0 if empty else 1) <= size <= maximum


def read_regular(path: Path, limit: int, reason: str) -> bytes:
    try:
        metadata = path.lstat()
        if path.is_symlink() or not path.is_file():
            raise OSError
    except OSError as error:
        raise Invalid(reason) from error
    if metadata.st_size > limit:
        raise Invalid("INPUT_TOO_LARGE")
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise Invalid(reason) from error
    if len(payload) > limit:
        raise Invalid("INPUT_TOO_LARGE")
    return payload


def read_object_file(path: Path, limit: int, reason: str) -> bytes:
    payload = read_regular(path, limit, reason)
    if payload.count(b"\n") != 1 or not payload.endswith(b"\n"):
        if payload.count(b"\n") > 1:
            raise Invalid("INPUT_TOO_LARGE")
        raise Invalid(reason)
    return payload


def contains_secret(payload: bytes, sentinels: list[bytes]) -> bool:
    return any(item in payload for item in sentinels) or any(
        pattern.search(payload) for pattern in SECRET_PATTERNS
    )
