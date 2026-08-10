"""Acceptance contract for the private, deterministic Behavior Map comparison."""

from __future__ import annotations

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from triana_labs.behavior_map import run_behavior_map


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return payload + (b"\n" if lf else b"")


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _write_manifest(
    tmp_path: Path, *, predecessor_report_id: str | None
) -> tuple[Path, str]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    selected_ids = ["selected-b", "selected-a"]
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": trace_id,
            "source_trace_id": f"source-{trace_id}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": "Synthetic request.",
                },
                {
                    "sequence": 1,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "Synthetic response.",
                    "is_final": True,
                },
            ],
        }
        for trace_id in selected_ids
    ]
    source = tmp_path / "traces.jsonl"
    source_payload = b"".join(_canonical(trace, lf=True) for trace in traces)
    source.write_bytes(source_payload)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "predecessor_report_id": predecessor_report_id,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": _sha256(source_payload),
            "physical_record_count": 2,
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "comparison-lineage"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": False,
                "model_id": None,
                "audit_model_id": None,
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {
                    "group_id": f"group-{trace_id}",
                    "trace_ids": [trace_id],
                }
                for trace_id in selected_ids
            ],
        },
        "semantic_scope": {
            "allowed_trace_ids": selected_ids,
            "sealed_counts": {"calibration": 0, "holdout": 0},
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": False,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": None,
        "existing_evals": None,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    selection_hash = _sha256(_canonical(sorted(selected_ids)))
    return manifest_path, selection_hash


def _report(
    report_id: str,
    *,
    episodes: int,
    assigned: int,
    populations: int,
    predecessor: str | None = None,
) -> dict[str, Any]:
    episode_rows = [
        {"episode_id": f"episode-{index}", "conversation_id": f"conversation-{index}"}
        for index in range(episodes)
    ]
    population_rows = [
        {
            "population_id": f"population-{index}",
            "episode_ids": [
                f"episode-{member}" for member in range(index, min(index + 2, assigned))
            ],
            "support": min(2, max(0, assigned - index)),
        }
        for index in range(populations)
    ]
    return {
        "artifact_kind": "behavior_map_report_v0",
        "schema_version": 0,
        "report_id": report_id,
        "predecessor_report_id": predecessor,
        "source": {
            "adapter_id": "synthetic",
            "source_sha256": "sha256:" + "a" * 64,
            "selected_list_sha256": "sha256:" + "c" * 64,
            "development_count": 10,
        },
        "accounting": {
            "accepted_conversation_count": 10,
            "semantic_conversation_count": 10,
            "sealed_calibration_count": 2,
            "sealed_holdout_count": 2,
            "surviving_episode_count": episodes,
            "population_assigned_episode_count": assigned,
        },
        "episodes": episode_rows,
        "populations": population_rows,
        "behavior_patterns": [],
        "behavior_occurrences": [],
        "gaps": [],
        "semantic_audit": {"items": []},
        "budget": {
            "total_reserved_usd": 0.0,
            "primary_actual_cost_usd": None,
            "audit_actual_cost_usd": None,
        },
    }


class _ExactLineageModel:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        self.requests: list[dict[str, Any]] = []

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.requests.append(
            {"stage": stage, "system": system, "payload": deepcopy(payload)}
        )
        fields = set(schema.model_fields)
        if "episodes" in fields and "behaviors" in fields:
            proposal = {
                "local_id": "demand",
                "goal": "Locate an order",
                "requested_action": "FIND_ORDER",
                "subject": "order",
                "constraints": [],
                "fallbacks": [],
                "supersedes_local_id": None,
                "start_turn_ordinal": 0,
                "end_turn_ordinal": 1,
                "citations": [
                    {
                        "conversation_id": "selected-a",
                        "event_sequence": 0,
                        "quote": "Synthetic request.",
                    }
                ],
                "field_grounding": {
                    "goal": [0],
                    "requested_action": [0],
                    "subject": [0],
                    "constraints": [],
                    "fallbacks": [],
                },
                "status": "PROPOSED",
            }
            episode_schema = schema.model_json_schema()["$defs"]["EpisodeProposal"]
            if "grounding_contract_version" in episode_schema["properties"]:
                proposal["grounding_contract_version"] = 1
            return {
                "episodes": [proposal]
                if payload["conversations"][0]["conversation_id"] == "selected-a"
                else [],
                "behaviors": (
                    [
                        {
                            "local_id": "response",
                            "lane": "SEMANTIC",
                            "action": "ACKNOWLEDGED_REQUEST",
                            "object": "order lookup",
                            "condition": "after a location request",
                            "observed_effect": None,
                            "episode_local_ids": ["demand"],
                            "citations": [
                                {
                                    "conversation_id": "selected-a",
                                    "event_sequence": 1,
                                    "quote": "Synthetic response.",
                                }
                            ],
                            "event_ids": [],
                            "status": "PROPOSED",
                        }
                    ]
                    if payload["conversations"][0]["conversation_id"] == "selected-a"
                    else []
                ),
            }
        if "populations" in fields:
            episodes = [
                row for row in payload.get("episodes", []) if "episode_id" in row
            ]
            return {
                "populations": [
                    {
                        "label": "Order lookup requests",
                        "definition": "Customers ask to locate an order.",
                        "episode_ids": [row["episode_id"] for row in episodes],
                    }
                ]
                if episodes
                else [],
                "unassigned_episode_ids": [],
                "ambiguous_episode_ids": [],
            }
        if "patterns" in fields:
            occurrences = payload.get("behavior_occurrences", [])
            return {
                "patterns": [
                    {
                        "label": "Acknowledges an order lookup request",
                        "definition": "The agent acknowledges the request before acting.",
                        "occurrence_ids": [row["occurrence_id"] for row in occurrences],
                    }
                ]
                if occurrences
                else []
            }
        if "audits" in fields:
            return {
                "audits": [
                    {
                        "item_id": next(
                            row[key]
                            for key in ("episode_id", "population_id", "pattern_id")
                            if key in row
                        ),
                        "decision": "SUPPORTED",
                        "reason": "Synthetic audit.",
                    }
                    for row in payload.get("items", [])
                ]
            }
        if "matches" in fields:
            return {"matches": []}
        raise AssertionError(stage)

    def lineage(self) -> dict[str, Any]:
        return {
            "provider": "SYNTHETIC_TEST_BOUNDARY",
            "model_id": self.model_id,
            "provider_calls": 0,
            "budget": {
                "max_reserved_usd": 0.0,
                "reserved_usd": 0.0,
                "reservation_usd_per_call": 0.0,
            },
            "retry_policy": "NONE",
            "fallback_policy": "NONE",
        }


class _PreEgressTrap:
    model_id = "legacy-trap"

    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, **_: Any) -> dict[str, Any]:
        self.calls += 1
        raise AssertionError("legacy predecessor validation must occur before egress")

    def lineage(self) -> dict[str, Any]:
        return {
            "provider": "SYNTHETIC_TEST_BOUNDARY",
            "model_id": self.model_id,
            "provider_calls": 0,
            "budget": {"max_reserved_usd": 0.0},
            "retry_policy": "NONE",
            "fallback_policy": "NONE",
        }


