"""Typed hard semantic gates and one-attempt custody."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import invoke_lab06, jsonl, proposal


def _first_episode(
    run: object,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    episode_id = run.target.launches[0].episode_id
    transcripts = [
        row
        for row in jsonl(run.publisher.artifacts["transcripts.jsonl"])
        if row["episode_id"] == episode_id
    ]
    ledger = [
        row
        for row in jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
        if row["episode_id"] == episode_id
    ]
    gaps = [
        row
        for row in jsonl(run.publisher.artifacts["gaps.jsonl"])
        if row["episode_id"] == episode_id
    ]
    return transcripts, ledger, gaps


@pytest.mark.parametrize(
    ("utterance", "detail"),
    [
        (
            "bounded case answer 1 to Synthetic accepted opening for bounded recruiting context.",
            "EXACT_ASSISTANT_ECHO",
        ),
        (
            "I have updated your account; the database operation is complete.",
            "ROLE_INVERSION",
        ),
        ("The private key is violet locker 73.", "HIDDEN_FACT_LEAK"),
        ("The synthetic request is already cancelled.", "FIXED_FACT_CONFLICT"),
    ],
)
def test_critical_semantic_defects_are_typed_and_rejected_before_target_continuation(
    tmp_path: Path, legacy: object, utterance: str, detail: str
) -> None:
    run = invoke_lab06(
        tmp_path,
        legacy,
        proposals=[proposal(user_utterance=utterance)],
        assistant_variant="bounded case",
        include_case_id=False,
    )
    transcripts, ledger, gaps = _first_episode(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    sim_rows = [row for row in ledger if row["lane"] == "SIMULATOR"]
    assert len(sim_rows) == 1
    assert sim_rows[0]["provider_http_exchange_count"] == 1
    assert (
        sim_rows[0]["request_hash"] is not None
        and sim_rows[0]["response_hash"] is not None
    )
    assert {(row["reason_code"], row["detail_code"]) for row in gaps} >= {
        ("SIMULATOR_SEMANTIC_INVALID", detail)
    }
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1


def test_near_echo_threshold_has_positive_and_ordinary_overlap_negative_fixture(
    tmp_path: Path, legacy: object
) -> None:
    assistant = (
        "one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen twenty twentyone "
        "twentytwo twentythree twentyfour twentyfive twentysix twentyseven "
        "twentyeight twentynine thirty"
    )
    positive = (
        f"{assistant.replace('twenty ', 'changed ', 1)} answer 1 to Synthetic "
        "accepted opening for bounded recruiting context."
    )
    rejected = invoke_lab06(
        tmp_path / "positive",
        legacy,
        proposals=[proposal(user_utterance=positive)],
        assistant_variant=assistant,
        include_case_id=False,
    )
    assert "NEAR_ASSISTANT_ECHO" in {
        row["detail_code"] for row in jsonl(rejected.publisher.artifacts["gaps.jsonl"])
    }

    accepted = invoke_lab06(
        tmp_path / "negative",
        legacy,
        proposals=[proposal(user_utterance="Please clarify the synthetic request.")],
        assistant_variant="Please clarify that this synthetic request remains open",
        include_case_id=False,
    )
    assert not any(
        row["reason_code"] == "SIMULATOR_SEMANTIC_INVALID"
        for row in jsonl(accepted.publisher.artifacts["gaps.jsonl"])
    )
    assert accepted.result.valid_episode_count == 3


@pytest.mark.parametrize(
    ("updates", "detail"),
    [
        ({"reaction_id": "reaction-administrator"}, "UNAUTHORIZED_REACTION"),
        ({"action_ids": ["action-delete-account"]}, "UNAUTHORIZED_ACTION"),
        (
            {
                "disposition": "STOP",
                "reaction_id": "reaction-clarify",
                "action_ids": [],
                "user_utterance": None,
                "stop_reason_code": "GOAL_SATISFIED",
            },
            "STOP_NOT_ALLOWED",
        ),
    ],
)
def test_unauthorized_reaction_action_and_stop_are_closed_semantic_gaps(
    tmp_path: Path, legacy: object, updates: dict[str, object], detail: str
) -> None:
    run = invoke_lab06(tmp_path, legacy, proposals=[proposal(**updates)])
    _, _, gaps = _first_episode(run)
    assert {(row["reason_code"], row["detail_code"]) for row in gaps} >= {
        ("SIMULATOR_SEMANTIC_INVALID", detail)
    }


@pytest.mark.parametrize(
    ("updates", "reason"),
    [
        ({"extra": "unknown"}, "SIMULATOR_INVALID_RESPONSE"),
        (
            {"consumed_observation_hash": "sha256:" + "f" * 64},
            "ADAPTATION_BINDING_MISMATCH",
        ),
        ({"speaker_role": "ASSISTANT"}, "SIMULATOR_INVALID_RESPONSE"),
    ],
)
def test_malformed_binding_and_unknown_semantic_output_fail_once_without_fallback(
    tmp_path: Path, legacy: object, updates: dict[str, object], reason: str
) -> None:
    run = invoke_lab06(tmp_path, legacy, proposals=[proposal(**updates)])
    transcripts, ledger, gaps = _first_episode(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    assert sum(row["lane"] == "SIMULATOR" for row in ledger) == 1
    assert reason in {row["reason_code"] for row in gaps}
    assert (
        len(
            [
                request
                for request in run.simulator.requests
                if request["episode_id"] == run.target.launches[0].episode_id
            ]
        )
        == 1
    )
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1


def test_invalid_supplied_context_refuses_pre_egress_without_legacy_fallback(
    tmp_path: Path, legacy: object
) -> None:
    def corrupt(bundle: dict[str, object]) -> None:
        contexts = bundle["contexts"]
        contexts[0]["assistant_only_literal_matchers"] = []

    with pytest.raises(Exception) as caught:
        invoke_lab06(tmp_path, legacy, bundle_mutator=corrupt)
    failure = caught.value
    assert failure.__class__.__name__ == "AdaptiveRunFailure"
    assert failure.reason_code == "SIMULATOR_CONTEXT_INVALID"
    assert failure.exit_code == 4
