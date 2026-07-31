"""Black-box record sealing, verification, and tamper tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from fixtures.factory import canonical_bytes, sealed_record, unsigned_record

from acceptance.support import assert_terminal, run_cli, write_json


@pytest.mark.parametrize("complete", [False, True], ids=["minimal", "complete"])
def test_seal_unsigned_record_matches_independent_golden(
    tmp_path: Path, complete: bool
) -> None:
    unsigned = unsigned_record(complete=complete)
    expected = sealed_record(complete=complete)
    path = write_json(tmp_path / "unsigned.json", unsigned, pretty=True)
    result = run_cli(
        "records",
        "seal",
        str(path),
        "--correlation-id",
        "seal-record",
    )
    assert result.returncode == 0
    assert result.stdout == canonical_bytes(expected) + b"\n"
    event = assert_terminal(
        result,
        event_name="triana.records.seal.succeeded",
        outcome="SUCCEEDED",
        correlation_id="seal-record",
    )
    assert event["record_hash"] == expected["current_record_hash"]


@pytest.mark.parametrize("complete", [False, True], ids=["minimal", "complete"])
def test_verify_sealed_record_returns_exact_receipt(
    tmp_path: Path, complete: bool
) -> None:
    record = sealed_record(complete=complete)
    path = write_json(tmp_path / "sealed.json", record)
    result = run_cli(
        "records",
        "verify",
        str(path),
        "--correlation-id",
        "verify-record",
    )
    expected = canonical_bytes(
        {"record_hash": record["current_record_hash"], "verified": True}
    )
    assert result.returncode == 0
    assert result.stdout == expected + b"\n"
    assert_terminal(
        result,
        event_name="triana.records.verify.succeeded",
        outcome="SUCCEEDED",
        correlation_id="verify-record",
    )


@pytest.mark.parametrize(
    ("path_parts", "replacement"),
    [
        (("project_id",), "project-tampered"),
        (("release_change", "candidate_code_ref"), "candidate-tampered"),
        (("policy_evaluation", "rule_id"), "rule-tampered"),
        (("recommendation",), "BLOCK"),
        (
            ("chain_link",),
            {"link_kind": "APPEND", "previous_record_hash": "sha256:" + "a" * 64},
        ),
    ],
)
def test_protected_field_tampering_is_rejected(
    tmp_path: Path,
    path_parts: tuple[str, ...],
    replacement: object,
) -> None:
    record = sealed_record()
    target: dict[str, object] = record
    for part in path_parts[:-1]:
        target = target[part]  # type: ignore[assignment]
    target[path_parts[-1]] = replacement
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / "tampered.json", record)),
    )
    assert result.returncode in {5, 6}
    assert result.stdout == b""
    assert result.log_lines()[0]["code"] in {"IMPOSSIBLE_STATE", "HASH_MISMATCH"}


def test_seal_rejects_sealed_and_verify_rejects_unsigned(tmp_path: Path) -> None:
    sealed_path = write_json(tmp_path / "sealed.json", sealed_record())
    unsigned_path = write_json(tmp_path / "unsigned.json", unsigned_record())
    seal_result = run_cli("records", "seal", str(sealed_path))
    verify_result = run_cli("records", "verify", str(unsigned_path))
    for result in (seal_result, verify_result):
        assert result.returncode == 5
        assert result.stdout == b""
        event = result.log_lines()[0]
        assert event["code"] == "IMPOSSIBLE_STATE"
        assert event["json_pointer"] == "/seal_state"


def test_verification_does_not_modify_input_file(tmp_path: Path) -> None:
    path = write_json(tmp_path / "sealed.json", sealed_record(), pretty=True)
    before = path.read_bytes()
    result = run_cli("records", "verify", str(path))
    assert result.returncode == 0
    assert path.read_bytes() == before