def test_comparison_writes_separate_hash_addressed_json_markdown_and_html(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=3, assigned=2, populations=1)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=4,
        assigned=3,
        populations=2,
        predecessor=before["report_id"],
    )
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))

    result = compare_behavior_maps(before_path, after_path, tmp_path / "comparison")

    assert result["artifact_kind"] == "behavior_map_comparison_v0"
    assert result["before_report_id"] == before["report_id"]
    assert result["after_report_id"] == after["report_id"]
    assert result["lineage_state"] == "EXPLICIT_PREDECESSOR"
    assert result["mechanical_movement"] == {
        "surviving_episode_count": {"before": 3, "after": 4, "delta": 1},
        "population_assigned_episode_count": {"before": 2, "after": 3, "delta": 1},
        "supported_population_count": {"before": 1, "after": 2, "delta": 1},
    }
    assert result["semantic_benchmark"] == {
        metric: {"state": "HUMAN_LABELS_MISSING", "value": None}
        for metric in (
            "demand_extraction_precision",
            "demand_extraction_recall",
            "no_demand_specificity",
            "multi_goal_boundary_accuracy",
            "population_assignment_accuracy",
            "pairwise_population_precision",
            "pairwise_population_recall",
            "novel_demand_preservation",
            "ambiguity_preservation",
            "batch_order_stability",
        )
    }
    assert result["conclusion"] == "MECHANICAL_MOVEMENT_ONLY"
    paths = [
        tmp_path / "comparison" / "behavior-map-comparison.json",
        tmp_path / "comparison" / "behavior-map-comparison.md",
        tmp_path / "comparison" / "behavior-map-comparison.html",
    ]
    assert all(path.exists() for path in paths)
    stored = json.loads(paths[0].read_text())
    identity_input = {
        key: value for key, value in stored.items() if key != "comparison_id"
    }
    assert stored["comparison_id"] == _sha256(
        b"behavior-map-comparison-v0\0" + _canonical(identity_input)
    )
    assert "Semantic benchmark: HUMAN_LABELS_MISSING" in paths[1].read_text()
    assert "MECHANICAL_MOVEMENT_ONLY" in paths[2].read_text()


def test_comparison_refuses_noncomparable_source_or_missing_predecessor_lineage(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=3, assigned=2, populations=1)
    after = _report("sha256:" + "2" * 64, episodes=4, assigned=3, populations=2)
    after["source"]["source_sha256"] = "sha256:" + "b" * 64
    after["source"]["selected_list_sha256"] = "sha256:" + "d" * 64
    after["accounting"]["sealed_holdout_count"] = 3
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))

    result = compare_behavior_maps(before_path, after_path, tmp_path / "comparison")

    assert result["lineage_state"] == "NONCOMPARABLE"
    assert result["conclusion"] == "NONCOMPARABLE"
    assert {gap["code"] for gap in result["gaps"]} == {
        "COMPARISON_PREDECESSOR_LINEAGE_MISSING",
        "COMPARISON_SEALED_SPLIT_MISMATCH",
        "COMPARISON_SELECTION_MISMATCH",
        "COMPARISON_SOURCE_MISMATCH",
    }
    assert all(row["delta"] is None for row in result["mechanical_movement"].values())


def test_comparison_is_byte_identical_and_never_mutates_inputs(tmp_path: Path) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=3, assigned=2, populations=1)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=4,
        assigned=3,
        populations=2,
        predecessor=before["report_id"],
    )
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))
    input_hashes = (_sha256(before_path.read_bytes()), _sha256(after_path.read_bytes()))

    compare_behavior_maps(before_path, after_path, tmp_path / "first")
    compare_behavior_maps(before_path, after_path, tmp_path / "second")

    for filename in (
        "behavior-map-comparison.json",
        "behavior-map-comparison.md",
        "behavior-map-comparison.html",
    ):
        assert (tmp_path / "first" / filename).read_bytes() == (
            tmp_path / "second" / filename
        ).read_bytes()
    assert (
        _sha256(before_path.read_bytes()),
        _sha256(after_path.read_bytes()),
    ) == input_hashes


