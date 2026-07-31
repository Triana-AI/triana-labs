"""Exact provider mapping, retry ledgers, and between-stage exhaustion."""

from __future__ import annotations

import json
from decimal import ROUND_CEILING, Decimal
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    CapturePublisher,
    azure_body,
    byte_hash,
    canonical,
    invoke,
    proposal_callback,
)


def attempts(publisher: CapturePublisher) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in publisher.artifacts["generation_attempts.jsonl"].splitlines()
    ]


def reserved_cost(body: bytes) -> str:
    raw = (Decimal(len(body)) * Decimal(10) + Decimal(4096) * Decimal(40)) / Decimal(
        1_000_000
    )
    return format(raw.quantize(Decimal("0.000001"), rounding=ROUND_CEILING), "f")


def refusal_body() -> bytes:
    return canonical(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": None, "refusal": "cannot comply"},
                }
            ],
            "usage": {
                "completion_tokens": 0,
                "prompt_tokens": 1,
                "total_tokens": 1,
            },
        }
    )


NONRETRYABLE = [
    pytest.param(
        302,
        b"redirect",
        "PROVIDER_REFUSED",
        "PROVIDER_REDIRECT_REFUSED",
        True,
        id="3xx",
    ),
    pytest.param(
        401, b"auth", "PROVIDER_REFUSED", "PROVIDER_AUTH_FAILED", True, id="401"
    ),
    pytest.param(
        403, b"forbidden", "PROVIDER_REFUSED", "PROVIDER_AUTH_FAILED", True, id="403"
    ),
    pytest.param(
        418,
        b"teapot",
        "PROVIDER_REFUSED",
        "PROVIDER_HTTP_REFUSED",
        True,
        id="other-http",
    ),
    pytest.param(
        200,
        azure_body({}, finish="content_filter"),
        "CONTENT_FILTERED",
        "PROVIDER_CONTENT_FILTERED",
        True,
        id="content-filter",
    ),
    pytest.param(
        200,
        azure_body({}, finish="length"),
        "TRUNCATED",
        "PROVIDER_RESPONSE_TRUNCATED",
        True,
        id="length",
    ),
    pytest.param(
        200,
        refusal_body(),
        "PROVIDER_REFUSED",
        "PROVIDER_MODEL_REFUSED",
        True,
        id="refusal",
    ),
    pytest.param(
        200, b"{", "INVALID_RESPONSE", "PROVIDER_RESPONSE_INVALID", True, id="malformed"
    ),
    pytest.param(
        200,
        b"",
        "INVALID_RESPONSE",
        "PROVIDER_RESPONSE_INVALID",
        True,
        id="empty-body",
    ),
    pytest.param(
        200,
        b'{"x":1,"x":2}',
        "INVALID_RESPONSE",
        "PROVIDER_RESPONSE_INVALID",
        True,
        id="duplicate-key",
    ),
    pytest.param(
        200,
        azure_body({}),
        "INVALID_RESPONSE",
        "PROVIDER_RESPONSE_INVALID",
        True,
        id="schema-invalid",
    ),
    pytest.param(
        200,
        b"x" * 1_000_001,
        "INVALID_RESPONSE",
        "PROVIDER_RESPONSE_TOO_LARGE",
        False,
        id="too-large",
    ),
    pytest.param(
        200,
        canonical({"leak": ENVIRON["TRIANA_LABS04_SECRET_SENTINEL"]}),
        "INVALID_RESPONSE",
        "PROVIDER_RESPONSE_SECRET_DETECTED",
        False,
        id="configured-sentinel",
    ),
]


@pytest.mark.parametrize(
    ("status_code", "body", "status", "reason", "has_hash"), NONRETRYABLE
)
def test_nonretryable_critique_attempt_is_exact_and_inspectable(
    tmp_path: Path,
    status_code: int,
    body: bytes,
    status: str,
    reason: str,
    has_hash: bool,
) -> None:
    publisher = CapturePublisher()
    result, transport, _, _ = invoke(
        tmp_path, [proposal_callback(), (status_code, body)], publisher=publisher
    )
    assert result.reason_code == "CRITIQUE_UNAVAILABLE"
    assert len(transport.requests) == 2
    ledger = attempts(publisher)
    assert len(ledger) == 2
    failed = ledger[1]
    assert (failed["stage"], failed["attempt_index"]) == ("CRITIQUE", 0)
    assert (failed["status"], failed["reason_code"]) == (status, reason)
    assert failed["request_hash"] == byte_hash(
        "provider-request", transport.requests[1].body
    )
    assert failed["conservative_cost_usd"] == reserved_cost(transport.requests[1].body)
    assert failed["response_hash"] == (
        byte_hash("provider-response", body) if has_hash else None
    )
    assert failed["input_tokens"] is None
    assert failed["output_tokens"] is None
    assert failed["provider_reported_cost_usd"] is None
    assert result.conservative_cost_usd == format(
        sum(Decimal(reserved_cost(request.body)) for request in transport.requests),
        ".6f",
    )
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    assert evaluation["conservative_cost_usd"] == result.conservative_cost_usd


