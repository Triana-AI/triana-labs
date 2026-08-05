"""Shared helpers for coercing provider payload values."""

from __future__ import annotations

from typing import Any


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def text_from_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        parts = [text_from_value(item) for item in value]
        return " ".join(part for part in parts if part) or None
    if isinstance(value, dict):
        if "text" in value:
            text = text_from_value(value.get("text"))
            if text:
                return text
        if "content" in value:
            text = text_from_value(value.get("content"))
            if text:
                return text
        parts = [text_from_value(item) for item in value.values()]
        return " ".join(part for part in parts if part) or None
    return None


def required_string(value: Any, field_name: str, *, context: str = "value") -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} missing {field_name}")
    return value


def float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "as_dict",
    "float_or_none",
    "optional_string",
    "required_string",
    "text_from_value",
]