def test_generated_report_projects_valid_predecessor_and_selection_lineage(
    tmp_path: Path,
) -> None:
    predecessor = "sha256:" + "1" * 64
    manifest, selection_hash = _write_manifest(
        tmp_path, predecessor_report_id=predecessor
    )

    report = run_behavior_map(
        manifest,
        tmp_path / "output",
        agent_context="Synthetic agent.",
    )

    assert report["predecessor_report_id"] == predecessor
    assert report["source"]["selected_list_sha256"] == selection_hash
    assert report["source"]["development_count"] == 2

    invalid_manifest, _ = _write_manifest(
        tmp_path / "invalid", predecessor_report_id="not-a-report-digest"
    )
    with pytest.raises(ValueError, match="MANIFEST_INVALID"):
        run_behavior_map(
            invalid_manifest,
            tmp_path / "invalid" / "output",
            agent_context="Synthetic agent.",
        )


def test_runtime_predecessor_sidecar_is_exact_private_and_projects_semantic_lineage(
    tmp_path: Path,
) -> None:
    predecessor_id = "sha256:" + "1" * 64
    manifest_path, selection_hash = _write_manifest(
        tmp_path, predecessor_report_id=predecessor_id
    )
    manifest = json.loads(manifest_path.read_bytes())
    predecessor = {
        "artifact_kind": "behavior_map_report_v0",
        "schema_version": 0,
        "report_id": predecessor_id,
        "source": {
            "source_sha256": manifest["source"]["sha256"],
            "selected_list_sha256": selection_hash,
            "development_count": 2,
        },
        "accounting": {"sealed_calibration_count": 0, "sealed_holdout_count": 0},
        "episodes": [
            {
                "episode_id": "legacy-episode",
                "conversation_id": "selected-a",
                "goal": "Locate an order",
                "requested_action": "FIND_ORDER",
                "subject": "order",
                "constraints": [],
                "fallbacks": [],
                "start_turn_ordinal": 0,
                "end_turn_ordinal": 1,
                "citations": [
                    {
                        "conversation_id": "selected-a",
                        "turn_ordinal": 0,
                        "quote": "Synthetic request.",
                    }
                ],
                "status": "PROPOSED",
            }
        ],
        "populations": [
            {
                "population_id": "legacy-population",
                "label": "Order lookup requests",
                "definition": "Customers ask to locate an order.",
                "episode_ids": ["legacy-episode"],
                "support": 1,
            }
        ],
        "behavior_occurrences": [
            {
                "occurrence_id": "legacy-occurrence",
                "action": "ACKNOWLEDGED_REQUEST",
                "object": "order lookup",
                "condition": "after a location request",
                "observed_effect": None,
                "episode_ids": ["legacy-episode"],
            }
        ],
        "behavior_patterns": [
            {
                "pattern_id": "legacy-pattern",
                "label": "Acknowledges an order lookup request",
                "definition": "The agent acknowledges the request before acting.",
                "occurrence_ids": ["legacy-occurrence"],
                "support": 1,
            }
        ],
    }
    predecessor_path = tmp_path / "predecessor.json"
    predecessor_path.write_bytes(_canonical(predecessor, lf=True))
    manifest["predecessor_report_path"] = str(predecessor_path)
    manifest["privacy"]["provider_egress"] = {
        "authorized": True,
        "model_id": "lineage-author",
        "audit_model_id": "lineage-auditor",
    }
    manifest_path.write_bytes(_canonical(manifest, lf=True))

    primary_model = _ExactLineageModel("lineage-author")
    audit_model = _ExactLineageModel("lineage-auditor")
    report = run_behavior_map(
        manifest_path,
        tmp_path / "output",
        primary_model=primary_model,
        audit_model=audit_model,
        agent_context="Synthetic agent.",
    )

    episode = next(
        row for row in report["episodes"] if row["conversation_id"] == "selected-a"
    )
    assert episode["predecessor_episode_id"] == "legacy-episode"
    population = next(
        row for row in report["populations"] if row["label"] == "Order lookup requests"
    )
    assert population["predecessor_population_ids"] == ["legacy-population"]
    assert population["predecessor_lineage"] == {
        "reason": "EXACT_MAPPED_MEMBERSHIP",
        "overlap_episode_ids": [episode["episode_id"]],
        "before_support": 1,
        "after_support": 1,
    }
    pattern = next(
        row
        for row in report["behavior_patterns"]
        if row["label"] == "Acknowledges an order lookup request"
    )
    assert pattern["predecessor_pattern_ids"] == ["legacy-pattern"]
    assert (
        pattern["predecessor_lineage"]["reason"]
        == "EXACT_BEHAVIOR_SEMANTICS_AND_MAPPED_EPISODE"
    )
    assert "predecessor_report_path" not in json.dumps(report)
    assert str(predecessor_path) not in json.dumps(
        [*primary_model.requests, *audit_model.requests]
    )

    ambiguous_predecessor = {
        **predecessor,
        "episodes": [
            *predecessor["episodes"],
            {**predecessor["episodes"][0], "episode_id": "legacy-episode-duplicate"},
        ],
    }
    ambiguous_path = tmp_path / "ambiguous.json"
    ambiguous_path.write_bytes(_canonical(ambiguous_predecessor, lf=True))
    manifest["predecessor_report_path"] = str(ambiguous_path)
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    ambiguous = run_behavior_map(
        manifest_path,
        tmp_path / "ambiguous-output",
        primary_model=_ExactLineageModel("lineage-author"),
        audit_model=_ExactLineageModel("lineage-auditor"),
        agent_context="Synthetic agent.",
    )
    ambiguous_episode = next(
        row for row in ambiguous["episodes"] if row["conversation_id"] == "selected-a"
    )
    assert "predecessor_episode_id" not in ambiguous_episode
    assert any(
        gap["code"] == "PREDECESSOR_EPISODE_MAPPING_AMBIGUOUS"
        and gap["episode_id"] == ambiguous_episode["episode_id"]
        for gap in ambiguous["gaps"]
    )

    symlink_path = tmp_path / "predecessor-link.json"
    symlink_path.symlink_to(predecessor_path)
    manifest["predecessor_report_path"] = str(symlink_path)
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    with pytest.raises(ValueError, match="PREDECESSOR_REPORT_PATH_INVALID"):
        run_behavior_map(
            manifest_path, tmp_path / "symlink-output", agent_context="Synthetic agent."
        )

    mismatched = {
        **predecessor,
        "source": {**predecessor["source"], "source_sha256": "sha256:" + "f" * 64},
    }
    mismatched_path = tmp_path / "mismatched.json"
    mismatched_path.write_bytes(_canonical(mismatched, lf=True))
    manifest["predecessor_report_path"] = str(mismatched_path)
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    with pytest.raises(ValueError, match="PREDECESSOR_REPORT_MISMATCH"):
        run_behavior_map(
            manifest_path,
            tmp_path / "mismatch-output",
            agent_context="Synthetic agent.",
        )


