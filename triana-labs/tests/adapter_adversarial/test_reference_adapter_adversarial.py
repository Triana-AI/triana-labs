from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).parents[2]
ADAPTER = PROJECT / "examples/hrai_v2/adapter.py"
FIXTURE = PROJECT / "tests/adapter_fixtures/minimal_hrai_v2.jsonl"


def run_adapter(
    source: Path,
    output: Path,
    *,
    script: Path = ADAPTER,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    command = [
        sys.executable,
        str(script),
        str(source),
        "--out",
        str(output),
        "--data-class",
        "SYNTHETIC",
    ]
    return subprocess.run(
        command, capture_output=True, check=False, env=env, timeout=30
    )


def assert_safe_fatal(result: subprocess.CompletedProcess[bytes]) -> None:
    assert result.stdout == b""
    refusal = json.loads(result.stderr)
    assert set(refusal) == {"outcome", "reason_code"}
    assert refusal["outcome"] == "REJECTED"


def test_adapter_runs_with_socket_creation_blocked(tmp_path: Path) -> None:
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
    result = run_adapter(FIXTURE, tmp_path / "output", env=env)
    assert result.returncode == 0
    assert result.stderr == b""


def test_rejected_private_marker_is_never_emitted(tmp_path: Path) -> None:
    marker = "PRIVATE-MARKER-DO-NOT-EMIT"
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value["session_id"] = marker + " with spaces"
    source = tmp_path / "private.jsonl"
    source.write_text(json.dumps(value) + "\n", encoding="utf-8")
    output = tmp_path / "output"

    result = run_adapter(source, output)

    assert result.returncode == 10
    observed = result.stdout + result.stderr
    observed += b"".join(path.read_bytes() for path in output.iterdir())
    assert marker.encode() not in observed


def test_non_regular_and_oversize_inputs_refuse_without_output(tmp_path: Path) -> None:
    directory = tmp_path / "directory"
    directory.mkdir()
    symlink = tmp_path / "symlink"
    symlink.symlink_to(FIXTURE)
    oversize = tmp_path / "oversize.jsonl"
    with oversize.open("wb") as handle:
        handle.truncate(16 * 1024 * 1024 + 1)

    for index, source in enumerate((directory, symlink, oversize)):
        output = tmp_path / f"output-{index}"
        result = run_adapter(source, output)
        assert result.returncode in {2, 3}
        assert not output.exists()
        assert_safe_fatal(result)


def test_copied_script_runs_outside_repository(tmp_path: Path) -> None:
    copied = tmp_path / "adapter.py"
    shutil.copyfile(ADAPTER, copied)
    output = tmp_path / "output"

    result = run_adapter(FIXTURE, output, script=copied)

    assert result.returncode == 0
    assert result.stderr == b""
    assert {path.name for path in output.iterdir()} == {
        "preview_traces.jsonl",
        "rejected_source_traces.jsonl",
    }


def test_unknown_cli_argument_is_a_safe_fatal_refusal(tmp_path: Path) -> None:
    output = tmp_path / "output"
    command = [
        sys.executable,
        str(ADAPTER),
        str(FIXTURE),
        "--out",
        str(output),
        "--data-class",
        "SYNTHETIC",
        "--private-marker",
        "DO-NOT-ECHO",
    ]
    result = subprocess.run(command, capture_output=True, check=False, timeout=30)

    assert result.returncode == 2
    assert not output.exists()
    assert b"DO-NOT-ECHO" not in result.stderr
    assert_safe_fatal(result)
