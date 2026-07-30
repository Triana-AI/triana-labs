"""Explicit Pydantic authoring source for Slice 0A JSON contracts."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from triana.contracts.types import (
    CanonicalDecimal,
    Digest,
    DurationMs,
    ExternalId,
    FixedMovement,
    FixedRate,
    Index,
    JsonPointer,
    LocalContent,
    PositiveInt,
    SafeCode,
    SafeId,
    SafeInt,
    SafeLabel,
    SchemaVersion,
    StatementText,
    Timestamp,
)


class ContractModel(BaseModel):
    """Closed, strict wire object."""

    model_config = ConfigDict(extra="forbid", strict=True)


class OpaqueLocator(ContractModel):
    locator_kind: Literal["OPAQUE"]
    token: SafeId


class HttpsLocator(ContractModel):
    locator_kind: Literal["HTTPS"]
    url: ExternalId


EvidenceLocator = Annotated[
    OpaqueLocator | HttpsLocator, Field(discriminator="locator_kind")
]


class EvidenceReference(ContractModel):
    reference_id: SafeId
    reference_kind: Literal[
        "TRACE",
        "TOOL_EVENT",
        "ASSERTION",
        "EVALUATOR",
        "FIXTURE",
        "POLICY",
        "APPROVAL",
        "GITHUB",
        "OTHER",
    ]
    content_hash: Digest
    locator: EvidenceLocator = Field(default=None)  # type: ignore[assignment]


Capability = Literal[
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


class ObservationScope(ContractModel):
    capabilities: list[Capability] = Field(min_length=1, max_length=9)


class Approval(ContractModel):
    actor_id: SafeId
    actor_display_name: SafeLabel = Field(default=None)  # type: ignore[assignment]
    approved_at: Timestamp
    source_reference: EvidenceReference


class BehaviorStatement(ContractModel):
    statement_id: SafeId
    text: StatementText


ComponentKind = Literal[
    "AGENT_CODE",
    "MODEL",
    "PROMPT",
    "TOOLING",
    "RUNTIME",
    "CONFIGURATION",
    "FIXTURE",
    "EVALUATOR",
]


class RuntimeComponent(ContractModel):
    component_kind: ComponentKind
    fingerprint: Digest


class RuntimeFingerprint(ContractModel):
    components: list[RuntimeComponent] = Field(min_length=1, max_length=8)
    runtime_hash: Digest


class NoExecutionRandomization(ContractModel):
    randomization_policy_kind: Literal["NONE"]


class SeededExecutionRandomization(ContractModel):
    randomization_policy_kind: Literal["SEEDED"]
    generator: SafeLabel
    generator_version: SafeLabel


ExecutionRandomizationPolicy = Annotated[
    NoExecutionRandomization | SeededExecutionRandomization,
    Field(discriminator="randomization_policy_kind"),
]


class NoTrialRandomization(ContractModel):
    randomization_kind: Literal["NONE"]


class SeededTrialRandomization(ContractModel):
    randomization_kind: Literal["SEEDED"]
    seed: SafeId
    generator: SafeLabel
    generator_version: SafeLabel


TrialRandomization = Annotated[
    NoTrialRandomization | SeededTrialRandomization,
    Field(discriminator="randomization_kind"),
]


class ExecutionContract(ContractModel):
    contract_version: PositiveInt
    command_hash: Digest
    fixture_fingerprint: Digest
    configuration_fingerprint: Digest
    reset_policy_hash: Digest
    observation_scope: ObservationScope
    randomization_policy: ExecutionRandomizationPolicy
    declared_trial_count: Annotated[PositiveInt, Field(le=1000)]
    execution_contract_hash: Digest


class MatchedExecutionBinding(ContractModel):
    execution_binding_kind: Literal["MATCHED"]
    execution_contract: ExecutionContract


class CandidateExecutionBinding(ContractModel):
    execution_binding_kind: Literal["CANDIDATE_ONLY"]
    candidate_execution_contract: ExecutionContract


class MismatchedExecutionBinding(ContractModel):
    execution_binding_kind: Literal["MISMATCHED"]
    baseline_execution_contract: ExecutionContract
    candidate_execution_contract: ExecutionContract


ExecutionContractBinding = Annotated[
    MatchedExecutionBinding | CandidateExecutionBinding | MismatchedExecutionBinding,
    Field(discriminator="execution_binding_kind"),
]


class ApprovedBaseline(ContractModel):
    baseline_kind: Literal["APPROVED"]
    code_ref: SafeId
    approval_reference: EvidenceReference


class MissingBaseline(ContractModel):
    baseline_kind: Literal["MISSING"]
    reason_code: Literal["MISSING_APPROVED_BASELINE"]


BaselineBinding = Annotated[
    ApprovedBaseline | MissingBaseline, Field(discriminator="baseline_kind")
]


class ReleaseChangeComponent(ContractModel):
    component_kind: ComponentKind
    candidate_fingerprint: Digest
    baseline_fingerprint: Digest = Field(default=None)  # type: ignore[assignment]
    declared_state: Literal["CHANGED", "UNCHANGED", "UNKNOWN"]
    difference_reference_id: SafeId = Field(default=None)  # type: ignore[assignment]


class ReleaseChange(ContractModel):
    change_id: SafeId
    declaration_reference: EvidenceReference
    candidate_code_ref: SafeId
    baseline: BaselineBinding
    components: list[ReleaseChangeComponent] = Field(min_length=1, max_length=8)
    unresolved_difference_references: list[EvidenceReference] = Field(max_length=100)


class TraceSource(ContractModel):
    source_kind: Literal["LANGFUSE", "JSONL", "OTEL", "OTHER"]
    source_trace_id: ExternalId
    source_export_hash: Digest


class TraceEventBase(ContractModel):
    event_id: SafeId
    sequence: Index
    parent_event_id: SafeId = Field(default=None)  # type: ignore[assignment]
    occurred_at: Timestamp = Field(default=None)  # type: ignore[assignment]


class UserMessageEvent(TraceEventBase):
    event_kind: Literal["USER_MESSAGE"]
    content: LocalContent


class AssistantMessageEvent(TraceEventBase):
    event_kind: Literal["ASSISTANT_MESSAGE"]
    content: LocalContent
    is_final: bool


class SystemMessageEvent(TraceEventBase):
    event_kind: Literal["SYSTEM_VISIBLE_MESSAGE"]
    content: LocalContent


class ModelObservationEvent(TraceEventBase):
    event_kind: Literal["MODEL_OBSERVATION"]
    model_ref: SafeId
    output: LocalContent
    latency_ms: DurationMs = Field(default=None)  # type: ignore[assignment]
    cost_amount: CanonicalDecimal = Field(default=None)  # type: ignore[assignment]
    cost_currency: Annotated[str, Field(strict=True, pattern=r"^[A-Z]{3}$")] = Field(
        default=None
    )  # type: ignore[assignment]


class ToolCallEvent(TraceEventBase):
    event_kind: Literal["TOOL_CALL"]
    tool_name: SafeId
    arguments: Any


class ToolResultEvent(TraceEventBase):
    event_kind: Literal["TOOL_RESULT"]
    tool_call_event_id: SafeId
    result_state: Literal["SUCCEEDED", "ERROR"]
    result: Any = Field(default=None)
    error_code: SafeCode = Field(default=None)  # type: ignore[assignment]
    error_message: LocalContent = Field(default=None)  # type: ignore[assignment]


class HandoffEvent(TraceEventBase):
    event_kind: Literal["HANDOFF"]
    handoff_kind: Literal["HUMAN", "AGENT", "QUEUE"]
    destination_ref: SafeId
    outcome: Literal["REQUESTED", "ACCEPTED", "REJECTED"]


class TerminalEvent(TraceEventBase):
    event_kind: Literal["TERMINAL"]
    terminal_state: Literal["SUCCESS", "ERROR", "ABORTED"]
    reason_code: SafeCode = Field(default=None)  # type: ignore[assignment]


TraceEvent = Annotated[
    UserMessageEvent
    | AssistantMessageEvent
    | SystemMessageEvent
    | ModelObservationEvent
    | ToolCallEvent
    | ToolResultEvent
    | HandoffEvent
    | TerminalEvent,
    Field(discriminator="event_kind"),
]


class NormalizedTrace(ContractModel):
    contract_kind: Literal["normalized_trace"]
    schema_version: SchemaVersion
    privacy_class: Literal["LOCAL_SENSITIVE"]
    trace_id: SafeId
    source: TraceSource
    conversation_id: SafeId
    thread_id: SafeId = Field(default=None)  # type: ignore[assignment]
    agent_ref: SafeId = Field(default=None)  # type: ignore[assignment]
    release_ref: SafeId = Field(default=None)  # type: ignore[assignment]
    observation_scope: ObservationScope
    events: list[TraceEvent] = Field(min_length=1, max_length=10_000)
    trace_hash: Digest


class ReplayMessage(ContractModel):
    message_id: SafeId
    role: Literal["USER", "ASSISTANT", "SYSTEM_VISIBLE"]
    content: LocalContent


class ReplayInput(ContractModel):
    messages: list[ReplayMessage] = Field(min_length=1, max_length=100)


class FixtureContract(ContractModel):
    fixture_id: SafeId
    fixture_version: PositiveInt
    fixture_fingerprint: Digest
    reset_policy_hash: Digest


class NoHandoffRequirement(ContractModel):
    handoff_kind: Literal["NONE"]


class RequiredHandoff(ContractModel):
    handoff_kind: Literal["REQUIRED"]
    destination_ref: SafeId = Field(default=None)  # type: ignore[assignment]


HandoffRequirement = Annotated[
    NoHandoffRequirement | RequiredHandoff, Field(discriminator="handoff_kind")
]


class ReleaseObligation(ContractModel):
    obligation_id: SafeId
    obligation_statement: BehaviorStatement
    source_reference: EvidenceReference
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    owner_actor_id: SafeId
    applicability_conditions: list[BehaviorStatement] = Field(
        min_length=1, max_length=100
    )
    expected_behavior: list[BehaviorStatement] = Field(min_length=1, max_length=100)
    prohibited_behavior: list[BehaviorStatement] = Field(max_length=100)
    allowed_alternatives: list[BehaviorStatement] = Field(max_length=100)
    handoff_requirement: HandoffRequirement
    policy_context_reference: EvidenceReference = Field(default=None)  # type: ignore[assignment]


RegexFlag = Literal["ASCII", "IGNORE_CASE", "MULTILINE"]


class ExactJsonMatcher(ContractModel):
    matcher_kind: Literal["EXACT_JSON"]
    expected_hash: Digest
    expected_value_reference: EvidenceReference = Field(default=None)  # type: ignore[assignment]


class StringRegexMatcher(ContractModel):
    matcher_kind: Literal["STRING_REGEX"]
    regex_engine: Literal["PYTHON_RE_3_13"]
    pattern: StatementText
    flags: list[RegexFlag] = Field(max_length=3)


ValueMatcher = Annotated[
    ExactJsonMatcher | StringRegexMatcher, Field(discriminator="matcher_kind")
]


class JsonSchemaMatcher(ContractModel):
    matcher_kind: Literal["JSON_SCHEMA"]
    schema_draft: Literal["2020-12"]
    schema_hash: Digest
    schema_reference: EvidenceReference


OutputMatcher = Annotated[
    StringRegexMatcher | JsonSchemaMatcher, Field(discriminator="matcher_kind")
]


class AssertionBase(ContractModel):
    assertion_id: SafeId
    assertion_version: PositiveInt


class ToolCalledAssertion(AssertionBase):
    assertion_kind: Literal["tool_called"]
    tool_name: SafeId


class ToolNotCalledAssertion(AssertionBase):
    assertion_kind: Literal["tool_not_called"]
    tool_name: SafeId


class ToolCalledBeforeAssertion(AssertionBase):
    assertion_kind: Literal["tool_called_before"]
    before_tool_name: SafeId
    after_tool_name: SafeId
    occurrence_rule: Literal["FIRST_SUCCESSFUL_DISPATCH"]


class ArgMatchesAssertion(AssertionBase):
    assertion_kind: Literal["arg_matches"]
    tool_name: SafeId
    argument_pointer: JsonPointer
    call_selection: Literal["FIRST", "LAST", "EVERY"]
    matcher: ValueMatcher


class NoLoopAssertion(AssertionBase):
    assertion_kind: Literal["no_loop"]
    signature: Literal["TOOL_NAME", "TOOL_NAME_AND_ARGUMENT_HASH"]
    maximum_consecutive_calls: Annotated[PositiveInt, Field(le=1000)]


class NoUnbackedClaimAssertion(AssertionBase):
    assertion_kind: Literal["no_unbacked_claim"]
    regex_engine: Literal["PYTHON_RE_3_13"]
    output_pattern: StatementText
    pattern_flags: list[RegexFlag] = Field(max_length=3)
    claim_group_name: Literal["claim"]
    supporting_tool_name: SafeId
    support_result_pointer: JsonPointer
    normalization: Literal["EXACT_STRING", "ASCII_CASEFOLD_TRIM"]
    support_must_precede_claim: Literal[True]


class OutputMatchesAssertion(AssertionBase):
    assertion_kind: Literal["output_matches"]
    target: Literal["FINAL_ASSISTANT_MESSAGE"]
    matcher: OutputMatcher


class TerminalStateAssertion(AssertionBase):
    assertion_kind: Literal["terminal_state"]
    expected_state: Literal["NO_ERROR"]


AssertionDefinition = Annotated[
    ToolCalledAssertion
    | ToolNotCalledAssertion
    | ToolCalledBeforeAssertion
    | ArgMatchesAssertion
    | NoLoopAssertion
    | NoUnbackedClaimAssertion
    | OutputMatchesAssertion
    | TerminalStateAssertion,
    Field(discriminator="assertion_kind"),
]


class AssertionEvidenceRequirement(ContractModel):
    requirement_id: SafeId
    requirement_kind: Literal["TRIANA_ASSERTION"]
    required_observation: ObservationScope
    minimum_trials: Annotated[PositiveInt, Field(le=1000)]
    assertion: AssertionDefinition


class EvaluatorEvidenceRequirement(ContractModel):
    requirement_id: SafeId
    requirement_kind: Literal["CUSTOMER_EVALUATOR"]
    required_observation: ObservationScope
    minimum_trials: Annotated[PositiveInt, Field(le=1000)]
    evaluator_id: SafeId
    evaluator_version: Digest
    check_id: SafeId


EvidenceRequirement = Annotated[
    AssertionEvidenceRequirement | EvaluatorEvidenceRequirement,
    Field(discriminator="requirement_kind"),
]


class ReadyQualification(ContractModel):
    qualification_state: Literal["READY"]


class NeedsFixtureQualification(ContractModel):
    qualification_state: Literal["NEEDS_FIXTURE"]
    reason_code: Literal["FIXTURE_REQUIRED"]
    explanation_reference: EvidenceReference


class NotYetQualification(ContractModel):
    qualification_state: Literal["NOT_YET"]
    reason_code: SafeCode
    explanation_reference: EvidenceReference


Qualification = Annotated[
    ReadyQualification | NeedsFixtureQualification | NotYetQualification,
    Field(discriminator="qualification_state"),
]


class ProtectedCase(ContractModel):
    contract_kind: Literal["protected_case"]
    schema_version: SchemaVersion
    case_id: SafeId
    risk_name: SafeLabel
    source_evidence: list[EvidenceReference] = Field(min_length=1, max_length=100)
    replay_input: ReplayInput
    fixture_contract: FixtureContract
    release_obligation: ReleaseObligation
    evidence_requirements: list[EvidenceRequirement] = Field(
        min_length=1, max_length=100
    )
    approval: Approval
    qualification: Qualification
    case_version: Digest


class AssertionResult(ContractModel):
    result_id: SafeId
    requirement_id: SafeId
    assertion_id: SafeId
    assertion_version: PositiveInt
    execution_index: Index
    status: Literal["PASS", "FAIL", "UNEVALUABLE"]
    reason_code: SafeCode
    evidence_references: list[EvidenceReference] = Field(max_length=100)
    gap_ids: list[SafeId] = Field(max_length=100)


class CustomerEvaluatorResult(ContractModel):
    result_id: SafeId
    requirement_id: SafeId
    check_id: SafeId
    evaluator_id: SafeId
    evaluator_version: Digest
    status: Literal["PASS", "FAIL", "UNEVALUABLE"]
    score: CanonicalDecimal = Field(default=None)  # type: ignore[assignment]
    evidence_references: list[EvidenceReference] = Field(max_length=100)
    gap_ids: list[SafeId] = Field(max_length=100)


class RecordGapScope(ContractModel):
    scope_kind: Literal["RECORD"]


class TrialGapScope(ContractModel):
    scope_kind: Literal["TRIAL"]
    trial_id: Digest


class AssertionGapScope(ContractModel):
    scope_kind: Literal["ASSERTION"]
    trial_id: Digest
    assertion_id: SafeId


class EvaluatorGapScope(ContractModel):
    scope_kind: Literal["EVALUATOR"]
    trial_id: Digest
    evaluator_id: SafeId
    check_id: SafeId


GapScope = Annotated[
    RecordGapScope | TrialGapScope | AssertionGapScope | EvaluatorGapScope,
    Field(discriminator="scope_kind"),
]


class EvidenceGap(ContractModel):
    gap_id: SafeId
    gap_code: Literal[
        "MISSING_APPROVED_BASELINE",
        "EXECUTION_CONTRACT_MISMATCH",
        "MISSING_OBSERVATION",
        "NEGATIVE_ASSERTION_UNEVALUABLE",
        "EVALUATOR_TIMEOUT",
        "EVALUATOR_ERROR",
        "EVALUATOR_REFUSAL",
        "EVALUATOR_SCHEMA_INVALID",
        "INSUFFICIENT_TRIALS",
        "FIXTURE_REQUIRED",
    ]
    stage: Literal["QUALIFICATION", "EXECUTION", "ASSERTION", "EVALUATOR", "COMPARISON"]
    scope: GapScope
    reason_reference: EvidenceReference
    evidence_references: list[EvidenceReference] = Field(max_length=100)


class TrialResult(ContractModel):
    trial_id: Digest
    run_id: SafeId
    case_version: Digest
    side: Literal["BASELINE", "CANDIDATE"]
    trial_index: Index
    code_ref: SafeId
    execution_contract_hash: Digest
    runtime_fingerprint: RuntimeFingerprint
    randomization: TrialRandomization
    execution_status: Literal["COMPLETED", "ERROR", "TIMEOUT", "REFUSED"]
    trace_reference: EvidenceReference = Field(default=None)  # type: ignore[assignment]
    assertion_results: list[AssertionResult] = Field(max_length=1000)
    customer_evaluator_results: list[CustomerEvaluatorResult] = Field(max_length=1000)
    gaps: list[EvidenceGap] = Field(max_length=1000)
    end_to_end_status: Literal["PASS", "FAIL", "UNEVALUABLE"]


class SideSummary(ContractModel):
    trial_count: SafeInt
    evaluable_count: SafeInt
    pass_count: SafeInt
    pass_rate: FixedRate


class Comparison(ContractModel):
    comparison_status: Literal[
        "COMPARABLE", "FIRST_OBSERVATION", "MOVED", "INSUFFICIENT_EVIDENCE"
    ]
    candidate: SideSummary
    baseline: SideSummary = Field(default=None)  # type: ignore[assignment]
    movement: FixedMovement = Field(default=None)  # type: ignore[assignment]
    reason_codes: list[SafeCode] = Field(max_length=100)


class PolicyEvaluation(ContractModel):
    policy_id: SafeId
    policy_version: PositiveInt
    policy_hash: Digest
    rule_id: SafeId
    input_evidence_hash: Digest
    reason_codes: list[SafeCode] = Field(min_length=1, max_length=100)
    recommendation: Literal["PASS", "REVIEW", "BLOCK"]


class GenesisChainLink(ContractModel):
    link_kind: Literal["GENESIS"]


class AppendChainLink(ContractModel):
    link_kind: Literal["APPEND"]
    previous_record_hash: Digest
    supersedes_record_hash: Digest = Field(default=None)  # type: ignore[assignment]


RecordChainLink = Annotated[
    GenesisChainLink | AppendChainLink, Field(discriminator="link_kind")
]


class ReleaseEvidenceRecord(ContractModel):
    contract_kind: Literal["release_evidence_record"]
    schema_version: SchemaVersion
    seal_state: Literal["UNSIGNED", "SEALED"]
    project_id: SafeId
    release_stream_id: SafeId
    run_id: SafeId
    created_at: Timestamp
    release_change: ReleaseChange
    protected_case_id: SafeId
    protected_case_version: Digest
    release_obligation: ReleaseObligation
    evidence_requirements: list[EvidenceRequirement] = Field(
        min_length=1, max_length=100
    )
    execution_contracts: ExecutionContractBinding
    trials: list[TrialResult] = Field(min_length=1, max_length=1000)
    comparison: Comparison
    evidence_strength: Literal["SUFFICIENT", "LIMITED", "INSUFFICIENT"]
    record_gaps: list[EvidenceGap] = Field(max_length=1000)
    policy_evaluation: PolicyEvaluation
    recommendation: Literal["PASS", "REVIEW", "BLOCK"]
    pr_reference: EvidenceReference = Field(default=None)  # type: ignore[assignment]
    chain_link: RecordChainLink
    current_record_hash: Digest = Field(default=None)  # type: ignore[assignment]


class RecordChainEntry(ContractModel):
    position: Index
    record_hash: Digest
    link_kind: Literal["GENESIS", "APPEND"]
    previous_record_hash: Digest = Field(default=None)  # type: ignore[assignment]
    supersedes_record_hash: Digest = Field(default=None)  # type: ignore[assignment]


class RecordChain(ContractModel):
    contract_kind: Literal["record_chain"]
    schema_version: SchemaVersion
    chain_id: SafeId
    project_id: SafeId
    release_stream_id: SafeId
    entries: list[RecordChainEntry] = Field(min_length=1, max_length=1000)
    head_record_hash: Digest
    chain_hash: Digest


class DecisionAttestation(ContractModel):
    contract_kind: Literal["decision_attestation"]
    schema_version: SchemaVersion
    attestation_id: SafeId
    release_record_hash: Digest
    decision_type: Literal["APPROVE", "HOLD", "APPROVE_WITH_EXCEPTION"]
    actor_id: SafeId
    actor_display_name: SafeLabel = Field(default=None)  # type: ignore[assignment]
    decided_at: Timestamp
    source_reference: EvidenceReference
    exception_rationale_reference: EvidenceReference = Field(default=None)  # type: ignore[assignment]
    attestation_hash: Digest


PublicDocument = (
    NormalizedTrace
    | ProtectedCase
    | ReleaseEvidenceRecord
    | RecordChain
    | DecisionAttestation
)

DOCUMENT_MODELS: dict[str, type[ContractModel]] = {
    "normalized_trace": NormalizedTrace,
    "protected_case": ProtectedCase,
    "release_evidence_record": ReleaseEvidenceRecord,
    "record_chain": RecordChain,
    "decision_attestation": DecisionAttestation,
}