def _write_legacy_predecessor_fixture(
    root: Path,
) -> tuple[Path, Path, dict[str, Any], str]:
    root.mkdir(parents=True, exist_ok=True)
    trace_ids = [f"legacy-{index:03d}" for index in range(374)]
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": trace_id,
            "source_trace_id": f"source-{trace_id}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": "Synthetic request.",
                }
            ],
        }
        for trace_id in trace_ids
    ]
    source = root / "traces.jsonl"
    source_bytes = b"".join(_canonical(trace, lf=True) for trace in traces)
    source.write_bytes(source_bytes)
    source_sha256 = _sha256(source_bytes)
    selection_sha256 = _sha256(_canonical(sorted(trace_ids)))
    predecessor: dict[str, Any] = {
        "artifact_kind": "behavior_map_report_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "source_sha256": source_sha256,
        },
        "accounting": {
            "accepted_conversation_count": 624,
            "semantic_conversation_count": 374,
            "sealed_calibration_count": 125,
            "sealed_holdout_count": 125,
        },
        "episodes": [],
        "populations": [],
        "behavior_patterns": [],
        "behavior_occurrences": [],
        "gaps": [],
        "semantic_audit": {"items": []},
    }
    predecessor["report_id"] = _sha256(
        b"behavior-map-report-v0\0" + _canonical(predecessor)
    )
    predecessor_path = root / "legacy-predecessor.json"
    predecessor_path.write_bytes(_canonical(predecessor, lf=True))
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "predecessor_report_id": predecessor["report_id"],
        "predecessor_report_path": str(predecessor_path),
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": source_sha256,
            "physical_record_count": 374,
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "legacy-agent"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": False,
                "model_id": None,
                "audit_model_id": None,
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {"group_id": f"group-{trace_id}", "trace_ids": [trace_id]}
                for trace_id in trace_ids
            ],
        },
        "semantic_scope": {
            "allowed_trace_ids": trace_ids,
            "selection": {
                "selected_list_sha256": selection_sha256,
                "development_count": 374,
            },
            "sealed_counts": {"calibration": 125, "holdout": 125},
        },
        "capabilities": {
            "paired_arms": False,
            "outcomes": False,
            "existing_evals": False,
            "embeddings": False,
        },
        "outcomes": None,
        "existing_evals": None,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    return manifest_path, predecessor_path, predecessor, selection_sha256


def test_exact_legacy_predecessor_without_new_source_fields_is_compatible(
    tmp_path: Path,
) -> None:
    manifest_path, _predecessor_path, predecessor, _selection = (
        _write_legacy_predecessor_fixture(tmp_path)
    )

    report = run_behavior_map(
        manifest_path,
        tmp_path / "output",
        primary_model=None,
        audit_model=None,
        agent_context="Synthetic agent.",
    )

    assert report["predecessor_report_id"] == predecessor["report_id"]
    assert report["source"]["development_count"] == 374
    assert report["accounting"]["sealed_calibration_count"] == 125
    assert report["accounting"]["sealed_holdout_count"] == 125


@pytest.mark.parametrize(
    "tamper",
    [
        "report_id",
        "content_identity",
        "source",
        "semantic_count",
        "sealed",
        "manifest_selection_hash",
        "manifest_development_count",
    ],
)
def test_legacy_predecessor_compatibility_refuses_any_exact_control_mismatch(
    tmp_path: Path, tamper: str
) -> None:
    manifest_path, predecessor_path, predecessor, _selection = (
        _write_legacy_predecessor_fixture(tmp_path)
    )
    manifest = json.loads(manifest_path.read_bytes())
    if tamper == "report_id":
        predecessor["report_id"] = "sha256:" + "0" * 64
    elif tamper == "content_identity":
        predecessor["gaps"] = [{"code": "TAMPERED", "stage": "TEST"}]
    elif tamper == "source":
        predecessor["source"]["source_sha256"] = "sha256:" + "0" * 64
    elif tamper == "semantic_count":
        predecessor["accounting"]["semantic_conversation_count"] = 373
    elif tamper == "sealed":
        predecessor["accounting"]["sealed_holdout_count"] = 124
    elif tamper == "manifest_selection_hash":
        manifest["semantic_scope"]["selection"]["selected_list_sha256"] = (
            "sha256:" + "0" * 64
        )
    else:
        manifest["semantic_scope"]["selection"]["development_count"] = 373
    if tamper not in {
        "report_id",
        "content_identity",
        "manifest_selection_hash",
        "manifest_development_count",
    }:
        predecessor.pop("report_id")
        predecessor["report_id"] = _sha256(
            b"behavior-map-report-v0\0" + _canonical(predecessor)
        )
        manifest["predecessor_report_id"] = predecessor["report_id"]
    predecessor_path.write_bytes(_canonical(predecessor, lf=True))
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    trap = _PreEgressTrap()

    with pytest.raises(ValueError, match="PREDECESSOR_REPORT_MISMATCH"):
        run_behavior_map(
            manifest_path,
            tmp_path / "output",
            primary_model=trap,
            audit_model=None,
            agent_context="Synthetic agent.",
        )
    assert trap.calls == 0


def test_comparison_derives_immutable_baseline_selection_from_sidecar(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=3, assigned=2, populations=1)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=4,
        assigned=3,
        populations=2,
        predecessor=before["report_id"],
    )
    selection_ids = ["selected-conversation"]
    selection_hash = _sha256(_canonical(selection_ids))
    before["source"].pop("selected_list_sha256")
    after["source"]["selected_list_sha256"] = selection_hash
    before_root = tmp_path / "before"
    after_root = tmp_path / "after"
    (before_root / "report").mkdir(parents=True)
    (after_root / "report").mkdir(parents=True)
    before_path = before_root / "report" / "behavior-map.json"
    after_path = after_root / "report" / "behavior-map.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))
    (before_root / "manifest.json").write_bytes(
        _canonical(
            {
                "artifact_kind": "evidence_bundle_manifest_v0",
                "schema_version": 0,
                "semantic_scope": {"allowed_trace_ids": selection_ids},
            },
            lf=True,
        )
    )

    result = compare_behavior_maps(
        before_path, after_path, tmp_path / "comparison-with-sidecar"
    )
    assert result["lineage_state"] == "EXPLICIT_PREDECESSOR"

    before_without_sidecar = tmp_path / "no-sidecar" / "report"
    before_without_sidecar.mkdir(parents=True)
    absent_before_path = before_without_sidecar / "behavior-map.json"
    absent_before_path.write_bytes(_canonical(before, lf=True))
    after_without_hash = json.loads(_canonical(after))
    after_without_hash["source"].pop("selected_list_sha256")
    absent_after_path = tmp_path / "after-without-hash.json"
    absent_after_path.write_bytes(_canonical(after_without_hash, lf=True))
    absent = compare_behavior_maps(
        absent_before_path, absent_after_path, tmp_path / "comparison-absent"
    )
    assert absent["lineage_state"] == "NONCOMPARABLE"
    assert "COMPARISON_SELECTION_MISSING" in {gap["code"] for gap in absent["gaps"]}


def test_comparison_prefers_authoritative_legacy_nested_selection_hash(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=3, assigned=2, populations=1)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=4,
        assigned=3,
        populations=2,
        predecessor=before["report_id"],
    )
    authoritative_selection = after["source"]["selected_list_sha256"]
    before["source"].pop("selected_list_sha256")
    before_root = tmp_path / "before"
    (before_root / "report").mkdir(parents=True)
    before_path = before_root / "report" / "behavior-map.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))
    manifest_path = before_root / "manifest.json"
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "semantic_scope": {
            # This legacy projection is not the selection authority. Its
            # recomputed hash deliberately differs from the frozen nested hash.
            "allowed_trace_ids": ["legacy-visible-conversation"],
            "selection": {
                "selected_list_sha256": authoritative_selection,
                "development_count": 10,
            },
        },
    }
    manifest_path.write_bytes(_canonical(manifest, lf=True))

    comparable = compare_behavior_maps(before_path, after_path, tmp_path / "comparison")
    assert comparable["lineage_state"] == "EXPLICIT_PREDECESSOR"
    assert comparable["conclusion"] == "MECHANICAL_MOVEMENT_ONLY"
    assert comparable["gaps"] == []

    manifest["semantic_scope"]["selection"]["selected_list_sha256"] = (
        "sha256:" + "d" * 64
    )
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    tampered = compare_behavior_maps(
        before_path, after_path, tmp_path / "comparison-tampered"
    )
    assert tampered["lineage_state"] == "NONCOMPARABLE"
    assert tampered["conclusion"] == "NONCOMPARABLE"
    assert tampered["gaps"] == [{"code": "COMPARISON_SELECTION_MISMATCH"}]


