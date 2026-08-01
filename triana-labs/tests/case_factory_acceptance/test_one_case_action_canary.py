"""Independent acceptance contract for the LABS-04 one-case canary."""

from __future__ import annotations

import importlib
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
        assert tools.submit_case_batch(submission) == {
            "accepted_for_validation": True
        }
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
    run_root = cache / "runs" / _field(initial_request, "run_id").removeprefix(
        "sha256:"
    )
    responses = list((run_root / "provider").glob("**/response.json"))
    assert len(responses) == 2
    assert len({path.read_bytes() for path in responses}) == 2


def test_resumed_no_tool_terminal_cannot_publish(tmp_path: Path) -> None:
    _, paused, cache = _pause_one_case(tmp_path)
    transport = ScriptedRestrictedTransport(
        [
            lambda request, _: _response(
                "SUBMITTED", submission=_submission(request)
            )
        ]
        * 2
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
