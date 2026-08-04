"""Successful Trace Observer behavior and portable-artifact acceptance."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from conftest import (
    EXPECTED_ARTIFACT_NAMES,
    assert_artifact_bundle,
    compact_json,
    minimal_trace,
    parse_jsonl,
    write_jsonl,
)


def assert_success_terminal_log(log: dict[str, Any], *, outcome: str) -> None:
    allowed_keys = {
        "accepted_count",
        "case_generation_eligible_count",
        "command",
        "duration_ms",
        "event_name",
        "input_count",
        "outcome",
        "reason_code",
        "rejected_count",
        "service",
        "service_version",
        "severity",
    }
    required_keys = allowed_keys - {"reason_code"}
    assert required_keys <= set(log) <= allowed_keys
    assert log["command"] == "traces.observe"
    assert log["event_name"] in {
        "triana.traces.observe.succeeded",
        "triana.traces.observe.completed_with_rejections",
    }
    assert log["outcome"] == outcome
    if "reason_code" in log:
        assert log["reason_code"] is None
    assert log["service"] == "triana-labs-cli"
    assert log["service_version"] == "0.0.0"
    assert log["severity"] == "INFO"
    assert type(log["duration_ms"]) is int
    assert log["duration_ms"] >= 0


def test_owner_authorized_canary_is_truthfully_published_in_private_custody(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    trace = minimal_trace()
    trace["privacy_class"] = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
    corpus = tmp_path / "canary.jsonl"
    write_jsonl(corpus, [trace])

    with tempfile.TemporaryDirectory(
        prefix="triana-observer-", dir="/private/tmp"
    ) as root:
        output = Path(root) / "observed"
        result = run_cli("traces", "observe", corpus, "--out", output)

        assert result.returncode == 0
        assert_artifact_bundle(output)
        assert parse_jsonl(output / "normalized_traces.jsonl") == [trace]
        manifest = json.loads((output / "manifest.json").read_bytes())
        assert manifest["privacy_class"] == "OWNER_AUTHORIZED_REAL_DATA_CANARY"
        assert (
            b"OWNER_AUTHORIZED_REAL_DATA_CANARY"
            in (output / "corpus_profile.md").read_bytes()
        )
        assert b"SYNTHETIC" not in (output / "manifest.json").read_bytes()


def test_minimal_valid_trace_creates_exact_bundle(run_cli: Any, tmp_path: Path) -> None:
    corpus = tmp_path / "minimal.jsonl"
    output = tmp_path / "observed"
    trace = minimal_trace()
    write_jsonl(corpus, [trace])

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 0
    assert_artifact_bundle(output)
    assert (output / "normalized_traces.jsonl").read_bytes() == compact_json(trace)
    assert (output / "rejected_traces.jsonl").read_bytes() == b""
    assert result.stdout_json() == {
        "accepted_count": 1,
        "case_generation_eligible_count": 1,
        "manifest_path": f"{output}/manifest.json",
        "outcome": "COMPLETED",
        "rejected_count": 0,
    }
    log = result.stderr_json()
    assert_success_terminal_log(log, outcome="COMPLETED")
    assert (
        log["input_count"],
        log["accepted_count"],
        log["rejected_count"],
        log["case_generation_eligible_count"],
    ) == (1, 1, 0, 1)


def test_every_event_variant_and_companion_state_is_accepted(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    corpus = fixture_root / "valid_all_events.jsonl"
    output = tmp_path / "all-events"

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 0
    expected_trace = json.loads(corpus.read_bytes())
    assert (output / "normalized_traces.jsonl").read_bytes() == compact_json(
        expected_trace
    )
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile["event_kind_counts"] == {
        "ASSISTANT_MESSAGE": 2,
        "SYSTEM_VISIBLE_MESSAGE": 1,
        "TERMINAL": 1,
        "TOOL_CALL": 2,
        "TOOL_RESULT": 2,
        "USER_MESSAGE": 1,
    }
    assert profile["terminal_state_counts"] == {
        "ABORTED": 0,
        "ERROR": 1,
        "SUCCESS": 0,
    }
    assert profile["tool_call_counts"] == {"lookup_record": 2}


def test_all_valid_multiline_corpus_preserves_input_order(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    traces = [
        minimal_trace(trace_id="z-trace", source_trace_id="z-source"),
        minimal_trace(trace_id="a-trace", source_trace_id="a-source"),
        minimal_trace(trace_id="m-trace", source_trace_id="m-source"),
    ]
    corpus = tmp_path / "ordered.jsonl"
    output = tmp_path / "ordered"
    write_jsonl(corpus, traces)

    result = run_cli("traces", "observe", corpus, "--out", output)

    assert result.returncode == 0
    assert parse_jsonl(output / "normalized_traces.jsonl") == traces


def test_canonical_mixed_fixture_has_exact_counts_and_order(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "mixed"
    result = run_cli(
        "traces",
        "observe",
        fixture_root / "mixed_corpus.jsonl",
        "--out",
        output,
    )

    assert result.returncode == 10
    assert result.stdout_json() == {
        "accepted_count": 3,
        "case_generation_eligible_count": 2,
        "manifest_path": f"{output}/manifest.json",
        "outcome": "COMPLETED_WITH_REJECTIONS",
        "rejected_count": 2,
    }
    profile = json.loads((output / "corpus_profile.json").read_bytes())
    assert profile == {
        "accepted_count": 3,
        "artifact_kind": "corpus_profile",
        "case_generation_eligible_count": 2,
        "distress_analysis": "NOT_EVALUATED",
        "event_kind_counts": {
            "ASSISTANT_MESSAGE": 2,
            "SYSTEM_VISIBLE_MESSAGE": 2,
            "TERMINAL": 1,
            "TOOL_CALL": 1,
            "TOOL_RESULT": 1,
            "USER_MESSAGE": 2,
        },
        "input_count": 5,
        "language_analysis": "NOT_EVALUATED",
        "rejected_count": 2,
        "rejection_code_counts": {
            "IMPOSSIBLE_TRACE_STATE": 1,
            "MALFORMED_JSON": 1,
        },
        "schema_version": 1,
        "terminal_state_counts": {"ABORTED": 0, "ERROR": 0, "SUCCESS": 1},
        "tool_call_counts": {"lookup_order": 1},
    }
    assert (output / "corpus_profile.json").read_bytes() == compact_json(profile)
    normalized = parse_jsonl(output / "normalized_traces.jsonl")
    rejected = parse_jsonl(output / "rejected_traces.jsonl")
    assert (output / "normalized_traces.jsonl").read_bytes() == b"".join(
        compact_json(item) for item in normalized
    )
    assert (output / "rejected_traces.jsonl").read_bytes() == b"".join(
        compact_json(item) for item in rejected
    )
    assert [
        item["line_number"] for item in parse_jsonl(output / "rejected_traces.jsonl")
    ] == [
        4,
        5,
    ]
    assert [
        item["trace_id"] for item in parse_jsonl(output / "normalized_traces.jsonl")
    ] == [
        "trace-complete",
        "trace-short",
        "trace-ineligible",
    ]


def test_crlf_and_missing_final_lf_normalize_equivalently(
    run_cli: Any,
    tmp_path: Path,
) -> None:
    trace = minimal_trace()
    canonical = compact_json(trace)
    variants = {
        "lf": canonical,
        "crlf": canonical.replace(b"\n", b"\r\n"),
        "no-final-lf": canonical[:-1],
    }
    artifact_sets: list[dict[str, bytes]] = []

    for name, payload in variants.items():
        corpus = tmp_path / f"{name}.jsonl"
        output = tmp_path / f"{name}-output"
        corpus.write_bytes(payload)
        result = run_cli("traces", "observe", corpus, "--out", output)
        assert result.returncode == 0
        artifact_sets.append(
            {
                artifact: (output / artifact).read_bytes()
                for artifact in EXPECTED_ARTIFACT_NAMES
            }
        )

    assert artifact_sets[0] == artifact_sets[1] == artifact_sets[2]


def test_fresh_process_repeats_are_byte_identical(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    outputs = [tmp_path / "repeat-one", tmp_path / "repeat-two"]
    for output in outputs:
        result = run_cli(
            "traces",
            "observe",
            fixture_root / "mixed_corpus.jsonl",
            "--out",
            output,
        )
        assert result.returncode == 10

    for artifact in EXPECTED_ARTIFACT_NAMES:
        assert (outputs[0] / artifact).read_bytes() == (
            outputs[1] / artifact
        ).read_bytes()


def test_manifest_hashes_are_independently_recomputed_from_exact_bytes(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "hashes"
    result = run_cli(
        "traces",
        "observe",
        fixture_root / "mixed_corpus.jsonl",
        "--out",
        output,
    )
    assert result.returncode == 10

    manifest = json.loads((output / "manifest.json").read_bytes())
    expected_hashes = {
        artifact: f"sha256:{hashlib.sha256((output / artifact).read_bytes()).hexdigest()}"
        for artifact in (
            "normalized_traces.jsonl",
            "rejected_traces.jsonl",
            "corpus_profile.json",
            "corpus_profile.md",
        )
    }
    assert manifest == {
        "accepted_count": 3,
        "artifact_kind": "corpus_manifest",
        "artifacts": expected_hashes,
        "case_generation_eligible_count": 2,
        "input_count": 5,
        "privacy_class": "SYNTHETIC",
        "rejected_count": 2,
        "schema_version": 1,
    }
    assert (output / "manifest.json").read_bytes() == compact_json(manifest)


def test_markdown_projects_json_and_manifest_without_new_claims(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "markdown"
    result = run_cli(
        "traces",
        "observe",
        fixture_root / "mixed_corpus.jsonl",
        "--out",
        output,
    )
    assert result.returncode == 10

    markdown = (output / "corpus_profile.md").read_text()
    for value in ("5", "3", "2"):
        assert value in markdown
    for required_text in (
        "SYNTHETIC",
        "ASSISTANT_MESSAGE",
        "SYSTEM_VISIBLE_MESSAGE",
        "TOOL_CALL",
        "lookup_order",
        "SUCCESS",
        "IMPOSSIBLE_TRACE_STATE",
        "MALFORMED_JSON",
        "language",
        "distress",
        "personas",
        "intents",
        "cases",
        "execution",
        "comparison",
        "manifest.json",
        "normalized_traces.jsonl",
        "rejected_traces.jsonl",
        "corpus_profile.json",
    ):
        assert required_text.lower() in markdown.lower()
    assert str(tmp_path) not in markdown
    assert "not evaluated" in markdown.lower()
