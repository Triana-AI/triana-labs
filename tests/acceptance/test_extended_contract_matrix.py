"""Exhaustive structural contract matrices required by the Slice 0A packet."""

from __future__ import annotations

import copy
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fixtures.contract_coverage import closed_boundary_cases, required_path_cases
from fixtures.factory import (
    complete_trace,
    decision_attestation,
    protected_case,
    record_chain,
    sealed_record,
)

from acceptance.support import run_cli, write_json, write_raw_json


def _parent(value: Any, path: tuple[str | int, ...]) -> tuple[Any, str | int]:
    target = value
    for part in path[:-1]:
        target = target[part]
    return target, path[-1]


def _delete(value: Any, path: tuple[str | int, ...]) -> None:
    target, key = _parent(value, path)
    del target[key]


def _assign(value: Any, path: tuple[str | int, ...], replacement: Any) -> None:
    target, key = _parent(value, path)
    target[key] = replacement


def _pointer(path: tuple[str | int, ...], final: str | None = None) -> str:
    parts = [str(part).replace("~", "~0").replace("/", "~1") for part in path]
    if final is not None:
        parts.append(final)
    return "/" + "/".join(parts)


def _required_cases() -> list[tuple[str, dict[str, Any], tuple[str | int, ...]]]:
    trace = complete_trace()
    case = protected_case(complete=True)
    record = sealed_record(complete=True)
    chain = record_chain(complete=True)
    attestation = decision_attestation(complete=True)
    cases: list[tuple[str, dict[str, Any], tuple[str | int, ...]]] = [
        ("trace-public-kind", trace, ("contract_kind",)),
        ("trace-self-hash", trace, ("trace_hash",)),
        ("trace-source", trace, ("source", "source_trace_id")),
        ("trace-scope", trace, ("observation_scope", "capabilities")),
        ("event-system", trace, ("events", 0, "content")),
        ("event-user", trace, ("events", 1, "content")),
        ("event-model", trace, ("events", 2, "model_ref")),
        ("event-tool-call", trace, ("events", 3, "arguments")),
        ("event-tool-result", trace, ("events", 4, "result_state")),
        ("event-assistant", trace, ("events", 5, "is_final")),
        ("event-handoff", trace, ("events", 6, "handoff_kind")),
        ("event-terminal", trace, ("events", 8, "terminal_state")),
        ("case-public-kind", case, ("contract_kind",)),
        ("case-self-version", case, ("case_version",)),
        ("case-replay", case, ("replay_input", "messages")),
        ("case-replay-message", case, ("replay_input", "messages", 0, "role")),
        ("case-fixture", case, ("fixture_contract", "fixture_id")),
        (
            "case-obligation",
            case,
            ("release_obligation", "obligation_statement"),
        ),
        (
            "case-behavior-statement",
            case,
            ("release_obligation", "expected_behavior", 0, "text"),
        ),
        (
            "case-handoff-union",
            case,
            ("release_obligation", "handoff_requirement", "handoff_kind"),
        ),
        ("case-approval", case, ("approval", "actor_id")),
        ("case-qualification-union", case, ("qualification", "qualification_state")),
        (
            "requirement-union",
            case,
            ("evidence_requirements", 0, "requirement_kind"),
        ),
        (
            "requirement-observation",
            case,
            ("evidence_requirements", 0, "required_observation"),
        ),
        (
            "evidence-reference",
            case,
            ("source_evidence", 0, "reference_id"),
        ),
        (
            "locator-union",
            case,
            ("source_evidence", 1, "locator", "locator_kind"),
        ),
    ]
    for index, field in enumerate(
        [
            "tool_name",
            "tool_name",
            "occurrence_rule",
            "matcher",
            "signature",
            "output_pattern",
            "matcher",
            "expected_state",
        ]
    ):
        cases.append(
            (
                f"assertion-{index + 1}",
                case,
                ("evidence_requirements", index, "assertion", field),
            )
        )
    cases.extend(
        [
            (
                "value-matcher-union",
                case,
                ("evidence_requirements", 3, "assertion", "matcher", "matcher_kind"),
            ),
            (
                "output-matcher-union",
                case,
                ("evidence_requirements", 6, "assertion", "matcher", "matcher_kind"),
            ),
            ("record-public-kind", record, ("contract_kind",)),
            ("record-seal-state", record, ("seal_state",)),
            ("record-release-change", record, ("release_change", "change_id")),
            (
                "record-baseline-union",
                record,
                ("release_change", "baseline", "baseline_kind"),
            ),
            (
                "record-change-component",
                record,
                ("release_change", "components", 0, "declared_state"),
            ),
            (
                "execution-binding-union",
                record,
                ("execution_contracts", "execution_binding_kind"),
            ),
            (
                "execution-contract",
                record,
                ("execution_contracts", "execution_contract", "command_hash"),
            ),
            (
                "execution-policy-union",
                record,
                (
                    "execution_contracts",
                    "execution_contract",
                    "randomization_policy",
                    "randomization_policy_kind",
                ),
            ),
            ("trial", record, ("trials", 0, "execution_status")),
            ("runtime", record, ("trials", 0, "runtime_fingerprint", "runtime_hash")),
            (
                "runtime-component",
                record,
                ("trials", 0, "runtime_fingerprint", "components", 0, "fingerprint"),
            ),
            (
                "trial-randomization-union",
                record,
                ("trials", 0, "randomization", "randomization_kind"),
            ),
            (
                "assertion-result",
                record,
                ("trials", 0, "assertion_results", 0, "status"),
            ),
            (
                "evaluator-result",
                record,
                ("trials", 0, "customer_evaluator_results", 0, "status"),
            ),
            ("comparison", record, ("comparison", "comparison_status")),
            ("side-summary", record, ("comparison", "candidate", "trial_count")),
            ("policy", record, ("policy_evaluation", "rule_id")),
            ("record-chain-link", record, ("chain_link", "link_kind")),
            ("record-self-hash", record, ("current_record_hash",)),
            ("chain-public-kind", chain, ("contract_kind",)),
            ("chain-entry", chain, ("entries", 0, "position")),
            ("chain-self-hash", chain, ("chain_hash",)),
            ("attestation-public-kind", attestation, ("contract_kind",)),
            ("attestation-decision", attestation, ("decision_type",)),
            ("attestation-self-hash", attestation, ("attestation_hash",)),
        ]
    )
    return cases


