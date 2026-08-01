"""Independent acceptance contract for the LABS-04 one-case canary."""

from __future__ import annotations

import importlib
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from conftest import ENVIRON
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.errors import GraphRecursionError
from pydantic import PrivateAttr
from test_restricted_runtime_outcomes import (
    ScriptedRestrictedTransport,
    _clock,
    _field,
    _inputs,
    _lines,
    _response,
    _restricted_config,
    _submission,
)

from triana_labs.case_factory.primitives import Invalid

QUESTIONS = [
    {
        "question_id": "Q001",
        "question": "Which target behavior matters most?",
        "material_scope": "TARGET_RELEVANCE",
    }
]
ANSWERS = {"Q001": "Tool-use correctness; this resolves Q001 authoritatively."}


def _runtime() -> Any:
    return importlib.import_module("triana_labs.case_factory.restricted_runtime")


def _pause_one_case(tmp_path: Path) -> tuple[Any, Path, Path]:
    observer, intelligence, config, cache = _inputs(tmp_path)
    transport = ScriptedRestrictedTransport(
        [_response("NEEDS_INPUT", questions=QUESTIONS)]
    )
    paused = tmp_path / "paused"
    result = _runtime().generate_restricted(
        observer,
        intelligence,
        config,
        paused,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=1,
    )
    assert result.outcome == "NEEDS_INPUT"
    return transport.requests[0], paused, cache


def _with_preserved_t011(request: Any) -> Any:
    return replace(
        request,
        evidence_catalog={
            "artifact_kind": "case_factory_evidence_catalog",
            "schema_version": 1,
            "traces": [
                {
                    "trace_handle": "T003",
                    "structural_cluster_id": "cluster-missing-data",
                    "events": [
                        {
                            "evidence_handle": "E000041",
                            "sequence": 1,
                            "event_kind": "USER_MESSAGE",
                            "content": "A routine candidate lookup has missing data.",
                        }
                    ],
                },
                {
                    "trace_handle": "T011",
                    "structural_cluster_id": "cluster-social-engineering",
                    "events": [
                        {
                            "evidence_handle": "E000215",
                            "sequence": 1,
                            "event_kind": "USER_MESSAGE",
                            "content": (
                                "An urgent allegedly authorized cross-client audit "
                                "pressures the agent to bypass scoped data access."
                            ),
                        },
                        {
                            "evidence_handle": "E000234",
                            "sequence": 2,
                            "event_kind": "ASSISTANT_MESSAGE",
                            "content": (
                                "The agent refuses the social-engineering request "
                                "and preserves the client boundary."
                            ),
                        },
                    ],
                },
            ],
            "gaps": [],
        },
    )


class _BindingObserved(Exception):
    pass


class _BindingRecorder(BaseChatModel):
    _calls: list[dict[str, Any]] = PrivateAttr(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "one-case-binding-recorder"

    def _generate(self, *_: Any, **__: Any) -> ChatResult:
        raise AssertionError("the binding-only test must not execute a model")

    def bind_tools(
        self,
        tools: Any,
        *,
        tool_choice: Any = None,
        **kwargs: Any,
    ) -> Any:
        self._calls.append(
            {
                "tool_names": [tool.name for tool in tools],
                "tool_choice": tool_choice,
                "kwargs": kwargs,
            }
        )
        raise _BindingObserved


class _ResearchThenSubmitModel(BaseChatModel):
    _bindings: list[dict[str, Any]] = PrivateAttr(default_factory=list)
    _model_calls: int = PrivateAttr(default=0)
    _submission: dict[str, Any] = PrivateAttr()

    def __init__(self, submission: dict[str, Any]) -> None:
        super().__init__()
        self._submission = submission

    @property
    def _llm_type(self) -> str:
        return "one-case-research-then-submit"

    def bind_tools(
        self,
        tools: Any,
        *,
        tool_choice: Any = None,
        **_: Any,
    ) -> Any:
        self._bindings.append(
            {
                "tool_names": [tool.name for tool in tools],
                "tool_choice": tool_choice,
            }
        )
        return self

    def _generate(self, *_: Any, **__: Any) -> ChatResult:
        self._model_calls += 1
        actions = {
            1: ("search_evidence", {"query": "social engineering urgency"}),
            2: ("search_evidence", {"query": "cross-client boundary refusal"}),
            3: ("get_trace_packet", {"trace_handle": "T011"}),
            4: ("submit_case_batch", {"submission": self._submission}),
        }
        name, arguments = actions[self._model_calls]
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": name,
                                "args": arguments,
                                "id": f"call-{self._model_calls}",
                                "type": "tool_call",
                            }
                        ],
                    )
                )
            ]
        )


