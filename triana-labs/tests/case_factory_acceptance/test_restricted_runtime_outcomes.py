"""Five black-box outcomes for the restricted LABS-04 Case Factory runtime."""

from __future__ import annotations

import importlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from conftest import (
    ENVIRON,
    ScriptedClock,
    build_upstream,
    canonical,
    config_value,
    write_config,
)

PORTABLE_FILES = {
    "manifest.json",
    "generation_attempts.jsonl",
    "evidence_index.json",
    "control_personas.jsonl",
    "control_intents.jsonl",
    "control_turn_policies.jsonl",
    "control_case_candidates.jsonl",
    "personas.jsonl",
    "intents.jsonl",
    "turn_policies.jsonl",
    "case_candidates.jsonl",
    "case_factory_eval.json",
    "human_review_template.json",
}


def _field(value: Any, name: str) -> Any:
    return value[name] if isinstance(value, dict) else getattr(value, name)


class ScriptedRestrictedTransport:
    """Framework-independent fake at the frozen restricted-agent boundary."""

    def __init__(self, actions: list[Any]) -> None:
        self.actions = actions
        self.requests: list[Any] = []

    def run(self, request: Any, tools: Any) -> Any:
        self.requests.append(request)
        action = self.actions[len(self.requests) - 1]
        return action(request, tools) if callable(action) else action


def _response(
    status: str,
    *,
    submission: dict[str, Any] | None = None,
    questions: list[dict[str, str]] | None = None,
    reason: str | None = None,
) -> Any:
    request_bytes = canonical({"safe": "restricted-request"})
    response_value = submission or questions or {"reason": reason}
    return SimpleNamespace(
        status=status,
        submission=submission,
        questions=questions or [],
        failure_reason_code=reason,
        request_bytes=request_bytes,
        response_bytes=canonical(response_value),
        input_tokens=20,
        output_tokens=10,
        actual_cost_usd="0.125000",
        latency_ms=25,
    )


def _supported(text: str, claim_key: str) -> dict[str, Any]:
    return {"text": text, "basis": "OBSERVED", "claim_keys": [claim_key]}


def _generated(text: str) -> dict[str, Any]:
    return {"text": text, "basis": "GENERATED_VARIATION", "claim_keys": []}


def _submission(request: Any, *, invented_handle: bool = False) -> dict[str, Any]:
    catalog = _field(request, "evidence_catalog")
    traces = catalog["traces"]
    handles = [trace["events"][0]["evidence_handle"] for trace in traces[:2]]
    if invented_handle:
        handles = ["E999999", handles[-1]]
    slots = list(_field(request, "case_slots"))
    personas: list[dict[str, Any]] = []
    intents: list[dict[str, Any]] = []
    policies: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    for offset, case_slot in enumerate(slots, start=1):
        suffix = case_slot.removeprefix("case_")
        persona_key = f"persona_{offset}"
        intent_key = f"intent_{offset}"
        policy_key = f"turn_policy_{offset}"
        claim_key = f"claim_{offset}"
        claim = {
            "claim_key": claim_key,
            "claim": f"Observed behavior for case {suffix}",
            "support_kind": "CORROBORATING",
            "evidence_handles": handles,
        }
        personas.append(
            {
                "persona_key": persona_key,
                "label": f"Careful requester {suffix}",
                "behavioral_traits": [_supported("Checks details", claim_key)],
                "communication_tendencies": [],
                "constraints": [],
                "grounding_claims": [deepcopy(claim)],
            }
        )
        intents.append(
            {
                "intent_key": intent_key,
                "goal": _supported(f"Complete request {suffix}", claim_key),
                "known_constraints": [],
                "observed_success_signals": [],
                "observed_failure_or_abandonment_signals": [],
                "grounding_claims": [deepcopy(claim)],
            }
        )
        policies.append(
            {
                "turn_policy_key": policy_key,
                "information_reveal_policy": [],
                "reaction_rules": [_supported("Clarify incomplete answers", claim_key)],
                "clarification_behavior": [],
                "escalation_tendencies": [],
                "stop_conditions": [_generated("Stop when resolved")],
                "forbidden_inventions": [],
                "grounding_claims": [deepcopy(claim)],
            }
        )
        cases.append(
            {
                "case_key": case_slot,
                "persona_key": persona_key,
                "intent_key": intent_key,
                "turn_policy_key": policy_key,
                "scenario": {
                    "opening_user_turn": _supported(
                        f"Opening request {suffix}", claim_key
                    ),
                    "known_facts": [],
                    "private_user_facts": [],
                    "unknowns": [],
                    "allowed_user_actions": [_generated("May clarify")],
                    "tool_world_constraints": [],
                    "termination_conditions": [_generated("Resolved")],
                    "expected_tool_names": [f"tool_{suffix}"],
                    "stressor_codes": [f"STRESS_{suffix}"],
                },
                "grounding_claims": [deepcopy(claim)],
                "proposed_evaluation": {
                    "criteria": [_generated("Agent adapts")],
                    "abstain_conditions": [_generated("Evidence unavailable")],
                },
                "gaps": [],
            }
        )
    return {
        "personas": personas,
        "intents": intents,
        "turn_policies": policies,
        "cases": cases,
    }


