# DEPRECATED — slated for deletion, replaced by behavioral-evals pipeline (see
# internal/DELETION_MANIFEST_behavioral_evals.md). build_goal_observable_slate is the
# measurement proposer + semantic-judge backfill + shortlist machinery being replaced.
# Its result also carries context_preflight/typed_gaps (via slate_v3's kept
# _context_preflight/_typed_gaps) for the Context preflight and Evidence gaps tabs,
# which stay working — a follow-up will move that passthrough off this module.
"""Compile agent purpose and historical evidence into repeatable observations."""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
from typing import Any

from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle
from agentagon.exploration_v1.llm import StructuredModel
from agentagon.measurement_discovery_v2 import build_behavior_evidence_map
from agentagon.measurement_promotion import (
    STATE_EXECUTOR,
    build_state_schema_profile,
    classifier_fixture_results,
    compile_measurement,
    compile_population_classifier,
    compute_state_measurement,
)
from agentagon.slate_v3.pipeline import _context_preflight, _slot_candidates, _typed_gaps

from .display_policy import compute_card_display
from .prompts import JUDGE_SYSTEM, JUDGE_VERSION, PROPOSAL_SYSTEM, PROPOSAL_VERSION


GOAL_KINDS = {
    "DOMAIN_OUTCOME",
    "BLOCKED_OR_ERROR",
    "DECISION_INTEGRITY",
    "AUTHORITY_POLICY",
    "BEHAVIOR_EXPLANATION",
    "OPERATIONAL",
}
EVIDENCE_KINDS = {
    "TRACE_TEXT",
    "TOOL_CALL",
    "OBSERVED_STATE",
    "TOOL_RESULT",
    "WORLD_STATE",
    "BUSINESS_OUTCOME",
    "HUMAN_LABEL",
    "EXECUTION_STATUS",
}
EVIDENCE_ALIASES = {
    "BEHAVIOR_CELLS": "TRACE_TEXT",
    "TRACE_EXAMPLES": "TRACE_TEXT",
    "STATE_AFTER": "OBSERVED_STATE",
    "STATE_AFTER_REF": "OBSERVED_STATE",
}
SHORTLIST_QUOTAS = {
    "DOMAIN_OUTCOME": 2,
    "BLOCKED_OR_ERROR": 1,
    "DECISION_INTEGRITY": 1,
    "AUTHORITY_POLICY": 1,
    "BEHAVIOR_EXPLANATION": 1,
    "OPERATIONAL": 1,
}
SHORTLIST_ORDER = tuple(SHORTLIST_QUOTAS)


