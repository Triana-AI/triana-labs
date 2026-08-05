"""Shared JSON type aliases."""

from __future__ import annotations

import json as _json
from typing import Any, TypeAlias


JsonValue: TypeAlias = (
    str
    | int
    | float
    | bool
    | None
    | dict[str, "JsonValue"]
    | list["JsonValue"]
)
JsonObject: TypeAlias = dict[str, JsonValue]


def canonical_json(value: Any) -> str:
    return _json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def json_safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def json_safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return [
            json_safe_value(item)
            for item in sorted(value, key=lambda item: str(item))
        ]
    if isinstance(value, (list, tuple)):
        return [json_safe_value(item) for item in value]
    return str(value)


__all__ = [
    "JsonObject",
    "JsonValue",
    "canonical_json",
    "json_safe_scalar",
    "json_safe_value",
]
