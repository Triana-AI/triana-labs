"""Exact success artifacts, identities, lineage, projection, and review evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import (
    ENVIRON,
    OUTPUT_NAMES,
    SCHEMA_ROOT,
    CapturePublisher,
    artifact_hash,
    canonical,
    compact_id,
    domain_hash,
    invoke,
    request_user_value,
)


def parse_jsonl(payload: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in payload.splitlines()]


def assert_portable_identity(record: dict[str, Any], kind: str, field: str) -> None:
    preimage = dict(record)
    identity = preimage.pop(field)
    if kind == "case":
        preimage.pop("novelty")
    assert identity == compact_id(kind, preimage)


def test_success_bundle_has_exact_canonical_files_ids_hashes_and_review(
    tmp_path: Path, success_callbacks: list[Any]
) -> None:
    publisher = CapturePublisher()
    result, transport, _, output = invoke(
        tmp_path, success_callbacks, publisher=publisher
    )

    assert result.outcome == "COMPLETED"
    assert result.reason_code is None
    assert result.manifest_path == output / "manifest.json"
    assert (result.attempted_case_count, result.valid_case_count) == (5, 5)
    assert result.provider_call_count == 3
    assert publisher.artifacts is not None
    artifacts = publisher.artifacts
    assert set(artifacts) == OUTPUT_NAMES
    for name, payload in artifacts.items():
        if name.endswith(".json"):
            assert payload == canonical(json.loads(payload), lf=True)
        else:
            assert payload == b"".join(
                canonical(item, lf=True) for item in parse_jsonl(payload)
            )

    manifest = json.loads(artifacts["manifest.json"])
    assert manifest["artifacts"] == {
        name: artifact_hash(payload)
        for name, payload in artifacts.items()
        if name != "manifest.json"
    }
    assert manifest["outcome"] == "COMPLETED"
    assert manifest["human_review_state"] == "PENDING"
    assert manifest["attempt_count"] == 3
    assert manifest["requested_case_count"] == 5
    assert manifest["valid_case_count"] == 5
    assert manifest["raw_case_count"] == 5
    assert manifest["distinct_case_count"] == 5
    assert manifest["duplicate_case_count"] == 0

    for path, kind, field in (
        ("personas.jsonl", "persona", "persona_id"),
        ("intents.jsonl", "intent", "intent_id"),
        ("turn_policies.jsonl", "turn-policy", "turn_policy_id"),
        ("case_candidates.jsonl", "case", "case_id"),
        ("control_personas.jsonl", "persona", "persona_id"),
        ("control_intents.jsonl", "intent", "intent_id"),
        ("control_turn_policies.jsonl", "turn-policy", "turn_policy_id"),
        ("control_case_candidates.jsonl", "case", "case_id"),
    ):
        records = parse_jsonl(artifacts[path])
        assert records == sorted(records, key=lambda item: item[field])
        for record in records:
            assert_portable_identity(record, kind, field)
            assert record["proposal_state"] == "PROPOSED"
            assert record["fidelity"] == "SYNTHETIC_CORPUS_GROUNDED"
            for claim in record["grounding_claims"]:
                preimage = dict(claim)
                claim_id = preimage.pop("claim_id")
                assert claim_id == compact_id("claim", preimage)

    evidence = json.loads(artifacts["evidence_index.json"])
    citations = evidence["citations"]
    assert citations == sorted(citations, key=lambda item: item["citation_id"])
    for citation in citations:
        preimage = dict(citation)
        identity = preimage.pop("citation_id")
        assert identity == compact_id("citation", preimage)

    review = json.loads(artifacts["human_review_template.json"])
    evaluation = json.loads(artifacts["case_factory_eval.json"])
    assert review["review_state"] == evaluation["human_review_state"] == "PENDING"
    assert len(review["review_items"]) == 10
    assert len(evaluation["blind_lineage"]) == 10
    assert review["evaluation_manifest_hash"] == domain_hash(
        "evaluation-manifest", evaluation
    )
    forbidden_review_keys = {"lane", "stage", "model", "attempt_id", "case_id"}
    assert all(
        not (forbidden_review_keys & set(item)) for item in review["review_items"]
    )

    attempts = parse_jsonl(artifacts["generation_attempts.jsonl"])
    assert [item["stage"] for item in attempts] == ["PROPOSE", "CRITIQUE", "REVISE"]
    for attempt, request in zip(attempts, transport.requests, strict=True):
        assert attempt["request_hash"].startswith("sha256:")
        assert attempt["status"] == "SUCCEEDED"
        preimage = {
            "input_manifest_hash": manifest["input_manifest_hash"],
            "intelligence_manifest_hash": manifest["intelligence_manifest_hash"],
            "provider_evidence_hash": manifest["provider_evidence_hash"],
            "stage": attempt["stage"],
            "attempt_index": attempt["attempt_index"],
            "request_hash": attempt["request_hash"],
            "deployment": "gpt-4.1-mini",
            "model_version": "2025-04-14",
            "seed": 2026080104,
        }
        assert attempt["attempt_id"] == compact_id("attempt", preimage)
        assert request.api_key == ENVIRON["AZURE_OPENAI_API_KEY"]


def test_request_uses_literal_schema_and_projects_only_allowlisted_evidence(
    tmp_path: Path, success_callbacks: list[Any]
) -> None:
    publisher = CapturePublisher()
    _, transport, _, _ = invoke(tmp_path, success_callbacks, publisher=publisher)
    proposal_schema = json.loads((SCHEMA_ROOT / "proposal.schema.json").read_bytes())
    critique_schema = json.loads((SCHEMA_ROOT / "critique.schema.json").read_bytes())

    for index, request in enumerate(transport.requests):
        envelope = json.loads(request.body)
        expected = critique_schema if index == 1 else proposal_schema
        assert envelope["response_format"]["json_schema"]["schema"] == expected
        assert envelope["temperature"] == 0.2
        assert envelope["seed"] == 2026080104
        assert envelope["max_tokens"] == 4096
        assert len(request.body) <= 100000
    evidence = request_user_value(transport.requests[0])["evidence"]
    payload = canonical(evidence)
    for private in (
        b"PRIVATE_SYSTEM",
        b"PRIVATE_ARGUMENT",
        b"PRIVATE_RESULT",
        b"PRIVATE_REASON",
        b"source-trace",
        ENVIRON["AZURE_OPENAI_API_KEY"].encode(),
    ):
        assert private not in payload
    assert "Need bilingual ayuda" in payload.decode()
    assert "Need code-switched सहायता" in payload.decode()


def test_fresh_runs_repeat_and_evidence_changes_lineage(
    tmp_path: Path, success_callbacks: list[Any]
) -> None:
    publishers = [CapturePublisher(), CapturePublisher()]
    for index, publisher in enumerate(publishers):
        invoke(tmp_path / str(index), success_callbacks, publisher=publisher)
    assert publishers[0].artifacts == publishers[1].artifacts

    changed = CapturePublisher()
    from conftest import trace

    traces = [
        trace("trace-alpha", "Changed evidence", "I can help"),
        trace("trace-beta", "Need code-switched सहायता", "I can assist"),
    ]
    invoke(tmp_path / "changed", success_callbacks, traces=traces, publisher=changed)
    first = json.loads(publishers[0].artifacts["manifest.json"])
    second = json.loads(changed.artifacts["manifest.json"])
    assert first["provider_evidence_hash"] != second["provider_evidence_hash"]
    assert first["input_manifest_hash"] != second["input_manifest_hash"]
