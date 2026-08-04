"""Typed hard semantic gates and one-attempt custody."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import (
    canonical,
    foundry_simulator,
    invoke_lab06,
    jsonl,
    proposal,
    provider_envelope,
)


def _episode_evidence(run: object) -> tuple[list[dict], list[dict], list[dict]]:
    episode_id = run.target.launches[0].episode_id
    return tuple(
        [
            row
            for row in jsonl(run.publisher.artifacts[name])
            if row["episode_id"] == episode_id
        ]
        for name in ("transcripts.jsonl", "provider_ledger.jsonl", "gaps.jsonl")
    )


@pytest.mark.parametrize(
    ("raw", "detail"),
    [
        (proposal(disposition=7), "SIMULATOR_DISPOSITION_INVALID"),
        (proposal(disposition="PAUSE"), "SIMULATOR_DISPOSITION_INVALID"),
        (proposal(user_utterance=None), "SIMULATOR_EMIT_FIELDS_INVALID"),
        (proposal(user_utterance=""), "SIMULATOR_EMIT_FIELDS_INVALID"),
        (proposal(user_utterance="unsafe\u0001text"), "SIMULATOR_EMIT_FIELDS_INVALID"),
        (proposal(user_utterance="x" * 16_385), "SIMULATOR_EMIT_FIELDS_INVALID"),
        (proposal(stop_reason_code="GOAL_SATISFIED"), "SIMULATOR_EMIT_FIELDS_INVALID"),
        (
            proposal(
                disposition="STOP",
                user_utterance="no",
                stop_reason_code="GOAL_SATISFIED",
            ),
            "SIMULATOR_STOP_FIELDS_INVALID",
        ),
        (
            proposal(disposition="STOP", user_utterance=None, stop_reason_code=None),
            "SIMULATOR_STOP_FIELDS_INVALID",
        ),
        (
            proposal(disposition="STOP", user_utterance=None, stop_reason_code=""),
            "SIMULATOR_STOP_FIELDS_INVALID",
        ),
        (
            proposal(
                disposition="STOP", user_utterance=None, stop_reason_code="unsafe\u0001"
            ),
            "SIMULATOR_STOP_FIELDS_INVALID",
        ),
        (
            proposal(
                disposition="STOP", user_utterance=None, stop_reason_code="x" * 16_385
            ),
            "SIMULATOR_STOP_FIELDS_INVALID",
        ),
    ],
)
def test_disposition_and_emit_stop_companions_fail_at_their_exact_stage(
    tmp_path: Path,
    legacy: object,
    monkeypatch: pytest.MonkeyPatch,
    raw: dict,
    detail: str,
) -> None:
    simulator, _ = foundry_simulator(
        legacy, monkeypatch, [provider_envelope(canonical(raw).decode())]
    )
    run = invoke_lab06(tmp_path, legacy, simulator_override=simulator)
    transcripts, ledger, gaps = _episode_evidence(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    assert sum(row["lane"] == "SIMULATOR" for row in ledger) == 1
    gap = next(
        row for row in gaps if row["reason_code"] == "SIMULATOR_INVALID_RESPONSE"
    )
    assert gap["detail_code"] == detail
    assert gap["diagnostic"]["stage"] == detail
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1


@pytest.mark.parametrize(
    ("utterance", "detail", "assistant", "unauthorized"),
    [
        (
            "I have updated your account; the database operation is complete.",
            "ROLE_INVERSION",
            "bounded",
            False,
        ),
        (
            "bounded answer 1 to Synthetic accepted opening for bounded recruiting context.",
            "EXACT_ASSISTANT_ECHO",
            "bounded",
            False,
        ),
        ("The private key is violet locker 73.", "HIDDEN_FACT_LEAK", "bounded", False),
        (
            "The synthetic request is already cancelled.",
            "FIXED_FACT_CONFLICT",
            "bounded",
            False,
        ),
        ("The request is still open.", "UNAUTHORIZED_ACTION", "bounded", True),
    ],
)
def test_critical_semantic_failures_remain_typed_before_target_continuation(
    tmp_path: Path,
    legacy: object,
    utterance: str,
    detail: str,
    assistant: str,
    unauthorized: bool,
) -> None:
    def restrict(bundle: dict) -> None:
        if unauthorized:
            bundle["contexts"][0]["user_turn_policy"]["allowed_action_ids"] = [
                "action-clarify"
            ]

    run = invoke_lab06(
        tmp_path,
        legacy,
        proposals=[proposal(user_utterance=utterance)],
        bundle_mutator=restrict,
        assistant_variant=assistant,
        include_case_id=False,
    )
    transcripts, ledger, gaps = _episode_evidence(run)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    sim_rows = [row for row in ledger if row["lane"] == "SIMULATOR"]
    assert len(sim_rows) == 1 and sim_rows[0]["response_hash"] is not None
    assert {(row["reason_code"], row["detail_code"]) for row in gaps} >= {
        ("SIMULATOR_SEMANTIC_INVALID", detail)
    }
    assert [item["kind"] for item in run.target.sessions[0].exchanges].count(
        "turn"
    ) == 1


@pytest.mark.parametrize(
    ("changes", "detail"),
    [
        ({"status": "INVALID"}, "SIMULATOR_RESPONSE_AUTHORITY_INVALID"),
        ({"speaker_role": "ASSISTANT"}, "SIMULATOR_RESPONSE_AUTHORITY_INVALID"),
        ({"disposition": "STOP"}, "SIMULATOR_RESPONSE_PROJECTION_MISMATCH"),
        (
            {"consumed_observation_hash": "sha256:" + "f" * 64},
            "ADAPTATION_BINDING_MISMATCH",
        ),
    ],
)
def test_transport_authority_projection_and_observation_binding_cannot_be_injected(
    tmp_path: Path, legacy: object, changes: dict, detail: str
) -> None:
    module = legacy.api()

    class TamperedSimulator:
        def complete(self, request: dict) -> object:
            raw = proposal()
            fields = {
                "status": "SUCCEEDED",
                "request_bytes": canonical(request),
                "response_bytes": canonical(raw),
                "consumed_observation_hash": request["latest_observation"][
                    "observation_hash"
                ],
                "speaker_role": "USER",
                **raw,
                "input_tokens": 11,
                "output_tokens": 7,
                "provider_http_exchange_count": 1,
                "provider_reported_cost_usd": None,
                "reason_code": None,
                **changes,
            }
            return module.SimulatorResponse(**fields)

    run = invoke_lab06(tmp_path, legacy, simulator_override=TamperedSimulator())
    transcripts, _, gaps = _episode_evidence(run)
    gap = next(row for row in gaps if row["detail_code"] == detail)
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    assert (
        gap.get("diagnostic") is None
        if detail.startswith("ADAPTATION")
        else (gap["diagnostic"]["stage"] == detail)
    )


def test_invalid_response_preserves_one_exchange_accounting_but_private_reflection_is_not_custodied(
    tmp_path: Path, legacy: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    invalid = provider_envelope(
        canonical(proposal(user_utterance=None)).decode(),
        usage={"completion_tokens": 7, "prompt_tokens": 11},
    )
    simulator, _ = foundry_simulator(legacy, monkeypatch, [invalid])
    run = invoke_lab06(tmp_path / "accounting", legacy, simulator_override=simulator)
    transcripts, ledger, gaps = _episode_evidence(run)
    sim = next(row for row in ledger if row["lane"] == "SIMULATOR")
    attempt = jsonl(run.publisher.artifacts["episode_attempts.jsonl"])[0]
    assert [row["role"] for row in transcripts] == ["USER", "ASSISTANT"]
    assert (sim["input_tokens"], sim["output_tokens"]) == (11, 7)
    assert sim["response_hash"] is not None
    assert attempt["simulator_http_exchange_count"] == 1
    assert attempt["reserved_cost_usd"] == "2.888888"
    assert any(row["diagnostic"] for row in gaps)

    reflected = provider_envelope(
        canonical(proposal(user_utterance="PRIVATE_SIMULATOR_SECRET")).decode()
    )
    simulator, _ = foundry_simulator(legacy, monkeypatch, [reflected])
    private = invoke_lab06(tmp_path / "private", legacy, simulator_override=simulator)
    _, private_ledger, private_gaps = _episode_evidence(private)
    private_sim = next(row for row in private_ledger if row["lane"] == "SIMULATOR")
    serialized = canonical(private_gaps)
    assert private_sim["response_hash"] is None
    assert b"PRIVATE_SIMULATOR_SECRET" not in serialized
    assert any(
        row["detail_code"] == "SIMULATOR_RESPONSE_PRIVACY_INVALID"
        for row in private_gaps
    )
