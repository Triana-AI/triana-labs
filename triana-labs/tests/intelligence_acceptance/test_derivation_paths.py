"""Filesystem publication and CLI boundary acceptance."""

from __future__ import annotations

import os
import resource
import signal
from pathlib import Path
from typing import Any

import pytest
from conftest import assert_refusal, build_observer_bundle


def limit_file_size() -> None:
    signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


def test_help_is_public_and_quiet(run_cli: Any) -> None:
    result = run_cli("corpus", "derive", "--help")
    assert result.returncode == 0
    assert b"corpus" in result.stdout and b"derive" in result.stdout
    assert result.stderr == b""


def test_safe_usage_and_missing_input_refusals(run_cli: Any, tmp_path: Path) -> None:
    private = "PRIVATE_USAGE_VALUE"
    usage = run_cli("corpus", "derive", private)
    assert_refusal(usage, "CLI_USAGE_ERROR", 2)
    assert private.encode() not in usage.stderr
    output = tmp_path / "out"
    missing = run_cli("corpus", "derive", tmp_path / "PRIVATE_MISSING", "--out", output)
    assert_refusal(missing, "INPUT_READ_FAILED", 2)
    assert b"PRIVATE_MISSING" not in missing.stderr
    assert not output.exists()


def test_output_parent_and_existing_target_are_refused(
    run_cli: Any, tmp_path: Path
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    missing_output = tmp_path / "missing-parent" / "derived"
    result = run_cli("corpus", "derive", manifest, "--out", missing_output)
    assert_refusal(result, "OUTPUT_PARENT_MISSING", 2)
    existing = tmp_path / "existing"
    existing.mkdir()
    marker = existing / "marker"
    marker.write_text("preserve")
    result = run_cli("corpus", "derive", manifest, "--out", existing)
    assert_refusal(result, "OUTPUT_ALREADY_EXISTS", 2)
    assert marker.read_text() == "preserve"


@pytest.mark.skipif(os.name != "posix", reason="RLIMIT_FSIZE is POSIX evidence")
def test_atomic_write_failure_leaves_no_target(run_cli: Any, tmp_path: Path) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    output = tmp_path / "derived"
    result = run_cli(
        "corpus",
        "derive",
        manifest,
        "--out",
        output,
        preexec_fn=limit_file_size,
    )
    assert_refusal(result, "OUTPUT_WRITE_FAILED", 7)
    assert not output.exists()


def test_manifest_and_sibling_symlinks_are_refused(
    run_cli: Any, tmp_path: Path
) -> None:
    manifest = build_observer_bundle(tmp_path / "observed")
    manifest_link = tmp_path / "manifest-link.json"
    manifest_link.symlink_to(manifest)
    result = run_cli("corpus", "derive", manifest_link, "--out", tmp_path / "one")
    assert_refusal(result, "INPUT_READ_FAILED", 2)
    normalized = manifest.parent / "normalized_traces.jsonl"
    target = tmp_path / "normalized-target"
    target.write_bytes(normalized.read_bytes())
    normalized.unlink()
    normalized.symlink_to(target)
    result = run_cli("corpus", "derive", manifest, "--out", tmp_path / "two")
    assert_refusal(result, "CORPUS_INTEGRITY_FAILED", 5)
