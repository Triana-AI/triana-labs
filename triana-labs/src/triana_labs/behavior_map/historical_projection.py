"""Provider-disabled projection of completed semantics onto corrected grounding."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]


class HistoricalProjectionError(ValueError):
    """Typed refusal raised before a historical projection is published."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _canonical(value: Any, *, newline: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if newline else b"")


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _identity(namespace: str, value: Any) -> str:
    return _sha256(namespace.encode("utf-8") + b"\0" + _canonical(value))


def _read(path: Path) -> tuple[JsonObject, bytes]:
    try:
        payload = path.read_bytes()
        value = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise HistoricalProjectionError(
            "HISTORICAL_PROJECTION_BINDING_INVALID"
        ) from error
    if not isinstance(value, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BINDING_INVALID")
    return cast(JsonObject, value), payload


def _rows(value: JsonObject, key: str) -> list[JsonObject]:
    rows = value.get(key)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
    return cast(list[JsonObject], rows)


def _index(rows: list[JsonObject], key: str) -> dict[str, JsonObject]:
    result: dict[str, JsonObject] = {}
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or identity in result:
            raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
        result[identity] = row
    return result


def _support(row: JsonObject, member_key: str) -> int:
    members = row.get(member_key, [])
    return len(set(cast(list[str], members))) if isinstance(members, list) else 0


def _nonnegative_decimal(row: JsonObject, key: str) -> Decimal:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    try:
        result = Decimal(str(value))
    except InvalidOperation as error:
        raise HistoricalProjectionError(
            "HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID"
        ) from error
    if not result.is_finite() or result < 0:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    return result


def _nonnegative_call_count(row: JsonObject, key: str) -> int:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    return value


def _historical_budget(
    predecessor_budget: JsonObject, provider_lineage: JsonObject
) -> JsonObject:
    primary = provider_lineage.get("primary")
    auditor = provider_lineage.get("auditor")
    if not isinstance(primary, dict) or not isinstance(auditor, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    auditor_budget = auditor.get("budget")
    if not isinstance(auditor_budget, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    primary_calls = _nonnegative_call_count(primary, "attempted_call_count")
    audit_calls = _nonnegative_call_count(auditor, "attempted_call_count")
    declared_reserve = _nonnegative_decimal(
        predecessor_budget, "audit_max_reserved_usd"
    )
    if declared_reserve != _nonnegative_decimal(
        predecessor_budget, "audit_reserved_usd"
    ):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    reservation_rate = _nonnegative_decimal(
        cast(JsonObject, auditor_budget), "reservation_usd_per_call"
    )
    if reservation_rate == 0:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    declared_call_cap = declared_reserve / reservation_rate
    if declared_call_cap != declared_call_cap.to_integral_value():
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    observed_reserve = _nonnegative_decimal(
        cast(JsonObject, auditor_budget), "reserved_usd"
    )
    if observed_reserve != reservation_rate * audit_calls:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    total_reserve = _nonnegative_decimal(predecessor_budget, "total_reserved_usd")
    if "cumulative_budget_ceiling_usd" in predecessor_budget:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    cumulative_ceiling = _nonnegative_decimal(
        predecessor_budget, "cumulative_limit_usd"
    )
    if (
        "primary_actual_cost_usd" not in predecessor_budget
        or predecessor_budget["primary_actual_cost_usd"] is not None
        or "audit_actual_cost_usd" not in predecessor_budget
        or predecessor_budget["audit_actual_cost_usd"] is not None
    ):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    cap = int(declared_call_cap)
    return {
        "historical_primary_attempted_call_count": primary_calls,
        "historical_audit_declared_call_cap": cap,
        "historical_audit_declared_reserved_usd": float(declared_reserve),
        "historical_audit_attempted_call_count": audit_calls,
        "historical_audit_excess_call_count": max(0, audit_calls - cap),
        "historical_audit_observed_reserved_usd": float(observed_reserve),
        "historical_total_reserved_usd": float(total_reserve),
        "historical_cumulative_budget_ceiling_usd": float(cumulative_ceiling),
        "historical_total_within_cumulative_ceiling": (
            total_reserve <= cumulative_ceiling
        ),
        "historical_actual_cost_state": "UNKNOWN",
        "historical_budget_state": (
            "SEMANTIC_LANE_BUDGET_CONTRACT_EXCEEDED"
            if audit_calls > cap
            else "WITHIN_SEMANTIC_LANE_BUDGET_CONTRACT"
        ),
        "projection_primary_attempted_call_count": 0,
        "projection_audit_attempted_call_count": 0,
    }


def _new_population(
    predecessor: JsonObject,
    members: list[str],
    affected: list[str],
    episode_by_id: dict[str, JsonObject],
) -> JsonObject:
    before_support = _support(predecessor, "episode_ids")
    identity = {
        "label": predecessor.get("label"),
        "definition": predecessor.get("definition"),
        "episode_ids": members,
        "support": len(members),
        "method": predecessor.get("method"),
        "audit_state": "MISSING",
        "visibility": "UNPUBLISHED_AUDIT_MISSING",
    }
    return {
        "population_id": _identity("behavior-map-population-v0", identity),
        **identity,
        "representative_evidence_ids": sorted(
            {
                evidence_id
                for episode_id in members[:3]
                for evidence_id in cast(
                    list[str], episode_by_id[episode_id].get("evidence_ids", [])
                )
            }
        ),
        "predecessor_population_id": predecessor["population_id"],
        "predecessor_lineage": {
            "reason": "GROUNDING_FRONTIER_MEMBERSHIP_CHANGED",
            "affected_episode_ids": affected,
            "before_support": before_support,
            "after_support": len(members),
        },
    }


def _pattern_support(
    occurrence_ids: list[str], occurrence_by_id: dict[str, JsonObject]
) -> int:
    rows = [occurrence_by_id[occurrence_id] for occurrence_id in occurrence_ids]
    episode_ids = {
        episode_id
        for row in rows
        for episode_id in cast(list[str], row.get("episode_ids", []))
    }
    return (
        len(episode_ids)
        if episode_ids
        else len(
            {
                cast(str, row["conversation_id"])
                for row in rows
                if isinstance(row.get("conversation_id"), str)
            }
        )
    )


def _new_pattern(
    predecessor: JsonObject,
    occurrence_ids: list[str],
    affected: list[str],
    occurrence_by_id: dict[str, JsonObject],
) -> JsonObject:
    support = _pattern_support(occurrence_ids, occurrence_by_id)
    identity = {
        "label": predecessor.get("label"),
        "definition": predecessor.get("definition"),
        "occurrence_ids": occurrence_ids,
        "support": support,
        "audit_state": "MISSING",
        "visibility": "UNPUBLISHED_AUDIT_MISSING",
    }
    return {
        "pattern_id": _identity("behavior-map-pattern-v0", identity),
        **identity,
        "predecessor_pattern_id": predecessor["pattern_id"],
        "predecessor_lineage": {
            "reason": "GROUNDING_FRONTIER_OCCURRENCE_MEMBERSHIP_CHANGED",
            "affected_occurrence_ids": affected,
            "before_support": _support(predecessor, "occurrence_ids"),
            "after_support": support,
        },
    }


def _edge_conservation(
    predecessor_rows: list[JsonObject],
    projected_rows: list[JsonObject],
    *,
    identity_key: str,
    predecessor_key: str,
    member_key: str,
    excluded_rejected_members: set[str],
    excluded_grounding_replacement_members: set[str],
    excluded_audit_disputed_members: set[str] | None = None,
) -> JsonObject:
    before_edges = {
        (cast(str, row[identity_key]), member)
        for row in predecessor_rows
        for member in cast(list[str], row.get(member_key, []))
    }
    after_edges = {
        (cast(str, row[identity_key]), member)
        for row in projected_rows
        for member in cast(list[str], row.get(member_key, []))
    }
    successor_by_predecessor = {
        cast(str, row[predecessor_key]): cast(str, row[identity_key])
        for row in projected_rows
        if isinstance(row.get(predecessor_key), str)
    }
    exact = 0
    superseded = 0
    excluded_rejected = 0
    excluded_grounding_replacement = 0
    excluded_audit_disputed = 0
    unexplained = 0
    for subject_id, member_id in before_edges:
        if member_id in excluded_rejected_members:
            excluded_rejected += 1
        elif member_id in excluded_grounding_replacement_members:
            excluded_grounding_replacement += 1
        elif member_id in (excluded_audit_disputed_members or set()):
            excluded_audit_disputed += 1
        elif (subject_id, member_id) in after_edges:
            exact += 1
        elif (
            subject_id in successor_by_predecessor
            and (successor_by_predecessor[subject_id], member_id) in after_edges
        ):
            superseded += 1
        else:
            unexplained += 1
    result: JsonObject = {
        "before": len(before_edges),
        "exact_preserved": exact,
        "explicitly_superseded": superseded,
        "excluded_rejected": excluded_rejected,
        "excluded_grounding_replacement": excluded_grounding_replacement,
        "unexplained": unexplained,
    }
    if excluded_audit_disputed:
        result["excluded_audit_disputed"] = excluded_audit_disputed
    return result


def _write_once(path: Path, payload: bytes) -> None:
    descriptor, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    temporary = Path(name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        path.chmod(0o600)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def project_grounded_behavior_map(
    *,
    predecessor_report_path: str | Path,
    corrected_extraction_path: str | Path,
    binding_path: str | Path,
    output_dir: str | Path,
) -> JsonObject:
    """Project exact historical authority without invoking semantic providers."""

    predecessor, predecessor_bytes = _read(Path(predecessor_report_path))
    corrected, corrected_bytes = _read(Path(corrected_extraction_path))
    binding, _binding_bytes = _read(Path(binding_path))
    source = predecessor.get("source")
    grounding_validation = corrected.get("grounding_validation")
    expected_report_id = _identity(
        "behavior-map-report-v0",
        {key: value for key, value in predecessor.items() if key != "report_id"},
    )
    valid = (
        predecessor.get("artifact_kind") == "behavior_map_report_v0"
        and predecessor.get("schema_version") == 0
        and predecessor.get("report_id") == expected_report_id
        and isinstance(source, dict)
        and corrected.get("artifact_kind") == "behavior_map_grounded_extraction_v0"
        and corrected.get("schema_version") == 0
        and isinstance(grounding_validation, dict)
        and grounding_validation.get("all_final_grounding_valid") is True
        and binding.get("artifact_kind")
        == "behavior_map_historical_projection_binding_v0"
        and binding.get("schema_version") == 0
        and binding.get("privacy_class") == "PRIVATE"
        and binding.get("provider_egress") == "DISABLED"
        and binding.get("predecessor_report_id") == predecessor.get("report_id")
        and isinstance(predecessor.get("baseline_predecessor_report_id"), str)
        and binding.get("baseline_predecessor_report_id")
        == predecessor.get("baseline_predecessor_report_id")
        and binding.get("predecessor_report_sha256") == _sha256(predecessor_bytes)
        and binding.get("corrected_extraction_sha256") == _sha256(corrected_bytes)
        and binding.get("source_sha256") == source.get("source_sha256")
        and binding.get("selected_list_sha256") == source.get("selected_list_sha256")
        and corrected.get("predecessor_report_id") == predecessor.get("report_id")
        and corrected.get("source_sha256") == binding.get("source_sha256")
        and corrected.get("selected_list_sha256") == binding.get("selected_list_sha256")
    )
    if not valid:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BINDING_INVALID")

    predecessor_episodes = _rows(predecessor, "episodes")
    corrected_episodes = _rows(corrected, "episodes")
    rejected_rows = _rows(corrected, "rejected_episodes")
    predecessor_episode_by_id = _index(predecessor_episodes, "episode_id")
    rejected_by_id = _index(rejected_rows, "predecessor_episode_id")
    rejected_episode_ids = set(rejected_by_id)
    episodes: list[JsonObject] = []
    exact_episode_ids: set[str] = set()
    replacement_by_predecessor: dict[str, str] = {}
    for source_episode in corrected_episodes:
        episode = dict(source_episode)
        episode_id = episode.get("episode_id")
        if not isinstance(episode_id, str):
            raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
        candidates = episode.pop("predecessor_episode_candidates", None)
        if episode_id in predecessor_episode_by_id:
            if candidates not in (None, []):
                raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
            exact_episode_ids.add(episode_id)
        elif (
            not isinstance(candidates, list)
            or len(candidates) != 1
            or not isinstance(candidates[0], str)
            or candidates[0] not in predecessor_episode_by_id
            or candidates[0] in replacement_by_predecessor
        ):
            raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
        else:
            predecessor_episode_id = candidates[0]
            episode["predecessor_episode_id"] = predecessor_episode_id
            replacement_by_predecessor[predecessor_episode_id] = episode_id
        episodes.append(episode)
    episode_by_id = _index(episodes, "episode_id")
    if exact_episode_ids | set(
        replacement_by_predecessor
    ) | rejected_episode_ids != set(predecessor_episode_by_id) or bool(
        (exact_episode_ids & set(replacement_by_predecessor))
        | (exact_episode_ids & rejected_episode_ids)
        | (set(replacement_by_predecessor) & rejected_episode_ids)
    ):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_CONSERVATION_INVALID")

    rejected_episodes = [
        {**row, "status": "EXCLUDED_HISTORY"}
        for row in sorted(
            rejected_rows, key=lambda item: item["predecessor_episode_id"]
        )
    ]
    old_dispositions = {
        cast(str, row["episode_id"]): row
        for row in _rows(predecessor, "population_dispositions")
    }
    predecessor_audit_disputed_ids = {
        episode_id
        for episode_id, disposition in old_dispositions.items()
        if disposition.get("disposition") == "AUDIT_DISPUTED"
        and episode_id in exact_episode_ids
    }
    predecessor_populations = _rows(predecessor, "populations")
    populations: list[JsonObject] = []
    excluded_population_memberships: list[JsonObject] = []
    exact_population_ids: set[str] = set()
    for predecessor_population in predecessor_populations:
        old_members = list(
            cast(list[str], predecessor_population.get("episode_ids", []))
        )
        members = sorted(
            member
            for member in old_members
            if member in exact_episode_ids
            and member not in rejected_episode_ids
            and member not in predecessor_audit_disputed_ids
        )
        affected = sorted(set(old_members) - set(members))
        excluded_population_memberships.extend(
            {
                "episode_id": episode_id,
                "population_id": predecessor_population["population_id"],
                "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
                "status": "EXCLUDED_HISTORY",
            }
            for episode_id in sorted(set(old_members) & set(replacement_by_predecessor))
        )
        excluded_population_memberships.extend(
            {
                "episode_id": episode_id,
                "predecessor_population_id": predecessor_population["population_id"],
                "reason": "SOURCE_EPISODE_GROUNDING_REJECTED",
                "status": "EXCLUDED_HISTORY",
            }
            for episode_id in sorted(set(old_members) & rejected_episode_ids)
        )
        excluded_population_memberships.extend(
            {
                "episode_id": episode_id,
                "predecessor_population_id": predecessor_population["population_id"],
                "reason": "PREDECESSOR_AUDIT_DISPUTED",
                "status": "EXCLUDED_HISTORY",
            }
            for episode_id in sorted(set(old_members) & predecessor_audit_disputed_ids)
        )
        if members == sorted(set(old_members)):
            population = dict(predecessor_population)
            population["episode_ids"] = members
            population["support"] = len(members)
            exact_population_ids.add(cast(str, population["population_id"]))
        elif members:
            population = _new_population(
                predecessor_population, members, affected, episode_by_id
            )
        else:
            continue
        populations.append(population)
    populations.sort(key=lambda row: cast(str, row["population_id"]))
    excluded_population_memberships.sort(
        key=lambda row: (
            cast(str, row["episode_id"]),
            cast(
                str,
                row.get("population_id", row.get("predecessor_population_id")),
            ),
        )
    )

    supported_populations = [
        population
        for population in populations
        if population.get("audit_state") == "SUPPORTED"
    ]
    candidate_populations = [
        population
        for population in populations
        if population.get("audit_state") != "SUPPORTED"
    ]
    population_by_episode = {
        episode_id: cast(str, population["population_id"])
        for population in supported_populations
        for episode_id in cast(list[str], population["episode_ids"])
    }
    candidate_episode_ids = {
        episode_id
        for population in candidate_populations
        for episode_id in cast(list[str], population["episode_ids"])
    }
    dispositions: list[JsonObject] = []
    for episode_id in sorted(episode_by_id):
        if episode_id in predecessor_audit_disputed_ids:
            dispositions.append(
                {
                    "episode_id": episode_id,
                    "disposition": "AUDIT_DISPUTED",
                    "reason": "PREDECESSOR_AUDIT_DISPUTE_PRESERVED",
                }
            )
        elif episode_id in population_by_episode:
            dispositions.append(
                {
                    "episode_id": episode_id,
                    "disposition": "ASSIGNED",
                    "population_id": population_by_episode[episode_id],
                    "reason": "POPULATION_MEMBERSHIP",
                }
            )
        elif episode_id in replacement_by_predecessor.values():
            dispositions.append(
                {
                    "episode_id": episode_id,
                    "disposition": "INTENTIONALLY_UNASSIGNED",
                    "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
                }
            )
        elif episode_id in candidate_episode_ids:
            dispositions.append(
                {
                    "episode_id": episode_id,
                    "disposition": "INTENTIONALLY_UNASSIGNED",
                    "reason": "REAUDIT_REQUIRED",
                }
            )
        else:
            previous = old_dispositions.get(episode_id, {})
            dispositions.append(
                {
                    "episode_id": episode_id,
                    "disposition": "INTENTIONALLY_UNASSIGNED",
                    "reason": cast(
                        str, previous.get("reason", "HISTORICAL_MEMBERSHIP_REMOVED")
                    ),
                }
            )

    predecessor_occurrences = _rows(predecessor, "behavior_occurrences")
    occurrences: list[JsonObject] = []
    excluded_occurrences: list[JsonObject] = []
    excluded_occurrence_ids: set[str] = set()
    rejected_occurrence_ids: set[str] = set()
    replacement_occurrence_ids: set[str] = set()
    for occurrence in predecessor_occurrences:
        member_ids = set(cast(list[str], occurrence.get("episode_ids", [])))
        if member_ids & rejected_episode_ids:
            occurrence_id = cast(str, occurrence["occurrence_id"])
            excluded_occurrence_ids.add(occurrence_id)
            rejected_occurrence_ids.add(occurrence_id)
            excluded_occurrences.append(
                {
                    "occurrence_id": occurrence_id,
                    "episode_ids": sorted(member_ids),
                    "reason": "SOURCE_EPISODE_GROUNDING_REJECTED",
                    "status": "EXCLUDED_HISTORY",
                }
            )
        elif member_ids <= exact_episode_ids:
            occurrences.append(dict(occurrence))
        else:
            occurrence_id = cast(str, occurrence["occurrence_id"])
            excluded_occurrence_ids.add(occurrence_id)
            replacement_occurrence_ids.add(occurrence_id)
            excluded_occurrences.append(
                {
                    "occurrence_id": occurrence_id,
                    "episode_ids": sorted(member_ids),
                    "reason": "GROUNDING_REPLACEMENT_REQUIRES_SEMANTIC_REVIEW",
                    "status": "EXCLUDED_HISTORY",
                }
            )
    occurrences.sort(key=lambda row: cast(str, row["occurrence_id"]))
    excluded_occurrences.sort(key=lambda row: cast(str, row["occurrence_id"]))
    occurrence_by_id = _index(occurrences, "occurrence_id")

    predecessor_patterns = _rows(predecessor, "behavior_patterns")
    patterns: list[JsonObject] = []
    exact_pattern_ids: set[str] = set()
    for predecessor_pattern in predecessor_patterns:
        old_members = list(
            cast(list[str], predecessor_pattern.get("occurrence_ids", []))
        )
        members = sorted(set(old_members) - excluded_occurrence_ids)
        affected = sorted(set(old_members) - set(members))
        if members == sorted(set(old_members)):
            pattern = dict(predecessor_pattern)
            pattern["occurrence_ids"] = members
            exact_pattern_ids.add(cast(str, pattern["pattern_id"]))
        elif members:
            pattern = _new_pattern(
                predecessor_pattern, members, affected, occurrence_by_id
            )
        else:
            continue
        patterns.append(pattern)
    patterns.sort(key=lambda row: cast(str, row["pattern_id"]))

    semantic_audit = predecessor.get("semantic_audit")
    if not isinstance(semantic_audit, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
    audit_items = semantic_audit.get("items")
    if not isinstance(audit_items, list):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_INPUT_INVALID")
    current_audits: list[JsonObject] = []
    historical_audits: list[JsonObject] = []
    current_subject_ids = exact_population_ids | exact_pattern_ids | exact_episode_ids
    for raw_audit in cast(list[JsonObject], audit_items):
        audit = dict(raw_audit)
        subject_id = audit.get("subject_id", audit.get("item_id"))
        if subject_id in current_subject_ids:
            current_audits.append(audit)
        else:
            historical_audits.append(
                {**audit, "history_status": "SUPERSEDED_SUBJECT_HISTORY_ONLY"}
            )
    current_audits.sort(key=lambda row: str(row.get("audit_id", row.get("item_id"))))
    historical_audits.sort(key=lambda row: str(row.get("audit_id", row.get("item_id"))))

    population_edges = _edge_conservation(
        predecessor_populations,
        populations,
        identity_key="population_id",
        predecessor_key="predecessor_population_id",
        member_key="episode_ids",
        excluded_rejected_members=rejected_episode_ids,
        excluded_grounding_replacement_members=set(replacement_by_predecessor),
        excluded_audit_disputed_members=predecessor_audit_disputed_ids,
    )
    pattern_edges = _edge_conservation(
        predecessor_patterns,
        patterns,
        identity_key="pattern_id",
        predecessor_key="predecessor_pattern_id",
        member_key="occurrence_ids",
        excluded_rejected_members=rejected_occurrence_ids,
        excluded_grounding_replacement_members=replacement_occurrence_ids,
    )
    if population_edges["unexplained"] or pattern_edges["unexplained"]:
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_CONSERVATION_INVALID")

    predecessor_budget = predecessor.get("budget")
    if not isinstance(predecessor_budget, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    provider_lineage = predecessor.get("provider_lineage")
    if not isinstance(provider_lineage, dict):
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_BUDGET_LINEAGE_INVALID")
    historical_budget = _historical_budget(
        cast(JsonObject, predecessor_budget), cast(JsonObject, provider_lineage)
    )
    gaps: list[JsonObject] = [
        {"code": "HISTORICAL_PROJECTION_NOT_FULL_REANALYSIS", "stage": "PROJECTION"},
        {"code": "HUMAN_LABELS_MISSING", "stage": "SEMANTIC_BENCHMARK"},
    ]
    gaps.extend(
        {
            "code": "SEMANTIC_AUDIT_MISSING",
            "stage": "AUDIT",
            "item_id": row.get("population_id", row.get("pattern_id")),
        }
        for row in [*populations, *patterns]
        if row.get("audit_state") == "MISSING"
    )
    report: JsonObject = {
        "artifact_kind": "behavior_map_historical_projection_v0",
        "schema_version": 0,
        "artifact_status": "PRIVATE_PROPOSED_PARTIAL_HISTORICAL_PROJECTION",
        "semantic_evaluation_state": "HISTORICAL_SEMANTIC_PROJECTION_PARTIAL",
        "predecessor_report_id": binding["predecessor_report_id"],
        "baseline_predecessor_report_id": binding["baseline_predecessor_report_id"],
        "claim_boundary": {
            "full_reanalysis": False,
            "defect_b_benchmark_pass": False,
            "accepted_taxonomy": False,
            "human_labels": "MISSING",
        },
        "binding": {
            key: binding[key]
            for key in (
                "predecessor_report_id",
                "baseline_predecessor_report_id",
                "predecessor_report_sha256",
                "corrected_extraction_sha256",
                "source_sha256",
                "selected_list_sha256",
                "provider_egress",
            )
        },
        "episodes": sorted(episodes, key=lambda row: cast(str, row["episode_id"])),
        "rejected_episodes": rejected_episodes,
        "population_dispositions": dispositions,
        "populations": populations,
        "excluded_population_memberships": excluded_population_memberships,
        "behavior_occurrences": occurrences,
        "excluded_behavior_occurrences": excluded_occurrences,
        "behavior_patterns": patterns,
        "semantic_audit": {
            "current_items": current_audits,
            "historical_items": historical_audits,
        },
        "accounting": {
            "predecessor_episode_count": len(predecessor_episodes),
            "corrected_episode_count": len(episodes),
            "exact_unchanged_episode_count": len(exact_episode_ids),
            "replacement_episode_count": len(replacement_by_predecessor),
            "rejected_episode_count": len(rejected_episode_ids),
            "assigned_episode_count": len(population_by_episode),
            "unassigned_episode_count": len(episodes) - len(population_by_episode),
            "population_count": len(populations),
            "supported_population_count": len(supported_populations),
            "supported_population_support": sum(
                cast(int, row["support"]) for row in supported_populations
            ),
            "unpublished_candidate_population_count": len(candidate_populations),
            "unpublished_candidate_population_membership_count": sum(
                len(cast(list[str], row["episode_ids"]))
                for row in candidate_populations
            ),
            "behavior_occurrence_count": len(occurrences),
            "excluded_behavior_occurrence_count": len(excluded_occurrences),
            "pattern_count": len(patterns),
            "pattern_support": sum(cast(int, row["support"]) for row in patterns),
        },
        "population_membership_edge_conservation": population_edges,
        "pattern_occurrence_edge_conservation": pattern_edges,
        "budget": historical_budget,
        "gaps": sorted(gaps, key=lambda row: (row["code"], row["stage"])),
    }
    report["projection_id"] = _identity("behavior-map-historical-projection-v0", report)
    destination = Path(output_dir)
    if destination.exists():
        raise HistoricalProjectionError("HISTORICAL_PROJECTION_OUTPUT_EXISTS")
    destination.mkdir(parents=True, mode=0o700)
    _write_once(
        destination / "behavior_map_historical_projection.json",
        _canonical(report, newline=True),
    )
    return report


__all__ = ["HistoricalProjectionError", "project_grounded_behavior_map"]
