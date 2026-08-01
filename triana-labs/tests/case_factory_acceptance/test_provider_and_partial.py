"""Fake-provider mapping, no-retry budgets, partial publication, and cleanup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    CapturePublisher,
    ScriptedClock,
    ScriptedTransport,
    api,
    azure_body,
    build_upstream,
    critique_callback,
    invoke,
    proposal_callback,
    request_user_value,
    valid_proposal,
    write_config,
)


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        ((302, b"redirect"), "PROVIDER_FAILED"),
        ((401, b"auth"), "PROVIDER_FAILED"),
        ((403, b"forbidden"), "PROVIDER_FAILED"),
        ((418, b"other refusal"), "PROVIDER_FAILED"),
        ((200, b""), "PROVIDER_FAILED"),
        ((200, b"{"), "PROVIDER_FAILED"),
        ((200, b'{"x":1,"x":2}'), "PROVIDER_FAILED"),
        ((200, azure_body({}, finish="content_filter")), "PROVIDER_FAILED"),
        ((200, azure_body({}, finish="length")), "PROVIDER_FAILED"),
        ((200, b"x" * 1_000_001), "PROVIDER_FAILED"),
        (
            (
                200,
                json.dumps(
                    {"leak": ENVIRON["TRIANA_LABS04_SECRET_SENTINEL"]},
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode(),
            ),
            "PROVIDER_FAILED",
        ),
        (
            (
                200,
                b'{"choices":[{"finish_reason":"stop","message":{"content":null,"refusal":"no"}}],"usage":{"completion_tokens":0,"prompt_tokens":1,"total_tokens":1}}',
            ),
            "PROVIDER_FAILED",
        ),
    ],
)
def test_nonretryable_provider_failures_are_fatal_and_safe(
    tmp_path: Path, response: Any, reason: str
) -> None:
    api()
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, [response])
    assert caught.value.reason_code == reason
    assert caught.value.exit_code == 8
    assert not (tmp_path / "case-factory").exists()


@pytest.mark.parametrize(
    ("transient", "provider_reason"),
    [
        ((429, b"rate"), "PROVIDER_RATE_LIMITED"),
        ((503, b"server"), "PROVIDER_SERVER_FAILED"),
        (TimeoutError("private"), "PROVIDER_TRANSPORT_FAILED"),
    ],
)
@pytest.mark.parametrize("failure_stage", ["PROPOSE", "CRITIQUE", "REVISE"])
def test_transient_provider_state_never_retries(
    tmp_path: Path,
    transient: Any,
    provider_reason: str,
    failure_stage: str,
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    generate_module, _ = api()
    publisher = CapturePublisher()
    callbacks = {
        "PROPOSE": [
            transient,
            proposal_callback(),
            critique_callback,
            proposal_callback(),
        ],
        "CRITIQUE": [
            proposal_callback(),
            transient,
            critique_callback,
            proposal_callback(),
        ],
        "REVISE": [
            proposal_callback(),
            critique_callback,
            transient,
            proposal_callback(),
        ],
    }[failure_stage]
    transport = ScriptedTransport(callbacks)
    output = tmp_path / "case-factory"
    try:
        result = generate_module.generate(
            observer,
            intelligence,
            write_config(tmp_path),
            output,
            transport=transport,
            environ=ENVIRON,
            publisher=publisher,
        )
    except generate_module.GenerateFailure as error:
        result = error

    expected_calls = {"PROPOSE": 1, "CRITIQUE": 2, "REVISE": 3}[failure_stage]
    assert len(transport.requests) == expected_calls
    if failure_stage == "PROPOSE":
        assert isinstance(result, generate_module.GenerateFailure)
        assert (result.reason_code, result.exit_code) == ("PROVIDER_FAILED", 8)
        assert publisher.artifacts is None
        assert not output.exists()
        return

    expected_reason = {
        "CRITIQUE": "CRITIQUE_UNAVAILABLE",
        "REVISE": "REVISION_UNAVAILABLE",
    }[failure_stage]
    assert result.reason_code == expected_reason
    assert result.provider_call_count == expected_calls
    assert publisher.artifacts is not None
    attempts = [
        json.loads(line)
        for line in publisher.artifacts["generation_attempts.jsonl"].splitlines()
    ]
    failed_attempts = [item for item in attempts if item["stage"] == failure_stage]
    assert len(failed_attempts) == 1
    assert failed_attempts[0]["attempt_index"] == 0
    assert failed_attempts[0]["status"] == "TRANSPORT_FAILED"
    assert failed_attempts[0]["reason_code"] == provider_reason
    control_attempt_ids = [attempts[0]["attempt_id"]]
    for name in (
        "control_personas.jsonl",
        "control_intents.jsonl",
        "control_turn_policies.jsonl",
        "control_case_candidates.jsonl",
    ):
        for line in publisher.artifacts[name].splitlines():
            assert json.loads(line)["lineage"]["attempt_ids"] == control_attempt_ids
    assert publisher.artifacts["case_candidates.jsonl"] == b""


@pytest.mark.parametrize(
    ("callbacks", "primary", "final_empty"),
    [
        ([proposal_callback(), (401, b"critic")], "CRITIQUE_UNAVAILABLE", True),
        (
            [proposal_callback(), critique_callback, (401, b"revise")],
            "REVISION_UNAVAILABLE",
            True,
        ),
    ],
)
def test_stage_failure_publishes_control_only_partial(
    tmp_path: Path, callbacks: list[Any], primary: str, final_empty: bool
) -> None:
    api()
    publisher = CapturePublisher()
    result, _, _, _ = invoke(tmp_path, callbacks, publisher=publisher)
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == primary
    assert publisher.artifacts["control_case_candidates.jsonl"]
    assert bool(publisher.artifacts["case_candidates.jsonl"]) is not final_empty
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    manifest = json.loads(publisher.artifacts["manifest.json"])
    review = json.loads(publisher.artifacts["human_review_template.json"])
    assert evaluation["machine_status"] == "FAILED"
    assert {
        key: manifest[key]
        for key in (
            "requested_case_count",
            "valid_case_count",
            "raw_case_count",
            "distinct_case_count",
            "duplicate_case_count",
        )
    } == {
        "requested_case_count": 0,
        "valid_case_count": 0,
        "raw_case_count": 0,
        "distinct_case_count": 0,
        "duplicate_case_count": 0,
    }
    assert evaluation["revised_requested_case_count"] == 0
    assert evaluation["revised_valid_case_count"] == 0
    assert evaluation["revised_invalid_case_count"] == 0
    assert evaluation["revised_raw_n"] == evaluation["revised_effective_n"] == 0
    assert evaluation["gap_codes"] == [primary]
    assert manifest["gap_count"] == 1
    assert review["review_items"] == []
    assert evaluation["blind_lineage"] == []


@pytest.mark.parametrize(
    ("cleanup_failed", "reason"),
    [(False, "OUTPUT_WRITE_FAILED"), (True, "OUTPUT_CLEANUP_FAILED")],
)
def test_publisher_failure_has_closed_cleanup_outcome(
    tmp_path: Path,
    success_callbacks: list[Any],
    cleanup_failed: bool,
    reason: str,
) -> None:
    api()
    publisher = CapturePublisher(cleanup_failed=cleanup_failed)
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, success_callbacks, publisher=publisher)
    assert caught.value.reason_code == reason
    assert caught.value.exit_code == 7
    assert not (tmp_path / "case-factory").exists()


def test_clock_exhaustion_and_decrease_are_closed(tmp_path: Path) -> None:
    api()
    exhausted = ScriptedClock([0, 601_000_000_000])
    with pytest.raises(Exception) as caught:
        invoke(tmp_path / "late", [proposal_callback()], clock=exhausted)
    assert caught.value.reason_code == "BUDGET_EXHAUSTED"
    assert caught.value.exit_code == 9
    decreasing = ScriptedClock([10, 9])
    with pytest.raises(Exception) as caught:
        invoke(tmp_path / "backward", [proposal_callback()], clock=decreasing)
    assert caught.value.reason_code == "INTERNAL_INVARIANT_FAILED"
    assert caught.value.exit_code == 70


def test_raw_response_extras_change_response_hash_not_projection(
    tmp_path: Path, success_callbacks: list[Any]
) -> None:
    api()

    def extra_proposal(request: Any) -> tuple[int, bytes]:
        return 200, azure_body(
            valid_proposal(request_user_value(request)["citations"]), extra=True
        )

    publishers = [CapturePublisher(), CapturePublisher()]
    invoke(tmp_path / "plain", success_callbacks, publisher=publishers[0])
    invoke(
        tmp_path / "extra",
        [extra_proposal, critique_callback, proposal_callback()],
        publisher=publishers[1],
    )
    plain = [
        json.loads(line)
        for line in publishers[0].artifacts["generation_attempts.jsonl"].splitlines()
    ]
    extra = [
        json.loads(line)
        for line in publishers[1].artifacts["generation_attempts.jsonl"].splitlines()
    ]
    assert plain[0]["response_hash"] != extra[0]["response_hash"]
