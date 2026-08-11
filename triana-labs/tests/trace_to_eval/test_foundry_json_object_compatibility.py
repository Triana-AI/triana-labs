"""Black-box acceptance for the Foundry OpenAI-v1 JSON-object boundary."""

from __future__ import annotations

import json
import sys
import time
from types import ModuleType
from typing import Any, ClassVar

import pytest
from pydantic import BaseModel, ConfigDict

from triana_labs.trace_to_eval.semantic import (
    FoundryStructuredSemanticModel,
    SemanticRunReservationLedger,
)


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


def _complete(
    model: FoundryStructuredSemanticModel, *, stage: str = "synthetic-preflight"
) -> dict[str, Any]:
    return model.complete_json(
        stage=stage,
        system="Return the requested result.",
        payload={"input": "synthetic"},
        schema=_RequestedResult,
    )


def test_extraction_stage_uses_its_exact_output_ceiling_without_changing_wire_mode(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    fake_chat_openai.next_result = _RawResponse('{"label":"observed","count":2}')
    model = _model()

    assert _complete(
        model, stage="demand-episodes-and-agent-behaviors-conversation-42"
    ) == {"label": "observed", "count": 2}
    assert _complete(
        model,
        stage=("semantic-run-0/demand-episodes-and-agent-behaviors-conversation-43"),
    ) == {"label": "observed", "count": 2}
    assert _complete(model, stage="population-consolidation-0") == {
        "label": "observed",
        "count": 2,
    }

    assert len(fake_chat_openai.instances) == 3
    extraction_client, checkpoint_qualified_extraction_client, non_extraction_client = (
        fake_chat_openai.instances
    )
    assert extraction_client.kwargs["max_completion_tokens"] == 8_000
    assert (
        checkpoint_qualified_extraction_client.kwargs["max_completion_tokens"] == 8_000
    )
    assert non_extraction_client.kwargs["max_completion_tokens"] == 2_000
    for client in fake_chat_openai.instances:
        assert client.kwargs["max_retries"] == 0
        assert "temperature" not in client.kwargs
        assert client.bind_calls == [{"response_format": {"type": "json_object"}}]
        assert (
            json.dumps(
                _RequestedResult.model_json_schema(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            in client.invoke_calls[0][0].content
        )

    lineage = model.lineage()
    assert lineage["budget"]["max_output_tokens_per_call"] == 2_000
    assert lineage["budget"]["extraction_max_output_tokens_per_call"] == 8_000


def test_consolidation_stages_use_exact_output_ceiling_without_changing_wire_mode(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    fake_chat_openai.next_result = _RawResponse('{"label":"observed","count":2}')
    model = _model()

    for stage in (
        "semantic-run-0/user-populations-0005",
        "semantic-run-0/agent-behavior-patterns-0000",
        "semantic-run-0/demand-episodes-and-agent-behaviors-conversation-42",
        "semantic-run-0/semantic-audit-population-0000",
    ):
        assert _complete(model, stage=stage) == {"label": "observed", "count": 2}

    assert len(fake_chat_openai.instances) == 4
    user_population, behavior_pattern, extraction, unrelated = (
        fake_chat_openai.instances
    )
    assert user_population.kwargs["max_completion_tokens"] == 8_000
    assert behavior_pattern.kwargs["max_completion_tokens"] == 8_000
    assert extraction.kwargs["max_completion_tokens"] == 8_000
    assert unrelated.kwargs["max_completion_tokens"] == 2_000
    for client in fake_chat_openai.instances:
        assert client.kwargs["max_retries"] == 0
        assert "temperature" not in client.kwargs
        assert client.bind_calls == [{"response_format": {"type": "json_object"}}]
        assert (
            json.dumps(
                _RequestedResult.model_json_schema(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            in client.invoke_calls[0][0].content
        )

    lineage = model.lineage()
    assert lineage["budget"]["max_output_tokens_per_call"] == 2_000
    assert lineage["budget"]["extraction_max_output_tokens_per_call"] == 8_000
    assert lineage["budget"]["consolidation_max_output_tokens_per_call"] == 8_000


def test_configured_minimum_call_interval_paces_without_changing_attempt_accounting(
    fake_chat_openai: type[_FakeChatOpenAI],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_chat_openai.next_result = _RawResponse('{"label":"observed","count":2}')
    assert _model().min_call_interval_seconds == 0
    model = FoundryStructuredSemanticModel(
        model_id="FW-GLM-5.2",
        endpoint="https://kairos-openai-1.openai.azure.com/openai/v1",
        api_key="synthetic-test-key",
        min_call_interval_seconds=5,
    )
    clock = {"now": 100.0}
    events: list[tuple[str, float]] = []
    original_invoke = fake_chat_openai.invoke

    def fake_monotonic() -> float:
        return clock["now"]

    def fake_sleep(seconds: float) -> None:
        events.append(("sleep", seconds))
        clock["now"] += seconds

    def observing_invoke(
        self: _FakeChatOpenAI, messages: list[_Message]
    ) -> _RawResponse:
        events.append(("invoke", clock["now"]))
        return original_invoke(self, messages)

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    monkeypatch.setattr(time, "sleep", fake_sleep)
    monkeypatch.setattr(fake_chat_openai, "invoke", observing_invoke)

    assert _complete(model, stage="semantic-run-0/user-populations-0000") == {
        "label": "observed",
        "count": 2,
    }
    assert events == [("invoke", 100.0)]

    clock["now"] += 2
    assert _complete(model, stage="semantic-run-0/user-populations-0001") == {
        "label": "observed",
        "count": 2,
    }
    assert events == [
        ("invoke", 100.0),
        ("sleep", 3.0),
        ("invoke", 105.0),
    ]

    assert len(fake_chat_openai.instances) == 2
    assert all(
        client.kwargs["max_retries"] == 0 for client in fake_chat_openai.instances
    )
    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 2
    assert lineage["successful_call_count"] == 2
    assert lineage["budget"]["reserved_usd"] == 0.3
    assert lineage["min_call_interval_seconds"] == 5


def test_paced_provider_failure_has_no_internal_sleep_retry_or_fallback(
    fake_chat_openai: type[_FakeChatOpenAI],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_chat_openai.next_result = RuntimeError("synthetic throttling detail")
    model = FoundryStructuredSemanticModel(
        model_id="synthetic-luna",
        endpoint="https://primary.example.invalid/openai/v1",
        api_key="synthetic-test-key",
        min_call_interval_seconds=20.0,
    )
    events: list[tuple[str, float]] = []
    original_invoke = fake_chat_openai.invoke

    def fake_monotonic() -> float:
        return 100.0

    def forbidden_sleep(seconds: float) -> None:
        events.append(("sleep", seconds))

    def observing_invoke(
        self: _FakeChatOpenAI, messages: list[_Message]
    ) -> _RawResponse:
        events.append(("invoke", 100.0))
        return original_invoke(self, messages)

    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    monkeypatch.setattr(time, "sleep", forbidden_sleep)
    monkeypatch.setattr(fake_chat_openai, "invoke", observing_invoke)

    with pytest.raises(ValueError, match="^SEMANTIC_PROVIDER_CALL_FAILED$"):
        _complete(model, stage="semantic-run-0/user-populations-0000")

    assert events == [("invoke", 100.0)]
    assert len(fake_chat_openai.instances) == 1
    assert len(fake_chat_openai.instances[0].invoke_calls) == 1
    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 1
    assert lineage["successful_call_count"] == 0
    assert lineage["retry_policy"] == "NONE"
    assert lineage["fallback_policy"] == "NONE"


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
    assert client.kwargs["max_completion_tokens"] == 2_000
    assert client.kwargs["timeout"] == 120
    assert "temperature" not in client.kwargs
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


def test_local_budget_refusal_is_not_recorded_as_a_provider_attempt() -> None:
    model = FoundryStructuredSemanticModel(
        model_id="FW-GLM-5.2",
        endpoint="https://kairos-openai-1.openai.azure.com/openai/v1",
        api_key="synthetic-test-key",
        max_calls=0,
        max_reserved_usd=0.0,
    )

    with pytest.raises(ValueError, match="^SEMANTIC_BUDGET_EXCEEDED$"):
        _complete(model)

    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 0
    assert lineage["successful_call_count"] == 0
    assert lineage["budget"]["reserved_usd"] == 0.0
    assert lineage["budget"]["reserved_usd"] <= lineage["budget"]["max_reserved_usd"]
    assert model.failure_diagnostic() == {
        "code": "SEMANTIC_BUDGET_EXCEEDED",
        "phase": "LOCAL_BUDGET_PREFLIGHT",
        "http_category": None,
        "http_status": None,
        "finish_reason": None,
        "schema_path": None,
        "truncation_state": "NOT_APPLICABLE",
        "response_sha256": None,
        "retryable": False,
        "provider_attempted": False,
    }


def test_run_wide_oversized_request_is_not_misreported_or_reserved_as_budget(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    ledger = SemanticRunReservationLedger(max_total_reserved_usd=200.0)
    model = FoundryStructuredSemanticModel(
        model_id="synthetic-primary",
        endpoint="https://primary.example.invalid/openai/v1",
        api_key="synthetic-primary-key",
        max_request_bytes=1,
        reservation_usd_per_call=60.0,
        reservation_ledger=ledger,
    )

    with pytest.raises(ValueError, match="^SEMANTIC_REQUEST_TOO_LARGE$"):
        _complete(model, stage="semantic-run-0/preflight-schema")

    assert fake_chat_openai.instances == []
    assert ledger.total_attempted_call_count == 0
    assert ledger.total_reserved_usd == 0.0
    lineage = model.lineage()
    assert lineage["attempted_call_count"] == 0
    assert lineage["successful_call_count"] == 0
    assert lineage["budget"]["total_attempted_call_count"] == 0
    assert lineage["budget"]["total_reserved_usd"] == 0.0
    assert lineage["retry_policy"] == "NONE"
    assert lineage["fallback_policy"] == "NONE"
    assert model.failure_diagnostic() == {
        "code": "SEMANTIC_REQUEST_TOO_LARGE",
        "phase": "LOCAL_REQUEST_PREFLIGHT",
        "http_category": None,
        "http_status": None,
        "finish_reason": None,
        "schema_path": None,
        "truncation_state": "NOT_APPLICABLE",
        "response_sha256": None,
        "retryable": False,
        "provider_attempted": False,
    }


def test_run_wide_ledger_accounts_both_roles_and_refuses_only_crossing_call(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    """A single deterministic ledger owns all preflight and role reservations."""

    from triana_labs.trace_to_eval import semantic as semantic_module

    fake_chat_openai.next_result = _RawResponse('{"label":"observed","count":2}')
    ledger_type = semantic_module.SemanticRunReservationLedger
    ledger = ledger_type(max_total_reserved_usd=200.0)
    primary = FoundryStructuredSemanticModel(
        model_id="synthetic-primary",
        endpoint="https://primary.example.invalid/openai/v1",
        api_key="synthetic-primary-key",
        max_calls=1,
        max_reserved_usd=1.0,
        reservation_usd_per_call=60.0,
        reservation_ledger=ledger,
    )
    auditor = FoundryStructuredSemanticModel(
        model_id="synthetic-auditor",
        endpoint="https://audit.example.invalid/openai/v1",
        api_key="synthetic-audit-key",
        max_calls=1,
        max_reserved_usd=1.0,
        reservation_usd_per_call=19.0,
        reservation_ledger=ledger,
    )

    for stage in (
        "semantic-run-0/preflight-contract",
        "semantic-run-0/preflight-privacy",
        "semantic-run-0/preflight-schema",
    ):
        assert _complete(primary, stage=stage) == {"label": "observed", "count": 2}
    assert _complete(auditor, stage="semantic-run-0/semantic-audit-population-0") == {
        "label": "observed",
        "count": 2,
    }

    assert len(fake_chat_openai.instances) == 4
    primary_lineage = primary.lineage()
    audit_lineage = auditor.lineage()
    for lineage in (primary_lineage, audit_lineage):
        assert lineage["budget"]["scope"] == "RUN_WIDE"
        assert lineage["budget"]["max_total_reserved_usd"] == 200.0
        assert lineage["budget"]["total_reserved_usd"] == 199.0
        assert lineage["budget"]["total_attempted_call_count"] == 4
        assert lineage["retry_policy"] == "NONE"
        assert lineage["fallback_policy"] == "NONE"
    assert primary_lineage["attempted_call_count"] == 3
    assert audit_lineage["attempted_call_count"] == 1

    with pytest.raises(ValueError, match="^SEMANTIC_BUDGET_EXCEEDED$"):
        _complete(auditor, stage="semantic-run-0/semantic-audit-pattern-1")

    assert len(fake_chat_openai.instances) == 4
    assert auditor.lineage()["attempted_call_count"] == 1
    assert auditor.lineage()["budget"]["total_reserved_usd"] == 199.0
    assert auditor.failure_diagnostic() == {
        "code": "SEMANTIC_BUDGET_EXCEEDED",
        "phase": "LOCAL_BUDGET_PREFLIGHT",
        "http_category": None,
        "http_status": None,
        "finish_reason": None,
        "schema_path": None,
        "truncation_state": "NOT_APPLICABLE",
        "response_sha256": None,
        "retryable": False,
        "provider_attempted": False,
    }


def test_schema_failure_path_never_persists_provider_chosen_field_name(
    fake_chat_openai: type[_FakeChatOpenAI],
) -> None:
    provider_field = "customer_secret_field_name_must_not_persist"
    fake_chat_openai.next_result = _RawResponse(
        json.dumps({"label": "observed", "count": 2, provider_field: "private"})
    )
    model = _model()

    with pytest.raises(ValueError, match="^SEMANTIC_SCHEMA_INVALID$"):
        _complete(model)

    diagnostic = model.failure_diagnostic()
    assert diagnostic is not None
    assert diagnostic["schema_path"] == "SCHEMA_ROOT/EXTRA_FIELD"
    assert provider_field not in json.dumps(diagnostic, sort_keys=True)
    assert "private" not in json.dumps(diagnostic, sort_keys=True)
