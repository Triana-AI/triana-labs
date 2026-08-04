"""Thirty-item teacher-forced denominator, identity, and human authority."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from conftest import (
    CRITICAL_CODES,
    FidelitySimulator,
    bundle_value,
    canonical,
    digest,
    foundry_simulator,
    invoke_lab06,
    jsonl,
    proposal,
    provider_envelope,
)


def test_shared_structural_circuit_blocks_only_third_identical_first_failure(
    tmp_path: Path, legacy: object, monkeypatch: object
) -> None:
    invalid = provider_envelope(canonical(proposal(user_utterance=None)).decode())
    simulator, opener = foundry_simulator(legacy, monkeypatch, [invalid])
    blocked = invoke_lab06(tmp_path / "blocked", legacy, simulator_override=simulator)
    attempts = jsonl(blocked.publisher.artifacts["episode_attempts.jsonl"])
    assert len(opener.requests) == len(blocked.target.launches) == 2
    assert attempts[2]["termination_reason"] == "SIMULATOR_SHARED_CONFORMANCE_BLOCKED"
    assert attempts[2]["simulator_http_exchange_count"] == 0
    assert attempts[2]["target_http_exchange_count"] == 0

    different = provider_envelope(canonical(proposal(disposition=7)).decode())
    valid = provider_envelope(canonical(proposal()).decode())
    simulator, opener = foundry_simulator(
        legacy, monkeypatch, [invalid, different, valid]
    )
    continued = invoke_lab06(
        tmp_path / "different", legacy, simulator_override=simulator
    )
    assert len(opener.requests) > 2 and len(continued.target.launches) == 3
    assert "SIMULATOR_SHARED_CONFORMANCE_BLOCKED" not in {
        row["termination_reason"]
        for row in jsonl(continued.publisher.artifacts["episode_attempts.jsonl"])
    }

    semantic = invoke_lab06(
        tmp_path / "semantic",
        legacy,
        proposals=[proposal(user_utterance="I have updated your account.")],
    )
    assert len(semantic.target.launches) == 3
    assert "SIMULATOR_SHARED_CONFORMANCE_BLOCKED" not in {
        row["termination_reason"]
        for row in jsonl(semantic.publisher.artifacts["episode_attempts.jsonl"])
    }


def test_historical_bundle_review_and_no_bundle_accounting_privacy_custody_remain_stable(
    tmp_path: Path, legacy: object
) -> None:
    historical = legacy.invoke(tmp_path / "legacy")
    assert all(
        request["protocol_version"] == "LABS05_WIRE_V1"
        for request in historical.simulator.requests
    )
    assert historical.result.simulator_http_exchange_count == 6
    assert (
        json.loads(historical.publisher.artifacts["manifest.json"])["privacy_class"]
        == "SYNTHETIC"
    )
    assert all(
        row["request_hash"] and row["response_hash"]
        for row in jsonl(historical.publisher.artifacts["provider_ledger.jsonl"])
    )

    module = legacy.api()
    bundle = bundle_value(legacy)
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_bytes(canonical(bundle, lf=True))
    structural = module.evaluate_teacher_forced(
        bundle_path,
        simulator=FidelitySimulator(module, [proposal(user_utterance=None)]),
    )
    structural_attempt = jsonl(structural["fidelity_attempts.jsonl"])[0]
    assert structural_attempt["reason_code"] == "SIMULATOR_INVALID_RESPONSE"
    assert structural_attempt["detail_codes"] == ["SIMULATOR_EMIT_FIELDS_INVALID"]
    assert structural_attempt["diagnostic"]["stage"] == "SIMULATOR_EMIT_FIELDS_INVALID"
    semantic = module.evaluate_teacher_forced(
        bundle_path,
        simulator=FidelitySimulator(
            module, [proposal(user_utterance="I have updated your account.")]
        ),
    )
    semantic_attempt = jsonl(semantic["fidelity_attempts.jsonl"])[0]
    assert semantic_attempt["reason_code"] == "SIMULATOR_SEMANTIC_INVALID"
    assert semantic_attempt["diagnostic"] is None
    simulator = FidelitySimulator(module)
    artifacts = module.evaluate_teacher_forced(bundle_path, simulator=simulator)

    assert set(artifacts) == {
        "fidelity_attempts.jsonl",
        "fidelity_manifest.json",
        "human_fidelity_review.json",
    }
    assert len(simulator.requests) == 30
    attempts = jsonl(artifacts["fidelity_attempts.jsonl"])
    review = json.loads(artifacts["human_fidelity_review.json"])
    manifest = json.loads(artifacts["fidelity_manifest.json"])
    assert len(attempts) == 30
    assert [row["item_id"] for row in attempts] == [
        row["item_id"] for row in bundle["teacher_forced_items"]
    ]
    assert review["rubric_version"] == "REGULAR_USER_SIMULATION_FIDELITY_V1"
    assert review["review_state"] == "PENDING"
    assert review["denominator"] == 30
    assert review["required_accepted"] == 24
    assert set(review["critical_failure_codes"]) == CRITICAL_CODES
    assert Counter(item["stratum"] for item in review["review_items"]) == Counter(
        {
            "ORDINARY": 24,
            "ANGRY": 1,
            "IMPATIENT": 1,
            "SKEPTICAL": 1,
            "INFORMAL": 1,
            "MISTAKEN": 1,
            "ADVERSARIAL": 1,
        }
    )
    assert all(
        item["human_accepted"] is None and item["human_notes"] is None
        for item in review["review_items"]
    )
    assert manifest["attempt_count"] == 30
    assert manifest["simulator_http_exchange_count"] == 30
    assert manifest["artifacts"] == {
        name: digest(payload)
        for name, payload in artifacts.items()
        if name != "fidelity_manifest.json"
    }