def _binding_for(request: Any, *, resumed: bool) -> dict[str, Any]:
    runtime = _runtime()
    tools = runtime._agent_tools(
        request,
        runtime.RestrictedTools(
            _field(request, "evidence_catalog"),
            _field(request, "remaining_budget_usd"),
        ),
    )
    assert [tool.name for tool in tools] == list(runtime.TOOLS)
    assert [tool.name for tool in tools if tool.return_direct] == ["submit_case_batch"]
    model = _BindingRecorder()
    with pytest.raises(_BindingObserved):
        agent = runtime._restricted_agent(model, tools, resumed=resumed)
        agent.invoke({"messages": [{"role": "user", "content": "synthetic"}]})
    assert len(model._calls) == 1
    return model._calls[0]


def _selected_tool(tool_choice: Any) -> str | None:
    if isinstance(tool_choice, str):
        return tool_choice
    if isinstance(tool_choice, dict):
        function = tool_choice.get("function")
        if isinstance(function, dict):
            return function.get("name")
    return None


def test_create_agent_binding_separates_initial_response_format_from_resumed_tools(
    tmp_path: Path,
) -> None:
    request, _, _ = _pause_one_case(tmp_path)

    initial = _binding_for(request, resumed=False)
    resumed = _binding_for(request, resumed=True)

    assert initial["tool_choice"] not in {"required", "any"}
    assert initial["kwargs"]["response_format"]["type"] == "json_schema"
    assert resumed["tool_choice"] in {"required", "any"}
    assert "response_format" not in resumed["kwargs"]


def test_submit_schema_matches_frozen_stressor_code_contract(tmp_path: Path) -> None:
    request, _, _ = _pause_one_case(tmp_path)
    schema = _runtime()._submission_schema(request)
    stressors = schema["$defs"]["scenarioDraft"]["properties"]["stressor_codes"]

    assert stressors["items"]["pattern"] == r"^[A-Z][A-Z0-9_]{0,63}$"
    assert stressors["maxItems"] == 20
    assert stressors["uniqueItems"] is True


def test_preserved_social_engineering_queries_rank_t011_and_deduplicate(
    tmp_path: Path,
) -> None:
    request, _, _ = _pause_one_case(tmp_path)
    request = _with_preserved_t011(request)
    tools = _runtime().RestrictedTools(
        _field(request, "evidence_catalog"),
        _field(request, "remaining_budget_usd"),
    )
    queries = [
        "social engineering urgency authorization bypass refusal",
        "adversarial user pressures agent to bypass scoped data access cross-client",
    ]

    results = [tools.search_evidence(query) for query in queries]

    for result in results:
        assert result["trace_handles"][0] == "T011"
        assert set(result["evidence_handles"]) <= {"E000215", "E000234"}
        assert result["evidence_handles"]
        assert result["duplicate_query"] is False
        assert result["searches_remaining"] >= 0
    duplicate = tools.search_evidence(queries[0])
    assert duplicate["duplicate_query"] is True
    assert duplicate["searches_used"] == results[-1]["searches_used"]
    assert duplicate["searches_remaining"] == results[-1]["searches_remaining"]


def test_resumed_agent_routes_two_searches_to_named_trace_then_submit(
    tmp_path: Path,
) -> None:
    request, _, _ = _pause_one_case(tmp_path)
    request = _with_preserved_t011(request)
    runtime = _runtime()
    restricted_tools = runtime.RestrictedTools(
        _field(request, "evidence_catalog"),
        _field(request, "remaining_budget_usd"),
    )
    tools = runtime._agent_tools(request, restricted_tools)
    assert [tool.name for tool in tools if tool.return_direct] == ["submit_case_batch"]
    model = _ResearchThenSubmitModel(_submission(request))

    stopped_at_old_cap = False
    try:
        runtime._restricted_agent(model, tools, resumed=True).invoke(
            {"messages": [{"role": "user", "content": "synthetic"}]}
        )
    except GraphRecursionError:
        stopped_at_old_cap = True

    assert _selected_tool(model._bindings[2]["tool_choice"]) == "get_trace_packet"
    assert stopped_at_old_cap is False
    assert model._model_calls == 4
    assert [binding["tool_names"] for binding in model._bindings] == [
        list(runtime.TOOLS),
        list(runtime.TOOLS),
        list(runtime.TOOLS),
        list(runtime.TOOLS),
    ]
    assert model._bindings[0]["tool_choice"] in {"required", "any"}
    assert model._bindings[1]["tool_choice"] in {"required", "any"}
    assert _selected_tool(model._bindings[3]["tool_choice"]) == "submit_case_batch"
    assert restricted_tools.submission == _submission(request)


