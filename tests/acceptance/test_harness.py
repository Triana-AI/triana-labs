"""Passing self-checks for the independent fixture/test harness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fixtures.contract_coverage import (
    DOCUMENTED_FAMILIES,
    OBJECT_COVERAGE,
    PUBLIC_KINDS,
    RELEASE_RECORD_PROTECTED_FIELDS,
    closed_boundary_cases,
    required_path_cases,
)
from fixtures.factory import (
    canonical_bytes,
    document_matrix,
    fixture_universe_hash,
)


def test_independent_canonical_oracle_matches_hand_authored_vector() -> None:
    fixtures = Path(__file__).parents[1] / "fixtures"
    expected = (fixtures / "jcs_expected.txt").read_bytes()
    value = __import__("json").loads((fixtures / "jcs_input.json").read_text())
    assert canonical_bytes(value) + b"\n" == expected


def test_plain_sha256_oracle_known_vector() -> None:
    assert hashlib.sha256(b"abc").hexdigest() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_fixture_matrix_is_synthetic_and_complete() -> None:
    matrix = document_matrix()
    assert len(matrix) == 12
    assert {value["contract_kind"] for value in matrix.values()} == {
        "normalized_trace",
        "protected_case",
        "release_evidence_record",
        "record_chain",
        "decision_attestation",
    }
    assert fixture_universe_hash().startswith("sha256:")


def test_each_document_matches_frozen_independent_golden() -> None:
    fixtures = Path(__file__).parents[1] / "fixtures"
    goldens = json.loads((fixtures / "goldens.json").read_text())
    identity_fields = {
        "normalized_trace": "trace_hash",
        "protected_case": "case_version",
        "release_evidence_record": "current_record_hash",
        "record_chain": "chain_hash",
        "decision_attestation": "attestation_hash",
    }
    for name, document in sorted(document_matrix().items()):
        expected = goldens[name]
        assert expected["canonical_sha256"] == (
            "sha256:" + hashlib.sha256(canonical_bytes(document)).hexdigest()
        )
        assert expected["self_identity"] == document.get(
            identity_fields[document["contract_kind"]]
        )


def test_contract_coverage_manifest_is_unique_resolvable_and_complete() -> None:
    object_names = [item.name for item in OBJECT_COVERAGE]
    required = required_path_cases()
    boundaries = closed_boundary_cases()

    assert len(object_names) == len(set(object_names))
    assert len(required) == len({name for name, _, _ in required})
    assert len(boundaries) == len({name for name, _, _ in boundaries})
    assert len(required) == len({(name, path) for name, _, path in required})
    assert {item.public_kind for item in OBJECT_COVERAGE} == PUBLIC_KINDS
    assert {item.family for item in OBJECT_COVERAGE} == DOCUMENTED_FAMILIES

    for item in OBJECT_COVERAGE:
        assert len(item.required_fields) == len(set(item.required_fields))
        target: object = item.factory()
        for part in item.path:
            target = target[part]  # type: ignore[index]
        assert isinstance(target, dict)
        assert set(item.required_fields) <= target.keys()

    record = next(
        item for item in OBJECT_COVERAGE if item.family == "release_evidence_record"
    )
    assert set(RELEASE_RECORD_PROTECTED_FIELDS) == (
        set(record.required_fields) - {"current_record_hash"}
    ) | {"pr_reference"}
