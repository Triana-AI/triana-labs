"""Literal Slice 0A contract-coverage manifest.

This is a test-owned transcription of the normative required-field and closed
object-boundary tables in ``docs/CONTRACTS.md``.  It deliberately imports no
production code.  Each object instance names a valid public fixture and the
path at which that documented family or union arm is instantiated.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fixtures.factory import (
    complete_trace,
    decision_attestation,
    domain_hash,
    evaluator_gap_record,
    moved_record,
    protected_case,
    record_chain,
    sealed_record,
    with_self_hash,
)

JsonObject = dict[str, Any]
Path = tuple[str | int, ...]


@dataclass(frozen=True)
class ObjectCoverage:
    """One documented closed object family or union arm."""

    name: str
    family: str
    public_kind: str
    factory: Callable[[], JsonObject]
    path: Path
    required_fields: tuple[str, ...]


def _trace_tool_error() -> JsonObject:
    value = complete_trace()
    event = value["events"][4]
    del event["result"]
    event["result_state"] = "ERROR"
    event["error_code"] = "SYNTHETIC_ERROR"
    event["error_message"] = "Synthetic safe failure."
    return with_self_hash(value, "normalized_trace", "trace_hash")


def _trace_terminal_error() -> JsonObject:
    value = complete_trace()
    terminal = value["events"][8]
    terminal["terminal_state"] = "ERROR"
    terminal["reason_code"] = "SYNTHETIC_ERROR"
    return with_self_hash(value, "normalized_trace", "trace_hash")


def _case_opaque_locator() -> JsonObject:
    value = protected_case(complete=True)
    value["source_evidence"][1]["locator"] = {
        "locator_kind": "OPAQUE",
        "token": "opaque-synthetic",
    }
    return with_self_hash(value, "protected_case", "case_version")


def _case_not_yet() -> JsonObject:
    value = protected_case(complete=True)
    value["qualification"] = {
        "qualification_state": "NOT_YET",
        "reason_code": "SYNTHETIC_NOT_READY",
        "explanation_reference": copy.deepcopy(value["source_evidence"][0]),
    }
    return with_self_hash(value, "protected_case", "case_version")


def _case_value_regex() -> JsonObject:
    value = protected_case(complete=True)
    value["evidence_requirements"][3]["assertion"]["matcher"] = {
        "matcher_kind": "STRING_REGEX",
        "regex_engine": "PYTHON_RE_3_13",
        "pattern": r"synthetic-[0-9]+",
        "flags": ["ASCII"],
    }
    return with_self_hash(value, "protected_case", "case_version")


def _case_output_regex() -> JsonObject:
    value = protected_case(complete=True)
    value["evidence_requirements"][6]["assertion"]["matcher"] = {
        "matcher_kind": "STRING_REGEX",
        "regex_engine": "PYTHON_RE_3_13",
        "pattern": r"active",
        "flags": ["IGNORE_CASE"],
    }
    return with_self_hash(value, "protected_case", "case_version")


def _record_append() -> JsonObject:
    value = sealed_record(complete=True)
    value["chain_link"] = {
        "link_kind": "APPEND",
        "previous_record_hash": "sha256:" + "8" * 64,
        "supersedes_record_hash": "sha256:" + "9" * 64,
    }
    return with_self_hash(value, "release_evidence_record", "current_record_hash")


def _record_gap_scope(scope_kind: str) -> JsonObject:
    value = evaluator_gap_record(sealed=False)
    candidate = next(trial for trial in value["trials"] if trial["side"] == "CANDIDATE")
    gap = candidate["gaps"][0]
    if scope_kind == "TRIAL":
        gap["scope"] = {
            "scope_kind": "TRIAL",
            "trial_id": candidate["trial_id"],
        }
    elif scope_kind == "ASSERTION":
        gap["scope"] = {
            "scope_kind": "ASSERTION",
            "trial_id": candidate["trial_id"],
            "assertion_id": "assertion-1",
        }
    elif scope_kind != "EVALUATOR":
        raise AssertionError(scope_kind)
    value["seal_state"] = "SEALED"
    return with_self_hash(value, "release_evidence_record", "current_record_hash")


def _record_trial_gap() -> JsonObject:
    return _record_gap_scope("TRIAL")


def _record_assertion_gap() -> JsonObject:
    return _record_gap_scope("ASSERTION")


def _record_evaluator_gap() -> JsonObject:
    return _record_gap_scope("EVALUATOR")


def insufficient_without_baseline_record() -> JsonObject:
    """Return the valid INSUFFICIENT_EVIDENCE arm with optional baseline absent."""
    value = evaluator_gap_record(sealed=False)
    del value["comparison"]["baseline"]
    value["seal_state"] = "SEALED"
    return with_self_hash(value, "release_evidence_record", "current_record_hash")


TRACE = complete_trace
TRACE_TOOL_ERROR = _trace_tool_error
TRACE_TERMINAL_ERROR = _trace_terminal_error
CASE = lambda: protected_case(complete=True)
CASE_MINIMAL = protected_case
CASE_OPAQUE = _case_opaque_locator
CASE_NOT_YET = _case_not_yet
CASE_VALUE_REGEX = _case_value_regex
CASE_OUTPUT_REGEX = _case_output_regex
RECORD = lambda: sealed_record(complete=True)
RECORD_FIRST = sealed_record
RECORD_MOVED = lambda: moved_record(sealed=True)
RECORD_GAP = lambda: evaluator_gap_record(sealed=True)
RECORD_GAP_NO_BASELINE = insufficient_without_baseline_record
RECORD_TRIAL_GAP = _record_trial_gap
RECORD_ASSERTION_GAP = _record_assertion_gap
RECORD_EVALUATOR_GAP = _record_evaluator_gap
RECORD_APPEND = _record_append
CHAIN = lambda: record_chain(complete=True)
ATTESTATION = lambda: decision_attestation(complete=True)


def _object(
    name: str,
    family: str,
    public_kind: str,
    factory: Callable[[], JsonObject],
    path: Path,
    *required_fields: str,
) -> ObjectCoverage:
    return ObjectCoverage(
        name, family, public_kind, factory, path, tuple(required_fields)
    )


OBJECT_COVERAGE: tuple[ObjectCoverage, ...] = (
    # normalized_trace and every event union arm.
    _object(
        "trace",
        "normalized_trace",
        "normalized_trace",
        TRACE,
        (),
        "contract_kind",
        "schema_version",
        "privacy_class",
        "trace_id",
        "source",
        "conversation_id",
        "observation_scope",
        "events",
        "trace_hash",
    ),
    _object(
        "trace-source",
        "TraceSource",
        "normalized_trace",
        TRACE,
        ("source",),
        "source_kind",
        "source_trace_id",
        "source_export_hash",
    ),
    _object(
        "trace-observation-scope",
        "ObservationScope",
        "normalized_trace",
        TRACE,
        ("observation_scope",),
        "capabilities",
    ),
    *tuple(
        _object(
            f"event-{index}-{kind.lower()}",
            f"TraceEvent.{kind}",
            "normalized_trace",
            TRACE,
            ("events", index),
            *fields,
        )
        for index, kind, fields in (
            (
                0,
                "SYSTEM_VISIBLE_MESSAGE",
                ("event_id", "sequence", "event_kind", "content"),
            ),
            (1, "USER_MESSAGE", ("event_id", "sequence", "event_kind", "content")),
            (
                2,
                "MODEL_OBSERVATION",
                (
                    "event_id",
                    "sequence",
                    "event_kind",
                    "model_ref",
                    "output",
                    "cost_amount",
                    "cost_currency",
                ),
            ),
            (
                3,
                "TOOL_CALL",
                ("event_id", "sequence", "event_kind", "tool_name", "arguments"),
            ),
            (
                4,
                "TOOL_RESULT.SUCCEEDED",
                (
                    "event_id",
                    "sequence",
                    "event_kind",
                    "tool_call_event_id",
                    "result_state",
                    "result",
                ),
            ),
            (
                5,
                "ASSISTANT_MESSAGE",
                ("event_id", "sequence", "event_kind", "content", "is_final"),
            ),
            (
                6,
                "HANDOFF",
                (
                    "event_id",
                    "sequence",
                    "event_kind",
                    "handoff_kind",
                    "destination_ref",
                    "outcome",
                ),
            ),
            (
                8,
                "TERMINAL.SUCCESS",
                ("event_id", "sequence", "event_kind", "terminal_state"),
            ),
        )
    ),
    _object(
        "event-tool-result-error",
        "TraceEvent.TOOL_RESULT.ERROR",
        "normalized_trace",
        TRACE_TOOL_ERROR,
        ("events", 4),
        "event_id",
        "sequence",
        "event_kind",
        "tool_call_event_id",
        "result_state",
        "error_code",
        "error_message",
    ),
    _object(
        "event-terminal-error",
        "TraceEvent.TERMINAL.ERROR",
        "normalized_trace",
        TRACE_TERMINAL_ERROR,
        ("events", 8),
        "event_id",
        "sequence",
        "event_kind",
        "terminal_state",
        "reason_code",
    ),
    # protected_case and shared nested families.
    _object(
        "case",
        "protected_case",
        "protected_case",
        CASE,
        (),
        "contract_kind",
        "schema_version",
        "case_id",
        "risk_name",
        "source_evidence",
        "replay_input",
        "fixture_contract",
        "release_obligation",
        "evidence_requirements",
        "approval",
        "qualification",
        "case_version",
    ),
    _object(
        "evidence-reference",
        "EvidenceReference",
        "protected_case",
        CASE,
        ("source_evidence", 0),
        "reference_id",
        "reference_kind",
        "content_hash",
    ),
    _object(
        "locator-https",
        "EvidenceLocator.HTTPS",
        "protected_case",
        CASE,
        ("source_evidence", 1, "locator"),
        "locator_kind",
        "url",
    ),
    _object(
        "locator-opaque",
        "EvidenceLocator.OPAQUE",
        "protected_case",
        CASE_OPAQUE,
        ("source_evidence", 1, "locator"),
        "locator_kind",
        "token",
    ),
    _object(
        "replay-input",
        "ReplayInput",
        "protected_case",
        CASE,
        ("replay_input",),
        "messages",
    ),
    _object(
        "replay-message",
        "ReplayMessage",
        "protected_case",
        CASE,
        ("replay_input", "messages", 0),
        "message_id",
        "role",
        "content",
    ),
    _object(
        "fixture-contract",
        "FixtureContract",
        "protected_case",
        CASE,
        ("fixture_contract",),
        "fixture_id",
        "fixture_version",
        "fixture_fingerprint",
        "reset_policy_hash",
    ),
    _object(
        "release-obligation",
        "ReleaseObligation",
        "protected_case",
        CASE,
        ("release_obligation",),
        "obligation_id",
        "obligation_statement",
        "source_reference",
        "severity",
        "owner_actor_id",
        "applicability_conditions",
        "expected_behavior",
        "prohibited_behavior",
        "allowed_alternatives",
        "handoff_requirement",
    ),
    _object(
        "behavior-statement",
        "BehaviorStatement",
        "protected_case",
        CASE,
        ("release_obligation", "obligation_statement"),
        "statement_id",
        "text",
    ),
    _object(
        "handoff-none",
        "HandoffRequirement.NONE",
        "protected_case",
        CASE_MINIMAL,
        ("release_obligation", "handoff_requirement"),
        "handoff_kind",
    ),
    _object(
        "handoff-required",
        "HandoffRequirement.REQUIRED",
        "protected_case",
        CASE,
        ("release_obligation", "handoff_requirement"),
        "handoff_kind",
    ),
    _object(
        "approval",
        "Approval",
        "protected_case",
        CASE,
        ("approval",),
        "actor_id",
        "approved_at",
        "source_reference",
    ),
    _object(
        "qualification-ready",
        "Qualification.READY",
        "protected_case",
        CASE_MINIMAL,
        ("qualification",),
        "qualification_state",
    ),
    _object(
        "qualification-needs-fixture",
        "Qualification.NEEDS_FIXTURE",
        "protected_case",
        CASE,
        ("qualification",),
        "qualification_state",
        "reason_code",
        "explanation_reference",
    ),
    _object(
        "qualification-not-yet",
        "Qualification.NOT_YET",
        "protected_case",
        CASE_NOT_YET,
        ("qualification",),
        "qualification_state",
        "reason_code",
        "explanation_reference",
    ),
    *tuple(
        _object(
            f"requirement-assertion-{index}",
            "EvidenceRequirement.TRIANA_ASSERTION",
            "protected_case",
            CASE,
            ("evidence_requirements", index - 1),
            "requirement_id",
            "requirement_kind",
            "required_observation",
            "minimum_trials",
            "assertion",
        )
        for index in range(1, 9)
    ),
    _object(
        "requirement-evaluator",
        "EvidenceRequirement.CUSTOMER_EVALUATOR",
        "protected_case",
        CASE,
        ("evidence_requirements", 8),
        "requirement_id",
        "requirement_kind",
        "required_observation",
        "minimum_trials",
        "evaluator_id",
        "evaluator_version",
        "check_id",
    ),
    *tuple(
        _object(
            f"assertion-{index}-{kind}",
            f"AssertionDefinition.{kind}",
            "protected_case",
            CASE,
            ("evidence_requirements", index - 1, "assertion"),
            *fields,
        )
        for index, kind, fields in (
            (
                1,
                "tool_called",
                ("assertion_id", "assertion_version", "assertion_kind", "tool_name"),
            ),
            (
                2,
                "tool_not_called",
                ("assertion_id", "assertion_version", "assertion_kind", "tool_name"),
            ),
            (
                3,
                "tool_called_before",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "before_tool_name",
                    "after_tool_name",
                    "occurrence_rule",
                ),
            ),
            (
                4,
                "arg_matches",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "tool_name",
                    "argument_pointer",
                    "call_selection",
                    "matcher",
                ),
            ),
            (
                5,
                "no_loop",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "signature",
                    "maximum_consecutive_calls",
                ),
            ),
            (
                6,
                "no_unbacked_claim",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "regex_engine",
                    "output_pattern",
                    "pattern_flags",
                    "claim_group_name",
                    "supporting_tool_name",
                    "support_result_pointer",
                    "normalization",
                    "support_must_precede_claim",
                ),
            ),
            (
                7,
                "output_matches",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "target",
                    "matcher",
                ),
            ),
            (
                8,
                "terminal_state",
                (
                    "assertion_id",
                    "assertion_version",
                    "assertion_kind",
                    "expected_state",
                ),
            ),
        )
    ),
    _object(
        "value-matcher-exact",
        "ValueMatcher.EXACT_JSON",
        "protected_case",
        CASE,
        ("evidence_requirements", 3, "assertion", "matcher"),
        "matcher_kind",
        "expected_hash",
    ),
    _object(
        "value-matcher-regex",
        "ValueMatcher.STRING_REGEX",
        "protected_case",
        CASE_VALUE_REGEX,
        ("evidence_requirements", 3, "assertion", "matcher"),
        "matcher_kind",
        "regex_engine",
        "pattern",
        "flags",
    ),
    _object(
        "output-matcher-schema",
        "OutputMatcher.JSON_SCHEMA",
        "protected_case",
        CASE,
        ("evidence_requirements", 6, "assertion", "matcher"),
        "matcher_kind",
        "schema_draft",
        "schema_hash",
        "schema_reference",
    ),
    _object(
        "output-matcher-regex",
        "OutputMatcher.STRING_REGEX",
        "protected_case",
        CASE_OUTPUT_REGEX,
        ("evidence_requirements", 6, "assertion", "matcher"),
        "matcher_kind",
        "regex_engine",
        "pattern",
        "flags",
    ),
    # release_evidence_record and all record-side union arms.
    _object(
        "record",
        "release_evidence_record",
        "release_evidence_record",
        RECORD,
        (),
        "contract_kind",
        "schema_version",
        "seal_state",
        "project_id",
        "release_stream_id",
        "run_id",
        "created_at",
        "release_change",
        "protected_case_id",
        "protected_case_version",
        "release_obligation",
        "evidence_requirements",
        "execution_contracts",
        "trials",
        "comparison",
        "evidence_strength",
        "record_gaps",
        "policy_evaluation",
        "recommendation",
        "chain_link",
        "current_record_hash",
    ),
    _object(
        "release-change",
        "ReleaseChange",
        "release_evidence_record",
        RECORD,
        ("release_change",),
        "change_id",
        "declaration_reference",
        "candidate_code_ref",
        "baseline",
        "components",
        "unresolved_difference_references",
    ),
    _object(
        "baseline-approved",
        "BaselineBinding.APPROVED",
        "release_evidence_record",
        RECORD,
        ("release_change", "baseline"),
        "baseline_kind",
        "code_ref",
        "approval_reference",
    ),
    _object(
        "baseline-missing",
        "BaselineBinding.MISSING",
        "release_evidence_record",
        RECORD_FIRST,
        ("release_change", "baseline"),
        "baseline_kind",
        "reason_code",
    ),
    _object(
        "change-component-changed",
        "ReleaseChangeComponent.CHANGED",
        "release_evidence_record",
        RECORD,
        ("release_change", "components", 0),
        "component_kind",
        "candidate_fingerprint",
        "baseline_fingerprint",
        "declared_state",
    ),
    _object(
        "change-component-unknown",
        "ReleaseChangeComponent.UNKNOWN",
        "release_evidence_record",
        RECORD,
        ("release_change", "components", 1),
        "component_kind",
        "candidate_fingerprint",
        "baseline_fingerprint",
        "declared_state",
        "difference_reference_id",
    ),
    *tuple(
        _object(
            name,
            family,
            "release_evidence_record",
            factory,
            ("execution_contracts",),
            *fields,
        )
        for name, family, factory, fields in (
            (
                "binding-matched",
                "ExecutionContractBinding.MATCHED",
                RECORD,
                ("execution_binding_kind", "execution_contract"),
            ),
            (
                "binding-candidate",
                "ExecutionContractBinding.CANDIDATE_ONLY",
                RECORD_FIRST,
                ("execution_binding_kind", "candidate_execution_contract"),
            ),
            (
                "binding-mismatched",
                "ExecutionContractBinding.MISMATCHED",
                RECORD_MOVED,
                (
                    "execution_binding_kind",
                    "baseline_execution_contract",
                    "candidate_execution_contract",
                ),
            ),
        )
    ),
    _object(
        "execution-contract",
        "ExecutionContract",
        "release_evidence_record",
        RECORD,
        ("execution_contracts", "execution_contract"),
        "contract_version",
        "command_hash",
        "fixture_fingerprint",
        "configuration_fingerprint",
        "reset_policy_hash",
        "observation_scope",
        "randomization_policy",
        "declared_trial_count",
        "execution_contract_hash",
    ),
    _object(
        "execution-random-none",
        "ExecutionRandomizationPolicy.NONE",
        "release_evidence_record",
        RECORD_FIRST,
        ("execution_contracts", "candidate_execution_contract", "randomization_policy"),
        "randomization_policy_kind",
    ),
    _object(
        "execution-random-seeded",
        "ExecutionRandomizationPolicy.SEEDED",
        "release_evidence_record",
        RECORD,
        ("execution_contracts", "execution_contract", "randomization_policy"),
        "randomization_policy_kind",
        "generator",
        "generator_version",
    ),
    _object(
        "runtime-fingerprint",
        "RuntimeFingerprint",
        "release_evidence_record",
        RECORD,
        ("trials", 0, "runtime_fingerprint"),
        "components",
        "runtime_hash",
    ),
    _object(
        "runtime-component",
        "RuntimeComponent",
        "release_evidence_record",
        RECORD,
        ("trials", 0, "runtime_fingerprint", "components", 0),
        "component_kind",
        "fingerprint",
    ),
    _object(
        "trial-random-none",
        "TrialRandomization.NONE",
        "release_evidence_record",
        RECORD_FIRST,
        ("trials", 0, "randomization"),
        "randomization_kind",
    ),
    _object(
        "trial-random-seeded",
        "TrialRandomization.SEEDED",
        "release_evidence_record",
        RECORD,
        ("trials", 0, "randomization"),
        "randomization_kind",
        "seed",
        "generator",
        "generator_version",
    ),
    _object(
        "trial-result",
        "TrialResult",
        "release_evidence_record",
        RECORD,
        ("trials", 0),
        "trial_id",
        "run_id",
        "case_version",
        "side",
        "trial_index",
        "code_ref",
        "execution_contract_hash",
        "runtime_fingerprint",
        "randomization",
        "execution_status",
        "assertion_results",
        "customer_evaluator_results",
        "gaps",
        "end_to_end_status",
    ),
    _object(
        "assertion-result",
        "AssertionResult",
        "release_evidence_record",
        RECORD,
        ("trials", 0, "assertion_results", 0),
        "result_id",
        "requirement_id",
        "assertion_id",
        "assertion_version",
        "execution_index",
        "status",
        "reason_code",
        "evidence_references",
        "gap_ids",
    ),
    _object(
        "evaluator-result",
        "CustomerEvaluatorResult",
        "release_evidence_record",
        RECORD,
        ("trials", 0, "customer_evaluator_results", 0),
        "result_id",
        "requirement_id",
        "check_id",
        "evaluator_id",
        "evaluator_version",
        "status",
        "evidence_references",
        "gap_ids",
    ),
    _object(
        "evidence-gap-record",
        "EvidenceGap",
        "release_evidence_record",
        RECORD_FIRST,
        ("record_gaps", 0),
        "gap_id",
        "gap_code",
        "stage",
        "scope",
        "reason_reference",
        "evidence_references",
    ),
    _object(
        "gap-scope-record",
        "GapScope.RECORD",
        "release_evidence_record",
        RECORD_FIRST,
        ("record_gaps", 0, "scope"),
        "scope_kind",
    ),
    _object(
        "gap-scope-trial",
        "GapScope.TRIAL",
        "release_evidence_record",
        RECORD_TRIAL_GAP,
        ("trials", 1, "gaps", 0, "scope"),
        "scope_kind",
        "trial_id",
    ),
    _object(
        "gap-scope-assertion",
        "GapScope.ASSERTION",
        "release_evidence_record",
        RECORD_ASSERTION_GAP,
        ("trials", 1, "gaps", 0, "scope"),
        "scope_kind",
        "trial_id",
        "assertion_id",
    ),
    _object(
        "gap-scope-evaluator",
        "GapScope.EVALUATOR",
        "release_evidence_record",
        RECORD_EVALUATOR_GAP,
        ("trials", 1, "gaps", 0, "scope"),
        "scope_kind",
        "trial_id",
        "evaluator_id",
        "check_id",
    ),
    _object(
        "side-summary",
        "SideSummary",
        "release_evidence_record",
        RECORD,
        ("comparison", "candidate"),
        "trial_count",
        "evaluable_count",
        "pass_count",
        "pass_rate",
    ),
    *tuple(
        _object(
            name,
            family,
            "release_evidence_record",
            factory,
            ("comparison",),
            *fields,
        )
        for name, family, factory, fields in (
            (
                "comparison-comparable",
                "Comparison.COMPARABLE",
                RECORD,
                (
                    "comparison_status",
                    "candidate",
                    "baseline",
                    "movement",
                    "reason_codes",
                ),
            ),
            (
                "comparison-first",
                "Comparison.FIRST_OBSERVATION",
                RECORD_FIRST,
                ("comparison_status", "candidate", "reason_codes"),
            ),
            (
                "comparison-moved",
                "Comparison.MOVED",
                RECORD_MOVED,
                ("comparison_status", "candidate", "baseline", "reason_codes"),
            ),
            (
                "comparison-insufficient",
                "Comparison.INSUFFICIENT_EVIDENCE",
                RECORD_GAP_NO_BASELINE,
                ("comparison_status", "candidate", "reason_codes"),
            ),
        )
    ),
    _object(
        "policy-evaluation",
        "PolicyEvaluation",
        "release_evidence_record",
        RECORD,
        ("policy_evaluation",),
        "policy_id",
        "policy_version",
        "policy_hash",
        "rule_id",
        "input_evidence_hash",
        "reason_codes",
        "recommendation",
    ),
    _object(
        "chain-link-genesis",
        "RecordChainLink.GENESIS",
        "release_evidence_record",
        RECORD,
        ("chain_link",),
        "link_kind",
    ),
    _object(
        "chain-link-append",
        "RecordChainLink.APPEND",
        "release_evidence_record",
        RECORD_APPEND,
        ("chain_link",),
        "link_kind",
        "previous_record_hash",
    ),
    # record_chain and decision_attestation.
    _object(
        "record-chain",
        "record_chain",
        "record_chain",
        CHAIN,
        (),
        "contract_kind",
        "schema_version",
        "chain_id",
        "project_id",
        "release_stream_id",
        "entries",
        "head_record_hash",
        "chain_hash",
    ),
    _object(
        "chain-entry-genesis",
        "RecordChainEntry.GENESIS",
        "record_chain",
        CHAIN,
        ("entries", 0),
        "position",
        "record_hash",
        "link_kind",
    ),
    _object(
        "chain-entry-append",
        "RecordChainEntry.APPEND",
        "record_chain",
        CHAIN,
        ("entries", 1),
        "position",
        "record_hash",
        "link_kind",
        "previous_record_hash",
    ),
    _object(
        "attestation",
        "decision_attestation",
        "decision_attestation",
        ATTESTATION,
        (),
        "contract_kind",
        "schema_version",
        "attestation_id",
        "release_record_hash",
        "decision_type",
        "actor_id",
        "decided_at",
        "source_reference",
        "exception_rationale_reference",
        "attestation_hash",
    ),
)


PUBLIC_KINDS = frozenset(
    {
        "normalized_trace",
        "protected_case",
        "release_evidence_record",
        "record_chain",
        "decision_attestation",
    }
)

DOCUMENTED_FAMILIES = frozenset(
    {
        "Approval",
        "AssertionDefinition.arg_matches",
        "AssertionDefinition.no_loop",
        "AssertionDefinition.no_unbacked_claim",
        "AssertionDefinition.output_matches",
        "AssertionDefinition.terminal_state",
        "AssertionDefinition.tool_called",
        "AssertionDefinition.tool_called_before",
        "AssertionDefinition.tool_not_called",
        "AssertionResult",
        "BaselineBinding.APPROVED",
        "BaselineBinding.MISSING",
        "BehaviorStatement",
        "Comparison.COMPARABLE",
        "Comparison.FIRST_OBSERVATION",
        "Comparison.INSUFFICIENT_EVIDENCE",
        "Comparison.MOVED",
        "CustomerEvaluatorResult",
        "EvidenceGap",
        "EvidenceLocator.HTTPS",
        "EvidenceLocator.OPAQUE",
        "EvidenceReference",
        "EvidenceRequirement.CUSTOMER_EVALUATOR",
        "EvidenceRequirement.TRIANA_ASSERTION",
        "ExecutionContract",
        "ExecutionContractBinding.CANDIDATE_ONLY",
        "ExecutionContractBinding.MATCHED",
        "ExecutionContractBinding.MISMATCHED",
        "ExecutionRandomizationPolicy.NONE",
        "ExecutionRandomizationPolicy.SEEDED",
        "FixtureContract",
        "GapScope.ASSERTION",
        "GapScope.EVALUATOR",
        "GapScope.RECORD",
        "GapScope.TRIAL",
        "HandoffRequirement.NONE",
        "HandoffRequirement.REQUIRED",
        "ObservationScope",
        "OutputMatcher.JSON_SCHEMA",
        "OutputMatcher.STRING_REGEX",
        "PolicyEvaluation",
        "Qualification.NEEDS_FIXTURE",
        "Qualification.NOT_YET",
        "Qualification.READY",
        "RecordChainEntry.APPEND",
        "RecordChainEntry.GENESIS",
        "RecordChainLink.APPEND",
        "RecordChainLink.GENESIS",
        "ReleaseChange",
        "ReleaseChangeComponent.CHANGED",
        "ReleaseChangeComponent.UNKNOWN",
        "ReleaseObligation",
        "ReplayInput",
        "ReplayMessage",
        "RuntimeComponent",
        "RuntimeFingerprint",
        "SideSummary",
        "TraceEvent.ASSISTANT_MESSAGE",
        "TraceEvent.HANDOFF",
        "TraceEvent.MODEL_OBSERVATION",
        "TraceEvent.SYSTEM_VISIBLE_MESSAGE",
        "TraceEvent.TERMINAL.ERROR",
        "TraceEvent.TERMINAL.SUCCESS",
        "TraceEvent.TOOL_CALL",
        "TraceEvent.TOOL_RESULT.ERROR",
        "TraceEvent.TOOL_RESULT.SUCCEEDED",
        "TraceEvent.USER_MESSAGE",
        "TraceSource",
        "TrialRandomization.NONE",
        "TrialRandomization.SEEDED",
        "TrialResult",
        "ValueMatcher.EXACT_JSON",
        "ValueMatcher.STRING_REGEX",
        "decision_attestation",
        "normalized_trace",
        "protected_case",
        "record_chain",
        "release_evidence_record",
    }
)


def required_path_cases() -> tuple[tuple[str, Callable[[], JsonObject], Path], ...]:
    return tuple(
        (
            f"{item.name}.{field}",
            item.factory,
            (*item.path, field),
        )
        for item in OBJECT_COVERAGE
        for field in item.required_fields
    )


def closed_boundary_cases() -> tuple[tuple[str, Callable[[], JsonObject], Path], ...]:
    return tuple((item.name, item.factory, item.path) for item in OBJECT_COVERAGE)


RELEASE_RECORD_PROTECTED_FIELDS = (
    "contract_kind",
    "schema_version",
    "seal_state",
    "project_id",
    "release_stream_id",
    "run_id",
    "created_at",
    "release_change",
    "protected_case_id",
    "protected_case_version",
    "release_obligation",
    "evidence_requirements",
    "execution_contracts",
    "trials",
    "comparison",
    "evidence_strength",
    "record_gaps",
    "policy_evaluation",
    "recommendation",
    "pr_reference",
    "chain_link",
)


def protected_field_replacement(field: str, value: Any) -> Any:
    """Return a schema-valid, identity-changing replacement for a top-level field."""
    if field == "contract_kind":
        return "protected_case"
    if field == "schema_version":
        return 2
    if field == "seal_state":
        return "UNSIGNED"
    if isinstance(value, str):
        if value.startswith("sha256:"):
            return "sha256:" + ("7" * 64)
        if value.endswith("Z"):
            return "2026-07-30T10:00:01.000Z"
        return f"{value}-changed"
    if isinstance(value, list):
        changed = copy.deepcopy(value)
        changed.reverse()
        if changed == value:
            changed.append(copy.deepcopy(value[0]))
        return changed
    if isinstance(value, dict):
        changed = copy.deepcopy(value)
        first = next(iter(changed))
        original = changed[first]
        if isinstance(original, str):
            changed[first] = (
                "sha256:" + ("7" * 64)
                if original.startswith("sha256:")
                else f"{original}-changed"
            )
        elif isinstance(original, int):
            changed[first] = original + 1
        elif isinstance(original, list):
            changed[first] = list(reversed(original))
        else:
            raise TypeError((field, first, original))
        return changed
    raise TypeError((field, value))


def trial_identity_hash(value: JsonObject) -> str:
    """Test oracle helper retained here for manifest self-checks."""
    return domain_hash("trial_identity", value)
