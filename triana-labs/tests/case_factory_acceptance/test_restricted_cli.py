"""Black-box CLI acceptance for the supported restricted Case Factory path."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import zipfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from conftest import PROJECT_ROOT, build_upstream, canonical, config_value, run_cli
from test_restricted_runtime_outcomes import (
    ScriptedRestrictedTransport,
    _clock,
    _field,
    _response,
    _submitted,
)

RESTRICTED_ENV = {
    "CUSTOM_FOUNDRY_ENDPOINT": "https://restricted.example.test/",
    "CUSTOM_FOUNDRY_KEY": "PRIVATE_RESTRICTED_KEY_123456789",
}
QUESTIONS = [
    {
        "question_id": "Q001",
        "question": "Which target behavior matters most?",
        "material_scope": "TARGET_RELEVANCE",
    }
]
ANSWERS = {"Q001": "Tool-use correctness; this resolves Q001 authoritatively."}
RESTRICTED_RECEIPT_KEYS = {
    "outcome",
    "reason_code",
    "manifest_path",
    "questions_path",
    "attempted_case_count",
    "valid_case_count",
    "distinct_case_count",
    "provider_call_count",
    "provider_http_exchange_count",
    "conservative_cost_usd",
}


def _restricted_value() -> dict[str, Any]:
    return {
        "artifact_kind": "case_factory_restricted_config",
        "schema_version": 1,
        "provider": {
            "provider_kind": "MICROSOFT_FOUNDRY_FIREWORKS",
            "deployment": "FW-GLM-5.2",
            "model_version": "1",
            "endpoint_env": "CUSTOM_FOUNDRY_ENDPOINT",
            "api_key_env": "CUSTOM_FOUNDRY_KEY",
            "secret_sentinel_envs": [],
            "request_timeout_seconds": 180,
        },
        "generation": {"candidate_count": 5},
        "budget": {
            "max_usd": "25.000000",
            "reservation_usd_per_agent_call": "2.000000",
        },
    }


def _write_config(
    root: Path, value: dict[str, Any] | None = None, *, raw: bytes | None = None
) -> Path:
    path = root / "restricted-config.json"
    path.write_bytes(
        raw if raw is not None else canonical(value or _restricted_value())
    )
    return path


def _invoke(cli: Any, capsys: pytest.CaptureFixture[str], *arguments: str) -> Any:
    try:
        exit_code = cli.main(list(arguments))
    except SystemExit as error:
        exit_code = error.code
    captured = capsys.readouterr()
    return SimpleNamespace(
        returncode=exit_code,
        stdout=captured.out.encode(),
        stderr=captured.err.encode(),
    )


def _json_line(payload: bytes) -> dict[str, Any]:
    assert payload.endswith(b"\n")
    assert payload.count(b"\n") == 1
    return json.loads(payload)


def _assert_pre_result_event(
    result: Any, *, command: str, reason: str, exit_code: int
) -> None:
    assert result.returncode == exit_code
    assert result.stdout == b""
    event = _json_line(result.stderr)
    duration = event.pop("duration_ms")
    assert isinstance(duration, int) and duration >= 0
    assert event == {
        "command": command,
        "event_name": f"triana.{command}.rejected",
        "outcome": "REJECTED",
        "reason_code": reason,
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "ERROR",
    }


def _assert_result_event(
    payload: bytes,
    *,
    command: str,
    suffix: str,
    outcome: str,
    reason: str | None,
    calls: int,
    exchanges: int,
    cost: str,
) -> None:
    event = _json_line(payload)
    duration = event.pop("duration_ms")
    assert isinstance(duration, int) and duration >= 0
    assert event == {
        "attempted_case_count": 5,
        "command": command,
        "conservative_cost_usd": cost,
        "distinct_case_count": 5 if outcome == "COMPLETED" else 0,
        "event_name": f"triana.{command}.{suffix}",
        "outcome": outcome,
        "provider_call_count": calls,
        "provider_http_exchange_count": exchanges,
        "reason_code": reason,
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "INFO",
        "valid_case_count": 5 if outcome == "COMPLETED" else 0,
    }


def _cli_module() -> Any:
    from triana_labs import cli

    return cli


def _install_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in RESTRICTED_ENV.items():
        monkeypatch.setenv(name, value)


def test_config_kind_dispatches_legacy_without_constructing_restricted_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    legacy = tmp_path / "legacy.json"
    legacy.write_bytes(canonical(config_value()))
    output = tmp_path / "legacy-output"
    cache = tmp_path / "legacy-cache"
    case_factory = __import__("triana_labs.case_factory", fromlist=["generate"])
    cli = _cli_module()
    calls: list[tuple[Any, ...]] = []

    def legacy_generate(*arguments: Any, **keywords: Any) -> Any:
        calls.append((*arguments, keywords))
        return SimpleNamespace(
            outcome="COMPLETED",
            reason_code=None,
            manifest_path=output / "manifest.json",
            attempted_case_count=5,
            valid_case_count=5,
            distinct_case_count=5,
            provider_call_count=3,
            conservative_cost_usd="1.000000",
        )

    monkeypatch.setattr(case_factory, "generate", legacy_generate)
    monkeypatch.setattr(
        cli,
        "_build_restricted_transport",
        lambda *_: pytest.fail("legacy dispatch constructed restricted transport"),
        raising=False,
    )
    result = _invoke(
        cli,
        capsys,
        "cases",
        "generate",
        os.fspath(observer),
        "--intelligence",
        os.fspath(intelligence),
        "--config",
        os.fspath(legacy),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    assert result.returncode == 0
    assert len(calls) == 1
    assert _json_line(result.stdout) == {
        "conservative_cost_usd": "1.000000",
        "distinct_case_count": 5,
        "manifest_path": os.fspath(output / "manifest.json"),
        "outcome": "COMPLETED",
        "provider_call_count": 3,
        "valid_case_count": 5,
    }


def test_restricted_generate_uses_validated_pinned_transport_and_config_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = _write_config(tmp_path)
    output = tmp_path / "restricted-output"
    cache = tmp_path / "restricted-cache"
    transport = ScriptedRestrictedTransport([_submitted] * 5)
    cli = _cli_module()
    _install_environment(monkeypatch)
    seen: list[tuple[dict[str, Any], dict[str, str]]] = []

    def build_transport(value: dict[str, Any], environ: Any) -> Any:
        seen.append((deepcopy(value), dict(environ)))
        return transport

    monkeypatch.setattr(
        cli, "_build_restricted_transport", build_transport, raising=False
    )
    result = _invoke(
        cli,
        capsys,
        "cases",
        "generate",
        os.fspath(observer),
        "--intelligence",
        os.fspath(intelligence),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    assert result.returncode == 0
    assert len(seen) == 1
    assert seen[0][0] == _restricted_value()
    assert seen[0][1]["CUSTOM_FOUNDRY_ENDPOINT"] == "https://restricted.example.test"
    assert [_field(request, "case_slots") for request in transport.requests] == [
        (f"case_{index}",) for index in range(1, 6)
    ]
    receipt = _json_line(result.stdout)
    assert set(receipt) == RESTRICTED_RECEIPT_KEYS
    assert receipt == {
        "attempted_case_count": 5,
        "conservative_cost_usd": "10.000000",
        "distinct_case_count": 5,
        "manifest_path": os.fspath(output / "manifest.json"),
        "outcome": "COMPLETED",
        "provider_call_count": 5,
        "provider_http_exchange_count": 5,
        "questions_path": None,
        "reason_code": None,
        "valid_case_count": 5,
    }
    _assert_result_event(
        result.stderr,
        command="cases.generate",
        suffix="completed",
        outcome="COMPLETED",
        reason=None,
        calls=5,
        exchanges=5,
        cost="10.000000",
    )


@pytest.mark.parametrize(
    ("payload", "environment", "reason"),
    [
        (
            b'{"artifact_kind":"unknown","private":"PRIVATE_CONFIG"}',
            {},
            "CONFIG_INVALID",
        ),
        (
            (
                b'{"artifact_kind":"case_factory_restricted_config",'
                b'"artifact_kind":"case_factory_config"}'
            ),
            {},
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "provider": {
                        **_restricted_value()["provider"],
                        "deployment": "PRIVATE_WRONG_MODEL",
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "generation": {"candidate_count": 10},
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "provider": {
                        **_restricted_value()["provider"],
                        "request_timeout_seconds": True,
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical({**_restricted_value(), "unknown": True}),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "provider": {
                        **_restricted_value()["provider"],
                        "unknown": "PRIVATE_UNKNOWN",
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical({**_restricted_value(), "schema_version": True}),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "budget": {
                        **_restricted_value()["budget"],
                        "max_usd": 25.0,
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "provider": {
                        **_restricted_value()["provider"],
                        "endpoint_env": "lowercase",
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (
            canonical(
                {
                    **_restricted_value(),
                    "provider": {
                        **_restricted_value()["provider"],
                        "secret_sentinel_envs": ["DUPLICATE", "DUPLICATE"],
                    },
                }
            ),
            RESTRICTED_ENV,
            "CONFIG_INVALID",
        ),
        (canonical(_restricted_value()), {}, "PROVIDER_CONFIGURATION_MISSING"),
        (
            canonical(_restricted_value()),
            {
                **RESTRICTED_ENV,
                "CUSTOM_FOUNDRY_ENDPOINT": "https://restricted.example.test/private",
            },
            "CONFIG_INVALID",
        ),
        (
            canonical(_restricted_value()),
            {
                **RESTRICTED_ENV,
                "CUSTOM_FOUNDRY_ENDPOINT": "http://restricted.example.test",
            },
            "CONFIG_INVALID",
        ),
        (
            canonical(_restricted_value()),
            {
                **RESTRICTED_ENV,
                "CUSTOM_FOUNDRY_ENDPOINT": "https://user@restricted.example.test",
            },
            "CONFIG_INVALID",
        ),
        (
            canonical(_restricted_value()),
            {
                **RESTRICTED_ENV,
                "CUSTOM_FOUNDRY_ENDPOINT": "https://restricted.example.test?private=1",
            },
            "CONFIG_INVALID",
        ),
        (
            canonical(_restricted_value()),
            {
                **RESTRICTED_ENV,
                "CUSTOM_FOUNDRY_ENDPOINT": "https://restricted.example.test:443",
            },
            "CONFIG_INVALID",
        ),
        (
            canonical(_restricted_value()),
            {**RESTRICTED_ENV, "CUSTOM_FOUNDRY_KEY": "   "},
            "PROVIDER_CONFIGURATION_MISSING",
        ),
    ],
    ids=(
        "unknown-kind",
        "duplicate-kind",
        "model-mismatch",
        "unsupported-count",
        "boolean-timeout",
        "unknown-root",
        "unknown-provider",
        "boolean-version",
        "float-money",
        "invalid-env-name",
        "duplicate-sentinels",
        "missing-environment",
        "endpoint-path",
        "endpoint-http",
        "endpoint-userinfo",
        "endpoint-query",
        "endpoint-port",
        "blank-key",
    ),
)
def test_restricted_config_and_environment_refuse_redacted_without_fallback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    payload: bytes,
    environment: dict[str, str],
    reason: str,
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = _write_config(tmp_path, raw=payload)
    cli = _cli_module()
    for name in RESTRICTED_ENV:
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    constructed: list[bool] = []
    monkeypatch.setattr(
        cli,
        "_build_restricted_transport",
        lambda *_: constructed.append(True),
        raising=False,
    )
    case_factory = __import__("triana_labs.case_factory", fromlist=["generate"])
    monkeypatch.setattr(
        case_factory,
        "generate",
        lambda *_args, **_kwargs: pytest.fail("restricted refusal fell back to legacy"),
    )
    private_output = tmp_path / "PRIVATE_RESTRICTED_OUTPUT"
    result = _invoke(
        cli,
        capsys,
        "cases",
        "generate",
        os.fspath(observer),
        "--intelligence",
        os.fspath(intelligence),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(tmp_path / "PRIVATE_RESTRICTED_CACHE"),
        "--out",
        os.fspath(private_output),
    )

    _assert_pre_result_event(
        result, command="cases.generate", reason=reason, exit_code=2
    )
    assert constructed == []
    assert not private_output.exists()
    for private in (
        b"PRIVATE_CONFIG",
        b"PRIVATE_WRONG_MODEL",
        b"PRIVATE_RESTRICTED_OUTPUT",
        RESTRICTED_ENV["CUSTOM_FOUNDRY_KEY"].encode(),
    ):
        assert private not in result.stderr


def test_needs_input_has_dedicated_receipt_event_and_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = _write_config(tmp_path)
    output = tmp_path / "paused"
    cache = tmp_path / "cache"
    response = _response("NEEDS_INPUT", questions=QUESTIONS)
    response.provider_http_exchange_count = 2
    transport = ScriptedRestrictedTransport([response])
    cli = _cli_module()
    _install_environment(monkeypatch)
    monkeypatch.setattr(
        cli, "_build_restricted_transport", lambda *_: transport, raising=False
    )

    result = _invoke(
        cli,
        capsys,
        "cases",
        "generate",
        os.fspath(observer),
        "--intelligence",
        os.fspath(intelligence),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    assert result.returncode == 11
    receipt = _json_line(result.stdout)
    assert set(receipt) == RESTRICTED_RECEIPT_KEYS
    assert receipt == {
        "attempted_case_count": 5,
        "conservative_cost_usd": "2.000000",
        "distinct_case_count": 0,
        "manifest_path": os.fspath(output / "manifest.json"),
        "outcome": "NEEDS_INPUT",
        "provider_call_count": 1,
        "provider_http_exchange_count": 2,
        "questions_path": os.fspath(output / "questions.json"),
        "reason_code": "MATERIAL_INPUT_REQUIRED",
        "valid_case_count": 0,
    }
    _assert_result_event(
        result.stderr,
        command="cases.generate",
        suffix="needs_input",
        outcome="NEEDS_INPUT",
        reason="MATERIAL_INPUT_REQUIRED",
        calls=1,
        exchanges=2,
        cost="2.000000",
    )


def test_terminal_restricted_rejection_has_receipt_event_and_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = _write_config(tmp_path)
    output = tmp_path / "rejected"
    cache = tmp_path / "cache"
    responses = []
    for _ in range(5):
        response = _response("FAILED", reason="PROVIDER_REFUSED")
        response.actual_cost_usd = None
        response.provider_http_exchange_count = 1
        responses.append(response)
    transport = ScriptedRestrictedTransport(responses)
    cli = _cli_module()
    _install_environment(monkeypatch)
    monkeypatch.setattr(
        cli, "_build_restricted_transport", lambda *_: transport, raising=False
    )

    result = _invoke(
        cli,
        capsys,
        "cases",
        "generate",
        os.fspath(observer),
        "--intelligence",
        os.fspath(intelligence),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    assert result.returncode == 8
    assert _json_line(result.stdout) == {
        "attempted_case_count": 5,
        "conservative_cost_usd": "10.000000",
        "distinct_case_count": 0,
        "manifest_path": os.fspath(output / "manifest.json"),
        "outcome": "REJECTED",
        "provider_call_count": 5,
        "provider_http_exchange_count": 5,
        "questions_path": None,
        "reason_code": "PROVIDER_REFUSED",
        "valid_case_count": 0,
    }
    _assert_result_event(
        result.stderr,
        command="cases.generate",
        suffix="rejected",
        outcome="REJECTED",
        reason="PROVIDER_REFUSED",
        calls=5,
        exchanges=5,
        cost="10.000000",
    )


def _pause(tmp_path: Path) -> tuple[Path, Path, Path]:
    from triana_labs.case_factory.restricted_runtime import generate_restricted

    observer, intelligence = build_upstream(tmp_path)
    config = _write_config(tmp_path)
    cache = tmp_path / "cache"
    output = tmp_path / "pause"
    response = _response("NEEDS_INPUT", questions=QUESTIONS)
    response.provider_http_exchange_count = 1
    generate_restricted(
        observer,
        intelligence,
        config,
        output,
        cache_path=cache,
        transport=ScriptedRestrictedTransport([response]),
        clock=_clock(),
        environ=RESTRICTED_ENV,
        requested_case_count=5,
    )
    return output, config, cache


def test_cases_resume_uses_exact_config_answers_and_cache_without_mutating_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paused, config, cache = _pause(tmp_path)
    answers = tmp_path / "answers.json"
    answers.write_bytes(canonical(ANSWERS))
    before = {path.name: path.read_bytes() for path in paused.iterdir()}
    transport = ScriptedRestrictedTransport([_submitted] * 5)
    cli = _cli_module()
    _install_environment(monkeypatch)
    monkeypatch.setattr(
        cli, "_build_restricted_transport", lambda *_: transport, raising=False
    )
    output = tmp_path / "resumed"

    result = _invoke(
        cli,
        capsys,
        "cases",
        "resume",
        os.fspath(paused / "manifest.json"),
        "--answers",
        os.fspath(answers),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    assert result.returncode == 0
    assert before == {path.name: path.read_bytes() for path in paused.iterdir()}
    assert len(transport.requests) == 5
    assert all(
        _field(request, "answers_authoritative") for request in transport.requests
    )
    assert all(
        _field(request, "answers")
        == [{"question_id": "Q001", "answer": ANSWERS["Q001"]}]
        for request in transport.requests
    )
    assert _json_line(result.stdout) == {
        "attempted_case_count": 5,
        "conservative_cost_usd": "12.000000",
        "distinct_case_count": 5,
        "manifest_path": os.fspath(output / "manifest.json"),
        "outcome": "COMPLETED",
        "provider_call_count": 6,
        "provider_http_exchange_count": 6,
        "questions_path": None,
        "reason_code": None,
        "valid_case_count": 5,
    }
    _assert_result_event(
        result.stderr,
        command="cases.resume",
        suffix="completed",
        outcome="COMPLETED",
        reason=None,
        calls=6,
        exchanges=6,
        cost="12.000000",
    )


@pytest.mark.parametrize(
    ("answers_payload", "config_mode", "cache_mode", "reason", "exit_code"),
    [
        (canonical({}), "same", "same", "RESUME_INPUT_INVALID", 2),
        (
            b'{"Q001":"first","Q001":"duplicate"}',
            "same",
            "same",
            "RESUME_INPUT_INVALID",
            2,
        ),
        (canonical({"Q001": 7}), "same", "same", "RESUME_INPUT_INVALID", 2),
        (
            canonical({**ANSWERS, "Q999": "PRIVATE_EXTRA"}),
            "same",
            "same",
            "RESUME_INPUT_INVALID",
            2,
        ),
        (canonical({"Q001": ""}), "same", "same", "RESUME_INPUT_INVALID", 2),
        (
            canonical({"Q001": "x" * 4097}),
            "same",
            "same",
            "RESUME_INPUT_INVALID",
            2,
        ),
        (canonical(ANSWERS), "reformatted", "same", "CONFIG_INVALID", 2),
        (canonical(ANSWERS), "wrong-kind", "same", "CONFIG_INVALID", 2),
        (
            canonical(ANSWERS),
            "same",
            "empty",
            "RESUME_STATE_UNAVAILABLE",
            5,
        ),
    ],
    ids=(
        "missing-answer",
        "duplicate-answer",
        "non-string-answer",
        "extra-answer",
        "empty-answer",
        "oversized-answer",
        "config-byte-mismatch",
        "wrong-config-kind",
        "private-state-unavailable",
    ),
)
def test_cases_resume_refuses_before_transport_and_redacts_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    answers_payload: bytes,
    config_mode: str,
    cache_mode: str,
    reason: str,
    exit_code: int,
) -> None:
    paused, config, cache = _pause(tmp_path)
    if config_mode == "reformatted":
        config.write_bytes(json.dumps(_restricted_value(), indent=2).encode())
    elif config_mode == "wrong-kind":
        config.write_bytes(canonical(config_value()))
    if cache_mode == "empty":
        cache = tmp_path / "empty-cache"
    answers = tmp_path / "PRIVATE_ANSWERS.json"
    answers.write_bytes(answers_payload)
    cli = _cli_module()
    _install_environment(monkeypatch)
    constructed: list[bool] = []
    monkeypatch.setattr(
        cli,
        "_build_restricted_transport",
        lambda *_: constructed.append(True),
        raising=False,
    )
    output = tmp_path / "PRIVATE_RESUME_OUTPUT"

    result = _invoke(
        cli,
        capsys,
        "cases",
        "resume",
        os.fspath(paused / "manifest.json"),
        "--answers",
        os.fspath(answers),
        "--config",
        os.fspath(config),
        "--cache-dir",
        os.fspath(cache),
        "--out",
        os.fspath(output),
    )

    _assert_pre_result_event(
        result, command="cases.resume", reason=reason, exit_code=exit_code
    )
    assert constructed == []
    assert not output.exists()
    assert b"PRIVATE_ANSWERS" not in result.stderr
    assert b"PRIVATE_RESUME_OUTPUT" not in result.stderr
    assert ANSWERS["Q001"].encode() not in result.stderr


def test_source_and_built_wheel_expose_identical_generate_and_resume_help(
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    built = subprocess.run(
        [
            uv,
            "build",
            "--project",
            os.fspath(PROJECT_ROOT),
            "--out-dir",
            os.fspath(dist),
        ],
        cwd=PROJECT_ROOT.parent,
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    wheel = next(dist.glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(installed)
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.fspath(installed)

    for command in ("generate", "resume"):
        source = run_cli("cases", command, "--help")
        packaged = subprocess.run(
            [sys.executable, "-m", "triana_labs", "cases", command, "--help"],
            cwd=tmp_path,
            env=environment,
            check=False,
            capture_output=True,
            timeout=30,
        )
        assert source.returncode == 0
        assert source.stderr == b""
        assert (source.returncode, source.stdout, source.stderr) == (
            packaged.returncode,
            packaged.stdout,
            packaged.stderr,
        )
    assert b"--answers" in run_cli("cases", "resume", "--help").stdout