def build_goal_observable_slate(
    *,
    exploration: dict[str, Any],
    bundles: tuple[NormalizedTraceBundle, ...],
    model: StructuredModel,
    batch_size: int = 10,
    semantic_workers: int = 6,
) -> dict[str, Any]:
    """Build one goal-linked slate while preserving behavioral candidates."""
    if not bundles:
        raise ValueError("At least one normalized trace is required")
    populations = {str(row["population_id"]): row for row in exploration["populations"]}
    behavior_map = build_behavior_evidence_map(exploration, bundles)
    classifiers = {
        population_id: compile_population_classifier(population)
        for population_id, population in populations.items()
    }
    classifier_audits = {
        population_id: classifier_fixture_results(classifiers[population_id], population)
        for population_id, population in populations.items()
    }
    inventory = _evidence_inventory(exploration, bundles, behavior_map)
    state_schema_profile = build_state_schema_profile(bundles)
    raw = model.complete_json(
        stage="goal-observable-proposals",
        prompt_version=PROPOSAL_VERSION,
        system=PROPOSAL_SYSTEM,
        payload={
            "agent_profile": exploration["agent_profile"],
            "populations": [
                {
                    key: row.get(key)
                    for key in (
                        "population_id",
                        "label",
                        "definition",
                        "kind",
                        "support",
                        "representative_demands",
                    )
                }
                for row in populations.values()
                if row.get("kind") != "NON_INTENT_TRAFFIC"
            ],
            "observed_evidence_inventory": inventory,
            "state_schema_profile": _compact_state_schema(state_schema_profile),
        },
    )
    specs, rejected = _validate_specs(raw, populations, state_schema_profile)
    semantic_specs = [spec for spec in specs if not spec.get("state_field")]
    state_specs = [spec for spec in specs if spec.get("state_field")]
    supported, unsupported = _route_specs(semantic_specs, _evidence_contract(bundles))
    units = _compact_units(exploration, bundles)
    measurements = _semantic_backfill(
        model,
        supported,
        units,
        exploration["semantic_facets"],
        batch_size=batch_size,
        semantic_workers=semantic_workers,
    )
    measurements += _state_backfill(state_specs, bundles, exploration["semantic_facets"])
    goal_candidates = []
    for measurement in measurements:
        population_id = measurement["population_ids"][0]
        classifier = (
            classifiers[population_id].to_dict()
            if population_id != "GLOBAL"
            else {
                "compiler_version": "global-population-v1",
                "artifact_hash": hashlib.sha256(b"GLOBAL").hexdigest(),
            }
        )
        definition = compile_measurement(
            measurement,
            author_kind="AUTO_DISCOVERED",
            population_catalog=list(populations.values()),
            supporting_examples=measurement["evidence_ids"][:5],
            evaluator_version=(
                "deterministic-v1"
                if measurement.get("executor") == STATE_EXECUTOR
                else JUDGE_VERSION
            ),
            population_classifier=classifier,
        )
        goal_candidates.append(measurement | {"frozen_definition": definition.to_dict()})

    behavior_candidates = _slot_candidates(behavior_map, populations)
    for candidate in behavior_candidates:
        population_id = candidate["population_id"]
        definition = compile_measurement(
            candidate,
            author_kind="AUTO_DISCOVERED",
            population_catalog=list(populations.values()),
            supporting_examples=candidate["evidence_ids"][:5],
            evaluator_version="deterministic-v1",
            population_classifier=classifiers[population_id].to_dict(),
        )
        candidate["frozen_definition"] = definition.to_dict()
        candidate["candidate_source"] = "BEHAVIORAL_SUPPORTING_INVENTORY"
        candidate["goal_kind"] = "BEHAVIOR_EXPLANATION"

    shortlist = _balanced_shortlist(goal_candidates)
    return {
        "schema_version": "agentagon-goal-observable-v0",
        "authority": "PROPOSED_OPINION",
        "agent_profile": exploration["agent_profile"],
        "trace_count": len(bundles),
        "source_hash": exploration["source_hash"],
        "prompt_versions": {"proposal": PROPOSAL_VERSION, "judge": JUDGE_VERSION},
        "populations": list(populations.values()),
        "behavior_evidence_map": behavior_map,
        "context_preflight": _context_preflight(exploration, bundles),
        "goal_candidate_library": goal_candidates,
        "behavior_candidate_library": behavior_candidates,
        "candidate_library": goal_candidates + behavior_candidates,
        "shortlist": shortlist,
        "unsupported_goal_questions": unsupported,
        "proposal_rejections": rejected,
        "typed_gaps": _typed_gaps(behavior_map, bundles),
        "classifiers": {
            population_id: classifier.to_dict()
            for population_id, classifier in classifiers.items()
        },
        "classifier_audits": classifier_audits,
        "evidence_inventory": inventory,
        "state_schema_profile": state_schema_profile,
        "selection_policy": {
            "version": "balanced-goal-slate-v0",
            "quotas": SHORTLIST_QUOTAS,
            "rule": "Qualified goal-linked candidates first within each concern; fill otherwise empty concern slots with clearly labeled OBSERVED_ONLY candidates. Qualification is never rewritten.",
        },
    }


