"""Route 1 (`NATIVE_SIGNAL`) executor: a small, closed, JSON expression AST that
computes a measurement's value from a normalized trace bundle without any LLM
call. See internal/REPEATABLE_MEASUREMENT_EXECUTION_RESEARCH_2026-07-19.md,
"Route 1: NATIVE_SIGNAL".

Programs are validated JSON data (dicts of dicts), never source code. The
operation set is deliberately small: `field`, `exists`, `eq`, `in_set`,
`count`, `all_equal`, `and`, `or`, `not`, `const`, wrapped by a top-level
`map_to_label` that reduces the evaluated value to one of a closed set of
labels.

Any node whose evaluation depends on a missing path, or on a `state_after`
that is `None`, evaluates to the internal ABSENT marker, which propagates
through every combinator. A program that resolves to ABSENT never guesses a
label: `evaluate_program` reports `status: "EVIDENCE_ABSENT"` instead.
"""

from __future__ import annotations

import json
import re
from typing import Any

from agentagon.evals.trace_bundle import NormalizedTraceBundle

NATIVE_SIGNAL_SCHEMA_VERSION = "native-signal-program-v0.1"
MAX_DEPTH = 8
_NODE_OPS = frozenset(
    {"const", "field", "exists", "eq", "in_set", "count", "all_equal", "and", "or", "not"}
)
_PATH_SEGMENT = r"[A-Za-z0-9_]+(?:\[\])?"
_PATH_RE = re.compile(rf"^{_PATH_SEGMENT}(?:\.{_PATH_SEGMENT})*$")


class NativeSignalValidationError(ValueError):
    """A NATIVE_SIGNAL program is malformed: unknown op, missing key, bad path, etc."""


