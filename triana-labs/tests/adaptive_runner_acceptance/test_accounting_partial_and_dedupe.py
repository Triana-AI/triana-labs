"""Budget reservations, provider accounting, partial custody, and effective N."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import TargetFactory, invoke, jsonl


def test_provider_ledger_separates_logical_turns_from_http_counts(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path)
    ledger = jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
    assert len(ledger) == 15
    simulator_rows = [row for row in ledger if row["lane"] == "SIMULATOR"]
    target_rows = [row for row in ledger if row["lane"] == "TARGET"]
    assert len(simulator_rows) == 6
    assert len(target_rows) == 9
    assert sum(row["provider_http_exchange_count"] for row in simulator_rows) == 6
    assert sum(row["provider_http_exchange_count"] for row in target_rows) == 9
    assert sum(row["input_tokens"] for row in simulator_rows) == 66
    assert sum(row["output_tokens"] for row in simulator_rows) == 42
    assert sum(row["input_tokens"] for row in target_rows) == 90
    assert sum(row["output_tokens"] for row in target_rows) == 45
    assert all(row["actual_cost_usd"] is None for row in ledger)
    assert (
        sum(
            1
            for session in run.target.sessions
            for item in session.exchanges
            if item["kind"] == "turn"
        )
        == 9
    )


@pytest.mark.parametrize(
    ("mode", "expected_reason"),
    [
        ("http_overrun", "BUDGET_EXHAUSTED"),
        ("token_overrun", "BUDGET_EXHAUSTED"),
        ("too_many_tools", "BUDGET_EXHAUSTED"),
    ],
)
def test_target_budget_overrun_is_typed_and_never_funded_further(
    tmp_path: Path, mode: str, expected_reason: str
) -> None:
    run = invoke(tmp_path, target_modes=(mode, "success", "success"))
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert attempts[0]["status"] != "VALID"
    assert expected_reason in attempts[0]["gap_codes"]
    assert expected_reason in {item["reason_code"] for item in gaps}
    assert len(run.target.sessions[0].exchanges) <= 3
    assert run.result.attempted_episode_count == 3
    assert run.target.sessions[1].exchanges[-1]["kind"] == "close"
    assert run.target.sessions[2].exchanges[-1]["kind"] == "close"


def test_simulator_token_overrun_stops_episode_before_next_target_turn(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path, simulator_token_scale=20_000)
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert "BUDGET_EXHAUSTED" in {item["reason_code"] for item in gaps}
    for session in run.target.sessions:
        assert [item["kind"] for item in session.exchanges].count("turn") == 1
        assert session.terminate_count == 1


def test_middle_slot_failure_is_preserved_and_later_funded_slot_continues(
    tmp_path: Path,
) -> None:
    run = invoke(
        tmp_path,
        target_modes=("success", "provider_failed", "success"),
    )
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    assert len(attempts) == 3
    assert attempts[0]["status"] == "VALID"
    assert attempts[1]["status"] != "VALID"
    assert attempts[1]["termination_reason"] == "TARGET_PROVIDER_ERROR"
    assert attempts[2]["status"] == "VALID"
    assert run.target.sessions[2].exchanges[-1]["kind"] == "close"
    assert run.result.outcome == "COMPLETED_WITH_GAPS"
    assert run.result.valid_episode_count == 2
    transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    by_episode: dict[str, list[dict[str, object]]] = {}
    for record in transcripts:
        by_episode.setdefault(record["episode_id"], []).append(record)
    counts = [len(records) for records in by_episode.values()]
    assert counts == [6, 1, 6]


def test_binding_mismatch_is_partial_not_a_default_turn(tmp_path: Path) -> None:
    run = invoke(tmp_path, simulator_mode="binding_mismatch")
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert "ADAPTATION_BINDING_MISMATCH" in {item["reason_code"] for item in gaps}
    transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    assert all(record["source"] != "SIMULATOR" for record in transcripts)
    assert run.result.effective_trajectory_count == 0


def test_exact_and_near_duplicates_remain_visible_but_do_not_inflate_effective_n(
    tmp_path: Path,
) -> None:
    target = TargetFactory(include_case_id=False)
    run = invoke(
        tmp_path,
        simulator_mode="same",
        include_case_id=False,
        target=target,
    )
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    clusters = json.loads(run.publisher.artifacts["trajectory_clusters.json"])
    assert len(attempts) == 3
    assert clusters["raw_n"] == 3
    assert clusters["valid_n"] == 3
    assert clusters["effective_n"] == 1
    assert len(clusters["components"]) == 1
    assert len(clusters["components"][0]) == 3
    assert [item["effective"] for item in attempts] == [True, False, False]
    assert all(item["trajectory_fingerprint"] for item in attempts)
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert sum(item["reason_code"] == "DUPLICATE_TRAJECTORY" for item in gaps) == 2
    assert "INSUFFICIENT_DISTINCT_TRAJECTORIES" in {
        item["reason_code"] for item in gaps
    }
