"""Orchestrator-owned adversarial checks reserved by the Slice 0A freeze."""

from __future__ import annotations

import copy
import hashlib
import importlib
import io
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from acceptance.support import run_cli
from fixtures.factory import (
    complete_trace,
    evaluator_gap_record,
    record_chain,
    sealed_record,
    with_self_hash,
)

JsonObject = dict[str, Any]

_SET_KEYS: dict[str, str | tuple[str, ...] | None] = {
    "applicability_conditions": "statement_id",
    "expected_behavior": "statement_id",
    "prohibited_behavior": "statement_id",
    "allowed_alternatives": "statement_id",
    "capabilities": None,
    "source_evidence": "reference_id",
    "evidence_references": "reference_id",
    "unresolved_difference_references": "reference_id",
    "evidence_requirements": "requirement_id",
    "customer_evaluator_results": ("evaluator_id", "check_id", "result_id"),
    "gaps": "gap_id",
    "record_gaps": "gap_id",
    "components": "component_kind",
    "reason_codes": None,
    "flags": None,
    "pattern_flags": None,
    "gap_ids": None,
}


def _normalize(value: Any, field: str | None = None, *, opaque: bool = False) -> Any:
    if isinstance(value, dict):
        result: JsonObject = {}
        for key, item in value.items():
            child_opaque = (
                opaque
                or (key == "arguments" and value.get("event_kind") == "TOOL_CALL")
                or (
                    key == "result"
                    and value.get("event_kind") == "TOOL_RESULT"
                    and value.get("result_state") == "SUCCEEDED"
                )
            )
            result[key] = _normalize(item, key, opaque=child_opaque)
        return result
    if isinstance(value, list):
        items = [_normalize(item, opaque=opaque) for item in value]
        if not opaque and field in _SET_KEYS:
            key = _SET_KEYS[field]
            if key is None:
                items.sort()
            elif isinstance(key, tuple):
                items.sort(key=lambda item: tuple(item[part] for part in key))
            else:
                items.sort(key=lambda item: item[key])
        return items
    return copy.deepcopy(value)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _with_hash(value: JsonObject, kind: str, field: str) -> JsonObject:
    result = copy.deepcopy(value)
    result.pop(field, None)
    preimage = b"triana\x00" + kind.encode() + b"\x00v1\x00" + _canonical(result)
    result[field] = "sha256:" + hashlib.sha256(preimage).hexdigest()
    return result


def _write(path: Path, value: Any) -> Path:
    path.write_bytes(_canonical(value) + b"\n")
    return path


@pytest.mark.parametrize(
    "arguments",
    [
        {"reason_codes": ["B", "A"]},
        {"seal_state": "SEALED"},
        {"content_hash": "customer-owned-value"},
        {"events": list(range(10_001))},
    ],
)
def test_sensitive_arguments_are_opaque_to_triana_semantics(
    tmp_path: Path, arguments: JsonObject
) -> None:
    trace = complete_trace()
    trace["events"][3]["arguments"] = arguments
    trace = _with_hash(trace, "normalized_trace", "trace_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "opaque.json", trace))
    )
    assert result.returncode == 0
    emitted = json.loads(result.stdout)
    assert emitted["events"][3]["arguments"] == arguments


def test_successful_tool_result_preserves_explicit_null(tmp_path: Path) -> None:
    trace = complete_trace()
    trace["events"][4]["result"] = None
    trace = _with_hash(trace, "normalized_trace", "trace_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "null-result.json", trace))
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["events"][4]["result"] is None


@pytest.mark.parametrize("key", ["", "x" * 257])
def test_sensitive_json_object_keys_obey_exact_domain(tmp_path: Path, key: str) -> None:
    trace = complete_trace()
    trace["events"][3]["arguments"] = {key: "value"}
    trace = _with_hash(trace, "normalized_trace", "trace_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "bad-key.json", trace))
    )
    assert result.returncode == 4
    event = result.log_lines()[0]
    assert event["code"] == "SCHEMA_VALIDATION_FAILED"
    if key:
        assert key.encode() not in result.stderr


@pytest.mark.parametrize("value", ["1.000001", "1.999999"])
def test_fixed_rate_rejects_values_above_one(tmp_path: Path, value: str) -> None:
    record = sealed_record()
    record["comparison"]["candidate"]["pass_rate"] = value
    record = with_self_hash(record, "release_evidence_record", "current_record_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "bad-rate.json", record))
    )
    assert result.returncode == 4
    assert result.log_lines()[0]["code"] == "SCHEMA_VALIDATION_FAILED"


def test_matched_trials_require_identical_paired_randomization(
    tmp_path: Path,
) -> None:
    record = sealed_record(complete=True)
    record["trials"][1]["randomization"]["seed"] = "different-seed"
    record = with_self_hash(record, "release_evidence_record", "current_record_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "seed-mismatch.json", record))
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


def test_record_gap_must_be_record_scoped(tmp_path: Path) -> None:
    record = evaluator_gap_record(sealed=False)
    record["record_gaps"] = [copy.deepcopy(record["trials"][1]["gaps"][0])]
    record["seal_state"] = "SEALED"
    record = with_self_hash(record, "release_evidence_record", "current_record_hash")
    result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "record-gap.json", record))
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


