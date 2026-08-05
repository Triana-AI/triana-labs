"""Frozen semantic contracts for the provider-neutral Diff V0 core."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import hashlib

from agentagon.core.types.json import JsonValue, canonical_json


class ReleaseSide(StrEnum):
    BASELINE = "BASELINE"
    CANDIDATE = "CANDIDATE"


class ReleaseRunKind(StrEnum):
    A_A_CONTROL = "A_A_CONTROL"
    A_B_CHANGE = "A_B_CHANGE"


class ResetPolicy(StrEnum):
    REQUIRED_EQUIVALENT = "REQUIRED_EQUIVALENT"
    ISOLATED_NAMESPACE = "ISOLATED_NAMESPACE"


class ExecutorKind(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    SEMANTIC_JUDGE = "SEMANTIC_JUDGE"
    EXTERNAL = "EXTERNAL"


class MeasurementValueType(StrEnum):
    BOOLEAN = "BOOLEAN"
    NUMBER = "NUMBER"
    CATEGORY = "CATEGORY"
    TEXT = "TEXT"


class MeasurementDirection(StrEnum):
    HIGHER_BETTER = "HIGHER_BETTER"
    LOWER_BETTER = "LOWER_BETTER"
    NEUTRAL = "NEUTRAL"


class MeasurementMaturity(StrEnum):
    DEFAULT = "DEFAULT"
    PROPOSED = "PROPOSED"
    CONFIRMED = "CONFIRMED"
    STALE = "STALE"


class MeasurementResultStatus(StrEnum):
    OK = "OK"
    ABSTAIN = "ABSTAIN"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    EXECUTION_ERROR = "EXECUTION_ERROR"


class ExecutionStatus(StrEnum):
    OK = "OK"
    GAP = "GAP"


class ExecutionGapKind(StrEnum):
    UNSUPPORTED = "UNSUPPORTED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    ANALYSIS_ONLY = "ANALYSIS_ONLY"
    MOCK_COVERAGE_GAP = "MOCK_COVERAGE_GAP"
    INVALID_SIMULATION = "INVALID_SIMULATION"
    EXECUTION_UNAVAILABLE = "EXECUTION_UNAVAILABLE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    TOOL_BACKEND_FAILURE = "TOOL_BACKEND_FAILURE"
    HARNESS_FAILURE = "HARNESS_FAILURE"
    TIMEOUT = "TIMEOUT"
    QUOTA = "QUOTA"
    NON_DETERMINISTIC_FLAKE = "NON_DETERMINISTIC_FLAKE"
    MALFORMED_TRACE = "MALFORMED_TRACE"
    MALFORMED_RESULT = "MALFORMED_RESULT"


class ComparisonStatus(StrEnum):
    CHANGED = "CHANGED"
    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    UNCHANGED = "UNCHANGED"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    IMPROVED = "IMPROVED"
    REGRESSED = "REGRESSED"
    VIOLATED = "VIOLATED"


@dataclass(frozen=True, slots=True)
class EvidenceReference:
    kind: str
    trace_id: str | None = None
    span_id: str | None = None
    case_id: str | None = None
    trial_id: str | None = None
    side: ReleaseSide | None = None
    artifact_path: str | None = None


@dataclass(frozen=True, slots=True)
class AgentVersion:
    agent_id: str
    source_revision: str
    config_digest: str
    prompt_digest: str | None = None
    model_digest: str | None = None
    tool_digest: str | None = None
    retrieval_digest: str | None = None
    harness_digest: str | None = None
    environment_profile: str | None = None

    @property
    def version_id(self) -> str:
        payload = {
            "agent_id": self.agent_id,
            "source_revision": self.source_revision,
            "config_digest": self.config_digest,
            "prompt_digest": self.prompt_digest,
            "model_digest": self.model_digest,
            "tool_digest": self.tool_digest,
            "retrieval_digest": self.retrieval_digest,
            "harness_digest": self.harness_digest,
            "environment_profile": self.environment_profile,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MaterialChange:
    change_id: str
    baseline_version_id: str
    candidate_version_id: str
    changed_artifacts: tuple[str, ...]
    developer_hypothesis: str | None = None
    commit_message: str | None = None

    def __post_init__(self) -> None:
        if self.baseline_version_id == self.candidate_version_id:
            raise ValueError("A material A/B change requires distinct agent versions")


@dataclass(frozen=True, slots=True)
class MeasurementDefinition:
    measurement_id: str
    version: str
    name: str
    criterion: str
    executor: ExecutorKind
    value_type: MeasurementValueType
    maturity: MeasurementMaturity
    evaluator_version: str
    direction: MeasurementDirection = MeasurementDirection.NEUTRAL
    expectation_id: str | None = None
    missingness_rule: str = "ABSTAIN"

    def __post_init__(self) -> None:
        if not self.evaluator_version:
            raise ValueError(
                "Measurement definitions require a pinned evaluator_version"
            )
        if (
            self.value_type is MeasurementValueType.TEXT
            and self.direction is not MeasurementDirection.NEUTRAL
        ):
            raise ValueError(
                "Text measurements need a structured evaluator before direction is meaningful"
            )


@dataclass(frozen=True, slots=True)
class MeasurementResult:
    measurement_id: str
    measurement_version: str
    status: MeasurementResultStatus
    value: JsonValue = None
    eligible_count: int = 0
    evaluable_count: int = 0
    reason: str | None = None
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        if self.status is MeasurementResultStatus.OK and self.value is None:
            raise ValueError("OK measurement results require a value")
        if self.status is not MeasurementResultStatus.OK and self.value is not None:
            raise ValueError(
                "Missing, abstained, or failed measurement results cannot carry a value"
            )
        if self.eligible_count < 0 or self.evaluable_count < 0:
            raise ValueError("Measurement counts cannot be negative")
        if self.evaluable_count > self.eligible_count:
            raise ValueError("Evaluable count cannot exceed eligible count")


@dataclass(frozen=True, slots=True)
class CaseTrialKey:
    case_id: str
    case_revision: str
    trial_id: str
    environment_draw_id: str
    expected_initial_state_hash: str
    reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT


@dataclass(frozen=True, slots=True)
class ExecutionGap:
    kind: ExecutionGapKind
    reason: str
    case_id: str | None = None
    trial_id: str | None = None
    side: ReleaseSide | None = None


@dataclass(frozen=True, slots=True)
class SideOutcome:
    side: ReleaseSide
    agent_version_id: str
    status: ExecutionStatus
    initial_state_hash: str | None
    final_reset_hash: str | None
    measurement_results: tuple[MeasurementResult, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()
    gap: ExecutionGap | None = None
    runtime_seconds: float | None = None
    estimated_cost: float | None = None
    final_state_hash: str | None = None

    def __post_init__(self) -> None:
        if (self.status is ExecutionStatus.GAP) != (self.gap is not None):
            raise ValueError(
                "GAP outcomes require one typed gap; OK outcomes cannot carry one"
            )


@dataclass(frozen=True, slots=True)
class PairOutcome:
    key: CaseTrialKey
    baseline: SideOutcome
    candidate: SideOutcome

    def __post_init__(self) -> None:
        if self.baseline.side is not ReleaseSide.BASELINE:
            raise ValueError("Baseline outcome must use BASELINE side")
        if self.candidate.side is not ReleaseSide.CANDIDATE:
            raise ValueError("Candidate outcome must use CANDIDATE side")

    @property
    def validity_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.baseline.status is not ExecutionStatus.OK:
            reasons.append("BASELINE_EXECUTION_GAP")
        if self.candidate.status is not ExecutionStatus.OK:
            reasons.append("CANDIDATE_EXECUTION_GAP")
        expected = self.key.expected_initial_state_hash
        for label, outcome in (
            ("BASELINE", self.baseline),
            ("CANDIDATE", self.candidate),
        ):
            if outcome.initial_state_hash != expected:
                reasons.append(f"{label}_INITIAL_STATE_MISMATCH")
            if (
                self.key.reset_policy is ResetPolicy.REQUIRED_EQUIVALENT
                and outcome.final_reset_hash != expected
            ):
                reasons.append(f"{label}_RESET_MISMATCH")
        return tuple(reasons)

    @property
    def is_valid(self) -> bool:
        return not self.validity_reasons


@dataclass(frozen=True, slots=True)
class ReleaseRun:
    run_id: str
    run_kind: ReleaseRunKind
    baseline: AgentVersion
    candidate: AgentVersion
    material_change: MaterialChange | None
    case_set_version: str
    measurement_versions: tuple[str, ...]
    evaluator_versions: tuple[str, ...]
    runner_adapter_version: str
    world_version: str
    fixture_bundle_hash: str
    protocol_version: str
    trial_count: int
    trace_adapter_versions: tuple[str, ...] = ()
    pairs: tuple[PairOutcome, ...] = ()
    execution_gaps: tuple[ExecutionGap, ...] = ()

    def __post_init__(self) -> None:
        if self.run_kind is ReleaseRunKind.A_A_CONTROL:
            if self.baseline.version_id != self.candidate.version_id:
                raise ValueError("A/A controls require the same pinned AgentVersion")
            if self.material_change is not None:
                raise ValueError("A/A controls cannot carry a MaterialChange")
        else:
            if self.material_change is None:
                raise ValueError("A/B runs require a MaterialChange")
            if self.baseline.version_id != self.material_change.baseline_version_id:
                raise ValueError(
                    "MaterialChange baseline does not match ReleaseRun baseline"
                )
            if self.candidate.version_id != self.material_change.candidate_version_id:
                raise ValueError(
                    "MaterialChange candidate does not match ReleaseRun candidate"
                )
        if self.trial_count < 1:
            raise ValueError("ReleaseRun requires at least one trial")
        seen_keys: set[CaseTrialKey] = set()
        for pair in self.pairs:
            if pair.key in seen_keys:
                raise ValueError("ReleaseRun cannot contain duplicate case/trial keys")
            seen_keys.add(pair.key)
            if pair.baseline.agent_version_id != self.baseline.version_id:
                raise ValueError(
                    "Pair baseline does not match pinned baseline AgentVersion"
                )
            if pair.candidate.agent_version_id != self.candidate.version_id:
                raise ValueError(
                    "Pair candidate does not match pinned candidate AgentVersion"
                )

    @property
    def baseline_cache_key(self) -> str:
        payload = {
            "baseline_version_id": self.baseline.version_id,
            "case_set_version": self.case_set_version,
            "measurement_versions": self.measurement_versions,
            "evaluator_versions": self.evaluator_versions,
            "runner_adapter_version": self.runner_adapter_version,
            "world_version": self.world_version,
            "fixture_bundle_hash": self.fixture_bundle_hash,
            "protocol_version": self.protocol_version,
            "trial_count": self.trial_count,
            "trace_adapter_versions": self.trace_adapter_versions,
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DiffRow:
    measurement_id: str
    measurement_version: str
    status: ComparisonStatus
    baseline_value: JsonValue
    candidate_value: JsonValue
    delta: float | None
    evaluable_pairs: int
    total_pairs: int
    independent_case_count: int = 0
    abstained_pairs: int = 0
    invalid_pairs: int = 0
    interval: tuple[float, float] | None = None
    minimum_detectable_effect: float | None = None
    paired_transitions: tuple[tuple[str, int], ...] = ()
    expectation_id: str | None = None
    affected_case_ids: tuple[str, ...] = ()
    evidence: tuple[EvidenceReference, ...] = ()

    def __post_init__(self) -> None:
        authoritative = {
            ComparisonStatus.IMPROVED,
            ComparisonStatus.REGRESSED,
            ComparisonStatus.VIOLATED,
        }
        if self.status in authoritative and self.expectation_id is None:
            raise ValueError(
                "Improvement/regression/violation wording requires an Expectation"
            )
        if self.evaluable_pairs > self.total_pairs:
            raise ValueError("Evaluable pair count cannot exceed total pair count")
        if self.independent_case_count > self.evaluable_pairs:
            raise ValueError("Independent cases cannot exceed evaluable pairs")
        if (
            self.abstained_pairs + self.invalid_pairs + self.evaluable_pairs
            > self.total_pairs
        ):
            raise ValueError("Pair accounting cannot exceed total pair count")


@dataclass(frozen=True, slots=True)
class ReleaseDiff:
    diff_id: str
    release_run_id: str
    rows: tuple[DiffRow, ...]
    execution_gaps: tuple[ExecutionGap, ...] = ()
    release_verdict: str = field(default="NOT_ASSIGNED", init=False)
