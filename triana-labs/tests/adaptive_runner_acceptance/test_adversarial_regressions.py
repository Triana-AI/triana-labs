"""Focused post-candidate regressions for privacy, scalar, budget, and custody."""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    Clock,
    Simulator,
    TargetFactory,
    api,
    config_value,
    invoke,
    jsonl,
)

SECRET = "PRIVATE_SIMULATOR_SECRET"


def _first_target_ledger(run: Any) -> dict[str, Any]:
    return next(
        row
        for row in jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
        if row["lane"] == "TARGET"
    )


def _first_simulator_ledger(run: Any) -> dict[str, Any]:
    return next(
        row
        for row in jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
        if row["lane"] == "SIMULATOR"
    )


def _safe_tool_event(**changes: Any) -> dict[str, Any]:
    event = {
        "arguments": {"query": "select bounded synthetic status"},
        "cached": False,
        "name": "query_database",
        "ordinal": 1,
        "reason_code": None,
        "result": {"state": "SUCCEEDED"},
        "status": "SUCCEEDED",
        "tool_event_id": "tool-event-1",
    }
    event.update(changes)
    return event


def test_over_budget_target_response_retains_safe_observed_accounting_only(
    tmp_path: Path,
) -> None:
    unsafe = "UNSAFE_OVER_BUDGET_ASSISTANT"

    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] == "turn" and request["turn_index"] == 1:
            response["assistant_content"] = unsafe
            response["usage"].update(
                input_tokens=393_217,
                output_tokens=24_577,
                provider_http_exchange_count=5,
            )
        elif request["kind"] == "close":
            response["provider_http_exchange_count"] = 5

    run = invoke(tmp_path, response_mutator=mutate)
    attempt = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0]
    ledger = _first_target_ledger(run)
    manifest = json.loads(run.publisher.artifacts["manifest.json"])
    assert attempt["termination_reason"] == "BUDGET_EXHAUSTED"
    assert "BUDGET_EXHAUSTED" in attempt["gap_codes"]
    assert (
        ledger["provider_http_exchange_count"],
        ledger["input_tokens"],
        ledger["output_tokens"],
    ) == (5, 393_217, 24_577)
    assert ledger["response_hash"] is None
    assert manifest["target_http_exchange_count"] >= 5
    assert manifest["target_input_tokens"] >= 393_217
    assert manifest["target_output_tokens"] >= 24_577
    assert unsafe.encode() not in b"".join(run.publisher.artifacts.values())


@pytest.mark.parametrize("location", ["assistant", "tool", "extra"])
def test_exact_target_secret_is_never_retained_but_safe_usage_is(
    tmp_path: Path, location: str
) -> None:
    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] != "turn" or request["turn_index"] != 1:
            return
        if location == "assistant":
            response["assistant_content"] = f"bounded {SECRET} disclosure"
        elif location == "tool":
            response["tool_events"] = [_safe_tool_event(arguments={"query": SECRET})]
        else:
            response["ignored_provider_extra"] = {"opaque": SECRET}

    run = invoke(tmp_path, response_mutator=mutate)
    ledger = _first_target_ledger(run)
    assert ledger["reason_code"] == "TARGET_PROTOCOL_ERROR"
    assert (
        ledger["provider_http_exchange_count"],
        ledger["input_tokens"],
        ledger["output_tokens"],
    ) == (1, 10, 5)
    assert ledger["response_hash"] is None
    assert SECRET.encode() not in b"".join(run.publisher.artifacts.values())


@pytest.mark.parametrize(
    "bad_cost",
    ["-1.000000", "1.0", "1.0000000", "NaN", "Infinity", 1.0, math.nan],
)
def test_invalid_target_reported_cost_is_protocol_error_and_never_retained(
    tmp_path: Path, bad_cost: Any
) -> None:
    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] == "turn" and request["turn_index"] == 1:
            response["usage"]["provider_reported_cost_usd"] = bad_cost

    run = invoke(tmp_path, response_mutator=mutate)
    attempt = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0]
    ledger = _first_target_ledger(run)
    assert attempt["termination_reason"] == "TARGET_PROTOCOL_ERROR"
    assert ledger["reason_code"] == "TARGET_PROTOCOL_ERROR"
    assert ledger["actual_cost_usd"] is None
    assert ledger["response_hash"] is None
    assert (
        ledger["provider_http_exchange_count"],
        ledger["input_tokens"],
        ledger["output_tokens"],
    ) == (1, 10, 5)


