"""Black-box acceptance for authoritative strict structured normalization."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from conftest import ENVIRON, ScriptedClock, canonical, config_value, write_config
from test_grounded_workflow_closure import (
    CANARY,
    CANARY_FIDELITY,
    CANARY_PROJECTION,
    MODE,
    _canary_inventory,
)

from triana_labs.case_factory import restricted_runtime as runtime


def _text(content: str, handles: list[str]) -> dict[str, Any]:
    return {
        "content": content,
        "support_kind": "CORROBORATING",
        "evidence_handles": handles,
    }


def _wire(prompt: str) -> dict[str, Any]:
    request = json.loads(prompt)
    slot = int(request["case_slots"][0].removeprefix("case_"))
    traces = request["evidence_catalog"]["traces"]
    if slot <= 6:
        selected = [traces[(slot - 1) % len(traces)]]
    else:
        pairs = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
        selected = [traces[index] for index in pairs[slot - 7]]
    # Non-user support does not reclassify an opening with initial USER evidence.
    event_indexes = (0, 1) if slot == 1 else (2,) if slot == 2 else (0,)
    handles = [
        trace["events"][event_index]["evidence_handle"]
        for trace in selected
        for event_index in event_indexes
    ]
    supported = _text(f"Observed content for slot {slot}", handles)
    inventory = request["evidence_catalog"]["world_inventory"]["inventory"]
    namespace = min(inventory)
    identifier = inventory[namespace][0]
    return {
        "persona": {
            "label": f"Grounded requester {slot}",
            "behavioral_traits": [supported],
            "communication_tendencies": [],
            "constraints": [],
        },
        "intent": {
            "goal": supported,
            "known_constraints": [],
            "observed_success_signals": [],
            "observed_failure_or_abandonment_signals": [],
        },
        "turn_policy": {
            "information_reveal_policy": [],
            "primary_reaction_rule": supported,
            "additional_reaction_rules": [],
            "clarification_behavior": [],
            "escalation_tendencies": [],
            "stop_conditions": [],
            "forbidden_inventions": [],
        },
        "case": {
            "opening_user_turn": supported,
            "known_facts": [],
            "private_user_facts": [],
            "unknowns": [],
            "allowed_user_actions": [],
            "tool_world_constraints": [],
            "termination_conditions": [],
            "expected_tool_names": [],
            "stressor_codes": [],
            "goal": supported,
            "done_when": supported,
            "primary_world_binding": f"{namespace}={identifier}",
            "additional_world_bindings": [],
            "primary_evaluation_criterion": supported,
            "additional_evaluation_criteria": [],
            "primary_abstain_condition": supported,
            "additional_abstain_conditions": [],
            "gaps": [],
        },
    }


class _Response:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def read(self) -> None:
        return None


class _Model:
    def __init__(self, state: dict[str, Any], capture: Any, ordinal: int) -> None:
        self.state = state
        self.capture = capture
        self.ordinal = ordinal

    def bind(self, **kwargs: Any) -> _Model:
        self.state["bindings"].append(kwargs)
        return self

    def invoke(self, messages: list[Any]) -> Any:
        self.state["invocations"] += 1
        prompt = messages[-1].content
        self.capture.on_request(SimpleNamespace(content=b'{"safe":"request"}'))
        failure = self.state.get("failure")
        if failure is not None and self.ordinal == failure[0]:
            if failure[1] == "transport":
                raise httpx.ConnectTimeout("synthetic timeout")
            content = b'{"malformed":true}'
        else:
            value = _wire(prompt)
            self.state["provider_values"].append(value)
            content = canonical(value)
        self.capture.on_response(_Response(content))
        return SimpleNamespace(
            content=content.decode(),
            response_metadata={"finish_reason": "stop"},
            usage_metadata={"input_tokens": 101, "output_tokens": 53},
        )


class _Client:
    def close(self) -> None:
        return None


def _install_model(
    monkeypatch: pytest.MonkeyPatch, failure: Any = None
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "bindings": [],
        "factory_calls": 0,
        "invocations": 0,
        "provider_values": [],
        "failure": failure,
    }

    def factory(_: str, __: str, ___: int, capture: Any) -> tuple[Any, Any]:
        state["factory_calls"] += 1
        return _Model(state, capture, state["factory_calls"]), _Client()

    monkeypatch.setattr(runtime, "_foundry_model", factory)
    return state


def _inputs(root: Path) -> tuple[Path, Path, Path, Path, Path]:
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": CANARY,
            "trace_id": f"trace-authoritative-{index}",
            "source_trace_id": f"source-authoritative-{index}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": f"Synthetic bounded request {index}.",
                },
                {
                    "sequence": 1,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": f"Synthetic bounded response {index}.",
                    "is_final": False,
                },
                {
                    "sequence": 2,
                    "event_kind": "USER_MESSAGE",
                    "content": f"Synthetic bounded continuation {index}.",
                },
            ],
        }
        for index in range(1, 5)
    ]
    corpus = root / "traces.jsonl"
    corpus.write_bytes(b"".join(canonical(trace, lf=True) for trace in traces))
    project = Path(__file__).resolve().parents[2]
    observed = root / "observed"
    observed_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "traces",
            "observe",
            str(corpus),
            "--out",
            str(observed),
        ],
        cwd=project,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert observed_result.returncode == 0, observed_result.stderr.decode()
    intelligence_root = root / "intelligence"
    intelligence_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "corpus",
            "derive",
            str(observed / "manifest.json"),
            "--out",
            str(intelligence_root),
        ],
        cwd=project,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert intelligence_result.returncode == 10, intelligence_result.stderr.decode()
    config = config_value()
    config["protocol_version"] = MODE
    config["authorization"].update(
        privacy_classes=[CANARY], allowed_projection=CANARY_PROJECTION
    )
    config["generation"] = {
        "candidate_count": 12,
        "evidence_byte_limit": 90_000,
        "seed": 2026080104,
    }
    config["budget"] = {
        "max_usd": "25.000000",
        "reservation_usd_per_agent_call": "2.000000",
    }
    config_path = write_config(root, config)
    return (
        observed / "manifest.json",
        intelligence_root / "manifest.json",
        config_path,
        _canary_inventory(root),
        root / "cache",
    )


def _run(root: Path, monkeypatch: pytest.MonkeyPatch, failure: Any = None) -> Any:
    state = _install_model(monkeypatch, failure)
    observer, intelligence, config, inventory, cache = _inputs(root)
    result = runtime.generate_restricted(
        observer,
        intelligence,
        config,
        root / "output",
        cache_path=cache,
        transport=runtime.FoundryGLMRestrictedTransport(
            "https://operator.example.azure.com", "SAFE_TEST_KEY"
        ),
        clock=ScriptedClock(list(range(0, 500_000_000, 1_000_000))),
        environ=ENVIRON,
        requested_case_count=12,
        world_inventory=inventory,
    )
    return result, state, cache, root / "output"


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def _schema_stats(value: Any, depth: int = 1) -> tuple[int, int]:
    if not isinstance(value, dict):
        return depth, 0
    forbidden = {
        "minLength",
        "maxLength",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "minProperties",
        "maxProperties",
        "pattern",
        "uniqueItems",
    }
    assert forbidden.isdisjoint(value)
    properties = value.get("properties", {})
    if value.get("type") == "object":
        assert value.get("additionalProperties") is False
        assert set(value.get("required", [])) == set(properties)
    children = list(properties.values())
    if isinstance(value.get("items"), dict):
        children.append(value["items"])
    child_stats = [
        _schema_stats(
            child,
            depth + int(child.get("type") in {"object", "array"}),
        )
        for child in children
    ]
    return (
        max([depth, *(item[0] for item in child_stats)]),
        len(properties) + sum(item[1] for item in child_stats),
    )


def test_strict_no_tool_exchange_persists_twelve_inventory_bound_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbid_tool(*_: Any, **__: Any) -> Any:
        raise AssertionError("authoritative normalization must not execute a tool")

    monkeypatch.setattr(runtime.RestrictedTools, "_execute", forbid_tool)
    with tempfile.TemporaryDirectory(
        prefix="triana-authoritative-", dir="/private/tmp"
    ) as raw:
        result, state, cache, output = _run(Path(raw), monkeypatch)

        assert result.outcome == "COMPLETED"
        assert result.provider_call_count == result.provider_http_exchange_count == 12
        assert result.conservative_cost_usd == "24.000000"
        assert state["factory_calls"] == state["invocations"] == 12
        assert all(
            "workflow_stratum" not in value["case"]
            for value in state["provider_values"]
        )
        assert len(state["bindings"]) == 12
        for binding in state["bindings"]:
            assert set(binding) == {"response_format", "max_tokens"}
            response_format = binding["response_format"]
            assert response_format["type"] == "json_schema"
            assert response_format["json_schema"]["strict"] is True
            schema = response_format["json_schema"]["schema"]
            assert "workflow_stratum" not in schema["properties"]["case"]["properties"]
            depth, _ = _schema_stats(schema)
            assert depth <= 5
            assert binding["max_tokens"] == 25_000

        attempts = _jsonl(output / "generation_attempts.jsonl")
        cases = _jsonl(output / "case_candidates.jsonl")
        assert len(attempts) == len(cases) == 12
        assert all(
            attempt["phase"] == "GENERATE"
            and attempt["status"] == "SUCCEEDED"
            and len(attempt["case_slots"]) == 1
            for attempt in attempts
        )
        assert [case["case_origin"] for case in cases].count(
            "OBSERVED_PRODUCTION_CASE"
        ) == 6
        assert [case["case_origin"] for case in cases].count(
            "GROUNDED_EXPANDED_CASE"
        ) == 6
        assert (
            sorted(len(case["source_trace_ids"]) for case in cases) == [1] * 6 + [2] * 6
        )
        assert all(case["fidelity"] == CANARY_FIDELITY for case in cases)
        assert all(case["required_world_keys"] for case in cases)
        by_opening = {
            case["scenario"]["opening_user_turn"]["text"]: case for case in cases
        }
        assert by_opening["Observed content for slot 1"]["workflow_stratum"] == (
            "ORDINARY"
        )
        assert by_opening["Observed content for slot 2"]["workflow_stratum"] == (
            "RECOVERY"
        )
        manifest = json.loads((output / "manifest.json").read_bytes())
        evidence = json.loads((output / "evidence_index.json").read_bytes())
        evaluation = json.loads((output / "case_factory_eval.json").read_bytes())
        assert manifest["privacy_class"] == evidence["privacy_class"] == CANARY
        assert manifest["world_inventory_hash"] == evidence["world_inventory_hash"]
        assert evaluation["provider_call_count"] == 12
        assert evaluation["provider_http_exchange_count"] == 12
        assert evaluation["reserved_cost_usd"] == "24.000000"
        assert evaluation["actual_cost_usd"] is None
        assert len(list(cache.rglob("parsed.json"))) == 12
        assert not list(cache.rglob("tool_calls.jsonl"))


@pytest.mark.parametrize(
    ("failure", "reason"),
    [
        ((4, "malformed"), "PROVIDER_STRUCTURED_OUTPUT_MALFORMED"),
        ((4, "transport"), "PROVIDER_TRANSPORT_FAILED"),
    ],
)
def test_later_typed_failure_retains_prior_cases_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    failure: tuple[int, str],
    reason: str,
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="triana-authoritative-partial-", dir="/private/tmp"
    ) as raw:
        result, state, cache, output = _run(Path(raw), monkeypatch, failure)

        assert result.outcome == "COMPLETED_WITH_GAPS"
        assert result.reason_code == reason
        assert result.valid_case_count == 3
        assert result.provider_call_count == result.provider_http_exchange_count == 4
        assert state["factory_calls"] == state["invocations"] == 4
        attempts = _jsonl(output / "generation_attempts.jsonl")
        assert [attempt["status"] for attempt in attempts] == [
            "SUCCEEDED",
            "SUCCEEDED",
            "SUCCEEDED",
            "PROVIDER_FAILED",
        ]
        assert attempts[-1]["reason_code"] == reason
        assert len(_jsonl(output / "case_candidates.jsonl")) == 3
        assert len(list(cache.rglob("parsed.json"))) == 3
        assert not any(attempt["phase"] == "REPAIR" for attempt in attempts)


def test_context_refusal_occurs_before_model_or_tool_egress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def forbidden_factory(*_: Any) -> Any:
        nonlocal calls
        calls += 1
        raise AssertionError("context refusal must precede provider construction")

    monkeypatch.setattr(runtime, "_foundry_model", forbidden_factory)
    request = runtime.AgentBatchRequest(
        "sha256:" + "1" * 64,
        "batch-001",
        "GENERATE",
        ("case_1",),
        {
            "artifact_kind": "case_factory_evidence_catalog",
            "schema_version": 1,
            "traces": [
                {
                    "trace_handle": f"T{index:03d}",
                    "structural_cluster_id": f"cluster-{index}",
                    "events": [
                        {
                            "evidence_handle": f"E{index:06d}",
                            "sequence": 0,
                            "event_kind": "USER_MESSAGE",
                            "content": "Synthetic bounded evidence.",
                        }
                    ],
                }
                for index in range(1, 5)
            ],
            "gaps": [],
            "privacy_class": CANARY,
            "authorization_projection": CANARY_PROJECTION,
            "world_inventory": {
                "artifact_kind": "labs046_world_inventory",
                "schema_version": 1,
                "protocol_version": "LABS046_WORLD_INVENTORY_V1",
                "data_class": CANARY,
                "captured_at": "2026-08-04T00:00:00Z",
                "source_lineage": {"source_kind": "FIXTURE", "source_id": "fixture"},
                "inventory": {"candidate_id": ["cand-01"]},
            },
        },
        [],
        None,
        [],
        "25.000000",
        "INITIAL",
        False,
    )
    tools = runtime.RestrictedTools(request.evidence_catalog, "25.000000")
    transport = runtime.FoundryGLMRestrictedTransport(
        "https://operator.example.azure.com",
        "SAFE_TEST_KEY",
        model_context_limit_tokens=1,
    )

    with pytest.raises(runtime.Invalid, match="PROVIDER_CONTEXT_PREFLIGHT_REFUSED"):
        transport.run(request, tools)
    assert calls == 0
    assert tools.sequence == 0 and tools.submission is None