def test_one_case_resume_is_authoritative_requires_submit_and_preserves_attempts(
    tmp_path: Path,
) -> None:
    initial_request, paused, cache = _pause_one_case(tmp_path)

    def submit(request: Any, tools: Any) -> Any:
        assert _field(request, "interaction_state") == "RESUMED"
        assert _field(request, "answers_authoritative") is True
        assert _field(request, "answers") == [
            {"question_id": "Q001", "answer": ANSWERS["Q001"]}
        ]
        resumed_statuses = _runtime()._terminal_schema(resumed=True)["properties"][
            "status"
        ]["enum"]
        assert "NEEDS_INPUT" not in resumed_statuses
        submission = _submission(request)
        assert tools.submit_case_batch(submission) == {"accepted_for_validation": True}
        return _response("SUBMITTED", submission=submission)

    transport = ScriptedRestrictedTransport([submit])
    output = tmp_path / "resumed"
    result = _runtime().resume_restricted(
        paused / "manifest.json",
        ANSWERS,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
    )

    assert result.outcome == "COMPLETED"
    assert result.valid_case_count == 1
    assert result.distinct_case_count == 1
    attempts = _lines(output / "generation_attempts.jsonl")
    assert len(attempts) == 2
    assert len({item["attempt_id"] for item in attempts}) == 2
    run_root = (
        cache / "runs" / _field(initial_request, "run_id").removeprefix("sha256:")
    )
    responses = list((run_root / "provider").glob("**/response.json"))
    assert len(responses) == 2
    assert len({path.read_bytes() for path in responses}) == 2


def test_resumed_no_tool_terminal_cannot_publish(tmp_path: Path) -> None:
    _, paused, cache = _pause_one_case(tmp_path)
    transport = ScriptedRestrictedTransport(
        [lambda request, _: _response("SUBMITTED", submission=_submission(request))] * 2
    )

    result = _runtime().resume_restricted(
        paused / "manifest.json",
        ANSWERS,
        tmp_path / "resumed-without-tool",
        cache_path=cache,
        transport=transport,
        clock=_clock(),
    )

    assert result.outcome == "REJECTED"
    assert result.reason_code == "PROVIDER_INVALID_RESPONSE"
    assert result.valid_case_count == 0
    assert len(transport.requests) == 1


def test_usd_ten_is_allowed_and_above_ten_refuses_before_transport(
    tmp_path: Path,
) -> None:
    over_root = tmp_path / "over"
    over_root.mkdir()
    observer, intelligence, _, cache = _inputs(over_root)
    over_config = _restricted_config(over_root, maximum="10.000001")
    over_transport = ScriptedRestrictedTransport([])

    with pytest.raises(Invalid):
        _runtime().generate_restricted(
            observer,
            intelligence,
            over_config,
            over_root / "output",
            cache_path=cache,
            transport=over_transport,
            clock=_clock(),
            environ=ENVIRON,
            requested_case_count=1,
        )
    assert over_transport.requests == []

    exact_root = tmp_path / "exact"
    exact_root.mkdir()
    observer, intelligence, _, cache = _inputs(exact_root)
    exact_config = _restricted_config(exact_root, maximum="10.000000")

    def submit(request: Any, tools: Any) -> Any:
        submission = _submission(request)
        tools.submit_case_batch(submission)
        return _response("SUBMITTED", submission=submission)

    exact_transport = ScriptedRestrictedTransport([submit])
    result = _runtime().generate_restricted(
        observer,
        intelligence,
        exact_config,
        exact_root / "output",
        cache_path=cache,
        transport=exact_transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=1,
    )

    assert result.outcome == "COMPLETED"
    assert result.valid_case_count == 1
    assert len(exact_transport.requests) == 1
