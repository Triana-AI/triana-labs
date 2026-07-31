"""Orchestrator-owned boundary cases reserved after acceptance freeze."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _compact(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        + b"\n"
    )


def _trace(
    *,
    trace_id: str,
    source_trace_id: str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "events": events,
        "privacy_class": "SYNTHETIC",
        "schema_version": 1,
        "source_trace_id": source_trace_id,
        "trace_id": trace_id,
    }


def _run(input_path: Path, output_path: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "traces",
            "observe",
            os.fspath(input_path),
            "--out",
            os.fspath(output_path),
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def test_multibyte_limits_are_bytes_not_characters(tmp_path: Path) -> None:
    accepted = _trace(
        trace_id="exact-byte-limits",
        source_trace_id="é" * 256,
        events=[
            {
                "content": "é" * 32_768,
                "event_kind": "USER_MESSAGE",
                "sequence": 0,
            },
            {
                "content": "",
                "event_kind": "ASSISTANT_MESSAGE",
                "is_final": False,
                "sequence": 1,
            },
        ],
    )
    oversized_source = _trace(
        trace_id="oversized-source",
        source_trace_id="é" * 257,
        events=accepted["events"],
    )
    oversized_content = _trace(
        trace_id="oversized-content",
        source_trace_id="oversized-content-source",
        events=[
            {
                "content": "é" * 32_769,
                "event_kind": "USER_MESSAGE",
                "sequence": 0,
            }
        ],
    )
    corpus = tmp_path / "multibyte.jsonl"
    corpus.write_bytes(
        _compact(accepted) + _compact(oversized_source) + _compact(oversized_content)
    )
    output = tmp_path / "output"

    result = _run(corpus, output)

    assert result.returncode == 10
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert (profile["accepted_count"], profile["rejected_count"]) == (1, 2)
    assert [item["code"] for item in _jsonl(output / "rejected_traces.jsonl")] == [
        "SCHEMA_VALIDATION_FAILED",
        "SCHEMA_VALIDATION_FAILED",
    ]


def test_lone_surrogate_is_a_safe_schema_rejection(tmp_path: Path) -> None:
    trace = _trace(
        trace_id="surrogate",
        source_trace_id="\ud800",
        events=[
            {
                "content": "synthetic",
                "event_kind": "USER_MESSAGE",
                "sequence": 0,
            }
        ],
    )
    corpus = tmp_path / "surrogate.jsonl"
    corpus.write_text(json.dumps(trace, ensure_ascii=True) + "\n")
    output = tmp_path / "output"

    result = _run(corpus, output)

    assert result.returncode == 10
    assert result.stderr.count(b"\n") == 1
    assert _jsonl(output / "rejected_traces.jsonl") == [
        {
            "code": "SCHEMA_VALIDATION_FAILED",
            "json_pointer": "/source_trace_id",
            "line_number": 1,
            "safe_message": "Input line does not match the trace schema.",
        }
    ]


def test_non_ascii_opaque_keys_are_canonical(tmp_path: Path) -> None:
    trace = _trace(
        trace_id="canonical-keys",
        source_trace_id="canonical-keys-source",
        events=[
            {
                "arguments": {"é": 1, "z": 2},
                "call_id": "call-1",
                "event_kind": "TOOL_CALL",
                "sequence": 0,
                "tool_name": "synthetic_tool",
            }
        ],
    )
    corpus = tmp_path / "canonical.jsonl"
    corpus.write_bytes(_compact(trace))
    output = tmp_path / "output"

    result = _run(corpus, output)

    assert result.returncode == 0
    normalized = (output / "normalized_traces.jsonl").read_bytes()
    assert normalized == _compact(trace)
    assert normalized.index(b'"z"') < normalized.index('"é"'.encode())


def test_exact_line_limit_is_parsed_and_one_byte_over_is_typed(
    tmp_path: Path,
) -> None:
    exact = tmp_path / "exact.jsonl"
    exact.write_bytes(b"{" + b"x" * (1024 * 1024 - 3) + b"}\n")
    exact_output = tmp_path / "exact-output"
    oversized = tmp_path / "oversized.jsonl"
    oversized.write_bytes(b"x" * (1024 * 1024) + b"\n")
    oversized_output = tmp_path / "oversized-output"

    exact_result = _run(exact, exact_output)
    oversized_result = _run(oversized, oversized_output)

    assert exact_result.returncode == 10
    assert _jsonl(exact_output / "rejected_traces.jsonl")[0]["code"] == (
        "MALFORMED_JSON"
    )
    assert oversized_result.returncode == 10
    assert _jsonl(oversized_output / "rejected_traces.jsonl")[0]["code"] == (
        "LINE_TOO_LARGE"
    )


def test_exact_thousand_line_limit_completes(tmp_path: Path) -> None:
    corpus = tmp_path / "thousand.jsonl"
    corpus.write_bytes(
        b"".join(
            _compact(
                _trace(
                    trace_id=f"trace-{index}",
                    source_trace_id=f"source-{index}",
                    events=[
                        {
                            "content": "synthetic",
                            "event_kind": "USER_MESSAGE",
                            "sequence": 0,
                        }
                    ],
                )
            )
            for index in range(1_000)
        )
    )
    output = tmp_path / "output"

    result = _run(corpus, output)

    assert result.returncode == 0
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile["input_count"] == 1_000
    assert profile["accepted_count"] == 1_000
    assert profile["case_generation_eligible_count"] == 0


def test_symlink_output_boundaries_are_never_followed(tmp_path: Path) -> None:
    trace = _trace(
        trace_id="symlink-boundary",
        source_trace_id="symlink-boundary-source",
        events=[
            {
                "content": "synthetic",
                "event_kind": "USER_MESSAGE",
                "sequence": 0,
            }
        ],
    )
    corpus = tmp_path / "valid.jsonl"
    corpus.write_bytes(_compact(trace))

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    parent_result = _run(corpus, linked_parent / "output")

    dangling_target = tmp_path / "dangling-output"
    dangling_target.symlink_to(tmp_path / "missing-target", target_is_directory=True)
    target_result = _run(corpus, dangling_target)

    assert parent_result.returncode == 2
    assert json.loads(parent_result.stderr)["reason_code"] == "OUTPUT_PARENT_MISSING"
    assert list(real_parent.iterdir()) == []
    assert target_result.returncode == 2
    assert json.loads(target_result.stderr)["reason_code"] == ("OUTPUT_ALREADY_EXISTS")
    assert dangling_target.is_symlink()
