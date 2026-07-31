"""Domain-set normalization, canonical JSON, and identity hashing."""

from __future__ import annotations

import copy
import hashlib
import json
from collections import OrderedDict
from typing import Any

SET_KEYS: dict[str, str | tuple[str, ...] | None] = {
    "applicability_conditions": "statement_id",
    "expected_behavior": "statement_id",
    "prohibited_behavior": "statement_id",
    "allowed_alternatives": "statement_id",
    "capabilities": None,
    "source_evidence": "reference_id",
    "evidence_references": "reference_id",
    "unresolved_difference_references": "reference_id",
    "evidence_requirements": "requirement_id",
    "customer_evaluator_results": ("evaluator_id", "check_id", "result_id"),
    "gaps": "gap_id",
    "record_gaps": "gap_id",
    "components": "component_kind",
    "reason_codes": None,
    "flags": None,
    "pattern_flags": None,
    "gap_ids": None,
}


def set_sort_key(field: str, item: Any) -> Any:
    key = SET_KEYS[field]
    if key is None:
        return item
    if isinstance(key, tuple):
        return tuple(item[part] for part in key)
    return item[key]


def normalize_sets(
    value: Any, field: str | None = None, *, opaque: bool = False
) -> Any:
    """Return a deep copy with only declared set-like arrays normalized."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            child_opaque = (
                opaque
                or (key == "arguments" and value.get("event_kind") == "TOOL_CALL")
                or (
                    key == "result"
                    and value.get("event_kind") == "TOOL_RESULT"
                    and value.get("result_state") == "SUCCEEDED"
                )
            )
            result[key] = normalize_sets(item, key, opaque=child_opaque)
        return result
    if isinstance(value, list):
        items = [normalize_sets(item, opaque=opaque) for item in value]
        if not opaque and field in SET_KEYS:
            items.sort(key=lambda item: set_sort_key(field, item))
        return items
    return copy.deepcopy(value)


def _jcs_order(value: Any) -> Any:
    if isinstance(value, dict):
        return OrderedDict(
            (
                key,
                _jcs_order(value[key]),
            )
            for key in sorted(
                value,
                key=lambda item: item.encode("utf-16-be", errors="surrogatepass"),
            )
        )
    if isinstance(value, list):
        return [_jcs_order(item) for item in value]
    return value


def canonical_bytes(value: Any) -> bytes:
    """Serialize an accepted value to the Slice 0A JCS subset."""
    return json.dumps(
        _jcs_order(normalize_sets(value)),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def domain_hash(identity_kind: str, value: Any, schema_version: int = 1) -> str:
    """Hash canonical bytes with Triana's frozen domain separator."""
    preimage = (
        b"triana\x00"
        + identity_kind.encode("utf-8")
        + b"\x00v"
        + str(schema_version).encode("ascii")
        + b"\x00"
        + canonical_bytes(value)
    )
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def without_field(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(field, None)
    return result
