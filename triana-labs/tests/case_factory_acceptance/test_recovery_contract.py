"""Decisive black-box RED contract for the bounded LABS-04 recovery."""

from __future__ import annotations

import inspect
import json
import stat
from pathlib import Path
from typing import Any

from conftest import (
    ENVIRON,
    ScriptedTransport,
    api,
    artifact_hash,
    azure_body,
    build_upstream,
    byte_hash,
    canonical,
    domain_hash,
    proposal_callback,
    request_user_value,
    valid_proposal,
    write_config,
)

SEMANTIC_FILES = {
    "control_personas.jsonl",
    "control_intents.jsonl",
    "control_turn_policies.jsonl",
    "control_case_candidates.jsonl",
    "personas.jsonl",
    "intents.jsonl",
    "turn_policies.jsonl",
    "case_candidates.jsonl",
}
FAILURE_KEYS = {
    "artifact_kind",
    "schema_version",
    "input_manifest_hash",
    "intelligence_manifest_hash",
    "privacy_class",
    "producing_component",
    "producing_component_version",
    "provider_kind",
    "endpoint_host_hash",
    "deployment",
    "model_name",
    "model_version",
    "prompt_pack_hash",
    "provider_evidence_hash",
    "seed",
    "outcome",
    "reason_code",
    "failing_stage",
    "attempt_count",
    "provider_call_count",
    "cache_replay_count",
    "input_token_count",
    "output_token_count",
    "provider_cached_input_token_count",
    "requested_case_count",
    "valid_case_count",
    "distinct_case_count",
    "conservative_cost_usd",
    "human_review_state",
    "artifacts",
}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes())


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def _mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def _cached(callback: Any, cached_tokens: int, bodies: list[bytes]) -> Any:
    def respond(request: Any) -> tuple[int, bytes]:
        status, body = callback(request)
        value = json.loads(body)
        value["usage"]["cost"] = 0.125
        value["usage"]["prompt_tokens_details"] = {"cached_tokens": cached_tokens}
        body = canonical(value)
        bodies.append(body)
        return status, body

    return respond


def _cache_entry(
    cache: Path, request: Any, response: bytes, prompt_hash: str
) -> tuple[Path, dict[str, Any]]:
    endpoint_hash = domain_hash("endpoint-host", "operator.example.azure.com")
    request_hash = byte_hash("provider-request", request.body)
    response_hash = byte_hash("provider-response", response)
    preimage = {
        "endpoint_host_hash": endpoint_hash,
        "deployment": "gpt-4.1-mini",
        "model_name": "gpt-4.1-mini",
        "model_version": "2025-04-14",
        "request_hash": request_hash,
        "prompt_pack_hash": prompt_hash,
    }
    cache_key = domain_hash("provider-response-cache-entry", preimage)
    digest = cache_key.removeprefix("sha256:")
    entry = cache / "v1" / digest[:2] / digest
    metadata = {
        "artifact_kind": "case_factory_provider_cache_entry",
        "schema_version": 1,
        "cache_key": cache_key,
        **preimage,
        "request_byte_count": len(request.body),
        "request_artifact_hash": artifact_hash(request.body),
        "status_code": 200,
        "response_byte_count": len(response),
        "response_hash": response_hash,
        "response_artifact_hash": artifact_hash(response),
    }
    return entry, metadata