def _submitted(
    request: Any, tools: Any, *, invented_handle: bool = False
) -> Any:
    submission = _submission(request, invented_handle=invented_handle)
    tools.submit_case_batch(submission)
    return _response("SUBMITTED", submission=submission)


def _restricted_config(tmp_path: Path, *, maximum: str = "3.000000") -> Path:
    value = config_value()
    value["generation"]["candidate_count"] = 10
    value["budget"] = {
        "max_usd": maximum,
        "reservation_usd_per_agent_call": "0.500000",
    }
    return write_config(tmp_path, value)


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    observer, intelligence = build_upstream(tmp_path)
    return observer, intelligence, _restricted_config(tmp_path), tmp_path / "cache"


def _api() -> Any:
    return importlib.import_module("triana_labs.case_factory.generate")


def _lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def _clock() -> ScriptedClock:
    return ScriptedClock(list(range(0, 100_000_000, 1_000_000)))


def test_valid_grounded_ten_case_run_publishes_handle_free_portable_bundle(
    tmp_path: Path,
) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    transport = ScriptedRestrictedTransport([_submitted] * 2)
    output = tmp_path / "complete"

    result = _api().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=10,
    )

    assert result.outcome == "COMPLETED"
    assert {path.name for path in output.iterdir()} == PORTABLE_FILES
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert manifest["requested_case_count"] == 10
    assert manifest["valid_case_count"] == 10
    assert manifest["distinct_case_count"] >= 7
    assert len(_lines(output / "case_candidates.jsonl")) == 10
    assert (output / "control_case_candidates.jsonl").read_bytes() == b""
    assert (
        json.loads((output / "case_factory_eval.json").read_bytes())[
            "comparison_available"
        ]
        is False
    )
    assert [_field(item, "batch_id") for item in transport.requests] == [
        "batch-001",
        "batch-002",
    ]
    assert all(
        token not in b"".join(path.read_bytes() for path in output.iterdir())
        for token in (b'"T001"', b'"E000001"', b'"case_1"')
    )


def test_invented_handle_fails_closed_after_one_repair(tmp_path: Path) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    transport = ScriptedRestrictedTransport(
        [
            lambda request, tools: _submitted(
                request, tools, invented_handle=True
            ),
            lambda request, tools: _submitted(
                request, tools, invented_handle=True
            ),
        ]
    )
    output = tmp_path / "invalid"

    result = _api().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
    )

    assert result.outcome == "REJECTED"
    assert result.reason_code == "INVALID_CASE_BATCH"
    assert [_field(item, "phase") for item in transport.requests] == [
        "GENERATE",
        "REPAIR",
    ]
    attempts = _lines(output / "generation_attempts.jsonl")
    assert [item["status"] for item in attempts] == ["INVALID", "INVALID"]
    run_hex = _field(transport.requests[0], "run_id").removeprefix("sha256:")
    defects = json.loads(
        (
            cache / "runs" / run_hex / "provider/batch-001/repair/defects.json"
        ).read_bytes()
    )
    assert "UNKNOWN_EVIDENCE_HANDLE" in {item["code"] for item in defects["defects"]}
    assert len(transport.requests) == 2


