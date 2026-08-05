"""Deterministic projection from persisted Labs facts to API report fields.

This module deliberately performs no analysis. It copies named, persisted
facts and preserves typed gaps. Missing required facts refuse publication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class PersistedLabsFact:
    fact_id: str
    fact_kind: str
    value: Any
    authority: str
    schema_version: int


@dataclass(frozen=True, slots=True)
class ReportProjectionInput:
    report_id: str
    run_id: str
    evidence_class: str
    source_sha256: str
    facts: Sequence[PersistedLabsFact]
    conversations: Sequence[Mapping[str, Any]]
    gaps: Sequence[Mapping[str, Any]]


class ReportProjectionUnavailable(ValueError):
    def __init__(self, missing_fact_kinds: Iterable[str]) -> None:
        self.missing_fact_kinds = tuple(sorted(set(missing_fact_kinds)))
        super().__init__("required persisted Labs facts are unavailable")


_REQUIRED_UNDERSTANDING_FACTS = (
    "physical_record_count",
    "source_status_counts",
    "usable_conversation_count",
)


def project_labs_report(source: ReportProjectionInput) -> dict[str, Any]:
    """Build the v1 report by copying stored Labs facts without new meaning."""

    facts: dict[str, PersistedLabsFact] = {}
    for fact in source.facts:
        if fact.fact_kind in facts:
            raise ReportProjectionUnavailable((fact.fact_kind,))
        facts[fact.fact_kind] = fact

    missing = [kind for kind in _REQUIRED_UNDERSTANDING_FACTS if kind not in facts]
    if missing:
        raise ReportProjectionUnavailable(missing)
    invalid_authority = [
        kind
        for kind in _REQUIRED_UNDERSTANDING_FACTS
        if facts[kind].authority != "DETERMINISTIC"
    ]
    if invalid_authority:
        raise ReportProjectionUnavailable(invalid_authority)

    understanding = {
        kind: facts[kind].value for kind in _REQUIRED_UNDERSTANDING_FACTS
    }
    actual_cost = facts.get("actual_cost_usd")
    return {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": source.report_id,
        "run_id": source.run_id,
        "evidence_class": source.evidence_class,
        "setup": {"understanding": understanding},
        "results": {
            "accounting": {
                "actual_cost_usd": None if actual_cost is None else actual_cost.value
            },
            "gaps": [dict(gap) for gap in source.gaps],
        },
        "conversations": [dict(conversation) for conversation in source.conversations],
        "lineage": {
            "source_sha256": source.source_sha256,
            "fact_ids": sorted(fact.fact_id for fact in source.facts),
        },
    }
