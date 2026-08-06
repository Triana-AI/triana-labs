from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import event, refresh_manifest, write_json, write_jsonl


class NullCostResponse(dict[str, Any]):
    def __init__(self, usage: Any) -> None:
        super().__init__(
            id="terra-response",
            choices=[{"finish_reason": "stop", "message": {"content": "done"}}],
            usage=usage,
        )
        self._hidden_params = {"response_cost": None}
        self._response_headers = {"x-request-id": "terra-request"}


def test_null_provider_cost_is_calculated_exactly_without_mutating_raw_response() -> None:
    from tau2_luna_local.capture import CompletionCapture
    from tau2_luna_local.terra_smoke import terra_response_cost_fallback

    response = NullCostResponse(
        {
            "prompt_tokens": 1_000,
            "completion_tokens": 1_000,
            "completion_tokens_details": {"reasoning_tokens": 200},
        }
    )
    before = json.loads(json.dumps(response))
    events: list[tuple[str, dict[str, Any]]] = []
    target = SimpleNamespace(completion=lambda **_: response)

    with CompletionCapture(
        target=target,
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=lambda _: None,
        response_cost_fallback=terra_response_cost_fallback,
    ):
        returned = target.completion(model="azure/gpt-5-6-terra-sentinel", messages=[])

    terminal = next(payload for name, payload in events if name == "model.response")
    assert returned is response
    assert response == before
    assert terminal["response"] == before
    assert Decimal(str(terminal["cost"])) == Decimal("0.017500")
    assert terminal["cost_source"] == {
        "kind": "CALCULATED_FROM_RETURNED_USAGE",
        "input_price_per_million_usd": "2.50",
        "output_price_per_million_usd": "15.00",
    }


@pytest.mark.parametrize(
    "usage",
    [
        None,
        {"prompt_tokens": 1_000},
        {"prompt_tokens": "1000", "completion_tokens": 1_000},
        {"prompt_tokens": -1, "completion_tokens": 1_000},
    ],
)
def test_null_cost_with_missing_or_malformed_usage_remains_typed_non_success(
    usage: Any,
) -> None:
    from tau2_luna_local.capture import CompletionCapture
    from tau2_luna_local.terra_smoke import terra_response_cost_fallback

    events: list[tuple[str, dict[str, Any]]] = []
    target = SimpleNamespace(completion=lambda **_: NullCostResponse(usage))

    with CompletionCapture(
        target=target,
        event_sink=lambda name, payload: events.append((name, payload)),
        span_sink=lambda _: None,
        response_cost_fallback=terra_response_cost_fallback,
    ):
        target.completion(model="azure/gpt-5-6-terra-sentinel", messages=[])

    terminal = next(payload for name, payload in events if name == "model.response")
    assert terminal["cost"] is None
    assert terminal["cost_source"] == {"kind": "UNAVAILABLE_MALFORMED_OR_MISSING_USAGE"}


def test_optional_reasoning_text_not_returned_does_not_invalidate_complete_bundle(
    valid_bundle: Path,
) -> None:
    from tau2_luna_local.runner import build_completeness
    from tau2_luna_local.verify import verify_bundle

    events_path = valid_bundle / "events.jsonl"
    request, response = [json.loads(line) for line in events_path.read_text().splitlines()]
    response_payload = response["payload"]
    response_payload["response"].pop("reasoning_content")
    response = event(2, "model.response", response_payload, request["event_hash"])
    write_jsonl(events_path, [request, response])

    completeness_path = valid_bundle / "completeness.json"
    completeness = build_completeness(valid_bundle, benchmark_succeeded=True)
    assert completeness["valid"] is True
    assert completeness["telemetry"]["response.reasoning"]["state"] == "NOT_RETURNED"
    assert completeness["telemetry"]["response.usage.reasoning_tokens"]["state"] == "CAPTURED"
    assert completeness["telemetry"]["provider_private_chain_of_thought"]["state"] == "NOT_RETURNED"
    write_json(completeness_path, completeness)
    refresh_manifest(valid_bundle)

    report = verify_bundle(valid_bundle)
    assert report["valid"] is True
    assert report["telemetry"]["response.reasoning"]["state"] == "NOT_RETURNED"
    assert report["telemetry"]["response.usage.reasoning_tokens"]["state"] == "CAPTURED"
    assert report["telemetry"]["provider_private_chain_of_thought"]["state"] == "NOT_RETURNED"
