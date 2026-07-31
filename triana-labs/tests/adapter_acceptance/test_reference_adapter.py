"""Acceptance contract for the copyable HRAI v2 reference transform."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ADAPTER,
    ADAPTER_README,
    FIXTURES,
    PROJECT_ROOT,
    assert_bundle,
    compact_json,
    minimal_source,
    parse_jsonl,
    write_jsonl,
)


def expected_minimal_trace() -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "events": [
            {
                "content": "You are the synthetic reference agent.",
                "event_kind": "SYSTEM_VISIBLE_MESSAGE",
                "sequence": 0,
            },
            {
                "content": "Find the synthetic candidate.",
                "event_kind": "USER_MESSAGE",
                "sequence": 1,
            },
            {
                "content": "I found the synthetic candidate.",
                "event_kind": "ASSISTANT_MESSAGE",
                "is_final": True,
                "sequence": 2,
            },
        ],
        "privacy_class": "SYNTHETIC",
        "schema_version": 1,
        "source_trace_id": "synthetic-session-minimal",
        "trace_id": "synthetic-session-minimal",
    }


def expected_tool_trace() -> dict[str, Any]:
    events: list[dict[str, Any]] = [
        {
            "content": "Use only synthetic candidate records.",
            "event_kind": "SYSTEM_VISIBLE_MESSAGE",
        },
        {"content": "Find two synthetic candidates.", "event_kind": "USER_MESSAGE"},
        {
            "arguments": {"candidate_id": 7, "labels": ["synthetic"]},
            "call_id": "hrai-t1-c1",
            "event_kind": "TOOL_CALL",
            "tool_name": "lookup_candidate",
        },
        {
            "call_id": "hrai-t1-c1",
            "event_kind": "TOOL_RESULT",
            "result": {"found": True},
            "result_state": "SUCCEEDED",
        },
        {
            "arguments": {"candidate_id": 8},
            "call_id": "hrai-t1-c2",
            "event_kind": "TOOL_CALL",
            "tool_name": "lookup_candidate",
        },
        {
            "content": "I found one candidate and need another lookup.",
            "event_kind": "ASSISTANT_MESSAGE",
            "is_final": False,
        },
        {
            "content": "Load the final synthetic candidate.",
            "event_kind": "USER_MESSAGE",
        },
        {
            "arguments": {"candidate_id": 9},
            "call_id": "hrai-t2-c1",
            "event_kind": "TOOL_CALL",
            "tool_name": "load_candidate",
        },
        {
            "call_id": "hrai-t2-c1",
            "error_code": "HRAI_TOOL_ERROR",
            "event_kind": "TOOL_RESULT",
            "result_state": "ERROR",
        },
        {
            "content": "The synthetic lookup is complete.",
            "event_kind": "ASSISTANT_MESSAGE",
            "is_final": True,
        },
    ]
    for sequence, event in enumerate(events):
        event["sequence"] = sequence
    return {
        "contract_kind": "preview_trace",
        "events": events,
        "privacy_class": "SYNTHETIC",
        "schema_version": 1,
        "source_trace_id": "synthetic-session-tools",
        "trace_id": "synthetic-session-tools",
    }


def assert_success_channels(result: Any, output: Path, *, outcome: str) -> None:
    receipt = result.stdout_json()
    assert set(receipt) == {
        "accepted_count",
        "manifest_path",
        "outcome",
        "rejected_count",
    }
    assert receipt["manifest_path"] == f"{output}/adapter_manifest.json"
    assert receipt["outcome"] == outcome
    terminal = result.stderr_json()
    assert terminal["accepted_count"] == receipt["accepted_count"]
    assert terminal["rejected_count"] == receipt["rejected_count"]
    assert terminal["outcome"] == outcome
    assert "path" not in terminal


@pytest.mark.parametrize(
    ("fixture", "expected"),
    [
        ("minimal_hrai_v2.jsonl", expected_minimal_trace),
        ("tool_rich_hrai_v2.jsonl", expected_tool_trace),
    ],
)
def test_success_mappings_have_exact_independently_authored_bytes(
    run_adapter: Any,
    tmp_path: Path,
    fixture: str,
    expected: Any,
) -> None:
    output = tmp_path / "adapted"

    result = run_adapter(FIXTURES / fixture, output)

    assert result.returncode == 0
    assert_bundle(output)
    expected_bytes = compact_json(expected())
    assert (output / "preview_traces.jsonl").read_bytes() == expected_bytes
    assert (output / "rejected_source_traces.jsonl").read_bytes() == b""
    manifest = json.loads((output / "adapter_manifest.json").read_bytes())
    assert manifest == {
        "accepted_count": 1,
        "adapter_kind": "hrai_normalized_trace_v2_reference",
        "artifacts": {
            "preview_traces.jsonl": f"sha256:{hashlib.sha256(expected_bytes).hexdigest()}",
            "rejected_source_traces.jsonl": (
                f"sha256:{hashlib.sha256(b'').hexdigest()}"
            ),
        },
        "input_count": 1,
        "privacy_class": "SYNTHETIC",
        "rejected_count": 0,
        "schema_version": 1,
        "source_schema_version": "normalized-trace-v2",
    }
    assert (output / "adapter_manifest.json").read_bytes() == compact_json(manifest)
    assert_success_channels(result, output, outcome="COMPLETED")


def test_tool_mapping_preserves_order_ids_gaps_and_no_terminal(
    run_adapter: Any, tmp_path: Path
) -> None:
    output = tmp_path / "tools"
    result = run_adapter(FIXTURES / "tool_rich_hrai_v2.jsonl", output)
    assert result.returncode == 0

    trace = parse_jsonl(output / "preview_traces.jsonl")[0]
    events = trace["events"]
    assert [event["sequence"] for event in events] == list(range(10))
    assert [event["event_kind"] for event in events] == [
        "SYSTEM_VISIBLE_MESSAGE",
        "USER_MESSAGE",
        "TOOL_CALL",
        "TOOL_RESULT",
        "TOOL_CALL",
        "ASSISTANT_MESSAGE",
        "USER_MESSAGE",
        "TOOL_CALL",
        "TOOL_RESULT",
        "ASSISTANT_MESSAGE",
    ]
    assert [event["call_id"] for event in events if "call_id" in event] == [
        "hrai-t1-c1",
        "hrai-t1-c1",
        "hrai-t1-c2",
        "hrai-t2-c1",
        "hrai-t2-c1",
    ]
    assert [event["is_final"] for event in events if "is_final" in event] == [
        False,
        True,
    ]
    assert not any(event["event_kind"] == "TERMINAL" for event in events)


def test_ignored_finite_floats_map_but_mapped_floats_reject(
    run_adapter: Any, tmp_path: Path
) -> None:
    ignored = minimal_source(session_id="finite-ignored")
    ignored.update({"usd": 0.125, "tokens": {"price": 1.5}})
    ignored["turns"][0]["metadata"] = {"score": 0.75}
    ignored["events"][0]["ts"] = 1.25
    bad_arguments = minimal_source(session_id="float-arguments")
    call = {
        "name": "lookup",
        "arguments": {"score": 0.5},
        "result_summary": None,
        "status": "ok",
        "error": None,
        "latency_ms": 0,
        "cached": False,
    }
    bad_arguments["events"][1]["tool_calls"] = [call]
    source = tmp_path / "floats.jsonl"
    write_jsonl(source, [ignored, bad_arguments])
    output = tmp_path / "floats"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert [
        item["trace_id"] for item in parse_jsonl(output / "preview_traces.jsonl")
    ] == ["finite-ignored"]
    assert [
        item["code"] for item in parse_jsonl(output / "rejected_source_traces.jsonl")
    ] == ["SOURCE_SCHEMA_VALIDATION_FAILED"]


def test_incomplete_harness_and_turn_event_mismatch_are_safe_rejections(
    run_adapter: Any, tmp_path: Path
) -> None:
    harness_error = minimal_source(
        session_id="private-session-harness", status="HARNESS_ERROR"
    )
    mismatch = minimal_source(session_id="private-session-mismatch")
    mismatch["events"][1]["role"] = "user"
    source = tmp_path / "private-input-name.jsonl"
    write_jsonl(source, [harness_error, mismatch])
    output = tmp_path / "adapted"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert (output / "preview_traces.jsonl").read_bytes() == b""
    rejections = parse_jsonl(output / "rejected_source_traces.jsonl")
    assert [item["code"] for item in rejections] == [
        "SOURCE_EXECUTION_INCOMPLETE",
        "SOURCE_TURN_EVENT_MISMATCH",
    ]
    assert rejections[1] == {
        "code": "SOURCE_TURN_EVENT_MISMATCH",
        "json_pointer": "/events",
        "line_number": 2,
        "safe_message": "Source turns and events do not align.",
    }
    combined = (
        result.stdout
        + result.stderr
        + (output / "rejected_source_traces.jsonl").read_bytes()
    )
    for secret in (
        b"private-input-name",
        b"private-session-harness",
        b"private-session-mismatch",
        b"HARNESS_ERROR",
    ):
        assert secret not in combined


@pytest.mark.parametrize(
    ("name", "payload", "code"),
    [
        ("blank", b" \t\n", "BLANK_LINE"),
        ("invalid-utf8", b"\xff\n", "INVALID_UTF8"),
        ("bom", b"\xef\xbb\xbf{}\n", "BOM_FORBIDDEN"),
        ("malformed", b'{"schema_version":\n', "MALFORMED_JSON"),
        (
            "duplicate-key",
            b'{"schema_version":"normalized-trace-v2","schema_version":"normalized-trace-v2"}\n',
            "DUPLICATE_JSON_KEY",
        ),
        ("nonfinite", b'{"usd":NaN}\n', "MALFORMED_JSON"),
    ],
)
def test_raw_line_rejections(
    run_adapter: Any,
    tmp_path: Path,
    name: str,
    payload: bytes,
    code: str,
) -> None:
    source = tmp_path / f"{name}.jsonl"
    source.write_bytes(payload)
    output = tmp_path / f"{name}-output"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert [
        item["code"] for item in parse_jsonl(output / "rejected_source_traces.jsonl")
    ] == [code]
    assert (
        json.loads((output / "adapter_manifest.json").read_bytes())["input_count"] == 1
    )


def test_depth_and_line_size_are_per_line_rejections(
    run_adapter: Any, tmp_path: Path
) -> None:
    too_deep = b'{"ignored":' + (b"[" * 32) + b"0" + (b"]" * 32) + b"}\n"
    too_large = b'"' + (b"x" * (1024 * 1024)) + b'"\n'
    source = tmp_path / "bounded.jsonl"
    source.write_bytes(too_deep + too_large)
    output = tmp_path / "bounded-output"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert [
        item["code"] for item in parse_jsonl(output / "rejected_source_traces.jsonl")
    ] == [
        "NESTING_TOO_DEEP",
        "LINE_TOO_LARGE",
    ]


def test_duplicate_accepted_session_and_rejected_identity_accounting(
    run_adapter: Any, tmp_path: Path
) -> None:
    rejected_first = minimal_source(session_id="reusable-session", status="ERROR")
    accepted = minimal_source(session_id="reusable-session")
    duplicate = minimal_source(session_id="reusable-session")
    source = tmp_path / "identity.jsonl"
    write_jsonl(source, [rejected_first, accepted, duplicate])
    output = tmp_path / "identity-output"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert [
        item["trace_id"] for item in parse_jsonl(output / "preview_traces.jsonl")
    ] == ["reusable-session"]
    rejections = parse_jsonl(output / "rejected_source_traces.jsonl")
    assert [item["code"] for item in rejections] == [
        "SOURCE_EXECUTION_INCOMPLETE",
        "DUPLICATE_TRACE_ID",
    ]
    manifest = json.loads((output / "adapter_manifest.json").read_bytes())
    assert (
        manifest["input_count"],
        manifest["accepted_count"],
        manifest["rejected_count"],
    ) == (3, 1, 2)


def test_mixed_partial_success_preserves_source_order_and_exact_accounting(
    run_adapter: Any, tmp_path: Path
) -> None:
    first = minimal_source(session_id="first-accepted")
    last = minimal_source(session_id="last-accepted")
    source = tmp_path / "mixed.jsonl"
    source.write_bytes(compact_json(first) + b"\n" + compact_json(last))
    output = tmp_path / "mixed-output"

    result = run_adapter(source, output)

    assert result.returncode == 10
    assert [
        item["trace_id"] for item in parse_jsonl(output / "preview_traces.jsonl")
    ] == [
        "first-accepted",
        "last-accepted",
    ]
    assert [
        item["line_number"]
        for item in parse_jsonl(output / "rejected_source_traces.jsonl")
    ] == [2]
    manifest = json.loads((output / "adapter_manifest.json").read_bytes())
    assert (
        manifest["input_count"]
        == manifest["accepted_count"] + manifest["rejected_count"]
        == 3
    )
    assert_success_channels(result, output, outcome="COMPLETED_WITH_REJECTIONS")


@pytest.mark.parametrize("payload", [b"", b"\n{}\n"])
def test_empty_and_all_rejected_bundles_are_deterministic(
    run_adapter: Any, tmp_path: Path, payload: bytes
) -> None:
    source = tmp_path / "input.jsonl"
    source.write_bytes(payload)
    outputs = [tmp_path / "one", tmp_path / "two"]
    bundles: list[dict[str, bytes]] = []
    for output in outputs:
        result = run_adapter(source, output)
        assert result.returncode == 10
        assert (output / "preview_traces.jsonl").read_bytes() == b""
        bundles.append({path.name: path.read_bytes() for path in output.iterdir()})
    assert bundles[0] == bundles[1]


def test_manifest_hashes_exact_artifact_bytes_and_fresh_process_repeatability(
    run_adapter: Any, tmp_path: Path
) -> None:
    outputs = [tmp_path / "first", tmp_path / "second"]
    for output in outputs:
        result = run_adapter(FIXTURES / "tool_rich_hrai_v2.jsonl", output)
        assert result.returncode == 0
        manifest = json.loads((output / "adapter_manifest.json").read_bytes())
        for artifact in ("preview_traces.jsonl", "rejected_source_traces.jsonl"):
            digest = hashlib.sha256((output / artifact).read_bytes()).hexdigest()
            assert manifest["artifacts"][artifact] == f"sha256:{digest}"
    for artifact in (
        "adapter_manifest.json",
        "preview_traces.jsonl",
        "rejected_source_traces.jsonl",
    ):
        assert (outputs[0] / artifact).read_bytes() == (
            outputs[1] / artifact
        ).read_bytes()


@pytest.mark.parametrize("extra", [(), ("--data-class", "LOCAL_SENSITIVE")])
def test_synthetic_attestation_is_mandatory_before_input_read(
    run_adapter: Any, tmp_path: Path, extra: tuple[str, ...]
) -> None:
    output = tmp_path / "must-not-exist"
    result = run_adapter(tmp_path / "private-do-not-read.jsonl", output, extra=extra)
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr_json()["reason_code"] == "UNSUPPORTED_DATA_CLASS"
    assert b"private-do-not-read" not in result.stderr
    assert not output.exists()


def test_help_is_safe_and_has_no_terminal_event(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, os.fspath(ADAPTER), "--help"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert completed.returncode == 0
    assert completed.stdout
    assert completed.stderr == b""


def test_fatal_input_and_publication_failures_never_overwrite(
    run_adapter: Any, tmp_path: Path
) -> None:
    missing_output = tmp_path / "missing-output"
    missing = run_adapter(tmp_path / "missing.jsonl", missing_output)
    assert missing.returncode in {2, 3}
    assert not missing_output.exists()

    existing = tmp_path / "existing"
    existing.mkdir()
    marker = existing / "customer-owned.txt"
    marker.write_text("keep", encoding="utf-8")
    collision = run_adapter(FIXTURES / "minimal_hrai_v2.jsonl", existing)
    assert collision.returncode == 7
    assert marker.read_text(encoding="utf-8") == "keep"
    assert {path.name for path in existing.iterdir()} == {"customer-owned.txt"}
    assert not list(tmp_path.glob(".*existing*"))


def test_total_line_limit_is_fatal_with_no_bundle(
    run_adapter: Any, tmp_path: Path
) -> None:
    source = tmp_path / "too-many.jsonl"
    source.write_bytes(b"{}\n" * 1001)
    output = tmp_path / "too-many-output"
    result = run_adapter(source, output)
    assert result.returncode in {2, 3}
    assert not output.exists()


def test_adapter_output_is_accepted_by_unchanged_observer(
    run_adapter: Any, tmp_path: Path
) -> None:
    adapted = tmp_path / "adapted"
    result = run_adapter(FIXTURES / "tool_rich_hrai_v2.jsonl", adapted)
    assert result.returncode == 0
    observed = tmp_path / "observed"
    observer = subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "traces",
            "observe",
            os.fspath(adapted / "preview_traces.jsonl"),
            "--out",
            os.fspath(observed),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert observer.returncode == 0, observer.stderr
    normalized = observed / "normalized_traces.jsonl"
    assert normalized.read_bytes() == compact_json(expected_tool_trace())


def test_script_is_copyable_standard_library_only_and_bounded() -> None:
    source = ADAPTER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert imports <= set(sys.stdlib_module_names)
    assert "triana_labs" not in imports
    counted_lines = [
        line
        for line in source.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert len(counted_lines) <= 200
    assert ADAPTER.is_relative_to(PROJECT_ROOT / "examples")
    assert not (PROJECT_ROOT / "src" / "triana_labs" / "examples").exists()


def test_readme_declares_copy_run_privacy_and_non_product_boundaries() -> None:
    text = ADAPTER_README.read_text(encoding="utf-8").lower()
    for required in (
        "--data-class synthetic",
        "preview_traces.jsonl",
        "triana traces observe",
        "reference",
        "copy",
        "unsupported",
        "production-derived",
        "customer",
        "blitz",
        "local-sensitive",
    ):
        assert required in text
