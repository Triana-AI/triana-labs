"""Canonical, identity, tamper, and cross-field acceptance matrices."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from fixtures.contract_coverage import RELEASE_RECORD_PROTECTED_FIELDS
from fixtures.factory import (
    canonical_bytes,
    complete_trace,
    decision_attestation,
    domain_hash,
    evaluator_gap_record,
    protected_case,
    sealed_record,
    with_self_hash,
)

from acceptance.support import run_cli, write_json


def _assign(value: Any, path: tuple[str | int, ...], replacement: Any) -> None:
    target = value
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = replacement


def test_unicode_preservation_and_escaped_literal_equivalence(tmp_path: Path) -> None:
    composed = complete_trace()
    composed["events"][1]["content"] = "caf\u00e9"
    composed = with_self_hash(composed, "normalized_trace", "trace_hash")
    decomposed = copy.deepcopy(composed)
    decomposed["events"][1]["content"] = "cafe\u0301"
    decomposed = with_self_hash(decomposed, "normalized_trace", "trace_hash")
    composed_path = write_json(tmp_path / "composed.json", composed)
    decomposed_path = write_json(tmp_path / "decomposed.json", decomposed)
    escaped_path = tmp_path / "escaped.json"
    escaped_path.write_text(json.dumps(composed, ensure_ascii=True))

    composed_result = run_cli("contracts", "validate", str(composed_path))
    decomposed_result = run_cli("contracts", "validate", str(decomposed_path))
    escaped_result = run_cli("contracts", "validate", str(escaped_path))

    assert composed_result.returncode == decomposed_result.returncode == 0
    assert escaped_result.returncode == 0
    assert composed_result.stdout == escaped_result.stdout
    assert composed_result.stdout != decomposed_result.stdout
    assert composed["trace_hash"] != decomposed["trace_hash"]


def test_allowed_control_is_canonically_escaped(tmp_path: Path) -> None:
    trace = complete_trace()
    trace["events"][1]["content"] = "line\nbreak"
    trace = with_self_hash(trace, "normalized_trace", "trace_hash")
    result = run_cli(
        "contracts", "validate", str(write_json(tmp_path / "newline.json", trace))
    )
    assert result.returncode == 0
    assert b"line\\nbreak" in result.stdout
    assert b"line\nbreak" not in result.stdout


def test_safe_integer_and_decimal_boundaries_are_accepted(tmp_path: Path) -> None:
    trace = complete_trace()
    trace["events"][2]["latency_ms"] = 9_007_199_254_740_991
    trace["events"][2]["cost_amount"] = "0"
    trace = with_self_hash(trace, "normalized_trace", "trace_hash")
    result = run_cli(
        "contracts", "validate", str(write_json(tmp_path / "bounds.json", trace))
    )
    assert result.returncode == 0
    assert result.stdout == canonical_bytes(trace) + b"\n"


def test_duplicate_set_key_is_impossible_state(tmp_path: Path) -> None:
    case = protected_case(complete=True)
    duplicate = copy.deepcopy(case["release_obligation"]["allowed_alternatives"][0])
    duplicate["text"] = "Different text, same stable key."
    case["release_obligation"]["allowed_alternatives"].append(duplicate)
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "duplicate-set-key.json", case)),
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


def test_cross_process_locale_timezone_stability(tmp_path: Path) -> None:
    record = sealed_record(complete=True)
    path = write_json(tmp_path / "stable.json", record, pretty=True)
    first = run_cli(
        "contracts",
        "validate",
        str(path),
        env={"TZ": "UTC", "LC_ALL": "C"},
    )
    second = run_cli(
        "contracts",
        "validate",
        str(path),
        env={"TZ": "Asia/Kolkata", "LC_ALL": "C"},
    )
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout == canonical_bytes(record) + b"\n"


def test_hash_domain_separation_is_independent_harness_fact() -> None:
    value = {"same": "canonical-value"}
    assert domain_hash("normalized_trace", value) != domain_hash(
        "protected_case", value
    )


@pytest.mark.parametrize(
    ("name", "mutation", "expected_code", "expected_exit"),
    [
        ("missing-hash", None, "SCHEMA_VALIDATION_FAILED", 4),
        ("replaced-hash", "sha256:" + "0" * 64, "HASH_MISMATCH", 6),
        ("algorithm-confusion", "sha512:" + "0" * 64, "HASH_FORMAT_INVALID", 6),
    ],
)
def test_stored_record_hash_missing_replaced_or_confused(
    tmp_path: Path,
    name: str,
    mutation: str | None,
    expected_code: str,
    expected_exit: int,
) -> None:
    record = sealed_record()
    if mutation is None:
        del record["current_record_hash"]
    else:
        record["current_record_hash"] = mutation
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / f"{name}.json", record)),
    )
    assert result.returncode == expected_exit
    assert result.log_lines()[0]["code"] == expected_code


def test_cross_kind_hash_copy_is_identity_mismatch(tmp_path: Path) -> None:
    trace = complete_trace()
    case = protected_case()
    case["case_version"] = trace["trace_hash"]
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "cross-kind.json", case)),
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IDENTITY_MISMATCH"


@pytest.mark.parametrize(
    ("name", "factory", "path", "replacement", "expected_code"),
    [
        (
            "release-change",
            sealed_record,
            ("release_change", "change_id"),
            "changed-id",
            "HASH_MISMATCH",
        ),
        (
            "obligation",
            sealed_record,
            ("release_obligation", "severity"),
            "CRITICAL",
            "HASH_MISMATCH",
        ),
        (
            "requirements",
            sealed_record,
            ("evidence_requirements", 0, "minimum_trials"),
            2,
            "HASH_MISMATCH",
        ),
        (
            "execution-contract",
            sealed_record,
            (
                "execution_contracts",
                "candidate_execution_contract",
                "command_hash",
            ),
            "sha256:" + "1" * 64,
            "IDENTITY_MISMATCH",
        ),
        (
            "runtime",
            lambda: sealed_record(complete=True),
            ("trials", 0, "runtime_fingerprint", "components", 0, "fingerprint"),
            "sha256:" + "2" * 64,
            "IDENTITY_MISMATCH",
        ),
        (
            "assertion-result",
            lambda: sealed_record(complete=True),
            ("trials", 0, "assertion_results", 0, "reason_code"),
            "CHANGED_REASON",
            "HASH_MISMATCH",
        ),
        (
            "evaluator-result",
            lambda: sealed_record(complete=True),
            ("trials", 0, "customer_evaluator_results", 0, "score"),
            "0.5",
            "HASH_MISMATCH",
        ),
        (
            "trial-gap",
            lambda: evaluator_gap_record(sealed=True),
            ("trials", 1, "gaps", 0, "stage"),
            "ASSERTION",
            "HASH_MISMATCH",
        ),
        (
            "comparison",
            sealed_record,
            ("evidence_strength",),
            "INSUFFICIENT",
            "HASH_MISMATCH",
        ),
        (
            "policy",
            sealed_record,
            ("policy_evaluation", "policy_hash"),
            "sha256:" + "3" * 64,
            "HASH_MISMATCH",
        ),
        (
            "record-gap",
            sealed_record,
            ("record_gaps", 0, "stage"),
            "EXECUTION",
            "HASH_MISMATCH",
        ),
        (
            "evidence-reference",
            sealed_record,
            ("release_change", "declaration_reference", "content_hash"),
            "sha256:" + "4" * 64,
            "HASH_MISMATCH",
        ),
    ],
)
def test_nested_evidence_category_mutation_is_detected(
    tmp_path: Path,
    name: str,
    factory: Any,
    path: tuple[str | int, ...],
    replacement: Any,
    expected_code: str,
) -> None:
    record = factory()
    _assign(record, path, replacement)
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / f"{name}.json", record)),
    )
    expected_exit = 5 if expected_code == "IDENTITY_MISMATCH" else 6
    assert result.returncode == expected_exit
    assert result.log_lines()[0]["code"] == expected_code


def test_schema_error_precedes_bad_stored_hash(tmp_path: Path) -> None:
    record = sealed_record()
    record["recommendation"] = "UNKNOWN"
    record["current_record_hash"] = "sha256:" + "0" * 64
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / "precedence.json", record)),
    )
    assert result.returncode == 4
    assert result.log_lines()[0]["code"] == "SCHEMA_VALIDATION_FAILED"


def test_set_reorder_preserves_sealed_record_verification(tmp_path: Path) -> None:
    record = sealed_record(complete=True)
    record["evidence_requirements"].reverse()
    record["release_obligation"]["expected_behavior"].reverse()
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / "set-reordered.json", record, pretty=True)),
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["verified"] is True


@pytest.mark.parametrize(
    ("name", "path", "replacement"),
    [
        ("duplicate-event-id", ("events", 1, "event_id"), "event-0"),
        ("bad-sequence", ("events", 1, "sequence"), 7),
    ],
)
def test_trace_duplicate_identity_and_sequence_are_impossible(
    tmp_path: Path,
    name: str,
    path: tuple[str | int, ...],
    replacement: Any,
) -> None:
    trace = complete_trace()
    _assign(trace, path, replacement)
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / f"{name}.json", trace)),
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


@pytest.mark.parametrize(
    ("name", "path", "replacement", "expected_code"),
    [
        (
            "trial-run",
            ("trials", 0, "run_id"),
            "wrong-run",
            "IMPOSSIBLE_STATE",
        ),
        (
            "trial-case",
            ("trials", 0, "case_version"),
            "sha256:" + "0" * 64,
            "IDENTITY_MISMATCH",
        ),
        (
            "trial-code",
            ("trials", 0, "code_ref"),
            "wrong-code",
            "IMPOSSIBLE_STATE",
        ),
        (
            "trial-contract",
            ("trials", 0, "execution_contract_hash"),
            "sha256:" + "1" * 64,
            "IDENTITY_MISMATCH",
        ),
    ],
)
def test_trial_containment_bindings_are_enforced(
    tmp_path: Path,
    name: str,
    path: tuple[str | int, ...],
    replacement: Any,
    expected_code: str,
) -> None:
    record = sealed_record(complete=True)
    _assign(record, path, replacement)
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / f"{name}.json", record)),
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == expected_code


def test_noncompleted_trial_cannot_report_pass(tmp_path: Path) -> None:
    record = sealed_record()
    record["trials"][0]["execution_status"] = "TIMEOUT"
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / "timeout-pass.json", record)),
    )
    assert result.returncode == 5
    assert result.log_lines()[0]["code"] == "IMPOSSIBLE_STATE"


@pytest.mark.parametrize(
    ("name", "path", "replacement", "expected_code", "expected_exit"),
    [
        (
            "missing-explicit-baseline",
            ("release_change", "baseline"),
            None,
            "SCHEMA_VALIDATION_FAILED",
            4,
        ),
        (
            "bad-count",
            ("comparison", "candidate", "pass_count"),
            2,
            "IMPOSSIBLE_STATE",
            5,
        ),
        (
            "bad-rate",
            ("comparison", "candidate", "pass_rate"),
            "0.500000",
            "IMPOSSIBLE_STATE",
            5,
        ),
        (
            "bad-first-companion",
            ("comparison", "baseline"),
            {
                "trial_count": 0,
                "evaluable_count": 0,
                "pass_count": 0,
                "pass_rate": "0.000000",
            },
            "IMPOSSIBLE_STATE",
            5,
        ),
    ],
)
def test_baseline_count_rate_and_comparison_states(
    tmp_path: Path,
    name: str,
    path: tuple[str | int, ...],
    replacement: Any,
    expected_code: str,
    expected_exit: int,
) -> None:
    record = sealed_record()
    if replacement is None:
        target = record
        for part in path[:-1]:
            target = target[part]
        del target[path[-1]]
    else:
        _assign(record, path, replacement)
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / f"{name}.json", record)),
    )
    assert result.returncode == expected_exit
    assert result.log_lines()[0]["code"] == expected_code


def test_semantic_case_edit_changes_case_version(tmp_path: Path) -> None:
    original = protected_case()
    edited = copy.deepcopy(original)
    edited["risk_name"] = "Different approved semantic risk"
    edited = with_self_hash(edited, "protected_case", "case_version")
    original_result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "original.json", original)),
    )
    edited_result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "edited.json", edited)),
    )
    assert original_result.returncode == edited_result.returncode == 0
    assert original["case_version"] != edited["case_version"]


def test_attestation_record_reference_mutation_breaks_integrity(tmp_path: Path) -> None:
    attestation = decision_attestation()
    attestation["release_record_hash"] = "sha256:" + "9" * 64
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / "attestation-tamper.json", attestation)),
    )
    assert result.returncode == 6
    assert result.log_lines()[0]["code"] == "HASH_MISMATCH"


_PROTECTED_FIELD_EXPECTATIONS = {
    "contract_kind": ("SCHEMA_VALIDATION_FAILED", 4),
    "schema_version": ("UNSUPPORTED_SCHEMA_VERSION", 4),
    "seal_state": ("SCHEMA_VALIDATION_FAILED", 4),
    "project_id": ("HASH_MISMATCH", 6),
    "release_stream_id": ("HASH_MISMATCH", 6),
    "run_id": ("IMPOSSIBLE_STATE", 5),
    "created_at": ("HASH_MISMATCH", 6),
    "release_change": ("HASH_MISMATCH", 6),
    "protected_case_id": ("HASH_MISMATCH", 6),
    "protected_case_version": ("IDENTITY_MISMATCH", 5),
    "release_obligation": ("HASH_MISMATCH", 6),
    "evidence_requirements": ("HASH_MISMATCH", 6),
    "execution_contracts": ("IDENTITY_MISMATCH", 5),
    "trials": ("HASH_MISMATCH", 6),
    "comparison": ("HASH_MISMATCH", 6),
    "evidence_strength": ("HASH_MISMATCH", 6),
    "record_gaps": ("HASH_MISMATCH", 6),
    "policy_evaluation": ("HASH_MISMATCH", 6),
    "recommendation": ("IMPOSSIBLE_STATE", 5),
    "pr_reference": ("HASH_MISMATCH", 6),
    "chain_link": ("HASH_MISMATCH", 6),
}


def _mutate_protected_record_field(
    field: str,
) -> dict[str, Any]:
    record = sealed_record(complete=field != "record_gaps")
    if field == "contract_kind":
        record[field] = "protected_case"
    elif field == "schema_version":
        record[field] = 2
    elif field == "seal_state":
        record[field] = "UNSIGNED"
    elif field in {
        "project_id",
        "release_stream_id",
        "run_id",
        "protected_case_id",
    }:
        record[field] = f"{record[field]}-changed"
    elif field == "created_at":
        record[field] = "2026-07-30T10:00:01.000Z"
    elif field == "release_change":
        record[field]["change_id"] = "change-tampered"
    elif field == "protected_case_version":
        record[field] = "sha256:" + "7" * 64
    elif field == "release_obligation":
        record[field]["severity"] = "CRITICAL"
    elif field == "evidence_requirements":
        record[field][0]["minimum_trials"] = 2
    elif field == "execution_contracts":
        record[field]["execution_contract"]["command_hash"] = "sha256:" + "7" * 64
    elif field == "trials":
        record[field][0]["assertion_results"][0]["reason_code"] = "TAMPERED_REASON"
    elif field == "comparison":
        record[field]["reason_codes"] = ["SYNTHETIC_REASON"]
    elif field == "evidence_strength":
        record[field] = "LIMITED"
    elif field == "record_gaps":
        record[field][0]["reason_reference"]["content_hash"] = "sha256:" + "7" * 64
    elif field == "policy_evaluation":
        record[field]["policy_hash"] = "sha256:" + "7" * 64
    elif field == "recommendation":
        record[field] = "BLOCK"
    elif field == "pr_reference":
        record[field]["content_hash"] = "sha256:" + "7" * 64
    elif field == "chain_link":
        record[field] = {
            "link_kind": "APPEND",
            "previous_record_hash": "sha256:" + "7" * 64,
        }
    else:
        raise AssertionError(field)
    return record


@pytest.mark.parametrize("field", RELEASE_RECORD_PROTECTED_FIELDS)
def test_every_release_record_protected_field_detects_tampering(
    tmp_path: Path,
    field: str,
) -> None:
    expected_code, expected_exit = _PROTECTED_FIELD_EXPECTATIONS[field]
    record = _mutate_protected_record_field(field)
    result = run_cli(
        "records",
        "verify",
        str(write_json(tmp_path / f"tamper-{field}.json", record)),
    )
    assert result.returncode == expected_exit
    assert result.log_lines()[0]["code"] == expected_code


def test_protected_field_expectations_match_literal_manifest() -> None:
    assert set(_PROTECTED_FIELD_EXPECTATIONS) == set(RELEASE_RECORD_PROTECTED_FIELDS)
