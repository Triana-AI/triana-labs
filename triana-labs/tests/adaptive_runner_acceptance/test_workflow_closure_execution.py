"""Black-box twelve-case workflow execution and tiered result acceptance."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from conftest import (
    ENVIRON,
    INPUT_HASH,
    INTELLIGENCE_HASH,
    CapturePublisher,
    Clock,
    SourceVerifier,
    TargetFactory,
    api,
    canonical,
    config_value,
    invoke,
    jsonl,
    projections,
)

MODE = "LABS046_WORKFLOW_CLOSURE_V1"
MARKDOWN = "LABS06_TIERED_RESULTS.md"


def _hash(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _closure_projections(module: Any) -> tuple[Any, ...]:
    templates = projections(module)
    result = []
    for index in range(12):
        template = templates[index % len(templates)]
        case, persona, intent, policy = map(
            deepcopy,
            (template.case, template.persona, template.intent, template.turn_policy),
        )
        suffix = index + 1
        case_id = f"case-closure-{suffix:02d}"
        persona["persona_id"] = f"persona-closure-{suffix:02d}"
        intent["intent_id"] = f"intent-closure-{suffix:02d}"
        policy["turn_policy_id"] = f"turn-policy-closure-{suffix:02d}"
        case.update(
            case_id=case_id,
            persona_id=persona["persona_id"],
            intent_id=intent["intent_id"],
            turn_policy_id=policy["turn_policy_id"],
            case_origin=(
                "OBSERVED_PRODUCTION_CASE" if index < 6 else "GROUNDED_EXPANDED_CASE"
            ),
            goal={
                "text": f"Complete synthetic workflow {suffix}",
                "basis": "OBSERVED",
                "claim_ids": [f"claim-goal-{suffix:02d}"],
            },
            done_when={
                "text": f"Synthetic workflow {suffix} is confirmed complete",
                "basis": "OBSERVED",
                "claim_ids": [f"claim-done-{suffix:02d}"],
            },
            source_trace_ids=(
                [f"trace-{suffix:02d}"]
                if index < 6
                else [f"trace-{suffix:02d}-a", f"trace-{suffix:02d}-b"]
            ),
            required_world_keys={"candidate_id": [f"cand-{suffix:02d}"]},
            workflow_stratum="ORDINARY" if index < 9 else "RECOVERY",
        )
        result.append(module.VerifiedCaseProjection(case, persona, intent, policy))
    return tuple(result)


class ClosureLoader:
    def __init__(self, module: Any, cases: tuple[Any, ...]) -> None:
        self.module = module
        self.cases = cases

    def load(self, manifest: Path) -> Any:
        del manifest
        return self.module.VerifiedCaseFactoryInput(
            "sha256:" + "a" * 64,
            "sha256:" + "b" * 64,
            INPUT_HASH,
            INTELLIGENCE_HASH,
            self.cases,
        )


class ClosureSimulator:
    def __init__(self, module: Any) -> None:
        self.module = module
        self.requests: list[Mapping[str, Any]] = []

    def complete(self, request: Mapping[str, Any]) -> Any:
        self.requests.append(deepcopy(request))
        proposal = {
            "disposition": "EMIT",
            "user_utterance": f"Please continue toward: {request['goal']['text']}",
            "stop_reason_code": None,
        }
        return self.module.SimulatorResponse(
            status="SUCCEEDED",
            request_bytes=canonical(request),
            response_bytes=canonical(proposal),
            consumed_observation_hash=request["latest_observation"]["observation_hash"],
            speaker_role="USER",
            disposition="EMIT",
            user_utterance=proposal["user_utterance"],
            stop_reason_code=None,
            input_tokens=11,
            output_tokens=7,
            provider_http_exchange_count=1,
            provider_reported_cost_usd=None,
            reason_code=None,
        )


def _inventory(tmp_path: Path, *, omit: str | None = None) -> tuple[Path, str]:
    identifiers = [
        f"cand-{index:02d}" for index in range(1, 13) if f"cand-{index:02d}" != omit
    ]
    value = {
        "artifact_kind": "labs046_world_inventory",
        "schema_version": 1,
        "protocol_version": "LABS046_WORLD_INVENTORY_V1",
        "data_class": "SYNTHETIC",
        "captured_at": "2026-08-03T00:00:00Z",
        "source_lineage": {
            "source_kind": "SYNTHETIC_FIXTURE",
            "source_id": "fixture-v1",
        },
        "inventory": {"candidate_id": identifiers},
    }
    payload = canonical(value, lf=True)
    path = tmp_path / "world-inventory.json"
    path.write_bytes(payload)
    return path, _hash(payload)


def _write_closure_inputs(
    tmp_path: Path, module: Any, inventory_hash: str, cases: tuple[Any, ...]
) -> tuple[Path, Path, Path, Path]:
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(canonical({"fixture": "closure-manifest"}, lf=True))
    context_hash = _hash(canonical([case.case for case in cases]))
    selection_value = {
        "artifact_kind": "labs046_execution_selection",
        "schema_version": 1,
        "protocol_version": MODE,
        "case_factory_manifest_hash": "sha256:" + "a" * 64,
        "case_candidate_file_hash": "sha256:" + "b" * 64,
        "ordered_case_ids": [case.case["case_id"] for case in cases],
        "world_inventory_hash": inventory_hash,
        "context_hash": context_hash,
        "reviewer": "Akarsh",
        "review_state": "PASSED",
    }
    selection = tmp_path / "execution-selection.json"
    selection_payload = canonical(selection_value, lf=True)
    selection.write_bytes(selection_payload)
    config = config_value()
    config.update(
        protocol_version=MODE,
        selected_case_ids=selection_value["ordered_case_ids"],
        workflow_closure={
            "execution_selection_hash": _hash(selection_payload),
            "world_inventory_hash": inventory_hash,
            "context_hash": context_hash,
        },
    )
    config["budget"] = {
        **config["budget"],
        "all_http_exchanges": 60,
        "episode_count": 12,
        "max_usd": "100.000000",
        "simulator_http_exchanges": 24,
        "target_http_exchanges": 36,
    }
    config_path = tmp_path / "config.json"
    config_path.write_bytes(canonical(config, lf=True))
    return manifest, selection, config_path, tmp_path / "output"


def _run(tmp_path: Path, *, omit: str | None = None) -> Any:
    tmp_path.mkdir(parents=True, exist_ok=True)
    module = api()
    cases = _closure_projections(module)
    inventory, inventory_hash = _inventory(tmp_path, omit=omit)
    manifest, selection, config, output = _write_closure_inputs(
        tmp_path, module, inventory_hash, cases
    )
    simulator = ClosureSimulator(module)
    target = TargetFactory(modes=("success",) * 12)
    publisher = CapturePublisher()
    result = module.run(
        manifest,
        selection,
        config,
        output,
        simulator=simulator,
        target_factory=target,
        clock=Clock(),
        environ={**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"},
        publisher=publisher,
        source_verifier=SourceVerifier(module),
        case_loader=ClosureLoader(module, cases),
        world_inventory=inventory,
    )
    return result, cases, simulator, target, publisher


def test_missing_world_value_is_zero_egress_partial_and_later_slots_continue(
    tmp_path: Path,
) -> None:
    result, _, simulator, target, publisher = _run(tmp_path, omit="cand-01")
    attempts = jsonl(publisher.artifacts["episode_attempts.jsonl"])
    gaps = jsonl(publisher.artifacts["gaps.jsonl"])
    assert (
        len(attempts) == 12
        and attempts[0]["termination_reason"] == "WORLD_DATA_UNAVAILABLE"
    )
    assert (
        attempts[0]["target_http_exchange_count"]
        == attempts[0]["simulator_http_exchange_count"]
        == 0
    )
    assert attempts[0]["reserved_cost_usd"] == "0.000000"
    assert len(target.launches) == 11 and len(simulator.requests) == 22
    assert attempts[1]["status"] == "VALID"
    gap = next(row for row in gaps if row["reason_code"] == "WORLD_DATA_UNAVAILABLE")
    assert gap["detail"] == {
        "missing_namespace_count": 1,
        "missing_value_count": 1,
        "namespaces": ["candidate_id"],
    }
    assert result.outcome == "COMPLETED_WITH_GAPS"


def test_twelve_case_mode_projects_goal_first_and_preserves_exact_accounting(
    tmp_path: Path,
) -> None:
    result, cases, simulator, target, _ = _run(tmp_path)
    assert result.outcome == "COMPLETED"
    assert (len(target.launches), len(simulator.requests)) == (12, 24)
    assert (
        result.target_http_exchange_count,
        result.simulator_http_exchange_count,
        result.all_http_exchange_count,
    ) == (36, 24, 60)
    assert result.reserved_cost_usd == "91.999968"
    for request in simulator.requests:
        case = next(
            item.case for item in cases if item.case["case_id"] == request["case_id"]
        )
        assert request["protocol_version"] == "LABS06_SIMULATOR_FIDELITY_V1"
        assert request["goal"] == case["goal"]
        assert request["done_when"] == case["done_when"]
        assert request["case_origin"] == case["case_origin"]
        assert request["source_trace_ids"] == case["source_trace_ids"]


def test_tiered_results_are_hashed_private_safe_pending_and_legacy_three_is_unchanged(
    tmp_path: Path,
) -> None:
    _, _, _, _, publisher = _run(tmp_path / "closure")
    markdown = publisher.artifacts[MARKDOWN]
    for heading in (
        b"# LABS-06 tiered results",
        b"## Workflow completed",
        b"## Multi-turn progress, incomplete",
        b"## Blocked, invalid, or unavailable",
    ):
        assert heading in markdown
    assert b"PRIVATE_SIMULATOR_SECRET" not in markdown
    assert b"owner completion: [ ]" in markdown.lower()
    manifest = json.loads(publisher.artifacts["manifest.json"])
    assert manifest["artifacts"][MARKDOWN] == _hash(markdown)

    legacy = invoke(tmp_path / "legacy")
    assert legacy.result.attempted_episode_count == 3
    assert MARKDOWN not in legacy.publisher.artifacts
