"""Black-box pattern and population-disposition conservation regressions."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from triana_labs.behavior_map import run_behavior_map


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


def _write_manifest(tmp_path: Path, count: int) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    traces = [
        {
            "contract_kind": "preview_trace",
            "schema_version": 1,
            "privacy_class": "SYNTHETIC",
            "trace_id": f"conversation-{index:02d}",
            "source_trace_id": f"source-{index:02d}",
            "events": [
                {
                    "sequence": 0,
                    "event_kind": "USER_MESSAGE",
                    "content": f"Cancel synthetic order {index:02d}.",
                },
                {
                    "sequence": 1,
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "I will verify that cancellation request.",
                    "is_final": True,
                },
            ],
        }
        for index in range(count)
    ]
    source = tmp_path / "traces.jsonl"
    source_bytes = b"".join(_canonical(row, newline=True) for row in traces)
    source.write_bytes(source_bytes)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": _sha256(source_bytes),
            "physical_record_count": count,
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "pattern-conservation"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": True,
                "model_id": "synthetic-pattern-author",
                "audit_model_id": "synthetic-pattern-auditor",
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {
                    "group_id": f"group-{row['trace_id']}",
                    "trace_ids": [row["trace_id"]],
                }
                for row in traces
            ],
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
    path = tmp_path / "manifest.json"
    path.write_bytes(_canonical(manifest, newline=True))
    return path


def _lineage(model_id: str) -> dict[str, Any]:
    return {
        "provider": "SYNTHETIC_TEST_BOUNDARY",
        "model_id": model_id,
        "provider_calls": 0,
        "attempted_call_count": 0,
        "successful_call_count": 0,
        "budget": {
            "max_calls": 0,
            "max_reserved_usd": 0.0,
            "reserved_usd": 0.0,
            "reservation_usd_per_call": 0.0,
        },
        "retry_policy": "NONE",
        "fallback_policy": "NONE",
    }


def _objects(value: Any, key: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if key in value:
            rows.append(value)
        for child in value.values():
            rows.extend(_objects(child, key))
    elif isinstance(value, list):
        for child in value:
            rows.extend(_objects(child, key))
    return rows


def _item_id(row: dict[str, Any]) -> str:
    for key in ("population_id", "pattern_id", "episode_id"):
        value = row.get(key)
        if isinstance(value, str):
            return value
    raise AssertionError("synthetic audit subject has no identity")


class _PatternAuthor:
    model_id = "synthetic-pattern-author"

    def __init__(
        self,
        *,
        omit_last: bool = False,
        add_foreign: bool = False,
        one_pattern_per_occurrence: bool = False,
        fail_hierarchy: bool = False,
    ) -> None:
        self.omit_last = omit_last
        self.add_foreign = add_foreign
        self.one_pattern_per_occurrence = one_pattern_per_occurrence
        self.fail_hierarchy = fail_hierarchy
        self.initial_pattern_inputs: dict[str, list[str]] = {}

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        del system
        fields = set(schema.model_fields)
        if "episodes" in fields and "behaviors" in fields:
            conversation_id = payload["conversations"][0]["conversation_id"]
            quote = next(
                row["content"]
                for row in payload["conversations"][0]["events"]
                if row["event_kind"] == "USER_MESSAGE"
            )
            return {
                "episodes": [
                    {
                        "local_id": "demand",
                        "goal": "Cancel a synthetic order",
                        "requested_action": "CANCEL_ORDER",
                        "subject": "synthetic order",
                        "constraints": [],
                        "fallbacks": [],
                        "supersedes_local_id": None,
                        "start_turn_ordinal": 0,
                        "end_turn_ordinal": 1,
                        "citations": [
                            {
                                "conversation_id": conversation_id,
                                "event_sequence": 0,
                                "quote": quote,
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
                ],
                "behaviors": [
                    {
                        "local_id": "behavior",
                        "lane": "SEMANTIC",
                        "action": "VERIFIED_CANCELLATION_SCOPE",
                        "object": "synthetic order",
                        "condition": "before cancellation",
                        "observed_effect": None,
                        "episode_local_ids": ["demand"],
                        "citations": [
                            {
                                "conversation_id": conversation_id,
                                "event_sequence": 1,
                                "quote": "I will verify that cancellation request.",
                            }
                        ],
                        "event_ids": [],
                        "status": "PROPOSED",
                    }
                ],
            }
        if "populations" in fields:
            candidates = payload.get("candidate_populations")
            if isinstance(candidates, list):
                return {
                    "populations": [
                        {
                            "label": row["label"],
                            "definition": row["definition"],
                            "episode_ids": list(row["episode_ids"]),
                        }
                        for row in candidates
                    ]
                }
            episode_ids = sorted(
                row["episode_id"] for row in _objects(payload, "episode_id")
            )
            return {
                "populations": [
                    {
                        "label": "Synthetic cancellations",
                        "definition": "Customers request synthetic cancellation.",
                        "episode_ids": episode_ids,
                    }
                ],
                "unassigned_episode_ids": [],
                "ambiguous_episode_ids": [],
            }
        if "matches" in fields:
            population_ids = [
                row["population_id"] for row in _objects(payload, "population_id")
            ]
            population_id = population_ids[0] if population_ids else None
            return {
                "matches": [
                    {
                        "episode_id": row["episode_id"],
                        "disposition": "MATCH" if population_id else "NO_MATCH",
                        "population_id": population_id,
                    }
                    for row in _objects(payload, "episode_id")
                ]
            }
        if "patterns" in fields:
            candidates = payload.get("candidate_patterns")
            if isinstance(candidates, list):
                if self.fail_hierarchy:
                    raise ValueError("SYNTHETIC_PATTERN_HIERARCHY_FAILED")
                return {
                    "patterns": [
                        {
                            "label": row["label"],
                            "definition": row["definition"],
                            "occurrence_ids": list(row["occurrence_ids"]),
                        }
                        for row in candidates
                    ]
                }
            occurrence_ids = sorted(
                row["occurrence_id"] for row in payload["behavior_occurrences"]
            )
            self.initial_pattern_inputs[stage] = occurrence_ids
            selected = occurrence_ids[:-1] if self.omit_last else occurrence_ids
            if self.one_pattern_per_occurrence:
                patterns = [
                    {
                        "label": f"Verifies cancellation scope {occurrence_id}",
                        "definition": "The agent verifies one synthetic request.",
                        "occurrence_ids": [occurrence_id],
                    }
                    for occurrence_id in selected
                ]
            else:
                members = list(selected)
                if self.add_foreign:
                    members.append("occurrence-not-supplied")
                patterns = [
                    {
                        "label": "Verifies cancellation scope before acting",
                        "definition": "The agent verifies cancellation scope before acting.",
                        "occurrence_ids": members,
                    }
                ]
            return {"patterns": patterns}
        raise AssertionError(f"unexpected stage {stage}: {sorted(fields)}")

    def lineage(self) -> dict[str, Any]:
        return _lineage(self.model_id)


class _AuditModel:
    model_id = "synthetic-pattern-auditor"

    def __init__(self, max_successes: int | None = None) -> None:
        self.max_successes = max_successes
        self.successful_ids: list[str] = []
        self.attempted_subject_kinds: list[str] = []

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        del stage, system
        assert "audits" in schema.model_fields
        item = payload["items"][0]
        item_id = _item_id(item)
        self.attempted_subject_kinds.append(
            "PATTERN"
            if "pattern_id" in item
            else "POPULATION"
            if "population_id" in item
            else "EPISODE"
        )
        if (
            self.max_successes is not None
            and len(self.successful_ids) >= self.max_successes
        ):
            raise ValueError("SYNTHETIC_AUDIT_BUDGET_EXCEEDED")
        self.successful_ids.append(item_id)
        return {
            "audits": [
                {
                    "item_id": item_id,
                    "decision": "SUPPORTED",
                    "reason": "Synthetic audit support.",
                }
            ]
        }

    def lineage(self) -> dict[str, Any]:
        lineage = _lineage(self.model_id)
        attempts = len(self.successful_ids)
        lineage.update(
            {
                "provider_calls": attempts,
                "attempted_call_count": attempts,
                "successful_call_count": attempts,
                "budget": {
                    "max_calls": self.max_successes,
                    "max_reserved_usd": float(self.max_successes or attempts),
                    "reserved_usd": float(attempts),
                    "reservation_usd_per_call": 1.0,
                },
            }
        )
        return lineage


class _RejectPatternAuditModel(_AuditModel):
    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        del stage, system
        assert "audits" in schema.model_fields
        item = payload["items"][0]
        item_id = _item_id(item)
        self.attempted_subject_kinds.append(
            "PATTERN"
            if "pattern_id" in item
            else "POPULATION"
            if "population_id" in item
            else "EPISODE"
        )
        self.successful_ids.append(item_id)
        return {
            "audits": [
                {
                    "item_id": item_id,
                    "decision": (
                        "UNSUPPORTED" if "pattern_id" in item else "SUPPORTED"
                    ),
                    "reason": "Synthetic subject-scoped audit.",
                }
            ]
        }


class _UncertainPatternAuditModel(_RejectPatternAuditModel):
    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        result = super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )
        if "pattern_id" in payload["items"][0]:
            result["audits"][0]["decision"] = "UNCERTAIN"
        return result


class _DuplicatePatternMembershipAuthor(_PatternAuthor):
    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        if "patterns" in schema.model_fields and isinstance(
            payload.get("behavior_occurrences"), list
        ):
            occurrence_id = payload["behavior_occurrences"][0]["occurrence_id"]
            self.initial_pattern_inputs[stage] = [occurrence_id]
            return {
                "patterns": [
                    {
                        "label": "Verifies cancellation scope",
                        "definition": "First candidate for the same occurrence.",
                        "occurrence_ids": [occurrence_id],
                    },
                    {
                        "label": "Checks cancellation details",
                        "definition": "Second candidate for the same occurrence.",
                        "occurrence_ids": [occurrence_id],
                    },
                ]
            }
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


class _HierarchyReintroducesOmittedOccurrenceAuthor(_PatternAuthor):
    def __init__(self) -> None:
        super().__init__(one_pattern_per_occurrence=True)
        self.omitted_occurrence_id: str | None = None
        self.reintroduction_stage: str | None = None
        self.reintroduction_input_ids: set[str] = set()

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        if "patterns" in schema.model_fields and isinstance(
            payload.get("behavior_occurrences"), list
        ):
            occurrence_ids = sorted(
                row["occurrence_id"] for row in payload["behavior_occurrences"]
            )
            self.initial_pattern_inputs[stage] = occurrence_ids
            selected = occurrence_ids
            if self.omitted_occurrence_id is None:
                self.omitted_occurrence_id = occurrence_ids[-1]
                selected = occurrence_ids[:-1]
            return {
                "patterns": [
                    {
                        "label": f"Verifies cancellation scope {occurrence_id}",
                        "definition": "The agent verifies one synthetic request.",
                        "occurrence_ids": [occurrence_id],
                    }
                    for occurrence_id in selected
                ]
            }
        if "patterns" in schema.model_fields and isinstance(
            payload.get("candidate_patterns"), list
        ):
            candidates = payload["candidate_patterns"]
            supplied_ids = {
                occurrence_id
                for row in candidates
                for occurrence_id in row["occurrence_ids"]
            }
            patterns = [
                {
                    "label": row["label"],
                    "definition": row["definition"],
                    "occurrence_ids": list(row["occurrence_ids"]),
                }
                for row in candidates
            ]
            if self.reintroduction_stage is None:
                assert self.omitted_occurrence_id is not None
                assert self.omitted_occurrence_id not in supplied_ids
                patterns[0]["occurrence_ids"].append(self.omitted_occurrence_id)
                self.reintroduction_stage = stage
                self.reintroduction_input_ids = supplied_ids
            return {"patterns": patterns}
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


def _run(
    tmp_path: Path,
    *,
    count: int,
    author: _PatternAuthor,
    auditor: _AuditModel,
    output_name: str = "output",
) -> dict[str, Any]:
    return run_behavior_map(
        _write_manifest(tmp_path, count),
        tmp_path / output_name,
        primary_model=author,
        audit_model=auditor,
        agent_context="Synthetic order-support agent.",
    )


def test_pattern_batch_reconciles_omitted_and_foreign_occurrences(
    tmp_path: Path,
) -> None:
    author = _PatternAuthor(omit_last=True, add_foreign=True)
    report = _run(tmp_path, count=25, author=author, auditor=_AuditModel())
    supplied_ids = {
        occurrence_id
        for occurrence_ids in author.initial_pattern_inputs.values()
        for occurrence_id in occurrence_ids
    }
    assert len(author.initial_pattern_inputs) > 1
    dispositions = {
        row["occurrence_id"]: row for row in report["pattern_occurrence_dispositions"]
    }

    assert set(dispositions) == supplied_ids
    assert len(dispositions) == len(report["eligible_behavior_occurrences"])
    assert sum(
        row["disposition"] == "INTENTIONALLY_UNASSIGNED"
        and row["reason"] == "MODEL_OMITTED_OCCURRENCE"
        for row in dispositions.values()
    ) == len(author.initial_pattern_inputs)
    assert any(
        gap["code"] == "UNSUPPLIED_PATTERN_OCCURRENCE_ID"
        and gap["occurrence_ids"] == ["occurrence-not-supplied"]
        for gap in report["gaps"]
    )
    assert "occurrence-not-supplied" not in {
        occurrence_id
        for row in report["behavior_patterns"]
        for occurrence_id in row["occurrence_ids"]
    }
    omitted_episode_ids = {
        episode_id
        for occurrence_id, disposition in dispositions.items()
        if disposition["reason"] == "MODEL_OMITTED_OCCURRENCE"
        for episode_id in next(
            row["episode_ids"]
            for row in report["behavior_occurrences"]
            if row["occurrence_id"] == occurrence_id
        )
    }
    assert omitted_episode_ids
    assert omitted_episode_ids <= {
        row["episode_id"]
        for row in report["emerging_unknown"]
        if row["reason"] == "UNASSIGNED_BEHAVIOR"
    }
    assert report["pattern_accounting"]["eligible_occurrence_count"] == len(
        supplied_ids
    )
    assert report["pattern_accounting"]["terminal_disposition_count"] == len(
        supplied_ids
    )
    assert report["pattern_accounting"]["foreign_occurrence_id_count"] == 1


def test_hierarchy_cannot_reintroduce_occurrence_omitted_by_exact_candidate_input(
    tmp_path: Path,
) -> None:
    author = _HierarchyReintroducesOmittedOccurrenceAuthor()
    report = _run(tmp_path, count=13, author=author, auditor=_AuditModel())
    omitted_occurrence_id = author.omitted_occurrence_id

    assert omitted_occurrence_id is not None
    assert author.reintroduction_stage is not None
    assert omitted_occurrence_id not in author.reintroduction_input_ids
    assert any(
        gap["code"] == "UNSUPPLIED_PATTERN_OCCURRENCE_ID"
        and omitted_occurrence_id in gap["occurrence_ids"]
        and (
            "HIERARCH" in str(gap.get("stage", "")).upper()
            or gap.get("source_stage") == author.reintroduction_stage
        )
        for gap in report["gaps"]
    )
    assert omitted_occurrence_id not in {
        occurrence_id
        for pattern in report["behavior_patterns"]
        for occurrence_id in pattern["occurrence_ids"]
    }
    disposition = next(
        row
        for row in report["pattern_occurrence_dispositions"]
        if row["occurrence_id"] == omitted_occurrence_id
    )
    assert disposition == {
        "occurrence_id": omitted_occurrence_id,
        "disposition": "INTENTIONALLY_UNASSIGNED",
        "reason": "MODEL_OMITTED_OCCURRENCE",
    }
    assert report["pattern_accounting"]["published_pattern_support"] == sum(
        row["support"]
        for row in report["behavior_patterns"]
        if row["audit_state"] == "SUPPORTED"
    )
    assert report["pattern_accounting"]["foreign_occurrence_id_count"] == 1


def test_audit_missing_pattern_candidates_survive_resume_with_stable_identity(
    tmp_path: Path,
) -> None:
    manifest = _write_manifest(tmp_path, 4)
    seed_output = tmp_path / "seed"
    seed_auditor = _AuditModel(max_successes=1)
    seed = run_behavior_map(
        manifest,
        seed_output,
        primary_model=_PatternAuthor(one_pattern_per_occurrence=True),
        audit_model=seed_auditor,
        agent_context="Synthetic order-support agent.",
    )
    missing_candidates = {
        row["pattern_id"]: row
        for row in seed["behavior_patterns"]
        if row["audit_state"] == "MISSING"
    }
    assert missing_candidates
    assert all(
        row["visibility"] == "UNPUBLISHED_AUDIT_MISSING"
        for row in missing_candidates.values()
    )
    assert seed["pattern_accounting"] == {
        "eligible_occurrence_count": 4,
        "terminal_disposition_count": 4,
        "candidate_pattern_count": 4,
        "audited_pattern_count": 0,
        "supported_pattern_count": 0,
        "disputed_pattern_count": 0,
        "audit_missing_pattern_count": 4,
        "active_pattern_membership_count": 0,
        "unpublished_candidate_pattern_membership_count": 4,
        "published_pattern_support": 0,
    }
    dispositions = {
        row["occurrence_id"]: row for row in seed["pattern_occurrence_dispositions"]
    }
    assert all(
        row["disposition"] == "INTENTIONALLY_UNASSIGNED"
        and row["reason"] == "REAUDIT_REQUIRED"
        and row["candidate_pattern_id"] in missing_candidates
        for row in dispositions.values()
    )
    # S2 is mechanically observable but not silently repaired: the bounded first
    # audit is population-first, while candidate custody preserves what remains.
    assert seed_auditor.attempted_subject_kinds[:1] == ["POPULATION"]

    continuation_output = tmp_path / "continuation"
    shutil.copytree(seed_output, continuation_output)
    resumed = run_behavior_map(
        manifest,
        continuation_output,
        primary_model=_PatternAuthor(one_pattern_per_occurrence=True),
        audit_model=_AuditModel(),
        agent_context="Synthetic order-support agent.",
    )
    resumed_by_id = {row["pattern_id"]: row for row in resumed["behavior_patterns"]}
    assert set(missing_candidates) <= set(resumed_by_id)
    assert all(
        resumed_by_id[pattern_id]["occurrence_ids"]
        == missing_candidates[pattern_id]["occurrence_ids"]
        for pattern_id in missing_candidates
    )
    assert (seed_output / "behavior-map.json").read_bytes() != (
        continuation_output / "behavior-map.json"
    ).read_bytes()


def test_population_conservation_rejects_historical_221_220_split() -> None:
    module = __import__("triana_labs.behavior_map", fromlist=["dummy"])
    validate = module.validate_behavior_map_conservation
    error_type = module.BehaviorMapConservationError
    episode_ids = [f"episode-{index:03d}" for index in range(221)]
    report = {
        "populations": [
            {
                "population_id": "population-supported",
                "audit_state": "SUPPORTED",
                "visibility": "PROPOSED_POPULATION",
                "episode_ids": episode_ids,
                "support": 221,
            }
        ],
        "population_dispositions": [
            *[
                {
                    "episode_id": episode_id,
                    "disposition": "ASSIGNED",
                    "population_id": "population-supported",
                    "reason": "POPULATION_MEMBERSHIP",
                }
                for episode_id in episode_ids[:220]
            ],
            {
                "episode_id": episode_ids[-1],
                "disposition": "AUDIT_DISPUTED",
                "reason": "AUDIT_DISAGREEMENT",
            },
        ],
    }

    with pytest.raises(error_type) as exc_info:
        validate(report)

    assert exc_info.value.code == "POPULATION_MEMBERSHIP_DISPOSITION_MISMATCH"
    assert exc_info.value.details == {
        "active_population_member_count": 221,
        "assigned_disposition_count": 220,
        "active_not_assigned_episode_ids": ["episode-220"],
        "assigned_not_active_episode_ids": [],
        "disputed_active_episode_ids": ["episode-220"],
    }


def test_disputed_episode_exclusion_satisfies_population_conservation() -> None:
    module = __import__("triana_labs.behavior_map", fromlist=["dummy"])
    validate = module.validate_behavior_map_conservation
    episode_ids = ["episode-assigned-a", "episode-assigned-b"]
    report = {
        "populations": [
            {
                "population_id": "population-supported",
                "audit_state": "SUPPORTED",
                "visibility": "PROPOSED_POPULATION",
                "episode_ids": episode_ids,
                "support": 2,
            }
        ],
        "population_dispositions": [
            *[
                {
                    "episode_id": episode_id,
                    "disposition": "ASSIGNED",
                    "population_id": "population-supported",
                    "reason": "POPULATION_MEMBERSHIP",
                }
                for episode_id in episode_ids
            ],
            {
                "episode_id": "episode-disputed",
                "disposition": "AUDIT_DISPUTED",
                "reason": "AUDIT_DISAGREEMENT",
            },
        ],
    }

    assert validate(report) == {
        "active_population_member_count": 2,
        "assigned_disposition_count": 2,
        "disputed_episode_count": 1,
        "state": "CONSERVED",
    }


def test_non_supported_pattern_remains_disputed_and_unpublished(
    tmp_path: Path,
) -> None:
    report = _run(
        tmp_path,
        count=3,
        author=_PatternAuthor(),
        auditor=_RejectPatternAuditModel(),
    )
    disputed = [
        row
        for row in report["behavior_patterns"]
        if row["audit_state"] == "UNSUPPORTED"
    ]
    assert disputed
    assert all(row["visibility"] == "UNPUBLISHED_AUDIT_DISPUTED" for row in disputed)
    disputed_ids = {row["pattern_id"] for row in disputed}
    assert report["pattern_accounting"]["disputed_pattern_count"] == len(disputed)
    assert report["pattern_accounting"]["supported_pattern_count"] == 0
    assert report["pattern_accounting"]["published_pattern_support"] == 0
    dispositions = report["pattern_occurrence_dispositions"]
    assert dispositions
    assert all(
        row["disposition"] == "AUDIT_DISPUTED"
        and row["reason"] == "AUDIT_DISAGREEMENT"
        and row["candidate_pattern_id"] in disputed_ids
        for row in dispositions
    )


def test_uncertain_pattern_audit_is_completed_disputed_not_missing(
    tmp_path: Path,
) -> None:
    report = _run(
        tmp_path,
        count=3,
        author=_PatternAuthor(),
        auditor=_UncertainPatternAuditModel(),
    )
    uncertain = [
        row for row in report["behavior_patterns"] if row["audit_state"] == "UNCERTAIN"
    ]
    assert uncertain
    assert all(row["visibility"] == "UNPUBLISHED_AUDIT_DISPUTED" for row in uncertain)
    uncertain_ids = {row["pattern_id"] for row in uncertain}
    accounting = report["pattern_accounting"]
    assert accounting["audited_pattern_count"] == len(uncertain)
    assert accounting["disputed_pattern_count"] == len(uncertain)
    assert accounting["audit_missing_pattern_count"] == 0
    assert accounting["supported_pattern_count"] == 0
    assert accounting["active_pattern_membership_count"] == 0
    assert all(
        row["disposition"] == "AUDIT_DISPUTED"
        and row["reason"] == "AUDIT_DISAGREEMENT"
        and row["candidate_pattern_id"] in uncertain_ids
        for row in report["pattern_occurrence_dispositions"]
    )


def test_duplicate_pattern_candidate_membership_refuses_before_publication(
    tmp_path: Path,
) -> None:
    module = __import__("triana_labs.behavior_map", fromlist=["dummy"])
    error_type = module.BehaviorMapConservationError
    output = tmp_path / "duplicate-pattern-output"

    with pytest.raises(error_type) as exc_info:
        run_behavior_map(
            _write_manifest(tmp_path, 1),
            output,
            primary_model=_DuplicatePatternMembershipAuthor(),
            audit_model=_AuditModel(max_successes=1),
            agent_context="Synthetic order-support agent.",
        )

    assert exc_info.value.code == "PATTERN_OCCURRENCE_MEMBERSHIP_DUPLICATE"
    assert not (output / "behavior-map.json").exists()


@pytest.mark.parametrize(
    ("populations", "expected_code"),
    [
        (
            [
                {
                    "population_id": "population-a",
                    "audit_state": "SUPPORTED",
                    "episode_ids": ["episode-a"],
                    "support": 1,
                },
                {
                    "population_id": "population-b",
                    "audit_state": "SUPPORTED",
                    "episode_ids": ["episode-a"],
                    "support": 1,
                },
            ],
            "POPULATION_DUPLICATE_ACTIVE_MEMBERSHIP",
        ),
        (
            [
                {
                    "population_id": "population-a",
                    "audit_state": "SUPPORTED",
                    "episode_ids": ["episode-a", "episode-b"],
                    "support": 3,
                }
            ],
            "POPULATION_SUPPORT_MISMATCH",
        ),
    ],
)
def test_population_conservation_refuses_duplicate_membership_or_support_mismatch(
    populations: list[dict[str, Any]], expected_code: str
) -> None:
    module = __import__("triana_labs.behavior_map", fromlist=["dummy"])
    validate = module.validate_behavior_map_conservation
    error_type = module.BehaviorMapConservationError
    episode_ids = sorted(
        {
            episode_id
            for population in populations
            for episode_id in population["episode_ids"]
        }
    )
    report = {
        "populations": populations,
        "population_dispositions": [
            {
                "episode_id": episode_id,
                "disposition": "ASSIGNED",
                "population_id": "population-a",
                "reason": "POPULATION_MEMBERSHIP",
            }
            for episode_id in episode_ids
        ],
    }

    with pytest.raises(error_type) as exc_info:
        validate(report)

    assert exc_info.value.code == expected_code


@pytest.mark.parametrize(
    ("dispositions", "expected_code", "expected_details"),
    [
        (
            [
                {
                    "episode_id": "episode-a",
                    "disposition": "ASSIGNED",
                    "population_id": "population-a",
                    "reason": "POPULATION_MEMBERSHIP",
                },
                {
                    "episode_id": "episode-a",
                    "disposition": "ASSIGNED",
                    "population_id": "population-a",
                    "reason": "POPULATION_MEMBERSHIP",
                },
            ],
            "POPULATION_DISPOSITION_DUPLICATE",
            {
                "episode_ids": ["episode-a"],
                "row_counts_by_episode": {"episode-a": 2},
            },
        ),
        (
            [
                {
                    "episode_id": "episode-a",
                    "disposition": "ASSIGNED",
                    "population_id": "population-b",
                    "reason": "POPULATION_MEMBERSHIP",
                }
            ],
            "POPULATION_ASSIGNMENT_EDGE_MISMATCH",
            {
                "mismatches": [
                    {
                        "episode_id": "episode-a",
                        "expected_population_id": "population-a",
                        "assigned_population_id": "population-b",
                    }
                ]
            },
        ),
    ],
)
def test_population_conservation_refuses_duplicate_or_wrong_assignment_edges(
    dispositions: list[dict[str, Any]],
    expected_code: str,
    expected_details: dict[str, Any],
) -> None:
    module = __import__("triana_labs.behavior_map", fromlist=["dummy"])
    validate = module.validate_behavior_map_conservation
    error_type = module.BehaviorMapConservationError
    report = {
        "populations": [
            {
                "population_id": "population-a",
                "audit_state": "SUPPORTED",
                "episode_ids": ["episode-a"],
                "support": 1,
            }
        ],
        "population_dispositions": dispositions,
    }

    with pytest.raises(error_type) as exc_info:
        validate(report)

    assert exc_info.value.code == expected_code
    assert exc_info.value.details == expected_details
