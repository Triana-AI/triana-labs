"""Black-box parsing, canonicalization, and public document tests."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from fixtures.factory import (
    canonical_bytes,
    document_matrix,
    evaluator_gap_record,
    moved_record,
)

from acceptance.support import assert_terminal, run_cli, write_json


@pytest.mark.parametrize(
    ("name", "document"),
    sorted(document_matrix().items()),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_validate_all_minimal_and_complete_public_documents(
    tmp_path: Path,
    name: str,
    document: dict[str, object],
) -> None:
    path = write_json(tmp_path / f"{name}.json", document, pretty=True)
    result = run_cli(
        "contracts",
        "validate",
        str(path),
        "--correlation-id",
        "contract-matrix",
    )
    assert result.returncode == 0
    assert result.stdout == canonical_bytes(document) + b"\n"
    assert_terminal(
        result,
        event_name="triana.contracts.validate.succeeded",
        outcome="SUCCEEDED",
        correlation_id="contract-matrix",
    )


def test_object_key_and_set_permutations_have_identical_output(tmp_path: Path) -> None:
    original = document_matrix()["protected_case.complete"]
    permuted = copy.deepcopy(original)
    permuted["source_evidence"].reverse()  # type: ignore[union-attr]
    permuted["evidence_requirements"].reverse()  # type: ignore[union-attr]
    first = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "first.json", original, pretty=True)),
    )
    second = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "second.json", permuted, pretty=True)),
    )
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout == canonical_bytes(original) + b"\n"


def test_ordered_trace_permutation_changes_identity(tmp_path: Path) -> None:
    original = document_matrix()["normalized_trace.complete"]
    permuted = copy.deepcopy(original)
    events = permuted["events"]
    events[0], events[1] = events[1], events[0]  # type: ignore[index]
    path = write_json(tmp_path / "ordered-mutation.json", permuted)
    result = run_cli("contracts", "validate", str(path))
    assert result.returncode == 5
    assert result.stdout == b""
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


@pytest.mark.parametrize(
    ("mutation", "expected_code", "pointer"),
    [
        ({"contract_kind": "unknown"}, "UNKNOWN_CONTRACT_KIND", "/contract_kind"),
        ({"schema_version": 2}, "UNSUPPORTED_SCHEMA_VERSION", "/schema_version"),
        ({"schema_version": "1"}, "SCHEMA_VALIDATION_FAILED", "/schema_version"),
        ({"trace_hash": "sha256:BAD"}, "HASH_FORMAT_INVALID", "/trace_hash"),
        ({"trace_hash": "sha256:" + ("0" * 64)}, "IDENTITY_MISMATCH", "/trace_hash"),
    ],
)
def test_boundary_and_identity_errors(
    tmp_path: Path,
    mutation: dict[str, object],
    expected_code: str,
    pointer: str,
) -> None:
    document = copy.deepcopy(document_matrix()["normalized_trace.minimal"])
    document.update(mutation)
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "invalid.json", document)),
        "--correlation-id",
        "boundary-errors",
    )
    assert result.returncode in {4, 5, 6}
    assert result.stdout == b""
    event = result.log_lines()[0]
    assert event["code"] == expected_code
    assert event["json_pointer"] == pointer
    assert event["correlation_id"] == "boundary-errors"


def test_duplicate_raw_json_keys_fail_before_schema_validation() -> None:
    path = Path(__file__).parents[1] / "fixtures" / "duplicate_keys.json"
    result = run_cli("contracts", "validate", str(path))
    assert result.returncode == 3
    assert result.stdout == b""
    assert result.log_lines()[0]["code"] == "DUPLICATE_JSON_KEY"


def test_explicit_null_and_unknown_nested_field_are_rejected(tmp_path: Path) -> None:
    document = copy.deepcopy(document_matrix()["protected_case.minimal"])
    document["approval"]["actor_display_name"] = None  # type: ignore[index]
    document["approval"]["invented"] = "forbidden"  # type: ignore[index]
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "closed-object.json", document)),
    )
    assert result.returncode == 4
    event = result.log_lines()[0]
    assert event["code"] == "SCHEMA_VALIDATION_FAILED"
    pointers = [item["json_pointer"] for item in event["errors"]]
    assert pointers == sorted(pointers, key=lambda item: item.encode())


def test_unsafe_https_evidence_locator_is_rejected(tmp_path: Path) -> None:
    document = copy.deepcopy(document_matrix()["decision_attestation.minimal"])
    document["source_reference"]["locator"] = {  # type: ignore[index]
        "locator_kind": "HTTPS",
        "url": "https://user:secret@example.test/evidence?token=secret#fragment",
    }
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "unsafe-locator.json", document)),
    )
    assert result.returncode == 4
    assert result.stdout == b""
    assert b"secret" not in result.stderr
    assert result.log_lines()[0]["code"] == "SCHEMA_VALIDATION_FAILED"


@pytest.mark.parametrize(
    ("name", "document"),
    [
        ("moved", moved_record(sealed=True)),
        ("evaluator-gap", evaluator_gap_record(sealed=True)),
    ],
)
def test_validate_typed_noncomparable_and_gap_records(
    tmp_path: Path,
    name: str,
    document: dict[str, object],
) -> None:
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / f"{name}.json", document, pretty=True)),
    )
    assert result.returncode == 0
    assert result.stdout == canonical_bytes(document) + b"\n"
