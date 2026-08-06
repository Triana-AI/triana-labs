from __future__ import annotations

import importlib.util
import json
from types import SimpleNamespace
from typing import Any

import pytest

from conftest import SECRET


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("tau2_luna_local") is None,
    reason="production package absent; test_package_contract owns the RED signal",
)


class FakeResponse(dict[str, Any]):
    def __init__(self) -> None:
        super().__init__(
            id="resp-1",
            created=1_750_000_000,
            model="luna-test-deployment",
            choices=[
                {
                    "index": 0,
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "reasoning_content": "returned concise rationale",
                        "tool_calls": [
                            {
                                "id": "tool-1",
                                "type": "function",
                                "function": {"name": "lookup_order", "arguments": '{"order_id":"O-1"}'},
                            }
                        ],
                    },
                }
            ],
            usage={
                "prompt_tokens": 9,
                "completion_tokens": 7,
                "total_tokens": 16,
                "completion_tokens_details": {"reasoning_tokens": 3},
                "prompt_tokens_details": {"cached_tokens": 2},
            },
        )
        self._hidden_params = {"response_cost": 0.0025, "api_base": "azure", "safe": "metadata"}
        self._response_headers = {"x-request-id": "provider-request-1"}

    def model_dump(self) -> dict[str, Any]:
        return dict(self)


class Sink:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.spans: list[dict[str, Any]] = []

    def event(self, name: str, payload: dict[str, Any]) -> None:
        self.events.append((name, payload))

    def span(self, payload: dict[str, Any]) -> None:
        self.spans.append(payload)


def capture_context(target: Any, sink: Sink):
    from tau2_luna_local.capture import CompletionCapture

    wall = iter([1_000, 1_100])
    mono = iter([10, 35])
    return CompletionCapture(
        target=target,
        event_sink=sink.event,
        span_sink=sink.span,
        secrets=(SECRET,),
        wall_time_ns=lambda: next(wall),
        monotonic_ns=lambda: next(mono),
        call_id_factory=lambda: "call-fixed",
        span_id_factory=lambda: "span-fixed",
        role_lane="agent",
    )


def test_success_captures_lossless_observable_request_response_and_span() -> None:
    calls: list[dict[str, Any]] = []

    def original(**kwargs: Any) -> FakeResponse:
        calls.append(kwargs)
        return FakeResponse()

    target = SimpleNamespace(completion=original)
    sink = Sink()
    kwargs = {
        "model": "azure/luna-test-deployment",
        "api_base": "https://unit.openai.azure.com",
        "api_version": "2026-01-01-preview",
        "api_key": SECRET,
        "messages": [{"role": "user", "content": "Need order status"}],
        "tools": [{"type": "function", "function": {"name": "lookup_order", "parameters": {"type": "object"}}}],
        "tool_choice": "auto",
        "num_retries": 0,
    }
    with capture_context(target, sink):
        response = target.completion(**kwargs)

    assert isinstance(response, FakeResponse)
    assert calls == [kwargs]
    assert [name for name, _ in sink.events] == ["model.request", "model.response"]
    request = sink.events[0][1]
    terminal = sink.events[1][1]
    assert request["model"] == kwargs["model"]
    assert request["messages"] == kwargs["messages"]
    assert request["tools"] == kwargs["tools"]
    assert request["tool_choice"] == "auto"
    assert request["retry_setting"] == 0
    assert request["endpoint_host"] == "unit.openai.azure.com"
    assert terminal["response"] == dict(response)
    assert terminal["response"]["usage"]["completion_tokens_details"]["reasoning_tokens"] == 3
    assert terminal["response"]["usage"]["prompt_tokens_details"]["cached_tokens"] == 2
    assert terminal["response"]["choices"][0]["message"]["reasoning_content"] == "returned concise rationale"
    assert terminal["cost"] == 0.0025
    assert terminal["response_headers"] == {"x-request-id": "provider-request-1"}
    assert terminal["hidden_metadata"]["safe"] == "metadata"
    assert terminal["raw_response_class"] == "FakeResponse"
    assert terminal["duration_ns"] == 25
    assert len(sink.spans) == 1
    assert sink.spans[0]["span_id"] == terminal["span_id"] == request["span_id"] == "span-fixed"
    assert sink.spans[0]["call_id"] == terminal["call_id"] == request["call_id"] == "call-fixed"
    assert SECRET not in json.dumps({"events": sink.events, "spans": sink.spans})
    assert target.completion is original


def test_provider_error_is_redacted_terminal_once_and_restores() -> None:
    class ProviderFailure(RuntimeError):
        status_code = 429
        retry_after = "3"
        response = {"headers": {"authorization": SECRET}, "body": ["safe", SECRET]}

    def original(**_: Any) -> FakeResponse:
        raise ProviderFailure(f"provider rejected {SECRET}")

    target = SimpleNamespace(completion=original)
    sink = Sink()
    with pytest.raises(ProviderFailure):
        with capture_context(target, sink):
            target.completion(model="azure/luna", api_key=SECRET, messages=[])

    assert [name for name, _ in sink.events] == ["model.request", "model.error"]
    terminal = sink.events[1][1]
    assert terminal["exception_class"] == "ProviderFailure"
    assert terminal["status_code"] == 429
    assert terminal["retry_after"] == "3"
    assert SECRET not in json.dumps({"events": sink.events, "spans": sink.spans})
    assert target.completion is original


def test_recursive_redaction_covers_nested_sequences_headers_errors_and_objects() -> None:
    from tau2_luna_local.capture import redact

    value = SimpleNamespace(
        mapping={"authorization": SECRET, "nested": [{"x-api-key": SECRET}]},
        error=RuntimeError(f"failed using {SECRET}"),
        tuple_value=(SECRET, {"safe": "prefix-" + SECRET + "-suffix"}),
    )
    projection = redact(value, secrets=(SECRET,))
    encoded = json.dumps(projection)
    assert SECRET not in encoded
    assert encoded.count("[REDACTED]") >= 4


def test_fixed_ids_and_clocks_produce_identical_identity_evidence_bytes() -> None:
    evidence: list[bytes] = []
    for _ in range(2):
        target = SimpleNamespace(completion=lambda **__: FakeResponse())
        sink = Sink()
        with capture_context(target, sink):
            target.completion(
                model="azure/luna-test-deployment",
                api_base="https://unit.openai.azure.com",
                messages=[{"role": "user", "content": "same"}],
                num_retries=0,
            )
        evidence.append(
            json.dumps(
                {"events": sink.events, "spans": sink.spans},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        )
    assert evidence[0] == evidence[1]


@pytest.mark.parametrize("raises", [False, True])
def test_interception_restores_exact_original_after_exit(raises: bool) -> None:
    def original(**_: Any) -> FakeResponse:
        if raises:
            raise ValueError("boom")
        return FakeResponse()

    target = SimpleNamespace(completion=original)
    sink = Sink()
    try:
        with capture_context(target, sink):
            assert target.completion is not original
            target.completion(model="azure/luna", messages=[])
    except ValueError:
        pass
    assert target.completion is original