class _Absent:
    """Sentinel: a field path did not resolve, or resolved through a None."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return "ABSENT"


ABSENT = _Absent()


def compile_program(program: dict[str, Any]) -> dict[str, Any]:
    """Validate a program once, up front, before evaluating it against any trace."""
    validate_program(program)
    return program


def validate_program(program: Any) -> None:
    if not isinstance(program, dict):
        raise NativeSignalValidationError("program must be a JSON object")
    if program.get("op") != "map_to_label":
        raise NativeSignalValidationError("top-level program must be a 'map_to_label' node")

    labels = program.get("labels")
    if not isinstance(labels, list) or not labels or not all(isinstance(l, str) and l for l in labels):
        raise NativeSignalValidationError("map_to_label requires a non-empty 'labels' list of strings")
    label_set = set(labels)
    if len(label_set) != len(labels):
        raise NativeSignalValidationError("map_to_label 'labels' must not contain duplicates")

    default = program.get("default")
    if default not in label_set:
        raise NativeSignalValidationError("map_to_label 'default' must be one of 'labels'")

    cases = program.get("cases")
    if not isinstance(cases, list) or not cases:
        raise NativeSignalValidationError("map_to_label requires a non-empty 'cases' list")
    for case in cases:
        if not isinstance(case, dict):
            raise NativeSignalValidationError("each case must be a JSON object")
        values = case.get("values")
        if not isinstance(values, list) or not values:
            raise NativeSignalValidationError("each case requires a non-empty 'values' list")
        if case.get("label") not in label_set:
            raise NativeSignalValidationError("each case 'label' must be one of 'labels'")

    value_node = program.get("value")
    if not isinstance(value_node, dict):
        raise NativeSignalValidationError("map_to_label requires a 'value' node")
    _validate_node(value_node, depth=0)


def _validate_node(node: Any, depth: int) -> None:
    if depth > MAX_DEPTH:
        raise NativeSignalValidationError(f"program exceeds max nesting depth {MAX_DEPTH}")
    if not isinstance(node, dict):
        raise NativeSignalValidationError("every expression node must be a JSON object")
    op = node.get("op")
    if op not in _NODE_OPS:
        raise NativeSignalValidationError(f"unsupported op: {op!r}")

    if op == "const":
        if "value" not in node:
            raise NativeSignalValidationError("const requires 'value'")
    elif op == "field":
        path = node.get("path")
        if not isinstance(path, str) or not path or not _PATH_RE.match(path):
            raise NativeSignalValidationError(f"invalid field path: {path!r}")
    elif op in ("exists", "not", "count"):
        if "value" not in node:
            raise NativeSignalValidationError(f"{op} requires 'value'")
        _validate_node(node["value"], depth + 1)
    elif op == "all_equal":
        if "value" not in node:
            raise NativeSignalValidationError("all_equal requires 'value'")
        _validate_node(node["value"], depth + 1)
        min_count = node.get("min_count", 2)
        if not isinstance(min_count, int) or isinstance(min_count, bool) or min_count < 1:
            raise NativeSignalValidationError("all_equal 'min_count' must be a positive integer")
    elif op == "eq":
        for key in ("left", "right"):
            if key not in node:
                raise NativeSignalValidationError(f"eq requires '{key}'")
            _validate_node(node[key], depth + 1)
    elif op == "in_set":
        if "value" not in node:
            raise NativeSignalValidationError("in_set requires 'value'")
        _validate_node(node["value"], depth + 1)
        if not isinstance(node.get("set"), list) or not node["set"]:
            raise NativeSignalValidationError("in_set requires a non-empty 'set' list")
    elif op in ("and", "or"):
        values = node.get("values")
        if not isinstance(values, list) or not values:
            raise NativeSignalValidationError(f"{op} requires a non-empty 'values' list")
        for child in values:
            _validate_node(child, depth + 1)


def evaluate_program(program: dict[str, Any], bundle: NormalizedTraceBundle) -> dict[str, Any]:
    """Evaluate a validated program against one normalized trace bundle.

    Returns {"value": LABEL | None, "status": "OK" | "EVIDENCE_ABSENT", "evidence_ref": str}.
    Never raises for missing data; only a malformed program (caught by validate_program /
    compile_program before this point) is an error.
    """
    ctx = _bundle_context(bundle)
    value_node = program["value"]
    resolved = _eval_node(value_node, ctx, depth=0)
    evidence_path = _describe_node(value_node)
    if resolved is ABSENT:
        return {"value": None, "status": "EVIDENCE_ABSENT", "evidence_ref": f"{evidence_path} = <ABSENT>"}
    label = program["default"]
    for case in program["cases"]:
        if _case_matches(case["values"], resolved):
            label = case["label"]
            break
    evidence_value = json.dumps(resolved, sort_keys=True, default=str)
    return {"value": label, "status": "OK", "evidence_ref": f"{evidence_path} = {evidence_value}"}


def _bundle_context(bundle: NormalizedTraceBundle) -> dict[str, Any]:
    return {
        "case_id": bundle.case_id,
        "trial_id": bundle.trial_id,
        "session_id": bundle.session_id,
        "release_id": bundle.release_id,
        "state_after": bundle.state_after_ref,
        "state_before": bundle.state_before_ref,
        "execution_status": bundle.execution.status.value,
        "events": [
            {
                "sequence": event.sequence,
                "kind": event.kind.value,
                "name": event.name,
                "content": event.content,
                "data": event.data,
            }
            for event in bundle.events
        ],
    }


def _eval_node(node: dict[str, Any], ctx: dict[str, Any], depth: int) -> Any:
    op = node["op"]
    if op == "const":
        return node["value"]
    if op == "field":
        return _resolve_path(node["path"], ctx)
    if op == "exists":
        return _eval_node(node["value"], ctx, depth + 1) is not ABSENT
    if op == "not":
        value = _eval_node(node["value"], ctx, depth + 1)
        return ABSENT if value is ABSENT else not bool(value)
    if op == "count":
        value = _eval_node(node["value"], ctx, depth + 1)
        if value is ABSENT or not isinstance(value, list):
            return ABSENT
        return len(value)
    if op == "all_equal":
        value = _eval_node(node["value"], ctx, depth + 1)
        min_count = node.get("min_count", 2)
        if value is ABSENT or not isinstance(value, list) or len(value) < min_count:
            return ABSENT
        first = value[0]
        return all(item == first for item in value)
    if op == "eq":
        left = _eval_node(node["left"], ctx, depth + 1)
        right = _eval_node(node["right"], ctx, depth + 1)
        if left is ABSENT or right is ABSENT:
            return ABSENT
        return left == right
    if op == "in_set":
        value = _eval_node(node["value"], ctx, depth + 1)
        if value is ABSENT:
            return ABSENT
        return _case_matches(node["set"], value)
    if op in ("and", "or"):
        values = [_eval_node(child, ctx, depth + 1) for child in node["values"]]
        if any(value is ABSENT for value in values):
            return ABSENT
        return all(bool(value) for value in values) if op == "and" else any(bool(value) for value in values)
    raise NativeSignalValidationError(f"unsupported op: {op!r}")  # unreachable after validate_program


def _resolve_path(path: str, ctx: dict[str, Any]) -> Any:
    return _resolve_segments(path.split("."), ctx)


def _resolve_segments(segments: list[str], value: Any) -> Any:
    if not segments:
        return value
    if not isinstance(value, dict):
        return ABSENT
    segment, rest = segments[0], segments[1:]
    is_list_segment = segment.endswith("[]")
    key = segment[:-2] if is_list_segment else segment
    if key not in value:
        return ABSENT
    child = value[key]
    if child is None:
        return ABSENT
    if not is_list_segment:
        return _resolve_segments(rest, child)
    if not isinstance(child, list):
        return ABSENT
    collected = []
    for item in child:
        resolved = _resolve_segments(rest, item)
        if resolved is not ABSENT:
            collected.append(resolved)
    return collected


def _case_matches(allowed: list[Any], resolved: Any) -> bool:
    if isinstance(resolved, list):
        return any(_values_equal(item, candidate) for item in resolved for candidate in allowed)
    return any(_values_equal(resolved, candidate) for candidate in allowed)


def _values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, str) and isinstance(right, str):
        return left.lower() == right.lower()
    return left == right


def _describe_node(node: dict[str, Any]) -> str:
    op = node["op"]
    if op == "const":
        return f"const:{node['value']!r}"
    if op == "field":
        return f"field:{node['path']}"
    if op in ("exists", "not", "count"):
        return f"{op}({_describe_node(node['value'])})"
    if op == "all_equal":
        return f"all_equal({_describe_node(node['value'])}, min_count={node.get('min_count', 2)})"
    if op == "eq":
        return f"eq({_describe_node(node['left'])}, {_describe_node(node['right'])})"
    if op == "in_set":
        return f"in_set({_describe_node(node['value'])}, set={node['set']})"
    if op in ("and", "or"):
        return f"{op}({', '.join(_describe_node(child) for child in node['values'])})"
    return op
