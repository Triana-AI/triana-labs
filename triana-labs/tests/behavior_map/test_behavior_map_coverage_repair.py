"""Black-box regressions for Behavior Map coverage conservation.

The fixtures are synthetic.  They deliberately model malformed semantic output;
no provider transport, private checkpoint, or customer trace is involved.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from triana_labs.behavior_map import run_behavior_map
from triana_labs.behavior_map.contracts import ExtractionBatch


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


def _trace(trace_id: str, user: str, assistant: str) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": trace_id,
        "source_trace_id": f"source-{trace_id}",
        "events": [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": user},
            {
                "sequence": 1,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": assistant,
                "is_final": True,
            },
        ],
    }


def _multi_subject_trace() -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": "case",
        "source_trace_id": "source-case",
        "events": [
            {
                "sequence": 0,
                "event_kind": "USER_MESSAGE",
                "content": "Cancel order alpha.",
            },
            {
                "sequence": 1,
                "event_kind": "USER_MESSAGE",
                "content": "Also return order beta.",
            },
            {
                "sequence": 2,
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "I can help with both requests.",
                "is_final": True,
            },
        ],
    }


def _write_manifest(
    tmp_path: Path, traces: list[dict[str, Any]], *, egress: bool = True
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    source = tmp_path / "traces.jsonl"
    source_payload = b"".join(_canonical(row, lf=True) for row in traces)
    source.write_bytes(source_payload)
    manifest = {
        "artifact_kind": "evidence_bundle_manifest_v0",
        "schema_version": 0,
        "source": {
            "adapter_id": "preview-trace-jsonl",
            "adapter_version": "1",
            "path": str(source),
            "sha256": _sha256(source_payload),
            "physical_record_count": len(traces),
        },
        "agent": {"workspace_id": "synthetic", "agent_id": "coverage-repair"},
        "privacy": {
            "authorization": "SYNTHETIC_FIXTURE",
            "execution_location": "LOCAL_PRIVATE",
            "provider_egress": {
                "authorized": egress,
                "model_id": "synthetic-author" if egress else None,
                "audit_model_id": "synthetic-auditor" if egress else None,
            },
        },
        "grouping": {
            "highest_dependency_key": "conversation",
            "assignments": [
                {"group_id": f"group-{row['trace_id']}", "trace_ids": [row["trace_id"]]}
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
    path.write_bytes(_canonical(manifest, lf=True))
    return path


def _citation(conversation_id: str, sequence: int, quote: str) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "event_sequence": sequence,
        "quote": quote,
    }


def _report_citation(conversation_id: str, sequence: int, quote: str) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "turn_ordinal": sequence,
        "quote": quote,
    }


def _grounding(
    *,
    goal: list[int] | None = None,
    requested_action: list[int] | None = None,
    subject: list[int] | None = None,
    constraints: list[list[int]] | None = None,
    fallbacks: list[list[int]] | None = None,
) -> dict[str, Any]:
    """The frozen provider contract binds semantic fields to citation indexes."""

    return {
        "goal": [0] if goal is None else goal,
        "requested_action": [0] if requested_action is None else requested_action,
        "subject": [0] if subject is None else subject,
        "constraints": [] if constraints is None else constraints,
        "fallbacks": [] if fallbacks is None else fallbacks,
    }


class _Author:
    model_id = "synthetic-author"

    def __init__(self, episodes: dict[str, list[dict[str, Any]]]) -> None:
        self.episodes = episodes
        self.requests: list[dict[str, Any]] = []

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.requests.append(
            {"stage": stage, "payload": deepcopy(payload), "system": system}
        )
        fields = set(schema.model_fields)
        if "episodes" in fields and "behaviors" in fields:
            conversation_id = payload["conversations"][0]["conversation_id"]
            rows = deepcopy(self.episodes.get(conversation_id, []))
            episode_schema = (
                schema.model_json_schema().get("$defs", {}).get("EpisodeProposal", {})
            )
            if "field_grounding" not in episode_schema.get("properties", {}):
                for row in rows:
                    row.pop("field_grounding", None)
            return {"episodes": rows, "behaviors": []}
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
            episodes = _objects(payload, "episode_id")
            populations = []
            cancellation_ids = [
                row["episode_id"]
                for row in episodes
                if row.get("requested_action") == "CANCEL_ORDER"
            ]
            if cancellation_ids:
                populations.append(
                    {
                        "label": "Order cancellation requests",
                        "definition": "Customers ask to cancel an order.",
                        "episode_ids": cancellation_ids,
                    }
                )
            result: dict[str, Any] = {"populations": populations}
            if "unassigned_episode_ids" in fields:
                result["unassigned_episode_ids"] = []
            if "ambiguous_episode_ids" in fields:
                result["ambiguous_episode_ids"] = []
            return result
        if "matches" in fields:
            episode_ids = [row["episode_id"] for row in _objects(payload, "episode_id")]
            populations = _objects(payload, "population_id")
            population_id = populations[0]["population_id"] if populations else None
            return {
                "matches": [
                    {
                        "episode_id": episode_id,
                        "disposition": "MATCH" if population_id else "NO_MATCH",
                        "population_id": population_id,
                    }
                    for episode_id in episode_ids
                ]
            }
        if "audits" in fields:
            return {
                "audits": [
                    {
                        "item_id": _first_id(row),
                        "decision": "SUPPORTED",
                        "reason": "Synthetic audit.",
                    }
                    for row in payload.get("items", [])
                ]
            }
        raise AssertionError(
            f"unexpected stage {stage} with schema fields {sorted(fields)}"
        )

    def lineage(self) -> dict[str, Any]:
        return _lineage(self.model_id)


class _Auditor(_Author):
    model_id = "synthetic-auditor"

    def __init__(self, unsupported_conversations: set[str] | None = None) -> None:
        super().__init__({})
        self.unsupported_conversations = unsupported_conversations or set()

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.requests.append(
            {"stage": stage, "payload": deepcopy(payload), "system": system}
        )
        assert "audits" in schema.model_fields
        audits = []
        for row in payload.get("items", []):
            unsupported = row.get("conversation_id") in self.unsupported_conversations
            audits.append(
                {
                    "item_id": _first_id(row),
                    "decision": "UNSUPPORTED" if unsupported else "SUPPORTED",
                    "reason": "Synthetic scoped audit.",
                }
            )
        return {"audits": audits}


class _OmittingBatchAuthor(_Author):
    """Omit one valid cancellation from each initial batch, then group leftovers."""

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        fields = set(schema.model_fields)
        self.requests.append(
            {"stage": stage, "payload": deepcopy(payload), "system": system}
        )
        if "episodes" in fields and "behaviors" in fields:
            conversation_id = payload["conversations"][0]["conversation_id"]
            rows = deepcopy(self.episodes[conversation_id])
            episode_schema = (
                schema.model_json_schema().get("$defs", {}).get("EpisodeProposal", {})
            )
            if "field_grounding" not in episode_schema.get("properties", {}):
                for row in rows:
                    row.pop("field_grounding", None)
            return {"episodes": rows, "behaviors": []}
        if "audits" in fields:
            return {
                "audits": [
                    {
                        "item_id": _first_id(row),
                        "decision": "SUPPORTED",
                        "reason": "Synthetic audit.",
                    }
                    for row in payload.get("items", [])
                ]
            }
        if "matches" in fields:
            # Preserve the no-match decision so the later leftover regrouping—not a
            # forced match—has to recover semantically similar cross-batch demands.
            return {
                "matches": [
                    {
                        "episode_id": row["episode_id"],
                        "disposition": "NO_MATCH",
                        "population_id": None,
                    }
                    for row in _objects(payload, "episode_id")
                ]
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
            rows = _objects(payload, "episode_id")
            cancellations = [
                row for row in rows if row.get("requested_action") == "CANCEL_ORDER"
            ]
            leftovers = "leftover" in stage.casefold() or "regroup" in stage.casefold()
            selected = cancellations if leftovers else cancellations[:-1]
            result: dict[str, Any] = {
                "populations": (
                    [
                        {
                            "label": "Order cancellation requests",
                            "definition": "Customers ask to cancel an order.",
                            "episode_ids": [row["episode_id"] for row in selected],
                        }
                    ]
                    if selected
                    else []
                )
            }
            if "unassigned_episode_ids" in fields:
                result["unassigned_episode_ids"] = []
            if "ambiguous_episode_ids" in fields:
                result["ambiguous_episode_ids"] = []
            return result
        raise AssertionError(
            f"unexpected stage {stage} with schema fields {sorted(fields)}"
        )


class _UnsuppliedIdAuthor(_Author):
    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        result = super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )
        if "populations" in schema.model_fields and result["populations"]:
            result["populations"][0]["episode_ids"].append("sha256:" + "f" * 64)
        return result


class _FailingPopulationBatchAuthor(_Author):
    """Fail one initial population batch while recording exact call boundaries."""

    failed_stage = "user-populations-0001"

    def __init__(self, episodes: dict[str, list[dict[str, Any]]]) -> None:
        super().__init__(episodes)
        self.initial_population_episode_ids: dict[str, list[str]] = {}

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        if (
            "populations" in schema.model_fields
            and isinstance(payload.get("episodes"), list)
            and stage.startswith("user-populations-")
            and "leftover" not in stage
        ):
            self.initial_population_episode_ids[stage] = sorted(
                row["episode_id"] for row in payload["episodes"]
            )
        if stage == self.failed_stage:
            self.requests.append(
                {"stage": stage, "payload": deepcopy(payload), "system": system}
            )
            raise ValueError("SEMANTIC_PROVIDER_CALL_FAILED")
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


class _FailingPatternBatchAuthor(_Author):
    """Produce grounded behaviors, then fail one first-level pattern batch."""

    failed_stage = "agent-behavior-patterns-0001"

    def __init__(self, episodes: dict[str, list[dict[str, Any]]]) -> None:
        super().__init__(episodes)
        self.initial_pattern_occurrence_ids: dict[str, list[str]] = {}

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        fields = set(schema.model_fields)
        if "episodes" in fields and "behaviors" in fields:
            result = super().complete_json(
                stage=stage, system=system, payload=payload, schema=schema
            )
            conversation_id = payload["conversations"][0]["conversation_id"]
            result["behaviors"] = [
                {
                    "local_id": "confirmed-cancellation",
                    "lane": "SEMANTIC",
                    "action": "CONFIRMED_REQUEST_SCOPE",
                    "object": "order cancellation",
                    "condition": "before changing the order",
                    "observed_effect": None,
                    "episode_local_ids": ["demand"],
                    "citations": [
                        _citation(
                            conversation_id,
                            1,
                            "I can help with that cancellation.",
                        )
                    ],
                    "event_ids": [],
                    "status": "PROPOSED",
                }
            ]
            return result
        if "patterns" in fields:
            candidates = payload.get("candidate_patterns")
            if isinstance(candidates, list):
                self.requests.append(
                    {"stage": stage, "payload": deepcopy(payload), "system": system}
                )
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
            self.initial_pattern_occurrence_ids[stage] = occurrence_ids
            self.requests.append(
                {"stage": stage, "payload": deepcopy(payload), "system": system}
            )
            if stage == self.failed_stage:
                raise ValueError("SEMANTIC_PROVIDER_CALL_FAILED")
            return {
                "patterns": [
                    {
                        "label": "Confirms requested scope before changing an order",
                        "definition": "The agent confirms the requested cancellation scope before acting.",
                        "occurrence_ids": occurrence_ids,
                    }
                ]
            }
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


class _FailingPatternHierarchyAuthor(_FailingPatternBatchAuthor):
    """Let all first-level pattern batches succeed, then fail consolidation."""

    failed_stage = "agent-behavior-patterns-hierarchical-0000-0000"

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        if stage == self.failed_stage:
            self.requests.append(
                {"stage": stage, "payload": deepcopy(payload), "system": system}
            )
            raise ValueError("SEMANTIC_PROVIDER_CALL_FAILED")
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


class _AuditPlanningAuthor(_FailingPatternBatchAuthor):
    """Emit several populations and patterns so audit ordering is observable."""

    failed_stage = "never"

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        fields = set(schema.model_fields)
        if (
            "populations" in fields
            and isinstance(payload.get("episodes"), list)
            and "leftover" not in stage
        ):
            self.requests.append(
                {"stage": stage, "payload": deepcopy(payload), "system": system}
            )
            return {
                "populations": [
                    {
                        "label": f"Demand family {row['episode_id']}",
                        "definition": "A synthetic independently auditable demand family.",
                        "episode_ids": [row["episode_id"]],
                    }
                    for row in payload["episodes"]
                ],
                "unassigned_episode_ids": [],
                "ambiguous_episode_ids": [],
            }
        if "patterns" in fields and isinstance(
            payload.get("behavior_occurrences"), list
        ):
            occurrence_ids = sorted(
                row["occurrence_id"] for row in payload["behavior_occurrences"]
            )
            self.initial_pattern_occurrence_ids[stage] = occurrence_ids
            self.requests.append(
                {"stage": stage, "payload": deepcopy(payload), "system": system}
            )
            return {
                "patterns": [
                    {
                        "label": f"Scoped agent behavior {occurrence_id}",
                        "definition": "A synthetic independently auditable behavior family.",
                        "occurrence_ids": [occurrence_id],
                    }
                    for occurrence_id in occurrence_ids
                ]
            }
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )


class _CappedAuditModel(_Auditor):
    """Expose a strict successful-call cap and detect a cap-plus-one invocation."""

    def __init__(self, max_calls: int) -> None:
        super().__init__()
        self.max_calls = max_calls
        self.provider_calls = 0
        self.boundary_invocations = 0
        self.successful_item_ids: list[str] = []
        self.blocked_item_ids: list[str] = []

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.boundary_invocations += 1
        item_id = _first_id(payload["items"][0])
        if self.provider_calls >= self.max_calls:
            self.blocked_item_ids.append(item_id)
            raise ValueError("SEMANTIC_BUDGET_EXCEEDED")
        self.provider_calls += 1
        self.successful_item_ids.append(item_id)
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )

    def lineage(self) -> dict[str, Any]:
        return {
            **_lineage(self.model_id),
            "provider_calls": self.provider_calls,
            "attempted_call_count": self.provider_calls,
            "successful_call_count": self.provider_calls,
            "budget": {
                "max_calls": self.max_calls,
                "max_reserved_usd": float(self.max_calls),
                "reserved_usd": float(self.provider_calls),
                "reservation_usd_per_call": 1.0,
                "reservation_method": "CONFIGURED_RUN_MAXIMUM",
            },
        }


class _ObservedOverCapAuditModel(_Auditor):
    """Reproduce historical checkpoints beyond a stale declared lane cap."""

    max_calls = 89
    reservation_usd_per_call = 0.18

    def __init__(self) -> None:
        super().__init__()
        self.provider_calls = 0

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.provider_calls += 1
        return super().complete_json(
            stage=stage, system=system, payload=payload, schema=schema
        )

    def lineage(self) -> dict[str, Any]:
        return {
            **_lineage(self.model_id),
            "provider_calls": self.provider_calls,
            "attempted_call_count": self.provider_calls,
            "successful_call_count": self.provider_calls,
            "actual_cost_state": "UNKNOWN",
            "budget": {
                "max_calls": self.max_calls,
                "max_reserved_usd": 16.02,
                "reserved_usd": round(
                    self.provider_calls * self.reservation_usd_per_call, 2
                ),
                "reservation_usd_per_call": self.reservation_usd_per_call,
                "reservation_method": "CONFIGURED_RUN_MAXIMUM",
            },
        }


class _ScopedAuditPatternAuthor(_FailingPatternBatchAuthor):
    """Produce one supported population and one independently auditable pattern."""

    failed_stage = "never"


class _SubjectScopedAuditor(_Auditor):
    def __init__(
        self,
        unsupported_scope: str,
        *,
        unsupported_episode_conversation: str | None = None,
    ) -> None:
        super().__init__()
        self.unsupported_scope = unsupported_scope
        self.unsupported_episode_conversation = unsupported_episode_conversation

    def complete_json(
        self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
    ) -> dict[str, Any]:
        self.requests.append(
            {"stage": stage, "payload": deepcopy(payload), "system": system}
        )
        audits = []
        for row in payload["items"]:
            if "population_id" in row:
                scope = "POPULATION"
            elif "pattern_id" in row:
                scope = "PATTERN"
            else:
                scope = "EPISODE"
            unsupported = scope == self.unsupported_scope
            if scope == "EPISODE" and self.unsupported_episode_conversation is not None:
                unsupported = (
                    unsupported
                    and row.get("conversation_id")
                    == self.unsupported_episode_conversation
                )
            audits.append(
                {
                    "item_id": _first_id(row),
                    "decision": "UNSUPPORTED" if unsupported else "SUPPORTED",
                    "reason": f"Synthetic {scope.casefold()}-scoped audit.",
                }
            )
        return {"audits": audits}


def _lineage(model_id: str) -> dict[str, Any]:
    return {
        "provider": "SYNTHETIC_TEST_BOUNDARY",
        "model_id": model_id,
        "provider_calls": 0,
        "budget": {
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


def _first_id(row: dict[str, Any]) -> str:
    for key in ("population_id", "pattern_id", "episode_id"):
        if key in row:
            return str(row[key])
    raise AssertionError("audit item has no subject identity")


def _episode(
    conversation_id: str,
    user_quote: str,
    *,
    citations: list[dict[str, Any]],
    constraints: list[str] | None = None,
    grounding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "local_id": "demand",
        "goal": "Locate an order",
        "requested_action": "FIND_ORDER",
        "subject": "order",
        "constraints": constraints or [],
        "fallbacks": [],
        "supersedes_local_id": None,
        "start_turn_ordinal": 0,
        "end_turn_ordinal": 1,
        "citations": citations,
        "field_grounding": grounding or _grounding(),
        "status": "PROPOSED",
    }


def _sibling_beta_episode() -> dict[str, Any]:
    row = _episode(
        "case",
        "Also return order beta.",
        citations=[_citation("case", 1, "Also return order beta.")],
    )
    row.update(
        {
            "local_id": "beta-demand",
            "goal": "Return order beta",
            "requested_action": "RETURN_ORDER",
            "subject": "order beta",
        }
    )
    return row


def _run_one(
    tmp_path: Path,
    proposal: dict[str, Any],
    *,
    user: str = "Where is my order?",
    assistant: str = "Your order is delayed.",
) -> dict[str, Any]:
    manifest = _write_manifest(tmp_path, [_trace("case", user, assistant)])
    return run_behavior_map(
        manifest,
        tmp_path / "output",
        primary_model=_Author({"case": [proposal]}),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )


def test_mixed_role_citation_is_detached_without_destroying_grounded_demand(
    tmp_path: Path,
) -> None:
    proposal = _episode(
        "case",
        "Where is my order?",
        citations=[
            _citation("case", 0, "Where is my order?"),
            _citation("case", 1, "Your order is delayed."),
        ],
    )
    report = _run_one(tmp_path, proposal)

    assert len(report["episodes"]) == 1
    episode = report["episodes"][0]
    assert [row["quote"] for row in episode["citations"]] == ["Where is my order?"]
    assert episode["field_grounding"] == _grounding()
    assert episode["grounding_authority"] == "AUTHOR_PROPOSED_FIELD_GROUNDING"
    assert episode["independent_grounding_state"] == "NOT_AUDITED"
    assert episode.get("human_accepted") is not True
    assert episode["excluded_citations"] == [
        {
            "citation": _report_citation("case", 1, "Your order is delayed."),
            "citation_index": 1,
            "reason": "EVENT_ROLE_NOT_PERMITTED",
        }
    ]
    assert report["excluded_episode_citations"] == [
        {
            "conversation_id": "case",
            "local_id": "demand",
            "citation_index": 1,
            "citation": _report_citation("case", 1, "Your order is delayed."),
            "reason": "EVENT_ROLE_NOT_PERMITTED",
            "support_status": "EXCLUDED",
        }
    ]
    assert any(
        gap["code"] == "SEMANTIC_EPISODE_CITATION_EXCLUDED"
        and gap["reason"] == "EVENT_ROLE_NOT_PERMITTED"
        for gap in report["gaps"]
    )


@pytest.mark.parametrize(
    ("user", "assistant", "citations", "expected_reason"),
    [
        (
            "Hello.",
            "Where is your order?",
            [_citation("case", 1, "Where is your order?")],
            "EVENT_ROLE_NOT_PERMITTED",
        ),
        (
            "Hello.",
            "Checked it.",
            [_citation("case", 2, "tool payload")],
            "EVENT_NOT_FOUND",
        ),
        (
            "Where is my order?",
            "Checking.",
            [_citation("wrong", 0, "Where is my order?")],
            "CONVERSATION_ID_MISMATCH",
        ),
        (
            "Where is my order?",
            "Checking.",
            [_citation("case", 0, "Where is order")],
            "EXACT_QUOTE_INVALID",
        ),
    ],
)
def test_no_permitted_exact_customer_grounding_rejects_episode_precisely(
    tmp_path: Path,
    user: str,
    assistant: str,
    citations: list[dict[str, Any]],
    expected_reason: str,
) -> None:
    report = _run_one(
        tmp_path,
        _episode("case", user, citations=citations),
        user=user,
        assistant=assistant,
    )
    assert report["episodes"] == []
    assert any(
        gap["code"] == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
        and expected_reason in gap["excluded_reasons"]
        for gap in report["gaps"]
    )
    assert any(
        row["conversation_id"] == "case" and row["reason"] == "NO_SURVIVING_EPISODE"
        for row in report["emerging_unknown"]
    )
    assert report["excluded_episode_citations"] == [
        {
            "conversation_id": "case",
            "local_id": "demand",
            "citation_index": 0,
            "citation": _report_citation(
                citations[0]["conversation_id"],
                citations[0]["event_sequence"],
                citations[0]["quote"],
            ),
            "reason": expected_reason,
            "support_status": "EXCLUDED",
        }
    ]


def test_valid_customer_quote_cannot_salvage_assistant_grounded_mandatory_field(
    tmp_path: Path,
) -> None:
    proposal = _episode(
        "case",
        "Where is my order?",
        citations=[
            _citation("case", 0, "Where is my order?"),
            _citation("case", 1, "Your order is delayed."),
        ],
        grounding=_grounding(subject=[1]),
    )
    report = _run_one(tmp_path, proposal)

    assert report["episodes"] == []
    assert any(
        gap["code"] == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
        and gap["unsupported_mandatory_fields"] == ["subject"]
        for gap in report["gaps"]
    )
    assert report["excluded_episode_citations"] == [
        {
            "conversation_id": "case",
            "local_id": "demand",
            "citation_index": 1,
            "citation": _report_citation("case", 1, "Your order is delayed."),
            "reason": "EVENT_ROLE_NOT_PERMITTED",
            "support_status": "EXCLUDED",
        }
    ]


def test_unsupported_optional_constraint_is_removed_with_visible_uncertainty(
    tmp_path: Path,
) -> None:
    proposal = _episode(
        "case",
        "Where is my order?",
        citations=[
            _citation("case", 0, "Where is my order?"),
            _citation("case", 1, "Your order is delayed."),
        ],
        constraints=["delivery is delayed"],
        grounding=_grounding(constraints=[[1]]),
    )
    report = _run_one(tmp_path, proposal)
    episode = report["episodes"][0]
    assert episode["constraints"] == []
    assert episode["field_grounding"]["constraints"] == []
    assert episode["field_uncertainties"] == [
        {
            "field": "constraints",
            "value": "delivery is delayed",
            "reason": "NO_PERMITTED_CUSTOMER_GROUNDING",
        }
    ]


def test_relevance_detachment_rejects_episode_when_mandatory_grounding_is_lost(
    tmp_path: Path,
) -> None:
    alpha = _episode(
        "case",
        "Cancel order alpha.",
        citations=[
            _citation("case", 0, "Cancel order alpha."),
            _citation("case", 1, "Also return order beta."),
        ],
        grounding=_grounding(goal=[1], requested_action=[1], subject=[1]),
    )
    alpha.update(
        {
            "local_id": "alpha-demand",
            "goal": "Cancel order alpha",
            "requested_action": "CANCEL_ORDER",
            "subject": "order alpha",
        }
    )
    report = run_behavior_map(
        _write_manifest(tmp_path, [_multi_subject_trace()]),
        tmp_path / "output",
        primary_model=_Author({"case": [alpha, _sibling_beta_episode()]}),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    assert {row["subject"] for row in report["episodes"]} == {"order beta"}
    assert any(
        gap["code"] == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
        and gap["conversation_id"] == "case"
        and gap["local_id"] == "alpha-demand"
        and gap["unsupported_mandatory_fields"]
        == ["goal", "requested_action", "subject"]
        for gap in report["gaps"]
    )


def test_relevance_detachment_reprojects_indices_and_strips_optional_field(
    tmp_path: Path,
) -> None:
    alpha = _episode(
        "case",
        "Cancel order alpha.",
        citations=[
            _citation("case", 0, "Cancel order alpha."),
            _citation("case", 1, "Also return order beta."),
        ],
        constraints=["coordinate with order beta"],
        grounding=_grounding(constraints=[[1]]),
    )
    alpha.update(
        {
            "local_id": "alpha-demand",
            "goal": "Cancel order alpha",
            "requested_action": "CANCEL_ORDER",
            "subject": "order alpha",
        }
    )
    report = run_behavior_map(
        _write_manifest(tmp_path, [_multi_subject_trace()]),
        tmp_path / "output",
        primary_model=_Author({"case": [alpha, _sibling_beta_episode()]}),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    retained = next(
        row for row in report["episodes"] if row["subject"] == "order alpha"
    )
    assert [row["quote"] for row in retained["citations"]] == ["Cancel order alpha."]
    assert retained["field_grounding"] == _grounding()
    assert retained["constraints"] == []
    assert retained["field_uncertainties"] == [
        {
            "field": "constraints",
            "value": "coordinate with order beta",
            "reason": "NO_PERMITTED_CUSTOMER_GROUNDING",
        }
    ]
    for episode in report["episodes"]:
        citation_count = len(episode["citations"])
        grounding = episode["field_grounding"]
        mandatory_indices = [
            index
            for field in ("goal", "requested_action", "subject")
            for index in grounding[field]
        ]
        optional_indices = [
            index
            for field in ("constraints", "fallbacks")
            for binding in grounding[field]
            for index in binding
        ]
        assert all(
            0 <= index < citation_count
            for index in [*mandatory_indices, *optional_indices]
        )


def test_greeting_does_not_become_demand_from_informative_assistant_response(
    tmp_path: Path,
) -> None:
    proposal = _episode(
        "case",
        "Hello.",
        citations=[_citation("case", 1, "Your package arrives Friday.")],
    )
    report = _run_one(
        tmp_path, proposal, user="Hello.", assistant="Your package arrives Friday."
    )
    assert report["episodes"] == []
    assert report["accounting"]["surviving_episode_count"] == 0


def test_tool_result_only_citation_does_not_create_customer_demand(
    tmp_path: Path,
) -> None:
    trace = {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": "case",
        "source_trace_id": "source-case",
        "events": [
            {"sequence": 0, "event_kind": "USER_MESSAGE", "content": "Hello."},
            {
                "sequence": 1,
                "event_kind": "TOOL_CALL",
                "call_id": "lookup-1",
                "tool_name": "lookup_order",
                "arguments": {"order_id": "synthetic"},
            },
            {
                "sequence": 2,
                "event_kind": "TOOL_RESULT",
                "call_id": "lookup-1",
                "result_state": "SUCCEEDED",
                "result": {"status": "delayed"},
            },
        ],
    }
    proposal = _episode(
        "case",
        "Hello.",
        citations=[_citation("case", 2, "delayed")],
    )
    report = run_behavior_map(
        _write_manifest(tmp_path, [trace]),
        tmp_path / "output",
        primary_model=_Author({"case": [proposal]}),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    assert report["episodes"] == []
    assert any(
        gap["code"] == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
        and "EVENT_ROLE_NOT_PERMITTED" in gap["excluded_reasons"]
        for gap in report["gaps"]
    )


def test_fresh_extraction_requires_versioned_explicit_field_grounding(
    tmp_path: Path,
) -> None:
    schema = ExtractionBatch.model_json_schema()["$defs"]["EpisodeProposal"]
    assert "field_grounding" in schema["required"]
    assert "grounding_contract_version" in schema["required"]
    proposal = _episode(
        "case",
        "Where is my order?",
        citations=[_citation("case", 0, "Where is my order?")],
    )
    proposal.pop("field_grounding")
    proposal["grounding_contract_version"] = 1
    with pytest.raises(ValidationError):
        ExtractionBatch.model_validate({"episodes": [proposal], "behaviors": []})
    report = _run_one(tmp_path, proposal)
    assert report["episodes"] == []
    assert any(
        gap["code"] in {"SEMANTIC_SCHEMA_INVALID", "SEMANTIC_EXTRACTION_FAILED"}
        for gap in report["gaps"]
    )


def _cancellation_corpus(
    count: int, order: list[int] | None = None
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    order = list(range(count)) if order is None else order
    traces = []
    proposals: dict[str, list[dict[str, Any]]] = {}
    for index in order:
        trace_id = f"cancel-{index:02d}"
        quote = f"Please cancel purchase {index:02d}."
        traces.append(_trace(trace_id, quote, "I can help with that cancellation."))
        row = _episode(trace_id, quote, citations=[_citation(trace_id, 0, quote)])
        row.update(
            {
                "goal": "Cancel a purchase",
                "requested_action": "CANCEL_ORDER",
                "subject": f"purchase {index:02d}",
            }
        )
        proposals[trace_id] = [row]
    return traces, proposals


def test_cross_batch_omissions_are_carried_and_every_episode_gets_one_disposition(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    primary = _OmittingBatchAuthor(proposals)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=primary,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    eligible = {
        row["episode_id"] for row in report["episodes"] if row["status"] == "PROPOSED"
    }
    dispositions = report["population_dispositions"]
    assert {row["episode_id"] for row in dispositions} == eligible
    assert len(dispositions) == len(eligible)
    assert len({row["episode_id"] for row in dispositions}) == len(dispositions)
    assert all(row["disposition"] == "ASSIGNED" for row in dispositions)
    assigned = {
        episode_id
        for population in report["populations"]
        for episode_id in population["episode_ids"]
    }
    assert assigned == eligible
    assert any(
        gap["code"] == "POPULATION_BATCH_OUTPUT_OMITTED" for gap in report["gaps"]
    )
    assert sum(row["support"] for row in report["populations"]) == len(eligible)
    match_requests = [
        row for row in primary.requests if "leftover-match" in row["stage"]
    ]
    assert match_requests
    for candidate in _objects(match_requests, "population_id"):
        evidence = candidate.get("representative_customer_evidence")
        assert isinstance(evidence, list) and evidence
        assert all(row["event_kind"] == "USER_MESSAGE" for row in evidence)


def test_unsupplied_population_member_is_rejected_with_typed_gap(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(3)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_UnsuppliedIdAuthor(proposals),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    invented = "sha256:" + "f" * 64
    assert all(
        invented not in population["episode_ids"]
        for population in report["populations"]
    )
    assert any(
        gap["code"] == "POPULATION_UNSUPPLIED_EPISODE_ID"
        and gap["episode_id"] == invented
        and gap["stage"].startswith("POPULATIONS_BATCH_")
        for gap in report["gaps"]
    )


def test_population_projection_is_repeatable_and_batch_permutation_conserves_dispositions(
    tmp_path: Path,
) -> None:
    traces_a, proposals_a = _cancellation_corpus(25)
    permutation = list(reversed(range(25)))
    traces_b, proposals_b = _cancellation_corpus(25, permutation)
    report_a = run_behavior_map(
        _write_manifest(tmp_path / "a", traces_a),
        tmp_path / "a" / "output",
        primary_model=_OmittingBatchAuthor(proposals_a),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    report_b = run_behavior_map(
        _write_manifest(tmp_path / "b", traces_b),
        tmp_path / "b" / "output",
        primary_model=_OmittingBatchAuthor(proposals_b),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    dispositions_a = {
        (row["episode_id"], row["disposition"])
        for row in report_a["population_dispositions"]
    }
    dispositions_b = {
        (row["episode_id"], row["disposition"])
        for row in report_b["population_dispositions"]
    }
    assert dispositions_a == dispositions_b
    assert _canonical(report_a["population_dispositions"]) == _canonical(
        report_b["population_dispositions"]
    )
    assert _canonical(report_a["populations"]) == _canonical(report_b["populations"])


def test_cross_origin_leftovers_survive_two_real_batch_boundary_arrangements(
    tmp_path: Path,
) -> None:
    traces, compact = _cancellation_corpus(25)
    expanded = deepcopy(compact)
    target_conversations = {"cancel-00", "cancel-12", "cancel-24"}
    for index in range(25):
        conversation_id = f"cancel-{index:02d}"
        if conversation_id in target_conversations:
            continue
        compact[conversation_id][0]["requested_action"] = f"UNIQUE_{index:02d}"
        expanded[conversation_id][0]["requested_action"] = f"UNIQUE_{index:02d}"
        expanded[conversation_id][0]["goal"] = "Synthetic filler " + ("x" * 8_000)

    models = (_OmittingBatchAuthor(compact), _OmittingBatchAuthor(expanded))
    reports = []
    for label, model in zip(("compact", "expanded"), models, strict=True):
        reports.append(
            run_behavior_map(
                _write_manifest(tmp_path / label, traces),
                tmp_path / label / "output",
                primary_model=model,
                audit_model=_Auditor(),
                agent_context="Synthetic order-support agent.",
            )
        )

    def initial_partitions(model: _OmittingBatchAuthor) -> list[list[str]]:
        return [
            [row["conversation_id"] for row in request["payload"]["episodes"]]
            for request in model.requests
            if request["stage"].startswith("user-populations-")
            and "hierarchical" not in request["stage"]
            and "leftover" not in request["stage"]
        ]

    assert initial_partitions(models[0]) != initial_partitions(models[1])
    for report in reports:
        target_episode_ids = {
            row["episode_id"]
            for row in report["episodes"]
            if row["conversation_id"] in target_conversations
        }
        final_dispositions = {
            row["episode_id"]: row["disposition"]
            for row in report["population_dispositions"]
        }
        assert target_episode_ids
        assert all(
            final_dispositions[episode_id] == "ASSIGNED"
            for episode_id in target_episode_ids
        )
        assert any(
            gap["code"] == "POPULATION_BATCH_OUTPUT_OMITTED" for gap in report["gaps"]
        )


def test_failed_population_batch_is_scoped_and_later_batches_continue(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    primary = _FailingPopulationBatchAuthor(proposals)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=primary,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    initial_stages = sorted(primary.initial_population_episode_ids)
    assert primary.failed_stage in initial_stages
    assert any(stage > primary.failed_stage for stage in initial_stages)
    failed_episode_ids = set(
        primary.initial_population_episode_ids[primary.failed_stage]
    )
    before_episode_ids = set(primary.initial_population_episode_ids[initial_stages[0]])
    later_episode_ids = {
        episode_id
        for stage, episode_ids in primary.initial_population_episode_ids.items()
        if stage > primary.failed_stage
        for episode_id in episode_ids
    }
    assert failed_episode_ids and before_episode_ids and later_episode_ids

    assert {
        (
            gap["code"],
            gap["stage"],
            gap["failure_code"],
            tuple(gap["episode_ids"]),
            gap["episode_count"],
        )
        for gap in report["gaps"]
        if gap["code"] == "SEMANTIC_POPULATION_BATCH_FAILED"
    } == {
        (
            "SEMANTIC_POPULATION_BATCH_FAILED",
            "POPULATIONS_BATCH_0001",
            "SEMANTIC_ATTEMPT_FAILED",
            tuple(sorted(failed_episode_ids)),
            len(failed_episode_ids),
        )
    }

    dispositions = {row["episode_id"]: row for row in report["population_dispositions"]}
    assert all(
        dispositions[episode_id]
        == {
            "episode_id": episode_id,
            "disposition": "INTENTIONALLY_UNASSIGNED",
            "reason": "POPULATION_BATCH_FAILED",
        }
        for episode_id in failed_episode_ids
    )
    assert all(
        any(
            row["episode_id"] == episode_id
            and row["reason"] == "POPULATION_BATCH_FAILED"
            for row in report["emerging_unknown"]
        )
        for episode_id in failed_episode_ids
    )

    assigned_episode_ids = {
        episode_id
        for population in report["populations"]
        for episode_id in population["episode_ids"]
    }
    assert before_episode_ids <= assigned_episode_ids
    assert later_episode_ids <= assigned_episode_ids
    assert failed_episode_ids.isdisjoint(assigned_episode_ids)
    assert all(
        population["support"] == len(set(population["episode_ids"]))
        for population in report["populations"]
    )


def test_failed_population_batch_checkpoint_is_not_retried_and_replay_is_stable(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    manifest = _write_manifest(tmp_path, traces)
    output = tmp_path / "output"
    first_model = _FailingPopulationBatchAuthor(proposals)
    first = run_behavior_map(
        manifest,
        output,
        primary_model=first_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    report_before = (output / "behavior-map.json").read_bytes()
    failed_attempts = []
    for path in sorted((output / "behavior-map-checkpoints").glob("*.json")):
        value = json.loads(path.read_text())
        if (
            value.get("artifact_kind") == "behavior_map_attempt_v0"
            and value.get("state") == "FAILED"
            and value.get("identity", {}).get("stage") == first_model.failed_stage
        ):
            failed_attempts.append((path, path.read_bytes()))
    assert len(failed_attempts) == 1

    replay_model = _FailingPopulationBatchAuthor(proposals)
    second = run_behavior_map(
        manifest,
        output,
        primary_model=replay_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    assert first == second
    assert (output / "behavior-map.json").read_bytes() == report_before
    assert all(path.read_bytes() == payload for path, payload in failed_attempts)
    assert first_model.failed_stage not in {
        request["stage"] for request in replay_model.requests
    }
    assert (
        sum(
            1
            for path in (output / "behavior-map-checkpoints").glob("*.json")
            if json.loads(path.read_text()).get("identity", {}).get("stage")
            == first_model.failed_stage
        )
        == 1
    )


def test_failed_pattern_batch_is_scoped_and_later_batches_continue(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    primary = _FailingPatternBatchAuthor(proposals)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=primary,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    initial_stages = sorted(primary.initial_pattern_occurrence_ids)
    assert primary.failed_stage in initial_stages
    assert any(stage > primary.failed_stage for stage in initial_stages)
    failed_occurrence_ids = set(
        primary.initial_pattern_occurrence_ids[primary.failed_stage]
    )
    before_occurrence_ids = set(
        primary.initial_pattern_occurrence_ids[initial_stages[0]]
    )
    later_occurrence_ids = {
        occurrence_id
        for stage, occurrence_ids in primary.initial_pattern_occurrence_ids.items()
        if stage > primary.failed_stage
        for occurrence_id in occurrence_ids
    }
    assert failed_occurrence_ids and before_occurrence_ids and later_occurrence_ids

    assert {
        (
            gap["code"],
            gap["stage"],
            gap["failure_code"],
            tuple(gap["occurrence_ids"]),
            gap["occurrence_count"],
        )
        for gap in report["gaps"]
        if gap["code"] == "SEMANTIC_PATTERN_BATCH_FAILED"
    } == {
        (
            "SEMANTIC_PATTERN_BATCH_FAILED",
            "PATTERNS_BATCH_0001",
            "SEMANTIC_ATTEMPT_FAILED",
            tuple(sorted(failed_occurrence_ids)),
            len(failed_occurrence_ids),
        )
    }

    published_occurrence_ids = {
        occurrence_id
        for pattern in report["behavior_patterns"]
        for occurrence_id in pattern["occurrence_ids"]
    }
    assert before_occurrence_ids <= published_occurrence_ids
    assert later_occurrence_ids <= published_occurrence_ids
    assert failed_occurrence_ids.isdisjoint(published_occurrence_ids)
    occurrence_by_id = {
        row["occurrence_id"]: row for row in report["behavior_occurrences"]
    }
    failed_episode_ids = {
        episode_id
        for occurrence_id in failed_occurrence_ids
        for episode_id in occurrence_by_id[occurrence_id]["episode_ids"]
    }
    assert failed_episode_ids
    assert all(
        any(
            row["episode_id"] == episode_id and row["reason"] == "PATTERN_BATCH_FAILED"
            for row in report["emerging_unknown"]
        )
        for episode_id in failed_episode_ids
    )
    assert report["behavior_patterns"]
    assert all(
        pattern["audit_state"] == "SUPPORTED" for pattern in report["behavior_patterns"]
    )


def test_failed_pattern_batch_checkpoint_is_not_retried_and_replay_is_stable(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    manifest = _write_manifest(tmp_path, traces)
    output = tmp_path / "output"
    first_model = _FailingPatternBatchAuthor(proposals)
    first = run_behavior_map(
        manifest,
        output,
        primary_model=first_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    report_before = (output / "behavior-map.json").read_bytes()
    failed_attempts = []
    for path in sorted((output / "behavior-map-checkpoints").glob("*.json")):
        value = json.loads(path.read_text())
        if (
            value.get("artifact_kind") == "behavior_map_attempt_v0"
            and value.get("state") == "FAILED"
            and value.get("identity", {}).get("stage") == first_model.failed_stage
        ):
            failed_attempts.append((path, path.read_bytes()))
    assert len(failed_attempts) == 1

    replay_model = _FailingPatternBatchAuthor(proposals)
    second = run_behavior_map(
        manifest,
        output,
        primary_model=replay_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    assert first == second
    assert (output / "behavior-map.json").read_bytes() == report_before
    assert all(path.read_bytes() == payload for path, payload in failed_attempts)
    assert first_model.failed_stage not in {
        request["stage"] for request in replay_model.requests
    }
    assert (
        sum(
            1
            for path in (output / "behavior-map-checkpoints").glob("*.json")
            if json.loads(path.read_text()).get("identity", {}).get("stage")
            == first_model.failed_stage
        )
        == 1
    )


def test_failed_pattern_hierarchy_preserves_candidates_and_replays_stably(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(25)
    manifest = _write_manifest(tmp_path, traces)
    output = tmp_path / "output"
    first_model = _FailingPatternHierarchyAuthor(proposals)
    first = run_behavior_map(
        manifest,
        output,
        primary_model=first_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    first_level_occurrence_ids = {
        occurrence_id
        for occurrence_ids in first_model.initial_pattern_occurrence_ids.values()
        for occurrence_id in occurrence_ids
    }
    assert len(first_model.initial_pattern_occurrence_ids) > 1
    assert first_level_occurrence_ids
    assert first_model.failed_stage in {
        request["stage"] for request in first_model.requests
    }

    assert {
        (
            gap["code"],
            gap["stage"],
            gap["failure_code"],
            tuple(gap["occurrence_ids"]),
            gap["occurrence_count"],
        )
        for gap in first["gaps"]
        if gap["code"] == "SEMANTIC_PATTERN_HIERARCHY_FAILED"
    } == {
        (
            "SEMANTIC_PATTERN_HIERARCHY_FAILED",
            "PATTERNS_HIERARCHY",
            "SEMANTIC_ATTEMPT_FAILED",
            tuple(sorted(first_level_occurrence_ids)),
            len(first_level_occurrence_ids),
        )
    }
    published_occurrence_ids = {
        occurrence_id
        for pattern in first["behavior_patterns"]
        for occurrence_id in pattern["occurrence_ids"]
    }
    assert first_level_occurrence_ids <= published_occurrence_ids
    assert first["behavior_patterns"]
    assert all(
        pattern["audit_state"] == "SUPPORTED" for pattern in first["behavior_patterns"]
    )

    report_before = (output / "behavior-map.json").read_bytes()
    failed_attempts = []
    for path in sorted((output / "behavior-map-checkpoints").glob("*.json")):
        value = json.loads(path.read_text())
        if (
            value.get("artifact_kind") == "behavior_map_attempt_v0"
            and value.get("state") == "FAILED"
            and value.get("identity", {}).get("stage") == first_model.failed_stage
        ):
            failed_attempts.append((path, path.read_bytes()))
    assert len(failed_attempts) == 1

    replay_model = _FailingPatternHierarchyAuthor(proposals)
    second = run_behavior_map(
        manifest,
        output,
        primary_model=replay_model,
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    assert first == second
    assert (output / "behavior-map.json").read_bytes() == report_before
    assert all(path.read_bytes() == payload for path, payload in failed_attempts)
    assert first_model.failed_stage not in {
        request["stage"] for request in replay_model.requests
    }


def test_checkpoint_aware_audit_continuation_prioritizes_starved_subject_class(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(12)
    manifest = _write_manifest(tmp_path, traces)
    seed_output = tmp_path / "seed-output"
    seed_auditor = _CappedAuditModel(max_calls=2)
    seed = run_behavior_map(
        manifest,
        seed_output,
        primary_model=_AuditPlanningAuthor(proposals),
        audit_model=seed_auditor,
        agent_context="Synthetic order-support agent.",
    )
    population_ids = {row["population_id"] for row in seed["populations"]}
    assert seed_auditor.successful_item_ids
    assert set(seed_auditor.successful_item_ids) <= population_ids
    assert len(seed_auditor.blocked_item_ids) == 1
    historical_prefix_ids = {
        *seed_auditor.successful_item_ids,
        *seed_auditor.blocked_item_ids,
    }

    audit_prefix = {}
    for path in sorted((seed_output / "behavior-map-checkpoints").glob("*.json")):
        value = json.loads(path.read_text())
        stage = value.get("identity", {}).get("stage", "")
        if stage.startswith("independent-semantic-audit-"):
            audit_prefix[path.name] = path.read_bytes()
    assert len(audit_prefix) == 3

    continuation_reports = []
    continuation_bytes = []
    for label in ("a", "b"):
        output = tmp_path / f"continuation-{label}"
        shutil.copytree(seed_output, output)
        auditor = _CappedAuditModel(max_calls=2)
        report = run_behavior_map(
            manifest,
            output,
            primary_model=_AuditPlanningAuthor(proposals),
            audit_model=auditor,
            agent_context="Synthetic order-support agent.",
        )
        continuation_reports.append(report)
        continuation_bytes.append((output / "behavior-map.json").read_bytes())

        pattern_ids = {row["pattern_id"] for row in report["behavior_patterns"]}
        assert len(auditor.successful_item_ids) == 2
        assert set(auditor.successful_item_ids) <= pattern_ids
        assert not historical_prefix_ids & set(auditor.successful_item_ids)
        assert auditor.provider_calls == auditor.boundary_invocations == 2
        assert auditor.blocked_item_ids == []
        assert all(
            (output / "behavior-map-checkpoints" / name).read_bytes() == payload
            for name, payload in audit_prefix.items()
        )
        assert any(gap["code"] == "SEMANTIC_AUDIT_MISSING" for gap in report["gaps"])
        missing_ids = {
            gap["item_id"]
            for gap in report["gaps"]
            if gap["code"] == "SEMANTIC_AUDIT_MISSING"
        }
        supported_ids = {
            row["item_id"]
            for row in report["semantic_audit"]["items"]
            if row["decision"] == "SUPPORTED"
        }
        assert missing_ids
        assert missing_ids.isdisjoint(supported_ids)

    assert continuation_reports[0] == continuation_reports[1]
    assert continuation_bytes[0] == continuation_bytes[1]


def test_observed_audit_attempts_cannot_be_understated_by_declared_lane_budget(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(56)
    manifest_path = _write_manifest(tmp_path, traces)
    manifest = json.loads(manifest_path.read_bytes())
    manifest["semantic_budget"] = {
        "cumulative_limit_usd": 70.0,
        "prior_reserved_usd": 0.0,
        "run_max_reserved_usd": 65.16,
        "post_reservation_total_usd": 65.16,
        "remaining_reserve_usd": 4.84,
        "primary_max_reserved_usd": 49.14,
        "audit_max_reserved_usd": 16.02,
    }
    manifest_path.write_bytes(_canonical(manifest, lf=True))
    output = tmp_path / "output"
    auditor = _ObservedOverCapAuditModel()
    first = run_behavior_map(
        manifest_path,
        output,
        primary_model=_AuditPlanningAuthor(proposals),
        audit_model=auditor,
        agent_context="Synthetic order-support agent.",
    )

    assert auditor.provider_calls == 115
    audit_checkpoint_count = 0
    for path in (output / "behavior-map-checkpoints").glob("*.json"):
        value = json.loads(path.read_text())
        if (
            value.get("identity", {})
            .get("stage", "")
            .startswith("independent-semantic-audit-")
        ):
            audit_checkpoint_count += 1
    assert audit_checkpoint_count == 115
    lineage = first["provider_lineage"]["auditor"]
    assert lineage["attempted_call_count"] == 115
    assert lineage["successful_call_count"] == 115
    assert lineage["budget"]["max_calls"] == 89
    assert lineage["budget"]["max_reserved_usd"] == 16.02
    assert lineage["budget"]["reserved_usd"] == 20.70
    assert lineage["actual_cost_state"] == "UNKNOWN"
    assert first["budget"]["audit_reserved_usd"] == 20.70
    assert first["budget"]["total_reserved_usd"] == 69.84
    assert first["budget"]["total_reserved_usd"] < 70.0
    assert first["budget"]["primary_actual_cost_usd"] is None
    assert first["budget"]["audit_actual_cost_usd"] is None
    assert [
        gap
        for gap in first["gaps"]
        if gap["code"] == "SEMANTIC_LANE_BUDGET_CONTRACT_EXCEEDED"
    ] == [
        {
            "code": "SEMANTIC_LANE_BUDGET_CONTRACT_EXCEEDED",
            "stage": "BUDGET",
            "lane": "AUDITOR",
            "declared_max_calls": 89,
            "observed_attempted_call_count": 115,
            "declared_max_reserved_usd": 16.02,
            "observed_reserved_usd": 20.70,
        }
    ]

    report_before = (output / "behavior-map.json").read_bytes()
    replay_auditor = _ObservedOverCapAuditModel()
    second = run_behavior_map(
        manifest_path,
        output,
        primary_model=_AuditPlanningAuthor(proposals),
        audit_model=replay_auditor,
        agent_context="Synthetic order-support agent.",
    )
    assert replay_auditor.provider_calls == 0
    assert first == second
    assert (output / "behavior-map.json").read_bytes() == report_before


def test_provider_disabled_run_never_invokes_semantic_models(tmp_path: Path) -> None:
    class _Trap:
        model_id = "forbidden"

        def complete_json(self, **_: Any) -> dict[str, Any]:
            raise AssertionError("provider-like semantic boundary was called")

        def lineage(self) -> dict[str, Any]:
            return _lineage(self.model_id)

    manifest = _write_manifest(
        tmp_path, [_trace("case", "Cancel my order.", "Okay.")], egress=False
    )
    report = run_behavior_map(
        manifest,
        tmp_path / "output",
        primary_model=_Trap(),
        audit_model=_Trap(),
        agent_context="Synthetic order-support agent.",
    )
    assert report["episodes"] == []
    assert any(gap["code"] == "SEMANTIC_ANALYSIS_UNAVAILABLE" for gap in report["gaps"])


def test_duplicate_membership_is_refused_and_support_equals_unique_membership(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(3)

    class _DuplicateAuthor(_Author):
        def complete_json(
            self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
        ) -> dict[str, Any]:
            result = super().complete_json(
                stage=stage, system=system, payload=payload, schema=schema
            )
            if "populations" in schema.model_fields and result["populations"]:
                duplicate = deepcopy(result["populations"][0])
                duplicate["label"] = "Duplicate family"
                result["populations"].append(duplicate)
            return result

    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_DuplicateAuthor(proposals),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    assert any(
        gap["code"] == "POPULATION_MEMBERSHIP_AMBIGUOUS" for gap in report["gaps"]
    )
    eligible_ids = {row["episode_id"] for row in report["episodes"]}
    assert {
        row["episode_id"]
        for row in report["population_dispositions"]
        if row["disposition"] == "AMBIGUOUS"
    } == eligible_ids
    for population in report["populations"]:
        assert population["support"] == len(set(population["episode_ids"]))


def test_conflicting_population_and_match_dispositions_never_become_assigned(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(13)

    class _ConflictAuthor(_OmittingBatchAuthor):
        def complete_json(
            self, *, stage: str, system: str, payload: dict[str, Any], schema: Any
        ) -> dict[str, Any]:
            result = super().complete_json(
                stage=stage, system=system, payload=payload, schema=schema
            )
            if "populations" in schema.model_fields and payload.get("episodes"):
                episode_id = payload["episodes"][0]["episode_id"]
                if result["populations"]:
                    result["populations"][0]["episode_ids"].append(episode_id)
                result["unassigned_episode_ids"] = [episode_id]
                result["ambiguous_episode_ids"] = [episode_id]
            if "matches" in schema.model_fields and payload.get("episodes"):
                episode_id = payload["episodes"][0]["episode_id"]
                population_id = payload["populations"][0]["population_id"]
                result["matches"] = [
                    {
                        "episode_id": episode_id,
                        "disposition": "MATCH",
                        "population_id": population_id,
                    },
                    {
                        "episode_id": episode_id,
                        "disposition": "NO_MATCH",
                        "population_id": None,
                    },
                ]
            return result

    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_ConflictAuthor(proposals),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )
    conflict_ids = {
        gap["episode_id"]
        for gap in report["gaps"]
        if gap["code"]
        in {"POPULATION_DISPOSITION_CONFLICT", "POPULATION_MATCH_CONFLICT"}
    }
    assert conflict_ids
    dispositions = {
        row["episode_id"]: row["disposition"]
        for row in report["population_dispositions"]
    }
    assert all(dispositions[episode_id] != "ASSIGNED" for episode_id in conflict_ids)


def test_dissimilar_and_unique_leftovers_are_not_forced_together(
    tmp_path: Path,
) -> None:
    traces = [
        _trace("cancel", "Cancel my order.", "I can help."),
        _trace("find", "Find my order.", "I can look."),
        _trace("address", "Change my delivery address.", "I can update it."),
        _trace("novel", "Gift wrap only the replacement lid.", "Let me check."),
    ]
    actions = {
        "cancel": ("CANCEL_ORDER", "order"),
        "find": ("FIND_ORDER", "order"),
        "address": ("CHANGE_ADDRESS", "delivery address"),
        "novel": ("GIFT_WRAP_REPLACEMENT_PART", "replacement lid"),
    }
    proposals: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        trace_id = trace["trace_id"]
        quote = trace["events"][0]["content"]
        row = _episode(trace_id, quote, citations=[_citation(trace_id, 0, quote)])
        row["requested_action"], row["subject"] = actions[trace_id]
        proposals[trace_id] = [row]

    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_Author(proposals),
        audit_model=_Auditor(),
        agent_context="Synthetic order-support agent.",
    )

    by_conversation = {
        row["conversation_id"]: row["episode_id"] for row in report["episodes"]
    }
    assert all(
        len(
            {
                by_conversation[conversation_id]
                for conversation_id in ("cancel", "find", "address", "novel")
            }
            & set(population["episode_ids"])
        )
        <= 1
        for population in report["populations"]
    )
    dispositions = {
        row["episode_id"]: row["disposition"]
        for row in report["population_dispositions"]
    }
    assert dispositions[by_conversation["novel"]] == "INTENTIONALLY_UNASSIGNED"
    assert any(
        row["episode_id"] == by_conversation["novel"]
        and row["reason"] in {"UNASSIGNED_DEMAND", "NOVEL_DEMAND"}
        for row in report["emerging_unknown"]
    )


def test_episode_audit_rejection_is_scoped_and_never_contributes_to_support(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(4)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_Author(proposals),
        audit_model=_Auditor({"cancel-00"}),
        agent_context="Synthetic order-support agent.",
    )
    rejected_id = next(
        row["episode_id"]
        for row in report["episodes"]
        if row["conversation_id"] == "cancel-00"
    )
    population = next(
        row
        for row in report["populations"]
        if row["label"] == "Order cancellation requests"
    )
    assert rejected_id not in population["episode_ids"]
    assert population["support"] == 3 == len(set(population["episode_ids"]))
    disposition = next(
        row
        for row in report["population_dispositions"]
        if row["episode_id"] == rejected_id
    )
    assert disposition["disposition"] == "AUDIT_DISPUTED"
    assert any(
        row["episode_id"] == rejected_id and row["reason"] == "AUDIT_DISAGREEMENT"
        for row in report["emerging_unknown"]
    )


def test_pattern_audit_rejection_never_changes_episode_population_assignment(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(4)
    manifest = _write_manifest(tmp_path, traces)
    output = tmp_path / "output"
    first = run_behavior_map(
        manifest,
        output,
        primary_model=_ScopedAuditPatternAuthor(proposals),
        audit_model=_SubjectScopedAuditor("PATTERN"),
        agent_context="Synthetic order-support agent.",
    )

    rejected_pattern_ids = {
        row["item_id"]
        for row in first["semantic_audit"]["items"]
        if row["decision"] == "UNSUPPORTED"
    }
    assert rejected_pattern_ids
    rejected_patterns = [
        row
        for row in first["behavior_patterns"]
        if row["pattern_id"] in rejected_pattern_ids
    ]
    assert {row["pattern_id"] for row in rejected_patterns} == rejected_pattern_ids
    assert all(
        row["audit_state"] == "UNSUPPORTED"
        and row["visibility"] == "UNPUBLISHED_AUDIT_DISPUTED"
        for row in rejected_patterns
    )
    rejected_occurrence_ids = {
        occurrence_id
        for pattern in rejected_patterns
        for occurrence_id in pattern["occurrence_ids"]
    }
    rejected_occurrence_dispositions = [
        row
        for row in first["pattern_occurrence_dispositions"]
        if row["occurrence_id"] in rejected_occurrence_ids
    ]
    assert {
        row["occurrence_id"] for row in rejected_occurrence_dispositions
    } == rejected_occurrence_ids
    assert all(
        row["disposition"] == "AUDIT_DISPUTED"
        and row["reason"] == "AUDIT_DISAGREEMENT"
        and row["candidate_pattern_id"] in rejected_pattern_ids
        for row in rejected_occurrence_dispositions
    )
    supported_patterns = [
        row for row in first["behavior_patterns"] if row["audit_state"] == "SUPPORTED"
    ]
    assert first["pattern_accounting"]["supported_pattern_count"] == len(
        supported_patterns
    )
    assert first["pattern_accounting"]["published_pattern_support"] == sum(
        row["support"] for row in supported_patterns
    )
    assert first["pattern_accounting"]["active_pattern_membership_count"] == sum(
        len(row["occurrence_ids"]) for row in supported_patterns
    )
    unique_population_members = {
        episode_id
        for population in first["populations"]
        for episode_id in population["episode_ids"]
    }
    assigned_dispositions = {
        row["episode_id"]
        for row in first["population_dispositions"]
        if row["disposition"] == "ASSIGNED"
    }
    assert assigned_dispositions == unique_population_members
    assert all(
        population["support"] == len(set(population["episode_ids"]))
        for population in first["populations"]
    )
    assert not any(
        row["disposition"] == "AUDIT_DISPUTED"
        for row in first["population_dispositions"]
    )

    report_before = (output / "behavior-map.json").read_bytes()
    second = run_behavior_map(
        manifest,
        output,
        primary_model=_ScopedAuditPatternAuthor(proposals),
        audit_model=_SubjectScopedAuditor("PATTERN"),
        agent_context="Synthetic order-support agent.",
    )
    assert first == second
    assert (output / "behavior-map.json").read_bytes() == report_before


def test_only_explicit_episode_audit_creates_audit_disputed_disposition(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(4)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_ScopedAuditPatternAuthor(proposals),
        audit_model=_SubjectScopedAuditor("EPISODE"),
        agent_context="Synthetic order-support agent.",
    )
    rejected_episode_ids = {
        row["item_id"]
        for row in report["semantic_audit"]["items"]
        if row["decision"] == "UNSUPPORTED"
    }
    assert rejected_episode_ids
    disputed_dispositions = {
        row["episode_id"]
        for row in report["population_dispositions"]
        if row["disposition"] == "AUDIT_DISPUTED"
    }
    assert disputed_dispositions == rejected_episode_ids
    unique_population_members = {
        episode_id
        for population in report["populations"]
        for episode_id in population["episode_ids"]
    }
    assert rejected_episode_ids.isdisjoint(unique_population_members)
    assert sum(
        row["disposition"] == "ASSIGNED" for row in report["population_dispositions"]
    ) == len(unique_population_members)


def test_population_audit_rejection_stays_population_scoped(
    tmp_path: Path,
) -> None:
    traces, proposals = _cancellation_corpus(4)
    report = run_behavior_map(
        _write_manifest(tmp_path, traces),
        tmp_path / "output",
        primary_model=_ScopedAuditPatternAuthor(proposals),
        audit_model=_SubjectScopedAuditor("POPULATION"),
        agent_context="Synthetic order-support agent.",
    )
    rejected_population_ids = {
        row["item_id"]
        for row in report["semantic_audit"]["items"]
        if row["decision"] == "UNSUPPORTED"
    }
    assert rejected_population_ids
    assert rejected_population_ids.isdisjoint(
        {row["population_id"] for row in report["populations"]}
    )
    assert not any(
        row["disposition"] == "AUDIT_DISPUTED"
        for row in report["population_dispositions"]
    )
    assert all(
        row["disposition"] == "INTENTIONALLY_UNASSIGNED"
        for row in report["population_dispositions"]
    )
    assert sum(
        row["disposition"] == "ASSIGNED" for row in report["population_dispositions"]
    ) == len(
        {
            episode_id
            for population in report["populations"]
            for episode_id in population["episode_ids"]
        }
    )


def test_private_repair_benchmark_is_complete_unlabeled_and_byte_stable(
    tmp_path: Path,
) -> None:
    benchmark_module = importlib.import_module("triana_labs.behavior_map.benchmark")
    build_repair_benchmark = benchmark_module.build_repair_benchmark
    report = {
        "artifact_kind": "behavior_map_report_v0",
        "schema_version": 0,
        "report_id": "sha256:" + "1" * 64,
        "source": {"source_sha256": "sha256:" + "a" * 64},
        "episodes": [
            {
                "episode_id": "assigned-1",
                "conversation_id": "assigned-conversation",
                "ordinal": 0,
                "status": "PROPOSED",
            },
            {
                "episode_id": "unassigned-1",
                "conversation_id": "unassigned-conversation-1",
                "ordinal": 0,
                "status": "PROPOSED",
            },
            {
                "episode_id": "unassigned-2",
                "conversation_id": "unassigned-conversation-2",
                "ordinal": 0,
                "status": "PROPOSED",
            },
            {
                "episode_id": "audit-disputed-1",
                "conversation_id": "audit-disputed-conversation",
                "ordinal": 0,
                "status": "PROPOSED",
            },
        ],
        "populations": [
            {
                "population_id": "population-1",
                "episode_ids": ["assigned-1"],
                "support": 1,
            }
        ],
        "emerging_unknown": [
            {
                "episode_id": "conversation:no-surviving-1",
                "conversation_id": "no-surviving-1",
                "reason": "NO_SURVIVING_EPISODE",
            },
            {
                "episode_id": "conversation:no-surviving-2",
                "conversation_id": "no-surviving-2",
                "reason": "NO_SURVIVING_EPISODE",
            },
            {"episode_id": "unassigned-1", "reason": "UNASSIGNED_DEMAND"},
            {"episode_id": "unassigned-2", "reason": "UNASSIGNED_DEMAND"},
            {"episode_id": "audit-disputed-1", "reason": "AUDIT_DISAGREEMENT"},
        ],
        "semantic_audit": {
            "items": [
                {
                    "item_id": "audit-rejected-1",
                    "subject_kind": "EPISODE",
                    "decision": "UNSUPPORTED",
                }
            ]
        },
    }
    report_path = tmp_path / "report.json"
    report_path.write_bytes(_canonical(report, lf=True))
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    # Content is generated only in the private pytest directory.  The committed
    # fixture contains no customer quote or identifier.
    checkpoint = {
        "artifact_kind": "behavior_map_checkpoint_v0",
        "schema_version": 0,
        "identity": {
            "stage": "demand-episodes-and-agent-behaviors-0000",
            "model_id": "synthetic-author",
        },
        "payload": {
            "conversations": [
                {"conversation_id": "no-surviving-1"},
                {"conversation_id": "no-surviving-2"},
            ]
        },
        "result": {"episodes": [], "behaviors": []},
    }
    (checkpoints / "synthetic.json").write_bytes(_canonical(checkpoint, lf=True))

    first = build_repair_benchmark(report_path, checkpoints, tmp_path / "first")
    second = build_repair_benchmark(report_path, checkpoints, tmp_path / "second")

    no_surviving = first["failure_panel"]["no_surviving_conversations"]
    unassigned = first["failure_panel"]["unassigned_episodes"]
    assert {row["conversation_id"] for row in no_surviving} == {
        "no-surviving-1",
        "no-surviving-2",
    }
    assert {row["episode_id"] for row in unassigned} == {
        "unassigned-1",
        "unassigned-2",
    }
    assert "audit-disputed-1" not in {row["episode_id"] for row in unassigned}
    for row in no_surviving:
        assert row["human_review"] == {
            "label": None,
            "allowed_labels": [
                "REAL_CUSTOMER_DEMAND",
                "CONSTRAINT_OR_CONTEXT_FRAGMENT",
                "NO_DEMAND",
                "AMBIGUOUS",
            ],
            "exact_customer_evidence": [],
            "distinct_demand_count": None,
            "goal": None,
            "requested_action": None,
        }
    for row in unassigned:
        assert row["human_review"] == {
            "label": None,
            "allowed_labels": [
                "EXISTING_POPULATION",
                "NEW_LEFTOVER_POPULATION",
                "GENUINELY_UNIQUE",
                "AMBIGUOUS_OR_INSUFFICIENT",
            ],
            "existing_population_id": None,
            "new_leftover_group_id": None,
        }
    assert all(
        metric["state"] == "HUMAN_LABELS_MISSING" and metric["value"] is None
        for metric in first["semantic_benchmark"].values()
    )
    assert first["controls"]["selection_sha256"].startswith("sha256:")
    assert (
        first["controls"]["control_kind"] == "UNLABELED_BASELINE_INTEGRITY_CANDIDATES"
    )
    assert "excluded_no_demand_conversation_ids" not in first["controls"]
    assert "distinct_demand_episode_ids" not in first["controls"]
    assert all(
        row["subject_scope"] in {"EPISODE", "POPULATION", "PATTERN"}
        for row in first["controls"]["audit_candidate_items"]
    )
    assert first["benchmark_id"].startswith("sha256:")
    assert first == second
    assert (tmp_path / "first" / "behavior-map-repair-benchmark.json").read_bytes() == (
        tmp_path / "second" / "behavior-map-repair-benchmark.json"
    ).read_bytes()
