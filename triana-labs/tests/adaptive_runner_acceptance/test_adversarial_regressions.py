"""Focused post-candidate regressions for privacy, scalar, budget, and custody."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
import sys
import types
from dataclasses import replace
from pathlib import Path
from typing import Any, Self

import pytest
from conftest import (
    ENVIRON,
    FAKE_TARGET,
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
    [
        "-1.000000",
        "1.0",
        "1.0000000",
        "NaN",
        "Infinity",
        1.0,
        math.nan,
        pytest.param("1" * 16_378 + ".000000", id="oversized-decimal"),
    ],
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


@pytest.mark.parametrize(
    ("status", "reason", "termination"),
    [
        ("PROVIDER_FAILED", "PROVIDER_ERROR", "TARGET_PROVIDER_ERROR"),
        ("INTERNAL_FAILED", "TARGET_INTERNAL_FAILED", "TARGET_PROTOCOL_ERROR"),
    ],
)
def test_typed_target_failure_retains_executed_tool_custody_and_close_counts(
    tmp_path: Path, status: str, reason: str, termination: str
) -> None:
    event = _safe_tool_event()
    failed_episode_id: str | None = None

    def mutate(request: dict[str, Any], response: dict[str, Any]) -> None:
        nonlocal failed_episode_id
        if (
            request["kind"] == "turn"
            and request["turn_index"] == 1
            and failed_episode_id is None
        ):
            failed_episode_id = request["episode_id"]
            response.update(
                assistant_content="",
                reason_code=reason,
                status=status,
                tool_events=[event],
            )
        elif request["kind"] == "close" and request["episode_id"] == failed_episode_id:
            response["tool_call_count"] = 1

    run = invoke(tmp_path, response_mutator=mutate)
    attempts = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])
    attempt = attempts[0]
    tools = jsonl(run.publisher.artifacts["target_tool_events.jsonl"])
    manifest = json.loads(run.publisher.artifacts["manifest.json"])
    first_episode = run.target.launches[0].episode_id
    first_transcript = [
        item
        for item in jsonl(run.publisher.artifacts["transcripts.jsonl"])
        if item["episode_id"] == first_episode
    ]
    assert failed_episode_id == first_episode
    assert attempt["termination_reason"] == termination
    assert attempt["target_tool_call_count"] == 1
    assert len(tools) == 1
    assert {key: tools[0][key] for key in event} == event
    assert tools[0]["episode_id"] == first_episode
    assert tools[0]["assistant_turn_ordinal"] == 2
    assert tools[0]["target_protocol"] == config_value()["target"]["protocol"]
    assert tools[0]["target_source_commit"] == config_value()["target"]["source_commit"]
    assert tools[0]["world_hash"].startswith("sha256:")
    assert tools[0]["record_id"].startswith("target-tool-event-")
    assert manifest["target_tool_call_count"] >= 1
    assert not any(item["role"] == "ASSISTANT" for item in first_transcript)
    assert attempt["gap_codes"] == [termination]
    assert [item["termination_reason"] for item in attempts[1:]] == [
        "TURN_LIMIT_REACHED",
        "TURN_LIMIT_REACHED",
    ]
    assert all(item["status"] == "VALID" for item in attempts[1:])


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


@pytest.mark.parametrize("race", ["argv", "adapter", "cwd", "tracked"])
def test_target_launch_rechecks_verified_source_before_child_execution(
    tmp_path: Path, race: str
) -> None:
    module = api()
    process_module = __import__(
        "triana_labs.adaptive_runner.process", fromlist=["_register_source_snapshot"]
    )
    checkout = tmp_path / "checkout"
    head = _initialize_git_checkout(checkout)
    executable = tmp_path / "python-regular"
    interpreter = os.fspath(Path(sys.executable).resolve())
    assert '"' not in interpreter
    executable.write_text(f'#!/bin/sh\nexec "{interpreter}" "$@"\n')
    executable.chmod(0o755)
    adapter = tmp_path / "adapter.py"
    shutil.copy2(FAKE_TARGET, adapter)
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
    world = config_value()["world"]
    world_hash = "sha256:" + "b" * 64
    launch = module.TargetLaunch(
        "episode-race",
        "case-b2b9570f6e763ca0",
        target,
        world,
        world_hash,
        identity,
        ENVIRON,
    )
    hello = {
        "agent_model": target["agent_model"],
        "allowed_tools": world["allowed_tools"],
        "case_id": launch.case_id,
        "episode_id": launch.episode_id,
        "kind": "hello",
        "prompt_version": target["prompt_version"],
        "protocol": target["protocol"],
        "source_commit": target["source_commit"],
        "world_hash": world_hash,
        "world_kind": world["kind"],
    }
    control = module.JsonlTargetProcessFactory().start(launch)
    try:
        assert control.exchange(hello)["kind"] == "ready"
    finally:
        control.terminate()
    if race == "argv":
        alternate = tmp_path / "alternate.py"
        shutil.copy2(FAKE_TARGET, alternate)
        alternate.write_text(alternate.read_text() + "\n# different adapter identity\n")
        target["argv"][1] = os.fspath(alternate)
    elif race == "adapter":
        adapter.write_text("raise SystemExit(97)\n")
    elif race == "cwd":
        moved = tmp_path / "moved-checkout"
        checkout.rename(moved)
        checkout.mkdir()
    else:
        (checkout / "tracked.txt").write_text("mutated after verification\n")
    with pytest.raises(module.TargetProtocolFailure) as caught:
        module.JsonlTargetProcessFactory().start(launch)
    assert caught.value.reason_code == "TARGET_PROTOCOL_ERROR"


def test_config_regular_file_substitution_after_check_refuses_before_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from conftest import CapturePublisher, FixtureLoader, SourceVerifier, write_inputs

    module = api()
    inputs = write_inputs(tmp_path / "input-race")
    replacement = tmp_path / "replacement-config.json"
    replacement.write_bytes(inputs.config.read_bytes())
    original_is_symlink = Path.is_symlink
    swapped = False

    def check_then_swap(path: Path) -> bool:
        nonlocal swapped
        result = original_is_symlink(path)
        if path == inputs.config and not swapped:
            swapped = True
            path.unlink()
            path.symlink_to(replacement)
        return result

    monkeypatch.setattr(Path, "is_symlink", check_then_swap)
    target = TargetFactory()
    simulator = Simulator(module)
    with pytest.raises(module.AdaptiveRunFailure) as caught:
        module.run(
            inputs.manifest,
            inputs.review,
            inputs.config,
            inputs.output,
            simulator=simulator,
            target_factory=target,
            clock=Clock(),
            environ={**ENVIRON, "LABS05_FAKE_API_KEY": SECRET},
            publisher=CapturePublisher(),
            source_verifier=SourceVerifier(module),
            case_loader=FixtureLoader(module),
        )
    assert caught.value.reason_code == "CONFIG_INVALID"
    assert swapped
    assert not target.launches
    assert not simulator.requests


def test_cli_refuses_config_swap_between_transport_and_evidence_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from conftest import write_inputs

    import triana_labs.adaptive_runner as adaptive
    from triana_labs import cli

    inputs = write_inputs(tmp_path / "cli-input-race")
    replacement = tmp_path / "replacement-cli-config.json"
    changed = config_value()
    changed["target"]["argv"][-1] = "synthetic-equivalent-alternate-mode"
    replacement.write_bytes(
        json.dumps(changed, separators=(",", ":"), sort_keys=True).encode() + b"\n"
    )
    original_read = cli._read_bytes
    reads = 0

    def read_then_swap(path: Path, reason: str) -> bytes:
        nonlocal reads
        payload = original_read(path, reason)
        if path == inputs.config and reads == 0:
            reads += 1
            path.unlink()
            path.symlink_to(replacement)
        return payload

    invoked: list[bool] = []

    def forbidden_run(*args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        invoked.append(True)
        raise AssertionError("config substitution must refuse before execution")

    monkeypatch.setattr(cli, "_read_bytes", read_then_swap)
    monkeypatch.setattr(adaptive, "run", forbidden_run)
    monkeypatch.setenv("LABS05_FAKE_API_KEY", SECRET)
    result = cli._run_episodes(
        types.SimpleNamespace(
            manifest=str(inputs.manifest),
            review=str(inputs.review),
            config=str(inputs.config),
            out=str(inputs.output),
        )
    )
    captured = capsys.readouterr()
    assert result == 2
    assert not invoked
    assert '"reason_code":"CONFIG_INVALID"' in captured.err


@pytest.mark.parametrize("bad_usage", [True, "7", -1])
def test_foundry_transport_rejects_non_normalized_usage_without_network(
    monkeypatch: pytest.MonkeyPatch, bad_usage: Any
) -> None:
    module = api()
    boundaries = __import__(
        "triana_labs.adaptive_runner.boundaries", fromlist=["FoundrySimulatorTransport"]
    )
    response_value = {
        "consumed_observation_hash": "sha256:" + "a" * 64,
        "next_user_content": "bounded synthetic follow-up",
        "proposed_stop": False,
        "stop_reason": None,
    }
    envelope = {
        "choices": [{"message": {"content": json.dumps(response_value)}}],
        "usage": {"completion_tokens": 0, "prompt_tokens": bad_usage},
    }

    class Response:
        def __enter__(self) -> Self:
            return self

        def __exit__(self, *args: object) -> None:
            del args

        def read(self, limit: int) -> bytes:
            assert limit == 1_000_001
            return json.dumps(envelope).encode()

    class Opener:
        calls = 0

        def open(self, request: Any, *, timeout: int) -> Response:
            del request
            assert timeout == 180
            self.calls += 1
            return Response()

    opener = Opener()
    monkeypatch.setattr(boundaries.urllib.request, "build_opener", lambda *args: opener)
    result = boundaries.FoundrySimulatorTransport(
        config_value()["simulator"], SECRET
    ).complete({"latest_observation": {"synthetic": True}})
    assert opener.calls == 1
    assert result == module.SimulatorResponse(
        "INVALID",
        result.request_bytes,
        result.response_bytes,
        None,
        None,
        None,
        None,
        0,
        0,
        1,
        None,
        "SIMULATOR_INVALID_RESPONSE",
    )