def test_exact_cache_miss_write_then_replay_has_zero_transport_and_cost(
    tmp_path: Path,
) -> None:
    generate_module, _ = api()
    signature = inspect.signature(generate_module.generate)
    cache_parameter = signature.parameters["cache_path"]
    assert cache_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert cache_parameter.default is inspect.Parameter.empty

    observer, intelligence = build_upstream(tmp_path / "upstream")
    config = write_config(tmp_path)
    cache = tmp_path / "private-cache"
    raw_bodies: list[bytes] = []
    fresh_transport = ScriptedTransport(
        [
            _cached(proposal_callback(), 11, raw_bodies),
            _cached(lambda _: (200, azure_body({"issues": []})), 22, raw_bodies),
            _cached(proposal_callback(), 33, raw_bodies),
        ]
    )
    first_output = tmp_path / "fresh-output"
    fresh = generate_module.generate(
        observer,
        intelligence,
        config,
        first_output,
        cache_path=cache,
        transport=fresh_transport,
        environ=ENVIRON,
    )
    assert fresh.outcome == "COMPLETED"
    assert fresh.provider_call_count == 3
    assert _mode(cache) == 0o700
    prompt_hash = _json(first_output / "manifest.json")["prompt_pack_hash"]
    for request, response in zip(fresh_transport.requests, raw_bodies, strict=True):
        entry, metadata = _cache_entry(cache, request, response, prompt_hash)
        assert {item.name for item in entry.iterdir()} == {
            "request.json",
            "response.json",
            "metadata.json",
        }
        assert _mode(entry) == 0o700
        assert entry.joinpath("request.json").read_bytes() == request.body
        assert entry.joinpath("response.json").read_bytes() == response
        assert entry.joinpath("metadata.json").read_bytes() == canonical(
            metadata, lf=True
        )
        assert all(_mode(item) == 0o600 for item in entry.iterdir())

    fresh_attempts = _jsonl(first_output / "generation_attempts.jsonl")
    assert [item["execution_mode"] for item in fresh_attempts] == ["FRESH_PROVIDER"] * 3
    assert [item["provider_cached_input_tokens"] for item in fresh_attempts] == [
        11,
        22,
        33,
    ]
    assert all(item["conservative_cost_usd"] != "0.000000" for item in fresh_attempts)

    replay_transport = ScriptedTransport([])
    second_output = tmp_path / "replay-output"
    replay = generate_module.generate(
        observer,
        intelligence,
        config,
        second_output,
        cache_path=cache,
        transport=replay_transport,
        environ=ENVIRON,
    )
    assert replay.outcome == "COMPLETED"
    assert replay.provider_call_count == 0
    assert replay.conservative_cost_usd == "0.000000"
    assert replay_transport.requests == []
    replay_attempts = _jsonl(second_output / "generation_attempts.jsonl")
    assert [item["execution_mode"] for item in replay_attempts] == ["CACHE_REPLAY"] * 3
    assert [item["attempt_id"] for item in replay_attempts] == [
        item["attempt_id"] for item in fresh_attempts
    ]
    assert [item["provider_cached_input_tokens"] for item in replay_attempts] == [
        11,
        22,
        33,
    ]
    assert all(item["provider_reported_cost_usd"] is None for item in replay_attempts)
    assert all(item["conservative_cost_usd"] == "0.000000" for item in replay_attempts)


def test_post_egress_invalid_response_publishes_safe_failure_bundle(
    tmp_path: Path,
) -> None:
    generate_module, _ = api()
    observer, intelligence = build_upstream(tmp_path / "upstream")
    transport = ScriptedTransport([(200, b"{")])
    output = tmp_path / "failure-output"
    try:
        generate_module.generate(
            observer,
            intelligence,
            write_config(tmp_path),
            output,
            cache_path=tmp_path / "private-cache",
            transport=transport,
            environ=ENVIRON,
        )
    except generate_module.GenerateFailure as failure:
        assert (failure.reason_code, failure.exit_code) == ("PROVIDER_FAILED", 8)
    else:
        raise AssertionError("invalid provider response must reject")

    manifest = _json(output / "manifest.json")
    assert set(manifest) == FAILURE_KEYS
    assert manifest["artifact_kind"] == "case_factory_failure_manifest"
    assert (
        manifest["outcome"],
        manifest["reason_code"],
        manifest["failing_stage"],
    ) == (
        "REJECTED",
        "PROVIDER_FAILED",
        "PROPOSE",
    )
    assert (manifest["attempt_count"], manifest["provider_call_count"]) == (1, 1)
    assert all((output / name).read_bytes() == b"" for name in SEMANTIC_FILES)
    stage = output / "provider" / "propose"
    assert stage.joinpath("request.json").read_bytes() == transport.requests[0].body
    assert stage.joinpath("response.json").read_bytes() == b"{"
    assert not stage.joinpath("parsed.json").exists()
    assert _json(stage / "defects.json") == {
        "artifact_kind": "case_factory_stage_defects",
        "schema_version": 1,
        "stage": "PROPOSE",
        "defects": [
            {
                "code": "PROVIDER_RESPONSE_INVALID",
                "path": "",
                "message": "PROVIDER RESPONSE INVALID",
                "related_ids": [],
                "repairable": False,
            }
        ],
    }
    attempt = _jsonl(output / "generation_attempts.jsonl")[0]
    assert attempt["response_hash"] == byte_hash("provider-response", b"{")
    assert attempt["execution_mode"] == "FRESH_PROVIDER"
    published = {
        str(item.relative_to(output))
        for item in output.rglob("*")
        if item.is_file() and item.name != "manifest.json"
    }
    assert set(manifest["artifacts"]) == published
    assert manifest["artifacts"] == {
        name: artifact_hash((output / name).read_bytes()) for name in sorted(published)
    }


def test_invalid_propose_defects_reach_repair_and_valid_revision_is_revised_only(
    tmp_path: Path,
) -> None:
    expected_defects: list[dict[str, Any]] = []

    def invalid_proposal(request: Any) -> tuple[int, bytes]:
        nonlocal expected_defects
        user = request_user_value(request)
        proposal = valid_proposal(user["citations"])
        citation_id = proposal["personas"][0]["grounding_claims"][0]["citation_ids"][0]
        claim = proposal["personas"][0]["grounding_claims"][0]
        claim.update(support_state="SUPPORTED", citation_ids=[citation_id])
        proposal["turn_policies"][0]["reaction_rules"] = []
        case = proposal["cases"][0]
        case["grounding_claims"] = []
        case["scenario"]["opening_user_turn"] = {
            "text": "Generated opening",
            "basis": "GENERATED_VARIATION",
            "claim_keys": [],
        }
        expected_defects = [
            {
                "code": "EMPTY_REACTION_RULES",
                "path": "/turn_policies/0/reaction_rules",
                "message": "reaction_rules must contain at least one item",
                "related_ids": [],
                "repairable": True,
            },
            {
                "code": "MISSING_OBSERVED_ANCHOR",
                "path": "/cases/0",
                "message": "case must contain at least one case-local OBSERVED item",
                "related_ids": [],
                "repairable": True,
            },
            {
                "code": "SUPPORT_CARDINALITY_MISMATCH",
                "path": "/personas/0/grounding_claims/0",
                "message": "SUPPORTED requires citations from at least two traces",
                "related_ids": [citation_id],
                "repairable": True,
            },
        ]
        return 200, azure_body(proposal)

    def critique(request: Any) -> tuple[int, bytes]:
        user = request_user_value(request)
        assert set(user) == {
            "evidence",
            "citations",
            "proposal",
            "deterministic_defects",
        }
        assert user["deterministic_defects"] == expected_defects
        return 200, azure_body({"issues": []})

    def revise(request: Any) -> tuple[int, bytes]:
        user = request_user_value(request)
        assert set(user) == {
            "evidence",
            "citations",
            "proposal",
            "critique",
            "deterministic_defects",
        }
        assert user["deterministic_defects"] == expected_defects
        return 200, azure_body(valid_proposal(user["citations"]))

    generate_module, _ = api()
    observer, intelligence = build_upstream(tmp_path / "upstream")
    output = tmp_path / "repaired-output"
    result = generate_module.generate(
        observer,
        intelligence,
        write_config(tmp_path),
        output,
        cache_path=tmp_path / "private-cache",
        transport=ScriptedTransport([invalid_proposal, critique, revise]),
        environ=ENVIRON,
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "CONTROL_SEMANTICALLY_INVALID"
    assert result.valid_case_count == 5
    assert all(
        (output / name).read_bytes() == b""
        for name in SEMANTIC_FILES
        if name.startswith("control_")
    )
    assert len(_jsonl(output / "case_candidates.jsonl")) == 5
    assert (
        _json(output / "provider" / "propose" / "defects.json")["defects"]
        == expected_defects
    )
    assert _json(output / "provider" / "revise" / "defects.json")["defects"] == []
    evaluation = _json(output / "case_factory_eval.json")
    assert evaluation["comparison_available"] is False
    assert (
        evaluation["control_requested_case_count"],
        evaluation["control_valid_case_count"],
        evaluation["control_invalid_case_count"],
        evaluation["control_raw_n"],
        evaluation["control_effective_n"],
    ) == (5, 0, 5, 5, 0)
    assert evaluation["revised_valid_case_count"] == 5
    assert evaluation["machine_status"] == "PASSED"
    assert "CONTROL_SEMANTICALLY_INVALID" in evaluation["gap_codes"]
    review = _json(output / "human_review_template.json")
    assert review["comparison_available"] is False
    assert len(review["review_items"]) == 5


def test_single_frozen_recoverable_defect_reaches_critique_and_revise(
    tmp_path: Path,
) -> None:
    expected_defects: list[dict[str, Any]] = []

    def invalid_proposal(request: Any) -> tuple[int, bytes]:
        nonlocal expected_defects
        user = request_user_value(request)
        proposal = valid_proposal(user["citations"])
        claim = proposal["personas"][0]["grounding_claims"][0]
        citation_id = claim["citation_ids"][0]
        claim.update(support_state="SUPPORTED", citation_ids=[citation_id])
        expected_defects = [
            {
                "code": "SUPPORT_CARDINALITY_MISMATCH",
                "path": "/personas/0/grounding_claims/0",
                "message": "SUPPORTED requires citations from at least two traces",
                "related_ids": [citation_id],
                "repairable": True,
            }
        ]
        return 200, azure_body(proposal)

    def critique(request: Any) -> tuple[int, bytes]:
        assert request_user_value(request)["deterministic_defects"] == expected_defects
        return 200, azure_body({"issues": []})

    def revise(request: Any) -> tuple[int, bytes]:
        user = request_user_value(request)
        assert user["deterministic_defects"] == expected_defects
        return 200, azure_body(valid_proposal(user["citations"]))

    generate_module, _ = api()
    observer, intelligence = build_upstream(tmp_path / "upstream")
    transport = ScriptedTransport([invalid_proposal, critique, revise])
    result = generate_module.generate(
        observer,
        intelligence,
        write_config(tmp_path),
        tmp_path / "repaired-output",
        cache_path=tmp_path / "private-cache",
        transport=transport,
        environ=ENVIRON,
    )
    assert len(transport.requests) == 3
    assert result.reason_code == "CONTROL_SEMANTICALLY_INVALID"
    assert result.valid_case_count == 5
