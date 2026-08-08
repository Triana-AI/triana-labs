"""Strict semantic boundary schemas for Behavior Map V0."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EvidenceCitationProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    conversation_id: str
    event_sequence: int
    quote: str

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_internal_coordinate(cls, value: Any) -> Any:
        """Keep test/internal producers compatible while exposing one canonical schema."""

        if isinstance(value, dict) and "turn_ordinal" in value:
            value = dict(value)
            value["event_sequence"] = value.pop("turn_ordinal")
        return value


class EpisodeFieldGroundingProposal(BaseModel):
    """Citation-index bindings for each independently retained demand field."""

    model_config = ConfigDict(extra="forbid")

    goal: list[int]
    requested_action: list[int]
    subject: list[int]
    constraints: list[list[int]]
    fallbacks: list[list[int]]


class EpisodeProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_id: str
    goal: str
    requested_action: str
    subject: str
    constraints: list[str]
    fallbacks: list[str]
    supersedes_local_id: str | None
    start_turn_ordinal: int
    end_turn_ordinal: int
    citations: list[EvidenceCitationProposal]
    grounding_contract_version: Literal[1]
    field_grounding: EpisodeFieldGroundingProposal
    status: Literal["PROPOSED", "UNKNOWN", "UNSUPPORTED"]

    @model_validator(mode="before")
    @classmethod
    def bind_current_grounding_version(cls, value: Any) -> Any:
        """Version explicit field bindings produced by current-schema callers."""

        if (
            isinstance(value, dict)
            and "field_grounding" in value
            and "grounding_contract_version" not in value
        ):
            value = dict(value)
            value["grounding_contract_version"] = 1
        return value


class BehaviorProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_id: str
    lane: Literal["DETERMINISTIC", "SEMANTIC", "HYBRID"]
    action: str
    object: str
    condition: str
    observed_effect: str | None
    episode_local_ids: list[str]
    citations: list[EvidenceCitationProposal]
    event_ids: list[str]
    status: Literal["PROPOSED", "OBSERVED", "UNKNOWN", "UNSUPPORTED"]


class ExtractionBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episodes: list[EpisodeProposal]
    behaviors: list[BehaviorProposal]


class PopulationProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    definition: str
    episode_ids: list[str]


class PopulationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    populations: list[PopulationProposal]
    unassigned_episode_ids: list[str] = Field(default_factory=list)
    ambiguous_episode_ids: list[str] = Field(default_factory=list)


class PopulationMatchProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    episode_id: str
    disposition: Literal["MATCH", "NO_MATCH", "AMBIGUOUS"]
    population_id: str | None


class PopulationMatchBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matches: list[PopulationMatchProposal]


class PatternProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    definition: str
    occurrence_ids: list[str]


class PatternBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patterns: list[PatternProposal]


class AgentContextProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    status: Literal["PROPOSED"]
    citations: list[EvidenceCitationProposal]


class AgentContextBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agent_context: AgentContextProposal


class AuditProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item_id: str
    decision: Literal["SUPPORTED", "MERGE", "SPLIT", "UNSUPPORTED", "UNCERTAIN"]
    reason: str


class AuditBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audits: list[AuditProposal]


class EvidenceCitationV0(TypedDict):
    conversation_id: str
    turn_ordinal: int
    quote: str


class ExcerptTruncationV0(TypedDict):
    truncated: Literal[True]
    field: str
    original_bytes: int
    displayed_bytes: int
    max_bytes: int
    string_byte_limit: int


class ConversationExcerptItemV0(TypedDict, total=False):
    event_sequence: int
    display_kind: Literal[
        "USER_MESSAGE",
        "TOOL_CALL",
        "TOOL_RESULT",
        "AGENT_RESPONSE",
        "NEXT_USER_MESSAGE",
    ]
    content: str
    tool_name: str
    tool_input: Any
    tool_result_status: str
    result_state: str | None
    result: Any
    error_code: str | None
    truncation: ExcerptTruncationV0


class EvidenceItemV0(TypedDict, total=False):
    evidence_id: str
    conversation_id: str
    kind: Literal["TRANSCRIPT", "EVENT"]
    ordinal: int
    text: str
    conversation_excerpt: list[ConversationExcerptItemV0]


class DemandEpisodeV0(TypedDict):
    episode_id: str
    conversation_id: str
    ordinal: int
    goal: str
    requested_action: str
    subject: str
    constraints: list[str]
    fallbacks: list[str]
    supersedes_episode_id: str | None
    start_turn_ordinal: int
    end_turn_ordinal: int
    citations: list[EvidenceCitationV0]
    status: Literal["PROPOSED", "UNKNOWN", "UNSUPPORTED"]
    method: str
    field_grounding: NotRequired[dict[str, Any]]
    excluded_citations: NotRequired[list[dict[str, Any]]]
    field_uncertainties: NotRequired[list[dict[str, Any]]]


class UserPopulationV0(TypedDict):
    population_id: str
    audit_subject_id: NotRequired[str]
    label: str
    definition: str
    episode_ids: list[str]
    support: int
    visibility: Literal["PROPOSED_POPULATION", "EMERGING", "UNKNOWN"]
    representative_evidence_ids: list[str]
    method: str
    audit_state: str
    predecessor_population_ids: NotRequired[list[str]]


class PopulationDispositionV0(TypedDict):
    episode_id: str
    disposition: Literal[
        "ASSIGNED",
        "INTENTIONALLY_UNASSIGNED",
        "AMBIGUOUS",
        "AUDIT_DISPUTED",
    ]
    population_id: NotRequired[str]
    reason: str


class AgentBehaviorOccurrenceV0(TypedDict):
    occurrence_id: str
    conversation_id: str
    lane: Literal["DETERMINISTIC", "SEMANTIC", "HYBRID"]
    action: str
    object: str
    condition: str
    observed_effect: str | None
    episode_ids: list[str]
    citations: list[EvidenceCitationV0]
    event_ids: list[str]
    evidence_ids: list[str]
    status: str
    method: str
    audit_disputed_episode_ids: NotRequired[list[str]]
    audit_state: NotRequired[Literal["DISPUTED", "PARTIAL"]]


class AgentBehaviorPatternV0(TypedDict):
    pattern_id: str
    audit_subject_id: NotRequired[str]
    label: str
    definition: str
    occurrence_ids: list[str]
    occurrence_count: int
    support: int
    method: str
    audit_state: str


class BehaviorMapReportV0(TypedDict):
    artifact_kind: Literal["behavior_map_report_v0"]
    schema_version: Literal[0]
    source: dict[str, Any]
    accounting: dict[str, Any]
    agent_context: dict[str, Any]
    episodes: list[DemandEpisodeV0]
    excluded_episode_citations: list[dict[str, Any]]
    populations: list[UserPopulationV0]
    population_dispositions: list[PopulationDispositionV0]
    behavior_occurrences: list[AgentBehaviorOccurrenceV0]
    behavior_patterns: list[AgentBehaviorPatternV0]
    emerging_unknown: list[dict[str, Any]]
    evidence: list[EvidenceItemV0]
    questions: list[str]
    gaps: list[dict[str, Any]]
    semantic_audit: dict[str, Any]
    method: dict[str, Any]
    provider_lineage: dict[str, Any]
    checkpoints: list[str]
    budget: dict[str, Any]
    report_id: str
