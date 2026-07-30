"""Deterministic mutation/property evidence for the contract boundary."""

from __future__ import annotations

import copy
import json

from fixtures.factory import (
    canonical_bytes,
    document_matrix,
    fixture_universe_hash,
)
from hypothesis import given, seed
from hypothesis import strategies as st


@seed(2026073001)
@given(st.permutations(["MODEL_OUTPUT", "TOOL_DISPATCH", "TERMINAL_STATE"]))
def test_set_normalization_is_permutation_invariant(
    permutation: list[str],
) -> None:
    value = {"capabilities": permutation}
    expected = {"capabilities": ["MODEL_OUTPUT", "TERMINAL_STATE", "TOOL_DISPATCH"]}
    assert canonical_bytes(value) == canonical_bytes(expected)


@seed(2026073001)
@given(st.sampled_from(sorted(document_matrix())))
def test_canonicalization_is_idempotent(document_name: str) -> None:
    value = document_matrix()[document_name]
    once = canonical_bytes(value)
    twice = canonical_bytes(json.loads(once))
    assert once == twice


def test_fixture_manifest_records_fixed_property_evidence(
    fixture_manifest: dict[str, object],
) -> None:
    assert fixture_manifest == {
        "fixture_universe_hash": fixture_universe_hash(),
        "hypothesis_version": "6.163.1",
        "profile": "slice0a",
        "seed": 2026073001,
        "reproduction_blob_policy": "present_only_on_failure",
        "property_tests": [
            {
                "test_node_id": (
                    "tests/acceptance/test_properties.py::"
                    "test_set_normalization_is_permutation_invariant"
                ),
                "outcome": "PASS",
            },
            {
                "test_node_id": (
                    "tests/acceptance/test_properties.py::"
                    "test_canonicalization_is_idempotent"
                ),
                "outcome": "PASS",
            },
        ],
    }
    for item in fixture_manifest["property_tests"]:  # type: ignore[index]
        assert "reproduction_blob" not in item


def test_fixture_mutation_does_not_mutate_source() -> None:
    source = document_matrix()["release_evidence_record.sealed_minimal"]
    before = copy.deepcopy(source)
    mutated = copy.deepcopy(source)
    mutated["project_id"] = "project-mutated"
    assert source == before
    assert mutated != source
