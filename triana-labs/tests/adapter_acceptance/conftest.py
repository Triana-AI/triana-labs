"""Black-box process harness for the standalone HRAI reference adapter."""

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
ADAPTER = PROJECT_ROOT / "examples" / "hrai_v2" / "adapter.py"
ADAPTER_README = PROJECT_ROOT / "examples" / "hrai_v2" / "README.md"
FIXTURES = PROJECT_ROOT / "tests" / "adapter_fixtures"
ARTIFACT_NAMES = {
    "preview_traces.jsonl",
    "rejected_source_traces.jsonl",
}


@dataclass(frozen=True)
class CommandResult:
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


@pytest.fixture(scope="session", autouse=True)
def implementation_files_exist() -> None:
    """Make canonical-base RED attributable only to the missing deliverable."""

    missing = [path for path in (ADAPTER, ADAPTER_README) if not path.is_file()]
    assert not missing, f"missing implementation-owned files: {missing}"


@pytest.fixture
def run_adapter() -> Iterator[Any]:
    def run(
        input_path: str | os.PathLike[str],
        output: str | os.PathLike[str],
        *,
        extra: tuple[str, ...] = ("--data-class", "SYNTHETIC"),
        env: Mapping[str, str] | None = None,
    ) -> CommandResult:
        child_env = os.environ.copy()
        if env is not None:
            child_env.update(env)
        completed = subprocess.run(
            [
                sys.executable,
                os.fspath(ADAPTER),
                os.fspath(input_path),
                "--out",
                os.fspath(output),
                *extra,
            ],
            cwd=PROJECT_ROOT,
            env=child_env,
            check=False,
            capture_output=True,
            timeout=30,
        )
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    yield run


def compact_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def write_jsonl(path: Path, values: list[Any]) -> None:
    path.write_bytes(b"".join(compact_json(value) for value in values))


def parse_jsonl(path: Path) -> list[dict[str, Any]]:
    values = [json.loads(line) for line in path.read_bytes().splitlines()]
    assert all(isinstance(value, dict) for value in values)
    return values


def minimal_source(
    *,
    session_id: str = "synthetic-session-dynamic",
    status: str = "COMPLETED",
) -> dict[str, Any]:
    return {
        "schema_version": "normalized-trace-v2",
        "case_id": "case-dynamic",
        "session_id": session_id,
        "status": status,
        "system_prompt": {"text": "Synthetic system instruction."},
        "turns": [
            {"role": "user", "content": "Synthetic question."},
            {"role": "assistant", "content": "Synthetic answer."},
        ],
        "events": [
            {"turn": 1, "role": "user", "tool_calls": []},
            {"turn": 1, "role": "assistant", "tool_calls": []},
        ],
    }


def assert_bundle(output: Path) -> None:
    assert output.is_dir()
    assert {path.name for path in output.iterdir()} == ARTIFACT_NAMES
    for name in ARTIFACT_NAMES:
        payload = (output / name).read_bytes()
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\r" not in payload
        if payload:
            assert payload.endswith(b"\n")
            assert not payload.endswith(b"\n\n")
