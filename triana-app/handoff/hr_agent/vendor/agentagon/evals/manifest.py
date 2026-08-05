"""Construct fully pinned release-run manifests."""

from __future__ import annotations

from collections.abc import Sequence

from agentagon.evals.identity import build_material_change
from agentagon.evals.models import (
    AgentVersion,
    ExecutionGap,
    MeasurementDefinition,
    PairOutcome,
    ReleaseRun,
    ReleaseRunKind,
)


def measurement_version_id(definition: MeasurementDefinition) -> str:
    return f"{definition.measurement_id}@{definition.version}"


def create_release_run(
    *,
    run_id: str,
    baseline: AgentVersion,
    candidate: AgentVersion,
    measurements: Sequence[MeasurementDefinition],
    case_set_version: str,
    runner_adapter_version: str,
    world_version: str,
    fixture_bundle_hash: str,
    protocol_version: str,
    trial_count: int,
    change_id: str,
    changed_artifacts: tuple[str, ...] = (),
    developer_hypothesis: str | None = None,
    commit_message: str | None = None,
    pairs: tuple[PairOutcome, ...] = (),
    run_kind: ReleaseRunKind = ReleaseRunKind.A_B_CHANGE,
    execution_gaps: tuple[ExecutionGap, ...] = (),
    trace_adapter_versions: tuple[str, ...] = (),
) -> ReleaseRun:
    if not measurements:
        raise ValueError("ReleaseRun requires at least one frozen measurement")
    measurement_versions = tuple(measurement_version_id(item) for item in measurements)
    if len(set(measurement_versions)) != len(measurement_versions):
        raise ValueError("Measurement versions must be unique within a ReleaseRun")
    evaluator_versions = tuple(
        dict.fromkeys(item.evaluator_version for item in measurements)
    )
    change = None
    if run_kind is ReleaseRunKind.A_B_CHANGE:
        change = build_material_change(
            change_id=change_id,
            baseline=baseline,
            candidate=candidate,
            changed_artifacts=changed_artifacts,
            developer_hypothesis=developer_hypothesis,
            commit_message=commit_message,
        )
    return ReleaseRun(
        run_id=run_id,
        run_kind=run_kind,
        baseline=baseline,
        candidate=candidate,
        material_change=change,
        case_set_version=case_set_version,
        measurement_versions=measurement_versions,
        evaluator_versions=evaluator_versions,
        runner_adapter_version=runner_adapter_version,
        world_version=world_version,
        fixture_bundle_hash=fixture_bundle_hash,
        protocol_version=protocol_version,
        trial_count=trial_count,
        trace_adapter_versions=trace_adapter_versions,
        pairs=pairs,
        execution_gaps=execution_gaps,
    )


__all__ = ["create_release_run", "measurement_version_id"]
