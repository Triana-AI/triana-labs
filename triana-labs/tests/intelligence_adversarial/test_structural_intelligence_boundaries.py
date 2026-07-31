from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).parents[2]
FIXTURE = PROJECT / "tests/intelligence_fixtures/structural_traces.jsonl"
DERIVE_MODULE = PROJECT / "src/triana_labs/intelligence/derive.py"


def run_cli(
    *arguments: object, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "triana_labs", *(os.fspath(arg) for arg in arguments)],
        cwd=PROJECT,
        env=env,
        check=False,
        capture_output=True,
        timeout=30,
    )


def observed_bundle(tmp_path: Path) -> Path:
    output = tmp_path / "observed"
    result = run_cli("traces", "observe", FIXTURE, "--out", output)
    assert result.returncode == 0, result.stderr
    return output / "manifest.json"


def test_real_observer_bundle_derives_with_socket_creation_blocked(
    tmp_path: Path,
) -> None:
    manifest = observed_bundle(tmp_path)
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(
        "import socket\n"
        "def blocked(*args, **kwargs): raise AssertionError('network forbidden')\n"
        "socket.socket = blocked\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(guard)

    result = run_cli(
        "corpus", "derive", manifest, "--out", tmp_path / "intelligence", env=env
    )

    assert result.returncode == 10, result.stderr
    report = json.loads((tmp_path / "intelligence/derivation_report.json").read_bytes())
    assert report["outcome"] == "COMPLETED_WITH_GAPS"
    assert report["trace_count"] == 4


def test_output_parent_symlink_is_refused_without_reading_private_path(
    tmp_path: Path,
) -> None:
    manifest = observed_bundle(tmp_path)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    result = run_cli(
        "corpus", "derive", manifest, "--out", linked_parent / "PRIVATE_OUTPUT"
    )

    assert result.returncode == 2
    assert b"PRIVATE_OUTPUT" not in result.stderr
    assert json.loads(result.stderr)["reason_code"] == "OUTPUT_PARENT_MISSING"
    assert not (real_parent / "PRIVATE_OUTPUT").exists()


def test_deep_manifest_is_typed_and_content_free(tmp_path: Path) -> None:
    observed = tmp_path / "observed"
    observed.mkdir()
    private = b"PRIVATE_DEEP_VALUE"
    manifest = observed / "manifest.json"
    manifest.write_bytes(b"[" * 64 + b'"' + private + b'"' + b"]" * 64)

    result = run_cli("corpus", "derive", manifest, "--out", tmp_path / "deep-output")

    assert result.returncode == 4
    assert private not in result.stderr
    assert json.loads(result.stderr)["reason_code"] == "MANIFEST_INVALID"
    assert not (tmp_path / "deep-output").exists()


def test_fingerprint_code_has_no_semantic_or_provider_dependency() -> None:
    tree = ast.parse(DERIVE_MODULE.read_text(encoding="utf-8"))
    imports = {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    imports.update(
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    )
    assert not imports & {"openai", "requests", "socket", "urllib"}

    fingerprint = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_fingerprint"
    )
    strings = {
        node.value
        for node in ast.walk(fingerprint)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not strings & {
        "arguments",
        "content",
        "error_code",
        "reason_code",
        "result",
        "source_trace_id",
    }
