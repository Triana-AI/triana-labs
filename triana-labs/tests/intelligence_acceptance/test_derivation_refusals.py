"""Integrity, boundary, path, and privacy refusals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    assert_refusal,
    build_observer_bundle,
    compact_json,
    digest,
    read_fixture_traces,
)


@pytest.mark.parametrize(
    ("mutation", "reason", "exit_code"),
    [
        (lambda value: value.update(schema_version=2), "MANIFEST_INVALID", 4),
        (lambda value: value.update(extra=True), "MANIFEST_INVALID", 4),
        (
            lambda value: value.update(privacy_class="LOCAL_SENSITIVE"),
            "UNSUPPORTED_PRIVACY_CLASS",
            4,
        ),
        (lambda value: value.update(accepted_count=99), "CORPUS_INTEGRITY_FAILED", 5),
    ],
)
def test_manifest_schema_privacy_and_count_refusals(
    run_cli: Any,
    tmp_path: Path,
    mutation: Any,
    reason: str,
    exit_code: int,
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    value = json.loads(manifest.read_bytes())
    mutation(value)
    manifest.write_bytes(compact_json(value))
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, reason, exit_code)
    assert not output.exists()


@pytest.mark.parametrize(
    "payload", [b"{", b'{"x":1,"x":2}\n', b"\xef\xbb\xbf{}\n", b'{"x":NaN}\n']
)
def test_invalid_manifest_bytes_are_safe(
    run_cli: Any, tmp_path: Path, payload: bytes
) -> None:
    observed = tmp_path / "observed"
    observed.mkdir()
    manifest = observed / "manifest.json"
    manifest.write_bytes(payload)
    output = tmp_path / "PRIVATE_OUTPUT_PATH"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "MANIFEST_INVALID", 4)
    assert b"PRIVATE_OUTPUT_PATH" not in result.stderr
    assert not output.exists()


def test_manifest_depth_and_size_limits(run_cli: Any, tmp_path: Path) -> None:
    observed = tmp_path / "observed"
    observed.mkdir()
    manifest = observed / "manifest.json"
    nested: Any = 0
    for _ in range(33):
        nested = [nested]
    manifest.write_bytes(compact_json(nested))
    result = run_cli("corpus", "derive", manifest, "--out", tmp_path / "depth-output")
    assert_refusal(result, "MANIFEST_INVALID", 4)
    manifest.write_bytes(b" " * (1024 * 1024 + 1))
    result = run_cli("corpus", "derive", manifest, "--out", tmp_path / "size-output")
    assert_refusal(result, "INPUT_TOO_LARGE", 3)


@pytest.mark.parametrize(
    "artifact",
    [
        "normalized_traces.jsonl",
        "corpus_profile.json",
        "corpus_profile.md",
        "rejected_traces.jsonl",
    ],
)
def test_missing_or_tampered_sibling_is_integrity_failure(
    run_cli: Any, tmp_path: Path, artifact: str
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    (manifest.parent / artifact).write_bytes(b"tampered\n")
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "CORPUS_INTEGRITY_FAILED", 5)
    assert not output.exists()


@pytest.mark.parametrize("identity", ["trace_id", "source_trace_id"])
def test_duplicate_trace_identity_is_integrity_failure(
    run_cli: Any, tmp_path: Path, identity: str
) -> None:
    traces = read_fixture_traces()[:2]
    traces[1][identity] = traces[0][identity]
    manifest = build_observer_bundle(tmp_path / "observed", traces)
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "CORPUS_INTEGRITY_FAILED", 5)
    assert not output.exists()


def test_invalid_normalized_trace_is_integrity_failure(
    run_cli: Any, tmp_path: Path
) -> None:
    traces = read_fixture_traces()
    traces[0]["unexpected"] = "private"
    manifest = build_observer_bundle(tmp_path / "observed", traces)
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "CORPUS_INTEGRITY_FAILED", 5)
    assert not output.exists()


def test_empty_corpus_is_typed_fatal(run_cli: Any, tmp_path: Path) -> None:
    manifest = build_observer_bundle(tmp_path / "observed", [], rejected_count=1)
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "EMPTY_CORPUS", 5)
    assert not output.exists()


@pytest.mark.parametrize(
    ("artifact", "size"),
    [
        ("normalized_traces.jsonl", 16 * 1024 * 1024 + 1),
        ("rejected_traces.jsonl", 16 * 1024 * 1024 + 1),
        ("corpus_profile.json", 1024 * 1024 + 1),
        ("corpus_profile.md", 1024 * 1024 + 1),
    ],
)
def test_oversized_sibling_is_typed_before_hash_validation(
    run_cli: Any, tmp_path: Path, artifact: str, size: int
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    payload = b"x" * size
    (manifest.parent / artifact).write_bytes(payload)
    value = json.loads(manifest.read_bytes())
    value["artifacts"][artifact] = digest(payload)
    manifest.write_bytes(compact_json(value))
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "INPUT_TOO_LARGE", 3)
    assert not output.exists()


def test_nonregular_sibling_is_integrity_failure(run_cli: Any, tmp_path: Path) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    profile = manifest.parent / "corpus_profile.md"
    profile.unlink()
    profile.mkdir()
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "CORPUS_INTEGRITY_FAILED", 5)
    assert not output.exists()


@pytest.mark.parametrize(
    "payload",
    [b"{}\n" * 1001, b'"' + b"x" * (1024 * 1024) + b'"\n'],
    ids=["too-many-lines", "line-too-large"],
)
def test_normalized_physical_limits_are_typed_before_trace_validation(
    run_cli: Any, tmp_path: Path, payload: bytes
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    normalized = manifest.parent / "normalized_traces.jsonl"
    normalized.write_bytes(payload)
    value = json.loads(manifest.read_bytes())
    value["artifacts"]["normalized_traces.jsonl"] = digest(payload)
    manifest.write_bytes(compact_json(value))
    output = tmp_path / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", output)
    assert_refusal(result, "INPUT_TOO_LARGE", 3)
    assert not output.exists()
