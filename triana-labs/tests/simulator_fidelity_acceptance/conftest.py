"""Independent LABS-06 black-box fixtures and deterministic oracles."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_HARNESS = PROJECT_ROOT / "tests" / "adaptive_runner_acceptance" / "conftest.py"
PROTOCOL = "LABS06_SIMULATOR_FIDELITY_V1"
CRITICAL_CODES = {
    "EXACT_ASSISTANT_ECHO",
    "FIXED_FACT_CONFLICT",
    "HIDDEN_FACT_LEAK",
    "NEAR_ASSISTANT_ECHO",
    "ROLE_INVERSION",
    "UNAUTHORIZED_ACTION",
}


def canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    return payload + (b"\n" if lf else b"")


def digest(value: Any) -> str:
    payload = value if isinstance(value, bytes) else canonical(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def identity(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(canonical(value)).hexdigest()[:16]}"


def jsonl(payload: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in payload.splitlines()]


@pytest.fixture(scope="session")
def legacy() -> Any:
    spec = importlib.util.spec_from_file_location(
        "labs05_acceptance_harness", LEGACY_HARNESS
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def initial_state(*, disclosure: str = "disclosure-account") -> dict[str, Any]:
    return {
        "confusion_level": "MEDIUM",
        "goal_state": "OPEN",
        "patience_level": "HIGH",
        "remaining_disclosure_ids": [disclosure],
        "trust_level": "MEDIUM",
        "urgency_level": "LOW",
    }


def next_state(*, disclosure: bool = True) -> dict[str, Any]:
    return {
        "confusion_level": "LOW",
        "goal_state": "OPEN",
        "patience_level": "MEDIUM",
        "remaining_disclosure_ids": ["disclosure-account"] if disclosure else [],
        "trust_level": "HIGH",
        "urgency_level": "LOW",
    }


def _source(projection: Any) -> dict[str, Any]:
    return {
        "case_hash": digest(projection.case),
        "case_id": projection.case["case_id"],
        "intent_hash": digest(projection.intent),
        "intent_id": projection.intent["intent_id"],
        "persona_hash": digest(projection.persona),
        "persona_id": projection.persona["persona_id"],
        "turn_policy_hash": digest(projection.turn_policy),
        "turn_policy_id": projection.turn_policy["turn_policy_id"],
    }


def context_for(projection: Any, ordinal: int) -> dict[str, Any]:
    body = {
        "action_registry": [
            {
                "action_id": "action-clarify",
                "literal_matchers": ["please clarify the requested synthetic record"],
            },
            {
                "action_id": "action-correct",
                "literal_matchers": ["the request is still open"],
            },
        ],
        "assistant_only_literal_matchers": [
            "i have updated your account",
            "i completed the database operation",
        ],
        "context_version": 1,
        "fixed_fact_conflict_literal_matchers": [
            "the synthetic request is already cancelled"
        ],
        "hidden_facts": [
            {
                "fact_id": "hidden-locker",
                "literal_matchers": ["violet locker 73"],
                "value": "violet locker 73",
                "visibility": "HIDDEN",
            }
        ],
        "initial_interaction_state": initial_state(),
        "intent": deepcopy(projection.intent),
        "known_facts": deepcopy(projection.case["scenario"]["known_facts"]),
        "persona": deepcopy(projection.persona),
        "reaction_registry": [
            {
                "allowed_action_ids": ["action-clarify", "action-correct"],
                "reaction_id": "reaction-clarify",
                "state_transition": next_state(),
                "stop_reason_codes": [],
            },
            {
                "allowed_action_ids": [],
                "reaction_id": "reaction-stop",
                "state_transition": {
                    **next_state(disclosure=False),
                    "goal_state": "SATISFIED",
                },
                "stop_reason_codes": ["GOAL_SATISFIED"],
            },
        ],
        "source": _source(projection),
        "stop_registry": [
            {
                "reaction_id": "reaction-stop",
                "stop_reason_code": "GOAL_SATISFIED",
            }
        ],
        "user_turn_policy": {
            "allowed_action_ids": ["action-clarify", "action-correct"],
            "allowed_reaction_ids": ["reaction-clarify", "reaction-stop"],
            "owner": "USER",
            "policy_id": f"user-policy-{ordinal}",
        },
    }
    return {**body, "context_id": identity("sim-context", body)}


def observation(content: str, ordinal: int) -> dict[str, Any]:
    core = {
        "assistant_content": content,
        "assistant_turn_id": f"teacher-assistant-{ordinal:02d}",
        "tool_events": [],
    }
    return {**core, "observation_hash": digest(core)}


def panel_item(context: dict[str, Any], ordinal: int, stratum: str) -> dict[str, Any]:
    latest = observation(
        f"Synthetic assistant observation {ordinal}: the request remains open.", ordinal
    )
    body = {
        "allowed_action_ids": ["action-clarify", "action-correct"],
        "allowed_reaction_ids": ["reaction-clarify", "reaction-stop"],
        "allowed_stop_reason_codes": ["GOAL_SATISFIED"],
        "context_id": context["context_id"],
        "interaction_state": initial_state(),
        "latest_observation": latest,
        "remaining_turns": 1,
        "stratum": stratum,
        "transcript": [
            {"content": "Please check the synthetic request.", "role": "USER"},
            {"content": latest["assistant_content"], "role": "ASSISTANT"},
        ],
        "turn_index": 2,
    }
    return {**body, "item_id": identity("fidelity-item", body)}


def bundle_value(legacy: Any) -> dict[str, Any]:
    module = legacy.api()
    projections = legacy.projections(module)
    contexts = [context_for(item, index) for index, item in enumerate(projections, 1)]
    strata = ["ORDINARY"] * 24 + [
        "ANGRY",
        "IMPATIENT",
        "SKEPTICAL",
        "INFORMAL",
        "MISTAKEN",
        "ADVERSARIAL",
    ]
    items = [
        panel_item(contexts[index % 3], index + 1, stratum)
        for index, stratum in enumerate(strata)
    ]
    body = {
        "artifact_kind": "labs06_simulator_context_bundle",
        "panel_identity_hash": digest([item["item_id"] for item in items]),
        "protocol_version": PROTOCOL,
        "schema_version": 1,
        "source_case_set_hash": digest([item.case["case_id"] for item in projections]),
        "source_policy_selection_hash": digest(
            [item.turn_policy["turn_policy_id"] for item in projections]
        ),
        "contexts": contexts,
        "teacher_forced_items": items,
    }
    return {**body, "bundle_hash": digest(body)}


class ContextLoader:
    def __init__(self, module: Any, value: dict[str, Any]) -> None:
        self.module = module
        self.value = deepcopy(value)
        self.calls: list[Path] = []

    def load(self, path: Path) -> Any:
        self.calls.append(path)
        return self.module.SimulatorContextBundle(
            self.value["bundle_hash"],
            tuple(deepcopy(self.value["contexts"])),
            tuple(deepcopy(self.value["teacher_forced_items"])),
        )


class FidelitySimulator:
    def __init__(
        self, module: Any, proposals: list[dict[str, Any]] | None = None
    ) -> None:
        self.module = module
        self.proposals = proposals or []
        self.requests: list[dict[str, Any]] = []

    def _proposal(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.proposals:
            proposal = deepcopy(
                self.proposals[min(len(self.requests) - 1, len(self.proposals) - 1)]
            )
        else:
            proposal = {
                "disposition": "EMIT",
                "stop_reason_code": None,
                "user_utterance": "Please clarify the requested synthetic record.",
            }
        return proposal

    def complete(self, request: dict[str, Any]) -> Any:
        self.requests.append(deepcopy(request))
        proposal = self._proposal(request)
        return self.module.SimulatorResponse(
            status="SUCCEEDED",
            request_bytes=canonical(request),
            response_bytes=canonical(proposal),
            consumed_observation_hash=request["latest_observation"]["observation_hash"],
            speaker_role="USER",
            disposition=proposal.get("disposition"),
            user_utterance=proposal.get("user_utterance"),
            stop_reason_code=proposal.get("stop_reason_code"),
            input_tokens=11,
            output_tokens=7,
            provider_http_exchange_count=1,
            provider_reported_cost_usd=None,
            reason_code=None,
        )


@dataclass(frozen=True)
class Lab06Run:
    result: Any
    module: Any
    simulator: FidelitySimulator
    target: Any
    publisher: Any
    context_loader: ContextLoader
    bundle: dict[str, Any]


def invoke_lab06(
    tmp_path: Path,
    legacy: Any,
    *,
    proposals: list[dict[str, Any]] | None = None,
    bundle_mutator: Any = None,
    assistant_variant: str = "bounded",
    include_case_id: bool = True,
) -> Lab06Run:
    module = legacy.api()
    bundle = bundle_value(legacy)
    if bundle_mutator is not None:
        bundle_mutator(bundle)
    context_loader = ContextLoader(module, bundle)
    inputs = legacy.write_inputs(tmp_path)
    simulator = FidelitySimulator(module, proposals)
    target = legacy.TargetFactory(
        assistant_variant=assistant_variant, include_case_id=include_case_id
    )
    publisher = legacy.CapturePublisher()
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator_context_bundle=tmp_path / "simulator-context.json",
        context_loader=context_loader,
        simulator=simulator,
        target_factory=target,
        clock=legacy.Clock(),
        environ={**legacy.ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"},
        publisher=publisher,
        source_verifier=legacy.SourceVerifier(module),
        case_loader=legacy.FixtureLoader(module),
    )
    return Lab06Run(
        result, module, simulator, target, publisher, context_loader, bundle
    )


def proposal(**updates: Any) -> dict[str, Any]:
    value = {
        "disposition": "EMIT",
        "stop_reason_code": None,
        "user_utterance": "Please clarify the requested synthetic record.",
    }
    value.update(updates)
    return value
