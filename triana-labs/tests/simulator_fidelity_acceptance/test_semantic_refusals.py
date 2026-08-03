"""Typed hard semantic gates and one-attempt custody."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import invoke_lab06, jsonl, proposal


def _episode_evidence(run: object) -> tuple[list[dict], list[dict], list[dict]]:
    episode_id = run.target.launches[0].episode_id
    return tuple(
        [
            row
            for row in jsonl(run.publisher.artifacts[name])
            if row["episode_id"] == episode_id
        ]
        for name in ("transcripts.jsonl", "provider_ledger.jsonl", "gaps.jsonl")
    )


@pytest.mark.parametrize(
    ("raw", "reason"),
    [
        (
            {
                "action_ids": ["action-clarify"],
                "consumed_observation_hash": "sha256:" + "f" * 64,
                "disposition": "EMIT",
                "reaction_id": "reaction-clarify",
                "speaker_role": "USER",
                "stop_reason_code": None,
                "user_utterance": "Legacy response must not be repaired.",
            },
            "SIMULATOR_INVALID_RESPONSE",
        ),
        (
            {"disposition": "EMIT", "user_utterance": "Missing stop companion."},
            "SIMULATOR_INVALID_RESPONSE",
        ),
        (
            {
                "disposition": "EMIT",
                "user_utterance": "Unknown fields are invalid.",
                "stop_reason_code": None,
                "unexpected": True,
            },
            "SIMULATOR_INVALID_RESPONSE",
        ),
        (
            {
                "disposition": "STOP",
                "user_utterance": None,
                "stop_reason_code": "NOT_DECLARED",
            },
            "SIMULATOR_SEMANTIC_INVALID",
        ),
    ],
)
def test_legacy_and_malformed_three_field_outputs_fail_once_without_repair(
    tmp_path: Path, legacy: object, raw: dict, reason: str
) -> None:
    run = invoke_lab06(tmp_path, legacy, proposals=[raw])
    transcripts, ledger, gaps = _episode_evidence(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    assert sum(row["lane"] == "SIMULATOR" for row in ledger) == 1
    assert reason in {row["reason_code"] for row in gaps}
    assert (
        len(
            [
                item
                for item in run.simulator.requests
                if item["episode_id"] == run.target.launches[0].episode_id
            ]
        )
        == 1
    )
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1


@pytest.mark.parametrize(
    ("utterance", "detail", "assistant", "unauthorized"),
    [
        (
            "I have updated your account; the database operation is complete.",
            "ROLE_INVERSION",
            "bounded",
            False,
        ),
        (
            "bounded answer 1 to Synthetic accepted opening for bounded recruiting context.",
            "EXACT_ASSISTANT_ECHO",
            "bounded",
            False,
        ),
        ("The private key is violet locker 73.", "HIDDEN_FACT_LEAK", "bounded", False),
        (
            "The synthetic request is already cancelled.",
            "FIXED_FACT_CONFLICT",
            "bounded",
            False,
        ),
        ("The request is still open.", "UNAUTHORIZED_ACTION", "bounded", True),
    ],
)
def test_critical_semantic_failures_remain_typed_before_target_continuation(
    tmp_path: Path,
    legacy: object,
    utterance: str,
    detail: str,
    assistant: str,
    unauthorized: bool,
) -> None:
    def restrict(bundle: dict) -> None:
        if unauthorized:
            bundle["contexts"][0]["user_turn_policy"]["allowed_action_ids"] = [
                "action-clarify"
            ]

    run = invoke_lab06(
        tmp_path,
        legacy,
        proposals=[proposal(user_utterance=utterance)],
        bundle_mutator=restrict,
        assistant_variant=assistant,
        include_case_id=False,
    )
    transcripts, ledger, gaps = _episode_evidence(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    sim_rows = [row for row in ledger if row["lane"] == "SIMULATOR"]
    assert len(sim_rows) == 1 and sim_rows[0]["response_hash"] is not None
    assert {(row["reason_code"], row["detail_code"]) for row in gaps} >= {
        ("SIMULATOR_SEMANTIC_INVALID", detail)
    }
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1