@pytest.mark.parametrize(
    ("failure", "reason", "hash_present"),
    [
        pytest.param((429, b"rate"), "PROVIDER_RATE_LIMITED", True, id="429"),
        pytest.param((503, b"server"), "PROVIDER_SERVER_FAILED", True, id="5xx"),
        pytest.param(
            TimeoutError("PRIVATE_TRANSPORT"),
            "PROVIDER_TRANSPORT_FAILED",
            False,
            id="transport",
        ),
    ],
)
def test_retry_exhaustion_retains_both_attempts_with_exact_mapping(
    tmp_path: Path, failure: Any, reason: str, hash_present: bool
) -> None:
    publisher = CapturePublisher()
    result, transport, _, _ = invoke(
        tmp_path,
        [proposal_callback(), failure, failure],
        publisher=publisher,
    )
    assert result.reason_code == "CRITIQUE_UNAVAILABLE"
    assert len(transport.requests) == 3
    failed = attempts(publisher)[1:]
    assert len(failed) == 2
    assert [item["attempt_index"] for item in failed] == [0, 1]
    assert all(item["stage"] == "CRITIQUE" for item in failed)
    assert all(item["status"] == "TRANSPORT_FAILED" for item in failed)
    assert all(item["reason_code"] == reason for item in failed)
    for item, request in zip(failed, transport.requests[1:], strict=True):
        assert item["request_hash"] == byte_hash("provider-request", request.body)
        assert item["conservative_cost_usd"] == reserved_cost(request.body)
        if isinstance(failure, tuple) and hash_present:
            assert item["response_hash"] == byte_hash("provider-response", failure[1])
        else:
            assert item["response_hash"] is None
    assert failed[0]["attempt_id"] != failed[1]["attempt_id"]
    assert result.conservative_cost_usd == format(
        sum(Decimal(reserved_cost(request.body)) for request in transport.requests),
        ".6f",
    )
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    assert evaluation["conservative_cost_usd"] == result.conservative_cost_usd


class MutableClock:
    def __init__(self) -> None:
        self.value = 0

    def monotonic_ns(self) -> int:
        return self.value


def test_wall_clock_exhaustion_between_propose_and_critique_is_ledgered(
    tmp_path: Path,
) -> None:
    clock = MutableClock()
    propose = proposal_callback()

    def propose_then_expire(request: Any) -> tuple[int, bytes]:
        response = propose(request)
        clock.value = 601_000_000_000
        return response

    publisher = CapturePublisher()
    result, transport, _, _ = invoke(
        tmp_path,
        [propose_then_expire],
        publisher=publisher,
        clock=clock,
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "CRITIQUE_UNAVAILABLE"
    assert len(transport.requests) == 1
    ledger = attempts(publisher)
    assert [item["status"] for item in ledger] == ["SUCCEEDED", "BUDGET_REFUSED"]
    assert ledger[1]["stage"] == "CRITIQUE"
    assert ledger[1]["response_hash"] is None
    assert ledger[1]["conservative_cost_usd"] == "0.000000"


def test_success_usage_and_provider_cost_projection_are_exact(tmp_path: Path) -> None:
    def priced_critique(_: Any) -> tuple[int, bytes]:
        value = json.loads(azure_body({"issues": []}))
        value["usage"]["cost"] = 0.125
        return 200, canonical(value)

    publisher = CapturePublisher()
    invoke(
        tmp_path,
        [proposal_callback(), priced_critique, proposal_callback()],
        publisher=publisher,
    )
    ledger = attempts(publisher)
    assert ledger[1]["provider_reported_cost_usd"] == "0.125000"
    assert ledger[1]["input_tokens"] == 100
    assert ledger[1]["output_tokens"] == 50
