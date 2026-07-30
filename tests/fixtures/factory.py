"""Fixture factory and independent canonical/hash oracle.

This module deliberately does not import ``triana``.  It implements only the
owner-approved wire specification needed to derive frozen acceptance values.
All fixture values are synthetic.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

JsonObject = dict[str, Any]

_DIGEST_A = "sha256:" + ("a" * 64)
_DIGEST_B = "sha256:" + ("b" * 64)
_DIGEST_C = "sha256:" + ("c" * 64)
_DIGEST_D = "sha256:" + ("d" * 64)
_DIGEST_E = "sha256:" + ("e" * 64)
_NOW = "2026-07-30T10:00:00.000Z"


def evidence_ref(
    reference_id: str,
    reference_kind: str = "OTHER",
    *,
    locator: JsonObject | None = None,
) -> JsonObject:
    value: JsonObject = {
        "reference_id": reference_id,
        "reference_kind": reference_kind,
        "content_hash": _DIGEST_A,
    }
    if locator is not None:
        value["locator"] = locator
    return value


def _set_key(field: str, value: Any) -> Any:
    if field in {
        "applicability_conditions",
        "expected_behavior",
        "prohibited_behavior",
        "allowed_alternatives",
    }:
        return value["statement_id"]
    if field == "capabilities":
        return value
    if field in {
        "source_evidence",
        "evidence_references",
        "unresolved_difference_references",
    }:
        return value["reference_id"]
    if field == "evidence_requirements":
        return value["requirement_id"]
    if field == "customer_evaluator_results":
        return (value["evaluator_id"], value["check_id"], value["result_id"])
    if field in {"gaps", "record_gaps"}:
        return value["gap_id"]
    if field in {"components"}:
        return value["component_kind"]
    if field in {"reason_codes", "flags", "pattern_flags", "gap_ids"}:
        return value
    raise AssertionError(f"Fixture oracle lacks a set key for {field}")


_SET_FIELDS = {
    "applicability_conditions",
    "expected_behavior",
    "prohibited_behavior",
    "allowed_alternatives",
    "capabilities",
    "source_evidence",
    "evidence_references",
    "unresolved_difference_references",
    "evidence_requirements",
    "customer_evaluator_results",
    "gaps",
    "record_gaps",
    "components",
    "reason_codes",
    "flags",
    "pattern_flags",
    "gap_ids",
}


def normalize_sets(value: Any, field: str | None = None) -> Any:
    """Return a deep, domain-set-normalized copy."""
    if isinstance(value, dict):
        return {key: normalize_sets(item, key) for key, item in value.items()}
    if isinstance(value, list):
        items = [normalize_sets(item) for item in value]
        if field in _SET_FIELDS:
            return sorted(items, key=lambda item: _set_key(field, item))
        return items
    return value


def canonical_bytes(value: Any) -> bytes:
    """Serialize the accepted fixture subset using RFC 8785-compatible bytes."""
    normalized = normalize_sets(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def domain_hash(kind: str, value: Any, *, schema_version: int = 1) -> str:
    preimage = (
        b"triana\x00"
        + kind.encode()
        + b"\x00v"
        + str(schema_version).encode()
        + b"\x00"
        + canonical_bytes(value)
    )
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def with_self_hash(value: JsonObject, kind: str, field: str) -> JsonObject:
    result = copy.deepcopy(value)
    result.pop(field, None)
    result[field] = domain_hash(kind, result)
    return result


def runtime_fingerprint(*, complete: bool = False) -> JsonObject:
    kinds = (
        [
            "AGENT_CODE",
            "MODEL",
            "PROMPT",
            "TOOLING",
            "RUNTIME",
            "CONFIGURATION",
            "FIXTURE",
            "EVALUATOR",
        ]
        if complete
        else ["AGENT_CODE"]
    )
    value: JsonObject = {
        "components": [
            {"component_kind": kind, "fingerprint": _DIGEST_B} for kind in kinds
        ]
    }
    return with_self_hash(value, "runtime_fingerprint", "runtime_hash")


def execution_contract(*, seeded: bool = False) -> JsonObject:
    policy: JsonObject
    if seeded:
        policy = {
            "randomization_policy_kind": "SEEDED",
            "generator": "fixture-generator",
            "generator_version": "1.0.0",
        }
    else:
        policy = {"randomization_policy_kind": "NONE"}
    value: JsonObject = {
        "contract_version": 1,
        "command_hash": _DIGEST_A,
        "fixture_fingerprint": _DIGEST_B,
        "configuration_fingerprint": _DIGEST_C,
        "reset_policy_hash": _DIGEST_D,
        "observation_scope": {"capabilities": ["TERMINAL_STATE", "CONVERSATION_TURNS"]},
        "randomization_policy": policy,
        "declared_trial_count": 1,
    }
    return with_self_hash(value, "execution_contract", "execution_contract_hash")


def minimal_trace() -> JsonObject:
    value: JsonObject = {
        "contract_kind": "normalized_trace",
        "schema_version": 1,
        "privacy_class": "LOCAL_SENSITIVE",
        "trace_id": "trace-minimal",
        "source": {
            "source_kind": "JSONL",
            "source_trace_id": "external-trace-minimal",
            "source_export_hash": _DIGEST_A,
        },
        "conversation_id": "conversation-minimal",
        "observation_scope": {"capabilities": ["CONVERSATION_TURNS"]},
        "events": [
            {
                "event_id": "event-0",
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Synthetic hello",
            }
        ],
    }
    return with_self_hash(value, "normalized_trace", "trace_hash")


def complete_trace() -> JsonObject:
    capabilities = [
        "CONVERSATION_TURNS",
        "MODEL_OUTPUT",
        "TOOL_DISPATCH",
        "TOOL_ARGUMENTS",
        "TOOL_RESULTS",
        "TERMINAL_STATE",
        "ESCALATION_HANDOFF",
        "TIMING",
        "COST",
    ]
    events: list[JsonObject] = [
        {
            "event_id": "event-0",
            "sequence": 0,
            "event_kind": "SYSTEM_VISIBLE_MESSAGE",
            "occurred_at": _NOW,
            "content": "Synthetic system context",
        },
        {
            "event_id": "event-1",
            "sequence": 1,
            "event_kind": "USER_MESSAGE",
            "parent_event_id": "event-0",
            "occurred_at": _NOW,
            "content": "Synthetic account question",
        },
        {
            "event_id": "event-2",
            "sequence": 2,
            "event_kind": "MODEL_OBSERVATION",
            "parent_event_id": "event-1",
            "occurred_at": _NOW,
            "model_ref": "model-synthetic",
            "output": "Synthetic tool plan",
            "latency_ms": 25,
            "cost_amount": "0.01",
            "cost_currency": "USD",
        },
        {
            "event_id": "event-3",
            "sequence": 3,
            "event_kind": "TOOL_CALL",
            "parent_event_id": "event-2",
            "occurred_at": _NOW,
            "tool_name": "lookup_account",
            "arguments": {"account_id": "synthetic-1", "include": ["status"]},
        },
        {
            "event_id": "event-4",
            "sequence": 4,
            "event_kind": "TOOL_RESULT",
            "parent_event_id": "event-3",
            "occurred_at": _NOW,
            "tool_call_event_id": "event-3",
            "result_state": "SUCCEEDED",
            "result": {"status": "active"},
        },
        {
            "event_id": "event-5",
            "sequence": 5,
            "event_kind": "ASSISTANT_MESSAGE",
            "parent_event_id": "event-4",
            "occurred_at": _NOW,
            "content": "The synthetic account is active.",
            "is_final": False,
        },
        {
            "event_id": "event-6",
            "sequence": 6,
            "event_kind": "HANDOFF",
            "parent_event_id": "event-5",
            "occurred_at": _NOW,
            "handoff_kind": "HUMAN",
            "destination_ref": "support",
            "outcome": "ACCEPTED",
        },
        {
            "event_id": "event-7",
            "sequence": 7,
            "event_kind": "ASSISTANT_MESSAGE",
            "parent_event_id": "event-6",
            "occurred_at": _NOW,
            "content": "A synthetic specialist will help.",
            "is_final": True,
        },
        {
            "event_id": "event-8",
            "sequence": 8,
            "event_kind": "TERMINAL",
            "parent_event_id": "event-7",
            "occurred_at": _NOW,
            "terminal_state": "SUCCESS",
        },
    ]
    value: JsonObject = {
        "contract_kind": "normalized_trace",
        "schema_version": 1,
        "privacy_class": "LOCAL_SENSITIVE",
        "trace_id": "trace-complete",
        "source": {
            "source_kind": "OTEL",
            "source_trace_id": "external-trace-complete",
            "source_export_hash": _DIGEST_B,
        },
        "conversation_id": "conversation-complete",
        "thread_id": "thread-complete",
        "agent_ref": "agent-complete",
        "release_ref": "release-complete",
        "observation_scope": {"capabilities": capabilities},
        "events": events,
    }
    return with_self_hash(value, "normalized_trace", "trace_hash")


def _statement(statement_id: str, text: str) -> JsonObject:
    return {"statement_id": statement_id, "text": text}


def _obligation(*, complete: bool = False) -> JsonObject:
    result: JsonObject = {
        "obligation_id": "obligation-refund",
        "obligation_statement": _statement(
            "statement-obligation", "Preserve safe refund escalation."
        ),
        "source_reference": evidence_ref("ref-obligation", "APPROVAL"),
        "severity": "HIGH",
        "owner_actor_id": "actor-owner",
        "applicability_conditions": [
            _statement("statement-applicable", "A refund request is present.")
        ],
        "expected_behavior": [
            _statement("statement-expected", "Escalate refunds above the limit.")
        ],
        "prohibited_behavior": [],
        "allowed_alternatives": [],
        "handoff_requirement": {"handoff_kind": "NONE"},
    }
    if complete:
        result["prohibited_behavior"] = [
            _statement("statement-prohibited", "Do not claim a refund was issued.")
        ]
        result["allowed_alternatives"] = [
            _statement("statement-alternative", "Ask for missing account details.")
        ]
        result["handoff_requirement"] = {
            "handoff_kind": "REQUIRED",
            "destination_ref": "refund-specialist",
        }
        result["policy_context_reference"] = evidence_ref("ref-policy", "POLICY")
    return result


def _assertions() -> list[JsonObject]:
    return [
        {
            "assertion_id": "assertion-1",
            "assertion_version": 1,
            "assertion_kind": "tool_called",
            "tool_name": "lookup_account",
        },
        {
            "assertion_id": "assertion-2",
            "assertion_version": 1,
            "assertion_kind": "tool_not_called",
            "tool_name": "issue_refund",
        },
        {
            "assertion_id": "assertion-3",
            "assertion_version": 1,
            "assertion_kind": "tool_called_before",
            "before_tool_name": "lookup_account",
            "after_tool_name": "escalate_refund",
            "occurrence_rule": "FIRST_SUCCESSFUL_DISPATCH",
        },
        {
            "assertion_id": "assertion-4",
            "assertion_version": 1,
            "assertion_kind": "arg_matches",
            "tool_name": "lookup_account",
            "argument_pointer": "/account_id",
            "call_selection": "FIRST",
            "matcher": {
                "matcher_kind": "EXACT_JSON",
                "expected_hash": domain_hash("json_value", "synthetic-1"),
                "expected_value_reference": evidence_ref(
                    "ref-expected-value", "ASSERTION"
                ),
            },
        },
        {
            "assertion_id": "assertion-5",
            "assertion_version": 1,
            "assertion_kind": "no_loop",
            "signature": "TOOL_NAME_AND_ARGUMENT_HASH",
            "maximum_consecutive_calls": 2,
        },
        {
            "assertion_id": "assertion-6",
            "assertion_version": 1,
            "assertion_kind": "no_unbacked_claim",
            "regex_engine": "PYTHON_RE_3_13",
            "output_pattern": r"status: (?P<claim>[A-Za-z]+)",
            "pattern_flags": ["ASCII", "IGNORE_CASE"],
            "claim_group_name": "claim",
            "supporting_tool_name": "lookup_account",
            "support_result_pointer": "/status",
            "normalization": "ASCII_CASEFOLD_TRIM",
            "support_must_precede_claim": True,
        },
        {
            "assertion_id": "assertion-7",
            "assertion_version": 1,
            "assertion_kind": "output_matches",
            "target": "FINAL_ASSISTANT_MESSAGE",
            "matcher": {
                "matcher_kind": "JSON_SCHEMA",
                "schema_draft": "2020-12",
                "schema_hash": _DIGEST_C,
                "schema_reference": evidence_ref("ref-output-schema", "ASSERTION"),
            },
        },
        {
            "assertion_id": "assertion-8",
            "assertion_version": 1,
            "assertion_kind": "terminal_state",
            "expected_state": "NO_ERROR",
        },
    ]


def _requirements(*, complete: bool = False) -> list[JsonObject]:
    assertions = _assertions() if complete else _assertions()[:1]
    requirements = [
        {
            "requirement_id": f"requirement-{index}",
            "requirement_kind": "TRIANA_ASSERTION",
            "required_observation": {
                "capabilities": ["TOOL_DISPATCH", "TERMINAL_STATE"]
            },
            "minimum_trials": 1,
            "assertion": assertion,
        }
        for index, assertion in enumerate(assertions, start=1)
    ]
    if complete:
        requirements.append(
            {
                "requirement_id": "requirement-evaluator",
                "requirement_kind": "CUSTOMER_EVALUATOR",
                "required_observation": {"capabilities": ["MODEL_OUTPUT"]},
                "minimum_trials": 1,
                "evaluator_id": "evaluator-customer",
                "evaluator_version": _DIGEST_E,
                "check_id": "check-customer",
            }
        )
    return requirements


def protected_case(*, complete: bool = False) -> JsonObject:
    source_evidence = [evidence_ref("ref-source", "TRACE")]
    replay_messages = [
        {
            "message_id": "message-1",
            "role": "USER",
            "content": "Please review this synthetic refund.",
        }
    ]
    qualification: JsonObject = {"qualification_state": "READY"}
    if complete:
        source_evidence.append(
            evidence_ref(
                "ref-source-2",
                "TOOL_EVENT",
                locator={
                    "locator_kind": "HTTPS",
                    "url": "https://evidence.example/synthetic/trace",
                },
            )
        )
        replay_messages = [
            {
                "message_id": "message-0",
                "role": "SYSTEM_VISIBLE",
                "content": "Synthetic policy context.",
            },
            *replay_messages,
            {
                "message_id": "message-2",
                "role": "ASSISTANT",
                "content": "I will inspect the synthetic account.",
            },
        ]
        qualification = {
            "qualification_state": "NEEDS_FIXTURE",
            "reason_code": "FIXTURE_REQUIRED",
            "explanation_reference": evidence_ref("ref-fixture-needed", "FIXTURE"),
        }
    value: JsonObject = {
        "contract_kind": "protected_case",
        "schema_version": 1,
        "case_id": "case-refund",
        "risk_name": "Unsafe refund completion",
        "source_evidence": source_evidence,
        "replay_input": {"messages": replay_messages},
        "fixture_contract": {
            "fixture_id": "fixture-refund",
            "fixture_version": 1,
            "fixture_fingerprint": _DIGEST_B,
            "reset_policy_hash": _DIGEST_C,
        },
        "release_obligation": _obligation(complete=complete),
        "evidence_requirements": _requirements(complete=complete),
        "approval": {
            "actor_id": "actor-approver",
            "actor_display_name": "Synthetic Approver" if complete else "Approver",
            "approved_at": _NOW,
            "source_reference": evidence_ref("ref-approval", "APPROVAL"),
        },
        "qualification": qualification,
    }
    return with_self_hash(value, "protected_case", "case_version")


def _release_change(*, missing: bool) -> JsonObject:
    if missing:
        baseline: JsonObject = {
            "baseline_kind": "MISSING",
            "reason_code": "MISSING_APPROVED_BASELINE",
        }
        components = [
            {
                "component_kind": "AGENT_CODE",
                "candidate_fingerprint": _DIGEST_B,
                "declared_state": "CHANGED",
            }
        ]
        unresolved: list[JsonObject] = []
    else:
        baseline = {
            "baseline_kind": "APPROVED",
            "code_ref": "baseline-sha",
            "approval_reference": evidence_ref("ref-baseline-approval", "APPROVAL"),
        }
        components = [
            {
                "component_kind": "AGENT_CODE",
                "candidate_fingerprint": _DIGEST_B,
                "baseline_fingerprint": _DIGEST_A,
                "declared_state": "CHANGED",
            },
            {
                "component_kind": "MODEL",
                "candidate_fingerprint": _DIGEST_C,
                "baseline_fingerprint": _DIGEST_C,
                "declared_state": "UNKNOWN",
                "difference_reference_id": "ref-model-difference",
            },
        ]
        unresolved = [evidence_ref("ref-model-difference", "OTHER")]
    return {
        "change_id": "change-synthetic",
        "declaration_reference": evidence_ref("ref-change", "OTHER"),
        "candidate_code_ref": "candidate-sha",
        "baseline": baseline,
        "components": components,
        "unresolved_difference_references": unresolved,
    }


def _trial(
    *,
    side: str,
    case_version: str,
    run_id: str,
    contract: JsonObject,
    complete: bool,
) -> JsonObject:
    code_ref = "baseline-sha" if side == "BASELINE" else "candidate-sha"
    randomization: JsonObject
    if contract["randomization_policy"]["randomization_policy_kind"] == "SEEDED":
        randomization = {
            "randomization_kind": "SEEDED",
            "seed": "seed-2026073001",
            "generator": "fixture-generator",
            "generator_version": "1.0.0",
        }
    else:
        randomization = {"randomization_kind": "NONE"}
    projection = {
        "run_id": run_id,
        "case_version": case_version,
        "side": side,
        "trial_index": 0,
        "code_ref": code_ref,
        "execution_contract_hash": contract["execution_contract_hash"],
    }
    assertion_results: list[JsonObject] = []
    evaluator_results: list[JsonObject] = []
    if complete:
        for index, assertion in enumerate(_assertions()):
            assertion_results.append(
                {
                    "result_id": f"result-{side.lower()}-{index + 1}",
                    "requirement_id": f"requirement-{index + 1}",
                    "assertion_id": assertion["assertion_id"],
                    "assertion_version": 1,
                    "execution_index": index,
                    "status": "PASS",
                    "reason_code": "ASSERTION_SATISFIED",
                    "evidence_references": [
                        evidence_ref(
                            f"ref-result-{side.lower()}-{index + 1}", "ASSERTION"
                        )
                    ],
                    "gap_ids": [],
                }
            )
        evaluator_results = [
            {
                "result_id": f"result-{side.lower()}-evaluator",
                "requirement_id": "requirement-evaluator",
                "check_id": "check-customer",
                "evaluator_id": "evaluator-customer",
                "evaluator_version": _DIGEST_E,
                "status": "PASS",
                "score": "1",
                "evidence_references": [
                    evidence_ref(f"ref-evaluator-{side.lower()}", "EVALUATOR")
                ],
                "gap_ids": [],
            }
        ]
    return {
        "trial_id": domain_hash("trial_identity", projection),
        **projection,
        "runtime_fingerprint": runtime_fingerprint(complete=complete),
        "randomization": randomization,
        "execution_status": "COMPLETED",
        "trace_reference": evidence_ref(f"ref-trace-{side.lower()}", "TRACE"),
        "assertion_results": assertion_results,
        "customer_evaluator_results": evaluator_results,
        "gaps": [],
        "end_to_end_status": "PASS",
    }


def unsigned_record(*, complete: bool = False) -> JsonObject:
    case = protected_case(complete=complete)
    run_id = "run-complete" if complete else "run-minimal"
    if complete:
        contract = execution_contract(seeded=True)
        binding: JsonObject = {
            "execution_binding_kind": "MATCHED",
            "execution_contract": contract,
        }
        trials = [
            _trial(
                side="BASELINE",
                case_version=case["case_version"],
                run_id=run_id,
                contract=contract,
                complete=True,
            ),
            _trial(
                side="CANDIDATE",
                case_version=case["case_version"],
                run_id=run_id,
                contract=contract,
                complete=True,
            ),
        ]
        comparison: JsonObject = {
            "comparison_status": "COMPARABLE",
            "candidate": {
                "trial_count": 1,
                "evaluable_count": 1,
                "pass_count": 1,
                "pass_rate": "1.000000",
            },
            "baseline": {
                "trial_count": 1,
                "evaluable_count": 1,
                "pass_count": 1,
                "pass_rate": "1.000000",
            },
            "movement": "0.000000",
            "reason_codes": [],
        }
        record_gaps: list[JsonObject] = []
        strength = "SUFFICIENT"
        recommendation = "PASS"
        policy_reasons = ["NO_REGRESSION"]
        release_change = _release_change(missing=False)
    else:
        contract = execution_contract()
        binding = {
            "execution_binding_kind": "CANDIDATE_ONLY",
            "candidate_execution_contract": contract,
        }
        trials = [
            _trial(
                side="CANDIDATE",
                case_version=case["case_version"],
                run_id=run_id,
                contract=contract,
                complete=False,
            )
        ]
        comparison = {
            "comparison_status": "FIRST_OBSERVATION",
            "candidate": {
                "trial_count": 1,
                "evaluable_count": 1,
                "pass_count": 1,
                "pass_rate": "1.000000",
            },
            "reason_codes": ["MISSING_APPROVED_BASELINE"],
        }
        gap = {
            "gap_id": "gap-missing-baseline",
            "gap_code": "MISSING_APPROVED_BASELINE",
            "stage": "COMPARISON",
            "scope": {"scope_kind": "RECORD"},
            "reason_reference": evidence_ref("ref-gap-reason", "OTHER"),
            "evidence_references": [],
        }
        record_gaps = [gap]
        strength = "LIMITED"
        recommendation = "REVIEW"
        policy_reasons = ["MISSING_APPROVED_BASELINE"]
        release_change = _release_change(missing=True)
    value: JsonObject = {
        "contract_kind": "release_evidence_record",
        "schema_version": 1,
        "seal_state": "UNSIGNED",
        "project_id": "project-synthetic",
        "release_stream_id": "stream-main",
        "run_id": run_id,
        "created_at": _NOW,
        "release_change": release_change,
        "protected_case_id": case["case_id"],
        "protected_case_version": case["case_version"],
        "release_obligation": case["release_obligation"],
        "evidence_requirements": case["evidence_requirements"],
        "execution_contracts": binding,
        "trials": trials,
        "comparison": comparison,
        "evidence_strength": strength,
        "record_gaps": record_gaps,
        "policy_evaluation": {
            "policy_id": "policy-default",
            "policy_version": 1,
            "policy_hash": _DIGEST_D,
            "rule_id": "rule-synthetic",
            "input_evidence_hash": _DIGEST_E,
            "reason_codes": policy_reasons,
            "recommendation": recommendation,
        },
        "recommendation": recommendation,
        "chain_link": {"link_kind": "GENESIS"},
    }
    if complete:
        value["pr_reference"] = evidence_ref(
            "ref-pr",
            "GITHUB",
            locator={
                "locator_kind": "HTTPS",
                "url": "https://github.example/synthetic/pull/1",
            },
        )
    return value


def sealed_record(*, complete: bool = False) -> JsonObject:
    value = unsigned_record(complete=complete)
    value["seal_state"] = "SEALED"
    return with_self_hash(value, "release_evidence_record", "current_record_hash")


def moved_record(*, sealed: bool = False) -> JsonObject:
    """Return a truthful execution-contract mismatch snapshot."""
    case = protected_case(complete=True)
    baseline_contract = execution_contract(seeded=False)
    candidate_contract = execution_contract(seeded=True)
    run_id = "run-moved"
    value = unsigned_record(complete=True)
    value["run_id"] = run_id
    value["protected_case_version"] = case["case_version"]
    value["execution_contracts"] = {
        "execution_binding_kind": "MISMATCHED",
        "baseline_execution_contract": baseline_contract,
        "candidate_execution_contract": candidate_contract,
    }
    value["trials"] = [
        _trial(
            side="BASELINE",
            case_version=case["case_version"],
            run_id=run_id,
            contract=baseline_contract,
            complete=True,
        ),
        _trial(
            side="CANDIDATE",
            case_version=case["case_version"],
            run_id=run_id,
            contract=candidate_contract,
            complete=True,
        ),
    ]
    value["comparison"] = {
        "comparison_status": "MOVED",
        "candidate": {
            "trial_count": 1,
            "evaluable_count": 1,
            "pass_count": 1,
            "pass_rate": "1.000000",
        },
        "baseline": {
            "trial_count": 1,
            "evaluable_count": 1,
            "pass_count": 1,
            "pass_rate": "1.000000",
        },
        "reason_codes": ["EXECUTION_CONTRACT_MISMATCH"],
    }
    value["record_gaps"] = [
        {
            "gap_id": "gap-contract-mismatch",
            "gap_code": "EXECUTION_CONTRACT_MISMATCH",
            "stage": "COMPARISON",
            "scope": {"scope_kind": "RECORD"},
            "reason_reference": evidence_ref("ref-contract-mismatch", "OTHER"),
            "evidence_references": [],
        }
    ]
    value["evidence_strength"] = "LIMITED"
    value["policy_evaluation"]["reason_codes"] = [  # type: ignore[index]
        "EXECUTION_CONTRACT_MISMATCH"
    ]
    value["policy_evaluation"]["recommendation"] = "REVIEW"  # type: ignore[index]
    value["recommendation"] = "REVIEW"
    if sealed:
        value["seal_state"] = "SEALED"
        return with_self_hash(value, "release_evidence_record", "current_record_hash")
    return value


def evaluator_gap_record(*, sealed: bool = False) -> JsonObject:
    """Return a matched record whose candidate evaluator timed out."""
    value = unsigned_record(complete=True)
    candidate = next(trial for trial in value["trials"] if trial["side"] == "CANDIDATE")
    evaluator_result = candidate["customer_evaluator_results"][0]
    gap_id = "gap-evaluator-timeout"
    evaluator_result["status"] = "UNEVALUABLE"
    evaluator_result["gap_ids"] = [gap_id]
    candidate["gaps"] = [
        {
            "gap_id": gap_id,
            "gap_code": "EVALUATOR_TIMEOUT",
            "stage": "EVALUATOR",
            "scope": {
                "scope_kind": "EVALUATOR",
                "trial_id": candidate["trial_id"],
                "evaluator_id": "evaluator-customer",
                "check_id": "check-customer",
            },
            "reason_reference": evidence_ref("ref-evaluator-timeout", "EVALUATOR"),
            "evidence_references": [],
        }
    ]
    candidate["end_to_end_status"] = "UNEVALUABLE"
    value["comparison"] = {
        "comparison_status": "INSUFFICIENT_EVIDENCE",
        "candidate": {
            "trial_count": 1,
            "evaluable_count": 0,
            "pass_count": 0,
            "pass_rate": "0.000000",
        },
        "baseline": {
            "trial_count": 1,
            "evaluable_count": 1,
            "pass_count": 1,
            "pass_rate": "1.000000",
        },
        "reason_codes": ["EVALUATOR_TIMEOUT"],
    }
    value["evidence_strength"] = "INSUFFICIENT"
    value["policy_evaluation"]["reason_codes"] = ["EVALUATOR_TIMEOUT"]  # type: ignore[index]
    value["policy_evaluation"]["recommendation"] = "REVIEW"  # type: ignore[index]
    value["recommendation"] = "REVIEW"
    if sealed:
        value["seal_state"] = "SEALED"
        return with_self_hash(value, "release_evidence_record", "current_record_hash")
    return value


def record_chain(*, complete: bool = False) -> JsonObject:
    first = sealed_record()
    entries: list[JsonObject] = [
        {
            "position": 0,
            "record_hash": first["current_record_hash"],
            "link_kind": "GENESIS",
        }
    ]
    if complete:
        second = sealed_record(complete=True)
        entries.append(
            {
                "position": 1,
                "record_hash": second["current_record_hash"],
                "link_kind": "APPEND",
                "previous_record_hash": first["current_record_hash"],
            }
        )
    value: JsonObject = {
        "contract_kind": "record_chain",
        "schema_version": 1,
        "chain_id": "chain-synthetic",
        "project_id": "project-synthetic",
        "release_stream_id": "stream-main",
        "entries": entries,
        "head_record_hash": entries[-1]["record_hash"],
    }
    return with_self_hash(value, "record_chain", "chain_hash")


def decision_attestation(*, complete: bool = False) -> JsonObject:
    record = sealed_record(complete=complete)
    value: JsonObject = {
        "contract_kind": "decision_attestation",
        "schema_version": 1,
        "attestation_id": "attestation-synthetic",
        "release_record_hash": record["current_record_hash"],
        "decision_type": "APPROVE",
        "actor_id": "actor-release-owner",
        "decided_at": _NOW,
        "source_reference": evidence_ref("ref-decision", "APPROVAL"),
    }
    if complete:
        value["decision_type"] = "APPROVE_WITH_EXCEPTION"
        value["actor_display_name"] = "Synthetic Release Owner"
        value["exception_rationale_reference"] = evidence_ref(
            "ref-exception", "APPROVAL"
        )
    return with_self_hash(value, "decision_attestation", "attestation_hash")


def document_matrix() -> dict[str, JsonObject]:
    return {
        "normalized_trace.minimal": minimal_trace(),
        "normalized_trace.complete": complete_trace(),
        "protected_case.minimal": protected_case(),
        "protected_case.complete": protected_case(complete=True),
        "release_evidence_record.unsigned_minimal": unsigned_record(),
        "release_evidence_record.sealed_minimal": sealed_record(),
        "release_evidence_record.unsigned_complete": unsigned_record(complete=True),
        "release_evidence_record.sealed_complete": sealed_record(complete=True),
        "record_chain.minimal": record_chain(),
        "record_chain.complete": record_chain(complete=True),
        "decision_attestation.minimal": decision_attestation(),
        "decision_attestation.complete": decision_attestation(complete=True),
    }


def fixture_universe_hash() -> str:
    payload = {name: document for name, document in sorted(document_matrix().items())}
    return "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()
