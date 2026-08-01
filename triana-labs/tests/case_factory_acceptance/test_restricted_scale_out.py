"""Black-box acceptance for deterministic five-slot restricted scale-out."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest
from conftest import ENVIRON
from test_restricted_runtime_outcomes import (
    ScriptedRestrictedTransport,
    _clock,
    _field,
    _inputs,
    _lines,
    _response,
    _restricted_config,
    _submission,
    _submitted,
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


def _with_http_exchanges(response: Any, count: int) -> Any:
    response.provider_http_exchange_count = count
    return response


def _submitted_with_http_exchanges(count: int = 1) -> Any:
    def submit(request: Any, tools: Any) -> Any:
        submission = _submission(request)
        tools.submit_case_batch(submission)
        response = _response("SUBMITTED", submission=submission)
        response.actual_cost_usd = None
        return _with_http_exchanges(response, count)

    return submit


def _case_openings(output: Path) -> list[str]:
    return [
        item["scenario"]["opening_user_turn"]["text"]
        for item in _lines(output / "case_candidates.jsonl")
    ]


def test_five_slots_run_as_stable_one_slot_batches_and_merge_in_slot_order(
    tmp_path: Path,
) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    transport = ScriptedRestrictedTransport([_submitted] * 5)
    output = tmp_path / "five-slots"

    result = _runtime().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=5,
    )

    assert result.outcome == "COMPLETED"
    assert [_field(request, "batch_id") for request in transport.requests] == [
        "batch-001",
        "batch-002",
        "batch-003",
        "batch-004",
        "batch-005",
    ]
    assert [_field(request, "case_slots") for request in transport.requests] == [
        ("case_1",),
        ("case_2",),
        ("case_3",),
        ("case_4",),
        ("case_5",),
    ]
    assert _case_openings(output) == [
        "Opening request 1",
        "Opening request 2",
        "Opening request 3",
        "Opening request 4",
        "Opening request 5",
    ]


def test_failed_middle_slot_is_preserved_and_later_funded_slots_continue(
    tmp_path: Path,
) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    failed = _with_http_exchanges(
        _response("FAILED", reason="PROVIDER_TRANSPORT_FAILED"), 1
    )
    transport = ScriptedRestrictedTransport(
        [_submitted, _submitted, failed, _submitted, _submitted]
    )
    output = tmp_path / "middle-gap"

    result = _runtime().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=5,
    )

    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.valid_case_count == result.distinct_case_count == 4
    assert [_field(request, "case_slots") for request in transport.requests] == [
        ("case_1",),
        ("case_2",),
        ("case_3",),
        ("case_4",),
        ("case_5",),
    ]
    attempts = _lines(output / "generation_attempts.jsonl")
    assert [attempt["status"] for attempt in attempts] == [
        "SUCCEEDED",
        "SUCCEEDED",
        "PROVIDER_FAILED",
        "SUCCEEDED",
        "SUCCEEDED",
    ]
    assert attempts[2]["case_slots"] == [3]
    assert attempts[2]["reason_code"] == "PROVIDER_TRANSPORT_FAILED"
    assert _case_openings(output) == [
        "Opening request 1",
        "Opening request 2",
        "Opening request 4",
        "Opening request 5",
    ]
    evaluation = json.loads((output / "case_factory_eval.json").read_bytes())
    assert evaluation["machine_status"] == "PASSED"


def test_resume_answers_are_authoritative_for_every_pending_one_slot_batch(
    tmp_path: Path,
) -> None:
    observer, intelligence, config, cache = _inputs(tmp_path)
    pause_transport = ScriptedRestrictedTransport(
        [_with_http_exchanges(_response("NEEDS_INPUT", questions=QUESTIONS), 1)]
    )
    paused = tmp_path / "paused"
    paused_result = _runtime().generate_restricted(
        observer,
        intelligence,
        config,
        paused,
        cache_path=cache,
        transport=pause_transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=5,
    )
    assert paused_result.outcome == "NEEDS_INPUT"

    def assert_authoritative(request: Any) -> None:
        assert _field(request, "case_slots") in [
            ("case_1",),
            ("case_2",),
            ("case_3",),
            ("case_4",),
            ("case_5",),
        ]
        assert _field(request, "interaction_state") == "RESUMED"
        assert _field(request, "answers_authoritative") is True
        assert _field(request, "answers") == [
            {"question_id": "Q001", "answer": ANSWERS["Q001"]}
        ]

    def submit_with_authoritative_answers(request: Any, tools: Any) -> Any:
        assert_authoritative(request)
        submission = _submission(request)
        tools.submit_case_batch(submission)
        return _with_http_exchanges(_response("SUBMITTED", submission=submission), 1)

    def forbidden_requestion(request: Any, _: Any) -> Any:
        assert_authoritative(request)
        return _with_http_exchanges(_response("NEEDS_INPUT", questions=QUESTIONS), 1)

    resume_transport = ScriptedRestrictedTransport(
        [
            submit_with_authoritative_answers,
            forbidden_requestion,
            submit_with_authoritative_answers,
            submit_with_authoritative_answers,
            submit_with_authoritative_answers,
        ]
    )
    output = tmp_path / "resumed"
    result = _runtime().resume_restricted(
        paused / "manifest.json",
        ANSWERS,
        output,
        cache_path=cache,
        transport=resume_transport,
        clock=_clock(),
    )

    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.outcome != "NEEDS_INPUT"
    assert result.valid_case_count == result.distinct_case_count == 4
    assert len(resume_transport.requests) == 5
    assert _case_openings(output) == [
        "Opening request 1",
        "Opening request 3",
        "Opening request 4",
        "Opening request 5",
    ]


def test_http_exchanges_are_distinct_from_logical_calls_and_budget_stops_slot(
    tmp_path: Path,
) -> None:
    observer, intelligence, _, cache = _inputs(tmp_path)
    config = _restricted_config(tmp_path, maximum="25.000000")
    value = json.loads(config.read_bytes())
    value["budget"]["reservation_usd_per_agent_call"] = "6.000000"
    config.write_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    )
    transport = ScriptedRestrictedTransport(
        [_submitted_with_http_exchanges(count) for count in (3, 2, 1, 3)]
    )
    output = tmp_path / "budget-gap"

    result = _runtime().generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=transport,
        clock=_clock(),
        environ=ENVIRON,
        requested_case_count=5,
    )

    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "BUDGET_REFUSED"
    assert result.provider_call_count == 4
    assert result.provider_http_exchange_count == 9
    assert len(transport.requests) == 4
    attempts = _lines(output / "generation_attempts.jsonl")
    assert [attempt["provider_http_exchange_count"] for attempt in attempts] == [
        3,
        2,
        1,
        3,
        0,
    ]
    assert attempts[-1]["case_slots"] == [5]
    assert attempts[-1]["status"] == "BUDGET_REFUSED"
    assert attempts[-1]["reserved_cost_usd"] == "6.000000"
    evaluation = json.loads((output / "case_factory_eval.json").read_bytes())
    manifest = json.loads((output / "manifest.json").read_bytes())
    assert evaluation["provider_call_count"] == 4
    assert evaluation["provider_http_exchange_count"] == 9
    assert manifest["provider_http_exchange_count"] == 9
    assert manifest["actual_cost_usd"] is None

    over_root = tmp_path / "over"
    over_root.mkdir()
    over_observer, over_intelligence, _, over_cache = _inputs(over_root)
    over_config = _restricted_config(over_root, maximum="25.000001")
    over_transport = ScriptedRestrictedTransport([])
    with pytest.raises(Invalid):
        _runtime().generate_restricted(
            over_observer,
            over_intelligence,
            over_config,
            over_root / "output",
            cache_path=over_cache,
            transport=over_transport,
            clock=_clock(),
            environ=ENVIRON,
            requested_case_count=5,
        )
    assert over_transport.requests == []
