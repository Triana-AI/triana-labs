"""Provider-envelope conformance and stage-specific structural diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import (
    PROTOCOL,
    canonical,
    foundry_simulator,
    invoke_lab06,
    jsonl,
    proposal,
    provider_envelope,
)

DIAGNOSTIC_KEYS = {
    "diagnostic_version",
    "stage",
    "response_byte_count",
    "content_byte_count",
    "envelope_class",
    "content_class",
    "finish_reason_class",
    "known_field_presence",
    "missing_known_field_count",
    "unknown_field_count",
    "disposition_class",
    "user_utterance_class",
    "stop_reason_code_class",
}
USAGE = {"completion_tokens": 7, "prompt_tokens": 11}


def _first_structural_gap(run: object) -> dict:
    return next(
        row
        for row in jsonl(run.publisher.artifacts["gaps.jsonl"])
        if row["reason_code"] == "SIMULATOR_INVALID_RESPONSE"
    )


def _run_payload(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
) -> tuple[object, object]:
    simulator, opener = foundry_simulator(legacy, monkeypatch, [payload])
    run = invoke_lab06(tmp_path, legacy, simulator_override=simulator)
    return run, opener


def _wire(*, action: str = "EMIT", content: str = "Please continue.") -> dict:
    return {"action": action, "content": content}


def test_schema_is_exact_two_field_wire_and_transport_projects_emit_stop(
    monkeypatch: pytest.MonkeyPatch, legacy: object
) -> None:
    emit = _wire(content="Please continue with the verified request.")
    stop = _wire(action="STOP", content="GOAL_SATISFIED")
    simulator, opener = foundry_simulator(
        legacy,
        monkeypatch,
        [
            provider_envelope(canonical(emit).decode(), usage=USAGE),
            provider_envelope(canonical(stop).decode(), usage=USAGE),
        ],
    )
    request = {
        "protocol_version": PROTOCOL,
        "latest_observation": {"observation_hash": "sha256:" + "a" * 64},
    }
    emitted, stopped = simulator.complete(request), simulator.complete(request)
    body = json.loads(opener.requests[0].data)
    schema = body["response_format"]["json_schema"]["schema"]
    assert schema == {
        "additionalProperties": False,
        "properties": {
            "action": {"enum": ["EMIT", "STOP"], "type": "string"},
            "content": {"minLength": 1, "type": "string"},
        },
        "required": ["action", "content"],
        "type": "object",
    }
    assert (emitted.disposition, emitted.user_utterance, emitted.stop_reason_code) == (
        "EMIT",
        emit["content"],
        None,
    )
    assert (stopped.disposition, stopped.user_utterance, stopped.stop_reason_code) == (
        "STOP",
        None,
        stop["content"],
    )


def test_labs06_rejects_old_three_field_content_without_retry(
    monkeypatch: pytest.MonkeyPatch, legacy: object
) -> None:
    payload = provider_envelope(canonical(proposal()).decode(), usage=USAGE)
    simulator, opener = foundry_simulator(legacy, monkeypatch, [payload])
    response = simulator.complete(
        {
            "protocol_version": PROTOCOL,
            "latest_observation": {"observation_hash": "sha256:" + "a" * 64},
        }
    )
    assert len(opener.requests) == 1
    assert (response.status, response.reason_code) == (
        "INVALID",
        "SIMULATOR_INVALID_RESPONSE",
    )
    assert (
        response.disposition,
        response.user_utterance,
        response.stop_reason_code,
    ) == (None, None, None)


def test_labs05_provider_request_remains_byte_compatible(
    monkeypatch: pytest.MonkeyPatch, legacy: object
) -> None:
    request = {"latest_observation": {"synthetic": True}}
    content = {
        "consumed_observation_hash": "sha256:" + "a" * 64,
        "next_user_content": "bounded synthetic follow-up",
        "proposed_stop": False,
        "stop_reason": None,
    }
    simulator, opener = foundry_simulator(
        legacy,
        monkeypatch,
        [provider_envelope(canonical(content).decode(), usage=USAGE)],
    )
    response = simulator.complete(request)
    config = legacy.config_value()["simulator"]
    expected = canonical(
        {
            "messages": [
                {
                    "content": (
                        "LABS05_ADAPTIVE_USER_V1: react only to the latest bounded "
                        "evidence."
                    ),
                    "role": "system",
                },
                {"content": canonical(request).decode(), "role": "user"},
            ],
            "model": config["deployment"],
            "n": 1,
            "response_format": {
                "json_schema": {
                    "name": "next_user_turn",
                    "schema": {
                        "additionalProperties": False,
                        "properties": {
                            "consumed_observation_hash": {"type": "string"},
                            "next_user_content": {"type": "string"},
                            "proposed_stop": {"type": "boolean"},
                            "stop_reason": {"type": ["string", "null"]},
                        },
                        "required": [
                            "next_user_content",
                            "consumed_observation_hash",
                            "proposed_stop",
                            "stop_reason",
                        ],
                        "type": "object",
                    },
                    "strict": True,
                },
                "type": "json_schema",
            },
            "seed": config["seed"],
            "temperature": 0,
        }
    )
    assert response.status == "SUCCEEDED"
    assert opener.requests[0].data == expected


@pytest.mark.parametrize(
    ("payload", "detail"),
    [
        (b"not-json", "SIMULATOR_ENVELOPE_JSON_INVALID"),
        (b'{"choices":[],"choices":[]}', "SIMULATOR_ENVELOPE_JSON_INVALID"),
        (b"[]", "SIMULATOR_ENVELOPE_SHAPE_INVALID"),
        (b"{}", "SIMULATOR_ENVELOPE_SHAPE_INVALID"),
        (canonical({"choices": [{"message": {}}]}), "SIMULATOR_CONTENT_TYPE_INVALID"),
        (
            canonical({"choices": [{"message": {"content": 7}}]}),
            "SIMULATOR_CONTENT_TYPE_INVALID",
        ),
    ],
)
def test_envelope_json_shape_and_content_type_fail_at_exact_first_stage(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    payload: bytes,
    detail: str,
) -> None:
    run, _ = _run_payload(tmp_path, legacy, monkeypatch, payload)
    gap = _first_structural_gap(run)
    assert gap["detail_code"] == detail
    assert gap["diagnostic"]["stage"] == detail
    assert set(gap["diagnostic"]) == DIAGNOSTIC_KEYS


@pytest.mark.parametrize(
    "content",
    ["not-json", '{"action":"EMIT","action":"STOP"}'],
)
def test_invalid_or_duplicate_content_json_has_content_json_diagnostic(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    payload = provider_envelope(content, usage=USAGE)
    run, _ = _run_payload(tmp_path, legacy, monkeypatch, payload)
    gap = _first_structural_gap(run)
    diagnostic = gap["diagnostic"]
    assert gap["detail_code"] == "SIMULATOR_CONTENT_JSON_INVALID"
    assert diagnostic["content_byte_count"] == len(content.encode())
    assert diagnostic["content_class"] == "STRING"
    assert diagnostic["envelope_class"] == "CHAT_COMPLETION"


@pytest.mark.parametrize(
    "content",
    [
        "[]",
        canonical({"action": "EMIT"}).decode(),
        canonical({**_wire(), "PRIVATE_UNKNOWN_KEY": "PRIVATE_UNKNOWN_VALUE"}).decode(),
        canonical(
            {
                **proposal(),
                "speaker_role": "USER",
                "reaction_id": "legacy",
                "action_ids": [],
                "consumed_observation_hash": "sha256:" + "f" * 64,
            }
        ).decode(),
    ],
)
def test_nonobject_missing_extra_and_legacy_proposals_use_key_diagnostic_without_leak(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    payload = provider_envelope(content, usage=USAGE)
    run, _ = _run_payload(tmp_path, legacy, monkeypatch, payload)
    gap = _first_structural_gap(run)
    serialized = canonical(gap["diagnostic"])
    assert gap["detail_code"] == "SIMULATOR_CONTENT_KEYS_INVALID"
    assert b"PRIVATE_UNKNOWN" not in serialized
    assert gap["diagnostic"]["known_field_presence"] == {
        key: key in json.loads(content) if content.startswith("{") else False
        for key in ("action", "content")
    }


@pytest.mark.parametrize(
    ("usage", "valid"),
    [
        (None, True),
        ({"completion_tokens": 0, "prompt_tokens": 0}, True),
        ({"completion_tokens": 7}, False),
        ({"completion_tokens": 7, "prompt_tokens": True}, False),
        ({"completion_tokens": "7", "prompt_tokens": 11}, False),
        ({"completion_tokens": -1, "prompt_tokens": 11}, False),
    ],
)
def test_usage_missing_or_zero_is_supported_but_malformed_usage_is_typed_without_partial_count(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    usage: object,
    valid: bool,
) -> None:
    payload = provider_envelope(canonical(_wire()).decode(), usage=usage)
    if valid:
        simulator, _ = foundry_simulator(legacy, monkeypatch, [payload])
        result = simulator.complete(
            {
                "protocol_version": PROTOCOL,
                "latest_observation": {"observation_hash": "sha256:" + "a" * 64},
            }
        )
        assert result.status == "SUCCEEDED"
        assert (result.input_tokens, result.output_tokens) == (0, 0)
    else:
        run, _ = _run_payload(tmp_path, legacy, monkeypatch, payload)
        gap = _first_structural_gap(run)
        ledger = jsonl(run.publisher.artifacts["provider_ledger.jsonl"])
        sim = next(row for row in ledger if row["lane"] == "SIMULATOR")
        assert gap["detail_code"] == "SIMULATOR_USAGE_INVALID"
        assert (sim["input_tokens"], sim["output_tokens"]) == (0, 0)
