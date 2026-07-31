"""Acceptance checks that prove the RED harness reaches the public CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def test_help_is_functional_and_silent(run_cli: Any) -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert b"traces" in result.stdout
    assert result.stderr == b""


def test_observe_help_is_functional_and_silent(run_cli: Any) -> None:
    result = run_cli("traces", "observe", "--help")

    assert result.returncode == 0
    assert b"--out" in result.stdout
    assert result.stderr == b""


def test_red_scaffold_returns_safe_not_implemented(
    run_cli: Any,
    fixture_root: Path,
    tmp_path: Path,
) -> None:
    result = run_cli(
        "traces",
        "observe",
        fixture_root / "valid_all_events.jsonl",
        "--out",
        tmp_path / "output",
    )

    assert result.returncode == 70
    assert result.stdout == b""
    assert json.loads(result.stderr) == {
        "command": "traces.observe",
        "event_name": "triana.traces.observe.rejected",
        "outcome": "NOT_IMPLEMENTED",
        "reason_code": "NOT_IMPLEMENTED",
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "ERROR",
    }
    assert not (tmp_path / "output").exists()
