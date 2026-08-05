"""Compile completed baseline/candidate bundles into paired Diff V0 outcomes."""

from __future__ import annotations

from collections.abc import Sequence

from agentagon.evals.evaluators import EvaluationInput, EvaluatorRegistry
from agentagon.evals.manifest import create_release_run
from agentagon.evals.models import (
    AgentVersion,
    CaseTrialKey,
    ExecutionGap,
    ExecutionGapKind,
    ExecutionStatus,
    MeasurementDefinition,
    PairOutcome,
    ReleaseRun,
    ReleaseRunKind,
    ReleaseSide,
    ResetPolicy,
    SideOutcome,
)
from agentagon.evals.trace_bundle import NormalizedTraceBundle


BundleIdentity = tuple[str, str, str, str]


def compile_release_run(
    *,
    run_id: str,
    run_kind: ReleaseRunKind,
    baseline_version: AgentVersion,
    candidate_version: AgentVersion,
    baseline_bundles: Sequence[NormalizedTraceBundle],
    candidate_bundles: Sequence[NormalizedTraceBundle],
    measurements: Sequence[MeasurementDefinition],
    registry: EvaluatorRegistry,
    case_set_version: str,
    runner_adapter_version: str,
    world_version: str,
    fixture_bundle_hash: str,
    protocol_version: str,
    change_id: str,
    changed_artifacts: tuple[str, ...] = (),
    developer_hypothesis: str | None = None,
    commit_message: str | None = None,
    execution_gaps: tuple[ExecutionGap, ...] = (),
    trace_adapter_versions: tuple[str, ...] = (),
) -> ReleaseRun:
    _validate_release_set(baseline_bundles, "baseline")
    _validate_release_set(candidate_bundles, "candidate")
    baseline_index = _index(baseline_bundles, "baseline")
    candidate_index = _index(candidate_bundles, "candidate")
    identities = sorted(set(baseline_index) | set(candidate_index))
    pairs = tuple(
        _compile_pair(
            identity,
            baseline_index.get(identity),
            candidate_index.get(identity),
            baseline_version,
            candidate_version,
            measurements,
            registry,
        )
        for identity in identities
    )
    trial_count = max(
        CounterByCase.from_identities(identities).maximum_trials,
        1,
    )
    return create_release_run(
        run_id=run_id,
        run_kind=run_kind,
        baseline=baseline_version,
        candidate=candidate_version,
        measurements=measurements,
        case_set_version=case_set_version,
        runner_adapter_version=runner_adapter_version,
        world_version=world_version,
        fixture_bundle_hash=fixture_bundle_hash,
        protocol_version=protocol_version,
        trial_count=trial_count,
        change_id=change_id,
        changed_artifacts=changed_artifacts,
        developer_hypothesis=developer_hypothesis,
        commit_message=commit_message,
        pairs=pairs,
        execution_gaps=execution_gaps,
        trace_adapter_versions=trace_adapter_versions,
    )


class CounterByCase:
    def __init__(self, counts: dict[tuple[str, str], int]) -> None:
        self.counts = counts

    @classmethod
    def from_identities(cls, identities: Sequence[BundleIdentity]) -> CounterByCase:
        seen: dict[tuple[str, str], set[str]] = {}
        for case_id, revision, trial_id, _ in identities:
            seen.setdefault((case_id, revision), set()).add(trial_id)
        return cls({key: len(value) for key, value in seen.items()})

    @property
    def maximum_trials(self) -> int:
        return max(self.counts.values(), default=0)


def _compile_pair(
    identity: BundleIdentity,
    baseline: NormalizedTraceBundle | None,
    candidate: NormalizedTraceBundle | None,
    baseline_version: AgentVersion,
    candidate_version: AgentVersion,
    measurements: Sequence[MeasurementDefinition],
    registry: EvaluatorRegistry,
) -> PairOutcome:
    case_id, revision, trial_id, draw_id = identity
    available = baseline or candidate
    assert available is not None
    reset_policy = _resolve_reset_policy(baseline, candidate)
    expected_hash = _resolve_initial_hash(baseline, candidate)
    key = CaseTrialKey(
        case_id=case_id,
        case_revision=revision,
        trial_id=trial_id,
        environment_draw_id=draw_id,
        expected_initial_state_hash=expected_hash,
        reset_policy=reset_policy,
    )
    return PairOutcome(
        key=key,
        baseline=_compile_side(
            baseline,
            ReleaseSide.BASELINE,
            baseline_version.version_id,
            measurements,
            registry,
            case_id,
            trial_id,
        ),
        candidate=_compile_side(
            candidate,
            ReleaseSide.CANDIDATE,
            candidate_version.version_id,
            measurements,
            registry,
            case_id,
            trial_id,
        ),
    )


