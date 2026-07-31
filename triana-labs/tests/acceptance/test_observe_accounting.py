"""Accounting, eligibility, and closed-profile acceptance behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_artifact_bundle, minimal_trace, parse_jsonl, write_jsonl

ELIGIBILITY_CASES: list[tuple[str, list[dict[str, Any]], bool]] = [
    (
        "user-then-assistant",
        [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": "x"},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "y",
                "is_final": False,
            },
        ],
        True,
    ),
    (
        "user-then-tool",
        [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": "x"},
            {
                "sequence": 1,
                "event_kind": "TOOL_CALL",
                "call_id": "call",
                "tool_name": "tool",
                "arguments": {},
            },
        ],
        True,
    ),
    (
        "assistant-before-user-only",
        [
            {
                "sequence": 0,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "y",
                "is_final": False,
            },
            {"sequence": 1, "event_kind": "USER_MESSAGE", "content": "x"},
        ],
        False,
    ),
    (
        "tool-before-user-only",
        [
            {
                "sequence": 0,
                "event_kind": "TOOL_CALL",
                "call_id": "call",
                "tool_name": "tool",
                "arguments": {},
            },
            {"sequence": 1, "event_kind": "USER_MESSAGE", "content": "x"},
        ],
        False,
    ),
    (
        "user-only",
        [{"sequence": 0, "event_kind": "USER_MESSAGE", "content": "x"}],
        False,
    ),
    (
        "system-only",
        [
            {
                "sequence": 0,
                "event_kind": "SYSTEM_VISIBLE_MESSAGE",
                "content": "x",
            }
        ],
        False,
    ),
]


@pytest.mark.parametrize(("name", "events", "eligible"), ELIGIBILITY_CASES)
def test_case_generation_eligibility_is_exactly_mechanical(
    name: str,
    events: list[dict[str, Any]],
    eligible: bool,
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / f"{name}.jsonl"
    output = tmp_path / f"{name}-output"
    write_jsonl(corpus, [minimal_trace(events=events)])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 0
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile["case_generation_eligible_count"] == int(eligible)


def test_every_physical_line_is_counted_exactly_once(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    valid = json.dumps(minimal_trace(), separators=(",", ":"), sort_keys=True)
    corpus = tmp_path / "accounting.jsonl"
    corpus.write_bytes(
        valid.encode()
        + b"\n"
        + b"\n"
        + b"{malformed}\n"
        + valid.replace("trace-minimal", "trace-second")
        .replace("source-minimal", "source-second")
        .encode()
    )
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile["input_count"] == 4
    assert profile["accepted_count"] == 2
    assert profile["rejected_count"] == 2
    assert (
        profile["input_count"] == profile["accepted_count"] + profile["rejected_count"]
    )
    assert [
        item["line_number"] for item in parse_jsonl(output / "rejected_traces.jsonl")
    ] == [
        2,
        3,
    ]


def test_closed_count_maps_include_required_zeroes_and_sort_dynamic_keys(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    first = minimal_trace(
        trace_id="one",
        source_trace_id="source-one",
        events=[
            {
                "sequence": 0,
                "event_kind": "TOOL_CALL",
                "call_id": "z",
                "tool_name": "z_tool",
                "arguments": {},
            }
        ],
    )
    second = minimal_trace(
        trace_id="two",
        source_trace_id="source-two",
        events=[
            {
                "sequence": 0,
                "event_kind": "TOOL_CALL",
                "call_id": "a",
                "tool_name": "a_tool",
                "arguments": {},
            }
        ],
    )
    corpus = tmp_path / "counts.jsonl"
    output = tmp_path / "output"
    write_jsonl(corpus, [first, second])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 0
    profile_bytes = (output / "corpus_profile.json").read_bytes()
    profile = json.loads(profile_bytes)
    assert profile["event_kind_counts"] == {
        "ASSISTANT_MESSAGE": 0,
        "SYSTEM_VISIBLE_MESSAGE": 0,
        "TERMINAL": 0,
        "TOOL_CALL": 2,
        "TOOL_RESULT": 0,
        "USER_MESSAGE": 0,
    }
    assert profile["terminal_state_counts"] == {
        "ABORTED": 0,
        "ERROR": 0,
        "SUCCESS": 0,
    }
    assert list(profile["tool_call_counts"]) == ["a_tool", "z_tool"]
    assert profile["rejection_code_counts"] == {}
    assert profile["language_analysis"] == "NOT_EVALUATED"
    assert profile["distress_analysis"] == "NOT_EVALUATED"


def test_empty_input_creates_zero_count_artifacts(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "empty.jsonl"
    corpus.write_bytes(b"")
    output = tmp_path / "empty-output"

    result = run_cli(
        "traces",
        "observe",
        corpus,
        "--out",
        output,
    )

    assert result.returncode == 10
    assert_artifact_bundle(output)
    assert (output / "normalized_traces.jsonl").read_bytes() == b""
    assert (output / "rejected_traces.jsonl").read_bytes() == b""
    assert result.stdout_json()["outcome"] == "EMPTY_CORPUS"
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert (
        profile["input_count"],
        profile["accepted_count"],
        profile["rejected_count"],
        profile["case_generation_eligible_count"],
    ) == (0, 0, 0, 0)


def test_all_rejected_corpus_still_creates_accounted_artifacts(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    corpus = tmp_path / "rejected.jsonl"
    corpus.write_bytes(b"\n{broken}\n")
    output = tmp_path / "output"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 10
    assert_artifact_bundle(output)
    assert (output / "normalized_traces.jsonl").read_bytes() == b""
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile["input_count"] == 2
    assert profile["accepted_count"] == 0
    assert profile["rejected_count"] == 2
    assert profile["rejection_code_counts"] == {
        "BLANK_LINE": 1,
        "MALFORMED_JSON": 1,
    }