def test_unfunded_first_batch_refuses_before_transport(tmp_path: Path) -> None:
    observer, intelligence, _, cache = _inputs(tmp_path)
    config = _restricted_config(tmp_path, maximum="0.499999")
    transport = ScriptedRestrictedTransport([])
    output = tmp_path / "unfunded"

    result = _api().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
    )

    assert result.outcome == "REJECTED"
    assert result.reason_code == "BUDGET_REFUSED"
    assert transport.requests == []
    attempts = _lines(output / "generation_attempts.jsonl")
    assert len(attempts) == 1
    assert attempts[0]["status"] == "BUDGET_REFUSED"
    assert attempts[0]["reserved_cost_usd"] == "0.500000"
    assert (
        json.loads((output / "manifest.json").read_bytes())["requested_case_count"]
        == 10
    )


def test_tool_and_provider_failures_preserve_reason_and_safe_artifacts(
    tmp_path: Path,
) -> None:
    for name, reason in (
        ("tool", "TOOL_EXECUTION_FAILED"),
        ("provider", "PROVIDER_TRANSPORT_FAILED"),
    ):
        root = tmp_path / name
        root.mkdir()
        observer, intelligence, config, cache = _inputs(root)
        transport = ScriptedRestrictedTransport([_response("FAILED", reason=reason)])
        output = root / "failed"

        result = _api().generate_restricted(
            observer,
            intelligence,
            config,
            output,
            cache_path=cache,
            transport=transport,
            clock=_clock(),
            environ=ENVIRON,
        )

        assert result.outcome == "REJECTED"
        assert result.reason_code == reason
        attempt = _lines(output / "generation_attempts.jsonl")[0]
        assert attempt["reason_code"] == reason
        run_hex = _field(transport.requests[0], "run_id").removeprefix("sha256:")
        stage = cache / "runs" / run_hex / "provider/batch-001/generate"
        assert (stage / "request.json").read_bytes() == canonical(
            {"safe": "restricted-request"}
        )
        assert (stage / "response.json").exists()
        assert (
            json.loads((output / "manifest.json").read_bytes())["reason_code"] == reason
        )


def test_needs_input_resumes_once_to_new_output_without_repeating_batch_one(
    tmp_path: Path,
) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    pause_transport = ScriptedRestrictedTransport(
        [
            _submitted,
            _response(
                "NEEDS_INPUT",
                questions=[
                    {
                        "question_id": "Q001",
                        "question": "Which target behavior matters most?",
                        "material_scope": "TARGET_RELEVANCE",
                    },
                    {
                        "question_id": "Q002",
                        "question": "Which case construction constraint applies?",
                        "material_scope": "CASE_CONSTRUCTION",
                    },
                ],
            ),
        ]
    )
    paused = tmp_path / "paused"

    pause_result = _api().generate_restricted(
        observer,
        intelligence,
        config,
        paused,
        cache_path=cache,
        transport=pause_transport,
        clock=_clock(),
        environ=ENVIRON,
    )

    assert pause_result.outcome == "NEEDS_INPUT"
    assert {path.name for path in paused.iterdir()} == {
        "manifest.json",
        "generation_attempts.jsonl",
        "evidence_index.json",
        "questions.json",
        "resume_state.json",
    }
    questions = json.loads((paused / "questions.json").read_bytes())["questions"]
    assert 1 <= len(questions) <= 3
    before = {path.name: path.read_bytes() for path in paused.iterdir()}
    resume_transport = ScriptedRestrictedTransport([_submitted])
    resumed = tmp_path / "resumed"

    result = _api().resume_restricted(
        paused / "manifest.json",
        {"Q001": "Tool adaptation", "Q002": "Keep the case synthetic"},
        resumed,
        cache_path=cache,
        transport=resume_transport,
        clock=_clock(),
    )

    assert result.outcome == "COMPLETED"
    assert len(_lines(resumed / "case_candidates.jsonl")) == 10
    assert len(resume_transport.requests) == 1
    request = resume_transport.requests[0]
    assert _field(request, "batch_id") == "batch-002"
    assert _field(request, "answers") == [
        {"question_id": "Q001", "answer": "Tool adaptation"},
        {"question_id": "Q002", "answer": "Keep the case synthetic"},
    ]
    assert before == {path.name: path.read_bytes() for path in paused.iterdir()}
