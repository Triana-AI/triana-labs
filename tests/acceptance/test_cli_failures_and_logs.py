"""CLI failure, resource, privacy, and logging acceptance behavior."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures.factory import minimal_trace

from acceptance.support import run_cli, write_json


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        (b"\xff", "INVALID_UTF8"),
        (b"\xef\xbb\xbf{}", "BOM_FORBIDDEN"),
        (b"{", "MALFORMED_JSON"),
    ],
)
def test_raw_input_failures_are_safe(payload: bytes, expected_code: str) -> None:
    result = run_cli(
        "contracts",
        "validate",
        "-",
        "--correlation-id",
        "raw-input",
        stdin=payload,
    )
    assert result.returncode == 3
    assert result.stdout == b""
    event = result.log_lines()[0]
    assert event["code"] == expected_code
    assert event["correlation_id"] == "raw-input"


def test_input_size_limit_fails_at_raw_boundary() -> None:
    payload = b" " * (16_777_216 + 1)
    result = run_cli("contracts", "validate", "-", stdin=payload)
    assert result.returncode == 3
    assert result.log_lines()[0]["code"] == "INPUT_TOO_LARGE"


def test_decoded_string_limit_is_enforced(tmp_path: Path) -> None:
    document = minimal_trace()
    document["events"][0]["content"] = "x" * (1_048_576 + 1)  # type: ignore[index]
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "large-string.json", document)),
    )
    assert result.returncode == 3
    assert result.log_lines()[0]["code"] == "STRING_TOO_LARGE"


def test_trace_event_collection_limit_is_enforced(tmp_path: Path) -> None:
    document = minimal_trace()
    event = document["events"][0]  # type: ignore[index]
    document["events"] = [
        {**event, "event_id": f"event-{index}", "sequence": index}
        for index in range(10_001)
    ]
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "too-many-events.json", document)),
    )
    assert result.returncode == 3
    assert result.log_lines()[0]["code"] == "COLLECTION_TOO_LARGE"


def test_sensitive_trace_values_never_appear_in_logs(tmp_path: Path) -> None:
    secret = "TRIANA-SECRET-SENTINEL-42"
    document = minimal_trace()
    document["events"][0]["content"] = secret  # type: ignore[index]
    document["trace_hash"] = "sha256:" + ("0" * 64)
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "secret.json", document)),
        "--correlation-id",
        "redaction-check",
    )
    assert result.returncode == 5
    assert secret.encode() not in result.stderr
    assert str(tmp_path).encode() not in result.stderr
    assert result.log_lines()[0]["correlation_id"] == "redaction-check"


def test_logs_and_artifacts_use_separate_channels(tmp_path: Path) -> None:
    document = minimal_trace()
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "valid.json", document)),
    )
    assert result.returncode == 0
    assert result.stdout.startswith(b"{")
    assert b"event_name" not in result.stdout
    assert len(result.log_lines()) == 1


def test_help_is_informational_without_terminal_json() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    assert b"usage:" in result.stdout
    assert result.stderr == b""


def test_unknown_command_uses_safe_cli_terminal_event() -> None:
    result = run_cli("unknown-command")
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.lstrip().startswith(b"{")
    event = result.log_lines()[0]
    assert event["event_name"] == "triana.cli.rejected"
    assert event["command"] == "cli"
    assert event["code"] == "CLI_USAGE_ERROR"


def test_invalid_correlation_id_is_not_echoed(tmp_path: Path) -> None:
    unsafe = "unsafe\nforged-event"
    path = write_json(tmp_path / "trace.json", minimal_trace())
    result = run_cli(
        "contracts",
        "validate",
        str(path),
        "--correlation-id",
        unsafe,
    )
    assert result.returncode == 2
    assert unsafe.encode() not in result.stderr
    event = result.log_lines()[0]
    assert event["event_name"] == "triana.cli.rejected"
    assert event["correlation_id"] != unsafe
