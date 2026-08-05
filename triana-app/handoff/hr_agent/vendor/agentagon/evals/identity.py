"""Resolve immutable agent versions without treating Git metadata as behavior."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from agentagon.core.types.json import JsonValue, canonical_json
from agentagon.evals.models import AgentVersion, MaterialChange


def digest_value(value: JsonValue) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AgentVersionInputs:
    agent_id: str
    source_revision: str
    config: JsonValue
    prompt: JsonValue = None
    model: JsonValue = None
    tools: JsonValue = None
    retrieval: JsonValue = None
    harness: JsonValue = None
    environment_profile: str | None = None


def resolve_agent_version(inputs: AgentVersionInputs) -> AgentVersion:
    """Hash behaviorally relevant inputs supplied by a customer/runtime adapter."""
    return AgentVersion(
        agent_id=inputs.agent_id,
        source_revision=inputs.source_revision,
        config_digest=digest_value(inputs.config),
        prompt_digest=_optional_digest(inputs.prompt),
        model_digest=_optional_digest(inputs.model),
        tool_digest=_optional_digest(inputs.tools),
        retrieval_digest=_optional_digest(inputs.retrieval),
        harness_digest=_optional_digest(inputs.harness),
        environment_profile=inputs.environment_profile,
    )


def build_material_change(
    *,
    change_id: str,
    baseline: AgentVersion,
    candidate: AgentVersion,
    changed_artifacts: tuple[str, ...] = (),
    developer_hypothesis: str | None = None,
    commit_message: str | None = None,
) -> MaterialChange:
    changed_components = tuple(
        name
        for name in (
            "source_revision",
            "config_digest",
            "prompt_digest",
            "model_digest",
            "tool_digest",
            "retrieval_digest",
            "harness_digest",
            "environment_profile",
        )
        if getattr(baseline, name) != getattr(candidate, name)
    )
    artifacts = tuple(dict.fromkeys((*changed_artifacts, *changed_components)))
    return MaterialChange(
        change_id=change_id,
        baseline_version_id=baseline.version_id,
        candidate_version_id=candidate.version_id,
        changed_artifacts=artifacts,
        developer_hypothesis=developer_hypothesis,
        commit_message=commit_message,
    )


def _optional_digest(value: JsonValue) -> str | None:
    return None if value is None else digest_value(value)


__all__ = [
    "AgentVersionInputs",
    "build_material_change",
    "digest_value",
    "resolve_agent_version",
]
