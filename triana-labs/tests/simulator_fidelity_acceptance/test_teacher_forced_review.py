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
    jsonl,
)


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
