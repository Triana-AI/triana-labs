"""CLI, configuration, custody, endpoint, integrity, and egress refusals."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    ScriptedTransport,
    api,
    build_upstream,
    canonical,
    config_value,
    invoke,
    proposal_callback,
    request_user_value,
    run_cli,
    trace,
    write_config,
)


def assert_failure(call: Any, reason: str, exit_code: int) -> None:
    with pytest.raises(Exception) as caught:
        call()
    assert caught.value.__class__.__name__ == "GenerateFailure"
    assert caught.value.reason_code == reason
    assert caught.value.exit_code == exit_code


def invoke_preflight(
    tmp_path: Path,
    *,
    config: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
    traces: list[dict[str, Any]] | None = None,
) -> tuple[Any, ScriptedTransport, Path]:
    observer, intelligence = build_upstream(tmp_path, traces)
    path = write_config(tmp_path, config)
    generate_module, _ = api()
    transport = ScriptedTransport([])

    def call() -> Any:
        return generate_module.generate(
            observer,
            intelligence,
            path,
            tmp_path / "output",
            transport=transport,
            environ=environ or dict(ENVIRON),
        )

    return call, transport, tmp_path / "output"


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("generation", "seed"), 7),
        (("provider", "deployment"), "different"),
        (("provider", "model_name"), "different"),
        (("budget", "max_usd"), "8.699999"),
        (("budget", "conservative_input_usd_per_million_tokens"), None),
        (("authorization", "allow_provider_egress"), False),
    ],
)
def test_fixed_config_variants_refuse_before_provider(
    tmp_path: Path, path: tuple[str, str], value: Any
) -> None:
    config = config_value()
    if value is None:
        del config[path[0]][path[1]]
    else:
        config[path[0]][path[1]] = value
    call, transport, output = invoke_preflight(tmp_path, config=config)
    assert_failure(call, "CONFIG_INVALID", 2)
    assert transport.requests == []
    assert not output.exists()


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://operator.example.azure.com",
        "https://wrong.example.azure.com",
        "https://user@operator.example.azure.com",
        "https://operator.example.azure.com?private=1",
        "https://operator.example.azure.com/#private",
        "https://operator.example.azure.com:444",
    ],
)
def test_endpoint_variants_refuse_without_egress(tmp_path: Path, endpoint: str) -> None:
    environ = dict(ENVIRON)
    environ["AZURE_OPENAI_ENDPOINT"] = endpoint
    call, transport, output = invoke_preflight(tmp_path, environ=environ)
    assert_failure(call, "ENDPOINT_REFUSED", 4)
    assert transport.requests == []
    assert not output.exists()


@pytest.mark.parametrize(
    "missing", ["AZURE_OPENAI_API_KEY", "TRIANA_LABS04_SECRET_SENTINEL"]
)
def test_missing_or_malformed_named_secrets_are_config_invalid(
    tmp_path: Path, missing: str
) -> None:
    environ = dict(ENVIRON)
    del environ[missing]
    call, transport, output = invoke_preflight(tmp_path, environ=environ)
    assert_failure(call, "CONFIG_INVALID", 2)
    assert transport.requests == []
    assert not output.exists()


@pytest.mark.parametrize(
    "content",
    json.loads(
        (
            Path(__file__).parents[1] / "case_factory_fixtures" / "injection_texts.json"
        ).read_text()
    ),
)
def test_injection_is_data_but_credential_shapes_refuse_before_hash_or_call(
    tmp_path: Path, content: str
) -> None:
    traces = [
        trace("trace-alpha", content, "Safe response"),
        trace("trace-beta", "Ordinary request", "Safe response"),
    ]
    if "Ignore policy" in content:
        result, transport, _, _ = invoke(
            tmp_path,
            [proposal_callback(), lambda _: (401, b"stop")],
            traces=traces,
        )
        assert result.outcome == "COMPLETED_WITH_GAPS"
        evidence = request_user_value(transport.requests[0])["evidence"]
        assert content in canonical(evidence).decode()
    else:
        call, transport, output = invoke_preflight(tmp_path, traces=traces)
        assert_failure(call, "SECRET_SENTINEL_DETECTED", 4)
        assert transport.requests == []
        assert not output.exists()


def test_config_bytes_and_linked_manifest_integrity_are_closed(tmp_path: Path) -> None:
    observer, intelligence = build_upstream(tmp_path)
    generate_module, _ = api()
    config = tmp_path / "config.json"
    config.write_bytes(b'{"x":1,"x":2}\n')
    transport = ScriptedTransport([])
    assert_failure(
        lambda: generate_module.generate(
            observer,
            intelligence,
            config,
            tmp_path / "out",
            transport=transport,
            environ=ENVIRON,
        ),
        "CONFIG_INVALID",
        2,
    )
    manifest = json.loads(intelligence.read_bytes())
    manifest["input_manifest_hash"] = "sha256:" + "0" * 64
    intelligence.write_bytes(canonical(manifest, lf=True))
    write_config(tmp_path)
    assert_failure(
        lambda: generate_module.generate(
            observer,
            intelligence,
            tmp_path / "config.json",
            tmp_path / "other",
            transport=transport,
            environ=ENVIRON,
        ),
        "INTELLIGENCE_MISMATCH",
        5,
    )


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"\xef\xbb\xbf" + canonical(config_value()), id="bom"),
        pytest.param(canonical({**config_value(), "unknown": True}), id="unknown-root"),
        pytest.param(
            canonical(
                {
                    **config_value(),
                    "provider": {**config_value()["provider"], "unknown": "x"},
                }
            ),
            id="unknown-nested",
        ),
        pytest.param(
            canonical(
                {
                    **config_value(),
                    "generation": {
                        **config_value()["generation"],
                        "candidate_count": 5.0,
                    },
                }
            ),
            id="float",
        ),
        pytest.param(
            canonical(config_value()).replace(
                b'"candidate_count":5', b'"candidate_count":NaN'
            ),
            id="nonfinite",
        ),
    ],
)
def test_config_bom_unknown_fields_float_and_nonfinite_refuse_before_egress(
    tmp_path: Path, payload: bytes
) -> None:
    observer, intelligence = build_upstream(tmp_path)
    config = tmp_path / "strict-config.json"
    config.write_bytes(payload + (b"" if payload.endswith(b"\n") else b"\n"))
    generate_module, _ = api()
    transport = ScriptedTransport([])
    assert_failure(
        lambda: generate_module.generate(
            observer,
            intelligence,
            config,
            tmp_path / "strict-output",
            transport=transport,
            environ=ENVIRON,
        ),
        "CONFIG_INVALID",
        2,
    )
    assert transport.requests == []
    assert not (tmp_path / "strict-output").exists()


def test_cli_help_usage_and_paths_are_safe(tmp_path: Path) -> None:
    help_result = run_cli("cases", "generate", "--help")
    assert help_result.returncode == 0
    assert help_result.stderr == b""
    private = "PRIVATE_CLI_VALUE"
    usage = run_cli("cases", "generate", private)
    assert usage.returncode == 2
    assert usage.stdout == b""
    assert private.encode() not in usage.stderr
