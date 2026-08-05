"""Provider-neutral completed trace bundles consumed by Diff V0."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
from pathlib import Path
from typing import Any

from agentagon.core.types.json import JsonObject, JsonValue
from agentagon.evals.identity import digest_value
from agentagon.evals.models import ExecutionGap, ExecutionGapKind, ResetPolicy


class TraceBundleError(ValueError):
    pass


class EventKind(StrEnum):
    USER = "USER"
    AGENT = "AGENT"
    TOOL = "TOOL"
    WORKFLOW = "WORKFLOW"
    SYSTEM = "SYSTEM"
    ARTIFACT = "ARTIFACT"
    STATE = "STATE"


class BundleExecutionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"
    HARNESS_ERROR = "HARNESS_ERROR"
    ENVIRONMENT_ERROR = "ENVIRONMENT_ERROR"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    TOOL_BACKEND_ERROR = "TOOL_BACKEND_ERROR"

    @property
    def gap_kind(self) -> ExecutionGapKind | None:
        return {
            self.COMPLETED: None,
            self.TIMEOUT: ExecutionGapKind.TIMEOUT,
            self.HARNESS_ERROR: ExecutionGapKind.HARNESS_FAILURE,
            self.ENVIRONMENT_ERROR: ExecutionGapKind.ENVIRONMENT_FAILURE,
            self.BUDGET_EXHAUSTED: ExecutionGapKind.QUOTA,
            self.TOOL_BACKEND_ERROR: ExecutionGapKind.TOOL_BACKEND_FAILURE,
        }[self]


@dataclass(frozen=True, slots=True)
class NormalizedEvent:
    sequence: int
    kind: EventKind
    name: str
    content: JsonValue = None
    data: JsonObject = field(default_factory=dict)
    started_at: str | float | None = None
    ended_at: str | float | None = None


@dataclass(frozen=True, slots=True)
class BundleExecution:
    status: BundleExecutionStatus
    started_at: str | float | None = None
    ended_at: str | float | None = None
    runtime_seconds: float | None = None
    estimated_cost: float | None = None
    attempts: tuple[JsonObject, ...] = ()
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class NormalizedTraceBundle:
    case_id: str
    case_revision: str
    release_id: str
    trial_id: str
    session_id: str
    scenario: JsonObject
    events: tuple[NormalizedEvent, ...]
    artifact_refs: tuple[str, ...]
    state_before_ref: JsonValue
    state_after_ref: JsonValue
    reset_state_ref: JsonValue
    environment_draw_id: str
    reset_policy: ResetPolicy
    execution: BundleExecution
    provenance: JsonObject
    source_path: str | None = None
    source_line: int | None = None

    @property
    def trace_id(self) -> str:
        return f"{self.release_id}:{self.case_id}:{self.trial_id}"

    @property
    def initial_state_hash(self) -> str | None:
        explicit = _nested_string(self.provenance, "initial_state_hash")
        if explicit:
            return explicit
        return _optional_digest(self.state_before_ref)

    @property
    def final_state_hash(self) -> str | None:
        explicit = _nested_string(self.provenance, "final_state_hash")
        if explicit:
            return explicit
        return _optional_digest(self.state_after_ref)

    @property
    def reset_state_hash(self) -> str | None:
        explicit = _nested_string(self.provenance, "reset_state_hash")
        if explicit:
            return explicit
        return _optional_digest(self.reset_state_ref)

    @property
    def content_hash(self) -> str:
        return digest_value(self.to_dict())

    def to_dict(self) -> JsonObject:
        return {
            "case_id": self.case_id,
            "case_revision": self.case_revision,
            "release_id": self.release_id,
            "trial_id": self.trial_id,
            "session_id": self.session_id,
            "scenario": self.scenario,
            "events": [
                {
                    "sequence": event.sequence,
                    "kind": event.kind.value,
                    "name": event.name,
                    "content": event.content,
                    "data": event.data,
                    "started_at": event.started_at,
                    "ended_at": event.ended_at,
                }
                for event in self.events
            ],
            "artifact_refs": list(self.artifact_refs),
            "state_before_ref": self.state_before_ref,
            "state_after_ref": self.state_after_ref,
            "reset_state_ref": self.reset_state_ref,
            "environment_draw_id": self.environment_draw_id,
            "reset_policy": self.reset_policy.value,
            "execution": {
                "status": self.execution.status.value,
                "started_at": self.execution.started_at,
                "ended_at": self.execution.ended_at,
                "runtime_seconds": self.execution.runtime_seconds,
                "estimated_cost": self.execution.estimated_cost,
                "attempts": list(self.execution.attempts),
                "reason": self.execution.reason,
            },
            "provenance": self.provenance,
        }


def parse_trace_bundle(
    value: Any,
    *,
    source_path: str | None = None,
    source_line: int | None = None,
    default_reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT,
) -> NormalizedTraceBundle:
    payload = _object(value, "trace bundle")
    scenario = _object(payload.get("scenario", {}), "scenario")
    provenance = _object(payload.get("provenance", {}), "provenance")
    execution_payload = _object(payload.get("execution"), "execution")
    events_payload = payload.get("events")
    if not isinstance(events_payload, list):
        raise TraceBundleError("events must be a list")
    events = tuple(
        _parse_event(item, index) for index, item in enumerate(events_payload)
    )
    sequences = [event.sequence for event in events]
    if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
        raise TraceBundleError("event sequence values must be unique and ordered")

    environment = _object(payload.get("environment", {}), "environment")
    reset_policy_value = (
        payload.get("reset_policy")
        or environment.get("reset_policy")
        or provenance.get("reset_policy")
        or scenario.get("reset_policy")
        or default_reset_policy.value
    )
    try:
        reset_policy = ResetPolicy(str(reset_policy_value).upper())
    except ValueError as error:
        raise TraceBundleError(f"unknown reset_policy: {reset_policy_value}") from error

    execution = _parse_execution(execution_payload)
    artifacts = payload.get("artifact_refs", [])
    if not isinstance(artifacts, list) or not all(
        isinstance(item, str) for item in artifacts
    ):
        raise TraceBundleError("artifact_refs must be a list of strings")
    bundle = NormalizedTraceBundle(
        case_id=_required_text(payload, "case_id"),
        case_revision=str(payload.get("case_revision") or ""),
        release_id=_required_text(payload, "release_id"),
        trial_id=_required_text(payload, "trial_id"),
        session_id=_required_text(payload, "session_id"),
        scenario=scenario,
        events=events,
        artifact_refs=tuple(artifacts),
        state_before_ref=payload.get("state_before_ref"),
        state_after_ref=payload.get("state_after_ref"),
        reset_state_ref=(
            payload.get("reset_state_ref")
            if "reset_state_ref" in payload
            else environment.get("reset_state_ref")
        ),
        environment_draw_id=str(
            payload.get("environment_draw_id")
            or environment.get("draw_id")
            or scenario.get("environment_draw_id")
            or "default"
        ),
        reset_policy=reset_policy,
        execution=execution,
        provenance=provenance,
        source_path=source_path,
        source_line=source_line,
    )
    if not bundle.case_revision:
        raise TraceBundleError("case_revision is required")
    if bundle.initial_state_hash is None:
        raise TraceBundleError(
            "state_before_ref or provenance.initial_state_hash is required"
        )
    if (
        bundle.reset_policy is ResetPolicy.REQUIRED_EQUIVALENT
        and bundle.reset_state_hash is None
    ):
        raise TraceBundleError(
            "reset_state_ref is required when reset_policy is REQUIRED_EQUIVALENT"
        )
    return bundle


def load_trace_bundles(
    path: Path,
    *,
    default_reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT,
) -> tuple[NormalizedTraceBundle, ...]:
    bundles: list[NormalizedTraceBundle] = []
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                bundles.append(
                    parse_trace_bundle(
                        payload,
                        source_path=str(path),
                        source_line=line_number,
                        default_reset_policy=default_reset_policy,
                    )
                )
            except (json.JSONDecodeError, TraceBundleError) as error:
                raise TraceBundleError(f"{path}:{line_number}: {error}") from error
    if not bundles:
        raise TraceBundleError(f"{path}: no trace bundles found")
    identities = [
        (item.case_id, item.case_revision, item.trial_id, item.environment_draw_id)
        for item in bundles
    ]
    if len(identities) != len(set(identities)):
        raise TraceBundleError(
            f"{path}: duplicate case/revision/trial/environment identity"
        )
    return tuple(bundles)


def load_trace_bundles_with_gaps(
    path: Path,
    *,
    default_reset_policy: ResetPolicy = ResetPolicy.REQUIRED_EQUIVALENT,
) -> tuple[tuple[NormalizedTraceBundle, ...], tuple[ExecutionGap, ...]]:
    bundles: list[NormalizedTraceBundle] = []
    gaps: list[ExecutionGap] = []
    seen: set[tuple[str, str, str, str]] = set()
    with path.open() as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            case_id: str | None = None
            trial_id: str | None = None
            try:
                payload = json.loads(line)
                if isinstance(payload, dict):
                    case_id = _optional_identifier(payload.get("case_id"))
                    trial_id = _optional_identifier(payload.get("trial_id"))
                bundle = parse_trace_bundle(
                    payload,
                    source_path=str(path),
                    source_line=line_number,
                    default_reset_policy=default_reset_policy,
                )
                identity = (
                    bundle.case_id,
                    bundle.case_revision,
                    bundle.trial_id,
                    bundle.environment_draw_id,
                )
                if identity in seen:
                    raise TraceBundleError(f"duplicate identity: {identity}")
                seen.add(identity)
                bundles.append(bundle)
            except (json.JSONDecodeError, TraceBundleError) as error:
                gaps.append(
                    ExecutionGap(
                        kind=ExecutionGapKind.MALFORMED_TRACE,
                        reason=f"{path}:{line_number}: {error}",
                        case_id=case_id,
                        trial_id=trial_id,
                    )
                )
    if not bundles:
        raise TraceBundleError(f"{path}: no valid trace bundles found")
    return tuple(bundles), tuple(gaps)


def _parse_event(value: Any, fallback_sequence: int) -> NormalizedEvent:
    payload = _object(value, "event")
    raw_kind = (
        payload.get("kind")
        or payload.get("actor")
        or payload.get("role")
        or payload.get("type")
    )
    if not isinstance(raw_kind, str):
        raise TraceBundleError("event kind/actor/role is required")
    aliases = {
        "assistant": EventKind.AGENT,
        "agent": EventKind.AGENT,
        "ai": EventKind.AGENT,
        "human": EventKind.USER,
        "user": EventKind.USER,
        "tool": EventKind.TOOL,
        "tool_call": EventKind.TOOL,
        "tool_result": EventKind.TOOL,
        "workflow": EventKind.WORKFLOW,
        "node": EventKind.WORKFLOW,
        "system": EventKind.SYSTEM,
        "harness": EventKind.SYSTEM,
        "artifact": EventKind.ARTIFACT,
        "state": EventKind.STATE,
    }
    kind = aliases.get(raw_kind.lower())
    if kind is None:
        try:
            kind = EventKind(raw_kind.upper())
        except ValueError as error:
            raise TraceBundleError(f"unknown event kind: {raw_kind}") from error
    sequence = payload.get("sequence", payload.get("index", fallback_sequence))
    if not isinstance(sequence, int) or sequence < 0:
        raise TraceBundleError("event sequence must be a non-negative integer")
    data_value = payload.get("data", payload.get("metadata", {}))
    data = _object(data_value, "event data")
    for key in ("arguments", "status", "error", "result_ref", "mutating"):
        if key in payload and key not in data:
            data[key] = payload[key]
    return NormalizedEvent(
        sequence=sequence,
        kind=kind,
        name=str(payload.get("name") or payload.get("tool_name") or kind.value.lower()),
        content=payload.get("content", payload.get("message", payload.get("output"))),
        data=data,
        started_at=payload.get("started_at", payload.get("timestamp")),
        ended_at=payload.get("ended_at"),
    )


def _parse_execution(payload: JsonObject) -> BundleExecution:
    raw_status = _required_text(payload, "status").upper()
    aliases = {
        "OK": "COMPLETED",
        "SUCCESS": "COMPLETED",
        "BUDGET_ERROR": "BUDGET_EXHAUSTED",
        "TOOL_ERROR": "TOOL_BACKEND_ERROR",
    }
    try:
        status = BundleExecutionStatus(aliases.get(raw_status, raw_status))
    except ValueError as error:
        raise TraceBundleError(f"unknown execution status: {raw_status}") from error
    attempts = payload.get("attempts", [])
    if not isinstance(attempts, list) or not all(
        isinstance(item, dict) for item in attempts
    ):
        raise TraceBundleError("execution.attempts must be a list of objects")
    return BundleExecution(
        status=status,
        started_at=payload.get("started_at"),
        ended_at=payload.get("ended_at"),
        runtime_seconds=_optional_number(payload.get("runtime_seconds")),
        estimated_cost=_optional_number(payload.get("estimated_cost")),
        attempts=tuple(attempts),
        reason=str(payload["reason"]) if payload.get("reason") is not None else None,
    )


def _required_text(payload: JsonObject, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise TraceBundleError(f"{key} is required and must be non-empty text")
    return value.strip()


def _object(value: Any, label: str) -> JsonObject:
    if not isinstance(value, dict):
        raise TraceBundleError(f"{label} must be an object")
    return value


def _optional_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TraceBundleError("runtime/cost values must be numeric")
    return float(value)


def _optional_digest(value: JsonValue) -> str | None:
    return None if value is None else digest_value(value)


def _nested_string(payload: JsonObject, key: str) -> str | None:
    value = payload.get(key)
    return value if isinstance(value, str) and value else None


def _optional_identifier(value: Any) -> str | None:
    if isinstance(value, (str, int)) and str(value):
        return str(value)
    return None


__all__ = [
    "BundleExecution",
    "BundleExecutionStatus",
    "EventKind",
    "NormalizedEvent",
    "NormalizedTraceBundle",
    "TraceBundleError",
    "load_trace_bundles",
    "load_trace_bundles_with_gaps",
    "parse_trace_bundle",
]