def test_comparison_reports_complete_deterministic_movement_without_semantic_verdict(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=4, assigned=2, populations=2)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=5,
        assigned=3,
        populations=3,
        predecessor=before["report_id"],
    )
    before.update(
        {
            "episodes": [
                {"episode_id": "episode-keep", "conversation_id": "conversation-keep"},
                {
                    "episode_id": "episode-change",
                    "conversation_id": "conversation-change",
                },
                {"episode_id": "episode-lost", "conversation_id": "conversation-lost"},
                {
                    "episode_id": "episode-disputed",
                    "conversation_id": "conversation-disputed",
                },
            ],
            "population_dispositions": [
                {"episode_id": "episode-keep", "disposition": "ASSIGNED"},
                {"episode_id": "episode-change", "disposition": "ASSIGNED"},
                {
                    "episode_id": "episode-lost",
                    "disposition": "INTENTIONALLY_UNASSIGNED",
                },
                {"episode_id": "episode-disputed", "disposition": "AUDIT_DISPUTED"},
                {"episode_id": "episode-ambiguous", "disposition": "AMBIGUOUS"},
            ],
            "populations": [
                {
                    "population_id": "population-keep",
                    "episode_ids": ["episode-keep"],
                    "support": 1,
                },
                {
                    "population_id": "population-change",
                    "episode_ids": ["episode-change"],
                    "support": 1,
                },
                {
                    "population_id": "population-lost",
                    "episode_ids": ["episode-lost"],
                    "support": 1,
                },
            ],
            "behavior_patterns": [
                {
                    "pattern_id": "pattern-keep",
                    "occurrence_ids": ["occurrence-1"],
                    "support": 1,
                },
                {
                    "pattern_id": "pattern-change",
                    "occurrence_ids": ["occurrence-2"],
                    "support": 1,
                },
            ],
            "behavior_occurrences": [
                {"occurrence_id": "occurrence-1"},
                {"occurrence_id": "occurrence-2"},
            ],
            "evidence": [{"evidence_id": "evidence-1"}, {"evidence_id": "evidence-2"}],
            "excluded_episode_citations": [{}, {}, {}],
            "emerging_unknown": [
                {
                    "episode_id": "conversation:recover",
                    "conversation_id": "recover",
                    "reason": "NO_SURVIVING_EPISODE",
                },
                {
                    "episode_id": "conversation:still",
                    "conversation_id": "still",
                    "reason": "NO_SURVIVING_EPISODE",
                },
            ],
            "gaps": [
                {
                    "code": "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT",
                    "stage": "EPISODES",
                },
                {
                    "code": "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT",
                    "stage": "EPISODES",
                },
                *[
                    {
                        "code": "SEMANTIC_AUDIT_MISSING",
                        "stage": "AUDIT",
                        "item_id": f"missing-{index:02d}",
                    }
                    for index in range(47)
                ],
            ],
            "semantic_audit": {
                "items": [
                    {"item_id": "audit-1", "decision": "SUPPORTED"},
                    {"item_id": "audit-2", "decision": "SUPPORTED"},
                    {"item_id": "audit-3", "decision": "UNCERTAIN"},
                ]
            },
            "budget": {
                "total_reserved_usd": 10.0,
                "primary_actual_cost_usd": None,
                "audit_actual_cost_usd": None,
            },
        }
    )
    after.update(
        {
            "episodes": [
                {"episode_id": "episode-keep", "conversation_id": "conversation-keep"},
                {
                    "episode_id": "episode-change-v2",
                    "predecessor_episode_id": "episode-change",
                    "conversation_id": "conversation-change",
                },
                {
                    "episode_id": "episode-disputed",
                    "conversation_id": "conversation-disputed",
                },
                {"episode_id": "episode-new-1", "conversation_id": "recover"},
                {"episode_id": "episode-new-2", "conversation_id": "conversation-new"},
            ],
            "population_dispositions": [
                {"episode_id": "episode-keep", "disposition": "ASSIGNED"},
                {"episode_id": "episode-change-v2", "disposition": "ASSIGNED"},
                {"episode_id": "episode-new-1", "disposition": "ASSIGNED"},
                {"episode_id": "episode-new-2", "disposition": "AMBIGUOUS"},
                {"episode_id": "episode-disputed", "disposition": "AUDIT_DISPUTED"},
            ],
            "populations": [
                {
                    "population_id": "population-keep",
                    "episode_ids": ["episode-keep"],
                    "support": 1,
                },
                {
                    "population_id": "population-change-v2",
                    "predecessor_population_id": "population-change",
                    "episode_ids": ["episode-change-v2", "episode-new-1"],
                    "support": 2,
                },
                {
                    "population_id": "population-new",
                    "episode_ids": ["episode-new-2"],
                    "support": 1,
                },
            ],
            "behavior_patterns": [
                {
                    "pattern_id": "pattern-keep",
                    "occurrence_ids": ["occurrence-1"],
                    "support": 1,
                },
                {
                    "pattern_id": "pattern-change-v2",
                    "predecessor_pattern_id": "pattern-change",
                    "occurrence_ids": ["occurrence-2", "occurrence-3"],
                    "support": 2,
                },
            ],
            "behavior_occurrences": [
                {"occurrence_id": "occurrence-1"},
                {"occurrence_id": "occurrence-2"},
                {"occurrence_id": "occurrence-3"},
            ],
            "evidence": [
                {"evidence_id": "evidence-1"},
                {"evidence_id": "evidence-2"},
                {"evidence_id": "evidence-3"},
            ],
            "excluded_episode_citations": [{}, {}, {}, {}],
            "emerging_unknown": [
                {
                    "episode_id": "conversation:still",
                    "conversation_id": "still",
                    "reason": "NO_SURVIVING_EPISODE",
                },
            ],
            "gaps": [
                {
                    "code": "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT",
                    "stage": "EPISODES",
                },
                {
                    "code": "SEMANTIC_AUDIT_MISSING",
                    "stage": "AUDIT",
                    "item_id": "missing-00",
                },
            ],
            "semantic_audit": {
                "items": [
                    {"item_id": "audit-1", "decision": "SUPPORTED"},
                    {"item_id": "audit-2", "decision": "SUPPORTED"},
                    {"item_id": "audit-4", "decision": "SUPPORTED"},
                    {"item_id": "audit-5", "decision": "UNSUPPORTED"},
                ]
            },
            "budget": {
                "total_reserved_usd": 20.0,
                "primary_actual_cost_usd": 5.0,
                "audit_actual_cost_usd": 2.5,
            },
        }
    )
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))

    result = compare_behavior_maps(before_path, after_path, tmp_path / "comparison")

    assert result["deterministic_classification"] == "MIXED"
    assert result["semantic_conclusion"] == "HUMAN_LABELS_MISSING"
    assert result["coverage_movement"]["no_surviving_conversations"] == {
        "before": 2,
        "after": 1,
        "recovered_ids": ["recover"],
        "still_no_surviving_ids": ["still"],
        "new_ids": [],
    }
    assert result["coverage_movement"]["episode_dispositions"] == {
        "ASSIGNED": {"before": 2, "after": 3, "delta": 1},
        "INTENTIONALLY_UNASSIGNED": {"before": 1, "after": 0, "delta": -1},
        "AMBIGUOUS": {"before": 1, "after": 1, "delta": 0},
        "AUDIT_DISPUTED": {"before": 1, "after": 1, "delta": 0},
    }
    assert result["coverage_movement"]["grounding"] == {
        "excluded_citations": {"before": 3, "after": 4, "delta": 1},
        "rejected_grounding": {"before": 2, "after": 1, "delta": -1},
    }
    assert result["object_movement"] == {
        "episodes": {"before": 4, "after": 5, "delta": 1},
        "populations": {"before": 3, "after": 3, "delta": 0},
        "patterns": {"before": 2, "after": 2, "delta": 0},
        "occurrences": {"before": 2, "after": 3, "delta": 1},
        "evidence": {"before": 2, "after": 3, "delta": 1},
    }
    assert result["audit_movement"]["decisions"] == {
        "SUPPORTED": {"before": 2, "after": 3, "delta": 1},
        "UNCERTAIN": {"before": 1, "after": 0, "delta": -1},
        "UNSUPPORTED": {"before": 0, "after": 1, "delta": 1},
    }
    assert result["audit_movement"]["missing"] == {
        "before": 47,
        "after": 1,
        "delta": -46,
    }
    assert result["gap_movement"] == [
        {"code": "SEMANTIC_AUDIT_MISSING", "before": 47, "after": 1, "delta": -46},
        {
            "code": "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT",
            "before": 2,
            "after": 1,
            "delta": -1,
        },
    ]
    assert result["cost_movement"] == {
        "reservation_usd": {"before": 10.0, "after": 20.0, "delta": 10.0},
        "actual_cost_usd": {
            "before": None,
            "before_state": "UNKNOWN",
            "after": 7.5,
            "after_state": "KNOWN",
            "delta": None,
        },
    }
    assert result["identity_lineage"]["episodes"] == {
        "preserved_count": 2,
        "superseded_count": 1,
        "predecessor_mappings": [
            {"before_id": "episode-change", "after_id": "episode-change-v2"}
        ],
        "unmapped_before_count": 1,
        "new_unmapped_after_count": 2,
    }
    assert result["identity_lineage"]["populations"]["predecessor_mappings"] == [
        {"before_id": "population-change", "after_id": "population-change-v2"}
    ]
    assert result["identity_lineage"]["patterns"]["predecessor_mappings"] == [
        {"before_id": "pattern-change", "after_id": "pattern-change-v2"}
    ]
    assert result["baseline_claims"] == {
        "preserved_count": 3,
        "superseded_count": 3,
        "unexplained_loss_count": 2,
        "unexplained_loss_ids": ["episode-lost", "population-lost"],
    }
    assert result["id_level_movement"] == {
        "occurrences": {
            "preserved_ids": ["occurrence-1", "occurrence-2"],
            "new_ids": ["occurrence-3"],
            "lost_ids": [],
        },
        "evidence": {
            "preserved_ids": ["evidence-1", "evidence-2"],
            "new_ids": ["evidence-3"],
            "lost_ids": [],
        },
        "audit_items": {
            "preserved_ids": ["audit-1", "audit-2"],
            "new_ids": ["audit-4", "audit-5"],
            "lost_ids": ["audit-3"],
        },
        "audit_disputed_episode_ids": {
            "preserved_ids": ["episode-disputed"],
            "new_ids": [],
            "lost_ids": [],
        },
        "missing_audit_item_ids": {
            "preserved_ids": ["missing-00"],
            "new_ids": [],
            "lost_ids": [f"missing-{index:02d}" for index in range(1, 47)],
        },
    }
    assert all(
        row["state"] == "HUMAN_LABELS_MISSING" and row["value"] is None
        for row in result["semantic_benchmark"].values()
    )
    markdown = (tmp_path / "comparison" / "behavior-map-comparison.md").read_text()
    html = (tmp_path / "comparison" / "behavior-map-comparison.html").read_text()
    for section in (
        "Deterministic integrity and coverage",
        "Identity and predecessor lineage",
        "Gaps and audits",
        "Cost and reservation",
        "Semantic benchmark",
    ):
        assert section in markdown
        assert section in html


