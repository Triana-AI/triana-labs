"""Independent deterministic oracles for LABS-05 adaptive-runner acceptance."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = REPOSITORY_ROOT / "triana-labs"
FIXTURE_ROOT = PROJECT_ROOT / "tests" / "adaptive_runner_fixtures"
FAKE_TARGET = FIXTURE_ROOT / "fake_hrai_jsonl.py"
WIRE = "LABS05_WIRE_V1"
MANIFEST_FILE_HASH = (
    "sha256:817000637daef25bff9bd95eee46a25976f575d1b2d5aa62965a6c6d9c5b6cb9"
)
CASE_FILE_HASH = (
    "sha256:06a3a2267f39041d98e08ef24466ffbc695e7833ebb16bd536f19f71c37ecbe4"
)
INPUT_HASH = "sha256:" + "1" * 64
INTELLIGENCE_HASH = "sha256:" + "2" * 64
SELECTED_CASE_IDS = (
    "case-b2b9570f6e763ca0",
    "case-62ca79446e3a22d5",
    "case-9a0d8a895afcd860",
)
ALL_CASE_IDS = tuple(
    sorted(
        (
            "case-0ae2cc98bc28d898",
            "case-1bf9692ff5fa600f",
            *SELECTED_CASE_IDS,
        )
    )
)
OUTPUT_NAMES = {
    "manifest.json",
    "episode_attempts.jsonl",
    "transcripts.jsonl",
    "target_tool_events.jsonl",
    "provider_ledger.jsonl",
    "gaps.jsonl",
    "trajectory_clusters.json",
    "human_adaptation_review.json",
}
ENVIRON = {"AWS_PROFILE": "synthetic-test", "AWS_REGION": "us-east-1"}


def canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def sha256(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def jsonl(payload: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in payload.splitlines()]


def api() -> Any:
    spec = importlib.util.find_spec("triana_labs.adaptive_runner")
    assert spec is not None, "LABS-05 adaptive_runner package is absent"
    return importlib.import_module("triana_labs.adaptive_runner")


def _observed(text: str) -> dict[str, Any]:
    return {"basis": "OBSERVED", "claim_ids": ["claim-synthetic"], "text": text}


def _generated(text: str) -> dict[str, Any]:
    return {"basis": "GENERATED_VARIATION", "claim_ids": [], "text": text}


def _common() -> dict[str, Any]:
    return {
        "fidelity": "SYNTHETIC_CORPUS_GROUNDED",
        "grounding_claims": [
            {
                "citation_ids": ["citation-synthetic"],
                "claim": "Synthetic accepted behavior anchor.",
                "claim_id": "claim-synthetic",
                "support_state": "SINGLE_OBSERVATION",
            }
        ],
        "input_manifest_hash": INPUT_HASH,
        "intelligence_manifest_hash": INTELLIGENCE_HASH,
        "lineage": {
            "attempt_ids": ["attempt-synthetic"],
            "deployment": "FW-GLM-5.2",
            "endpoint_host_hash": "sha256:" + "3" * 64,
            "model_name": "FW-GLM-5.2",
            "model_version": "1",
            "prompt_pack_hash": "sha256:" + "4" * 64,
            "provider_evidence_hash": "sha256:" + "5" * 64,
            "provider_kind": "MICROSOFT_FOUNDRY_FIREWORKS",
            "seed": 2026080104,
            "stage": "REVISE",
        },
        "proposal_state": "PROPOSED",
        "schema_version": 1,
    }


def projections(
    module: Any, *, order: tuple[str, ...] = SELECTED_CASE_IDS
) -> tuple[Any, ...]:
    result = []
    for index, case_id in enumerate(order, start=1):
        suffix = str(index)
        persona_id = f"persona-synthetic-{suffix}"
        intent_id = f"intent-synthetic-{suffix}"
        policy_id = f"turn-policy-synthetic-{suffix}"
        common = _common()
        persona = {
            **deepcopy(common),
            "artifact_kind": "persona_proposal",
            "behavioral_traits": [_observed("Checks bounded context.")],
            "communication_tendencies": [],
            "constraints": [],
            "label": f"Synthetic persona {suffix}",
            "persona_id": persona_id,
        }
        intent = {
            **deepcopy(common),
            "artifact_kind": "intent_proposal",
            "goal": _observed("Resolve the bounded recruiting request."),
            "intent_id": intent_id,
            "known_constraints": [],
            "observed_failure_or_abandonment_signals": [],
            "observed_success_signals": [],
        }
        policy = {
            **deepcopy(common),
            "artifact_kind": "turn_policy_proposal",
            "clarification_behavior": [_generated("Ask one bounded clarification.")],
            "escalation_tendencies": [],
            "forbidden_inventions": [_generated("Do not invent private records.")],
            "information_reveal_policy": [],
            "reaction_rules": [_observed("React to the latest target response.")],
            "stop_conditions": [_generated("Stop after bounded resolution.")],
            "turn_policy_id": policy_id,
        }
        case = {
            **deepcopy(common),
            "artifact_kind": "simulation_case_candidate",
            "case_id": case_id,
            "gaps": [],
            "intent_id": intent_id,
            "novelty": {
                "duplicate_cluster_id": None,
                "exact_duplicate_of": None,
                "slot_key": "sha256:" + f"{index:x}" * 64,
            },
            "persona_id": persona_id,
            "proposed_evaluation": {
                "abstain_conditions": [_generated("Evidence is unavailable.")],
                "criteria": [_generated("Agent follows the bounded policy.")],
            },
            "scenario": {
                "allowed_user_actions": [_generated("May clarify the request.")],
                "expected_tool_names": ["query_database"],
                "known_facts": [_observed(f"Synthetic case fact {suffix}.")],
                "opening_user_turn": _observed(
                    "Synthetic accepted opening for bounded recruiting context."
                ),
                "private_user_facts": [],
                "stressor_codes": [f"SYNTHETIC_{suffix}"],
                "termination_conditions": [_generated("Bounded request resolved.")],
                "tool_world_constraints": [_generated("Read-only synthetic world.")],
                "unknowns": [],
            },
            "turn_policy_id": policy_id,
        }
        result.append(module.VerifiedCaseProjection(case, persona, intent, policy))
    return tuple(result)


class FixtureLoader:
    def __init__(
        self, module: Any, *, order: tuple[str, ...] = SELECTED_CASE_IDS
    ) -> None:
        self.module = module
        self.order = order
        self.calls: list[Path] = []

    def load(self, manifest: Path) -> Any:
        self.calls.append(manifest)
        return self.module.VerifiedCaseFactoryInput(
            MANIFEST_FILE_HASH,
            CASE_FILE_HASH,
            INPUT_HASH,
            INTELLIGENCE_HASH,
            projections(self.module, order=self.order),
        )


class SourceVerifier:
    def __init__(self, module: Any, *, fail: bool = False) -> None:
        self.module = module
        self.fail = fail
        self.calls: list[Mapping[str, Any]] = []

    def verify(self, target_config: Mapping[str, Any]) -> Any:
        self.calls.append(target_config)
        if self.fail:
            raise self.module.AdaptiveRunFailure("TARGET_SOURCE_MISMATCH", 4)
        return self.module.TargetSourceIdentity(
            "728f6c5058efe40a16e2aecc9b528b3353f4df4f",
            "sha256:" + "6" * 64,
            "sha256:" + "7" * 64,
        )


class Clock:
    def __init__(self, values: list[int] | None = None) -> None:
        self.values = iter(values or range(0, 10_000_000_000, 1_000_000))

    def monotonic_ns(self) -> int:
        return next(self.values)


class Simulator:
    def __init__(
        self,
        module: Any,
        *,
        mode: str = "adaptive",
        token_scale: int = 1,
    ) -> None:
        self.module = module
        self.mode = mode
        self.token_scale = token_scale
        self.requests: list[Mapping[str, Any]] = []

    def complete(self, request: Mapping[str, Any]) -> Any:
        self.requests.append(deepcopy(request))
        latest = request["latest_observation"]
        observed = str(latest["assistant_content"])
        digest = hashlib.sha256(observed.encode()).hexdigest()[:12]
        next_turn = "same simulated follow-up"
        if self.mode == "adaptive":
            next_turn = f"follow-up reacting to {digest}"
        consumed = str(latest["observation_hash"])
        if self.mode == "binding_mismatch":
            consumed = "sha256:" + "f" * 64
        response = {
            "consumed_observation_hash": consumed,
            "next_user_content": next_turn,
            "proposed_stop": False,
            "stop_reason": None,
        }
        if self.mode == "invalid_response":
            return self.module.SimulatorResponse(
                "INVALID",
                canonical(request),
                b'{"next_user_content":null}',
                None,
                None,
                None,
                None,
                1,
                0,
                1,
                None,
                "SIMULATOR_INVALID_RESPONSE",
            )
        return self.module.SimulatorResponse(
            "SUCCEEDED",
            canonical(request),
            canonical(response),
            next_turn,
            consumed,
            False,
            None,
            11 * self.token_scale,
            7 * self.token_scale,
            1,
            None,
            None,
        )


class Session:
    def __init__(
        self,
        launch: Any,
        *,
        mode: str,
        assistant_variant: str,
        include_case_id: bool,
        response_mutator: Callable[[Mapping[str, Any], dict[str, Any]], None] | None,
    ) -> None:
        self.launch = launch
        self.mode = mode
        self.assistant_variant = assistant_variant
        self.include_case_id = include_case_id
        self.response_mutator = response_mutator
        self.exchanges: list[Mapping[str, Any]] = []
        self.terminate_count = 0
        self.http_count = 0

    def exchange(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        self.exchanges.append(deepcopy(request))
        if self.mode == "timeout" and request["kind"] == "turn":
            raise TimeoutError("PRIVATE timeout detail")
        if self.mode == "oserror" and request["kind"] == "turn":
            raise OSError("PRIVATE process detail")
        if self.mode == "interrupt" and request["kind"] == "turn":
            raise KeyboardInterrupt
        if request["kind"] == "hello":
            response = {
                "agent_model": request["agent_model"],
                "case_id": request["case_id"],
                "episode_id": request["episode_id"],
                "fallback_enabled": False,
                "kind": "ready",
                "memory_state": "EMPTY",
                "prompt_version": request["prompt_version"],
                "protocol": request["protocol"],
                "source_commit": request["source_commit"],
                "world_hash": request["world_hash"],
            }
            if self.mode == "unknown_field":
                response["unexpected"] = "private"
            if self.mode == "identity_mismatch":
                response["case_id"] = "case-wrong"
            if self.response_mutator is not None:
                self.response_mutator(request, response)
            return response
        if request["kind"] == "turn":
            self.http_count += 1
            turn_index = int(request["turn_index"])
            status, reason = "SUCCEEDED", None
            case_marker = f" {self.launch.case_id}" if self.include_case_id else ""
            content = (
                f"{self.assistant_variant}{case_marker} answer {turn_index} "
                f"to {request['content']}"
            )
            tool_events: list[dict[str, Any]] = []
            if self.mode == "tool_refused" and turn_index == 1:
                status, reason, content = "TOOL_REFUSED", "TOOL_NOT_ALLOWED", ""
            if self.mode == "provider_failed" and turn_index == 1:
                status, reason, content = "PROVIDER_FAILED", "PROVIDER_ERROR", ""
            if self.mode == "too_many_tools" and turn_index == 1:
                tool_events = [
                    {
                        "arguments": {},
                        "cached": False,
                        "name": "query_database",
                        "ordinal": ordinal,
                        "reason_code": None,
                        "result": {"row": ordinal},
                        "status": "SUCCEEDED",
                        "tool_event_id": f"tool-event-{ordinal}",
                    }
                    for ordinal in range(1, 14)
                ]
            http_count = 1
            input_tokens = 10
            if self.mode == "http_overrun" and turn_index == 1:
                http_count = 5
            if self.mode == "token_overrun" and turn_index == 1:
                input_tokens = 393_217
            response = {
                "assistant_content": content,
                "episode_id": request["episode_id"],
                "kind": "turn_result",
                "reason_code": reason,
                "status": status,
                "tool_events": tool_events,
                "turn_index": turn_index,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": 5,
                    "provider_http_exchange_count": http_count,
                    "provider_reported_cost_usd": None,
                },
            }
            if self.response_mutator is not None:
                self.response_mutator(request, response)
            return response
        response = {
            "episode_id": request["episode_id"],
            "kind": "closed",
            "last_turn_index": request["last_turn_index"],
            "memory_state": "DISCARDED",
            "provider_http_exchange_count": self.http_count,
            "tool_call_count": 13 if self.mode == "too_many_tools" else 0,
        }
        if self.response_mutator is not None:
            self.response_mutator(request, response)
        return response

    def terminate(self) -> None:
        self.terminate_count += 1


class TargetFactory:
    def __init__(
        self,
        *,
        modes: tuple[str, ...] = ("success", "success", "success"),
        assistant_variant: str = "bounded",
        include_case_id: bool = True,
        response_mutator: Callable[[Mapping[str, Any], dict[str, Any]], None]
        | None = None,
    ) -> None:
        self.modes = modes
        self.assistant_variant = assistant_variant
        self.include_case_id = include_case_id
        self.response_mutator = response_mutator
        self.launches: list[Any] = []
        self.sessions: list[Session] = []

    def start(self, launch: Any) -> Session:
        index = len(self.launches)
        self.launches.append(launch)
        session = Session(
            launch,
            mode=self.modes[index],
            assistant_variant=self.assistant_variant,
            include_case_id=self.include_case_id,
            response_mutator=self.response_mutator,
        )
        self.sessions.append(session)
        return session


class CapturePublisher:
    def __init__(self, *, failure: BaseException | None = None) -> None:
        self.failure = failure
        self.calls: list[tuple[Path, dict[str, bytes]]] = []

    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None:
        self.calls.append((output_path, dict(artifacts)))
        if self.failure is not None:
            raise self.failure

    @property
    def artifacts(self) -> dict[str, bytes]:
        assert len(self.calls) == 1
        return self.calls[0][1]


def review_value() -> dict[str, Any]:
    return {
        "artifact_kind": "labs04_usefulness_ruling",
        "case_candidate_file_hash": CASE_FILE_HASH,
        "case_factory_manifest_file_hash": MANIFEST_FILE_HASH,
        "cases": [
            {
                "adaptive_multi_turn": True,
                "case_id": case_id,
                "depends_on_hidden_or_fabricated_fact": False,
                "judgeable_expected_behavior": True,
                "materially_distinct": True,
                "opening_understandable": True,
                "support_sufficient": True,
                "would_run": True,
            }
            for case_id in ALL_CASE_IDS
        ],
        "review_date": "2026-08-02",
        "review_state": "PASSED",
        "reviewer": "Akarsh",
        "rubric_version": "LABS04_USEFULNESS_V1",
        "schema_version": 1,
    }


def config_value(*, target_mode: str = "success") -> dict[str, Any]:
    return {
        "artifact_kind": "adaptive_runner_config",
        "budget": {
            "all_http_exchanges": 42,
            "episode_count": 3,
            "episode_timeout_seconds": 180,
            "max_usd": "23.000000",
            "role_turns_per_episode": 6,
            "run_timeout_seconds": 600,
            "simulator_http_exchanges": 6,
            "simulator_input_tokens_per_exchange": 131072,
            "simulator_output_tokens_per_exchange": 4096,
            "simulator_reservation_usd_per_exchange": "1.000000",
            "target_http_exchanges": 36,
            "target_http_exchanges_per_turn": 4,
            "target_input_tokens_per_episode": 393216,
            "target_output_tokens_per_episode": 24576,
            "target_reservation_usd_per_turn": "1.888888",
            "target_tool_calls_per_episode": 12,
        },
        "privacy_class": "SYNTHETIC",
        "protocol_version": WIRE,
        "schema_version": 1,
        "selected_case_ids": list(SELECTED_CASE_IDS),
        "simulator": {
            "allowed_host": "synthetic.example",
            "api_key_env": "LABS05_FAKE_API_KEY",
            "deployment": "FW-GLM-5.2",
            "endpoint": "https://synthetic.example/openai/v1",
            "model_name": "FW-GLM-5.2",
            "model_version": "1",
            "prompt_version": "LABS05_ADAPTIVE_USER_V1",
            "provider_kind": "MICROSOFT_FOUNDRY_FIREWORKS",
            "seed": 2026080205,
            "timeout_seconds": 180,
        },
        "target": {
            "agent_model": "qwen.qwen3-235b-a22b-2507-v1:0",
            "argv": [sys.executable, str(FAKE_TARGET), target_mode],
            "cwd": str(PROJECT_ROOT),
            "env_names": ["AWS_PROFILE", "AWS_REGION"],
            "fallback_model": None,
            "prompt_version": "candidate-screening-v3-decision-followthrough",
            "protocol": "HRAI_RECRUITER_CHAT_REACT_JSONL_V1",
            "source_commit": "728f6c5058efe40a16e2aecc9b528b3353f4df4f",
            "timeout_seconds": 180,
        },
        "world": {
            "allowed_tools": [
                "get_candidate_by_email",
                "get_existing_evaluation",
                "get_hiring_rubric",
                "query_database",
            ],
            "kind": "HRAI_SYNTHETIC_READ_ONLY_V1",
            "persistent_memory": "DISABLED",
            "reset_policy": "FRESH_PER_EPISODE",
        },
    }


@dataclass(frozen=True)
class Inputs:
    manifest: Path
    review: Path
    config: Path
    output: Path


def write_inputs(
    tmp_path: Path,
    *,
    review: Mapping[str, Any] | None = None,
    config: Mapping[str, Any] | None = None,
) -> Inputs:
    tmp_path.mkdir(parents=True, exist_ok=True)
    manifest = tmp_path / "manifest.json"
    owner_review = tmp_path / "review.json"
    runner_config = tmp_path / "config.json"
    manifest.write_bytes(canonical({"fixture": "external-reader-boundary"}, lf=True))
    owner_review.write_bytes(canonical(review or review_value(), lf=True))
    runner_config.write_bytes(canonical(config or config_value(), lf=True))
    return Inputs(manifest, owner_review, runner_config, tmp_path / "output")


@dataclass(frozen=True)
class Invocation:
    result: Any
    module: Any
    simulator: Simulator
    target: Any
    publisher: CapturePublisher
    loader: FixtureLoader
    verifier: SourceVerifier
    inputs: Inputs


def invoke(
    tmp_path: Path,
    *,
    simulator_mode: str = "adaptive",
    simulator_token_scale: int = 1,
    target_modes: tuple[str, ...] = ("success", "success", "success"),
    assistant_variant: str = "bounded",
    include_case_id: bool = True,
    response_mutator: Callable[[Mapping[str, Any], dict[str, Any]], None] | None = None,
    config: Mapping[str, Any] | None = None,
    target: Any = None,
    publisher: CapturePublisher | None = None,
    loader_order: tuple[str, ...] = SELECTED_CASE_IDS,
    clock: Clock | None = None,
) -> Invocation:
    module = api()
    inputs = write_inputs(tmp_path, config=config)
    simulator = Simulator(
        module, mode=simulator_mode, token_scale=simulator_token_scale
    )
    active_target = target or TargetFactory(
        modes=target_modes,
        assistant_variant=assistant_variant,
        include_case_id=include_case_id,
        response_mutator=response_mutator,
    )
    active_publisher = publisher or CapturePublisher()
    loader = FixtureLoader(module, order=loader_order)
    verifier = SourceVerifier(module)
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator=simulator,
        target_factory=active_target,
        clock=clock or Clock(),
        environ={**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"},
        publisher=active_publisher,
        source_verifier=verifier,
        case_loader=loader,
    )
    return Invocation(
        result,
        module,
        simulator,
        active_target,
        active_publisher,
        loader,
        verifier,
        inputs,
    )


def run_cli(*args: str | Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-m", "triana_labs", *(os.fspath(item) for item in args)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )
