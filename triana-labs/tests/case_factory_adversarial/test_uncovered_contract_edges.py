"""Adversarial checks for explicitly frozen LABS-04 edge clauses."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def _acceptance_helpers() -> ModuleType:
    path = Path(__file__).parents[1] / "case_factory_acceptance" / "conftest.py"
    spec = importlib.util.spec_from_file_location("labs04_edge_helpers", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("acceptance helper module is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


HELPERS = _acceptance_helpers()


def _failure(
    tmp_path: Path,
    *,
    config: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
) -> tuple[Any, Any, Path]:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport([(400, b"unexpected-egress")])
    output = tmp_path / "case-factory"
    with pytest.raises(generate_module.GenerateFailure) as caught:
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path, config),
            output,
            transport=transport,
            environ=environ or dict(HELPERS.ENVIRON),
        )
    return caught.value, transport, output


def test_publication_target_is_absent_until_atomic_rename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, provider = HELPERS.api()
    target_existed_at_rename: list[bool] = []
    real_rename = Path.rename

    def observe_rename(source: Path, target: Path) -> Path:
        target_existed_at_rename.append(target.exists())
        return real_rename(source, target)

    monkeypatch.setattr(Path, "rename", observe_rename)
    output = tmp_path / "published"
    provider.AtomicPublisher().publish(output, {"manifest.json": b"{}\n"})

    assert target_existed_at_rename == [False]
    assert output.is_dir()


def test_swapped_publication_claim_is_never_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, provider = HELPERS.api()
    output = tmp_path / "published"
    real_rename = Path.rename
    swapped_inode: int | None = None

    def swap_claim_then_rename(source: Path, target: Path) -> Path:
        nonlocal swapped_inode
        if target.exists():
            target.rmdir()
            target.mkdir()
            swapped_inode = target.stat().st_ino
        return real_rename(source, target)

    monkeypatch.setattr(Path, "rename", swap_claim_then_rename)
    failure: Any = None
    try:
        provider.AtomicPublisher().publish(output, {"manifest.json": b"{}\n"})
    except provider.PublicationFailure as error:
        failure = error

    if swapped_inode is None:
        assert failure is None
        assert (output / "manifest.json").read_bytes() == b"{}\n"
    else:
        assert isinstance(failure, provider.PublicationFailure)
        assert failure.cleanup_failed is False
        assert output.stat().st_ino == swapped_inode
        assert list(output.iterdir()) == []


def _large_valid_trace() -> dict[str, Any]:
    trace = HELPERS.trace("trace-large", "Need help", "Initial response")
    prefix = trace["events"][:4]
    assistants = [
        {
            "sequence": 4 + index,
            "event_kind": "ASSISTANT_MESSAGE",
            "content": "a",
            "is_final": index == 715,
        }
        for index in range(716)
    ]
    terminal = dict(trace["events"][-1], sequence=720)
    trace["events"] = [*prefix, *assistants, terminal]
    return trace


def test_oversized_propose_request_refuses_as_evidence_too_large(
    tmp_path: Path,
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path, [_large_valid_trace()])
    generate_module, _ = HELPERS.api()
    evidence, citations, _, _ = generate_module.build_evidence(observer, intelligence)
    schema = json.loads((generate_module.SCHEMAS / "proposal.schema.json").read_bytes())
    current_body = generate_module._request(
        "PROPOSE", {"evidence": evidence, "citations": citations}, schema
    )
    envelope = json.loads(current_body)
    envelope["max_tokens"] = 12000
    amended_body = HELPERS.canonical(envelope)
    assert len(amended_body) == 240_055
    transport = HELPERS.ScriptedTransport([])
    output = tmp_path / "case-factory"

    with pytest.raises(generate_module.GenerateFailure) as caught:
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            output,
            transport=transport,
            environ=HELPERS.ENVIRON,
        )

    assert (caught.value.reason_code, caught.value.exit_code) == (
        "EVIDENCE_TOO_LARGE",
        3,
    )
    assert transport.requests == []
    assert not output.exists()


def test_exact_api_key_in_ignored_response_field_is_secret_detected(
    tmp_path: Path,
) -> None:
    api_key = "Q7vN2mL9pX4z"
    environ = {**HELPERS.ENVIRON, "AZURE_OPENAI_API_KEY": api_key}

    def leaking_critique(_request: Any) -> tuple[int, bytes]:
        response = json.loads(HELPERS.azure_body({"issues": []}))
        response["provider_note"] = api_key
        return 200, HELPERS.canonical(response)

    publisher = HELPERS.CapturePublisher()
    result, transport, _, _ = HELPERS.invoke(
        tmp_path,
        [HELPERS.proposal_callback(), leaking_critique, (400, b"unused")],
        environ=environ,
        publisher=publisher,
    )

    assert result.reason_code == "CRITIQUE_UNAVAILABLE"
    assert len(transport.requests) == 2
    assert publisher.artifacts is not None
    attempts = [
        json.loads(line)
        for line in publisher.artifacts["generation_attempts.jsonl"].splitlines()
    ]
    assert attempts[1]["status"] == "INVALID_RESPONSE"
    assert attempts[1]["reason_code"] == "PROVIDER_RESPONSE_SECRET_DETECTED"
    assert attempts[1]["response_hash"] is None


@pytest.mark.parametrize(
    ("config_mutation", "environment_mutation"),
    [
        pytest.param(
            lambda config: config["provider"].update(
                secret_sentinel_envs=["invalid sentinel name"]
            ),
            lambda environment: environment.update(
                {"invalid sentinel name": "VALID_SENTINEL_VALUE"}
            ),
            id="sentinel-name-not-safe-id",
        ),
        pytest.param(
            lambda _config: None,
            lambda environment: environment.update(
                {"AZURE_OPENAI_API_KEY": "VALIDKEY\nCONTROL"}
            ),
            id="api-key-control",
        ),
        pytest.param(
            lambda _config: None,
            lambda environment: environment.update(
                {"TRIANA_LABS04_SECRET_SENTINEL": "VALIDSENTINEL\tCONTROL"}
            ),
            id="sentinel-value-control",
        ),
    ],
)
def test_invalid_secret_configuration_refuses_before_provider(
    tmp_path: Path,
    config_mutation: Any,
    environment_mutation: Any,
) -> None:
    config = HELPERS.config_value()
    environ = dict(HELPERS.ENVIRON)
    config_mutation(config)
    environment_mutation(environ)

    error, transport, output = _failure(tmp_path, config=config, environ=environ)

    assert (error.reason_code, error.exit_code) == ("CONFIG_INVALID", 2)
    assert transport.requests == []
    assert not output.exists()


@pytest.mark.parametrize(
    "host",
    [
        pytest.param("operator..example.com", id="consecutive-dots"),
        pytest.param(f"{'a' * 64}.example.com", id="overlong-label"),
    ],
)
def test_malformed_lowercase_dns_host_is_config_invalid(
    tmp_path: Path, host: str
) -> None:
    config = HELPERS.config_value()
    config["provider"]["allowed_endpoint_host"] = host
    environ = {
        **HELPERS.ENVIRON,
        "AZURE_OPENAI_ENDPOINT": f"https://{host}",
    }

    error, transport, output = _failure(tmp_path, config=config, environ=environ)

    assert (error.reason_code, error.exit_code) == ("CONFIG_INVALID", 2)
    assert transport.requests == []
    assert not output.exists()


def test_interrupt_before_valid_propose_publishes_nothing(tmp_path: Path) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport([KeyboardInterrupt()])
    publisher = HELPERS.CapturePublisher()
    output = tmp_path / "case-factory"

    with pytest.raises(KeyboardInterrupt):
        generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            output,
            transport=transport,
            environ=HELPERS.ENVIRON,
            publisher=publisher,
        )

    assert len(transport.requests) == 1
    assert publisher.artifacts is None
    assert not output.exists()


def test_interrupt_during_critique_publishes_control_only_partial(
    tmp_path: Path,
) -> None:
    observer, intelligence = HELPERS.build_upstream(tmp_path)
    generate_module, _ = HELPERS.api()
    transport = HELPERS.ScriptedTransport(
        [HELPERS.proposal_callback(), KeyboardInterrupt()]
    )
    publisher = HELPERS.CapturePublisher()

    try:
        result = generate_module.generate(
            observer,
            intelligence,
            HELPERS.write_config(tmp_path),
            tmp_path / "case-factory",
            transport=transport,
            environ=HELPERS.ENVIRON,
            publisher=publisher,
        )
    except KeyboardInterrupt as error:
        raise AssertionError(
            "post-PROPOSE interrupt escaped without finalization"
        ) from error

    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "INTERRUPTED"
    assert len(transport.requests) == 2
    assert publisher.artifacts is not None
    assert publisher.artifacts["control_case_candidates.jsonl"]
    assert publisher.artifacts["case_candidates.jsonl"] == b""
