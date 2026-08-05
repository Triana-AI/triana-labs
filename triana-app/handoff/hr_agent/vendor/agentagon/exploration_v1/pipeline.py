"""Portable semantic discovery and advisory proposal pipeline."""

from __future__ import annotations

from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
from pathlib import Path
import re
from statistics import fmean, median
from typing import Any

from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle
from agentagon.exploration_v1.llm import StructuredModel
from agentagon.exploration_v1.report_ui import render_behavioral_analysis
from agentagon.exploration_v1.prompts import (
    CONSOLIDATE_SYSTEM,
    CONSOLIDATE_VERSION,
    FACET_SYSTEM,
    FACET_VERSION,
    PROFILE_SYSTEM,
    PROFILE_VERSION,
    MEASUREMENT_JUDGE_SYSTEM,
    MEASUREMENT_JUDGE_VERSION,
    PROPOSAL_SYSTEM,
    PROPOSAL_VERSION,
)


class ExplorationError(ValueError):
    pass


HANDLING_MODES = {
    "INFORMATION_RETURNED",
    "INFORMATION_REQUESTED",
    "TOOL_ACTION_OBSERVED",
    "HANDOFF_OR_ESCALATION",
    "REFUSAL_OR_LIMIT",
    "STALLED_OR_REPEATED",
    "NO_CLEAR_HANDLING",
}
HANDLING_ALIASES = {
    "INFORMATION_PROVIDED": "INFORMATION_RETURNED",
    "ACTION_EVENT_OBSERVED": "TOOL_ACTION_OBSERVED",
    "RAISE_ESCALATION": "HANDOFF_OR_ESCALATION",
    "HUMAN_HANDOFF": "HANDOFF_OR_ESCALATION",
    "ESCALATION": "HANDOFF_OR_ESCALATION",
    "REFUSED_OR_LIMIT_SET": "REFUSAL_OR_LIMIT",
    "OTHER_OR_UNCLEAR": "NO_CLEAR_HANDLING",
}


def run_exploration(
    bundles: tuple[NormalizedTraceBundle, ...],
    model: StructuredModel,
    *,
    customer_context: str = "",
    batch_size: int = 12,
    semantic_workers: int = 6,
) -> dict[str, Any]:
    if not bundles:
        raise ExplorationError("At least one trace bundle is required")
    if batch_size < 1 or batch_size > 40:
        raise ExplorationError("batch_size must be between 1 and 40")
    units = [_evidence_unit(bundle) for bundle in _one_trial_per_case(bundles)]
    batches = _chunks(units, batch_size)

    def extract(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        facet_batch = [
            {key: value for key, value in row.items() if key != "measurement_transcript"}
            for row in batch
        ]
        response = model.complete_json(
            stage="facets",
            prompt_version=FACET_VERSION,
            system=FACET_SYSTEM,
            payload={"traces": facet_batch},
        )
        return _validate_facets(response, batch)

    facets = []
    with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
        for rows in pool.map(extract, batches):
            facets.extend(rows)
    labels = sorted({row["goal_label"] for row in facets})
    examples = {
        label: [row["demand_summary"] for row in facets if row["goal_label"] == label][:4]
        for label in labels
    }
    populations, label_to_population = _consolidate_hierarchically(
        model,
        labels,
        examples,
        semantic_workers=semantic_workers,
    )
    for facet in facets:
        facet["population_id"] = label_to_population[facet["goal_label"]]
    population_stats = _population_stats(populations, facets)
    profile = model.complete_json(
        stage="profile",
        prompt_version=PROFILE_VERSION,
        system=PROFILE_SYSTEM,
        payload={
            "customer_context": customer_context,
            "population_summary": population_stats,
            "observed_tools": _tool_counts(bundles),
        },
    )
    candidates = _candidate_inventory(facets, population_stats, units)
    qualified = [row for row in candidates if row["qualification"] == "QUALIFIED"]
    evidence_contract = _evidence_contract(bundles)
    proposed = model.complete_json(
        stage="measurement-discovery",
        prompt_version=PROPOSAL_VERSION,
        system=PROPOSAL_SYSTEM,
        payload={
            "profile": profile,
            "populations": [
                {
                    "population_id": row["population_id"],
                    "label": row["label"],
                    "kind": row["kind"],
                    "support": row["support"],
                    "representative_demands": row["representative_demands"],
                }
                for row in population_stats
            ],
            "observed_tools": _tool_counts(bundles),
            "evidence_contract": evidence_contract,
            "observed_analytics": [
                {
                    "candidate_id": row["candidate_id"],
                    "population_label": row["population_label"],
                    "signal": row["signal"],
                    "distribution": row["distribution"],
                }
                for row in qualified
                if row["signal"] != "BEHAVIOR_SUMMARY"
            ],
        },
    )
    proposal_specs, proposal_rejections = _validate_measurement_specs(
        proposed,
        population_stats,
    )
    supported_specs, unsupported_questions = _route_measurement_specs(
        proposal_specs,
        evidence_contract,
    )
    semantic_measurements = _backfill_measurement_specs(
        model,
        supported_specs,
        units,
        facets,
        batch_size=batch_size,
        semantic_workers=semantic_workers,
    )
    proposals = [
        row for row in semantic_measurements if row["qualification"] == "QUALIFIED"
    ][:5]
    behavior_analytics = _behavior_analytics(units, facets, population_stats)
    return {
        "schema_version": "agentagon-exploration-v1",
        "authority": "PROPOSED_OPINION",
        "claim_boundary": "LLM proposes semantic structure; deterministic code computes membership, denominators, qualification, and values; a human decides what matters.",
        "model_id": model.model_id,
        "prompt_versions": {
            "facets": FACET_VERSION,
            "populations": CONSOLIDATE_VERSION,
            "profile": PROFILE_VERSION,
            "proposals": PROPOSAL_VERSION,
            "measurement_judge": MEASUREMENT_JUDGE_VERSION,
        },
        "trace_count": len(units),
        "agent_profile": profile,
        "semantic_facets": facets,
        "populations": population_stats,
        "behavior_analytics": behavior_analytics,
        "candidate_measurements": candidates,
        "observed_analytics": qualified,
        "proposed_measurement_specs": proposal_specs,
        "semantic_measurements": semantic_measurements,
        "suggested_measurements": proposals,
        "unsupported_questions": unsupported_questions,
        "advisory_proposal_rejections": proposal_rejections,
        "full_qualified_inventory_preserved": True,
        "human_checkpoint": "CONFIRM_PROFILE_AND_TRACK_EDIT_DEFER_PROPOSALS",
        "source_hash": hashlib.sha256("".join(sorted(b.content_hash for b in bundles)).encode()).hexdigest(),
    }


def write_exploration_artifacts(output_dir: Path, result: dict[str, Any]) -> tuple[Path, ...]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {
        "exploration.json": result,
        "profile.json": result["agent_profile"],
        "populations.json": result["populations"],
        "candidate_measurements.json": result["candidate_measurements"],
        "suggested_measurements.json": result["suggested_measurements"],
        "proposed_measurement_specs.json": result.get("proposed_measurement_specs", []),
        "semantic_measurements.json": result.get("semantic_measurements", []),
        "unsupported_questions.json": result.get("unsupported_questions", []),
        "advisory_proposal_rejections.json": result["advisory_proposal_rejections"],
    }
    paths: list[Path] = []
    for name, payload in payloads.items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
        paths.append(path)
    facets = output_dir / "semantic_facets.jsonl"
    facets.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in result["semantic_facets"]))
    paths.append(facets)
    review = output_dir / "REVIEW.html"
    review.write_text(_render_review(result), encoding="utf-8")
    paths.append(review)
    html_report = output_dir / "REPORT.html"
    html_report.write_text(render_behavioral_analysis(result), encoding="utf-8")
    paths.append(html_report)
    report = output_dir / "REPORT.md"
    report.write_text(_render_report(result), encoding="utf-8")
    paths.append(report)
    manifest = output_dir / "RUN_MANIFEST.json"
    manifest_payload = {
        "schema_version": result["schema_version"],
        "source_hash": result["source_hash"],
        "trace_adapter": result.get("trace_adapter", {}),
        "model_id": result["model_id"],
        "prompt_versions": result["prompt_versions"],
        "trace_count": result["trace_count"],
        "population_count": len(result["populations"]),
        "candidate_count": len(result["candidate_measurements"]),
        "semantic_measurement_count": len(result.get("semantic_measurements", [])),
        "suggestion_count": len(result["suggested_measurements"]),
        "unsupported_question_count": len(result.get("unsupported_questions", [])),
        "usage": result.get("usage", {}),
        "artifact_hashes": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        },
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n")
    paths.append(manifest)
    return tuple(paths)


