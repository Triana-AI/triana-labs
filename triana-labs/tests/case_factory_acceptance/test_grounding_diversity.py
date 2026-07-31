"""Grounding validity, retained gaps, diversity, and human-authority boundaries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from conftest import (
    CapturePublisher,
    api,
    compact_id,
    critique_callback,
    domain_hash,
    invoke,
    proposal_callback,
    trace,
)


def mutation(kind: str) -> Any:
    def mutate(value: dict[str, Any]) -> None:
        case = value["cases"][0]
        if kind == "hallucinated-citation":
            case["grounding_claims"][0]["citation_ids"] = ["citation-missing"]
        elif kind == "unresolved-asset":
            case["persona_key"] = "missing"
        elif kind == "no-anchor":
            case["scenario"]["opening_user_turn"] = {
                "text": "Generated only",
                "basis": "GENERATED_VARIATION",
                "claim_keys": [],
            }
            case["grounding_claims"] = []
        elif kind == "unsupported-population":
            case["grounding_claims"][0]["support_state"] = "SUPPORTED"
        elif kind == "demographic":
            value["personas"][0]["label"] = "Pregnancy requester"
        elif kind == "empty-abstain":
            case["proposed_evaluation"]["abstain_conditions"] = []
        elif kind == "nonadaptive":
            value["turn_policies"][0]["reaction_rules"] = []
        elif kind == "unknown-field":
            case["future_dialogue"] = ["fixed turn"]

    return mutate


@pytest.mark.parametrize(
    "kind",
    [
        "hallucinated-citation",
        "unresolved-asset",
        "no-anchor",
        "unsupported-population",
        "demographic",
        "empty-abstain",
        "nonadaptive",
        "unknown-field",
    ],
)
def test_invalid_grounding_and_semantics_never_become_valid_cases(
    tmp_path: Path, kind: str
) -> None:
    api()
    with pytest.raises(Exception) as caught:
        invoke(tmp_path, [proposal_callback(mutate=mutation(kind))])
    assert caught.value.reason_code == "PROVIDER_FAILED"
    assert caught.value.exit_code == 8


def test_duplicates_remain_visible_but_do_not_raise_effective_n(tmp_path: Path) -> None:
    api()
    publisher = CapturePublisher()
    callbacks = [
        proposal_callback(duplicate=True),
        critique_callback,
        proposal_callback(duplicate=True),
    ]
    traces = [
        trace("trace-alpha", "First structural request", "Reply"),
        trace("trace-beta", "Second structural request", "Reply"),
    ]
    traces[1]["events"][2]["tool_name"] = "lookup_other"
    result, _, _, _ = invoke(tmp_path, callbacks, traces=traces, publisher=publisher)
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "INSUFFICIENT_DISTINCT_CASES"
    cases = [
        json.loads(line)
        for line in publisher.artifacts["case_candidates.jsonl"].splitlines()
    ]
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    evidence = json.loads(publisher.artifacts["evidence_index.json"])
    manifest = json.loads(publisher.artifacts["manifest.json"])
    citation_cluster = {
        item["citation_id"]: item["structural_cluster_id"]
        for item in evidence["citations"]
    }
    personas = {
        item["persona_id"]: item
        for item in (
            json.loads(line)
            for line in publisher.artifacts["personas.jsonl"].splitlines()
        )
    }
    intents = {
        item["intent_id"]: item
        for item in (
            json.loads(line)
            for line in publisher.artifacts["intents.jsonl"].splitlines()
        )
    }
    policies = {
        item["turn_policy_id"]: item
        for item in (
            json.loads(line)
            for line in publisher.artifacts["turn_policies.jsonl"].splitlines()
        )
    }
    assert len(cases) == 5
    assert evaluation["revised_raw_n"] == 5
    assert evaluation["revised_effective_n"] == 1
    assert manifest["raw_case_count"] == manifest["valid_case_count"] == 5
    assert manifest["distinct_case_count"] == 1
    assert manifest["duplicate_case_count"] == 4
    assert "DUPLICATE_CASE" in evaluation["gap_codes"]
    assert all(item["novelty"]["duplicate_cluster_id"] for item in cases)
    sorted_ids = sorted(item["case_id"] for item in cases)
    cluster_id = compact_id("duplicate-cluster", sorted_ids)
    representative = sorted_ids[0]
    control_ids = sorted(
        json.loads(line)["case_id"]
        for line in publisher.artifacts["control_case_candidates.jsonl"].splitlines()
    )
    assert {
        tuple(item["member_case_ids"]) for item in evaluation["duplicate_clusters"]
    } == {tuple(control_ids), tuple(sorted_ids)}
    assert all(
        item["similarity_basis"] == "MIXED" for item in evaluation["duplicate_clusters"]
    )
    assert all(
        not (
            set(item["member_case_ids"]) & set(control_ids)
            and set(item["member_case_ids"]) & set(sorted_ids)
        )
        for item in evaluation["duplicate_clusters"]
    )
    revised_cluster = next(
        item
        for item in evaluation["duplicate_clusters"]
        if item["member_case_ids"] == sorted_ids
    )
    assert revised_cluster == {
        "duplicate_cluster_id": cluster_id,
        "representative_case_id": representative,
        "member_case_ids": sorted_ids,
        "similarity_basis": "MIXED",
    }
    for case in cases:
        novelty = case["novelty"]
        resolved_assets = (
            personas[case["persona_id"]],
            intents[case["intent_id"]],
            policies[case["turn_policy_id"]],
        )
        reachable_claims = [
            *case["grounding_claims"],
            *(
                claim
                for asset in resolved_assets
                for claim in asset["grounding_claims"]
            ),
        ]
        cited_clusters = sorted(
            {
                citation_cluster[citation_id]
                for claim in reachable_claims
                for citation_id in claim["citation_ids"]
            }
        )
        case_only_clusters = {
            citation_cluster[citation_id]
            for claim in case["grounding_claims"]
            for citation_id in claim["citation_ids"]
        }
        assert set(cited_clusters) > case_only_clusters
        assert novelty["slot_key"] == domain_hash(
            "case-slot",
            {
                "persona_id": case["persona_id"],
                "intent_id": case["intent_id"],
                "turn_policy_id": case["turn_policy_id"],
                "structural_cluster_ids": cited_clusters,
                "stressor_codes": case["scenario"]["stressor_codes"],
                "expected_tool_names": case["scenario"]["expected_tool_names"],
            },
        )
        assert novelty["duplicate_cluster_id"] == cluster_id
        assert novelty["exact_duplicate_of"] == (
            None if case["case_id"] == representative else representative
        )
    review = json.loads(publisher.artifacts["human_review_template.json"])
    assert len(review["review_items"]) == 10
    assert len(evaluation["blind_lineage"]) == 10
    assert {item["blind_id"] for item in review["review_items"]} == {
        item["blind_id"] for item in evaluation["blind_lineage"]
    }


def test_model_declared_gap_is_retained_without_invalidating_case(
    tmp_path: Path,
) -> None:
    api()

    def add_gap(value: dict[str, Any]) -> None:
        value["cases"][0]["gaps"] = ["MODEL_DECLARED_AMBIGUITY"]

    publisher = CapturePublisher()
    callbacks = [
        proposal_callback(),
        critique_callback,
        proposal_callback(mutate=add_gap),
    ]
    result, _, _, _ = invoke(tmp_path, callbacks, publisher=publisher)
    assert result.outcome == "COMPLETED_WITH_GAPS"
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    cases = [
        json.loads(line)
        for line in publisher.artifacts["case_candidates.jsonl"].splitlines()
    ]
    assert evaluation["revised_valid_case_count"] == 5
    assert "MODEL_DECLARED_AMBIGUITY" in evaluation["gap_codes"]
    assert any(item["gaps"] == ["MODEL_DECLARED_AMBIGUITY"] for item in cases)


def test_critic_cannot_score_approve_or_create_truth(tmp_path: Path) -> None:
    api()

    def critic_with_score(_: Any) -> tuple[int, bytes]:
        from conftest import azure_body

        return 200, azure_body({"issues": [], "score": 4, "approved": True})

    publisher = CapturePublisher()
    result, _, _, _ = invoke(
        tmp_path,
        [proposal_callback(), critic_with_score],
        publisher=publisher,
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "CRITIQUE_UNAVAILABLE"
    combined = b"".join(publisher.artifacts.values())
    assert b'"approved"' not in combined
    assert b'"score":4' not in combined
    review = json.loads(publisher.artifacts["human_review_template.json"])
    assert review["review_state"] == "PENDING"


def test_invalid_revised_case_is_local_and_preserves_other_cases_and_positions(
    tmp_path: Path,
) -> None:
    def invalidate_first(value: dict[str, Any]) -> None:
        value["cases"][0]["grounding_claims"][0]["citation_ids"] = ["citation-missing"]

    publisher = CapturePublisher()
    result, _, _, _ = invoke(
        tmp_path,
        [
            proposal_callback(),
            critique_callback,
            proposal_callback(mutate=invalidate_first),
        ],
        publisher=publisher,
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "INVALID_CASE"
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    manifest = json.loads(publisher.artifacts["manifest.json"])
    assert {
        "control_requested_case_count": evaluation["control_requested_case_count"],
        "control_valid_case_count": evaluation["control_valid_case_count"],
        "control_invalid_case_count": evaluation["control_invalid_case_count"],
        "revised_requested_case_count": evaluation["revised_requested_case_count"],
        "revised_valid_case_count": evaluation["revised_valid_case_count"],
        "revised_invalid_case_count": evaluation["revised_invalid_case_count"],
        "revised_raw_n": evaluation["revised_raw_n"],
    } == {
        "control_requested_case_count": 5,
        "control_valid_case_count": 5,
        "control_invalid_case_count": 0,
        "revised_requested_case_count": 5,
        "revised_valid_case_count": 4,
        "revised_invalid_case_count": 1,
        "revised_raw_n": 4,
    }
    assert manifest["requested_case_count"] == 5
    assert manifest["valid_case_count"] == manifest["raw_case_count"] == 4
    assert "INVALID_CASE" in evaluation["gap_codes"]
    assert evaluation["citation_invalid_count"] == 1
    lineage = evaluation["blind_lineage"]
    revised_positions = sorted(
        item["position"] for item in lineage if item["lane"] == "REVISED"
    )
    assert revised_positions == [1, 2, 3, 4]
    assert (
        len(
            json.loads(publisher.artifacts["human_review_template.json"])[
                "review_items"
            ]
        )
        == 9
    )


def test_all_invalid_revised_cases_publish_zero_valid_without_dropping_denominator(
    tmp_path: Path,
) -> None:
    def invalidate_all(value: dict[str, Any]) -> None:
        for case in value["cases"]:
            case["grounding_claims"][0]["citation_ids"] = ["citation-missing"]

    publisher = CapturePublisher()
    result, _, _, _ = invoke(
        tmp_path,
        [
            proposal_callback(),
            critique_callback,
            proposal_callback(mutate=invalidate_all),
        ],
        publisher=publisher,
    )
    assert result.outcome == "COMPLETED_WITH_GAPS"
    assert result.reason_code == "NO_VALID_CASES"
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    manifest = json.loads(publisher.artifacts["manifest.json"])
    assert evaluation["revised_requested_case_count"] == 5
    assert evaluation["revised_valid_case_count"] == 0
    assert evaluation["revised_invalid_case_count"] == 5
    assert evaluation["revised_raw_n"] == evaluation["revised_effective_n"] == 0
    assert evaluation["citation_invalid_count"] == 5
    assert manifest["requested_case_count"] == 5
    assert manifest["valid_case_count"] == manifest["raw_case_count"] == 0
    assert manifest["distinct_case_count"] == manifest["duplicate_case_count"] == 0
    assert (
        len(
            json.loads(publisher.artifacts["human_review_template.json"])[
                "review_items"
            ]
        )
        == 5
    )


def test_near_text_same_tools_collapses_but_ordered_tool_difference_does_not(
    tmp_path: Path,
) -> None:
    def near_text(value: dict[str, Any]) -> None:
        cases = value["cases"]
        cases[0]["scenario"]["expected_tool_names"] = ["tool_a", "tool_b"]
        cases[1]["scenario"]["expected_tool_names"] = ["tool_a", "tool_b"]
        cases[2]["scenario"]["expected_tool_names"] = ["tool_a", "tool_b"]
        cases[3]["scenario"]["expected_tool_names"] = ["tool_b", "tool_a"]
        cases[4]["scenario"]["expected_tool_names"] = ["tool_unique"]
        for index, case in enumerate(cases):
            case["scenario"]["stressor_codes"] = [f"STRESS_{index}"]
            if index < 4:
                case["scenario"]["opening_user_turn"]["text"] = (
                    f"Please carefully complete this supported request variant {index}"
                )
            else:
                case["scenario"]["opening_user_turn"]["text"] = (
                    "Completely unrelated vocabulary for distinct scenario"
                )

    publisher = CapturePublisher()
    invoke(
        tmp_path,
        [
            proposal_callback(mutate=near_text),
            critique_callback,
            proposal_callback(mutate=near_text),
        ],
        publisher=publisher,
    )
    cases = [
        json.loads(line)
        for line in publisher.artifacts["case_candidates.jsonl"].splitlines()
    ]
    by_opening = {item["scenario"]["opening_user_turn"]["text"]: item for item in cases}
    same_tools = [
        by_opening[f"Please carefully complete this supported request variant {index}"]
        for index in range(3)
    ]
    reversed_tools = by_opening[
        "Please carefully complete this supported request variant 3"
    ]
    cluster_ids = {item["novelty"]["duplicate_cluster_id"] for item in same_tools}
    assert len(cluster_ids) == 1
    cluster_id = cluster_ids.pop()
    assert cluster_id is not None
    assert reversed_tools["novelty"]["duplicate_cluster_id"] != cluster_id
    evaluation = json.loads(publisher.artifacts["case_factory_eval.json"])
    component = next(
        item
        for item in evaluation["duplicate_clusters"]
        if item["duplicate_cluster_id"] == cluster_id
    )
    member_ids = sorted(item["case_id"] for item in same_tools)
    assert component == {
        "duplicate_cluster_id": compact_id("duplicate-cluster", member_ids),
        "representative_case_id": member_ids[0],
        "member_case_ids": member_ids,
        "similarity_basis": "NEAR_TEXT",
    }
    assert all(item["novelty"]["exact_duplicate_of"] is None for item in same_tools)