def _compile_side(
    bundle: NormalizedTraceBundle | None,
    side: ReleaseSide,
    version_id: str,
    measurements: Sequence[MeasurementDefinition],
    registry: EvaluatorRegistry,
    case_id: str,
    trial_id: str,
) -> SideOutcome:
    if bundle is None:
        gap = ExecutionGap(
            ExecutionGapKind.EXECUTION_UNAVAILABLE,
            f"{side.value} bundle is missing",
            case_id,
            trial_id,
            side,
        )
        return SideOutcome(side, version_id, ExecutionStatus.GAP, None, None, gap=gap)
    gap_kind = bundle.execution.status.gap_kind
    if gap_kind is not None:
        gap = ExecutionGap(
            gap_kind,
            bundle.execution.reason or bundle.execution.status.value,
            bundle.case_id,
            bundle.trial_id,
            side,
        )
        return SideOutcome(
            side,
            version_id,
            ExecutionStatus.GAP,
            bundle.initial_state_hash,
            bundle.reset_state_hash,
            final_state_hash=bundle.final_state_hash,
            gap=gap,
            runtime_seconds=bundle.execution.runtime_seconds,
            estimated_cost=bundle.execution.estimated_cost,
        )
    evaluation_input = EvaluationInput(normalized_trace=bundle.to_dict())
    results = tuple(
        registry.evaluate(definition, evaluation_input) for definition in measurements
    )
    return SideOutcome(
        side,
        version_id,
        ExecutionStatus.OK,
        bundle.initial_state_hash,
        bundle.reset_state_hash,
        final_state_hash=bundle.final_state_hash,
        measurement_results=results,
        runtime_seconds=bundle.execution.runtime_seconds,
        estimated_cost=bundle.execution.estimated_cost,
    )


def _index(
    bundles: Sequence[NormalizedTraceBundle],
    label: str,
) -> dict[BundleIdentity, NormalizedTraceBundle]:
    result: dict[BundleIdentity, NormalizedTraceBundle] = {}
    for bundle in bundles:
        identity = (
            bundle.case_id,
            bundle.case_revision,
            bundle.trial_id,
            bundle.environment_draw_id,
        )
        if identity in result:
            raise ValueError(f"Duplicate {label} bundle identity: {identity}")
        result[identity] = bundle
    return result


def _validate_release_set(
    bundles: Sequence[NormalizedTraceBundle],
    label: str,
) -> None:
    release_ids = {bundle.release_id for bundle in bundles}
    if len(release_ids) != 1:
        raise ValueError(f"{label} bundles must contain exactly one release_id")


def _resolve_initial_hash(
    baseline: NormalizedTraceBundle | None,
    candidate: NormalizedTraceBundle | None,
) -> str:
    hashes = {
        bundle.initial_state_hash
        for bundle in (baseline, candidate)
        if bundle is not None and bundle.initial_state_hash is not None
    }
    if len(hashes) == 1:
        return hashes.pop()
    if not hashes:
        return "MISSING_INITIAL_STATE"
    return "CONFLICTING_INITIAL_STATE"


def _resolve_reset_policy(
    baseline: NormalizedTraceBundle | None,
    candidate: NormalizedTraceBundle | None,
) -> ResetPolicy:
    policies = {
        bundle.reset_policy for bundle in (baseline, candidate) if bundle is not None
    }
    if policies == {ResetPolicy.ISOLATED_NAMESPACE}:
        return ResetPolicy.ISOLATED_NAMESPACE
    return ResetPolicy.REQUIRED_EQUIVALENT


__all__ = ["compile_release_run"]