@pytest.mark.parametrize(
    ("name", "source_factory", "path"),
    required_path_cases(),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_required_field_removal_reports_exact_pointer(
    tmp_path: Path,
    name: str,
    source_factory: Callable[[], dict[str, Any]],
    path: tuple[str | int, ...],
) -> None:
    document = source_factory()
    _delete(document, path)
    result = run_cli(
        "contracts",
        "validate",
        str(write_raw_json(tmp_path / f"{name}.json", document)),
    )
    assert result.returncode == 4
    event = result.log_lines()[0]
    assert event["code"] == "SCHEMA_VALIDATION_FAILED"
    assert event["json_pointer"] == _pointer(path)


def _unknown_cases() -> list[tuple[str, dict[str, Any], tuple[str | int, ...]]]:
    trace = complete_trace()
    case = protected_case(complete=True)
    record = sealed_record(complete=True)
    chain = record_chain(complete=True)
    attestation = decision_attestation(complete=True)
    return [
        ("trace", trace, ()),
        ("trace-source", trace, ("source",)),
        ("trace-event", trace, ("events", 3)),
        ("trace-scope", trace, ("observation_scope",)),
        ("case", case, ()),
        ("case-replay", case, ("replay_input",)),
        ("case-message", case, ("replay_input", "messages", 0)),
        ("case-fixture", case, ("fixture_contract",)),
        ("case-obligation", case, ("release_obligation",)),
        ("case-statement", case, ("release_obligation", "expected_behavior", 0)),
        ("case-handoff", case, ("release_obligation", "handoff_requirement")),
        ("case-requirement", case, ("evidence_requirements", 0)),
        ("case-assertion", case, ("evidence_requirements", 0, "assertion")),
        ("case-approval", case, ("approval",)),
        ("case-qualification", case, ("qualification",)),
        ("reference", case, ("source_evidence", 0)),
        ("locator", case, ("source_evidence", 1, "locator")),
        ("record", record, ()),
        ("release-change", record, ("release_change",)),
        ("baseline", record, ("release_change", "baseline")),
        ("execution-binding", record, ("execution_contracts",)),
        ("execution-contract", record, ("execution_contracts", "execution_contract")),
        (
            "execution-policy",
            record,
            ("execution_contracts", "execution_contract", "randomization_policy"),
        ),
        ("trial", record, ("trials", 0)),
        ("runtime", record, ("trials", 0, "runtime_fingerprint")),
        ("trial-randomization", record, ("trials", 0, "randomization")),
        ("assertion-result", record, ("trials", 0, "assertion_results", 0)),
        (
            "evaluator-result",
            record,
            ("trials", 0, "customer_evaluator_results", 0),
        ),
        ("comparison", record, ("comparison",)),
        ("summary", record, ("comparison", "candidate")),
        ("policy", record, ("policy_evaluation",)),
        ("chain-link", record, ("chain_link",)),
        ("record-chain", chain, ()),
        ("chain-entry", chain, ("entries", 0)),
        ("attestation", attestation, ()),
    ]


@pytest.mark.parametrize(
    ("name", "source_factory", "path"),
    closed_boundary_cases(),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_unknown_field_is_rejected_at_nested_boundary(
    tmp_path: Path,
    name: str,
    source_factory: Callable[[], dict[str, Any]],
    path: tuple[str | int, ...],
) -> None:
    document = source_factory()
    target = document
    for part in path:
        target = target[part]
    target["unexpected"] = "forbidden"
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / f"{name}.json", document)),
    )
    assert result.returncode == 4
    event = result.log_lines()[0]
    assert event["code"] == "SCHEMA_VALIDATION_FAILED"
    assert any(
        item["json_pointer"] == _pointer(path, "unexpected") for item in event["errors"]
    )