def test_comparison_conserves_baseline_population_membership_edges(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=4, assigned=4, populations=4)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=4,
        assigned=4,
        populations=3,
        predecessor=before["report_id"],
    )
    before["episodes"] = [
        {"episode_id": "episode-keep", "conversation_id": "conversation-keep"},
        {
            "episode_id": "episode-change",
            "conversation_id": "conversation-change",
        },
        {
            "episode_id": "episode-partial",
            "conversation_id": "conversation-partial",
        },
        {"episode_id": "episode-lost", "conversation_id": "conversation-lost"},
    ]
    before["populations"] = [
        {
            "population_id": "population-keep",
            "episode_ids": ["episode-keep"],
            "support": 1,
        },
        {
            "population_id": "population-change",
            "episode_ids": ["episode-change"],
            "support": 1,
        },
        {
            "population_id": "population-partial",
            "episode_ids": ["episode-partial"],
            "support": 1,
        },
        {
            "population_id": "population-lost",
            "episode_ids": ["episode-lost"],
            "support": 1,
        },
    ]
    after["episodes"] = [
        {"episode_id": "episode-keep", "conversation_id": "conversation-keep"},
        {
            "episode_id": "episode-change-v2",
            "predecessor_episode_id": "episode-change",
            "conversation_id": "conversation-change",
        },
        {"episode_id": "episode-extra", "conversation_id": "conversation-extra"},
        {
            "episode_id": "episode-unmapped",
            "conversation_id": "conversation-partial",
        },
    ]
    after["populations"] = [
        {
            "population_id": "population-keep",
            "episode_ids": ["episode-keep"],
            "support": 1,
        },
        {
            "population_id": "population-change-v2",
            "predecessor_population_id": "population-change",
            "episode_ids": ["episode-change-v2", "episode-extra"],
            "support": 2,
        },
        {
            "population_id": "population-partial-v2",
            "predecessor_population_id": "population-partial",
            "episode_ids": ["episode-unmapped"],
            "support": 1,
        },
    ]
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))

    first = compare_behavior_maps(before_path, after_path, tmp_path / "first")
    second = compare_behavior_maps(before_path, after_path, tmp_path / "second")

    edges = first["membership_edge_lineage"]
    assert edges == {
        "before_edge_count": 4,
        "after_edge_count": 4,
        "classified_before_edge_count": 4,
        "preserved_count": 1,
        "explicitly_superseded_count": 1,
        "unexplained_count": 2,
        "preserved_edges": [
            {
                "before_population_id": "population-keep",
                "before_episode_id": "episode-keep",
                "before_support": 1,
                "after_population_id": "population-keep",
                "after_episode_id": "episode-keep",
                "after_support": 1,
            }
        ],
        "explicitly_superseded_edges": [
            {
                "before_population_id": "population-change",
                "before_episode_id": "episode-change",
                "before_support": 1,
                "after_population_id": "population-change-v2",
                "after_episode_id": "episode-change-v2",
                "after_support": 2,
            }
        ],
        "unexplained_edges": [
            {
                "before_population_id": "population-lost",
                "before_episode_id": "episode-lost",
                "before_support": 1,
                "mapped_after_population_ids": [],
                "mapped_after_episode_ids": [],
            },
            {
                "before_population_id": "population-partial",
                "before_episode_id": "episode-partial",
                "before_support": 1,
                "mapped_after_population_ids": ["population-partial-v2"],
                "mapped_after_episode_ids": [],
            },
        ],
    }
    assert (
        edges["preserved_count"]
        + edges["explicitly_superseded_count"]
        + edges["unexplained_count"]
        == edges["before_edge_count"]
        == edges["classified_before_edge_count"]
    )
    assert first == second
    for filename in (
        "behavior-map-comparison.json",
        "behavior-map-comparison.md",
        "behavior-map-comparison.html",
    ):
        assert (tmp_path / "first" / filename).read_bytes() == (
            tmp_path / "second" / filename
        ).read_bytes()


