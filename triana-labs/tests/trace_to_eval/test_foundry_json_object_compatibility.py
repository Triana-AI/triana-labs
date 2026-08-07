"""Black-box acceptance for the Foundry OpenAI-v1 JSON-object boundary."""

from __future__ import annotations

import json
import sys
from types import ModuleType
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel, ConfigDict

from triana_labs.trace_to_eval.semantic import FoundryStructuredSemanticModel


class _RequestedResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    count: int


class _Message:
    def __init__(self, *, content: str) -> None:
        self.content = content


class _RawResponse:
    def __init__(self, content: Any) -> None:
        self.content = content
        self.usage_metadata = {"input_tokens": 7, "output_tokens": 3}


class _FakeChatOpenAI:
    instances: ClassVar[list[_FakeChatOpenAI]] = []
    next_result: ClassVar[_RawResponse | Exception]

    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.bind_calls: list[dict[str, Any]] = []
        self.invoke_calls: list[list[_Message]] = []
        self.__class__.instances.append(self)

    def bind(self, **kwargs: Any) -> _FakeChatOpenAI:
        self.bind_calls.append(kwargs)
        return self

    def invoke(self, messages: list[_Message]) -> _RawResponse:
        self.invoke_calls.append(messages)
        if isinstance(self.next_result, Exception):
            raise self.next_result
        return self.next_result


@pytest.fixture
def fake_chat_openai(monkeypatch: pytest.MonkeyPatch) -> type[_FakeChatOpenAI]:
    messages = ModuleType("langchain_core.messages")
    messages.HumanMessage = _Message  # type: ignore[attr-defined]
    messages.SystemMessage = _Message  # type: ignore[attr-defined]
    openai = ModuleType("langchain_openai")
    openai.ChatOpenAI = _FakeChatOpenAI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "langchain_core.messages", messages)
    monkeypatch.setitem(sys.modules, "langchain_openai", openai)
    _FakeChatOpenAI.instances = []
    return _FakeChatOpenAI


def _model() -> FoundryStructuredSemanticModel:
    return FoundryStructuredSemanticModel(
        model_id="FW-GLM-5.2",
        endpoint="https://kairos-openai-1.openai.azure.com/openai/v1",
        api_key="synthetic-test-key",
    )


def _complete(model: FoundryStructuredSemanticModel) -> dict[str, Any]:
    return model.complete_json(
        stage="synthetic-preflight",
        system="Return the requested result.",
        payload={"input": "synthetic"},
        schema=_RequestedResult,
    )


def test_openai_v1_json_object_wire_includes_requested_schema_and_accounts_usage(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    fake_chat_openai.next_result = _RawResponse('{"label":"observed","count":2}')
    model = _model()

    assert _complete(model) == {"label": "observed", "count": 2}

    assert len(fake_chat_openai.instances) == 1
    client = fake_chat_openai.instances[0]
    assert client.kwargs["model"] == "FW-GLM-5.2"
    assert client.kwargs["api_key"].get_secret_value() == "synthetic-test-key"
    assert client.kwargs["base_url"].endswith("/openai/v1")
    assert client.kwargs["max_retries"] == 0
    assert {
        "api_version",
        "azure_endpoint",
        "default_headers",
        "default_query",
    }.isdisjoint(client.kwargs)
    assert client.bind_calls == [{"response_format": {"type": "json_object"}}]
    assert len(client.invoke_calls) == 1
    requested_schema = json.dumps(
        _RequestedResult.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert requested_schema in client.invoke_calls[0][0].content

    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 1
    assert lineage["successful_call_count"] == 1
    assert lineage["input_tokens"] == 7
    assert lineage["output_tokens"] == 3
    assert lineage["budget"]["reserved_usd"] == 0.15
    assert lineage["retry_policy"] == "NONE"
    assert lineage["fallback_policy"] == "NONE"


@pytest.mark.parametrize(
    ("content", "failure_code"),
    [
        ("not-json", "SEMANTIC_RESPONSE_JSON_INVALID"),
        ('{"label":"observed","count":2,"extra":true}', "SEMANTIC_SCHEMA_INVALID"),
        ('{"label":"observed"}', "SEMANTIC_SCHEMA_INVALID"),
        ('{"label":"observed","count":"2"}', "SEMANTIC_SCHEMA_INVALID"),
    ],
)
def test_invalid_json_or_non_strict_schema_never_returns_a_semantic_row(
    fake_chat_openai: type[_FakeChatOpenAI],
    content: str,
    failure_code: str,
) -> None:
    fake_chat_openai.next_result = _RawResponse(content)
    model = _model()

    with pytest.raises(ValueError, match=f"^{failure_code}$"):
        _complete(model)

    assert len(fake_chat_openai.instances) == 1
    assert len(fake_chat_openai.instances[0].invoke_calls) == 1
    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 1
    assert lineage["successful_call_count"] == 0
    assert lineage["input_tokens"] == 7
    assert lineage["output_tokens"] == 3
    assert lineage["budget"]["reserved_usd"] == 0.15
    assert lineage["last_failure_code"] == failure_code


@pytest.mark.parametrize(
    ("result", "failure_code"),
    [
        (_RawResponse(None), "SEMANTIC_RESPONSE_CONTENT_MISSING"),
        (RuntimeError("synthetic transport detail"), "SEMANTIC_PROVIDER_CALL_FAILED"),
    ],
)
def test_specific_content_free_failure_survives_outer_generic_recording(
    fake_chat_openai: type[_FakeChatOpenAI],
    result: _RawResponse | Exception,
    failure_code: str,
) -> None:
    fake_chat_openai.next_result = result
    model = _model()

    with pytest.raises(ValueError, match=f"^{failure_code}$"):
        _complete(model)
    model.record_failure("SEMANTIC_ANALYSIS_FAILED")

    assert len(fake_chat_openai.instances) == 1
    assert len(fake_chat_openai.instances[0].invoke_calls) == 1
    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 1
    assert lineage["successful_call_count"] == 0
    assert lineage["budget"]["reserved_usd"] == 0.15
    assert lineage["last_failure_code"] == failure_code
    assert "synthetic transport detail" not in json.dumps(lineage)