def test_superseded_hash_is_distinct_in_record_and_chain(tmp_path: Path) -> None:
    previous = "sha256:" + "8" * 64
    record = sealed_record(complete=True)
    record["chain_link"] = {
        "link_kind": "APPEND",
        "previous_record_hash": previous,
        "supersedes_record_hash": previous,
    }
    record = with_self_hash(record, "release_evidence_record", "current_record_hash")
    record_result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "record.json", record))
    )

    chain = record_chain(complete=True)
    chain["entries"][1]["supersedes_record_hash"] = chain["entries"][1][
        "previous_record_hash"
    ]
    chain = with_self_hash(chain, "record_chain", "chain_hash")
    chain_result = run_cli(
        "contracts", "validate", str(_write(tmp_path / "chain.json", chain))
    )

    for result in (record_result, chain_result):
        assert result.returncode == 5
        assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


def _walk_schema(value: Any) -> None:
    if isinstance(value, dict):
        assert value.get("default", object()) is not None
        for item in value.values():
            _walk_schema(item)
    elif isinstance(value, list):
        for item in value:
            _walk_schema(item)


def test_generated_schemas_pin_version_and_omit_invalid_null_defaults() -> None:
    schema_directory = Path(__file__).parents[2] / "schemas"
    for path in sorted(schema_directory.glob("*.schema.json")):
        schema = json.loads(path.read_text())
        assert schema["properties"]["schema_version"]["const"] == 1
        _walk_schema(schema)


class _CapturedStdout:
    def __init__(self) -> None:
        self.buffer = io.BytesIO()


class _BrokenStdout:
    class _Buffer:
        def write(self, _value: bytes) -> int:
            raise BrokenPipeError

        def flush(self) -> None:
            return None

    def __init__(self) -> None:
        self.buffer = self._Buffer()


def test_output_write_failure_is_typed_and_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = importlib.import_module("triana.cli.main")
    trace = complete_trace()
    path = _write(tmp_path / "valid.json", trace)
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stdout", _BrokenStdout())
    monkeypatch.setattr(sys, "stderr", stderr)

    exit_code = cli.main(
        ["contracts", "validate", str(path), "--correlation-id", "write-failure"]
    )

    assert exit_code == 7
    events = [json.loads(line) for line in stderr.getvalue().splitlines()]
    assert len(events) == 1
    assert events[0]["code"] == "OUTPUT_WRITE_FAILED"
    assert events[0]["correlation_id"] == "write-failure"


def test_log_serialization_failure_fails_before_artifact_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = importlib.import_module("triana.cli.main")
    logging = importlib.import_module("triana.cli.logging")
    path = _write(tmp_path / "valid.json", complete_trace())
    stdout = _CapturedStdout()
    stderr = io.StringIO()

    def fail_serialization(_event: JsonObject) -> str:
        raise ValueError("UNSAFE-SERIALIZATION-SENTINEL")

    monkeypatch.setattr(logging, "_serialize_event", fail_serialization)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    exit_code = cli.main(
        ["contracts", "validate", str(path), "--correlation-id", "log-failure"]
    )

    assert exit_code == 70
    assert stdout.buffer.getvalue() == b""
    assert "UNSAFE-SERIALIZATION-SENTINEL" not in stderr.getvalue()
    events = [json.loads(line) for line in stderr.getvalue().splitlines()]
    assert len(events) == 1
    assert events[0] == {
        "code": "LOG_REDACTION_FAILED",
        "command": "logging",
        "correlation_id": "log-failure",
        "duration_ms": 0,
        "event_name": "triana.logging.rejected",
        "outcome": "REJECTED",
        "reason_code": "LOG_REDACTION_FAILED",
        "safe_message": "Terminal logging failed safely.",
        "service": "triana-cli",
        "service_version": "0.0.0",
        "severity": "ERROR",
        "timestamp": events[0]["timestamp"],
    }
