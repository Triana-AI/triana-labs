"""Public CLI harness used by independent acceptance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fixtures.factory import canonical_bytes


@dataclass(frozen=True)
class CliResult:
    returncode: int
    stdout: bytes
    stderr: bytes

    def log_lines(self) -> list[dict[str, Any]]:
        return [
            json.loads(line)
            for line in self.stderr.decode().splitlines()
            if line.strip()
        ]


def run_cli(
    *args: str,
    stdin: bytes | None = None,
    env: dict[str, str] | None = None,
) -> CliResult:
    command = [sys.executable, "-m", "triana", *args]
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    completed = subprocess.run(
        command,
        input=stdin,
        capture_output=True,
        check=False,
        env=process_env,
    )
    return CliResult(completed.returncode, completed.stdout, completed.stderr)


def write_json(path: Path, value: Any, *, pretty: bool = False) -> Path:
    if pretty:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    else:
        path.write_bytes(canonical_bytes(value) + b"\n")
    return path


def write_raw_json(path: Path, value: Any) -> Path:
    """Write an invalid test document without applying domain normalization.

    Negative schema cases can deliberately remove the stable key used by the
    independent canonical oracle.  Sorting object keys here keeps the fixture
    bytes deterministic while allowing the malformed document to reach the
    public CLI unchanged.
    """
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )
    return path


def assert_terminal(
    result: CliResult,
    *,
    event_name: str,
    outcome: str,
    correlation_id: str,
) -> dict[str, Any]:
    logs = result.log_lines()
    assert len(logs) == 1
    event = logs[0]
    assert event["event_name"] == event_name
    assert event["outcome"] == outcome
    assert event["correlation_id"] == correlation_id
    assert event["service"] == "triana-cli"
    return event