def _evidence_inventory(
    exploration: dict[str, Any],
    bundles: tuple[NormalizedTraceBundle, ...],
    behavior_map: dict[str, Any],
) -> dict[str, Any]:
    tool_counts: Counter[str] = Counter()
    action_examples: list[str] = []
    state_values: defaultdict[str, Counter[str]] = defaultdict(Counter)
    execution = Counter(bundle.execution.status.value for bundle in bundles)
    for bundle in bundles:
        for event in bundle.events:
            if event.kind is EventKind.TOOL:
                tool_counts[event.name] += 1
                if isinstance(event.content, str) and event.content.strip():
                    action_examples.append(event.content.strip()[:240])
        _collect_leaf_values(bundle.state_after_ref, "state_after", state_values)
    facets = exploration.get("semantic_facets", [])
    facet_examples = [
        {
            "population_id": row.get("population_id"),
            "demand": row.get("demand_summary"),
            "observed_ending": row.get("terminal_summary"),
            "handling": row.get("handling_mode"),
        }
        for row in facets[:80]
    ]
    cells = [
        {
            "cell_id": row["cell_id"],
            "population_id": row["population_id"],
            "category": row["category"],
            "label": row["label"],
            "numerator": row["numerator"],
            "denominator": row["denominator"],
        }
        for row in behavior_map["cells"]
        if row.get("denominator")
    ][:100]
    return {
        "tool_names": [
            {"name": name, "observed_count": count}
            for name, count in tool_counts.most_common(50)
        ],
        "action_event_examples": list(dict.fromkeys(action_examples))[:50],
        "state_fields": [
            {"path": path, "observed_values": [value for value, _ in counts.most_common(8)]}
            for path, counts in sorted(state_values.items())[:50]
        ],
        "execution_statuses": dict(execution),
        "trace_examples": facet_examples,
        "behavior_cells": cells,
        "limits": {
            "tool_results_available": all(
                bool(bundle.provenance.get("tool_results_available")) for bundle in bundles
            ),
            "world_state_available": all(
                bool(bundle.provenance.get("full_world_state_available")) for bundle in bundles
            ),
            "business_outcome_available": all(
                bool(bundle.provenance.get("business_outcome_available")) for bundle in bundles
            ),
        },
    }