@pytest.mark.parametrize(
    "event",
    [
        _safe_tool_event(tool_event_id="bad id"),
        _safe_tool_event(ordinal=True),
        _safe_tool_event(status="UNKNOWN"),
        _safe_tool_event(reason_code="BAD_ON_SUCCESS"),
        _safe_tool_event(cached=1),
        _safe_tool_event(
            arguments={
                "level": {"a": {"b": {"c": {"d": {"e": {"f": {"g": {"h": 1}}}}}}}}
            }
        ),
        _safe_tool_event(result=list(range(101))),
        _safe_tool_event(arguments={1: "non-string key"}),
        _safe_tool_event(result={"oversized": "x" * 65_536}),
    ],
)
def test_target_tool_event_schema_and_bounds_fail_closed(
    tmp_path: Path, event: dict[str, Any]
) -> None:
    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] == "turn" and request["turn_index"] == 1:
            response["tool_events"] = [event]

    run = invoke(tmp_path, response_mutator=mutate)
    attempt = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0]
    assert attempt["termination_reason"] == "TARGET_PROTOCOL_ERROR"
    assert not run.publisher.artifacts["target_tool_events.jsonl"]
    assert _first_target_ledger(run)["response_hash"] is None


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["simulator"].update(
            endpoint="https://user:pass@synthetic.example/openai/v1"
        ),
        lambda value: value["simulator"].update(
            endpoint="https://synthetic.example:443/openai/v1"
        ),
        lambda value: value["simulator"].update(allowed_host="Synthetic.Example"),
        lambda value: value["simulator"].update(
            endpoint="https://bad_host/openai/v1", allowed_host="bad_host"
        ),
    ],
)
def test_simulator_endpoint_rejects_credentials_port_and_non_dns_host(
    tmp_path: Path, mutation: Any
) -> None:
    config = config_value()
    mutation(config)
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, config=config)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert (caught.value.reason_code, caught.value.exit_code) == (
        "SIMULATOR_ENDPOINT_REFUSED",
        4,
    )


def test_run_timeout_preserves_all_three_requested_slots_in_denominator(
    tmp_path: Path,
) -> None:
    clock = Clock([0, *([600_000_000_001] * 20)])
    run = invoke(tmp_path, clock=clock)
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert len(attempts) == 3
    assert [item["case_id"] for item in attempts] == list(
        config_value()["selected_case_ids"]
    )
    assert all(item["termination_reason"] == "RUN_TIMEOUT" for item in attempts)
    assert sum(item["reason_code"] == "RUN_TIMEOUT" for item in gaps) == 3
    assert run.result.attempted_episode_count == 3
    assert not run.target.launches
    assert not run.simulator.requests


@pytest.mark.parametrize(
    ("field_changes", "reason"),
    [
        ({"input_tokens": True}, "SIMULATOR_INVALID_RESPONSE"),
        ({"provider_http_exchange_count": -1}, "SIMULATOR_INVALID_RESPONSE"),
        ({"provider_reported_cost_usd": "1.0"}, "SIMULATOR_INVALID_RESPONSE"),
        ({"provider_reported_cost_usd": "NaN"}, "SIMULATOR_INVALID_RESPONSE"),
        ({"next_user_content": "bad\x00control"}, "SIMULATOR_INVALID_RESPONSE"),
        ({"next_user_content": "x" * 16_385}, "SIMULATOR_INVALID_RESPONSE"),
        ({"input_tokens": 9_007_199_254_740_992}, "SIMULATOR_INVALID_RESPONSE"),
        ({"input_tokens": 131_073}, "BUDGET_EXHAUSTED"),
    ],
)
def test_normalized_simulator_scalars_are_validated_before_hashing(
    tmp_path: Path, field_changes: dict[str, Any], reason: str
) -> None:
    module = api()

    class MutatingSimulator(Simulator):
        def complete(self, request: dict[str, Any]) -> Any:
            response = super().complete(request)
            return replace(response, **field_changes)

    simulator = MutatingSimulator(module)
    # Exercise the exact frozen seam with the mutating normalized response.
    from conftest import CapturePublisher, FixtureLoader, SourceVerifier, write_inputs

    inputs = write_inputs(tmp_path / "mutated")
    publisher = CapturePublisher()
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator=simulator,
        target_factory=TargetFactory(),
        clock=Clock(),
        environ={**ENVIRON, "LABS05_FAKE_API_KEY": SECRET},
        publisher=publisher,
        source_verifier=SourceVerifier(module),
        case_loader=FixtureLoader(module),
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    ledger = next(
        row
        for row in jsonl(publisher.artifacts["provider_ledger.jsonl"])
        if row["lane"] == "SIMULATOR"
    )
    assert ledger["reason_code"] == reason
    assert ledger["response_hash"] is None
    if reason == "BUDGET_EXHAUSTED":
        assert ledger["input_tokens"] == 131_073


