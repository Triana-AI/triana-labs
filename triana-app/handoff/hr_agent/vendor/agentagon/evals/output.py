"""Write portable Diff V0 artifacts without assigning a release verdict."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import json
from pathlib import Path
from typing import Any, Literal

from agentagon.evals.models import (
    DiffRow,
    MeasurementDefinition,
    ReleaseDiff,
    ReleaseRun,
)


EvidenceClass = Literal["REAL_CONTROLLED", "PREVIEW_SYNTHETIC"]


def to_primitive(value: Any) -> Any:
    """Convert frozen contracts into stable JSON-compatible structures."""
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): to_primitive(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_primitive(item) for item in value]
    return value


def render_markdown(
    run: ReleaseRun,
    release_diff: ReleaseDiff,
    measurements: tuple[MeasurementDefinition, ...],
    *,
    evidence_class: EvidenceClass,
) -> str:
    definitions = {item.measurement_id: item for item in measurements}
    lines = [
        "# Release Diff",
        "",
        f"**Evidence:** `{evidence_class}`  ",
        f"**Run:** `{run.run_id}`  ",
        f"**Baseline:** `{run.baseline.version_id}`  ",
        f"**Candidate:** `{run.candidate.version_id}`  ",
        f"**Case set:** `{run.case_set_version}`  ",
        f"**Trace adapters:** `{', '.join(run.trace_adapter_versions) or 'NOT_PINNED'}`  ",
        f"**Evaluators:** `{', '.join(run.evaluator_versions)}`  ",
        f"**Verdict:** `{release_diff.release_verdict}`",
        "",
        "This report describes retained paired evidence. It does not decide whether the release is safe.",
        "",
        "## Measurements",
        "",
        "| Measurement | Authority | Baseline | Candidate | Delta | Status | Cases | Pairs | CI | MDE |",
        "|---|---|---:|---:|---:|---|---:|---:|---|---:|",
    ]
    for row in release_diff.rows:
        definition = definitions[row.measurement_id]
        authority = definition.maturity.value
        if definition.expectation_id:
            authority = f"{authority} / {definition.expectation_id}"
        lines.append(
            "| "
            + " | ".join(
                (
                    _cell(definition.name),
                    _cell(authority),
                    _cell(row.baseline_value),
                    _cell(row.candidate_value),
                    _cell(row.delta),
                    row.status.value,
                    str(row.independent_case_count),
                    f"{row.evaluable_pairs}/{row.total_pairs}",
                    _cell(row.interval),
                    _cell(row.minimum_detectable_effect),
                )
            )
            + " |"
        )

    lines.extend(["", "## Execution gaps", ""])
    if not release_diff.execution_gaps:
        lines.append("None recorded.")
    else:
        lines.append("| Kind | Side | Case | Trial | Reason |")
        lines.append("|---|---|---|---|---|")
        for gap in release_diff.execution_gaps:
            lines.append(
                f"| {gap.kind.value} | {_cell(gap.side)} | {_cell(gap.case_id)} | "
                f"{_cell(gap.trial_id)} | {_cell(gap.reason)} |"
            )

    lines.extend(["", "## Evidence boundaries", ""])
    for row in release_diff.rows:
        lines.append(_evidence_line(row, definitions[row.measurement_id]))
    lines.append("")
    return "\n".join(lines)


def build_memory_event(
    run: ReleaseRun,
    release_diff: ReleaseDiff,
    *,
    evidence_class: EvidenceClass,
) -> dict[str, Any]:
    write_status = (
        "READY_FOR_APPEND_ONLY_MEMORY"
        if evidence_class == "REAL_CONTROLLED"
        else "PREVIEW_ONLY_DO_NOT_APPEND"
    )
    return {
        "schema_version": "diff-memory-v0",
        "write_status": write_status,
        "evidence_class": evidence_class,
        "release_run_id": run.run_id,
        "release_diff_id": release_diff.diff_id,
        "baseline_version_id": run.baseline.version_id,
        "candidate_version_id": run.candidate.version_id,
        "material_change": to_primitive(run.material_change),
        "measurement_results": [
            {
                "measurement_id": row.measurement_id,
                "measurement_version": row.measurement_version,
                "comparison_status": row.status.value,
                "independent_case_count": row.independent_case_count,
                "evaluable_pairs": row.evaluable_pairs,
                "invalid_pairs": row.invalid_pairs,
                "affected_case_ids": list(row.affected_case_ids),
            }
            for row in release_diff.rows
        ],
        "execution_gaps": to_primitive(release_diff.execution_gaps),
        "release_verdict": release_diff.release_verdict,
    }


def write_release_artifacts(
    output_dir: Path,
    run: ReleaseRun,
    release_diff: ReleaseDiff,
    measurements: tuple[MeasurementDefinition, ...],
    *,
    evidence_class: EvidenceClass,
) -> tuple[Path, ...]:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "run.json": to_primitive(run),
        "diff.json": to_primitive(release_diff),
        "memory_event.json": build_memory_event(
            run, release_diff, evidence_class=evidence_class
        ),
    }
    paths: list[Path] = []
    for name, payload in artifacts.items():
        path = output_dir / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        paths.append(path)
    summary_path = output_dir / "summary.md"
    summary_path.write_text(
        render_markdown(run, release_diff, measurements, evidence_class=evidence_class)
    )
    paths.append(summary_path)
    return tuple(paths)


def _cell(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, tuple) and len(value) == 2:
        return f"[{value[0]:.4f}, {value[1]:.4f}]"
    if isinstance(value, dict):
        return ", ".join(f"{key}: {item:.1%}" for key, item in value.items())
    if isinstance(value, Enum):
        return value.value
    return str(value).replace("|", "\\|").replace("\n", " ")


def _evidence_line(row: DiffRow, definition: MeasurementDefinition) -> str:
    authority = (
        f"authoritative Expectation `{definition.expectation_id}`"
        if definition.expectation_id
        else f"{definition.maturity.value.lower()} measurement; no correctness authority"
    )
    return (
        f"- **{definition.name}:** {authority}; {len(row.evidence)} evidence references, "
        f"{row.abstained_pairs} abstained and {row.invalid_pairs} invalid pairs."
    )


__all__ = [
    "EvidenceClass",
    "build_memory_event",
    "render_markdown",
    "to_primitive",
    "write_release_artifacts",
]
