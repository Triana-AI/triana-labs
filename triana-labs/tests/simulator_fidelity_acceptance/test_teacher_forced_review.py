"""Thirty-item teacher-forced denominator, identity, and human authority."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from conftest import (
    CRITICAL_CODES,
    ContextLoader,
    FidelitySimulator,
    bundle_value,
    canonical,
    digest,
    jsonl,
)


def test_teacher_forced_default_bundle_load_and_exact_three_artifact_review_contract(
    tmp_path: Path, legacy: object
) -> None:
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


def test_teacher_forced_injected_loader_preserves_rejected_denominator_and_accounting(
    tmp_path: Path, legacy: object
) -> None:
    module = legacy.api()
    bundle = bundle_value(legacy)
    echo = "Synthetic assistant observation 1: the request remains open."
    simulator = FidelitySimulator(
        module,
        [
            {
                "action_ids": ["action-clarify"],
                "consumed_observation_hash": "LATEST",
                "disposition": "EMIT",
                "reaction_id": "reaction-clarify",
                "speaker_role": "USER",
                "stop_reason_code": None,
                "user_utterance": echo,
            }
        ],
    )
    loader = ContextLoader(module, bundle)
    artifacts = module.evaluate_teacher_forced(
        tmp_path / "injected.json", simulator=simulator, context_loader=loader
    )
    attempts = jsonl(artifacts["fidelity_attempts.jsonl"])
    review = json.loads(artifacts["human_fidelity_review.json"])
    assert loader.calls == [tmp_path / "injected.json"]
    assert len(attempts) == review["denominator"] == 30
    assert attempts[0]["outcome"] == "REJECTED"
    assert attempts[0]["reason_code"] == "SIMULATOR_SEMANTIC_INVALID"
    assert "EXACT_ASSISTANT_ECHO" in attempts[0]["detail_codes"]
    assert all(item["human_accepted"] is None for item in review["review_items"])
