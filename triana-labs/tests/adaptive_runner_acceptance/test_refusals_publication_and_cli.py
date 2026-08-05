"""Pre-egress refusal, atomic custody, interruption, CLI, and redaction."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    ENVIRON,
    OUTPUT_NAMES,
    PROJECT_ROOT,
    CapturePublisher,
    Clock,
    FixtureLoader,
    Simulator,
    SourceVerifier,
    TargetFactory,
    api,
    config_value,
    executable_config_value,
    invoke,
    jsonl,
    review_value,
    run_cli,
    write_inputs,
)
from test_target_connector_v1 import _http_config

CANARY_PRIVACY = "OWNER_AUTHORIZED_REAL_DATA_CANARY"
CANARY_TARGET_CLASS = "OWNER_AUTHORIZED_REAL_TARGET"
CANARY_TARGET_HOST = "3-6-37-142.sslip.io"
CANARY_SIMULATOR_HOST = "kairos-openai-1.openai.azure.com"


def call_run(
    tmp_path: Path,
    *,
    review: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    environ: dict[str, str] | None = None,
    publisher: Any = None,
    verifier_fail: bool = False,
    default_publisher: bool = False,
) -> tuple[Any, Any, Any, Any]:
    module = api()
    inputs = write_inputs(tmp_path, review=review, config=config)
    simulator = Simulator(module)
    target = TargetFactory()
    loader = FixtureLoader(module)
    verifier = SourceVerifier(module, fail=verifier_fail)
    kwargs = {
        "simulator": simulator,
        "target_factory": target,
        "clock": Clock(),
        "environ": dict(
            environ or {**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"}
        ),
        "source_verifier": verifier,
        "case_loader": loader,
    }
    if not default_publisher:
        kwargs["publisher"] = publisher or CapturePublisher()
    result = module.run(
        inputs.manifest,
        inputs.review,
        inputs.config,
        inputs.output,
        **kwargs,
    )
    return result, inputs, simulator, target


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda value: value.update(privacy_class="REAL"), "UNSUPPORTED_PRIVACY_CLASS"),
        (
            lambda value: value["target"].update(
                fallback={"connector_kind": "HTTP_JSON_V1"}
            ),
            "TARGET_CONNECTOR_CONFIG_INVALID",
        ),
        (
            lambda value: value.update(persistent_memory={"enabled": True}),
            "CONFIG_INVALID",
        ),
        (
            lambda value: value["simulator"].update(
                endpoint="https://other.example/openai/v1"
            ),
            "SIMULATOR_ENDPOINT_REFUSED",
        ),
        (
            lambda value: value["budget"].update(all_http_exchanges=41),
            "CONFIG_INVALID",
        ),
    ],
)
def test_config_expansion_and_egress_mismatch_refuse_before_any_boundary_call(
    tmp_path: Path, mutation: Any, reason: str
) -> None:
    value = config_value()
    mutation(value)
    with pytest.raises(Exception) as caught:
        call_run(tmp_path, config=value)
    failure = caught.value
    assert failure.__class__.__name__ == "AdaptiveRunFailure"
    assert (failure.reason_code, failure.exit_code) == (
        reason,
        4 if reason.startswith(("UNSUPPORTED", "SIMULATOR")) else 2,
    )
    assert not (tmp_path / "output").exists()


def test_review_must_be_complete_human_pass_and_never_software_repaired(
    tmp_path: Path,
) -> None:
    review = review_value()
    review["cases"][0]["adaptive_multi_turn"] = False
    with pytest.raises(Exception) as caught:
        call_run(tmp_path, review=review)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert (caught.value.reason_code, caught.value.exit_code) == (
        "REVIEW_NOT_ACCEPTED",
        4,
    )
    assert not (tmp_path / "output").exists()


def test_missing_simulator_secret_and_target_source_mismatch_refuse_pre_egress(
    tmp_path: Path,
) -> None:
    with pytest.raises(Exception) as missing:
        call_run(tmp_path / "missing", environ=dict(ENVIRON))
    assert missing.value.reason_code == "SIMULATOR_AUTHORIZATION_REFUSED"
    assert missing.value.exit_code == 4

    with pytest.raises(Exception) as source:
        call_run(
            tmp_path / "source",
            config=executable_config_value(),
            verifier_fail=True,
        )
    assert source.value.reason_code == "TARGET_SOURCE_MISMATCH"
    assert source.value.exit_code == 4


def test_default_publisher_is_atomic_no_replace_and_leaves_no_staging(
    tmp_path: Path,
) -> None:
    result, inputs, _, _ = call_run(tmp_path, default_publisher=True)
    assert result.exit_code == 0
    assert {path.name for path in inputs.output.iterdir()} == OUTPUT_NAMES
    assert not list(tmp_path.glob(".*output*"))

    with pytest.raises(Exception) as caught:
        module = api()
        module.run(
            inputs.manifest,
            inputs.review,
            inputs.config,
            inputs.output,
            simulator=Simulator(module),
            target_factory=TargetFactory(),
            clock=Clock(),
            environ={**ENVIRON, "LABS05_FAKE_API_KEY": "secret"},
            source_verifier=SourceVerifier(module),
            case_loader=FixtureLoader(module),
        )
    assert (caught.value.reason_code, caught.value.exit_code) == (
        "OUTPUT_ALREADY_EXISTS",
        2,
    )


def test_publication_failure_is_closed_and_redacts_exception(tmp_path: Path) -> None:
    publisher = CapturePublisher(failure=OSError("PRIVATE path secret exception"))
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, publisher=publisher)
    assert caught.value.__class__.__name__ == "AdaptiveRunFailure"
    assert (caught.value.reason_code, caught.value.exit_code) == (
        "OUTPUT_WRITE_FAILED",
        7,
    )
    assert not (tmp_path / "output").exists()


def test_post_boundary_interrupt_publishes_only_observed_partial_custody(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path, target_modes=("interrupt", "success", "success"))
    assert run.result.exit_code == 130
    assert run.result.reason_code == "INTERRUPTED"
    assert run.result.outcome == "COMPLETED_WITH_GAPS"
    assert len(run.target.sessions) == 1
    assert run.target.sessions[0].terminate_count == 1
    gaps = jsonl(run.publisher.artifacts["gaps.jsonl"])
    assert "INTERRUPTED" in {gap["reason_code"] for gap in gaps}
    transcripts = jsonl(run.publisher.artifacts["transcripts.jsonl"])
    assert [record["ordinal"] for record in transcripts] == [1]
    payload = b"".join(run.publisher.artifacts.values())
    assert b"PRIVATE" not in payload


def test_human_adaptation_review_is_pending_six_items_and_unfilled(
    tmp_path: Path,
) -> None:
    run = invoke(tmp_path)
    review = json.loads(run.publisher.artifacts["human_adaptation_review.json"])
    assert review["rubric_version"] == "LABS05_ADAPTATION_V1"
    assert review["review_state"] == "PENDING"
    assert len(review["review_items"]) == 6
    assert {item["user_turn_ordinal"] for item in review["review_items"]} == {3, 5}
    assert all(item["materially_reacts"] is None for item in review["review_items"])
    assert all(item["notes"] is None for item in review["review_items"])


def test_cli_rejects_tampered_case_input_without_leaking_paths_or_secrets(
    tmp_path: Path,
) -> None:
    inputs = write_inputs(tmp_path)
    secret_output = tmp_path / "PRIVATE_OUTPUT_SECRET"
    completed = run_cli(
        "episodes",
        "run",
        inputs.manifest,
        "--review",
        inputs.review,
        "--config",
        inputs.config,
        "--out",
        secret_output,
    )
    assert completed.returncode == 4
    assert completed.stdout == b""
    lines = completed.stderr.splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["command"] == "episodes.run"
    assert event["reason_code"] in {"MANIFEST_INVALID", "CASE_INTEGRITY_FAILED"}
    for private in (
        str(tmp_path).encode(),
        b"PRIVATE_OUTPUT_SECRET",
        b"PRIVATE_SIMULATOR_SECRET",
        b"synthetic.example",
    ):
        assert private not in completed.stderr
    assert not secret_output.exists()


def test_cli_usage_is_one_redacted_terminal_event() -> None:
    completed = run_cli("episodes", "run", "PRIVATE_ARG_SECRET")
    assert completed.returncode == 2
    assert completed.stdout == b""
    lines = completed.stderr.splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["command"] == "episodes.run"
    assert event["reason_code"] == "CLI_USAGE_ERROR"
    assert b"PRIVATE_ARG_SECRET" not in completed.stderr


def _canary_config() -> dict[str, Any]:
    value = _http_config(f"https://{CANARY_TARGET_HOST}")
    value["privacy_class"] = CANARY_PRIVACY
    value["target"].update(
        allowed_host=CANARY_TARGET_HOST, data_class=CANARY_TARGET_CLASS
    )
    value["target"]["session"]["create"]["constant_json"]["client_id"] = (
        "client-techcorp"
    )
    value["target"]["turn"]["operation"]["constant_json"]["client_id"] = (
        "client-techcorp"
    )
    value["simulator"].update(
        allowed_host=CANARY_SIMULATOR_HOST,
        deployment="FW-GLM-5.2",
        endpoint=f"https://{CANARY_SIMULATOR_HOST}/openai/v1",
        provider_kind="MICROSOFT_FOUNDRY_FIREWORKS",
    )
    return value


def _run_canary(
    tmp_path: Path, config: dict[str, Any], output: Path | None = None
) -> tuple[Any, Any, Any, Any, Any]:
    module = api()
    inputs = write_inputs(tmp_path, config=config)
    simulator, target, publisher = (
        Simulator(module),
        TargetFactory(),
        CapturePublisher(),
    )
    result = failure = None
    try:
        result = module.run(
            inputs.manifest,
            inputs.review,
            inputs.config,
            output or inputs.output,
            simulator=simulator,
            target_factory=target,
            clock=Clock(),
            environ={**ENVIRON, "LABS05_FAKE_API_KEY": "PRIVATE_SIMULATOR_SECRET"},
            publisher=publisher,
            source_verifier=SourceVerifier(module),
            case_loader=FixtureLoader(module),
        )
    except module.AdaptiveRunFailure as caught:
        failure = caught
    return result, failure, simulator, target, publisher


def _assert_canary_pre_egress(run: tuple[Any, Any, Any, Any, Any]) -> None:
    _, failure, simulator, target, publisher = run
    assert failure is not None
    assert failure.__class__.__name__ == "AdaptiveRunFailure"
    assert not simulator.requests
    assert not target.launches
    assert not publisher.calls


def test_exact_real_data_canary_propagates_truthful_private_lineage(
    tmp_path: Path,
) -> None:
    output = Path("/private/tmp") / f"labs05-canary-{tmp_path.name}"
    result, failure, _, _, publisher = _run_canary(tmp_path, _canary_config(), output)
    assert failure is None
    assert result.outcome == "COMPLETED"
    assert publisher.calls[0][0] == output
    assert all(b"SYNTHETIC" not in item for item in publisher.artifacts.values())
    for name, payload in publisher.artifacts.items():
        records = [json.loads(payload)] if name.endswith(".json") else jsonl(payload)
        assert all(record["privacy_class"] == CANARY_PRIVACY for record in records)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["target"].update(data_class="SYNTHETIC_LOCAL_TARGET"),
        lambda value: value.update(privacy_class="SYNTHETIC"),
        lambda value: value.update(target=executable_config_value()["target"]),
        lambda value: value["target"].update(
            allowed_host="other.example", base_url="https://other.example"
        ),
        lambda value: value["target"].update(base_url=f"http://{CANARY_TARGET_HOST}"),
        lambda value: value["target"]["session"]["create"]["constant_json"].update(
            client_id="other-client"
        ),
        lambda value: value["simulator"].update(
            allowed_host="other.example", endpoint="https://other.example/openai/v1"
        ),
        lambda value: value["simulator"].update(provider_kind="OTHER_PROVIDER"),
        lambda value: value["simulator"].update(deployment="OTHER_DEPLOYMENT"),
    ],
)
def test_real_canary_mismatch_refuses_before_provider_egress(
    tmp_path: Path, mutation: Any
) -> None:
    config = _canary_config()
    mutation(config)
    _assert_canary_pre_egress(_run_canary(tmp_path, config))


@pytest.mark.parametrize(
    "output",
    [PROJECT_ROOT / "real-canary-output", Path("/Users/Shared/real-canary-output")],
)
def test_real_canary_repository_or_public_output_refuses_pre_egress(
    tmp_path: Path, output: Path
) -> None:
    _assert_canary_pre_egress(_run_canary(tmp_path, _canary_config(), output))
