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


def test_schema_describes_both_union_members_and_transport_projects_valid_emit_stop(
    monkeypatch: pytest.MonkeyPatch, legacy: object
) -> None:
    emit = proposal(user_utterance="Please continue with the verified request.")
    stop = proposal(
        disposition="STOP", user_utterance=None, stop_reason_code="GOAL_SATISFIED"
    )
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
    schema_text = json.dumps(schema).casefold()
    instruction = body["messages"][0]["content"].casefold()
    assert "emit" in schema_text and "nonempty" in schema_text and "null" in schema_text
    assert "stop" in schema_text and "declared" in schema_text
    assert "emit" in instruction and "stop" in instruction and "nonempty" in instruction
    assert (emitted.disposition, emitted.user_utterance, emitted.stop_reason_code) == (
        "EMIT",
        emit["user_utterance"],
        None,
    )
    assert (stopped.disposition, stopped.user_utterance, stopped.stop_reason_code) == (
        "STOP",
        None,
        "GOAL_SATISFIED",
    )


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
    ["not-json", '{"disposition":"EMIT","disposition":"STOP"}'],
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
        canonical({"disposition": "EMIT"}).decode(),
        canonical(
            {**proposal(), "PRIVATE_UNKNOWN_KEY": "PRIVATE_UNKNOWN_VALUE"}
        ).decode(),
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
        for key in ("disposition", "user_utterance", "stop_reason_code")
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
    payload = provider_envelope(canonical(proposal()).decode(), usage=usage)
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
