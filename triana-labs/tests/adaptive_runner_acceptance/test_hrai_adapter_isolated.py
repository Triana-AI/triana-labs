"""Source-level and isolated tests for the one pinned HRAI target adapter."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from copy import deepcopy
from typing import Any

import pytest
from conftest import PROJECT_ROOT, SELECTED_CASE_IDS

ADAPTER = PROJECT_ROOT / "examples" / "hrai_recruiter_chat_v1" / "adapter.py"
PROMPT = "candidate-screening-v3-decision-followthrough"
TOOLS = (
    "get_candidate_by_email",
    "get_existing_evaluation",
    "get_hiring_rubric",
    "query_database",
)


def _load_adapter() -> Any:
    name = "triana_labs05_isolated_adapter"
    spec = importlib.util.spec_from_file_location(name, ADAPTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_agent_modules(
    monkeypatch: pytest.MonkeyPatch, capture: dict[str, Any]
) -> None:
    agents = types.ModuleType("langchain.agents")
    agents.create_agent = lambda **kwargs: capture.setdefault("agent", kwargs)
    tools = types.ModuleType("langchain_core.tools")
    tools.tool = lambda function: function
    middleware = types.ModuleType("langchain.agents.middleware")

    class ModelCallLimitMiddleware:
        def __init__(self, **values: Any) -> None:
            self.values = values
            self.kind = "model"

    class ToolCallLimitMiddleware:
        def __init__(self, **values: Any) -> None:
            self.values = values
            self.kind = "tool"

    middleware.ModelCallLimitMiddleware = ModelCallLimitMiddleware
    middleware.ToolCallLimitMiddleware = ToolCallLimitMiddleware
    llm = types.ModuleType("src.llm")

    def build_chat_model(**kwargs: Any) -> object:
        capture["model"] = kwargs
        return object()

    llm.build_chat_model = build_chat_model
    prompts = types.ModuleType("src.prompts.evaluation")

    def build_system_prompt(**kwargs: Any) -> str:
        capture["prompt"] = kwargs
        return "synthetic-system-prompt"

    prompts.build_system_prompt = build_system_prompt
    for name, module in {
        "langchain.agents": agents,
        "langchain.agents.middleware": middleware,
        "langchain_core.tools": tools,
        "src.llm": llm,
        "src.prompts.evaluation": prompts,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)


def _install_message_module(monkeypatch: pytest.MonkeyPatch) -> type[Any]:
    messages = types.ModuleType("langchain_core.messages")

    class HumanMessage:
        type = "human"

        def __init__(self, content: str) -> None:
            self.content = content

    messages.HumanMessage = HumanMessage
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages)
    return HumanMessage


def _request(*, http: int = 4, tools: int = 12) -> dict[str, Any]:
    return {
        "kind": "turn",
        "episode_id": "episode-isolated",
        "turn_index": 1,
        "user_turn_id": "turn-isolated",
        "content": "synthetic bounded request",
        "remaining_budget": {
            "http_exchanges": http,
            "input_tokens": 393216,
            "output_tokens": 24576,
            "tool_calls": tools,
            "timeout_ms": 180000,
        },
    }


def test_adapter_pins_executable_v3_identity_and_exact_read_only_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _load_adapter()
    assert adapter.PROMPT == PROMPT
    assert adapter.TOOLS == TOOLS
    assert adapter.MAX_MODEL_CALLS_PER_TURN == 4
    assert adapter.MAX_TOOL_CALLS_PER_EPISODE == 12

    capture: dict[str, Any] = {}
    _install_agent_modules(monkeypatch, capture)
    world = deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]])
    adapter._agent(world, 7)
    assert capture["model"] == {
        "temperature": 0,
        "model": "qwen.qwen3-235b-a22b-2507-v1:0",
    }
    assert capture["prompt"]["prior_memories"] == []
    registered = capture["agent"]["tools"]
    assert tuple(tool.__name__ for tool in registered) == TOOLS
    assert registered[0](world["candidate"]["email"]) == world["candidate"]
    assert registered[1](world["candidate"]["email"]) == world["evaluation"]
    assert registered[2](world["candidate"]["position"]) == world["rubric"]
    assert registered[3]("delete from candidates")["state"] == "REFUSED"
    configured = capture["agent"]["middleware"]
    assert [(item.kind, item.values) for item in configured] == [
        ("model", {"run_limit": 4, "exit_behavior": "error"}),
        (
            "tool",
            {
                "tool_name": None,
                "run_limit": 7,
                "exit_behavior": "error",
            },
        ),
    ]


def test_adapter_worlds_are_case_specific_and_grounded_in_selected_cases() -> None:
    adapter = _load_adapter()
    assert tuple(adapter._WORLDS) == SELECTED_CASE_IDS
    context, isolation, status = (adapter._WORLDS[item] for item in SELECTED_CASE_IDS)
    context_text = json.dumps(context, sort_keys=True)
    isolation_text = json.dumps(isolation, sort_keys=True)
    status_text = json.dumps(status, sort_keys=True)
    assert all(
        item in context_text for item in ("Grace Ndlovu", "TechCorp", "AI Engineer")
    )
    assert "alternative" in context_text.casefold()
    assert all(item in isolation_text for item in ("Bob Martinez", "client-techcorp"))
    assert "inaccessible" in isolation_text.casefold()
    assert all(
        item in status_text
        for item in ("Aaron Blackwood", "req-sre-2024-08", "PENDING")
    )
    assert "disposition" in status_text.casefold()
    assert len({context_text, isolation_text, status_text}) == 3


def test_adapter_aggregates_all_model_usage_and_pairs_actual_tool_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _load_adapter()
    _install_message_module(monkeypatch)

    class Message:
        def __init__(self, kind: str, content: Any, **values: Any) -> None:
            self.type = kind
            self.content = content
            for key, value in values.items():
                setattr(self, key, value)

    first = Message(
        "ai",
        "",
        usage_metadata={"input_tokens": 10, "output_tokens": 2},
        tool_calls=[
            {
                "id": "call-1",
                "name": "query_database",
                "args": {"query": "select bounded synthetic status"},
            }
        ],
    )
    tool_result = Message(
        "tool",
        '{"state":"SUCCEEDED"}',
        name="query_database",
        tool_call_id="call-1",
    )
    final = Message(
        "ai",
        "bounded final",
        usage_metadata={"input_tokens": 20, "output_tokens": 3},
        tool_calls=[],
    )

    class Agent:
        def invoke(self, value: dict[str, Any]) -> dict[str, Any]:
            return {"messages": [*value["messages"], first, tool_result, final]}

    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(adapter, "_emit", emitted.append)
    state = adapter.State(
        {"episode_id": "episode-isolated"},
        deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]]),
        Agent(),
    )
    adapter._turn(state, _request())
    result = emitted[-1]
    assert result["usage"] == {
        "input_tokens": 30,
        "output_tokens": 5,
        "provider_http_exchange_count": 2,
        "provider_reported_cost_usd": None,
    }
    assert result["tool_events"] == [
        {
            "arguments": {"query": "select bounded synthetic status"},
            "cached": False,
            "name": "query_database",
            "ordinal": 1,
            "reason_code": None,
            "result": {"state": "SUCCEEDED"},
            "status": "SUCCEEDED",
            "tool_event_id": "tool-event-1",
        }
    ]


@pytest.mark.parametrize(("http", "tools"), [(5, 12), (4, 13)])
def test_adapter_rejects_malformed_declared_caps_before_agent_construction(
    monkeypatch: pytest.MonkeyPatch, http: int, tools: int
) -> None:
    adapter = _load_adapter()
    _install_message_module(monkeypatch)
    constructions: list[int] = []

    def construct(world: dict[str, Any], remaining_tools: int) -> object:
        del world
        constructions.append(remaining_tools)
        raise AssertionError("must reject before agent construction")

    monkeypatch.setattr(adapter, "_agent", construct)
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(adapter, "_emit", emitted.append)
    state = adapter.State(
        {"episode_id": "episode-isolated"},
        deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]]),
        None,
    )
    adapter._turn(state, _request(http=http, tools=tools))
    assert not constructions
    assert emitted[-1]["status"] == "BUDGET_EXHAUSTED"
    assert emitted[-1]["reason_code"] == "BUDGET_EXHAUSTED"
    assert emitted[-1]["usage"]["provider_http_exchange_count"] == 0


@pytest.mark.parametrize(
    ("prior_tools", "declared_tools", "expected_limit"),
    [(0, 12, 12), (5, 4, 4), (12, 0, 0)],
)
def test_adapter_constructs_each_turn_with_computed_pre_execution_tool_limit(
    monkeypatch: pytest.MonkeyPatch,
    prior_tools: int,
    declared_tools: int,
    expected_limit: int,
) -> None:
    adapter = _load_adapter()
    human = _install_message_module(monkeypatch)
    limits: list[int] = []

    class Agent:
        calls = 0

        def invoke(self, value: dict[str, Any]) -> dict[str, Any]:
            self.calls += 1
            final = types.SimpleNamespace(
                type="ai",
                content="tool-free bounded answer",
                usage_metadata={"input_tokens": 3, "output_tokens": 2},
                tool_calls=[],
            )
            assert isinstance(value["messages"][-1], human)
            return {"messages": [*value["messages"], final]}

    agent = Agent()

    def construct(world: dict[str, Any], remaining_tools: int) -> Agent:
        assert world == adapter._WORLDS[SELECTED_CASE_IDS[0]]
        limits.append(remaining_tools)
        return agent

    monkeypatch.setattr(adapter, "_agent", construct)
    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(adapter, "_emit", emitted.append)
    state = adapter.State(
        {"episode_id": "episode-isolated"},
        deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]]),
        None,
        tool_count=prior_tools,
    )
    adapter._turn(state, _request(tools=declared_tools))
    assert limits == [expected_limit]
    assert agent.calls == 1
    assert emitted[-1]["status"] == "SUCCEEDED"
    assert emitted[-1]["tool_events"] == []


def test_adapter_failure_retains_usage_observed_before_render_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _load_adapter()
    _install_message_module(monkeypatch)

    class Unrenderable:
        def __str__(self) -> str:
            raise ValueError("PRIVATE provider payload")

    message = types.SimpleNamespace(
        type="ai",
        content=Unrenderable(),
        usage_metadata={"input_tokens": 17, "output_tokens": 4},
        tool_calls=[],
    )

    class Agent:
        def invoke(self, value: dict[str, Any]) -> dict[str, Any]:
            return {"messages": [*value["messages"], message]}

    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(adapter, "_emit", emitted.append)
    state = adapter.State(
        {"episode_id": "episode-isolated"},
        deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]]),
        Agent(),
    )
    adapter._turn(state, _request())
    result = emitted[-1]
    assert result["status"] == "INTERNAL_FAILED"
    assert result["usage"] == {
        "input_tokens": 17,
        "output_tokens": 4,
        "provider_http_exchange_count": 1,
        "provider_reported_cost_usd": None,
    }
    assert "PRIVATE" not in json.dumps(result)
