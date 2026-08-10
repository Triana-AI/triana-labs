"""Black-box contract for provider-disabled post-grounding projection."""

from __future__ import annotations

import hashlib
import importlib
import json
import socket
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest


def _canonical(value: Any, *, newline: bool = False) -> bytes:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return payload + (b"\n" if newline else b"")


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _identity(namespace: str, value: Any) -> str:
    return _sha256(namespace.encode() + b"\0" + _canonical(value))


def _episode(episode_id: str, conversation_id: str) -> dict[str, Any]:
    return {
        "episode_id": episode_id,
        "conversation_id": conversation_id,
        "goal": "Resolve the synthetic order request.",
        "requested_action": "Resolve order",
        "subject": "Synthetic order",
        "constraints": [],
        "fallbacks": [],
        "start_turn_ordinal": 0,
        "end_turn_ordinal": 0,
        "citations": [
            {
                "conversation_id": conversation_id,
                "event_sequence": 0,
                "quote": "Resolve my synthetic order.",
            }
        ],
        "status": "PROPOSED",
        "evidence_ids": [f"evidence-{episode_id}"],
    }


def _population(
    population_id: str, episode_ids: list[str], *, label: str
) -> dict[str, Any]:
    return {
        "population_id": population_id,
        "label": label,
        "definition": f"Synthetic definition for {label}.",
        "episode_ids": episode_ids,
        "support": len(episode_ids),
        "visibility": "PROPOSED_POPULATION",
        "method": "PRIMARY_POPULATION_CONSOLIDATION_V0",
        "audit_state": "SUPPORTED",
        "representative_evidence_ids": [
            f"evidence-{episode_id}" for episode_id in episode_ids[:3]
        ],
    }


def _occurrence(occurrence_id: str, episode_id: str) -> dict[str, Any]:
    return {
        "occurrence_id": occurrence_id,
        "conversation_id": f"conversation-{episode_id}",
        "episode_ids": [episode_id],
        "evidence_ids": [f"behavior-evidence-{episode_id}"],
        "description": "Agent performs the synthetic action.",
    }


def _pattern(
    pattern_id: str, occurrence_ids: list[str], *, label: str
) -> dict[str, Any]:
    return {
        "pattern_id": pattern_id,
        "label": label,
        "definition": f"Synthetic definition for {label}.",
        "occurrence_ids": occurrence_ids,
        "support": len(occurrence_ids),
        "visibility": "SUPPORTED_PATTERN",
        "audit_state": "SUPPORTED",
    }


def _write_projection_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    source_sha256 = "sha256:" + "a" * 64
    selection_sha256 = "sha256:" + "b" * 64
    baseline_predecessor_report_id = "sha256:" + "c" * 64
    exact_episode_ids = [
        "episode-keep-1",
        "episode-keep-2",
        "episode-keep-3",
        "episode-stable-1",
        "episode-stable-2",
        "episode-stable-3",
        "episode-stable-4",
        "episode-stable-5",
        "episode-stable-6",
        "episode-stable-7",
        "episode-stable-8",
    ]
    optional_episode_ids = ["episode-optional-a", "episode-optional-b"]
    rejected_episode_id = "episode-mandatory-invalid"
    predecessor_episodes = [
        _episode(episode_id, f"conversation-{episode_id}")
        for episode_id in exact_episode_ids
        + optional_episode_ids
        + [rejected_episode_id]
    ]
    keep_occurrence_ids = [
        f"occurrence-{episode_id}" for episode_id in exact_episode_ids[:3]
    ]
    changed_occurrence_ids = [
        f"occurrence-{episode_id}"
        for episode_id in exact_episode_ids[3:]
        + [rejected_episode_id, *optional_episode_ids]
    ]
    predecessor: dict[str, Any] = {
        "artifact_kind": "behavior_map_report_v0",
        "schema_version": 0,
        "baseline_predecessor_report_id": baseline_predecessor_report_id,
        "source": {
            "source_sha256": source_sha256,
            "selected_list_sha256": selection_sha256,
            "development_count": 14,
        },
        "accounting": {
            "accepted_conversation_count": 14,
            "semantic_conversation_count": 14,
            "surviving_episode_count": 14,
            "population_assigned_episode_count": 14,
            "supported_population_count": 2,
            "supported_agent_pattern_count": 2,
            "behavior_occurrence_count": 14,
        },
        "episodes": predecessor_episodes,
        "population_dispositions": [
            *[
                {
                    "episode_id": episode_id,
                    "disposition": "ASSIGNED",
                    "population_id": (
                        "population-keep"
                        if episode_id in exact_episode_ids[:3]
                        else "population-change"
                    ),
                    "reason": "POPULATION_MEMBERSHIP",
                }
                for episode_id in exact_episode_ids
                + [rejected_episode_id, *optional_episode_ids]
            ],
        ],
        "populations": [
            _population(
                "population-keep", exact_episode_ids[:3], label="Unchanged demand"
            ),
            _population(
                "population-change",
                exact_episode_ids[3:] + [rejected_episode_id, *optional_episode_ids],
                label="Changed demand",
            ),
        ],
        "behavior_occurrences": [
            *[
                _occurrence(occurrence_id, episode_id)
                for occurrence_id, episode_id in zip(
                    keep_occurrence_ids, exact_episode_ids[:3], strict=True
                )
            ],
            *[
                _occurrence(occurrence_id, episode_id)
                for occurrence_id, episode_id in zip(
                    changed_occurrence_ids,
                    exact_episode_ids[3:]
                    + [rejected_episode_id, *optional_episode_ids],
                    strict=True,
                )
            ],
        ],
        "behavior_patterns": [
            _pattern("pattern-keep", keep_occurrence_ids, label="Unchanged behavior"),
            _pattern(
                "pattern-change", changed_occurrence_ids, label="Changed behavior"
            ),
        ],
        "semantic_audit": {
            "items": [
                {
                    "audit_id": "audit-population-keep",
                    "subject_type": "POPULATION",
                    "subject_id": "population-keep",
                    "ruling": "SUPPORTED",
                },
                {
                    "audit_id": "audit-population-change",
                    "subject_type": "POPULATION",
                    "subject_id": "population-change",
                    "ruling": "SUPPORTED",
                },
                {
                    "audit_id": "audit-pattern-keep",
                    "subject_type": "PATTERN",
                    "subject_id": "pattern-keep",
                    "ruling": "SUPPORTED",
                },
                {
                    "audit_id": "audit-pattern-change",
                    "subject_type": "PATTERN",
                    "subject_id": "pattern-change",
                    "ruling": "SUPPORTED",
                },
            ]
        },
        "budget": {
            "audit_max_reserved_usd": 16.02,
            "audit_reserved_usd": 16.02,
            "total_reserved_usd": 69.912,
            "cumulative_limit_usd": 70.0,
            "primary_actual_cost_usd": None,
            "audit_actual_cost_usd": None,
        },
        "provider_lineage": {
            "primary": {"attempted_call_count": 455},
            "auditor": {
                "attempted_call_count": 115,
                "budget": {
                    "reservation_usd_per_call": 0.18,
                    "reserved_usd": 20.70,
                },
            },
        },
        "gaps": [],
    }
    predecessor["report_id"] = _identity(
        "behavior-map-report-v0",
        {key: value for key, value in predecessor.items() if key != "report_id"},
    )
    predecessor_path = tmp_path / "predecessor.json"
    predecessor_bytes = _canonical(predecessor, newline=True)
    predecessor_path.write_bytes(predecessor_bytes)

    corrected_episodes = [
        deepcopy(row)
        for row in predecessor_episodes
        if row["episode_id"] in exact_episode_ids
    ]
    for suffix, predecessor_episode_id in (
        ("a", "episode-optional-a"),
        ("b", "episode-optional-b"),
    ):
        replacement = _episode(
            f"episode-optional-{suffix}-grounded",
            f"conversation-episode-optional-{suffix}",
        )
        replacement["constraints"] = []
        replacement["field_uncertainties"] = [
            {
                "field": "constraints",
                "reason": "OPTIONAL_FIELD_GROUNDING_REMOVED",
            }
        ]
        replacement["predecessor_episode_candidates"] = [predecessor_episode_id]
        corrected_episodes.append(replacement)
    corrected: dict[str, Any] = {
        "artifact_kind": "behavior_map_grounded_extraction_v0",
        "schema_version": 0,
        "source_sha256": source_sha256,
        "selected_list_sha256": selection_sha256,
        "predecessor_report_id": predecessor["report_id"],
        "episodes": corrected_episodes,
        "rejected_episodes": [
            {
                "predecessor_episode_id": rejected_episode_id,
                "conversation_id": f"conversation-{rejected_episode_id}",
                "reason": "MANDATORY_FIELD_GROUNDING_INVALID",
                "excluded_citations": [
                    {
                        "event_sequence": 1,
                        "reason": "CITATION_ROLE_NOT_PERMITTED",
                    }
                ],
            }
        ],
        "grounding_validation": {
            "valid_episode_count": 13,
            "rejected_episode_count": 1,
            "all_final_grounding_valid": True,
        },
    }
    corrected_path = tmp_path / "corrected-extraction.json"
    corrected_bytes = _canonical(corrected, newline=True)
    corrected_path.write_bytes(corrected_bytes)

    binding = {
        "artifact_kind": "behavior_map_historical_projection_binding_v0",
        "schema_version": 0,
        "privacy_class": "PRIVATE",
        "provider_egress": "DISABLED",
        "predecessor_report_id": predecessor["report_id"],
        "baseline_predecessor_report_id": baseline_predecessor_report_id,
        "predecessor_report_sha256": _sha256(predecessor_bytes),
        "corrected_extraction_sha256": _sha256(corrected_bytes),
        "source_sha256": source_sha256,
        "selected_list_sha256": selection_sha256,
    }
    binding_path = tmp_path / "binding.json"
    binding_path.write_bytes(_canonical(binding, newline=True))
    return predecessor_path, corrected_path, binding_path


