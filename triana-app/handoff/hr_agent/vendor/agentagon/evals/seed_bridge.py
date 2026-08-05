"""Data-only cold-start audit for any normalized trace bundle corpus."""

from __future__ import annotations

from collections import Counter
from typing import Any

from agentagon.evals.native_measurements import default_mechanical_measurements
from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle


def build_seed_bridge(bundles: tuple[NormalizedTraceBundle, ...]) -> dict[str, Any]:
    families = Counter(_scenario_text(item, "family", "UNKNOWN") for item in bundles)
    input_modes = Counter(
        _scenario_text(item, "input_mode", "UNKNOWN") for item in bundles
    )
    execution = Counter(item.execution.status.value for item in bundles)
    tool_calls = Counter(
        event.name
        for item in bundles
        for event in item.events
        if event.kind is EventKind.TOOL
    )
    user_turns = [
        sum(event.kind is EventKind.USER for event in item.events) for item in bundles
    ]
    agent_turns = [
        sum(event.kind is EventKind.AGENT for event in item.events) for item in bundles
    ]
    return {
        "schema_version": "seed-bridge-v0",
        "claim_boundary": (
            "Observed synthetic/test traffic coverage only. This is not production demand, "
            "a golden dataset, or inferred correctness."
        ),
        "trace_count": len(bundles),
        "case_count": len({(item.case_id, item.case_revision) for item in bundles}),
        "release_ids": sorted({item.release_id for item in bundles}),
        "scenario_family_counts": dict(sorted(families.items())),
        "input_mode_counts": dict(sorted(input_modes.items())),
        "execution_status_counts": dict(sorted(execution.items())),
        "tool_call_counts": dict(sorted(tool_calls.items())),
        "user_turns": _summary(user_turns),
        "agent_turns": _summary(agent_turns),
        "artifact_trace_count": sum(bool(item.artifact_refs) for item in bundles),
        "state_before_coverage": sum(
            item.initial_state_hash is not None for item in bundles
        ),
        "state_after_coverage": sum(
            item.final_state_hash is not None for item in bundles
        ),
        "reset_or_isolation_coverage": sum(
            item.reset_state_hash is not None
            or item.reset_policy.value == "ISOLATED_NAMESPACE"
            for item in bundles
        ),
        "default_mechanical_measurements": [
            {
                "measurement_id": item.measurement_id,
                "version": item.version,
                "name": item.name,
                "value_type": item.value_type.value,
                "direction": item.direction.value,
                "maturity": item.maturity.value,
            }
            for item in default_mechanical_measurements()
        ],
        "still_requires_seed_v0": [
            "agent purpose and authority inference",
            "semantic demand populations",
            "customer-relevant measurement proposals",
            "representative corpus review",
            "semantic judge qualification and customer confirmation",
        ],
    }


def _scenario_text(bundle: NormalizedTraceBundle, key: str, default: str) -> str:
    value = bundle.scenario.get(key)
    return value if isinstance(value, str) and value else default


def _summary(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"minimum": 0, "maximum": 0, "mean": 0.0}
    return {
        "minimum": min(values),
        "maximum": max(values),
        "mean": sum(values) / len(values),
    }


__all__ = ["build_seed_bridge"]
