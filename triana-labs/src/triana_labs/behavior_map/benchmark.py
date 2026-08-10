"""Private, content-free review contract for Behavior Map coverage repair."""

from __future__ import annotations

import hashlib
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


def _digest(domain: str, value: Any) -> str:
    return (
        "sha256:"
        + hashlib.sha256(domain.encode("ascii") + b"\0" + _canonical(value)).hexdigest()
    )


def _read_object(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise TypeError("BENCHMARK_SOURCE_INVALID")
    return cast(JsonObject, value)


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


def _stable_selection(values: list[str], limit: int, domain: str) -> list[str]:
    return sorted(values, key=lambda value: (_digest(domain, value), value))[:limit]


def build_repair_benchmark(
    report_path: str | Path,
    checkpoints_dir: str | Path,
    output_dir: str | Path,
) -> JsonObject:
    """Write an unlabeled, hash-addressed private review queue.

    Checkpoints are accepted only as an immutable source identity. Customer
    quotes and provider results are never copied into this artifact.
    """

    report_file = Path(report_path)
    checkpoint_root = Path(checkpoints_dir)
    destination = Path(output_dir)
    report = _read_object(report_file)
    if report.get("artifact_kind") != "behavior_map_report_v0":
        raise ValueError("BENCHMARK_SOURCE_INVALID")
    if not checkpoint_root.is_dir():
        raise ValueError("BENCHMARK_CHECKPOINTS_UNAVAILABLE")

    episodes = cast(list[JsonObject], report.get("episodes", []))
    populations = cast(list[JsonObject], report.get("populations", []))
    emerging = cast(list[JsonObject], report.get("emerging_unknown", []))
    assigned = {
        episode_id
        for population in populations
        for episode_id in cast(list[str], population.get("episode_ids", []))
    }
    no_surviving_ids = sorted(
        {
            cast(str, row["conversation_id"])
            for row in emerging
            if row.get("reason") == "NO_SURVIVING_EPISODE"
            and isinstance(row.get("conversation_id"), str)
        }
    )
    unassigned_ids = sorted(
        {
            cast(str, row["episode_id"])
            for row in emerging
            if row.get("reason") == "UNASSIGNED_DEMAND"
            and isinstance(row.get("episode_id"), str)
        }
    )
    episode_by_id = {
        cast(str, row["episode_id"]): row
        for row in episodes
        if isinstance(row.get("episode_id"), str)
    }
    no_surviving = [
        {
            "conversation_id": conversation_id,
            "human_review": {
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
            },
        }
        for conversation_id in no_surviving_ids
    ]
    unassigned = [
        {
            "episode_id": episode_id,
            "conversation_id": episode_by_id.get(episode_id, {}).get("conversation_id"),
            "human_review": {
                "label": None,
                "allowed_labels": [
                    "EXISTING_POPULATION",
                    "NEW_LEFTOVER_POPULATION",
                    "GENUINELY_UNIQUE",
                    "AMBIGUOUS_OR_INSUFFICIENT",
                ],
                "existing_population_id": None,
                "new_leftover_group_id": None,
            },
        }
        for episode_id in unassigned_ids
    ]

    by_conversation: dict[str, list[str]] = {}
    for row in episodes:
        if isinstance(row.get("conversation_id"), str) and isinstance(
            row.get("episode_id"), str
        ):
            by_conversation.setdefault(cast(str, row["conversation_id"]), []).append(
                cast(str, row["episode_id"])
            )
    pattern_ids = {
        cast(str, row["pattern_id"])
        for row in cast(list[JsonObject], report.get("behavior_patterns", []))
        if isinstance(row.get("pattern_id"), str)
    }
    population_ids = {
        cast(str, row["population_id"])
        for row in populations
        if isinstance(row.get("population_id"), str)
    }
    episode_ids = set(episode_by_id)

    def audit_scope(item_id: str) -> str:
        if item_id in pattern_ids:
            return "PATTERN"
        if item_id in population_ids:
            return "POPULATION"
        if item_id in episode_ids:
            return "EPISODE"
        return "EPISODE"

    audit_candidates = [
        {
            "item_id": cast(str, row["item_id"]),
            "subject_scope": audit_scope(cast(str, row["item_id"])),
            "scoring_target": None,
            "scoring_scope": None,
        }
        for row in cast(
            list[JsonObject],
            cast(JsonObject, report.get("semantic_audit", {})).get("items", []),
        )
        if row.get("decision") in {"UNSUPPORTED", "UNCERTAIN", "SPLIT", "MERGE"}
        and isinstance(row.get("item_id"), str)
    ]
    controls: JsonObject = {
        "control_kind": "UNLABELED_BASELINE_INTEGRITY_CANDIDATES",
        "assigned_episode_ids": _stable_selection(
            sorted(assigned), 20, "behavior-map-control-assigned-v0"
        ),
        "multi_goal_conversation_ids": _stable_selection(
            sorted(
                conversation_id
                for conversation_id, members in by_conversation.items()
                if len(members) > 1
            ),
            10,
            "behavior-map-control-multigoal-v0",
        ),
        "audit_candidate_items": sorted(
            audit_candidates,
            key=lambda row: (
                cast(str, row["subject_scope"]),
                cast(str, row["item_id"]),
            ),
        )[:5],
    }
    controls["selection_sha256"] = _digest(
        "behavior-map-repair-control-selection-v0", controls
    )
    checkpoint_tree = [
        {
            "relative_path": str(path.relative_to(checkpoint_root)),
            "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for path in sorted(checkpoint_root.rglob("*"))
        if path.is_file()
    ]
    benchmark: JsonObject = {
        "artifact_kind": "behavior_map_repair_benchmark_v0",
        "schema_version": 0,
        "source": {
            "report_id": report.get("report_id"),
            "source_sha256": cast(JsonObject, report.get("source", {})).get(
                "source_sha256"
            ),
            "report_file_sha256": "sha256:"
            + hashlib.sha256(report_file.read_bytes()).hexdigest(),
            "checkpoint_tree_sha256": _digest(
                "behavior-map-repair-checkpoint-tree-v0", checkpoint_tree
            ),
        },
        "failure_panel": {
            "no_surviving_conversations": no_surviving,
            "unassigned_episodes": unassigned,
        },
        "controls": controls,
        "semantic_benchmark": {
            metric: {"state": "HUMAN_LABELS_MISSING", "value": None}
            for metric in _METRICS
        },
    }
    benchmark["benchmark_id"] = _digest("behavior-map-repair-benchmark-v0", benchmark)
    destination.mkdir(parents=True, exist_ok=True)
    destination.chmod(0o700)
    _write_once(
        destination / "behavior-map-repair-benchmark.json",
        _canonical(benchmark, lf=True),
    )
    return benchmark


__all__ = ["build_repair_benchmark"]