def _by_id(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {row[key]: row for row in rows}


def _rewrite_bound_predecessor(
    predecessor_path: Path,
    corrected_path: Path,
    binding_path: Path,
    mutation: str,
) -> None:
    predecessor = json.loads(predecessor_path.read_text())
    if mutation == "NON_INTEGRAL_DECLARED_RESERVE":
        predecessor["budget"]["audit_max_reserved_usd"] = 16.03
    elif mutation == "MISSING_AUDITOR_LINEAGE":
        predecessor["provider_lineage"].pop("auditor")
    elif mutation == "MISSING_AUDITOR_RATE":
        predecessor["provider_lineage"]["auditor"]["budget"].pop(
            "reservation_usd_per_call"
        )
    elif mutation == "CONFLICTING_CEILING_ALIASES":
        predecessor["budget"]["cumulative_budget_ceiling_usd"] = 71.0
    elif mutation == "NON_NULL_PRIMARY_ACTUAL_COST":
        predecessor["budget"]["primary_actual_cost_usd"] = 1.0
    elif mutation == "NON_NULL_AUDIT_ACTUAL_COST":
        predecessor["budget"]["audit_actual_cost_usd"] = 1.0
    elif mutation == "PREDECESSOR_EPISODE_AUDIT_DISPUTED":
        for disposition in predecessor["population_dispositions"]:
            if disposition["episode_id"] == "episode-keep-1":
                disposition.clear()
                disposition.update(
                    {
                        "episode_id": "episode-keep-1",
                        "disposition": "AUDIT_DISPUTED",
                        "reason": "AUDIT_DISAGREEMENT",
                    }
                )
                break
    else:  # pragma: no cover - test setup guard
        raise AssertionError(mutation)
    predecessor["report_id"] = _identity(
        "behavior-map-report-v0",
        {key: value for key, value in predecessor.items() if key != "report_id"},
    )
    predecessor_bytes = _canonical(predecessor, newline=True)
    predecessor_path.write_bytes(predecessor_bytes)

    corrected = json.loads(corrected_path.read_text())
    corrected["predecessor_report_id"] = predecessor["report_id"]
    corrected_bytes = _canonical(corrected, newline=True)
    corrected_path.write_bytes(corrected_bytes)

    binding = json.loads(binding_path.read_text())
    binding["predecessor_report_id"] = predecessor["report_id"]
    binding["predecessor_report_sha256"] = _sha256(predecessor_bytes)
    binding["corrected_extraction_sha256"] = _sha256(corrected_bytes)
    binding_path.write_bytes(_canonical(binding, newline=True))


def test_projection_preserves_only_semantically_unchanged_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = importlib.import_module("triana_labs.behavior_map.historical_projection")
    project = module.project_grounded_behavior_map
    predecessor_path, corrected_path, binding_path = _write_projection_fixture(tmp_path)
    immutable = {
        path: path.read_bytes()
        for path in (predecessor_path, corrected_path, binding_path)
    }

    def refuse_network(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("provider/network access is forbidden")

    monkeypatch.setattr(socket.socket, "connect", refuse_network)
    first = project(
        predecessor_report_path=predecessor_path,
        corrected_extraction_path=corrected_path,
        binding_path=binding_path,
        output_dir=tmp_path / "first",
    )
    second = project(
        predecessor_report_path=predecessor_path,
        corrected_extraction_path=corrected_path,
        binding_path=binding_path,
        output_dir=tmp_path / "second",
    )

    assert first == second
    assert first["artifact_kind"] == "behavior_map_historical_projection_v0"
    assert first["artifact_status"] == "PRIVATE_PROPOSED_PARTIAL_HISTORICAL_PROJECTION"
    assert (
        first["semantic_evaluation_state"] == "HISTORICAL_SEMANTIC_PROJECTION_PARTIAL"
    )
    assert first["claim_boundary"] == {
        "full_reanalysis": False,
        "defect_b_benchmark_pass": False,
        "accepted_taxonomy": False,
        "human_labels": "MISSING",
    }
    binding = json.loads(binding_path.read_text())
    assert first["predecessor_report_id"] == binding["predecessor_report_id"]
    assert (
        first["baseline_predecessor_report_id"]
        == binding["baseline_predecessor_report_id"]
    )
    assert first["binding"] == {
        "predecessor_report_id": binding["predecessor_report_id"],
        "baseline_predecessor_report_id": binding["baseline_predecessor_report_id"],
        "predecessor_report_sha256": binding["predecessor_report_sha256"],
        "corrected_extraction_sha256": binding["corrected_extraction_sha256"],
        "source_sha256": binding["source_sha256"],
        "selected_list_sha256": binding["selected_list_sha256"],
        "provider_egress": "DISABLED",
    }

    episodes = _by_id(first["episodes"], "episode_id")
    assert len(episodes) == 13
    for episode_id in (
        "episode-keep-1",
        "episode-keep-2",
        "episode-keep-3",
        *(f"episode-stable-{index}" for index in range(1, 9)),
    ):
        assert "predecessor_episode_id" not in episodes[episode_id]
    assert episodes["episode-optional-a-grounded"]["predecessor_episode_id"] == (
        "episode-optional-a"
    )
    assert episodes["episode-optional-b-grounded"]["predecessor_episode_id"] == (
        "episode-optional-b"
    )
    excluded_memberships = _by_id(
        first["excluded_population_memberships"], "episode_id"
    )
    assert excluded_memberships["episode-mandatory-invalid"] == {
        "episode_id": "episode-mandatory-invalid",
        "predecessor_population_id": "population-change",
        "reason": "SOURCE_EPISODE_GROUNDING_REJECTED",
        "status": "EXCLUDED_HISTORY",
    }
    assert excluded_memberships["episode-optional-a"] == {
        "episode_id": "episode-optional-a",
        "population_id": "population-change",
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
        "status": "EXCLUDED_HISTORY",
    }
    assert excluded_memberships["episode-optional-b"] == {
        "episode_id": "episode-optional-b",
        "population_id": "population-change",
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
        "status": "EXCLUDED_HISTORY",
    }

    dispositions = _by_id(first["population_dispositions"], "episode_id")
    assert set(dispositions) == set(episodes)
    assert all(
        sum(
            disposition["disposition"] == state
            for state in (
                "ASSIGNED",
                "INTENTIONALLY_UNASSIGNED",
                "AMBIGUOUS",
                "AUDIT_DISPUTED",
            )
        )
        == 1
        for disposition in dispositions.values()
    )
    assert dispositions["episode-optional-a-grounded"] == {
        "episode_id": "episode-optional-a-grounded",
        "disposition": "INTENTIONALLY_UNASSIGNED",
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
    }
    assert dispositions["episode-optional-b-grounded"] == {
        "episode_id": "episode-optional-b-grounded",
        "disposition": "INTENTIONALLY_UNASSIGNED",
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
    }
    for episode_id in (f"episode-stable-{index}" for index in range(1, 9)):
        assert dispositions[episode_id] == {
            "episode_id": episode_id,
            "disposition": "INTENTIONALLY_UNASSIGNED",
            "reason": "REAUDIT_REQUIRED",
        }
    assert first["rejected_episodes"] == [
        {
            "predecessor_episode_id": "episode-mandatory-invalid",
            "conversation_id": "conversation-episode-mandatory-invalid",
            "reason": "MANDATORY_FIELD_GROUNDING_INVALID",
            "status": "EXCLUDED_HISTORY",
            "excluded_citations": [
                {
                    "event_sequence": 1,
                    "reason": "CITATION_ROLE_NOT_PERMITTED",
                }
            ],
        }
    ]

    populations = _by_id(first["populations"], "population_id")
    assert populations["population-keep"]["episode_ids"] == [
        "episode-keep-1",
        "episode-keep-2",
        "episode-keep-3",
    ]
    assert populations["population-keep"]["support"] == 3
    changed_populations = [
        row
        for row in first["populations"]
        if row.get("predecessor_population_id") == "population-change"
    ]
    assert len(changed_populations) == 1
    changed_population = changed_populations[0]
    assert changed_population["population_id"] != "population-change"
    assert changed_population["episode_ids"] == [
        f"episode-stable-{index}" for index in range(1, 9)
    ]
    assert changed_population["support"] == 8
    assert changed_population["audit_state"] == "MISSING"
    assert changed_population["visibility"] == "UNPUBLISHED_AUDIT_MISSING"
    assert changed_population["predecessor_lineage"] == {
        "reason": "GROUNDING_FRONTIER_MEMBERSHIP_CHANGED",
        "affected_episode_ids": [
            "episode-mandatory-invalid",
            "episode-optional-a",
            "episode-optional-b",
        ],
        "before_support": 11,
        "after_support": 8,
    }
    occurrences = _by_id(first["behavior_occurrences"], "occurrence_id")
    assert "occurrence-episode-mandatory-invalid" not in occurrences
    excluded_occurrences = _by_id(
        first["excluded_behavior_occurrences"], "occurrence_id"
    )
    assert excluded_occurrences["occurrence-episode-mandatory-invalid"] == {
        "occurrence_id": "occurrence-episode-mandatory-invalid",
        "episode_ids": ["episode-mandatory-invalid"],
        "reason": "SOURCE_EPISODE_GROUNDING_REJECTED",
        "status": "EXCLUDED_HISTORY",
    }
    assert excluded_occurrences["occurrence-episode-optional-a"] == {
        "occurrence_id": "occurrence-episode-optional-a",
        "episode_ids": ["episode-optional-a"],
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
        "status": "EXCLUDED_HISTORY",
    }
    assert excluded_occurrences["occurrence-episode-optional-b"] == {
        "occurrence_id": "occurrence-episode-optional-b",
        "episode_ids": ["episode-optional-b"],
        "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
        "status": "EXCLUDED_HISTORY",
    }
    patterns = _by_id(first["behavior_patterns"], "pattern_id")
    assert patterns["pattern-keep"]["support"] == 3
    assert patterns["pattern-keep"]["occurrence_ids"] == [
        "occurrence-episode-keep-1",
        "occurrence-episode-keep-2",
        "occurrence-episode-keep-3",
    ]
    changed_patterns = [
        row
        for row in first["behavior_patterns"]
        if row.get("predecessor_pattern_id") == "pattern-change"
    ]
    assert len(changed_patterns) == 1
    changed_pattern = changed_patterns[0]
    assert changed_pattern["pattern_id"] != "pattern-change"
    assert changed_pattern["occurrence_ids"] == [
        f"occurrence-episode-stable-{index}" for index in range(1, 9)
    ]
    assert changed_pattern["support"] == 8
    assert changed_pattern["audit_state"] == "MISSING"
    assert changed_pattern["visibility"] == "UNPUBLISHED_AUDIT_MISSING"
    assert changed_pattern["predecessor_lineage"] == {
        "reason": "GROUNDING_FRONTIER_OCCURRENCE_MEMBERSHIP_CHANGED",
        "affected_occurrence_ids": [
            "occurrence-episode-mandatory-invalid",
            "occurrence-episode-optional-a",
            "occurrence-episode-optional-b",
        ],
        "before_support": 11,
        "after_support": 8,
    }

    audits = _by_id(first["semantic_audit"]["current_items"], "audit_id")
    assert set(audits) == {"audit-population-keep", "audit-pattern-keep"}
    assert audits["audit-population-keep"]["ruling"] == "SUPPORTED"
    assert audits["audit-pattern-keep"]["ruling"] == "SUPPORTED"
    historical_audits = _by_id(first["semantic_audit"]["historical_items"], "audit_id")
    assert set(historical_audits) == {
        "audit-population-change",
        "audit-pattern-change",
    }
    assert historical_audits["audit-population-change"]["history_status"] == (
        "SUPERSEDED_SUBJECT_HISTORY_ONLY"
    )
    assert historical_audits["audit-pattern-change"]["history_status"] == (
        "SUPERSEDED_SUBJECT_HISTORY_ONLY"
    )

    assert first["accounting"] == {
        "predecessor_episode_count": 14,
        "corrected_episode_count": 13,
        "exact_unchanged_episode_count": 11,
        "replacement_episode_count": 2,
        "rejected_episode_count": 1,
        "assigned_episode_count": 3,
        "unassigned_episode_count": 10,
        "population_count": 2,
        "supported_population_count": 1,
        "supported_population_support": 3,
        "unpublished_candidate_population_count": 1,
        "unpublished_candidate_population_membership_count": 8,
        "behavior_occurrence_count": 11,
        "excluded_behavior_occurrence_count": 3,
        "pattern_count": 2,
        "pattern_support": 11,
    }
    assert first["population_membership_edge_conservation"] == {
        "before": 14,
        "exact_preserved": 3,
        "explicitly_superseded": 8,
        "excluded_rejected": 1,
        "excluded_grounding_replacement": 2,
        "unexplained": 0,
    }
    assert first["pattern_occurrence_edge_conservation"] == {
        "before": 14,
        "exact_preserved": 3,
        "explicitly_superseded": 8,
        "excluded_rejected": 1,
        "excluded_grounding_replacement": 2,
        "unexplained": 0,
    }
    assert first["budget"] == {
        "historical_primary_attempted_call_count": 455,
        "historical_audit_declared_call_cap": 89,
        "historical_audit_declared_reserved_usd": 16.02,
        "historical_audit_attempted_call_count": 115,
        "historical_audit_excess_call_count": 26,
        "historical_audit_observed_reserved_usd": 20.70,
        "historical_total_reserved_usd": 69.912,
        "historical_cumulative_budget_ceiling_usd": 70.0,
        "historical_total_within_cumulative_ceiling": True,
        "historical_actual_cost_state": "UNKNOWN",
        "historical_budget_state": "SEMANTIC_LANE_BUDGET_CONTRACT_EXCEEDED",
        "projection_primary_attempted_call_count": 0,
        "projection_audit_attempted_call_count": 0,
    }
    assert {gap["code"] for gap in first["gaps"]} >= {
        "HUMAN_LABELS_MISSING",
        "HISTORICAL_PROJECTION_NOT_FULL_REANALYSIS",
    }
    assert all(path.read_bytes() == content for path, content in immutable.items())
    assert (
        tmp_path / "first" / "behavior_map_historical_projection.json"
    ).read_bytes() == (
        tmp_path / "second" / "behavior_map_historical_projection.json"
    ).read_bytes()


@pytest.mark.parametrize(
    ("target", "field"),
    [
        ("binding", "predecessor_report_id"),
        ("binding", "baseline_predecessor_report_id"),
        ("binding", "predecessor_report_sha256"),
        ("binding", "corrected_extraction_sha256"),
        ("binding", "source_sha256"),
        ("binding", "selected_list_sha256"),
        ("corrected", "predecessor_report_id"),
        ("corrected", "source_sha256"),
        ("corrected", "selected_list_sha256"),
    ],
)
def test_projection_refuses_any_binding_mismatch_before_publication(
    tmp_path: Path, target: str, field: str
) -> None:
    module = importlib.import_module("triana_labs.behavior_map.historical_projection")
    project = module.project_grounded_behavior_map
    error_type = module.HistoricalProjectionError
    predecessor_path, corrected_path, binding_path = _write_projection_fixture(tmp_path)
    target_path = binding_path if target == "binding" else corrected_path
    payload = json.loads(target_path.read_text())
    payload[field] = "sha256:" + "f" * 64
    target_path.write_bytes(_canonical(payload, newline=True))
    output_dir = tmp_path / "refused"

    with pytest.raises(error_type) as exc_info:
        project(
            predecessor_report_path=predecessor_path,
            corrected_extraction_path=corrected_path,
            binding_path=binding_path,
            output_dir=output_dir,
        )

    assert exc_info.value.code == "HISTORICAL_PROJECTION_BINDING_INVALID"
    assert not output_dir.exists()


def test_projection_refuses_missing_accepted_baseline_lineage_before_publication(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("triana_labs.behavior_map.historical_projection")
    project = module.project_grounded_behavior_map
    error_type = module.HistoricalProjectionError
    predecessor_path, corrected_path, binding_path = _write_projection_fixture(tmp_path)
    binding = json.loads(binding_path.read_text())
    binding.pop("baseline_predecessor_report_id")
    binding_path.write_bytes(_canonical(binding, newline=True))
    output_dir = tmp_path / "refused-missing-baseline"

    with pytest.raises(error_type) as exc_info:
        project(
            predecessor_report_path=predecessor_path,
            corrected_extraction_path=corrected_path,
            binding_path=binding_path,
            output_dir=output_dir,
        )

    assert exc_info.value.code == "HISTORICAL_PROJECTION_BINDING_INVALID"
    assert not output_dir.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "NON_INTEGRAL_DECLARED_RESERVE",
        "MISSING_AUDITOR_LINEAGE",
        "MISSING_AUDITOR_RATE",
        "CONFLICTING_CEILING_ALIASES",
        "NON_NULL_PRIMARY_ACTUAL_COST",
        "NON_NULL_AUDIT_ACTUAL_COST",
    ],
)
def test_projection_refuses_invalid_legacy_budget_lineage_before_publication(
    tmp_path: Path, mutation: str
) -> None:
    module = importlib.import_module("triana_labs.behavior_map.historical_projection")
    project = module.project_grounded_behavior_map
    error_type = module.HistoricalProjectionError
    predecessor_path, corrected_path, binding_path = _write_projection_fixture(tmp_path)
    _rewrite_bound_predecessor(predecessor_path, corrected_path, binding_path, mutation)
    output_dir = tmp_path / "refused-budget-lineage"

    with pytest.raises(error_type) as exc_info:
        project(
            predecessor_report_path=predecessor_path,
            corrected_extraction_path=corrected_path,
            binding_path=binding_path,
            output_dir=output_dir,
        )

    assert exc_info.value.code == "HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID"
    assert not output_dir.exists()


def test_projection_never_restores_predecessor_dispute_without_current_support(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("triana_labs.behavior_map.historical_projection")
    project = module.project_grounded_behavior_map
    predecessor_path, corrected_path, binding_path = _write_projection_fixture(tmp_path)
    _rewrite_bound_predecessor(
        predecessor_path,
        corrected_path,
        binding_path,
        "PREDECESSOR_EPISODE_AUDIT_DISPUTED",
    )

    report = project(
        predecessor_report_path=predecessor_path,
        corrected_extraction_path=corrected_path,
        binding_path=binding_path,
        output_dir=tmp_path / "dispute-preserved",
    )

    disposition = next(
        row
        for row in report["population_dispositions"]
        if row["episode_id"] == "episode-keep-1"
    )
    assert disposition == {
        "episode_id": "episode-keep-1",
        "disposition": "AUDIT_DISPUTED",
        "reason": "PREDECESSOR_AUDIT_DISPUTE_PRESERVED",
    }
    assert all(
        "episode-keep-1" not in population["episode_ids"]
        for population in report["populations"]
    )
    assert any(
        row
        == {
            "episode_id": "episode-keep-1",
            "predecessor_population_id": "population-keep",
            "reason": "PREDECESSOR_AUDIT_DISPUTED",
            "status": "EXCLUDED_HISTORY",
        }
        for row in report["excluded_population_memberships"]
    )
    assert (
        report["population_membership_edge_conservation"]["excluded_audit_disputed"]
        == 1
    )
    assert report["population_membership_edge_conservation"]["unexplained"] == 0