@pytest.mark.parametrize(
    ("name", "source", "path", "replacement", "expected_exit"),
    [
        (
            "invalid-enum",
            complete_trace(),
            ("events", 0, "event_kind"),
            "UNKNOWN_EVENT",
            4,
        ),
        ("wrong-type", protected_case(), ("risk_name",), 42, 4),
        ("empty-safe-id", protected_case(), ("case_id",), "", 4),
        (
            "broken-ready-union",
            protected_case(),
            ("qualification",),
            {
                "qualification_state": "READY",
                "reason_code": "FIXTURE_REQUIRED",
            },
            4,
        ),
        (
            "broken-result-union",
            complete_trace(),
            ("events", 4),
            {
                "event_id": "event-4",
                "sequence": 4,
                "event_kind": "TOOL_RESULT",
                "tool_call_event_id": "event-3",
                "result_state": "SUCCEEDED",
                "result": {"ok": True},
                "error_code": "ERROR",
                "error_message": "forbidden companion",
            },
            4,
        ),
        (
            "unsafe-integer",
            complete_trace(),
            ("events", 2, "latency_ms"),
            9_007_199_254_740_992,
            4,
        ),
        (
            "float-sensitive-json",
            complete_trace(),
            ("events", 3, "arguments"),
            {"unsafe": 1.5},
            4,
        ),
        (
            "noncanonical-decimal",
            complete_trace(),
            ("events", 2, "cost_amount"),
            "1.0",
            4,
        ),
        (
            "invalid-fixed-rate",
            sealed_record(),
            ("comparison", "candidate", "pass_rate"),
            "1.0",
            4,
        ),
    ],
)
def test_invalid_enum_type_identifier_union_and_number_domains(
    tmp_path: Path,
    name: str,
    source: dict[str, Any],
    path: tuple[str | int, ...],
    replacement: Any,
    expected_exit: int,
) -> None:
    document = copy.deepcopy(source)
    _assign(document, path, replacement)
    result = run_cli(
        "contracts",
        "validate",
        str(write_json(tmp_path / f"{name}.json", document)),
    )
    assert result.returncode == expected_exit
    assert result.log_lines()[0]["code"] == "SCHEMA_VALIDATION_FAILED"


def test_negative_zero_is_rejected_from_raw_number_lexeme(tmp_path: Path) -> None:
    document = complete_trace()
    raw = write_json(tmp_path / "negative-zero.json", document).read_bytes()
    raw = raw.replace(b'"latency_ms":25', b'"latency_ms":-0')
    (tmp_path / "negative-zero.json").write_bytes(raw)
    result = run_cli("contracts", "validate", str(tmp_path / "negative-zero.json"))
    assert result.returncode == 4
    assert result.log_lines()[0]["code"] == "SCHEMA_VALIDATION_FAILED"
