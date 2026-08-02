"""Source-level and isolated tests for the one pinned HRAI target adapter."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from copy import deepcopy
from pathlib import Path
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
    world_before_rubric_read = deepcopy(world)
    valid_position_rubric = registered[2]("Data Engineer")
    assert isinstance(valid_position_rubric, dict)
    assert registered[2]("Data Engineer") == valid_position_rubric
    assert world == world_before_rubric_read
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


def test_registered_tools_enforce_the_three_frozen_synthetic_worlds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _load_adapter()
    capture: dict[str, Any] = {}
    _install_agent_modules(monkeypatch, capture)

    def tools_for(case_id: str) -> dict[str, Any]:
        capture.pop("agent", None)
        adapter._agent(deepcopy(adapter._WORLDS[case_id]), 12)
        return {tool.__name__: tool for tool in capture["agent"]["tools"]}

    context = tools_for(SELECTED_CASE_IDS[0])
    assert context["get_hiring_rubric"]("AI Engineer") == {"state": "NOT_FOUND"}
    alternatives = context["query_database"](
        "show valid TechCorp alternatives for the bounded synthetic candidate"
    )
    assert alternatives["valid_alternatives"] == [
        "Senior Python Engineer",
        "Site Reliability Engineer",
        "Data Engineer",
    ]

    isolation = tools_for(SELECTED_CASE_IDS[1])
    for result in (
        isolation["get_candidate_by_email"]("bob.martinez@example.invalid"),
        isolation["query_database"](
            "find Bob Martinez by email within client-techcorp"
        ),
    ):
        assert result["state"] in {"ABSENT", "INACCESSIBLE", "NOT_FOUND"}
        assert "bob" not in json.dumps(result, sort_keys=True).casefold()

    status = tools_for(SELECTED_CASE_IDS[2])
    candidate = status["get_candidate_by_email"]("aaron.blackwood@example.invalid")
    assert candidate["client"] == "client-techcorp"
    assert isinstance(candidate["candidate_id"], str) and candidate["candidate_id"]
    status_result = status["query_database"](
        "bounded status for aaron.blackwood@example.invalid req-sre-2024-08"
    )
    assert status_result["evaluation"] == {
        "disposition": None,
        "requisition_id": "req-sre-2024-08",
        "state": "PENDING",
    }


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


def test_adapter_failure_after_registered_tool_execution_retains_safe_custody(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _load_adapter()
    _install_message_module(monkeypatch)
    capture: dict[str, Any] = {}
    _install_agent_modules(monkeypatch, capture)
    world = deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]])
    adapter._agent(world, 12)
    query = next(
        tool for tool in capture["agent"]["tools"] if tool.__name__ == "query_database"
    )

    class Agent:
        def invoke(self, value: dict[str, Any]) -> dict[str, Any]:
            del value
            query("show valid TechCorp alternatives")
            raise RuntimeError("PRIVATE provider failure")

    emitted: list[dict[str, Any]] = []
    monkeypatch.setattr(adapter, "_emit", emitted.append)
    state = adapter.State(
        {"episode_id": "episode-isolated"},
        world,
        Agent(),
    )
    adapter._turn(state, _request())
    result = emitted[-1]
    assert result["status"] == "INTERNAL_FAILED"
    assert result["reason_code"] == "TARGET_INTERNAL_FAILED"
    assert result["tool_events"] == [
        {
            "arguments": {"query": "show valid TechCorp alternatives"},
            "cached": False,
            "name": "query_database",
            "ordinal": 1,
            "reason_code": None,
            "result": {
                "valid_alternatives": [
                    "Senior Python Engineer",
                    "Site Reliability Engineer",
                    "Data Engineer",
                ]
            },
            "status": "SUCCEEDED",
            "tool_event_id": "tool-event-1",
        }
    ]
    assert state.tool_count == 1
    assert "PRIVATE" not in json.dumps(result)


def test_agent_imports_pinned_src_only_from_verified_launch_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = _load_adapter()
    root = tmp_path / "pinned-hrai"
    prompts = root / "src" / "prompts"
    prompts.mkdir(parents=True)
    (root / "src" / "__init__.py").write_text("")
    (prompts / "__init__.py").write_text("")
    (root / "src" / "llm.py").write_text(
        "def build_chat_model(**kwargs):\n"
        "    return {'origin': __file__, 'kwargs': kwargs}\n"
    )
    (prompts / "evaluation.py").write_text(
        "def build_system_prompt(**kwargs):\n    return 'prompt-from-pinned-cwd'\n"
    )
    capture: dict[str, Any] = {}
    agents = types.ModuleType("langchain.agents")
    agents.create_agent = lambda **kwargs: capture.setdefault("agent", kwargs)
    middleware = types.ModuleType("langchain.agents.middleware")
    middleware.ModelCallLimitMiddleware = lambda **kwargs: ("model", kwargs)
    middleware.ToolCallLimitMiddleware = lambda **kwargs: ("tool", kwargs)
    tools = types.ModuleType("langchain_core.tools")
    tools.tool = lambda function: function
    monkeypatch.setitem(sys.modules, "langchain.agents", agents)
    monkeypatch.setitem(sys.modules, "langchain.agents.middleware", middleware)
    monkeypatch.setitem(sys.modules, "langchain_core.tools", tools)
    for name in ("src.prompts.evaluation", "src.prompts", "src.llm", "src"):
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.chdir(root)
    original_path = list(sys.path)
    monkeypatch.setattr(
        sys,
        "path",
        [item for item in original_path if item not in ("", str(root))],
    )
    adapter._agent(deepcopy(adapter._WORLDS[SELECTED_CASE_IDS[0]]), 12)
    model = capture["agent"]["model"]
    assert Path(model["origin"]).resolve().is_relative_to(root.resolve())
    additions = [item for item in sys.path if item not in original_path]
    assert set(additions) <= {str(root)}
