"""LABS-06 context projection, state, termination, and isolation behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Self

import pytest
from conftest import PROTOCOL, canonical, invoke_lab06, jsonl, proposal

INSTRUCTION = """You simulate the next USER message in an ongoing conversation.

The user's goal is the primary authority. The persona affects tone,
communication style, patience, and persistence; it must not replace or weaken
the goal.

Read the full conversation, the assistant's latest response, and the verified
current facts. Produce exactly one natural user message that advances the goal
from the current state. Continue by default when a useful next step exists.

If the requested item is unavailable, naturally clarify, correct the request,
select an offered alternative, or challenge once when the persona supports it.
Stop only when the goal is satisfied, abandoned, or a final boundary has been
established.

Do not answer as the assistant, copy or paraphrase the assistant, invent facts,
tools, records, permissions, or results, reveal hidden facts, or take an action
outside the supplied user authority. Use structured STOP, never a visible stop
token."""


def test_foundry_uses_intent_first_instruction_and_exact_three_field_schema(
    monkeypatch: pytest.MonkeyPatch, legacy: object
) -> None:
    boundaries = __import__(
        "triana_labs.adaptive_runner.boundaries", fromlist=["FoundrySimulatorTransport"]
    )
    captured: list[Any] = []

    class Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            del args

        def read(self, limit: int) -> bytes:
            assert limit == 1_000_001
            content = canonical(proposal()).decode()
            return canonical(
                {
                    "choices": [{"message": {"content": content}}],
                    "usage": {"completion_tokens": 7, "prompt_tokens": 11},
                }
            )

    class Opener:
        def open(self, request: Any, *, timeout: int) -> Response:
            assert timeout == 180
            captured.append(request)
            return Response()

    monkeypatch.setattr(
        boundaries.urllib.request, "build_opener", lambda *args: Opener()
    )
    request = {
        "protocol_version": PROTOCOL,
        "latest_observation": {"observation_hash": "sha256:" + "a" * 64},
    }
    result = boundaries.FoundrySimulatorTransport(
        legacy.config_value()["simulator"], "PRIVATE_TEST_SECRET"
    ).complete(request)
    body = json.loads(captured[0].data)
    schema = body["response_format"]["json_schema"]["schema"]
    assert body["messages"][0]["content"] == INSTRUCTION
    assert schema["required"] == [
        "disposition",
        "user_utterance",
        "stop_reason_code",
    ]
    assert set(schema["properties"]) == set(schema["required"])
    assert result.response_bytes is not None


def test_valid_emit_is_observation_bound_assigned_user_and_reaches_second_target(
    tmp_path: Path, legacy: object
) -> None:
    run = invoke_lab06(tmp_path, legacy)
    first_request = run.simulator.requests[0]
    first_episode = run.target.launches[0].episode_id
    turns = [
        row
        for row in jsonl(run.publisher.artifacts["transcripts.jsonl"])
        if row["episode_id"] == first_episode
    ]
    assert [row["role"] for row in turns[:4]] == [
        "USER",
        "ASSISTANT",
        "USER",
        "ASSISTANT",
    ]
    assert turns[2]["source"] == "SIMULATOR"
    assert (
        turns[2]["consumed_observation_hash"]
        == first_request["latest_observation"]["observation_hash"]
    )
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) >= 2


def test_unavailable_item_recovery_accepts_a_purposeful_alternative_without_internal_ids(
    tmp_path: Path, legacy: object
) -> None:
    recovery = "Could you use the offered synthetic alternative instead?"
    run = invoke_lab06(
        tmp_path,
        legacy,
        proposals=[proposal(user_utterance=recovery)],
        assistant_variant="That requested item is unavailable; an alternative is available",
    )
    assert set(run.simulator.proposals[0]) == {
        "disposition",
        "user_utterance",
        "stop_reason_code",
    }
    turns = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    assert any(
        row["source"] == "SIMULATOR" and row["content"] == recovery for row in turns
    )
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) >= 2


def test_valid_world_deepening_preserves_state_and_cross_episode_isolation(
    tmp_path: Path, legacy: object
) -> None:
    follow_up = "What is the next verified step for this open synthetic request?"
    run = invoke_lab06(tmp_path, legacy, proposals=[proposal(user_utterance=follow_up)])
    first, second = run.simulator.requests[:2]
    assert first["episode_id"] == second["episode_id"]
    assert first["interaction_state"] == second["interaction_state"]
    first_by_episode = {}
    for request in run.simulator.requests:
        first_by_episode.setdefault(request["episode_id"], request)
    assert len(first_by_episode) == 3
    states = [item["interaction_state"] for item in first_by_episode.values()]
    assert states[0] == states[1] == states[2]


def test_structured_stop_terminates_once_without_visible_user_token_or_later_target_turn(
    tmp_path: Path, legacy: object
) -> None:
    stopped = proposal(
        disposition="STOP",
        stop_reason_code="GOAL_SATISFIED",
        user_utterance=None,
    )
    run = invoke_lab06(tmp_path, legacy, proposals=[stopped])
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    assert all(row["termination_reason"] == "CASE_STOP_CONDITION" for row in attempts)
    transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    assert all(row["source"] != "SIMULATOR" for row in transcripts)
    assert b":done:" not in run.publisher.artifacts["transcripts.jsonl"]
    assert all(
        [item["kind"] for item in session.exchanges].count("turn") == 1
        for session in run.target.sessions
    )
    assert all(session.terminate_count == 1 for session in run.target.sessions)
    assert len(run.simulator.requests) == 3
