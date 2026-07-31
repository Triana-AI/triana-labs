"""Acceptance checks that prove the RED harness reaches the public CLI."""

from __future__ import annotations

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
