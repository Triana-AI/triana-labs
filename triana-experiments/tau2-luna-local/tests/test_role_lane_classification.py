from __future__ import annotations

from types import SimpleNamespace
from typing import Any


def test_capture_classifies_each_attempt_lane_or_emits_typed_unknown_gap() -> None:
    from tau2_luna_local.capture import CompletionCapture

    events: list[tuple[str, dict[str, Any]]] = []
    spans: list[dict[str, Any]] = []
    lanes = iter(["agent", "user", "evaluator", None])

    def provider(**_: Any) -> dict[str, Any]:
        return {"usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    capture = CompletionCapture(
        target=(target := SimpleNamespace(completion=provider)),
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=spans.append,
        role_lane_resolver=lambda _args, _kwargs: next(lanes),
        call_id_factory=lambda: f"call-{len(events)}",
        span_id_factory=lambda: f"span-{len(events)}",
    )

    with capture:
        for _ in range(4):
            target.completion(model="azure/gpt-5-6-terra-sentinel", messages=[])

    requests = [payload for name, payload in events if name == "model.request"]
    responses = [payload for name, payload in events if name == "model.response"]
    assert [payload["role_lane"] for payload in requests] == [
        "agent",
        "user",
        "evaluator",
        "unknown",
    ]
    assert [payload["role_lane"] for payload in responses] == [
        "agent",
        "user",
        "evaluator",
        "unknown",
    ]
    assert requests[-1]["role_lane_gap"] == "BOUNDARY_NOT_OBSERVABLE"
    assert responses[-1]["role_lane_gap"] == "BOUNDARY_NOT_OBSERVABLE"
    assert spans[-1]["role_lane"] == "unknown"
    assert spans[-1]["role_lane_gap"] == "BOUNDARY_NOT_OBSERVABLE"


def test_invalid_lane_classifier_output_cannot_silently_become_agent() -> None:
    from tau2_luna_local.capture import CompletionCapture

    events: list[tuple[str, dict[str, Any]]] = []
    target = SimpleNamespace(completion=lambda **_: {})

    with CompletionCapture(
        target=target,
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=lambda _: None,
        role_lane_resolver=lambda _args, _kwargs: "assistant",
    ):
        target.completion(model="azure/gpt-5-6-terra-sentinel", messages=[])

    request = next(payload for name, payload in events if name == "model.request")
    assert request["role_lane"] == "unknown"
    assert request["role_lane_gap"] == "INVALID_BOUNDARY_CLASSIFICATION"


def test_shared_imported_generate_code_defers_to_distinct_outer_tau2_boundaries() -> None:
    from tau2_luna_local import runner
    from tau2_luna_local.capture import CompletionCapture

    class ProviderResponse(dict[str, Any]):
        def __init__(self) -> None:
            super().__init__(
                id="response-shared-generate",
                choices=[{"finish_reason": "stop", "message": {"content": "unchanged"}}],
                usage={"prompt_tokens": 9, "completion_tokens": 7},
            )
            self._hidden_params = {"response_cost": 0.0025, "safe": "unchanged"}
            self._response_headers = {"x-request-id": "request-shared-generate"}

    events: list[tuple[str, dict[str, Any]]] = []
    spans: list[dict[str, Any]] = []
    provider_calls = 0
    returned: list[ProviderResponse] = []

    def provider(**_: Any) -> ProviderResponse:
        nonlocal provider_calls
        provider_calls += 1
        response = ProviderResponse()
        returned.append(response)
        return response

    target = SimpleNamespace(completion=provider)

    def shared_generate() -> ProviderResponse:
        return target.completion(
            model="azure/gpt-5-6-terra-sentinel",
            messages=[{"role": "user", "content": "same observable request"}],
        )

    def agent_step() -> ProviderResponse:
        return shared_generate()

    def user_step() -> ProviderResponse:
        return shared_generate()

    def evaluator_step() -> ProviderResponse:
        return shared_generate()

    boundaries = {
        "agent": SimpleNamespace(__name__="fake_tau2.agent", generate=shared_generate, step=agent_step),
        "user": SimpleNamespace(__name__="fake_tau2.user", generate=shared_generate, step=user_step),
        "evaluator": SimpleNamespace(
            __name__="fake_tau2.evaluator", generate=shared_generate, step=evaluator_step
        ),
    }
    resolver = runner._role_lane_resolver(boundaries)
    call_ids = iter(["agent-call", "user-call", "evaluator-call", "unknown-call"])

    with CompletionCapture(
        target=target,
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=spans.append,
        role_lane_resolver=resolver,
        call_id_factory=lambda: next(call_ids),
    ):
        boundaries["agent"].step()
        boundaries["user"].step()
        boundaries["evaluator"].step()
        target.completion(model="azure/gpt-5-6-terra-sentinel", messages=[])

    requests = [payload for name, payload in events if name == "model.request"]
    responses = [payload for name, payload in events if name == "model.response"]
    assert [payload["role_lane"] for payload in requests] == [
        "agent",
        "user",
        "evaluator",
        "unknown",
    ]
    assert requests[-1]["role_lane_gap"] == "BOUNDARY_NOT_OBSERVABLE"
    assert [payload["call_id"] for payload in requests] == [payload["call_id"] for payload in responses]
    assert [payload["role_lane"] for payload in responses] == [payload["role_lane"] for payload in requests]
    assert [payload["cost"] for payload in responses] == [0.0025] * 4
    assert all(
        payload["response_headers"] == {"x-request-id": "request-shared-generate"}
        and payload["hidden_metadata"] == {"response_cost": 0.0025, "safe": "unchanged"}
        and payload["response"]["usage"] == {"prompt_tokens": 9, "completion_tokens": 7}
        and payload["raw_response_class"] == "ProviderResponse"
        for payload in responses
    )
    assert [span["role_lane"] for span in spans] == [
        "agent",
        "user",
        "evaluator",
        "unknown",
    ]
    assert provider_calls == 4
    assert all(response._hidden_params["response_cost"] == 0.0025 for response in returned)
