"""Strict target framing, sequence validation, reset, and memory isolation."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ENVIRON, SELECTED_CASE_IDS, api, config_value, invoke, jsonl


def test_each_episode_gets_fresh_target_state_and_discards_memory(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path)
    assert len(run.target.launches) == len(run.target.sessions) == 3
    assert [launch.case_id for launch in run.target.launches] == list(SELECTED_CASE_IDS)
    assert len({launch.episode_id for launch in run.target.launches}) == 3
    for launch, session in zip(run.target.launches, run.target.sessions, strict=True):
        assert launch.environment == ENVIRON
        assert launch.world["persistent_memory"] == "DISABLED"
        assert launch.world["reset_policy"] == "FRESH_PER_EPISODE"
        assert [request["kind"] for request in session.exchanges] == [
            "hello",
            "turn",
            "turn",
            "turn",
            "close",
        ]
        assert session.exchanges[0]["episode_id"] == launch.episode_id
        assert session.terminate_count == 1
    payload = b"".join(run.publisher.artifacts.values())
    assert b"persistent_memory" not in payload
    assert b"PRIVATE_SIMULATOR_SECRET" not in payload


@pytest.mark.parametrize(
    ("mode", "reason"),
    [
        ("unknown_field", "TARGET_PROTOCOL_ERROR"),
        ("identity_mismatch", "TARGET_PROTOCOL_ERROR"),
        ("tool_refused", "TARGET_TOOL_REFUSED"),
        ("provider_failed", "TARGET_PROVIDER_ERROR"),
        ("timeout", "TARGET_TIMEOUT"),
        ("oserror", "TARGET_PROTOCOL_ERROR"),
    ],
)
def test_closed_target_failures_publish_typed_partial_and_continue_slots(
    tmp_path: Path, mode: str, reason: str
) -> None:
    run = invoke(tmp_path, target_modes=(mode, "success", "success"))
    assert run.result.outcome == "COMPLETED_WITH_GAPS"
    assert run.result.exit_code == 10
    assert run.result.attempted_episode_count == 3
    assert len(run.target.sessions) == 3
    assert all(session.terminate_count == 1 for session in run.target.sessions)
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert reason in {gap["reason_code"] for gap in gaps}
    assert "INSUFFICIENT_DISTINCT_TRAJECTORIES" in {gap["reason_code"] for gap in gaps}


@pytest.mark.parametrize(
    "mode",
    [
        "blank",
        "duplicate",
        "invalid_utf8",
        "extra_line",
        "nonzero",
        "identity_mismatch",
        "unknown_field",
        "out_of_order",
    ],
)
def test_real_jsonl_factory_fails_closed_on_raw_protocol_defects(
    tmp_path: Path, mode: str
) -> None:
    module = api()
    completed = invoke(
        tmp_path,
        config=config_value(target_mode=mode),
        target=module.JsonlTargetProcessFactory(),
    )
    assert completed.result.outcome == "COMPLETED_WITH_GAPS"
    assert completed.result.exit_code == 10
    gaps = jsonl(completed.publisher.artifacts["gaps.jsonl"])
    assert "TARGET_PROTOCOL_ERROR" in {gap["reason_code"] for gap in gaps}


def test_real_jsonl_factory_classifies_and_redacts_stderr(tmp_path: Path) -> None:
    module = api()
    run = invoke(
        tmp_path,
        config=config_value(target_mode="stderr"),
        target=module.JsonlTargetProcessFactory(),
    )
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert "TARGET_STDERR" in {gap["reason_code"] for gap in gaps}
    assert b"PRIVATE_TARGET_EXCEPTION" not in b"".join(run.publisher.artifacts.values())


def test_fallback_and_unallowlisted_environment_never_reach_launch(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path)
    for launch in run.target.launches:
        assert launch.target_config["fallback_model"] is None
        assert set(launch.environment) == set(ENVIRON)
        assert "LABS05_FAKE_API_KEY" not in launch.environment