def _collect_leaf_values(
    value: Any,
    path: str,
    output: defaultdict[str, Counter[str]],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            _collect_leaf_values(child, f"{path}.{key}", output)
    elif isinstance(value, list):
        for child in value[:20]:
            _collect_leaf_values(child, f"{path}[]", output)
    elif value is not None:
        output[path][str(value)[:120]] += 1


def _validate_specs(
    response: dict[str, Any],
    populations: dict[str, dict[str, Any]],
    state_schema_profile: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = response.get("proposals", [])
    if not isinstance(rows, list) or len(rows) > 10:
        raise ValueError("Goal observable discovery must return at most ten proposals")
    valid_populations = {"GLOBAL"} | set(populations)
    state_fields = _state_field_index(state_schema_profile)
    output: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows, 1):
        proposal_id = _clean(str(row.get("proposal_id") or f"M{index:02d}"))
        goal_kind = str(row.get("goal_kind", "")).upper()
        value_type = str(row.get("value_type", "")).upper()
        population_ids = [str(value) for value in row.get("population_ids", [])]
        categories = [_clean(str(value)).upper() for value in row.get("categories", [])]
        required = [
            EVIDENCE_ALIASES.get(str(value).upper(), str(value).upper())
            for value in row.get("required_evidence", [])
        ]
        state_field = str(row.get("state_field") or "").strip() or None
        errors = []
        if proposal_id in seen:
            errors.append("DUPLICATE_ID")
        if goal_kind not in GOAL_KINDS:
            errors.append("INVALID_GOAL_KIND")
        if len(population_ids) != 1 or population_ids[0] not in valid_populations:
            errors.append("ONE_VALID_POPULATION_REQUIRED")
        if not str(row.get("observable_definition", "")).strip():
            errors.append("MISSING_OBSERVABLE_DEFINITION")

        if state_field is not None or value_type == "NUMBER":
            # A state-field measurement is computed deterministically by code; it
            # must reference a field the schema inspector actually discovered, of
            # the matching inferred type. Code owns the value_set, so we adopt the
            # discovered one rather than trusting the model's category list.
            field = state_fields.get(state_field)
            if field is None:
                errors.append("UNKNOWN_STATE_FIELD")
            elif value_type == "NUMBER" and field["type"] != "NUMERIC":
                errors.append("STATE_FIELD_NOT_NUMERIC")
            elif value_type == "CATEGORY" and field["type"] != "CATEGORICAL":
                errors.append("STATE_FIELD_NOT_CATEGORICAL")
            elif value_type == "BOOLEAN" and field["type"] != "BOOLEAN":
                errors.append("STATE_FIELD_NOT_BOOLEAN")
            elif value_type not in {"NUMBER", "CATEGORY", "BOOLEAN"}:
                errors.append("INVALID_VALUE_TYPE")
            if not errors and value_type != "NUMBER":
                categories = [label.upper() for label in field["value_set"]]
            elif value_type == "NUMBER":
                categories = []
            required = required or ["OBSERVED_STATE"]
        else:
            if value_type not in {"BOOLEAN", "CATEGORY"}:
                errors.append("INVALID_VALUE_TYPE")
            if value_type == "BOOLEAN" and categories != ["TRUE", "FALSE"]:
                errors.append("BOOLEAN_REQUIRES_TRUE_FALSE")
            if value_type == "CATEGORY" and not 2 <= len(set(categories)) <= 5:
                errors.append("CATEGORY_REQUIRES_2_TO_5_LABELS")

        if not required or any(value not in EVIDENCE_KINDS for value in required):
            errors.append("INVALID_EVIDENCE")
        if errors:
            rejected.append({"proposal_id": proposal_id, "reason": ",".join(dict.fromkeys(errors))})
            continue
        seen.add(proposal_id)
        is_state = state_field is not None
        output.append(
            {
                "proposal_id": proposal_id,
                "candidate_id": f"GOAL|{proposal_id}",
                "goal_kind": goal_kind,
                "slot_id": goal_kind,
                "variant_id": proposal_id,
                "title": str(row.get("title") or proposal_id)[:120],
                "developer_question": str(row.get("developer_question", ""))[:400],
                "dimension": "BEHAVIOR",
                "value_type": value_type,
                "population_ids": population_ids,
                "population_label": (
                    "All observed traces"
                    if population_ids[0] == "GLOBAL"
                    else str(populations[population_ids[0]].get("label") or population_ids[0])
                ),
                "observable_definition": str(row["observable_definition"])[:800],
                "categories": list(dict.fromkeys(categories)),
                "required_evidence": list(dict.fromkeys(required)),
                "release_use": str(row.get("release_use", ""))[:500],
                "known_gap": str(row.get("known_gap", ""))[:500],
                "priority_reason": str(row.get("priority_reason", ""))[:500],
                "authority": "PROPOSED_OPINION",
                "state_field": state_field,
                "executor": STATE_EXECUTOR if is_state else "PINNED_SEMANTIC_JUDGE",
                "executor_parameters": (
                    {
                        "state_field": state_field,
                        "aggregation": "NUMERIC_SUMMARY" if value_type == "NUMBER" else "CATEGORY_SHARE",
                        "categories": list(dict.fromkeys(categories)),
                    }
                    if is_state
                    else {
                        "observable_definition": str(row["observable_definition"])[:800],
                        "categories": list(dict.fromkeys(categories)),
                        "prompt_version": JUDGE_VERSION,
                    }
                ),
                "candidate_source": "STATE_FIELD_AGGREGATE" if is_state else "GOAL_TO_OBSERVABLE",
            }
        )
    return output, rejected


def _state_field_index(state_schema_profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["path"]: row
        for group in ("numeric_fields", "categorical_fields", "boolean_fields")
        for row in state_schema_profile.get(group, [])
    }


def _compact_state_schema(state_schema_profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "note": "Fields code already discovered in captured state. Copy a path verbatim into "
        "state_field to track it deterministically.",
        "numeric_fields": [
            {"path": row["path"], "n": row["n"], "min": row["min"], "max": row["max"], "mean": row["mean"]}
            for row in state_schema_profile.get("numeric_fields", [])
        ],
        "categorical_fields": [
            {"path": row["path"], "value_set": row["value_set"]}
            for row in state_schema_profile.get("categorical_fields", [])
        ],
        "boolean_fields": [
            {"path": row["path"]} for row in state_schema_profile.get("boolean_fields", [])
        ],
    }


def _route_specs(
    specs: list[dict[str, Any]], evidence: dict[str, bool]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    supported = []
    unsupported = []
    for spec in specs:
        missing = [value for value in spec["required_evidence"] if not evidence.get(value, False)]
        if missing:
            unsupported.append(
                spec
                | {
                    "status": "UNSUPPORTED",
                    "missing_evidence": missing,
                    "unsupported_reason": "Current traces do not contain "
                    + ", ".join(value.replace("_", " ").lower() for value in missing)
                    + ".",
                }
            )
        else:
            supported.append(spec | {"status": "BACKFILLABLE"})
    return supported, unsupported


def _evidence_contract(bundles: tuple[NormalizedTraceBundle, ...]) -> dict[str, bool]:
    return {
        "TRACE_TEXT": True,
        "TOOL_CALL": any(event.kind is EventKind.TOOL for bundle in bundles for event in bundle.events),
        "OBSERVED_STATE": all(bundle.state_after_ref is not None for bundle in bundles),
        "TOOL_RESULT": all(bool(bundle.provenance.get("tool_results_available")) for bundle in bundles),
        "WORLD_STATE": all(bool(bundle.provenance.get("full_world_state_available")) for bundle in bundles),
        "BUSINESS_OUTCOME": all(bool(bundle.provenance.get("business_outcome_available")) for bundle in bundles),
        "HUMAN_LABEL": all(bool(bundle.provenance.get("human_label_available")) for bundle in bundles),
        "EXECUTION_STATUS": all(bundle.execution.status is not None for bundle in bundles),
    }


def _compact_units(
    exploration: dict[str, Any], bundles: tuple[NormalizedTraceBundle, ...]
) -> list[dict[str, str]]:
    facets = {str(row["evidence_id"]): row for row in exploration["semantic_facets"]}
    units = []
    for bundle in bundles:
        facet = facets.get(bundle.trace_id, {})
        user_lines = []
        agent_lines = []
        tools = []
        for event in bundle.events:
            content = event.content if isinstance(event.content, str) else json.dumps(event.content, sort_keys=True, default=str)
            if event.kind is EventKind.USER:
                user_lines.append(content[:500])
            elif event.kind is EventKind.AGENT:
                agent_lines.append(content[:800])
            elif event.kind is EventKind.TOOL:
                tools.append(f"{event.name}: {content[:300]}")
        compact = "\n".join(
            [
                f"DEMAND: {facet.get('demand_summary', '')}",
                f"OBSERVED ENDING: {facet.get('terminal_summary', '')}",
                f"HANDLING: {facet.get('handling_mode', '')}",
                "USER: " + " | ".join(user_lines[:4]),
                "AGENT: " + " | ".join(agent_lines[-3:]),
                "TOOLS/ACTIONS: " + " | ".join(tools[:20]),
                "STATE AFTER: " + json.dumps(bundle.state_after_ref, sort_keys=True, default=str)[:1800],
                f"EXECUTION: {bundle.execution.status.value}",
                "TRACE BOUNDARY: complete normalized trace evidence for this imported run",
            ]
        )
        units.append({"evidence_id": bundle.trace_id, "compact_evidence": compact[:6000]})
    return units


def _semantic_backfill(
    model: StructuredModel,
    specs: list[dict[str, Any]],
    units: list[dict[str, str]],
    facets: list[dict[str, Any]],
    *,
    batch_size: int,
    semantic_workers: int,
    max_pairs_per_batch: int = 12,
    max_retries: int = 2,
) -> list[dict[str, Any]]:
    if not specs:
        return []
    population_by_evidence = {str(row["evidence_id"]): str(row["population_id"]) for row in facets}
    requests = []
    for unit in units:
        population_id = population_by_evidence.get(unit["evidence_id"])
        applicable = [
            spec
            for spec in specs
            if spec["population_ids"] == ["GLOBAL"] or population_id in spec["population_ids"]
        ]
        if applicable:
            requests.append(
                {
                    "trace": unit,
                    "proposals": [
                        {
                            key: spec[key]
                            for key in (
                                "proposal_id",
                                "title",
                                "observable_definition",
                                "categories",
                            )
                        }
                        for spec in applicable
                    ],
                }
            )

    judged = _judge_with_retries(
        model,
        requests,
        semantic_workers=semantic_workers,
        max_requests_per_batch=max(1, min(batch_size, 12)),
        max_pairs_per_batch=max(1, max_pairs_per_batch),
        max_retries=max(0, max_retries),
    )
    by_proposal: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in judged:
        by_proposal[row["proposal_id"]].append(row)
    output = []
    for spec in specs:
        rows = by_proposal.get(spec["proposal_id"], [])
        values = [row["value"] for row in rows if row["value"] != "ABSTAIN"]
        counts = Counter(values)
        qualification, reason = _qualify(values, spec["value_type"])
        population_id = spec["population_ids"][0]
        distribution = dict(sorted((key.lower(), value) for key, value in counts.items()))
        evaluable = len(values)
        unknown = len(rows) - len(values)
        output.append(
            spec
            | {
                "population_id": population_id,
                "population_label": spec["population_label"],
                "support": len(rows),
                "evaluable": evaluable,
                "unknown": unknown,
                "distribution": distribution,
                "display": compute_card_display(distribution, evaluable, unknown),
                "qualification": qualification,
                "qualification_reason": reason,
                "why_review": spec["priority_reason"],
                "release_change": spec["release_use"],
                "evidence_ids": [row["evidence_id"] for row in rows if row["value"] != "ABSTAIN"][:30],
                "judge_results": rows,
            }
        )
    return output


def _state_backfill(
    specs: list[dict[str, Any]],
    bundles: tuple[NormalizedTraceBundle, ...],
    facets: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compute every state-field measurement deterministically (no model call)."""
    if not specs:
        return []
    population_by_evidence = {str(row["evidence_id"]): str(row["population_id"]) for row in facets}
    output = []
    for spec in specs:
        population_id = spec["population_ids"][0]
        if population_id == "GLOBAL":
            population_bundles = bundles
        else:
            population_bundles = tuple(
                bundle
                for bundle in bundles
                if population_by_evidence.get(bundle.trace_id) == population_id
            )
        computed = compute_state_measurement(spec, population_bundles)
        qualification, reason = _qualify_state(computed)
        numeric_summary = computed.get("numeric_summary")
        display = (
            None
            if numeric_summary is not None
            else compute_card_display(computed["distribution"], computed["evaluable"], computed["unknown"])
        )
        output.append(
            spec
            | {
                "population_id": population_id,
                "population_label": spec["population_label"],
                "support": computed["eligible"],
                "evaluable": computed["evaluable"],
                "unknown": computed["unknown"],
                "distribution": computed["distribution"],
                "numeric_summary": numeric_summary,
                "display": display,
                "qualification": qualification,
                "qualification_reason": reason,
                "why_review": spec["priority_reason"],
                "release_change": spec["release_use"],
                "evidence_ids": computed["evidence_ids"],
                "judge_results": [],
            }
        )
    return output


def _qualify_state(computed: dict[str, Any]) -> tuple[str, str]:
    if computed.get("numeric_summary") is not None:
        summary = computed["numeric_summary"]
        if summary["n"] < 10:
            return "OBSERVED_ONLY", "INSUFFICIENT_SUPPORT"
        if not summary["stdev"]:
            return "OBSERVED_ONLY", "NO_NUMERIC_SPREAD"
        return "QUALIFIED", "NUMERIC_SUPPORT_AND_SPREAD"
    distribution = computed["distribution"]
    if computed["evaluable"] < 10:
        return "OBSERVED_ONLY", "INSUFFICIENT_SUPPORT"
    if sum(count >= 3 for count in distribution.values()) >= 2:
        return "QUALIFIED", "SUPPORT_AND_CONTRAST"
    return "OBSERVED_ONLY", "INSUFFICIENT_CATEGORY_CONTRAST"


def _validate_results(
    response: dict[str, Any], requests: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    expected = {}
    for request in requests:
        evidence_id = request["trace"]["evidence_id"]
        for proposal in request["proposals"]:
            expected[(proposal["proposal_id"], evidence_id)] = (proposal, request["trace"])
    supplied = {
        (str(row.get("proposal_id")), str(row.get("evidence_id"))): row
        for row in response.get("results", [])
        if isinstance(row, dict)
    }
    output = []
    for key, (proposal, trace) in expected.items():
        raw = supplied.get(key)
        abstain_reason: str | None = None
        if raw is None:
            value, quote = "ABSTAIN", ""
            abstain_reason = "NO_RESULT_RETURNED"
        else:
            value = str(raw.get("value", "ABSTAIN")).upper()
            quote = str(raw.get("evidence_quote", ""))
            if value == "ABSTAIN":
                value, quote, abstain_reason = "ABSTAIN", "", "JUDGE_ABSTAIN"
            elif value not in set(proposal["categories"]):
                value, quote, abstain_reason = "ABSTAIN", "", "INVALID_CATEGORY"
            elif not quote:
                value, quote, abstain_reason = "ABSTAIN", "", "QUOTE_EMPTY"
            elif quote not in trace["compact_evidence"]:
                value, quote, abstain_reason = "ABSTAIN", "", "QUOTE_NOT_FOUND"
        output.append(
            {
                "proposal_id": key[0],
                "evidence_id": key[1],
                "value": value,
                "evidence_quote": quote,
                "reason": str((raw or {}).get("reason", ""))[:300],
                "abstain_reason": abstain_reason,
            }
        )
    return output


def _judge_with_retries(
    model: StructuredModel,
    requests: list[dict[str, Any]],
    *,
    semantic_workers: int,
    max_requests_per_batch: int,
    max_pairs_per_batch: int,
    max_retries: int,
) -> list[dict[str, Any]]:
    """Judge every (proposal_id, evidence_id) pair, retrying pairs the model dropped.

    A single batched judge call routinely omits entries for some of the pairs it was
    asked about (the model just doesn't answer every row in a large batch). Re-asking
    only the missing pairs, in smaller batches, recovers most of those without
    changing judge semantics (JUDGE_SYSTEM/JUDGE_VERSION stay pinned).
    """

    def judge(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        try:
            response = model.complete_json(
                stage="goal-observable-backfill",
                prompt_version=JUDGE_VERSION,
                system=JUDGE_SYSTEM,
                payload={"requests": batch},
            )
        except (json.JSONDecodeError, RuntimeError):
            # A single malformed model response (bad unicode escape, truncated
            # JSON, provider error) must not crash the whole run. Treat the
            # batch as unreturned; _validate_results types every pair
            # NO_RESULT_RETURNED, which the retry loop re-requests and, if still
            # missing, reports as a typed unknown rather than a fake value.
            response = {"results": []}
        return _validate_results(response, batch)

    def run_batches(batch_requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
        batches = _pair_budget_chunks(batch_requests, max_pairs_per_batch, max_requests_per_batch)
        if not batches:
            return []
        rows: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
            for batch_rows in pool.map(judge, batches):
                rows.extend(batch_rows)
        return rows

    judged_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in run_batches(requests):
        judged_by_key[(row["proposal_id"], row["evidence_id"])] = row

    for _ in range(max_retries):
        missing_keys = {
            key for key, row in judged_by_key.items() if row["abstain_reason"] == "NO_RESULT_RETURNED"
        }
        if not missing_keys:
            break
        retry_requests = _requests_for_missing(requests, missing_keys)
        if not retry_requests:
            break
        for row in run_batches(retry_requests):
            judged_by_key[(row["proposal_id"], row["evidence_id"])] = row

    return list(judged_by_key.values())


def _pair_budget_chunks(
    requests: list[dict[str, Any]], max_pairs_per_batch: int, max_requests_per_batch: int
) -> list[list[dict[str, Any]]]:
    """Group requests into batches capped by both pair-judgment count and request count."""
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_pairs = 0
    for request in requests:
        pair_count = max(1, len(request["proposals"]))
        if current and (
            current_pairs + pair_count > max_pairs_per_batch or len(current) >= max_requests_per_batch
        ):
            batches.append(current)
            current, current_pairs = [], 0
        current.append(request)
        current_pairs += pair_count
    if current:
        batches.append(current)
    return batches


def _requests_for_missing(
    requests: list[dict[str, Any]], missing_keys: set[tuple[str, str]]
) -> list[dict[str, Any]]:
    """Rebuild minimal requests covering only the still-missing (proposal_id, evidence_id) pairs."""
    missing_proposals_by_evidence: defaultdict[str, set[str]] = defaultdict(set)
    for proposal_id, evidence_id in missing_keys:
        missing_proposals_by_evidence[evidence_id].add(proposal_id)
    retry_requests = []
    for request in requests:
        evidence_id = request["trace"]["evidence_id"]
        wanted = missing_proposals_by_evidence.get(evidence_id)
        if not wanted:
            continue
        proposals = [proposal for proposal in request["proposals"] if proposal["proposal_id"] in wanted]
        if proposals:
            retry_requests.append({"trace": request["trace"], "proposals": proposals})
    return retry_requests


def _qualify(values: list[str], value_type: str) -> tuple[str, str]:
    if len(values) < 10:
        return "OBSERVED_ONLY", "INSUFFICIENT_SUPPORT"
    counts = Counter(values)
    if value_type == "BOOLEAN":
        if counts["TRUE"] >= 3 and counts["FALSE"] >= 3:
            return "QUALIFIED", "SUPPORT_AND_CONTRAST"
        return "OBSERVED_ONLY", "INSUFFICIENT_BOOLEAN_CONTRAST"
    if sum(count >= 3 for count in counts.values()) >= 2:
        return "QUALIFIED", "SUPPORT_AND_CONTRAST"
    return "OBSERVED_ONLY", "INSUFFICIENT_CATEGORY_CONTRAST"


def _balanced_shortlist(candidates: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    eligible = [
        row for row in candidates
        if row["qualification"] in {"QUALIFIED", "OBSERVED_ONLY"} and row["evaluable"] > 0
    ]
    eligible.sort(
        key=lambda row: (
            0 if row["qualification"] == "QUALIFIED" else 1,
            -row["evaluable"],
            row["unknown"],
            row["frozen_definition"]["measurement_id"],
        )
    )
    selected = []
    selected_ids = set()
    for goal_kind in SHORTLIST_ORDER:
        quota = SHORTLIST_QUOTAS[goal_kind]
        for row in [item for item in eligible if item["goal_kind"] == goal_kind][:quota]:
            selected.append(row)
            selected_ids.add(row["candidate_id"])
            if len(selected) == limit:
                return selected
    for row in eligible:
        if row["candidate_id"] not in selected_ids:
            selected.append(row)
            if len(selected) == limit:
                break
    return selected


def _clean(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_")[:80]