def test_simulator_secret_is_redacted_while_observed_usage_is_retained(
    tmp_path: Path,
) -> None:
    module = api()

    class SecretSimulator(Simulator):
        def complete(self, request: dict[str, Any]) -> Any:
            response = super().complete(request)
            return replace(
                response,
                response_bytes=(response.response_bytes or b"") + SECRET.encode(),
                next_user_content=f"bounded {SECRET}",
                input_tokens=13,
                output_tokens=9,
            )

    from conftest import CapturePublisher, FixtureLoader, SourceVerifier, write_inputs

    inputs = write_inputs(tmp_path)
    publisher = CapturePublisher()
    module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        simulator=SecretSimulator(module),
        target_factory=TargetFactory(),
        clock=Clock(),
        environ={**ENVIRON, "LABS05_FAKE_API_KEY": SECRET},
        publisher=publisher,
        source_verifier=SourceVerifier(module),
        case_loader=FixtureLoader(module),
    )
    ledger = next(
        row
        for row in jsonl(publisher.artifacts["provider_ledger.jsonl"])
        if row["lane"] == "SIMULATOR"
    )
    assert (ledger["input_tokens"], ledger["output_tokens"]) == (13, 9)
    assert ledger["response_hash"] is None
    assert SECRET.encode() not in b"".join(publisher.artifacts.values())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda _request, response: response.update(turn_index=True),
        lambda _request, response: response.update(
            assistant_content="invalid\x00target text"
        ),
        lambda _request, response: response["usage"].update(
            input_tokens=9_007_199_254_740_992
        ),
        lambda _request, response: response.update(
            status="REFUSED",
            assistant_content="",
            reason_code="TARGET_PROVIDER_ERROR",
        ),
    ],
)
def test_target_global_scalar_and_status_reason_rules_fail_closed(
    tmp_path: Path, mutation: Any
) -> None:
    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] == "turn" and request["turn_index"] == 1:
            mutation(request, response)

    run = invoke(tmp_path, response_mutator=mutate)
    assert (
        jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0][
            "termination_reason"
        ]
        == "TARGET_PROTOCOL_ERROR"
    )
    assert _first_target_ledger(run)["response_hash"] is None


def test_close_counts_reject_bool_even_when_bool_equals_observed_integer(
    tmp_path: Path,
) -> None:
    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        if request["kind"] == "turn" and request["turn_index"] == 1:
            response.update(
                status="REFUSED",
                assistant_content="",
                reason_code="TARGET_REFUSAL",
            )
        elif request["kind"] == "close":
            response["provider_http_exchange_count"] = True
            response["tool_call_count"] = False

    run = invoke(tmp_path, response_mutator=mutate)
    attempt = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0]
    assert attempt["termination_reason"] == "TARGET_PROTOCOL_ERROR"
    assert "TARGET_PROTOCOL_ERROR" in attempt["gap_codes"]


def _initialize_git_checkout(path: Path) -> str:
    path.mkdir()
    subprocess.run(["git", "init", "-q", path], check=True)
    (path / "tracked.txt").write_text("synthetic\n")
    subprocess.run(["git", "-C", path, "add", "tracked.txt"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            path,
            "-c",
            "user.name=Triana Tests",
            "-c",
            "user.email=tests@example.invalid",
            "commit",
            "-qm",
            "synthetic fixture",
        ],
        check=True,
    )
    return subprocess.run(
        ["git", "-C", path, "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.mark.parametrize("race", ["argv", "adapter", "cwd"])
def test_target_launch_rechecks_verified_source_before_child_execution(
    tmp_path: Path, race: str
) -> None:
    module = api()
    process_module = __import__(
        "triana_labs.adaptive_runner.process", fromlist=["_register_source_snapshot"]
    )
    checkout = tmp_path / "checkout"
    head = _initialize_git_checkout(checkout)
    executable = Path(sys.executable)
    adapter = tmp_path / "adapter.py"
    adapter.write_text("raise SystemExit(99)\n")
    adapter_hash = (
        "sha256:" + __import__("hashlib").sha256(adapter.read_bytes()).hexdigest()
    )
    executable_hash = (
        "sha256:" + __import__("hashlib").sha256(executable.read_bytes()).hexdigest()
    )
    identity = module.TargetSourceIdentity(head, "sha256:" + "a" * 64, adapter_hash)
    cwd_info = checkout.lstat()
    process_module._register_source_snapshot(
        (identity.source_commit, identity.source_tree_hash, identity.adapter_file_hash),
        os.fspath(checkout),
        os.fspath(executable),
        os.fspath(adapter),
        (cwd_info.st_dev, cwd_info.st_ino),
        executable_hash,
        adapter_hash,
    )
    target = config_value()["target"]
    target["source_commit"] = head
    target["argv"] = [os.fspath(executable), os.fspath(adapter)]
    target["cwd"] = os.fspath(checkout)
    if race == "argv":
        alternate = tmp_path / "alternate.py"
        alternate.write_text("raise SystemExit(98)\n")
        target["argv"][1] = os.fspath(alternate)
    elif race == "adapter":
        adapter.write_text("raise SystemExit(97)\n")
    else:
        moved = tmp_path / "moved-checkout"
        checkout.rename(moved)
        checkout.mkdir()
    launch = module.TargetLaunch(
        "episode-race",
        "case-b2b9570f6e763ca0",
        target,
        config_value()["world"],
        "sha256:" + "b" * 64,
        identity,
        ENVIRON,
    )
    with pytest.raises(module.TargetProtocolFailure) as caught:
        module.JsonlTargetProcessFactory().start(launch)
    assert caught.value.reason_code == "TARGET_PROTOCOL_ERROR"
