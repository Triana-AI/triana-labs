"""Successful episode shape, adaptive binding, identity, and portable evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import OUTPUT_NAMES, SELECTED_CASE_IDS, canonical, invoke, jsonl, sha256


def test_success_has_exact_episode_shape_binding_and_accounting(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path)
    assert run.result.outcome == "COMPLETED"
    assert run.result.reason_code is None
    assert run.result.exit_code == 0
    assert (
        run.result.attempted_episode_count,
        run.result.valid_episode_count,
        run.result.effective_trajectory_count,
    ) == (3, 3, 3)
    assert (
        run.result.simulator_http_exchange_count,
        run.result.target_http_exchange_count,
        run.result.all_http_exchange_count,
    ) == (6, 9, 15)
    assert run.result.reserved_cost_usd == "22.999992"
    assert run.result.actual_cost_usd is None

    artifacts = run.publisher.artifacts
    assert set(artifacts) == OUTPUT_NAMES
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            assert payload == canonical(json.loads(payload), lf=True)
        else:
            assert payload == b"".join(
                canonical(record, lf=True) for record in jsonl(payload)
            )

    manifest = json.loads(artifacts["manifest.json"])
    assert manifest["outcome"] == "COMPLETED"
    assert manifest["privacy_class"] == "SYNTHETIC"
    assert manifest["human_review_state"] == "PENDING"
    assert manifest["selected_episode_count"] == 3
    assert manifest["attempted_episode_count"] == 3
    assert manifest["valid_episode_count"] == 3
    assert manifest["effective_trajectory_count"] == 3
    assert manifest["artifacts"] == {
        name: sha256(payload)
        for name, payload in artifacts.items()
        if name != "manifest.json"
    }

    transcripts = jsonl(artifacts["transcripts.jsonl"])
    assert len(transcripts) == 18
    for slot in range(3):
        episode = transcripts[slot * 6 : slot * 6 + 6]
        assert [record["ordinal"] for record in episode] == list(range(1, 7))
        assert [record["role"] for record in episode] == [
            "USER",
            "ASSISTANT",
            "USER",
            "ASSISTANT",
            "USER",
            "ASSISTANT",
        ]
        assert [record["source"] for record in episode] == [
            "CASE_OPENING",
            "TARGET",
            "SIMULATOR",
            "TARGET",
            "SIMULATOR",
            "TARGET",
        ]

    assert len(run.simulator.requests) == 6
    for index, request in enumerate(run.simulator.requests):
        slot = index // 2
        prior_assistant_ordinal = 2 if index % 2 == 0 else 4
        episode = transcripts[slot * 6 : slot * 6 + 6]
        prior = episode[prior_assistant_ordinal - 1]
        generated = episode[prior_assistant_ordinal]
        latest = request["latest_observation"]
        assert request["turn_index"] in (2, 3)
        assert latest["assistant_content"] == prior["content"]
        assert generated["consumed_observation_hash"] == latest["observation_hash"]
        assert generated["content"].startswith("follow-up reacting to ")


def test_changed_target_observation_causes_changed_bound_next_turn(
    tmp_path: Path,
) -> None:
    first = invoke(tmp_path / "first", assistant_variant="alpha-target")
    second = invoke(tmp_path / "second", assistant_variant="beta-target")

    first_request = first.simulator.requests[0]
    second_request = second.simulator.requests[0]
    assert (
        first_request["latest_observation"]["assistant_content"]
        != second_request["latest_observation"]["assistant_content"]
    )
    assert (
        first_request["latest_observation"]["observation_hash"]
        != second_request["latest_observation"]["observation_hash"]
    )
    first_turns = jsonl(first.publisher.artifacts["transcripts.jsonl"])
    second_turns = jsonl(second.publisher.artifacts["transcripts.jsonl"])
    assert first_turns[2]["content"] != second_turns[2]["content"]
    assert (
        first_turns[2]["consumed_observation_hash"]
        == first_request["latest_observation"]["observation_hash"]
    )
    assert (
        second_turns[2]["consumed_observation_hash"]
        == second_request["latest_observation"]["observation_hash"]
    )


def test_fresh_runs_repeat_byte_for_byte_and_material_config_changes_identity(
    tmp_path: Path,
) -> None:
    first = invoke(tmp_path / "first")
    second = invoke(tmp_path / "second")
    assert first.publisher.artifacts == second.publisher.artifacts

    changed_config = json.loads(first.inputs.config.read_bytes())
    changed_config["target"]["target_identity"]["version"] = "2-material-change"
    changed = invoke(tmp_path / "changed", config=changed_config)
    original_attempts = jsonl(first.publisher.artifacts["episode_attempts.jsonl"])
    changed_attempts = jsonl(changed.publisher.artifacts["episode_attempts.jsonl"])
    assert [item["episode_id"] for item in original_attempts] != [
        item["episode_id"] for item in changed_attempts
    ]


def test_loader_order_is_revalidated_not_trusted(tmp_path: Path) -> None:
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, loader_order=tuple(reversed(SELECTED_CASE_IDS)))
    failure = caught.value
    assert failure.__class__.__name__ == "AdaptiveRunFailure"
    assert failure.reason_code == "CASE_INTEGRITY_FAILED"
    assert failure.exit_code == 4
