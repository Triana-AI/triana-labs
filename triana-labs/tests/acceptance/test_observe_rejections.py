"""Per-line rejection coverage for the closed PreviewTrace boundary."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from conftest import minimal_trace, parse_jsonl, write_jsonl

Mutator = Callable[[dict[str, Any]], Any]


@pytest.mark.parametrize("mode", ["mixed", "unknown", "public-custody"])
def test_privacy_class_refusals_are_atomic_and_publish_nothing(
    run_cli: Any,
    tmp_path: Path,
    mode: str,
) -> None:
    first = minimal_trace(trace_id="trace-one", source_trace_id="source-one")
    second = minimal_trace(trace_id="trace-two", source_trace_id="source-two")
    if mode == "mixed":
        second["privacy_class"] = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
        expected = "PRIVACY_CLASS_MISMATCH"
    elif mode == "unknown":
        first["privacy_class"] = "LOCAL_SENSITIVE"
        expected = "UNSUPPORTED_PRIVACY_CLASS"
    else:
        first["privacy_class"] = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
        second["privacy_class"] = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
        expected = "UNSUPPORTED_PRIVACY_CLASS"
    corpus = tmp_path / f"{mode}.jsonl"
    write_jsonl(corpus, [first, second])

    if mode == "public-custody":
        output = tmp_path / "public-output"
        result = run_cli("traces", "observe", corpus, "--out", output)
    else:
        with tempfile.TemporaryDirectory(
            prefix="triana-observer-refusal-", dir="/private/tmp"
        ) as root:
            output = Path(root) / "output"
            result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode != 0
    assert result.stderr_json()["reason_code"] == expected
    assert not output.exists()


def _delete(field: str) -> Mutator:
    def mutate(trace: dict[str, Any]) -> dict[str, Any]:
        del trace[field]
        return trace

    return mutate


def _set(field: str, value: Any) -> Mutator:
    def mutate(trace: dict[str, Any]) -> dict[str, Any]:
        trace[field] = value
        return trace

    return mutate


def _event_mutator(events: list[dict[str, Any]]) -> Mutator:
    def mutate(trace: dict[str, Any]) -> dict[str, Any]:
        trace["events"] = events
        return trace

    return mutate


SCHEMA_CASES: list[tuple[str, Mutator, str]] = [
    ("non-object-root", lambda trace: [], "SCHEMA_VALIDATION_FAILED"),
    ("missing-field", _delete("trace_id"), "SCHEMA_VALIDATION_FAILED"),
    ("unknown-field", _set("unexpected", True), "SCHEMA_VALIDATION_FAILED"),
    ("null-required", _set("trace_id", None), "SCHEMA_VALIDATION_FAILED"),
    ("wrong-type", _set("trace_id", 7), "SCHEMA_VALIDATION_FAILED"),
    ("boolean-version", _set("schema_version", True), "SCHEMA_VALIDATION_FAILED"),
    ("wrong-kind", _set("contract_kind", "other"), "SCHEMA_VALIDATION_FAILED"),
    ("unsupported-version", _set("schema_version", 2), "UNSUPPORTED_SCHEMA_VERSION"),
    (
        "unsupported-privacy",
        _set("privacy_class", "LOCAL_SENSITIVE"),
        "UNSUPPORTED_PRIVACY_CLASS",
    ),
    ("empty-trace-id", _set("trace_id", ""), "SCHEMA_VALIDATION_FAILED"),
    ("invalid-safe-id", _set("trace_id", "unsafe id"), "SCHEMA_VALIDATION_FAILED"),
    ("non-ascii-safe-id", _set("trace_id", "tracé"), "SCHEMA_VALIDATION_FAILED"),
    ("oversized-safe-id", _set("trace_id", "a" * 129), "SCHEMA_VALIDATION_FAILED"),
    ("empty-source-id", _set("source_trace_id", ""), "SCHEMA_VALIDATION_FAILED"),
    (
        "source-control",
        _set("source_trace_id", "unsafe\u0085source"),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "oversized-source-id",
        _set("source_trace_id", "é" * 257),
        "SCHEMA_VALIDATION_FAILED",
    ),
    ("empty-events", _set("events", []), "SCHEMA_VALIDATION_FAILED"),
    (
        "too-many-events",
        _event_mutator(
            [
                {
                    "sequence": index,
                    "event_kind": "SYSTEM_VISIBLE_MESSAGE",
                    "content": "x",
                }
                for index in range(1001)
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "sequence-gap",
        _event_mutator(
            [
                {"sequence": 0, "event_kind": "USER_MESSAGE", "content": "x"},
                {
                    "sequence": 2,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "y",
                    "is_final": False,
                },
            ]
        ),
        "IMPOSSIBLE_TRACE_STATE",
    ),
    (
        "sequence-negative",
        _event_mutator(
            [{"sequence": -1, "event_kind": "USER_MESSAGE", "content": "x"}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "sequence-too-large",
        _event_mutator(
            [
                {
                    "sequence": 9007199254740992,
                    "event_kind": "USER_MESSAGE",
                    "content": "x",
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "sequence-boolean",
        _event_mutator(
            [{"sequence": True, "event_kind": "USER_MESSAGE", "content": "x"}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "unknown-event-kind",
        _event_mutator([{"sequence": 0, "event_kind": "THOUGHT", "content": "x"}]),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "event-unknown-field",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": "x",
                    "hidden": "no",
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "empty-user-content",
        _event_mutator([{"sequence": 0, "event_kind": "USER_MESSAGE", "content": ""}]),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "user-content-control",
        _event_mutator(
            [{"sequence": 0, "event_kind": "USER_MESSAGE", "content": "a\u0000b"}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "user-content-c1-control",
        _event_mutator(
            [{"sequence": 0, "event_kind": "USER_MESSAGE", "content": "a\u0085b"}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "oversized-content",
        _event_mutator(
            [{"sequence": 0, "event_kind": "USER_MESSAGE", "content": "é" * 32769}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "assistant-final-not-bool",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "",
                    "is_final": 1,
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "invalid-call-id",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "bad id",
                    "tool_name": "tool",
                    "arguments": {},
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "invalid-tool-name",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "",
                    "arguments": {},
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "float-arguments",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": 1.5,
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "success-result-missing",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "SUCCEEDED",
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "success-result-with-error",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "SUCCEEDED",
                    "result": {},
                    "error_code": "NO",
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "error-result-missing-code",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "ERROR",
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "error-result-with-result",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "ERROR",
                    "error_code": "NO",
                    "result": {},
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "invalid-error-code",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "ERROR",
                    "error_code": "lowercase",
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "unknown-result-state",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TOOL_CALL",
                    "call_id": "call",
                    "tool_name": "tool",
                    "arguments": {},
                },
                {
                    "sequence": 1,
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call",
                    "result_state": "UNKNOWN",
                },
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "terminal-success-with-reason",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TERMINAL",
                    "terminal_state": "SUCCESS",
                    "reason_code": "NO",
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "terminal-error-missing-reason",
        _event_mutator(
            [{"sequence": 0, "event_kind": "TERMINAL", "terminal_state": "ERROR"}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "unknown-terminal-state",
        _event_mutator(
            [
                {
                    "sequence": 0,
                    "event_kind": "TERMINAL",
                    "terminal_state": "UNKNOWN",
                }
            ]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "terminal-state-list",
        _event_mutator(
            [{"sequence": 0, "event_kind": "TERMINAL", "terminal_state": []}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
    (
        "terminal-state-object",
        _event_mutator(
            [{"sequence": 0, "event_kind": "TERMINAL", "terminal_state": {}}]
        ),
        "SCHEMA_VALIDATION_FAILED",
    ),
]


@pytest.mark.parametrize(("name", "mutator", "expected_code"), SCHEMA_CASES)
def test_schema_and_value_rejections_are_safe_and_typed(
    name: str,
    mutator: Mutator,
    expected_code: str,
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / f"{name}.jsonl"
    output = tmp_path / f"{name}-output"
    value = mutator(deepcopy(minimal_trace()))
    write_jsonl(corpus, [value])

    result = run_cli("traces", "observe", corpus, "--out", output)

    if expected_code == "UNSUPPORTED_PRIVACY_CLASS":
        assert result.returncode == 4
        assert result.stderr_json()["reason_code"] == expected_code
        assert not output.exists()
        return
    assert result.returncode == 10
    rejection = parse_jsonl(output / "rejected_traces.jsonl")
    assert len(rejection) == 1
    assert rejection[0]["line_number"] == 1
    assert rejection[0]["code"] == expected_code
    assert set(rejection[0]) == {"line_number", "code", "json_pointer", "safe_message"}
    assert isinstance(rejection[0]["json_pointer"], str)
    assert isinstance(rejection[0]["safe_message"], str)
    assert rejection[0]["safe_message"]


@pytest.mark.parametrize(
    ("name", "payload", "expected_codes"),
    [
        ("blank", b" \t\r\n", {"BLANK_LINE"}),
        ("bom", b"\xef\xbb\xbf{}\n", {"BOM_FORBIDDEN"}),
        ("malformed", b'{"trace_id":\n', {"MALFORMED_JSON"}),
        (
            "duplicate-key",
            b'{"contract_kind":"preview_trace","contract_kind":"preview_trace"}\n',
            {"DUPLICATE_JSON_KEY"},
        ),
        (
            "nested-duplicate-key",
            b'{"outer":{"same":1,"same":2}}\n',
            {"DUPLICATE_JSON_KEY"},
        ),
        (
            "nonfinite-nan",
            b"NaN\n",
            {"MALFORMED_JSON"},
        ),
        (
            "nonfinite-infinity",
            b"Infinity\n",
            {"MALFORMED_JSON"},
        ),
        ("nonfinite-negative-infinity", b"-Infinity\n", {"MALFORMED_JSON"}),
        ("float-root", b"1.25\n", {"SCHEMA_VALIDATION_FAILED"}),
        ("exponent-root", b"1e3\n", {"SCHEMA_VALIDATION_FAILED"}),
    ],
)
def test_raw_boundary_rejections(
    name: str,
    payload: bytes,
    expected_codes: set[str],
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / f"{name}.jsonl"
    output = tmp_path / f"{name}-output"
    corpus.write_bytes(payload)

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert parse_jsonl(output / "rejected_traces.jsonl")[0]["code"] in expected_codes


def test_invalid_utf8_is_a_safe_line_rejection(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "invalid-utf8.jsonl"
    corpus.write_bytes(
        bytes.fromhex((fixture_root / "invalid_utf8.hex").read_text().strip())
    )
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert parse_jsonl(output / "rejected_traces.jsonl")[0]["code"] == "INVALID_UTF8"


def test_line_larger_than_one_mib_is_rejected_not_truncated(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "oversized-line.jsonl"
    corpus.write_bytes(b" " * (1024 * 1024) + b"\n")
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert parse_jsonl(output / "rejected_traces.jsonl")[0]["code"] == "LINE_TOO_LARGE"


def test_nesting_deeper_than_32_is_rejected(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "deep.jsonl"
    payload = b'{"x":' + (b"[" * 33) + b"0" + (b"]" * 33) + b"}\n"
    corpus.write_bytes(payload)
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert (
        parse_jsonl(output / "rejected_traces.jsonl")[0]["code"] == "NESTING_TOO_DEEP"
    )


IMPOSSIBLE_EVENT_CASES: list[tuple[str, list[dict[str, Any]]]] = [
    (
        "duplicate-call",
        [
            {
                "sequence": 0,
                "event_kind": "TOOL_CALL",
                "call_id": "call",
                "tool_name": "tool",
                "arguments": {},
            },
            {
                "sequence": 1,
                "event_kind": "TOOL_CALL",
                "call_id": "call",
                "tool_name": "tool",
                "arguments": {},
            },
        ],
    ),
    (
        "orphan-result",
        [
            {
                "sequence": 0,
                "event_kind": "TOOL_RESULT",
                "call_id": "call",
                "result_state": "ERROR",
                "error_code": "NO_CALL",
            }
        ],
    ),
    (
        "repeated-result",
        [
            {
                "sequence": 0,
                "event_kind": "TOOL_CALL",
                "call_id": "call",
                "tool_name": "tool",
                "arguments": {},
            },
            {
                "sequence": 1,
                "event_kind": "TOOL_RESULT",
                "call_id": "call",
                "result_state": "SUCCEEDED",
                "result": {},
            },
            {
                "sequence": 2,
                "event_kind": "TOOL_RESULT",
                "call_id": "call",
                "result_state": "ERROR",
                "error_code": "REPEATED",
            },
        ],
    ),
    (
        "multiple-final",
        [
            {
                "sequence": 0,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "a",
                "is_final": True,
            },
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "b",
                "is_final": True,
            },
        ],
    ),
    (
        "multiple-terminal",
        [
            {"sequence": 0, "event_kind": "TERMINAL", "terminal_state": "SUCCESS"},
            {
                "sequence": 1,
                "event_kind": "TERMINAL",
                "terminal_state": "ABORTED",
                "reason_code": "STOPPED",
            },
        ],
    ),
    (
        "terminal-not-last",
        [
            {"sequence": 0, "event_kind": "TERMINAL", "terminal_state": "SUCCESS"},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "after",
                "is_final": False,
            },
        ],
    ),
    (
        "final-after-terminal",
        [
            {"sequence": 0, "event_kind": "TERMINAL", "terminal_state": "SUCCESS"},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "after",
                "is_final": True,
            },
        ],
    ),
]


@pytest.mark.parametrize(("name", "events"), IMPOSSIBLE_EVENT_CASES)
def test_cross_event_invariants_reject_impossible_trace_state(
    name: str,
    events: list[dict[str, Any]],
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / f"{name}.jsonl"
    output = tmp_path / f"{name}-output"
    write_jsonl(corpus, [minimal_trace(events=events)])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert (
        parse_jsonl(output / "rejected_traces.jsonl")[0]["code"]
        == "IMPOSSIBLE_TRACE_STATE"
    )


@pytest.mark.parametrize(
    ("duplicate_field", "expected_code"),
    [
        ("trace_id", "DUPLICATE_TRACE_ID"),
        ("source_trace_id", "DUPLICATE_SOURCE_TRACE_ID"),
    ],
)
def test_later_duplicate_identity_is_rejected(
    duplicate_field: str,
    expected_code: str,
    run_cli: Any,
    tmp_path: Path,
) -> None:
    first = minimal_trace(trace_id="first", source_trace_id="source-first")
    second = minimal_trace(trace_id="second", source_trace_id="source-second")
    second[duplicate_field] = first[duplicate_field]
    corpus = tmp_path / f"duplicate-{duplicate_field}.jsonl"
    output = tmp_path / "output"
    write_jsonl(corpus, [first, second])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert parse_jsonl(output / "normalized_traces.jsonl") == [first]
    assert parse_jsonl(output / "rejected_traces.jsonl")[0]["code"] == expected_code


def test_rejected_line_does_not_reserve_either_identity(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    rejected = minimal_trace(trace_id="reusable", source_trace_id="reusable-source")
    rejected["unknown"] = "forces rejection"
    accepted = minimal_trace(trace_id="reusable", source_trace_id="reusable-source")
    corpus = tmp_path / "identity-reuse.jsonl"
    output = tmp_path / "output"
    write_jsonl(corpus, [rejected, accepted])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert parse_jsonl(output / "normalized_traces.jsonl") == [accepted]
    assert parse_jsonl(output / "rejected_traces.jsonl")[0]["line_number"] == 1
