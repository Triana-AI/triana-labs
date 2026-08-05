"""Load pinned Diff V0 versions and measurement definitions from JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentagon.evals.identity import AgentVersionInputs, resolve_agent_version
from agentagon.evals.models import (
    AgentVersion,
    ExecutorKind,
    MeasurementDefinition,
    MeasurementDirection,
    MeasurementMaturity,
    MeasurementValueType,
)


def load_agent_version(path: Path) -> AgentVersion:
    payload = _load_object(path)
    return resolve_agent_version(
        AgentVersionInputs(
            agent_id=_required_text(payload, "agent_id"),
            source_revision=_required_text(payload, "source_revision"),
            config=payload.get("config"),
            prompt=payload.get("prompt"),
            model=payload.get("model"),
            tools=payload.get("tools"),
            retrieval=payload.get("retrieval"),
            harness=payload.get("harness"),
            environment_profile=_optional_text(payload.get("environment_profile")),
        )
    )


def load_measurements(path: Path) -> tuple[MeasurementDefinition, ...]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, list):
        raise ValueError(f"{path}: measurement config must be a list")
    definitions = tuple(_parse_measurement(item, path) for item in payload)
    if not definitions:
        raise ValueError(f"{path}: at least one measurement is required")
    return definitions


def _parse_measurement(value: Any, path: Path) -> MeasurementDefinition:
    if not isinstance(value, dict):
        raise ValueError(f"{path}: each measurement must be an object")
    try:
        return MeasurementDefinition(
            measurement_id=_required_text(value, "measurement_id"),
            version=_required_text(value, "version"),
            name=_required_text(value, "name"),
            criterion=_required_text(value, "criterion"),
            executor=ExecutorKind(_required_text(value, "executor").upper()),
            value_type=MeasurementValueType(
                _required_text(value, "value_type").upper()
            ),
            maturity=MeasurementMaturity(_required_text(value, "maturity").upper()),
            evaluator_version=_required_text(value, "evaluator_version"),
            direction=MeasurementDirection(
                str(value.get("direction", "NEUTRAL")).upper()
            ),
            expectation_id=_optional_text(value.get("expectation_id")),
            missingness_rule=str(value.get("missingness_rule", "ABSTAIN")),
        )
    except ValueError as error:
        raise ValueError(f"{path}: invalid measurement definition: {error}") from error


def _load_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


__all__ = ["load_agent_version", "load_measurements"]
