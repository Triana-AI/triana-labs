"""LABS-06 context projection, state, termination, and isolation behavior."""

from __future__ import annotations

from pathlib import Path

from conftest import PROTOCOL, invoke_lab06, jsonl, proposal


def test_explicit_bundle_projects_verified_context_without_hidden_value_and_no_bundle_is_legacy(
    tmp_path: Path, legacy: object
) -> None:
    historical = legacy.invoke(tmp_path / "legacy")
    assert all(
        request["protocol_version"] == "LABS05_WIRE_V1"
        for request in historical.simulator.requests
    )

    run = invoke_lab06(tmp_path / "labs06", legacy)
    request = run.simulator.requests[0]
    assert set(request) == {
        "case_context",
        "episode_id",
        "interaction_state",
        "latest_observation",
        "protocol_version",
        "remaining_turns",
        "transcript",
        "turn_index",
    }
    assert request["protocol_version"] == PROTOCOL
    assert request["case_context"]["persona"] == run.bundle["contexts"][0]["persona"]
    assert request["case_context"]["intent"] == run.bundle["contexts"][0]["intent"]
    assert request["case_context"]["hidden_fact_ids"] == ["hidden-locker"]
    assert b"violet locker 73" not in run.simulator.requests[0].__repr__().encode()
    assert run.context_loader.calls == [tmp_path / "labs06" / "simulator-context.json"]


def test_valid_emit_binds_observation_applies_registered_state_and_preserves_accounting(
    tmp_path: Path, legacy: object
) -> None:
    run = invoke_lab06(tmp_path, legacy)
    assert run.result.simulator_http_exchange_count == 6
    assert len(run.simulator.requests) == 6
    first, second = run.simulator.requests[:2]
    assert first["interaction_state"]["trust_level"] == "MEDIUM"
    assert second["interaction_state"]["trust_level"] == "HIGH"
    assert first["episode_id"] == second["episode_id"]
    transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    generated = [row for row in transcripts if row["source"] == "SIMULATOR"]
    assert len(generated) == 6
    assert (
        generated[0]["consumed_observation_hash"]
        == first["latest_observation"]["observation_hash"]
    )
    ledger = jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
    simulator_rows = [row for row in ledger if row["lane"] == "SIMULATOR"]
    assert (
        len(simulator_rows),
        sum(row["input_tokens"] for row in simulator_rows),
    ) == (6, 66)


def test_structured_stop_terminates_once_without_visible_user_token_or_later_target_turn(
    tmp_path: Path, legacy: object
) -> None:
    stopped = proposal(
        action_ids=[],
        disposition="STOP",
        reaction_id="reaction-stop",
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


def test_episode_state_is_recreated_and_never_leaks_between_episode_identities(
    tmp_path: Path, legacy: object
) -> None:
    run = invoke_lab06(tmp_path, legacy)
    first_by_episode = {}
    for request in run.simulator.requests:
        first_by_episode.setdefault(request["episode_id"], request)
    assert len(first_by_episode) == 3
    assert all(
        item["interaction_state"]["trust_level"] == "MEDIUM"
        for item in first_by_episode.values()
    )
    states = [item["interaction_state"] for item in first_by_episode.values()]
    assert states[0] == states[1] == states[2]
