from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)
type JsonObject = Mapping[str, Any]


@dataclass(frozen=True)
class VerifiedCaseProjection:
    case: JsonObject
    persona: JsonObject
    intent: JsonObject
    turn_policy: JsonObject


@dataclass(frozen=True)
class VerifiedCaseFactoryInput:
    manifest_file_hash: str
    case_candidate_file_hash: str
    input_manifest_hash: str
    intelligence_manifest_hash: str
    cases: tuple[VerifiedCaseProjection, ...]


@dataclass(frozen=True)
class TargetSourceIdentity:
    source_commit: str
    source_tree_hash: str
    adapter_file_hash: str


@dataclass(frozen=True)
class SimulatorResponse:
    status: str
    request_bytes: bytes | None
    response_bytes: bytes | None
    next_user_content: str | None
    consumed_observation_hash: str | None
    proposed_stop: bool | None
    stop_reason: str | None
    input_tokens: int
    output_tokens: int
    provider_http_exchange_count: int
    provider_reported_cost_usd: str | None
    reason_code: str | None


@dataclass(frozen=True)
class TargetLaunch:
    episode_id: str
    case_id: str
    target_config: JsonObject
    world: JsonObject
    world_hash: str
    source_identity: TargetSourceIdentity
    environment: Mapping[str, str]


@dataclass(frozen=True)
class AdaptiveRunResult:
    outcome: str
    reason_code: str | None
    exit_code: int
    manifest_path: Path
    attempted_episode_count: int
    valid_episode_count: int
    effective_trajectory_count: int
    simulator_http_exchange_count: int
    target_http_exchange_count: int
    all_http_exchange_count: int
    reserved_cost_usd: str
    actual_cost_usd: str | None


class CaseFactoryInputLoader(Protocol):
    def load(self, manifest: Path) -> VerifiedCaseFactoryInput: ...


class TargetSourceVerifier(Protocol):
    def verify(self, target_config: JsonObject) -> TargetSourceIdentity: ...


class SimulatorTransport(Protocol):
    def complete(self, request: JsonObject) -> SimulatorResponse: ...


class TargetSession(Protocol):
    def exchange(self, request: JsonObject) -> JsonObject: ...

    def terminate(self) -> None: ...


class TargetProcessFactory(Protocol):
    def start(self, launch: TargetLaunch) -> TargetSession: ...


class Clock(Protocol):
    def monotonic_ns(self) -> int: ...


class ArtifactPublisher(Protocol):
    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None: ...


class TargetProtocolFailure(Exception):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class AdaptiveRunFailure(Exception):
    def __init__(self, reason_code: str, exit_code: int) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.exit_code = exit_code
