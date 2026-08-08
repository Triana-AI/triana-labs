"""Deterministic, claim-limited comparison of two Behavior Map reports."""

from __future__ import annotations

import hashlib
import html
import json
import os
import tempfile
from pathlib import Path
from typing import Any, cast

JsonObject = dict[str, Any]

_METRICS = (
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


def _canonical(value: Any, *, lf: bool = False) -> bytes:
    payload = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return payload + (b"\n" if lf else b"")


def _read_report(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if (
        not isinstance(value, dict)
        or value.get("artifact_kind") != "behavior_map_report_v0"
    ):
        raise ValueError("COMPARISON_REPORT_INVALID")
    return cast(JsonObject, value)


def _selection_hash_from_report_or_sidecar(
    report: JsonObject, report_path: Path
) -> str | None:
    source = report.get("source")
    if isinstance(source, dict):
        selected = source.get("selected_list_sha256")
        if isinstance(selected, str) and selected:
            return selected
    sidecar_path = report_path.parent.parent / "manifest.json"
    if not sidecar_path.is_file():
        return None
    try:
        sidecar = json.loads(sidecar_path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(sidecar, dict):
        return None
    scope = sidecar.get("semantic_scope")
    if not isinstance(scope, dict):
        return None
    selection = scope.get("selection")
    if isinstance(selection, dict):
        selected = selection.get("selected_list_sha256")
        if isinstance(selected, str) and selected:
            return selected
    allowed = scope.get("allowed_trace_ids")
    if not isinstance(allowed, list) or any(
        not isinstance(item, str) for item in allowed
    ):
        return None
    canonical_ids = sorted(set(cast(list[str], allowed)))
    return "sha256:" + hashlib.sha256(_canonical(canonical_ids)).hexdigest()


def _write_once(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(path)
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


def _movement(before: JsonObject, after: JsonObject, comparable: bool) -> JsonObject:
    before_accounting = cast(JsonObject, before["accounting"])
    after_accounting = cast(JsonObject, after["accounting"])
    values = {
        "surviving_episode_count": (
            int(before_accounting["surviving_episode_count"]),
            int(after_accounting["surviving_episode_count"]),
        ),
        "population_assigned_episode_count": (
            int(before_accounting["population_assigned_episode_count"]),
            int(after_accounting["population_assigned_episode_count"]),
        ),
        "supported_population_count": (
            len(cast(list[JsonObject], before.get("populations", []))),
            len(cast(list[JsonObject], after.get("populations", []))),
        ),
    }
    return {
        key: {
            "before": pair[0],
            "after": pair[1],
            "delta": pair[1] - pair[0] if comparable else None,
        }
        for key, pair in values.items()
    }


def _count_movement(before: float, after: float, comparable: bool) -> JsonObject:
    return {
        "before": before,
        "after": after,
        "delta": after - before if comparable else None,
    }


def _rows(report: JsonObject, key: str) -> list[JsonObject]:
    value = report.get(key, [])
    return cast(list[JsonObject], value) if isinstance(value, list) else []


def _histogram(rows: list[JsonObject], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, str):
            counts[value] = counts.get(value, 0) + 1
    return counts


def _histogram_movement(
    before: dict[str, int], after: dict[str, int], comparable: bool
) -> JsonObject:
    return {
        key: _count_movement(before.get(key, 0), after.get(key, 0), comparable)
        for key in sorted(set(before) | set(after))
    }


def _no_surviving_ids(report: JsonObject) -> set[str]:
    return {
        cast(str, row["conversation_id"])
        for row in _rows(report, "emerging_unknown")
        if row.get("reason") == "NO_SURVIVING_EPISODE"
        and isinstance(row.get("conversation_id"), str)
    }


def _identity_lineage(
    before: JsonObject,
    after: JsonObject,
    *,
    collection: str,
    identity_key: str,
    predecessor_key: str,
) -> JsonObject:
    before_ids = {
        cast(str, row[identity_key])
        for row in _rows(before, collection)
        if isinstance(row.get(identity_key), str)
    }
    after_rows = _rows(after, collection)
    after_ids = {
        cast(str, row[identity_key])
        for row in after_rows
        if isinstance(row.get(identity_key), str)
    }
    mappings: set[tuple[str, str]] = set()
    plural_key = predecessor_key.removesuffix("_id") + "_ids"
    for row in after_rows:
        after_id = row.get(identity_key)
        if not isinstance(after_id, str):
            continue
        predecessor_values: list[str] = []
        predecessor = row.get(predecessor_key)
        if isinstance(predecessor, str):
            predecessor_values.append(predecessor)
        predecessors = row.get(plural_key)
        if isinstance(predecessors, list):
            predecessor_values.extend(
                item for item in predecessors if isinstance(item, str)
            )
        mappings.update(
            (before_id, after_id)
            for before_id in predecessor_values
            if before_id in before_ids
        )
    preserved = before_ids & after_ids
    superseded_before = {before_id for before_id, _after_id in mappings}
    superseding_after = {after_id for _before_id, after_id in mappings}
    return {
        "preserved_count": len(preserved),
        "superseded_count": len(superseded_before),
        "predecessor_mappings": [
            {"before_id": before_id, "after_id": after_id}
            for before_id, after_id in sorted(mappings)
        ],
        "unmapped_before_count": len(before_ids - preserved - superseded_before),
        "new_unmapped_after_count": len(after_ids - preserved - superseding_after),
        "_preserved_ids": sorted(preserved),
        "_superseded_before_ids": sorted(superseded_before),
        "_unmapped_before_ids": sorted(before_ids - preserved - superseded_before),
    }


def _membership_edge_lineage(before: JsonObject, after: JsonObject) -> JsonObject:
    """Conserve baseline population membership without semantic matching."""

    before_populations = {
        cast(str, row["population_id"]): row
        for row in _rows(before, "populations")
        if isinstance(row.get("population_id"), str)
    }
    after_populations = {
        cast(str, row["population_id"]): row
        for row in _rows(after, "populations")
        if isinstance(row.get("population_id"), str)
    }
    before_edges = {
        (population_id, episode_id)
        for population_id, population in before_populations.items()
        for episode_id in cast(list[str], population.get("episode_ids", []))
        if isinstance(episode_id, str)
    }
    after_edges = {
        (population_id, episode_id)
        for population_id, population in after_populations.items()
        for episode_id in cast(list[str], population.get("episode_ids", []))
        if isinstance(episode_id, str)
    }

    def support(row: JsonObject) -> int:
        value = row.get("support")
        return (
            int(value)
            if isinstance(value, int) and not isinstance(value, bool)
            else len(set(cast(list[str], row.get("episode_ids", []))))
        )

    def predecessor_ids(row: JsonObject, singular_key: str) -> set[str]:
        values: set[str] = set()
        singular = row.get(singular_key)
        if isinstance(singular, str):
            values.add(singular)
        plural = row.get(singular_key.removesuffix("_id") + "_ids")
        if isinstance(plural, list):
            values.update(item for item in plural if isinstance(item, str))
        return values

    population_mappings: dict[str, set[str]] = {}
    for after_id, row in after_populations.items():
        for before_id in predecessor_ids(row, "predecessor_population_id"):
            if before_id in before_populations:
                population_mappings.setdefault(before_id, set()).add(after_id)

    before_episode_ids = _row_ids(before, "episodes", "episode_id")
    episode_mappings: dict[str, set[str]] = {}
    for row in _rows(after, "episodes"):
        after_episode_id = row.get("episode_id")
        if not isinstance(after_episode_id, str):
            continue
        for before_id in predecessor_ids(row, "predecessor_episode_id"):
            if before_id in before_episode_ids:
                episode_mappings.setdefault(before_id, set()).add(after_episode_id)

    preserved: list[JsonObject] = []
    superseded: list[JsonObject] = []
    unexplained: list[JsonObject] = []
    for before_population_id, before_episode_id in sorted(before_edges):
        before_support = support(before_populations[before_population_id])
        if (before_population_id, before_episode_id) in after_edges:
            preserved.append(
                {
                    "before_population_id": before_population_id,
                    "before_episode_id": before_episode_id,
                    "before_support": before_support,
                    "after_population_id": before_population_id,
                    "after_episode_id": before_episode_id,
                    "after_support": support(after_populations[before_population_id]),
                }
            )
            continue
        mapped_populations = sorted(
            population_mappings.get(before_population_id, set())
        )
        mapped_episodes = sorted(episode_mappings.get(before_episode_id, set()))
        mapped_edges = sorted(
            (population_id, episode_id)
            for population_id in mapped_populations
            for episode_id in mapped_episodes
            if (population_id, episode_id) in after_edges
        )
        if len(mapped_edges) == 1:
            after_population_id, after_episode_id = mapped_edges[0]
            superseded.append(
                {
                    "before_population_id": before_population_id,
                    "before_episode_id": before_episode_id,
                    "before_support": before_support,
                    "after_population_id": after_population_id,
                    "after_episode_id": after_episode_id,
                    "after_support": support(after_populations[after_population_id]),
                }
            )
            continue
        unexplained.append(
            {
                "before_population_id": before_population_id,
                "before_episode_id": before_episode_id,
                "before_support": before_support,
                "mapped_after_population_ids": mapped_populations,
                "mapped_after_episode_ids": mapped_episodes,
            }
        )
    return {
        "before_edge_count": len(before_edges),
        "after_edge_count": len(after_edges),
        "classified_before_edge_count": len(preserved)
        + len(superseded)
        + len(unexplained),
        "preserved_count": len(preserved),
        "explicitly_superseded_count": len(superseded),
        "unexplained_count": len(unexplained),
        "preserved_edges": preserved,
        "explicitly_superseded_edges": superseded,
        "unexplained_edges": unexplained,
    }


def _actual_cost(report: JsonObject) -> tuple[float | None, str]:
    budget = report.get("budget")
    if not isinstance(budget, dict):
        return None, "UNKNOWN"
    values = [
        budget.get("primary_actual_cost_usd"),
        budget.get("audit_actual_cost_usd"),
    ]
    if any(
        not isinstance(value, (int, float)) or isinstance(value, bool)
        for value in values
    ):
        return None, "UNKNOWN"
    return float(sum(cast(list[float], values))), "KNOWN"


def _id_movement(before_ids: set[str], after_ids: set[str]) -> JsonObject:
    return {
        "preserved_ids": sorted(before_ids & after_ids),
        "new_ids": sorted(after_ids - before_ids),
        "lost_ids": sorted(before_ids - after_ids),
    }


def _row_ids(report: JsonObject, collection: str, key: str) -> set[str]:
    return {
        cast(str, row[key])
        for row in _rows(report, collection)
        if isinstance(row.get(key), str)
    }


def _audit_item_ids(report: JsonObject) -> set[str]:
    semantic_audit = report.get("semantic_audit", {})
    return (
        _row_ids(cast(JsonObject, semantic_audit), "items", "item_id")
        if isinstance(semantic_audit, dict)
        else set()
    )


def _missing_audit_item_ids(report: JsonObject) -> set[str]:
    return {
        cast(str, row["item_id"])
        for row in _rows(report, "gaps")
        if row.get("code") == "SEMANTIC_AUDIT_MISSING"
        and isinstance(row.get("item_id"), str)
    }


def compare_behavior_maps(
    before_path: str | Path,
    after_path: str | Path,
    output_dir: str | Path,
) -> JsonObject:
    """Compare the same selection and label movement as mechanical evidence only."""

    before_file = Path(before_path)
    after_file = Path(after_path)
    before = _read_report(before_file)
    after = _read_report(after_file)
    before_source = cast(JsonObject, before["source"])
    after_source = cast(JsonObject, after["source"])
    before_accounting = cast(JsonObject, before["accounting"])
    after_accounting = cast(JsonObject, after["accounting"])
    gaps: list[JsonObject] = []
    if after.get("predecessor_report_id") != before.get("report_id"):
        gaps.append({"code": "COMPARISON_PREDECESSOR_LINEAGE_MISSING"})
    if before_source.get("source_sha256") != after_source.get("source_sha256"):
        gaps.append({"code": "COMPARISON_SOURCE_MISMATCH"})
    before_selection = _selection_hash_from_report_or_sidecar(before, before_file)
    after_selection = _selection_hash_from_report_or_sidecar(after, after_file)
    if before_selection is None or after_selection is None:
        gaps.append({"code": "COMPARISON_SELECTION_MISSING"})
    elif before_selection != after_selection:
        gaps.append({"code": "COMPARISON_SELECTION_MISMATCH"})
    sealed_keys = ("sealed_calibration_count", "sealed_holdout_count")
    if any(
        before_accounting.get(key) != after_accounting.get(key) for key in sealed_keys
    ):
        gaps.append({"code": "COMPARISON_SEALED_SPLIT_MISMATCH"})
    comparable = not gaps

    before_no_surviving = _no_surviving_ids(before)
    after_no_surviving = _no_surviving_ids(after)
    disposition_order = (
        "ASSIGNED",
        "INTENTIONALLY_UNASSIGNED",
        "AMBIGUOUS",
        "AUDIT_DISPUTED",
    )
    before_dispositions = _histogram(
        _rows(before, "population_dispositions"), "disposition"
    )
    after_dispositions = _histogram(
        _rows(after, "population_dispositions"), "disposition"
    )
    coverage_movement: JsonObject = {
        "no_surviving_conversations": {
            "before": len(before_no_surviving),
            "after": len(after_no_surviving),
            "recovered_ids": (
                sorted(before_no_surviving - after_no_surviving) if comparable else []
            ),
            "still_no_surviving_ids": (
                sorted(before_no_surviving & after_no_surviving) if comparable else []
            ),
            "new_ids": (
                sorted(after_no_surviving - before_no_surviving) if comparable else []
            ),
        },
        "episode_dispositions": {
            disposition: _count_movement(
                before_dispositions.get(disposition, 0),
                after_dispositions.get(disposition, 0),
                comparable,
            )
            for disposition in disposition_order
        },
        "grounding": {
            "excluded_citations": _count_movement(
                len(_rows(before, "excluded_episode_citations")),
                len(_rows(after, "excluded_episode_citations")),
                comparable,
            ),
            "rejected_grounding": _count_movement(
                sum(
                    row.get("code") == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
                    for row in _rows(before, "gaps")
                ),
                sum(
                    row.get("code") == "SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT"
                    for row in _rows(after, "gaps")
                ),
                comparable,
            ),
        },
    }
    object_keys = {
        "episodes": "episodes",
        "populations": "populations",
        "patterns": "behavior_patterns",
        "occurrences": "behavior_occurrences",
        "evidence": "evidence",
    }
    object_movement: JsonObject = {
        label: _count_movement(
            len(_rows(before, key)), len(_rows(after, key)), comparable
        )
        for label, key in object_keys.items()
    }
    before_audits = _histogram(
        _rows(cast(JsonObject, before.get("semantic_audit", {})), "items"),
        "decision",
    )
    after_audits = _histogram(
        _rows(cast(JsonObject, after.get("semantic_audit", {})), "items"),
        "decision",
    )
    before_gaps = _histogram(_rows(before, "gaps"), "code")
    after_gaps = _histogram(_rows(after, "gaps"), "code")
    audit_movement: JsonObject = {
        "decisions": _histogram_movement(before_audits, after_audits, comparable),
        "missing": _count_movement(
            before_gaps.get("SEMANTIC_AUDIT_MISSING", 0),
            after_gaps.get("SEMANTIC_AUDIT_MISSING", 0),
            comparable,
        ),
    }
    gap_movement = [
        {
            "code": code,
            **_count_movement(
                before_gaps.get(code, 0), after_gaps.get(code, 0), comparable
            ),
        }
        for code in sorted(set(before_gaps) | set(after_gaps))
    ]
    before_budget = cast(JsonObject, before.get("budget", {}))
    after_budget = cast(JsonObject, after.get("budget", {}))
    before_reservation = float(before_budget.get("total_reserved_usd", 0.0))
    after_reservation = float(after_budget.get("total_reserved_usd", 0.0))
    before_actual, before_actual_state = _actual_cost(before)
    after_actual, after_actual_state = _actual_cost(after)
    cost_movement: JsonObject = {
        "reservation_usd": _count_movement(
            before_reservation, after_reservation, comparable
        ),
        "actual_cost_usd": {
            "before": before_actual,
            "before_state": before_actual_state,
            "after": after_actual,
            "after_state": after_actual_state,
            "delta": (
                after_actual - before_actual
                if comparable and before_actual is not None and after_actual is not None
                else None
            ),
        },
    }
    identity_specs = {
        "episodes": ("episodes", "episode_id", "predecessor_episode_id"),
        "populations": (
            "populations",
            "population_id",
            "predecessor_population_id",
        ),
        "patterns": (
            "behavior_patterns",
            "pattern_id",
            "predecessor_pattern_id",
        ),
    }
    identity_internal = {
        label: _identity_lineage(
            before,
            after,
            collection=collection,
            identity_key=identity_key,
            predecessor_key=predecessor_key,
        )
        for label, (collection, identity_key, predecessor_key) in identity_specs.items()
    }
    before_disputed_ids = {
        cast(str, row["episode_id"])
        for row in _rows(before, "population_dispositions")
        if row.get("disposition") == "AUDIT_DISPUTED"
        and isinstance(row.get("episode_id"), str)
    }
    after_disputed_ids = {
        cast(str, row["episode_id"])
        for row in _rows(after, "population_dispositions")
        if row.get("disposition") == "AUDIT_DISPUTED"
        and isinstance(row.get("episode_id"), str)
    }
    id_level_movement: JsonObject = {
        "occurrences": _id_movement(
            _row_ids(before, "behavior_occurrences", "occurrence_id"),
            _row_ids(after, "behavior_occurrences", "occurrence_id"),
        ),
        "evidence": _id_movement(
            _row_ids(before, "evidence", "evidence_id"),
            _row_ids(after, "evidence", "evidence_id"),
        ),
        "audit_items": _id_movement(_audit_item_ids(before), _audit_item_ids(after)),
        "audit_disputed_episode_ids": _id_movement(
            before_disputed_ids, after_disputed_ids
        ),
        "missing_audit_item_ids": _id_movement(
            _missing_audit_item_ids(before), _missing_audit_item_ids(after)
        ),
    }
    claim_preserved: set[str] = set()
    claim_superseded: set[str] = set()
    claim_losses: set[str] = set()
    for label, lineage in identity_internal.items():
        excluded = before_disputed_ids if label == "episodes" else set()
        claim_preserved.update(set(lineage["_preserved_ids"]) - excluded)
        claim_superseded.update(set(lineage["_superseded_before_ids"]) - excluded)
        claim_losses.update(set(lineage["_unmapped_before_ids"]) - excluded)
    baseline_claims: JsonObject = {
        "preserved_count": len(claim_preserved),
        "superseded_count": len(claim_superseded),
        "unexplained_loss_count": len(claim_losses),
        "unexplained_loss_ids": sorted(claim_losses),
    }
    identity_lineage: JsonObject = {
        label: {key: value for key, value in lineage.items() if not key.startswith("_")}
        for label, lineage in identity_internal.items()
    }
    membership_edge_lineage = _membership_edge_lineage(before, after)
    improvement = comparable and (
        bool(before_no_surviving - after_no_surviving)
        or after_dispositions.get("ASSIGNED", 0)
        > before_dispositions.get("ASSIGNED", 0)
        or after_gaps.get("SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT", 0)
        < before_gaps.get("SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT", 0)
    )
    regression = comparable and (
        bool(after_no_surviving - before_no_surviving)
        or bool(claim_losses)
        or after_gaps.get("SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT", 0)
        > before_gaps.get("SEMANTIC_EPISODE_GROUNDING_INSUFFICIENT", 0)
        or after_gaps.get("SEMANTIC_AUDIT_MISSING", 0)
        > before_gaps.get("SEMANTIC_AUDIT_MISSING", 0)
    )
    deterministic_classification = (
        "NONCOMPARABLE"
        if not comparable
        else "MIXED"
        if improvement and regression
        else "IMPROVED"
        if improvement
        else "REGRESSED"
        if regression
        else "NO_CHANGE"
    )
    comparison: JsonObject = {
        "artifact_kind": "behavior_map_comparison_v0",
        "schema_version": 0,
        "before_report_id": before["report_id"],
        "after_report_id": after["report_id"],
        "lineage_state": "EXPLICIT_PREDECESSOR" if comparable else "NONCOMPARABLE",
        "mechanical_movement": _movement(before, after, comparable),
        "deterministic_classification": deterministic_classification,
        "coverage_movement": coverage_movement,
        "object_movement": object_movement,
        "audit_movement": audit_movement,
        "gap_movement": gap_movement,
        "cost_movement": cost_movement,
        "identity_lineage": identity_lineage,
        "membership_edge_lineage": membership_edge_lineage,
        "id_level_movement": id_level_movement,
        "baseline_claims": baseline_claims,
        "semantic_conclusion": "HUMAN_LABELS_MISSING",
        "semantic_benchmark": {
            metric: {"state": "HUMAN_LABELS_MISSING", "value": None}
            for metric in _METRICS
        },
        "gaps": sorted(gaps, key=lambda row: cast(str, row["code"])),
        "conclusion": "MECHANICAL_MOVEMENT_ONLY" if comparable else "NONCOMPARABLE",
    }
    comparison["comparison_id"] = (
        "sha256:"
        + hashlib.sha256(
            b"behavior-map-comparison-v0\0" + _canonical(comparison)
        ).hexdigest()
    )
    movement = cast(JsonObject, comparison["mechanical_movement"])
    markdown = "\n".join(
        [
            "# Behavior Map before/after comparison",
            "",
            f"Conclusion: **{comparison['conclusion']}**",
            "",
            "## Deterministic integrity and coverage",
            "",
            "| Measure | Before | After | Delta |",
            "|---|---:|---:|---:|",
            *[
                f"| {key} | {row['before']} | {row['after']} | {row['delta']} |"
                for key, row in movement.items()
            ],
            "",
            f"Classification: **{deterministic_classification}**",
            "",
            "## Identity and predecessor lineage",
            "",
            f"Baseline claims: `{json.dumps(baseline_claims, sort_keys=True)}`",
            "",
            f"ID-level movement: `{json.dumps(id_level_movement, sort_keys=True)}`",
            "",
            f"Population membership edges: `{json.dumps(membership_edge_lineage, sort_keys=True)}`",
            "",
            "## Gaps and audits",
            "",
            f"Gap movement: `{json.dumps(gap_movement, sort_keys=True)}`",
            "",
            "## Cost and reservation",
            "",
            f"Cost movement: `{json.dumps(cost_movement, sort_keys=True)}`",
            "",
            "## Semantic benchmark",
            "",
            "Semantic benchmark: HUMAN_LABELS_MISSING",
            "",
            "Mechanical movement is not evidence of semantic improvement.",
            "",
        ]
    )
    html_report = (
        '<!doctype html><html lang="en"><meta charset="utf-8">'
        "<title>Behavior Map comparison</title><body>"
        "<h1>Behavior Map before/after comparison</h1>"
        f"<p>Conclusion: <strong>{html.escape(cast(str, comparison['conclusion']))}</strong></p>"
        "<h2>Deterministic integrity and coverage</h2>"
        "<table><thead><tr><th>Measure</th><th>Before</th><th>After</th><th>Delta</th>"
        "</tr></thead><tbody>"
        + "".join(
            f"<tr><td>{html.escape(key)}</td><td>{row['before']}</td>"
            f"<td>{row['after']}</td><td>{row['delta']}</td></tr>"
            for key, row in movement.items()
        )
        + "</tbody></table>"
        f"<p>Classification: <strong>{html.escape(deterministic_classification)}</strong></p>"
        "<h2>Identity and predecessor lineage</h2>"
        f"<pre>{html.escape(json.dumps(baseline_claims, sort_keys=True))}</pre>"
        f"<pre>{html.escape(json.dumps(id_level_movement, sort_keys=True))}</pre>"
        f"<pre>{html.escape(json.dumps(membership_edge_lineage, sort_keys=True))}</pre>"
        "<h2>Gaps and audits</h2>"
        f"<pre>{html.escape(json.dumps(gap_movement, sort_keys=True))}</pre>"
        "<h2>Cost and reservation</h2>"
        f"<pre>{html.escape(json.dumps(cost_movement, sort_keys=True))}</pre>"
        "<h2>Semantic benchmark</h2>"
        "<p>Semantic benchmark: HUMAN_LABELS_MISSING</p>"
        "<p>Mechanical movement is not evidence of semantic improvement.</p>"
        "</body></html>\n"
    )
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    destination.chmod(0o700)
    _write_once(
        destination / "behavior-map-comparison.json", _canonical(comparison, lf=True)
    )
    _write_once(destination / "behavior-map-comparison.md", markdown.encode("utf-8"))
    _write_once(
        destination / "behavior-map-comparison.html", html_report.encode("utf-8")
    )
    return comparison


__all__ = ["compare_behavior_maps"]
