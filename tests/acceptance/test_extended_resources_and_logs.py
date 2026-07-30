"""Resource, error aggregation, and structured-log acceptance matrices."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from fixtures.factory import complete_trace, sealed_record

from acceptance.support import run_cli, write_json


def test_input_read_failure_is_safe_and_typed(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.json"
    result = run_cli(
        "contracts",
        "validate",
        str(missing),
        "--correlation-id",
        "missing-file",
    )
    assert result.returncode == 2
    assert result.stdout == b""
    assert str(missing).encode() not in result.stderr
    event = result.log_lines()[0]
    assert event["code"] == "INPUT_READ_FAILED"
    assert event["correlation_id"] == "missing-file"


def test_nesting_depth_limit_precedes_schema(tmp_path: Path) -> None:
    nested: object = "leaf"
    for _ in range(65):
        nested = [nested]
    trace = complete_trace()
    trace["events"][3]["arguments"] = nested
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "deep.json", trace)),
    )
    assert result.returncode == 3
    assert result.log_lines()[0]["code"] == "NESTING_TOO_DEEP"


def test_validation_error_cap_shape_and_order(tmp_path: Path) -> None:
    trace = complete_trace()
    for index in range(105):
        trace[f"unknown_{index:03d}"] = index
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "many-errors.json", trace)),
    )
    assert result.returncode == 4
    event = result.log_lines()[0]
    assert event["code"] == "SCHEMA_VALIDATION_FAILED"
    assert len(event["errors"]) == 100
    real = event["errors"][:99]
    assert [item["json_pointer"] for item in real] == sorted(
        (item["json_pointer"] for item in real),
        key=lambda item: item.encode(),
    )
    assert event["errors"][-1] == {
        "code": "VALIDATION_ERROR_LIMIT_REACHED",
        "json_pointer": "",
        "safe_message": "Additional validation errors were omitted.",
    }


_REQUIRED_LOG_FIELDS = {
    "timestamp",
    "event_name",
    "severity",
    "service",
    "service_version",
    "command",
    "outcome",
    "correlation_id",
    "duration_ms",
}


@pytest.mark.parametrize(
    ("command", "event_name"),
    [
        (
            ("contracts", "validate"),
            "triana.contracts.validate.succeeded",
        ),
        (("records", "seal"), "triana.records.seal.succeeded"),
        (("records", "verify"), "triana.records.verify.succeeded"),
    ],
)
def test_success_logs_have_required_fields_and_correlation(
    tmp_path: Path,
    command: tuple[str, str],
    event_name: str,
) -> None:
    source = sealed_record() if command[1] != "seal" else copy.deepcopy(sealed_record())
    if command[1] == "seal":
        source["seal_state"] = "UNSIGNED"
        del source["current_record_hash"]
    path = write_json(tmp_path / f"{command[1]}.json", source)
    result = run_cli(
        *command,
        str(path),
        "--correlation-id",
        f"correlation-{command[1]}",
    )
    assert result.returncode == 0
    logs = result.log_lines()
    assert len(logs) == 1
    event = logs[0]
    assert _REQUIRED_LOG_FIELDS <= event.keys()
    assert event["event_name"] == event_name
    assert event["outcome"] == "SUCCEEDED"
    assert event["severity"] == "INFO"
    assert event["correlation_id"] == f"correlation-{command[1]}"


def test_rejection_log_has_required_fields_and_reason_code() -> None:
    sentinel = "MALFORMED-SECRET-VALUE"
    result = run_cli(
        "contracts",
        "validate",
        "-",
        "--correlation-id",
        "rejection-log",
        stdin=f'{{"secret":"{sentinel}"'.encode(),
    )
    assert result.returncode == 3
    assert sentinel.encode() not in result.stderr
    event = result.log_lines()[0]
    assert _REQUIRED_LOG_FIELDS <= event.keys()
    assert event["event_name"] == "triana.contracts.validate.rejected"
    assert event["outcome"] == "REJECTED"
    assert event["severity"] == "WARN"
    assert event["reason_code"] == "MALFORMED_JSON"
    assert event["code"] == "MALFORMED_JSON"


@pytest.mark.parametrize(
    ("category", "path", "sensitive_value", "sentinel"),
    [
        (
            "prompt",
            ("events", 0, "content"),
            "PROMPT-SECRET-SENTINEL",
            "PROMPT-SECRET-SENTINEL",
        ),
        (
            "tool-arguments",
            ("events", 3, "arguments"),
            {"token": "TOOL-ARGUMENT-SECRET"},
            "TOOL-ARGUMENT-SECRET",
        ),
        (
            "tool-result",
            ("events", 4, "result"),
            {"cookie": "TOOL-RESULT-COOKIE"},
            "TOOL-RESULT-COOKIE",
        ),
        (
            "model-output",
            ("events", 2, "output"),
            "MODEL-OUTPUT-SECRET",
            "MODEL-OUTPUT-SECRET",
        ),
    ],
)
def test_sensitive_trace_categories_never_reach_rejection_logs(
    tmp_path: Path,
    category: str,
    path: tuple[str | int, ...],
    sensitive_value: object,
    sentinel: str,
) -> None:
    trace = complete_trace()
    target = trace
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = sensitive_value
    trace["trace_hash"] = "sha256:" + "0" * 64
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / f"{category}.json", trace)),
    )
    assert result.returncode == 5
    assert sentinel.encode() not in result.stderr


def test_locator_and_forbidden_header_cookie_environment_are_not_logged(
    tmp_path: Path,
) -> None:
    record = sealed_record(complete=True)
    record["pr_reference"]["locator"]["url"] = (  # type: ignore[index]
        "https://github.example/synthetic/pull/SECRET-PATH"
    )
    record["authorization_header"] = "Bearer HEADER-SECRET"
    record["cookie"] = "COOKIE-SECRET"
    record["environment_value"] = "ENV-SECRET"
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "forbidden-sensitive-fields.json", record)),
    )
    assert result.returncode == 4
    for sentinel in [
        b"SECRET-PATH",
        b"HEADER-SECRET",
        b"COOKIE-SECRET",
        b"ENV-SECRET",
    ]:
        assert sentinel not in result.stderr


def test_canonical_artifact_is_invariant_under_logging_configuration(
    tmp_path: Path,
) -> None:
    record = sealed_record()
    path = write_json(tmp_path / "record.json", record, pretty=True)
    first = run_cli(
        "contracts",
        "validate",
        str(path),
        "--correlation-id",
        "logging-a",
        env={"TRIANA_LOG_LEVEL": "INFO"},
    )
    second = run_cli(
        "contracts",
        "validate",
        str(path),
        "--correlation-id",
        "logging-b",
        env={"TRIANA_LOG_LEVEL": "DEBUG"},
    )
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
