"""Black-box harness for the Triana Labs command-line acceptance contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = REPOSITORY_ROOT / "triana-labs"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "fixtures"
EXPECTED_ARTIFACT_NAMES = {
    "corpus_profile.json",
    "corpus_profile.md",
    "manifest.json",
    "normalized_traces.jsonl",
    "rejected_traces.jsonl",
}


@dataclass(frozen=True)
class CommandResult:
    """Captured public-command result."""

    returncode: int
    stdout: bytes
    stderr: bytes

    def stdout_json(self) -> dict[str, Any]:
        value = json.loads(self.stdout)
        assert isinstance(value, dict)
        return value

    def stderr_json(self) -> dict[str, Any]:
        lines = self.stderr.splitlines()
        assert len(lines) == 1
        value = json.loads(lines[0])
        assert isinstance(value, dict)
        return value


@pytest.fixture
def fixture_root() -> Path:
    return FIXTURE_ROOT


@pytest.fixture
def run_cli() -> Iterator[Any]:
    """Run the installed package entrypoint in a fresh child process."""

    def run(
        *arguments: str | os.PathLike[str],
        env: Mapping[str, str] | None = None,
        cwd: Path = PROJECT_ROOT,
    ) -> CommandResult:
        child_env = os.environ.copy()
        if env is not None:
            child_env.update(env)
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "triana_labs",
                *(os.fspath(arg) for arg in arguments),
            ],
            cwd=cwd,
            env=child_env,
            check=False,
            capture_output=True,
            timeout=30,
        )
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    yield run


def compact_json(value: Any) -> bytes:
    """Serialize an independently authored ASCII fixture canonically."""

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


def minimal_trace(
    *,
    trace_id: str = "trace-minimal",
    source_trace_id: str = "source-minimal",
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if events is None:
        events = [
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Synthetic question.",
            },
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "Synthetic answer.",
                "is_final": True,
            },
        ]
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": trace_id,
        "source_trace_id": source_trace_id,
        "events": events,
    }


def write_jsonl(path: Path, values: list[Any], *, final_lf: bool = True) -> None:
    payload = b"".join(compact_json(value) for value in values)
    if payload and not final_lf:
        payload = payload[:-1]
    path.write_bytes(payload)


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in path.read_bytes().splitlines():
        value = json.loads(line)
        assert isinstance(value, dict)
        values.append(value)
    return values


def assert_portable_file_bytes(payload: bytes, *, empty_allowed: bool = False) -> None:
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in payload
    if payload or not empty_allowed:
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")


def assert_artifact_bundle(output: Path) -> None:
    assert output.is_dir()
    assert {path.name for path in output.iterdir()} == EXPECTED_ARTIFACT_NAMES
    assert_portable_file_bytes(
        (output / "normalized_traces.jsonl").read_bytes(),
        empty_allowed=True,
    )
    assert_portable_file_bytes(
        (output / "rejected_traces.jsonl").read_bytes(),
        empty_allowed=True,
    )
    for name in ("manifest.json", "corpus_profile.json", "corpus_profile.md"):
        assert_portable_file_bytes((output / name).read_bytes())