def test_comparison_uses_no_change_not_semantic_pass_for_identical_integrity(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    before = _report("sha256:" + "1" * 64, episodes=2, assigned=1, populations=1)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=2,
        assigned=1,
        populations=1,
        predecessor=before["report_id"],
    )
    before_path = tmp_path / "before-stable.json"
    after_path = tmp_path / "after-stable.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))
    result = comparison_module.compare_behavior_maps(
        before_path, after_path, tmp_path / "stable-comparison"
    )
    assert result["deterministic_classification"] == "NO_CHANGE"
    assert result["semantic_conclusion"] == "HUMAN_LABELS_MISSING"


def test_zero_lineage_pattern_counts_are_noncomparable_not_regression(
    tmp_path: Path,
) -> None:
    comparison_module = importlib.import_module("triana_labs.behavior_map.comparison")
    compare_behavior_maps = comparison_module.compare_behavior_maps
    before = _report("sha256:" + "1" * 64, episodes=0, assigned=0, populations=0)
    after = _report(
        "sha256:" + "2" * 64,
        episodes=0,
        assigned=0,
        populations=0,
        predecessor=before["report_id"],
    )
    before["behavior_patterns"] = [
        {
            "pattern_id": f"before-pattern-{index:02d}",
            "label": f"Before candidate {index:02d}",
            "definition": "Content-free historical pattern.",
            "occurrence_ids": [f"before-occurrence-{index:02d}"],
            "support": 1,
            "audit_state": "SUPPORTED",
        }
        for index in range(61)
    ]
    after["behavior_patterns"] = [
        {
            "pattern_id": f"after-pattern-{index:02d}",
            "label": f"After candidate {index:02d}",
            "definition": "Content-free successor pattern.",
            "occurrence_ids": [f"after-occurrence-{index:02d}"],
            "support": 1,
            "audit_state": "SUPPORTED",
        }
        for index in range(24)
    ]
    before_path = tmp_path / "before.json"
    after_path = tmp_path / "after.json"
    before_path.write_bytes(_canonical(before, lf=True))
    after_path.write_bytes(_canonical(after, lf=True))

    first = compare_behavior_maps(before_path, after_path, tmp_path / "first")
    second = compare_behavior_maps(before_path, after_path, tmp_path / "second")

    assert first == second
    assert first["semantic_subject_movement"]["patterns"] == {
        "state": "NONCOMPARABLE_ZERO_SUBJECT_LINEAGE",
        "before_raw_count": 61,
        "after_raw_count": 24,
        "preserved_count": 0,
        "superseded_count": 0,
        "comparable_loss_count": None,
        "delta": None,
    }
    assert first["deterministic_classification"] == "NO_CHANGE"
    assert first["baseline_claims"]["unexplained_loss_count"] == 0
    assert first["semantic_conclusion"] == "HUMAN_LABELS_MISSING"
    assert all(
        row["state"] == "HUMAN_LABELS_MISSING" and row["value"] is None
        for row in first["semantic_benchmark"].values()
    )
    assert any(
        gap["code"] == "COMPARISON_PATTERN_SUBJECT_LINEAGE_MISSING"
        for gap in first["gaps"]
    )
    assert (
        "REGRESSED"
        not in (tmp_path / "first" / "behavior-map-comparison.md").read_text()
    )
    assert (
        "NONCOMPARABLE_ZERO_SUBJECT_LINEAGE"
        in (tmp_path / "first" / "behavior-map-comparison.md").read_text()
    )
    for filename in (
        "behavior-map-comparison.json",
        "behavior-map-comparison.md",
        "behavior-map-comparison.html",
    ):
        assert (tmp_path / "first" / filename).read_bytes() == (
            tmp_path / "second" / filename
        ).read_bytes()