def freeze_review(result: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    decisions = {str(row["candidate_id"]): row for row in review.get("decisions", [])}
    known = {row["candidate_id"] for row in result["suggested_measurements"]}
    if set(decisions) - known:
        raise ExplorationError("Review contains unknown candidate ids")
    accepted = []
    for proposal in result["suggested_measurements"]:
        decision = decisions.get(proposal["candidate_id"], {"decision": "DEFER"})
        if decision.get("decision") == "TRACK":
            accepted.append(proposal | {"customer_edit": decision.get("edit", "")})
    return {
        "schema_version": "agentagon-frozen-seed-v1",
        "source_hash": result["source_hash"],
        "confirmed_profile": review.get("confirmed_profile", result["agent_profile"]),
        "tracked_measurements": accepted,
        "deferred_or_unreviewed": len(result["suggested_measurements"]) - len(accepted),
        "authority": "CUSTOMER_REVIEWED",
    }


def _one_trial_per_case(bundles: tuple[NormalizedTraceBundle, ...]) -> tuple[NormalizedTraceBundle, ...]:
    chosen: dict[tuple[str, str], NormalizedTraceBundle] = {}
    for bundle in sorted(bundles, key=lambda row: (row.case_id, row.case_revision, row.trial_id)):
        chosen.setdefault((bundle.case_id, bundle.case_revision), bundle)
    return tuple(chosen.values())


def _evidence_unit(bundle: NormalizedTraceBundle) -> dict[str, Any]:
    lines = []
    measurement_lines = []
    for event in bundle.events:
        if event.kind in {EventKind.USER, EventKind.AGENT, EventKind.TOOL, EventKind.WORKFLOW}:
            content = event.content if isinstance(event.content, str) else json.dumps(event.content, sort_keys=True)
            lines.append(f"{event.kind.value}: {event.name}: {content}"[:1800])
            measurement_content = content
            if event.kind is EventKind.TOOL and event.data:
                measurement_content = json.dumps(
                    {"content": event.content, "data": dict(event.data)},
                    sort_keys=True,
                    default=str,
                )
            measurement_lines.append(
                f"{event.kind.value}: {event.name}: {measurement_content}"[:1800]
            )
    checkpoints: list[str] = []
    agent_contents: list[str] = []
    tool_names: list[str] = []
    for event in bundle.events:
        checkpoint = {
            EventKind.USER: "USER_GOAL_OR_CONTEXT",
            EventKind.AGENT: "AGENT_RESPONSE",
            EventKind.TOOL: "TOOL_ACTION",
            EventKind.WORKFLOW: "WORKFLOW_STEP",
        }.get(event.kind)
        if event.kind is EventKind.TOOL and bundle.provenance.get("tool_order_boundary"):
            checkpoint = None
        if checkpoint and (not checkpoints or checkpoints[-1] != checkpoint):
            checkpoints.append(checkpoint)
        if event.kind is EventKind.AGENT and isinstance(event.content, str):
            agent_contents.append(event.content.strip())
        if event.kind is EventKind.TOOL:
            tool_names.append(event.name)
    return {
        "evidence_id": bundle.trace_id,
        "case_id": bundle.case_id,
        "transcript": "\n".join(lines)[:14000],
        "measurement_transcript": "\n".join(measurement_lines)[:14000],
        "tool_names": tool_names,
        "turn_count": sum(event.kind in {EventKind.USER, EventKind.AGENT} for event in bundle.events),
        "checkpoints": checkpoints,
        "repeated_agent_response": len(agent_contents) != len(set(agent_contents)),
        "repeated_tool_call": len(tool_names) != len(set(tool_names)),
        "tool_order_trustworthy": not bool(bundle.provenance.get("tool_order_boundary")),
    }


def _validate_facets(response: dict[str, Any], batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = response.get("facets")
    if not isinstance(rows, list):
        raise ExplorationError("Facet response must contain facets list")
    expected = {row["evidence_id"]: row for row in batch}
    supplied = {
        str(row.get("evidence_id")): row
        for row in rows
        if str(row.get("evidence_id")) in expected
    }
    output: list[dict[str, Any]] = []
    for evidence_id, evidence in expected.items():
        row = supplied.get(evidence_id)
        if row is None:
            output.append(
                {
                    "evidence_id": evidence_id,
                    "case_id": evidence["case_id"],
                    "demand_summary": "Semantic extraction unavailable",
                    "goal_label": "Semantic extraction gap",
                    "handling_mode": "NO_CLEAR_HANDLING",
                    "claimed_action": "UNKNOWN",
                    "terminal_summary": "",
                    "quotes": [],
                    "quote_grounding": "NONE",
                    "schema_valid": False,
                    "raw_handling_mode": "MISSING_MODEL_ROW",
                    "semantic_evaluable": False,
                    "confidence": "LOW",
                    "tool_observed": bool(evidence["tool_names"]),
                    "turn_count": evidence["turn_count"],
                }
            )
            continue
        raw_mode = str(row.get("handling_mode"))
        mode = HANDLING_ALIASES.get(raw_mode, raw_mode)
        schema_valid = mode in HANDLING_MODES
        if not schema_valid:
            mode = "NO_CLEAR_HANDLING"
        label = _clean_label(str(row.get("goal_label", "")))
        if not label:
            raise ExplorationError("Empty proposed goal label")
        quotes = row.get("quotes", [])
        if not isinstance(quotes, list):
            quotes = []
        valid_quotes = [
            str(quote)
            for quote in quotes
            if str(quote) and str(quote) in evidence["transcript"]
        ]
        output.append({
            "evidence_id": evidence_id,
            "case_id": evidence["case_id"],
            "demand_summary": str(row.get("demand_summary", ""))[:300],
            "goal_label": label,
            "handling_mode": mode,
            "claimed_action": str(row.get("claimed_action", "UNKNOWN")),
            "terminal_summary": str(row.get("terminal_summary", ""))[:300],
            "quotes": valid_quotes[:3],
            "quote_grounding": (
                "EXACT_ALL"
                if valid_quotes and len(valid_quotes) == len(quotes)
                else "EXACT_PARTIAL"
                if valid_quotes
                else "NONE"
            ),
            "schema_valid": schema_valid,
            "raw_handling_mode": raw_mode,
            "semantic_evaluable": bool(valid_quotes) and schema_valid,
            "confidence": str(row.get("confidence", "LOW")),
            "tool_observed": bool(evidence["tool_names"]),
            "turn_count": evidence["turn_count"],
        })
    return output


def _validate_populations(
    response: dict[str, Any],
    labels: list[str],
    *,
    allow_unresolved_remainder: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    rows = response.get("populations")
    if not isinstance(rows, list) or not rows:
        raise ExplorationError("Population response must contain 1-12 populations")
    if len(rows) > 12 and allow_unresolved_remainder:
        overflow_members = [
            str(member)
            for row in rows[11:]
            if isinstance(row, dict)
            for member in row.get("member_labels", [])
        ]
        rows = rows[:11] + [
            {
                "population_id": "OVERFLOW_UNRESOLVED",
                "label": "Mixed/unresolved overflow",
                "kind": "MIXED_UNRESOLVED",
                "definition": "Model exceeded the 12-population contract; overflow labels are retained without a forced semantic merge.",
                "member_labels": overflow_members,
            }
        ]
    elif len(rows) > 12:
        raise ExplorationError("Population response must contain 1-12 populations")
    mapping: dict[str, str] = {}
    output: list[dict[str, Any]] = []
    population_ids: set[str] = set()
    for index, row in enumerate(rows, 1):
        population_id = str(row.get("population_id") or f"P{index:02d}")
        if population_id in population_ids:
            raise ExplorationError(f"Population id assigned twice: {population_id}")
        population_ids.add(population_id)
        members: list[str] = []
        seen_in_row: set[str] = set()
        for item in row.get("member_labels", []):
            member = str(item)
            if member not in labels or member in mapping or member in seen_in_row:
                continue
            seen_in_row.add(member)
            members.append(member)
        if not members:
            continue
        for member in members:
            if member in mapping:
                raise ExplorationError(f"Label assigned twice: {member}")
            mapping[member] = population_id
        output.append({
            "population_id": population_id,
            "label": str(row.get("label", population_id)),
            "kind": str(row.get("kind", "MIXED_UNRESOLVED")),
            "definition": str(row.get("definition", "")),
            "member_labels": members,
        })
    missing = sorted(set(labels) - set(mapping))
    if missing and not allow_unresolved_remainder:
        raise ExplorationError("Population consolidation did not cover every proposed label exactly once")
    if missing:
        unresolved: dict[str, Any] | None = next(
            (row for row in output if row["kind"] == "MIXED_UNRESOLVED"),
            None,
        )
        if unresolved is None and len(output) < 12:
            unresolved = {
                "population_id": "UNRESOLVED",
                "label": "Mixed/unresolved remainder",
                "kind": "MIXED_UNRESOLVED",
                "definition": "Labels omitted or altered by semantic consolidation; retained without forced assignment.",
                "member_labels": [],
                "normalization_note": "MODEL_OMISSION_PRESERVED",
            }
            output.append(unresolved)
        elif unresolved is None:
            unresolved = output[-1]
            unresolved["label"] = "Mixed/unresolved remainder"
            unresolved["kind"] = "MIXED_UNRESOLVED"
            unresolved["normalization_note"] = "MODEL_OMISSION_MERGED_AT_CAP"
        unresolved["member_labels"].extend(missing)
        for member in missing:
            mapping[member] = unresolved["population_id"]
    return output, mapping


def _consolidate_hierarchically(
    model: StructuredModel,
    labels: list[str],
    examples: dict[str, list[str]],
    *,
    semantic_workers: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    items: list[dict[str, Any]] = [
        {"key": label, "original_labels": [label], "examples": examples[label]}
        for label in labels
    ]
    level = 0
    while len(items) > 40:
        batches = [items[index:index + 40] for index in range(0, len(items), 40)]

        def merge(numbered: tuple[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
            chunk_index, batch = numbered
            response = model.complete_json(
                stage=f"populations-level-{level}-chunk-{chunk_index}",
                prompt_version=CONSOLIDATE_VERSION,
                system=CONSOLIDATE_SYSTEM,
                payload={
                    "labels": [
                        {"label": item["key"], "examples": item["examples"][:4]}
                        for item in batch
                    ]
                },
            )
            populations, _ = _validate_populations(
                response,
                [item["key"] for item in batch],
                allow_unresolved_remainder=True,
            )
            by_key = {item["key"]: item for item in batch}
            merged = []
            for population in populations:
                originals = [
                    original
                    for member in population["member_labels"]
                    for original in by_key[member]["original_labels"]
                ]
                merged.append(
                    {
                        "key": f"L{level}C{chunk_index}:{population['population_id']}:{population['label']}",
                        "original_labels": originals,
                        "examples": [
                            example
                            for member in population["member_labels"]
                            for example in by_key[member]["examples"][:2]
                        ][:6],
                    }
                )
            return merged

        next_items: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
            for merged in pool.map(merge, enumerate(batches)):
                next_items.extend(merged)
        items = next_items
        level += 1

    response = model.complete_json(
        stage=f"populations-final-level-{level}",
        prompt_version=CONSOLIDATE_VERSION,
        system=CONSOLIDATE_SYSTEM,
        payload={
            "labels": [
                {"label": item["key"], "examples": item["examples"][:4]}
                for item in items
            ]
        },
    )
    final, _ = _validate_populations(
        response,
        [item["key"] for item in items],
        allow_unresolved_remainder=True,
    )
    by_key = {item["key"]: item for item in items}
    output = []
    original_mapping: dict[str, str] = {}
    for index, population in enumerate(final, 1):
        population_id = f"P{index:02d}"
        original_labels = [
            original
            for member in population["member_labels"]
            for original in by_key[member]["original_labels"]
        ]
        for original in original_labels:
            original_mapping[original] = population_id
        output.append(
            population
            | {
                "population_id": population_id,
                "member_labels": sorted(original_labels),
            }
        )
    if set(original_mapping) != set(labels):
        raise ExplorationError("Hierarchical consolidation lost original labels")
    return output, original_mapping


def _population_stats(populations: list[dict[str, Any]], facets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for facet in facets:
        grouped[facet["population_id"]].append(facet)
    output = []
    for population in populations:
        rows = grouped[population["population_id"]]
        output.append(population | {
            "support": len(rows),
            "handling_distribution": dict(sorted(Counter(row["handling_mode"] for row in rows).items())),
            "representative_demands": [row["demand_summary"] for row in rows[:4]],
            "evidence_ids": [row["evidence_id"] for row in rows],
        })
    return output


def _candidate_inventory(facets: list[dict[str, Any]], populations: list[dict[str, Any]], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = {"GLOBAL": facets} | {
        row["population_id"]: [facet for facet in facets if facet["population_id"] == row["population_id"]]
        for row in populations if row["kind"] == "PROPOSED_GOAL"
    }
    labels = {"GLOBAL": "All observed conversations"} | {row["population_id"]: row["label"] for row in populations}
    candidates = []
    for population_id, rows in groups.items():
        grounded = [row for row in rows if row["semantic_evaluable"]]
        values = {
            "HANDLING_MODE": [row["handling_mode"] for row in grounded],
            "ACTION_OBSERVED": [row["tool_observed"] for row in rows],
            "CLAIM_WITHOUT_ACTION_EVIDENCE": [row["claimed_action"] == "TRUE" and not row["tool_observed"] for row in grounded if row["claimed_action"] != "UNKNOWN"],
            "TURN_COUNT": [row["turn_count"] for row in rows],
            "BEHAVIOR_SUMMARY": [row["terminal_summary"] for row in grounded if row["terminal_summary"]],
        }
        for signal, observed in values.items():
            value_type = {"HANDLING_MODE": "CATEGORY", "ACTION_OBSERVED": "BOOLEAN", "CLAIM_WITHOUT_ACTION_EVIDENCE": "BOOLEAN", "TURN_COUNT": "NUMBER", "BEHAVIOR_SUMMARY": "TEXT"}[signal]
            qualification, reason = _qualify(observed, value_type)
            candidates.append({
                "candidate_id": f"{population_id}|{signal}",
                "population_id": population_id,
                "population_label": labels[population_id],
                "signal": signal,
                "value_type": value_type,
                "support": len(rows),
                "evaluable": len(observed),
                "distribution": _distribution(observed, value_type),
                "qualification": qualification,
                "qualification_reason": reason,
                "evidence_ids": [row["evidence_id"] for row in rows[:5]],
                "executor": "PINNED_SEMANTIC" if signal in {"HANDLING_MODE", "CLAIM_WITHOUT_ACTION_EVIDENCE", "BEHAVIOR_SUMMARY"} else "DETERMINISTIC",
                "authority": "PROPOSED_OPINION",
            })
    return candidates


def _qualify(values: list[Any], value_type: str) -> tuple[str, str]:
    if len(values) < 10:
        return "REJECTED", "INSUFFICIENT_SUPPORT"
    if value_type == "BOOLEAN":
        counts = Counter(
            value if isinstance(value, bool) else str(value).upper() == "TRUE"
            for value in values
        )
        return ("QUALIFIED", "SUPPORT_AND_CONTRAST") if min(counts[True], counts[False]) >= 3 else ("REJECTED", "INSUFFICIENT_BOOLEAN_CONTRAST")
    if value_type == "CATEGORY":
        counts = Counter(values)
        contrasted = sum(count >= 3 for count in counts.values())
        return ("QUALIFIED", "SUPPORT_AND_CONTRAST") if contrasted >= 2 else ("REJECTED", "INSUFFICIENT_CATEGORY_CONTRAST")
    if value_type == "NUMBER":
        return ("QUALIFIED", "SUPPORT_AND_VARIATION") if len(set(values)) >= 2 else ("REJECTED", "ZERO_VARIANCE")
    return ("QUALIFIED", "EVIDENCE_NAVIGATION_ONLY") if len(values) >= 10 else ("REJECTED", "INSUFFICIENT_SUPPORT")


def _distribution(values: list[Any], value_type: str) -> dict[str, Any]:
    if not values:
        return {}
    if value_type in {"BOOLEAN", "CATEGORY"}:
        return dict(sorted((str(key).lower(), value) for key, value in Counter(values).items()))
    if value_type == "NUMBER":
        nums = [float(value) for value in values]
        return {"minimum": min(nums), "median": median(nums), "mean": fmean(nums), "maximum": max(nums)}
    return {"non_empty": len(values), "examples": [str(value)[:180] for value in values[:3]]}


_EVIDENCE_KINDS = {
    "TRACE_TEXT",
    "TOOL_CALL",
    "TOOL_RESULT",
    "WORLD_STATE",
    "BUSINESS_OUTCOME",
    "HUMAN_LABEL",
}


def _evidence_contract(
    bundles: tuple[NormalizedTraceBundle, ...],
) -> dict[str, bool]:
    return {
        "TRACE_TEXT": True,
        "TOOL_CALL": any(
            event.kind is EventKind.TOOL for bundle in bundles for event in bundle.events
        ),
        "TOOL_RESULT": all(
            bool(bundle.provenance.get("tool_results_available")) for bundle in bundles
        ),
        "WORLD_STATE": all(
            bool(bundle.provenance.get("full_world_state_available")) for bundle in bundles
        ),
        "BUSINESS_OUTCOME": all(
            bool(bundle.provenance.get("business_outcome_available")) for bundle in bundles
        ),
        "HUMAN_LABEL": all(
            bool(bundle.provenance.get("human_label_available")) for bundle in bundles
        ),
    }


def _validate_measurement_specs(
    response: dict[str, Any],
    populations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = response.get("proposals", [])
    if not isinstance(rows, list) or len(rows) > 6:
        raise ExplorationError("Measurement discovery must return at most six proposals")
    valid_population_ids = {"GLOBAL"} | {
        str(row["population_id"]) for row in populations
    }
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for index, raw in enumerate(rows, 1):
        proposal_id = _clean_label(str(raw.get("proposal_id") or f"M{index:02d}"))
        if proposal_id in seen:
            rejected.append({"proposal_id": proposal_id, "reason": "DUPLICATE_ID"})
            continue
        seen.add(proposal_id)
        dimension = str(raw.get("dimension", "")).upper()
        value_type = str(raw.get("value_type", "")).upper()
        population_ids = [str(value) for value in raw.get("population_ids", [])]
        required = [str(value).upper() for value in raw.get("required_evidence", [])]
        categories = [_clean_label(str(value)).upper().replace(" ", "_") for value in raw.get("categories", [])]
        errors = []
        if dimension not in {"BEHAVIOR", "EXECUTION", "BUSINESS", "EVALUATION", "MECHANICAL"}:
            errors.append("INVALID_DIMENSION")
        if value_type not in {"BOOLEAN", "CATEGORY"}:
            errors.append("INVALID_VALUE_TYPE")
        if not population_ids or any(value not in valid_population_ids for value in population_ids):
            errors.append("INVALID_POPULATION")
        if not required or any(value not in _EVIDENCE_KINDS for value in required):
            errors.append("INVALID_EVIDENCE_REQUIREMENT")
        if value_type == "BOOLEAN" and categories != ["TRUE", "FALSE"]:
            errors.append("BOOLEAN_REQUIRES_TRUE_FALSE")
        if value_type == "CATEGORY" and not 2 <= len(set(categories)) <= 5:
            errors.append("CATEGORY_REQUIRES_2_TO_5_LABELS")
        if not str(raw.get("observable_definition", "")).strip():
            errors.append("MISSING_OBSERVABLE_DEFINITION")
        if errors:
            rejected.append({"proposal_id": proposal_id, "reason": ",".join(errors)})
            continue
        output.append(
            {
                "proposal_id": proposal_id,
                "candidate_id": f"PROPOSED|{proposal_id}",
                "title": str(raw.get("title", proposal_id))[:120],
                "developer_question": str(raw.get("developer_question", ""))[:300],
                "dimension": dimension,
                "value_type": value_type,
                "population_ids": population_ids,
                "observable_definition": str(raw["observable_definition"])[:600],
                "categories": list(dict.fromkeys(categories)),
                "required_evidence": list(dict.fromkeys(required)),
                "release_use": str(raw.get("release_use", ""))[:400],
                "known_gap": str(raw.get("known_gap", ""))[:400],
                "priority_reason": str(raw.get("priority_reason", ""))[:400],
                "authority": "PROPOSED_OPINION",
            }
        )
    return output, rejected


def _route_measurement_specs(
    specs: list[dict[str, Any]], evidence_contract: dict[str, bool]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    supported: list[dict[str, Any]] = []
    unsupported: list[dict[str, Any]] = []
    for spec in specs:
        explicit_requirements = list(spec["required_evidence"])
        inferred_requirements: list[str] = []
        wording = " ".join(
            str(spec.get(key, ""))
            for key in ("title", "developer_question")
        ).lower()
        if re.search(r"\b(correct|correctly|accurate|accurately|accuracy|effective|effectively|appropriate|appropriately|proper|properly|complete|completeness|compliant|compliance)\b", wording):
            inferred_requirements.append("HUMAN_LABEL")
        if re.search(r"\b(successful|successfully|actual|actually|authorized|authorization|resolved|resolution|world state|state changed)\b", wording):
            inferred_requirements.append("WORLD_STATE")
        if re.search(r"\b(impact|revenue|conversion|retention|satisfaction|throughput quality)\b", wording):
            inferred_requirements.append("BUSINESS_OUTCOME")
        requirements = list(dict.fromkeys(explicit_requirements + inferred_requirements))
        missing = [
            requirement
            for requirement in requirements
            if not evidence_contract.get(requirement, False)
        ]
        if missing:
            unsupported.append(
                spec
                | {
                    "required_evidence": requirements,
                    "status": "UNSUPPORTED",
                    "missing_evidence": missing,
                    "unsupported_reason": (
                        "Current traces do not contain "
                        + ", ".join(value.replace("_", " ").lower() for value in missing)
                        + ". Agentagon will not infer it from wording or tool presence."
                    ),
                }
            )
        explicit_missing = [
            requirement
            for requirement in explicit_requirements
            if not evidence_contract.get(requirement, False)
        ]
        if explicit_missing:
            continue
        proxy = spec
        if inferred_requirements:
            proxy = spec | {
                "proposal_id": f"{spec['proposal_id']}-PROXY",
                "candidate_id": f"{spec['candidate_id']}-PROXY",
                "title": f"Observable proxy: {spec['title']}",
                "known_gap": (
                    f"This proxy does not answer the original question: {spec['developer_question']} "
                    + (spec["known_gap"] or "Authoritative outcome evidence is unavailable.")
                )[:700],
            }
        normalized_question = (
            "How often do scoped traces show: "
            + str(spec["observable_definition"]).rstrip(".")
            + "?"
        )
        supported.append(
            proxy
            | {
                "developer_question": normalized_question,
                "release_use": (
                    "Compare baseline and candidate rates for this observable proxy: "
                    + str(spec["observable_definition"]).rstrip(".")
                    + "."
                )[:700],
                "required_evidence": explicit_requirements,
                "status": "BACKFILLABLE_PROXY" if inferred_requirements else "BACKFILLABLE",
            }
        )
    return supported, unsupported


def _backfill_measurement_specs(
    model: StructuredModel,
    specs: list[dict[str, Any]],
    units: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    *,
    batch_size: int,
    semantic_workers: int,
) -> list[dict[str, Any]]:
    if not specs:
        return []
    population_by_evidence = {
        str(row["evidence_id"]): str(row["population_id"]) for row in facets
    }
    requests: list[dict[str, Any]] = []
    for spec in specs:
        for unit in units:
            population_id = population_by_evidence.get(str(unit["evidence_id"]))
            if "GLOBAL" not in spec["population_ids"] and population_id not in spec["population_ids"]:
                continue
            requests.append(
                {
                    "proposal": {
                        "proposal_id": spec["proposal_id"],
                        "title": spec["title"],
                        "observable_definition": spec["observable_definition"],
                        "categories": spec["categories"],
                        "required_evidence": spec["required_evidence"],
                    },
                    "trace": {
                        "evidence_id": unit["evidence_id"],
                        "case_id": unit["case_id"],
                        "transcript": unit["measurement_transcript"],
                    },
                }
            )

    def judge(batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        response = model.complete_json(
            stage="measurement-backfill",
            prompt_version=MEASUREMENT_JUDGE_VERSION,
            system=MEASUREMENT_JUDGE_SYSTEM,
            payload={"requests": batch},
        )
        return _validate_measurement_results(response, batch)

    judged: list[dict[str, Any]] = []
    judge_batch_size = min(24, max(4, batch_size))
    with ThreadPoolExecutor(max_workers=max(1, semantic_workers)) as pool:
        for rows in pool.map(judge, _chunks(requests, judge_batch_size)):
            judged.extend(rows)
    by_proposal: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in judged:
        by_proposal[row["proposal_id"]].append(row)
    output: list[dict[str, Any]] = []
    for spec in specs:
        rows = by_proposal.get(spec["proposal_id"], [])
        evaluable = [row for row in rows if row["value"] != "ABSTAIN"]
        values = [row["value"] for row in evaluable]
        qualification, reason = _qualify(values, spec["value_type"])
        distribution = dict(
            sorted((str(key).lower(), count) for key, count in Counter(values).items())
        )
        support = len(rows)
        output.append(
            spec
            | {
                "population_id": ",".join(spec["population_ids"]),
                "population_label": _measurement_population_label(spec, facets),
                "signal": spec["title"].upper().replace(" ", "_")[:80],
                "support": support,
                "evaluable": len(evaluable),
                "unknown": support - len(evaluable),
                "distribution": distribution,
                "qualification": qualification,
                "qualification_reason": reason,
                "executor": "PINNED_SEMANTIC_JUDGE",
                "category": "RELEASE_MEASUREMENT",
                "why_review": spec["priority_reason"],
                "release_change": spec["release_use"],
                "evidence_ids": [row["evidence_id"] for row in evaluable[:12]],
                "judge_results": rows,
            }
        )
    return output


def _validate_measurement_results(
    response: dict[str, Any], requests: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    expected = {
        (str(row["proposal"]["proposal_id"]), str(row["trace"]["evidence_id"])): row
        for row in requests
    }
    supplied = {
        (str(row.get("proposal_id")), str(row.get("evidence_id"))): row
        for row in response.get("results", [])
        if isinstance(row, dict)
    }
    output: list[dict[str, Any]] = []
    for key, request in expected.items():
        raw = supplied.get(key, {})
        allowed = set(request["proposal"]["categories"])
        value = str(raw.get("value", "ABSTAIN")).upper()
        quote = str(raw.get("evidence_quote", ""))
        transcript = str(request["trace"]["transcript"])
        if value not in allowed or not quote or quote not in transcript:
            value = "ABSTAIN"
            quote = ""
        output.append(
            {
                "proposal_id": key[0],
                "evidence_id": key[1],
                "value": value,
                "evidence_quote": quote,
                "reason": str(raw.get("reason", ""))[:300],
            }
        )
    return output


def _measurement_population_label(
    spec: dict[str, Any], facets: list[dict[str, Any]]
) -> str:
    if "GLOBAL" in spec["population_ids"]:
        return "All observed conversations"
    labels = sorted(
        {
            str(row["goal_label"])
            for row in facets
            if str(row["population_id"]) in spec["population_ids"]
        }
    )
    return ", ".join(labels[:3]) or ", ".join(spec["population_ids"])


def _validate_proposals(
    response: dict[str, Any],
    qualified: list[dict[str, Any]],
    *,
    text_cue_already_selected: bool = False,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    rows = response.get("proposals", [])
    if not isinstance(rows, list) or len(rows) > 5:
        raise ExplorationError("Proposal response must contain at most five proposals")
    available = {row["candidate_id"]: row for row in qualified}
    seen: set[str] = set()
    output = []
    rejections: list[dict[str, str]] = []
    text_cue_selected = text_cue_already_selected
    for row in rows:
        candidate_id = str(row.get("candidate_id"))
        if candidate_id not in available or candidate_id in seen:
            raise ExplorationError(f"Unknown or duplicate proposal: {candidate_id}")
        seen.add(candidate_id)
        question = str(row.get("developer_question", ""))
        signal = str(available[candidate_id]["signal"])
        forbidden = {
            "HANDLING_MODE": {
                "effective", "effectively", "correct", "correctly", "successful",
                "successfully", "appropriate", "appropriately", "resolved", "compliant",
            },
            "ACTION_OBSERVED": {
                "unauthorized", "authorized", "correct", "correctly", "successful", "successfully",
            },
        }.get(signal, set())
        overclaims = sorted(set(re.findall(r"[a-z]+", question.lower())) & forbidden)
        if overclaims:
            rejections.append(
                {
                    "candidate_id": candidate_id,
                    "reason": "QUESTION_OVERCLAIMS_SIGNAL:" + ",".join(overclaims),
                }
            )
            continue
        value_type = str(available[candidate_id]["value_type"])
        if value_type == "TEXT":
            if text_cue_selected:
                rejections.append(
                    {
                        "candidate_id": candidate_id,
                        "reason": "ONLY_ONE_TEXT_INVESTIGATION_CUE_ALLOWED",
                    }
                )
                continue
            category = "INVESTIGATION_CUE"
            text_cue_selected = True
        else:
            category = str(row.get("category", "BEHAVIOR_ANALYTIC"))
            if category not in {
                "RELEASE_MEASUREMENT",
                "BEHAVIOR_ANALYTIC",
                "INVESTIGATION_CUE",
            }:
                category = "BEHAVIOR_ANALYTIC"
        explanation = _proposal_explanation(available[candidate_id])
        output.append(available[candidate_id] | {
            "category": category,
            "developer_question": question,
            **explanation,
        })
    return output, rejections


def _proposal_explanation(candidate: dict[str, Any]) -> dict[str, str]:
    signal = str(candidate["signal"])
    if signal == "HANDLING_MODE":
        return {
            "why_review": "This population has enough evidence and more than one observed handling category to compare.",
            "release_change": "Compare the baseline and candidate distributions of observed handling categories.",
            "known_gap": "Handling categories do not establish correctness, resolution, policy compliance, or world-state success.",
        }
    if signal == "BEHAVIOR_SUMMARY":
        return {
            "why_review": "Evidence-linked summaries can reveal recurring examples worth inspecting before a scorer exists.",
            "release_change": "Surface qualitative examples whose wording or terminal handling differs between runs.",
            "known_gap": "Text summaries are investigation context, not an aggregate score or correctness judgment.",
        }
    if signal == "ACTION_OBSERVED":
        return {
            "why_review": "Both action-present and action-absent traces exist in this population.",
            "release_change": "Compare the share of traces containing at least one observable action event.",
            "known_gap": "Action presence does not establish authorization, argument correctness, or successful external state change.",
        }
    if signal == "CLAIM_WITHOUT_ACTION_EVIDENCE":
        return {
            "why_review": "The historical evidence contains both claim/evidence matches and mismatches.",
            "release_change": "Compare explicit action claims that lack a matching observable action event.",
            "known_gap": "Missing trace evidence is not proof that no external action occurred; instrumentation coverage still matters.",
        }
    return {
        "why_review": "The historical evidence has enough support and numeric variation to compare.",
        "release_change": "Compare the baseline and candidate distributions for this observed quantity.",
        "known_gap": "This quantity alone does not establish correctness, efficiency, or user success.",
    }


def _tool_counts(bundles: tuple[NormalizedTraceBundle, ...]) -> dict[str, int]:
    return dict(sorted(Counter(event.name for bundle in bundles for event in bundle.events if event.kind is EventKind.TOOL).items()))


def _behavior_analytics(
    units: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    populations: list[dict[str, Any]],
) -> dict[str, Any]:
    transitions: Counter[tuple[str, str]] = Counter()
    ordered_tool_pairs: Counter[tuple[str, str]] = Counter()
    tool_cooccurrence: Counter[tuple[str, str]] = Counter()
    tools: Counter[str] = Counter()
    tool_order_trustworthy = all(unit["tool_order_trustworthy"] for unit in units)
    for unit in units:
        transitions.update(zip(unit["checkpoints"], unit["checkpoints"][1:]))
        tool_sequence = unit["tool_names"]
        tools.update(tool_sequence)
        if unit["tool_order_trustworthy"]:
            ordered_tool_pairs.update(zip(tool_sequence, tool_sequence[1:]))
        unique_tools = sorted(set(tool_sequence))
        tool_cooccurrence.update(
            (unique_tools[left], unique_tools[right])
            for left in range(len(unique_tools))
            for right in range(left + 1, len(unique_tools))
        )
    return {
        "top_populations": sorted(populations, key=lambda row: (-row["support"], row["population_id"])),
        "handling_distribution": dict(sorted(Counter(row["handling_mode"] for row in facets).items())),
        "top_tools": [{"name": name, "count": count} for name, count in tools.most_common(12)],
        "checkpoint_transitions": [
            {"from": pair[0], "to": pair[1], "count": count}
            for pair, count in transitions.most_common(12)
        ],
        "ordered_tool_pairs": [
            {"first": pair[0], "second": pair[1], "count": count}
            for pair, count in ordered_tool_pairs.most_common(12)
        ],
        "tool_order_trustworthy": tool_order_trustworthy,
        "tool_cooccurrence": [
            {"left": pair[0], "right": pair[1], "count": count}
            for pair, count in tool_cooccurrence.most_common(12)
        ],
        "repetition": {
            "repeated_agent_response": sum(row["repeated_agent_response"] for row in units),
            "repeated_tool_call": sum(row["repeated_tool_call"] for row in units),
        },
        "semantic_grounding": dict(
            sorted(Counter(row["quote_grounding"] for row in facets).items())
        ),
        "trajectory_boundary": "Checkpoint transitions are observed local patterns, not an ideal path or correctness verdict. Tool order is reported only when the source preserves it.",
    }


def _clean_label(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())[:80]


def _chunks(rows: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [rows[index:index + size] for index in range(0, len(rows), size)]


def _render_report(result: dict[str, Any]) -> str:
    return "\n".join([
        "# Agentagon Exploration V1", "", f"**Boundary:** {result['claim_boundary']}", "",
        f"- Traces analyzed: **{result['trace_count']}**", f"- Proposed populations: **{len(result['populations'])}**",
        f"- Primitive observed analytics: **{len(result['candidate_measurements'])}**",
        f"- Agent-specific questions backfilled: **{len(result.get('semantic_measurements', []))}**",
        f"- Qualified release-measurement proposals: **{len(result['suggested_measurements'])}**",
        f"- Unsupported questions retained: **{len(result.get('unsupported_questions', []))}**", "",
        "Observed analytics are not automatically release criteria. Agent-specific proposals remain PROPOSED / OPINION until Track, Edit, or Defer review.", "",
    ])


def _render_review(result: dict[str, Any]) -> str:
    cards = []
    for row in result["suggested_measurements"]:
        dist = html.escape(json.dumps(row["distribution"], sort_keys=True))
        cid = html.escape(row["candidate_id"])
        cards.append(f'''<article><header><div><small>{html.escape(row['value_type'])} · {html.escape(row['category'])}</small><h2>{html.escape(row['developer_question'])}</h2></div><b>PROPOSED · OPINION</b></header><p>{html.escape(row['why_review'])}</p><code>{dist}</code><p><strong>Could expose:</strong> {html.escape(row['release_change'])}</p><p><strong>Cannot establish:</strong> {html.escape(row['known_gap'])}</p><div class="actions"><button data-id="{cid}" data-action="TRACK">Track</button><button data-id="{cid}" data-action="EDIT">Edit</button><button data-id="{cid}" data-action="DEFER">Defer</button></div></article>''')
    data = json.dumps({"source_hash": result["source_hash"]}).replace("</", "<\\/")
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Agentagon proposal review</title><style>body{{font:15px system-ui;margin:0;background:#f5f7f8;color:#172027}}main{{max-width:1100px;margin:auto;padding:32px}}.notice{{border-left:4px solid #b68216;background:#fff8df;padding:14px}}article{{background:white;border:1px solid #d7dfe3;border-radius:8px;padding:20px;margin:16px 0}}header{{display:flex;justify-content:space-between;gap:20px}}small{{color:#5b6972}}b{{color:#74520c}}code{{display:block;white-space:pre-wrap;background:#eef3f4;padding:12px}}button{{padding:9px 15px;margin-right:8px}}button.selected{{background:#126b4d;color:white}}textarea{{width:100%;min-height:70px;display:none;margin-top:10px}}</style></head><body><main><h1>Suggested release measurements</h1><div class="notice"><strong>These are not golden evals.</strong> A pinned model proposed agent-specific questions; an evidence-grounded judge backfilled them; code enforced support and contrast. You still decide what matters.</div>{''.join(cards)}<button id="download">Download review</button></main><script>const base={data};const decisions={{}};document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{{const id=b.dataset.id;const action=b.dataset.action;decisions[id]={{candidate_id:id,decision:action}};b.parentElement.querySelectorAll('button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected');}});document.getElementById('download').onclick=()=>{{const blob=new Blob([JSON.stringify({{...base,decisions:Object.values(decisions)}},null,2)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='HUMAN_REVIEW.json';a.click();}};</script></body></html>'''


def _render_html_report(result: dict[str, Any]) -> str:
    analytics = result["behavior_analytics"]
    total = result["trace_count"]
    ungrounded = analytics["semantic_grounding"].get("NONE", 0)
    mixed = sum(
        row["support"]
        for row in result["populations"]
        if row["kind"] == "MIXED_UNRESOLVED"
    )
    populations = "".join(
        f'''<tr><td><strong>{html.escape(row['label'])}</strong><small>{html.escape(row['kind'])}</small></td><td>{row['support']} · {row['support'] / total:.1%}</td><td>{html.escape(_compact_counts(row['handling_distribution'], row['support']))}</td><td>{html.escape('; '.join(row['representative_demands'][:2]))}</td></tr>'''
        for row in analytics["top_populations"]
    )
    tools = "".join(
        f"<li><strong>{html.escape(row['name'])}</strong><span>{row['count']} observed calls</span></li>"
        for row in analytics["top_tools"]
    ) or "<li><span>No tool events were captured.</span></li>"
    transitions = "".join(
        f"<li><strong>{html.escape(row['from'].replace('_', ' ').title())}</strong><i>→</i><strong>{html.escape(row['to'].replace('_', ' ').title())}</strong><span>{row['count']} conversations/transitions</span></li>"
        for row in analytics["checkpoint_transitions"]
    ) or "<li><span>No ordered checkpoint transitions available.</span></li>"
    if analytics["tool_order_trustworthy"]:
        tool_pair_title = "Recurring ordered tool pairs"
        tool_pairs = "".join(
            f"<li><strong>{html.escape(row['first'])}</strong><i>→</i><strong>{html.escape(row['second'])}</strong><span>{row['count']} observed sequences</span></li>"
            for row in analytics["ordered_tool_pairs"]
        ) or "<li><span>No ordered tool pairs were captured.</span></li>"
    else:
        tool_pair_title = "Recurring tool co-occurrence"
        tool_pairs = "".join(
            f"<li><strong>{html.escape(row['left'])}</strong><i>+</i><strong>{html.escape(row['right'])}</strong><span>{row['count']} conversations</span></li>"
            for row in analytics["tool_cooccurrence"]
        ) or "<li><span>No recurring tool pairs were captured.</span></li>"
    suggestions = "".join(
        f'''<article class="card"><div class="cardtop"><div><small>{html.escape(row['value_type'])} · {html.escape(row['population_label'])}</small><h3>{html.escape(row['developer_question'])}</h3></div><b>PROPOSED · OPINION</b></div><p>{html.escape(row['why_review'])}</p><pre>{html.escape(json.dumps(row['distribution'], sort_keys=True, indent=2))}</pre><p><strong>Release use:</strong> {html.escape(row['release_change'])}</p><p class="muted"><strong>Gap:</strong> {html.escape(row['known_gap'])}</p></article>'''
        for row in result["suggested_measurements"]
    ) or '<div class="callout">The bounded proposer returned no sufficiently relevant suggestions. The qualified inventory remains available for review.</div>'
    profile = result["agent_profile"]
    profile_json = html.escape(json.dumps(profile, indent=2, sort_keys=True))
    method = html.escape("""raw traces -> TraceAdapter@version -> NormalizedTraceBundle
  -> deterministic evidence units
  -> pinned LLM facets in bounded batches
       demand label + observed handling + evidence quotes
  -> hierarchical pinned LLM consolidation
       proposed Goal populations + non-intent/mixed buckets
  -> CODE backfill
       exact membership + denominators + distributions
       every supported population x signal pair
  -> CODE qualification gates
       support + contrast + variance + typed rejection
  -> bounded LLM advisory proposal pass
       selects <=5 from qualified candidate IDs only
       code validates claims; at most two repair calls
  -> human Track / Edit / Defer
  -> frozen seed definitions and proposed regression cases""")
    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agentagon cold-start report</title><style>
*{{box-sizing:border-box}}body{{margin:0;font:15px/1.5 Inter,system-ui,sans-serif;background:#f4f6f7;color:#182127}}nav{{position:sticky;top:0;z-index:2;display:flex;gap:4px;padding:12px 24px;background:#17242a}}nav button{{border:0;background:transparent;color:#aebbc1;padding:10px 14px;cursor:pointer}}nav button.active{{background:#fff;color:#17242a;border-radius:5px}}main{{max-width:1180px;margin:auto;padding:36px 24px 70px}}section{{display:none}}section.active{{display:block}}h1{{font-size:32px;margin:0}}h2{{font-size:21px}}h3{{margin:4px 0}}.lede{{color:#5d6b72;max-width:780px}}.head{{display:flex;justify-content:space-between;gap:20px;align-items:start;margin-bottom:26px}}.badge,b{{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#74520c;background:#fff6d8;border:1px solid #ddc976;padding:5px 8px;border-radius:4px;white-space:nowrap}}.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}}.kpi,.panel,.card,.callout{{background:#fff;border:1px solid #d8e0e3;border-radius:7px;padding:18px}}.kpi strong{{display:block;font-size:26px;background:none;border:0;padding:0;color:#17242a}}.kpi span,small,.muted{{display:block;color:#66757c}}.tablewrap{{overflow-x:auto;border:1px solid #d8e0e3;background:#fff}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{text-align:left;padding:13px;border-bottom:1px solid #e3e8ea;vertical-align:top}}th{{font-size:12px;color:#66757c}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}ul.paths,ul.tools{{list-style:none;margin:0;padding:0}}ul.paths li,ul.tools li{{display:flex;gap:10px;align-items:center;border-bottom:1px solid #e3e8ea;padding:11px 0}}ul.paths span,ul.tools span{{margin-left:auto;color:#66757c}}.cards{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.cardtop{{display:flex;justify-content:space-between;gap:12px}}pre{{white-space:pre-wrap;background:#edf2f3;padding:14px;border-radius:5px;overflow:auto}}.callout{{border-left:4px solid #c69325;margin:18px 0}}@media(max-width:800px){{.kpis,.grid,.cards{{grid-template-columns:1fr}}.head{{display:block}}table{{font-size:13px;min-width:820px}}}}
</style></head><body><nav><button class="active" data-tab="behavior">Behavioral analysis</button><button data-tab="measurements">Proposed measurements</button><button data-tab="method">How it works</button></nav><main>
<section id="behavior" class="active"><div class="head"><div><h1>Behavioral analysis</h1><p class="lede">What users ask this agent to do, how it responds, and which recurring local paths appear in the imported traces. This is an observed baseline, not a correctness verdict.</p></div><span class="badge">Semantic groups are proposed</span></div>
<div class="kpis"><div class="kpi"><span>Traces analyzed</span><strong>{total}</strong></div><div class="kpi"><span>Demand populations</span><strong>{len(result['populations'])}</strong></div><div class="kpi"><span>Quote-grounded facets</span><strong>{(total - ungrounded) / total:.1%}</strong></div><div class="kpi"><span>Qualified candidates</span><strong>{sum(r['qualification']=='QUALIFIED' for r in result['candidate_measurements'])}</strong></div></div>
<h2>Top user intents and demand populations</h2><p class="lede">The pinned model proposes labels; code owns population membership, support, percentages, and handling distributions.</p><div class="tablewrap"><table><thead><tr><th>Population</th><th>Size</th><th>Observed handling</th><th>Examples</th></tr></thead><tbody>{populations}</tbody></table></div>
<div class="callout"><strong>Uncertainty is retained.</strong> {mixed} of {total} traces remain in mixed/unresolved populations, and {ungrounded} semantic rows have no exact supporting quote. They remain visible but do not enter semantic measurement denominators.</div>
<div class="grid" style="margin-top:18px"><div class="panel"><h2>Common tools</h2><ul class="tools">{tools}</ul></div><div class="panel"><h2>Behavioral checkpoint transitions</h2><p class="muted">{html.escape(analytics['trajectory_boundary'])}</p><ul class="paths">{transitions}</ul></div><div class="panel"><h2>{tool_pair_title}</h2><ul class="paths">{tool_pairs}</ul></div><div class="panel"><h2>Loop and repetition cues</h2><p><strong>{analytics['repetition']['repeated_agent_response']}</strong> traces repeat an identical agent response.</p><p><strong>{analytics['repetition']['repeated_tool_call']}</strong> traces repeat a tool name.</p><p class="muted">These are investigation cues; repeated calls can be valid retries.</p></div></div></section>
<section id="measurements"><div class="head"><div><h1>Proposed measurements</h1><p class="lede">Evidence-backed quantities Agentagon can already backfill. They become tracked only after customer confirmation.</p></div><span class="badge">Proposed · Opinion</span></div><div class="callout"><strong>These are not golden evals.</strong> Qualification only means enough support and contrast exist to inspect the measurement. The advisory LLM selected from the qualified inventory; it did not invent values or decide importance.</div><div class="cards">{suggestions}</div></section>
<section id="method"><div class="head"><div><h1>How this report was produced</h1><p class="lede">The same pipeline accepts any provider through a versioned trace adapter. Customer-specific parsing and labels remain outside the core.</p></div></div><div class="grid"><div class="panel"><h2>Pipeline</h2><pre>{method}</pre></div><div class="panel"><h2>Proposed profile</h2><pre>{profile_json}</pre></div></div><div class="callout"><strong>Why not ask one LLM for interesting things?</strong> Free-form analysis is useful for hypotheses but lacks stable identities, denominators, exhaustive coverage, reproducibility, and release-to-release comparability. Here, LLM judgment is bounded to semantic proposals; code and human review provide the durable structure.</div></section>
</main><script>const buttons=[...document.querySelectorAll('nav button')];buttons.forEach(b=>b.onclick=()=>{{buttons.forEach(x=>x.classList.remove('active'));document.querySelectorAll('section').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}});</script></body></html>'''


def _compact_counts(counts: dict[str, int], total: int) -> str:
    return " · ".join(
        f"{key.replace('_', ' ').lower()}: {value} ({value / total:.0%})"
        for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )
