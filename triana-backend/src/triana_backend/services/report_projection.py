"""Direct projection of persisted Labs accounting facts into the UI contract."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


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
    created_at: str
    compiler_version: str
    compiler_result_hash: str
    rejected_evidence: Sequence[dict[str, Any]] = ()
    analysis_artifact_sha256: str | None = None


class ReportProjectionUnavailable(ValueError):
    def __init__(self, missing_fact_kinds: Iterable[str]) -> None:
        self.missing_fact_kinds = tuple(sorted(set(missing_fact_kinds)))
        super().__init__("required persisted Labs facts are unavailable")


_REQUIRED = (
    "physical_record_count",
    "source_status_counts",
    "usable_conversation_count",
)


def project_labs_report(source: ReportProjectionInput) -> dict[str, Any]:
    """Copy source accounting and express every unperformed semantic lane as a gap."""

    facts = {fact.fact_kind: fact for fact in source.facts}
    if len(facts) != len(source.facts):
        raise ReportProjectionUnavailable(("duplicate_fact_kind",))
    missing = [kind for kind in _REQUIRED if kind not in facts]
    if missing:
        raise ReportProjectionUnavailable(missing)
    invalid = [kind for kind in _REQUIRED if facts[kind].authority != "DETERMINISTIC"]
    if invalid:
        raise ReportProjectionUnavailable(invalid)

    physical = _count(facts["physical_record_count"].value, "physical_record_count")
    usable = _count(
        facts["usable_conversation_count"].value, "usable_conversation_count"
    )
    status_counts = facts["source_status_counts"].value
    if not isinstance(status_counts, dict) or not all(
        isinstance(key, str) and isinstance(value, int) and value >= 0
        for key, value in status_counts.items()
    ):
        raise ReportProjectionUnavailable(("source_status_counts",))
    rejected = _count(facts["rejected_record_count"].value, "rejected_record_count")
    rejection_summary = facts.get("rejection_summary")
    structural = source.compiler_version == "preview-trace-structural-v1"
    allowed_rejection_summaries = (
        ({},)
        if structural
        else (
            ({}, {"SOURCE_EXECUTION_INCOMPLETE": 0})
            if rejected == 0
            else ({"SOURCE_EXECUTION_INCOMPLETE": rejected},)
        )
    )
    if (
        rejection_summary is None
        or rejection_summary.authority != "DETERMINISTIC"
        or rejection_summary.value not in allowed_rejection_summaries
    ):
        raise ReportProjectionUnavailable(("rejection_summary",))
    if source.rejected_evidence and len(source.rejected_evidence) != rejected:
        raise ReportProjectionUnavailable(("rejected_evidence",))
    if physical != usable + rejected:
        raise ReportProjectionUnavailable(("rejected_evidence",))

    behavior_groups = _structural_groups(facts, physical) if structural else []
    sample_disclosure = (
        "All retained synthetic PreviewTrace records were accounted for and grouped "
        "only by ordered event and tool-name structure; no semantic population, "
        "accepted behavior, simulation, verdict, or ruling was established."
        if structural
        else "All 200 retained synthetic-corpus records were accounted for; no "
        "behavior grouping, simulation, outcome judgment, or ruling was performed."
    )
    unassessed_semantics = (
        "No semantic population or accepted-behavior claim was established."
        if structural
        else "No semantic behavior groups, cases, simulations, or human rulings "
        "were created by this accounting import."
    )
    limitation_detail = (
        "This run groups only observable event and tool-name structure; semantic "
        "population analysis and simulation were not run."
        if structural
        else "This run validates retained-source accounting and lineage only; "
        "semantic analysis and simulation were not run."
    )

    report: dict[str, Any] = {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": source.report_id,
        "title": (
            "TAU² retained trace structural analysis"
            if structural
            else "HRAI run_200 retained trace accounting"
        ),
        "evidence_class": source.evidence_class,
        "mode": "RETAINED_TRACE_ACCOUNTING",
        "privacy_class": "PRIVATE_OPERATOR_TUNNEL",
        "sample_class": "COMPLETE_RETAINED_CORPUS",
        "sample_disclosure": sample_disclosure,
        "created_at": source.created_at,
        "lineage": {
            "report_contract": "LABS07_08_REPORT_V1",
            "compiler_result_hash": source.compiler_result_hash,
            **(
                {"analysis_artifact_sha256": source.analysis_artifact_sha256}
                if source.analysis_artifact_sha256 is not None
                else {}
            ),
            "source_sha256": source.source_sha256,
            "source_artifact_hashes": [
                {"artifact_kind": "SOURCE_TRACE_JSONL", "hash": source.source_sha256},
                *(
                    [
                        {
                            "artifact_kind": "LABS_ANALYSIS_FACTS",
                            "hash": source.analysis_artifact_sha256,
                        }
                    ]
                    if source.analysis_artifact_sha256 is not None
                    else []
                ),
            ],
            "compiler": {"name": "triana-labs-report", "version": "1"},
        },
        "setup": {
            "source": {
                "source_kind": "S3_RETAINED_JSONL",
                "display_name": (
                    "tau2_preview_traces.jsonl"
                    if structural
                    else "normalized_traces.jsonl"
                ),
                "authorization": "OWNER_AUTHORIZED_RETAINED_SYNTHETIC_CORPUS",
                "custody": "PRIVATE_S3_SSE_KMS",
            },
            "adapter": {
                "adapter_id": (
                    "preview-trace-v1" if structural else "hrai-normalized-trace-v2"
                ),
                "adapter_version": source.compiler_version,
                "mapping_status": "UNDERSTOOD" if structural else "PARTIAL",
            },
            "understanding": {
                "physical_record_count": physical,
                "accepted_record_count": usable,
                "rejected_record_count": rejected,
                "usable_conversation_count": usable,
                "source_status_counts": dict(sorted(status_counts.items())),
                "rejection_reasons": (
                    [
                        {
                            "reason_code": "SOURCE_EXECUTION_INCOMPLETE",
                            "label": "Harness execution incomplete",
                            "count": rejected,
                        }
                    ]
                    if rejected
                    else []
                ),
                "unassessed_semantics": [unassessed_semantics],
            },
        },
        "behavior": {
            "derivation_kind": "STRUCTURAL_GROUPING" if structural else "NOT_PERFORMED",
            "membership_authority": "DETERMINISTIC",
            "semantic_summary_authority": "DETERMINISTIC"
            if structural
            else "NOT_PERFORMED",
            "population_claim": "NOT_ESTABLISHED",
            "groups": behavior_groups,
        },
        "cases": [],
        "conversations": [dict(item) for item in source.conversations],
        "reviews": [],
        "limitations": [
            {
                "limitation_id": (
                    "limit-semantic-population"
                    if structural
                    else "limit-accounting-only"
                ),
                "title": (
                    "Structural grouping only"
                    if structural
                    else "Accounting-only import"
                ),
                "detail": limitation_detail,
                "status": "KNOWN_GAP",
                "claim_blocked": (
                    "No behavior, outcome, regression, quality, or release "
                    "claim is established."
                ),
            }
        ],
        "run": {
            "run_id": source.run_id,
            "recorded_state": "COMPLETED_WITH_GAPS",
            "target": {
                "target_id": "not-evaluated",
                "label": "Target not evaluated",
                "connection_state": "UNKNOWN",
            },
            "simulator": {
                "provider_label": "No provider call",
                "model_label": "Not applicable",
                "identity_count": 0,
            },
            "limits": {
                "selected_case_count": 0,
                "max_turns_per_conversation": 0,
                "max_conversations": 0,
                "max_http_exchanges": 0,
                "max_minutes_per_conversation": 0,
                "reserved_cost_ceiling_usd": "0.00",
                "retry_policy": "NONE",
                "repair_policy": "NONE",
                "fallback_policy": "NONE",
            },
            "privacy_egress": {
                "provider": "NONE",
                "target": "NONE",
                "authorization": "NO_PROVIDER_CALL",
            },
            "conversation_order": [],
        },
        "results": {
            "learned": {
                "headline": (
                    "Structural trace grouping completed"
                    if structural
                    else "Retained-source accounting completed"
                ),
                "detail": (
                    "Groups describe observed event and tool-name structure only."
                    if structural
                    else "No behavioral learning was performed."
                ),
                "group_count": len(behavior_groups),
                "usable_conversation_count": usable,
            },
            "created": {
                "headline": "No cases were created",
                "detail": "Case derivation was outside this accounting run.",
                "selected_count": 0,
                "seen_count": 0,
                "variation_count": 0,
                "excluded_count": 0,
            },
            "happened": {
                "headline": "No simulation was run",
                "detail": "Retained source statuses are shown only in Setup.",
                "complete_count": 0,
                "partial_count": 0,
                "unavailable_count": 0,
                "running_count": 0,
                "queued_count": 0,
                "not_started_count": 0,
                "goal_met_count": 0,
                "goal_review_required_count": 0,
            },
            "judgment": {
                "headline": "No human judgment was recorded",
                "detail": "This accounting workflow creates no rulings.",
                "review_eligible_count": 0,
                "reviewed_count": 0,
            },
            "accounting": {
                "http_exchange_count": 0,
                "tool_call_count": 0,
                "actual_cost_usd": None,
                "privacy_gap_count": 0,
                "retry_count": 0,
                "repair_count": 0,
                "fallback_count": 0,
            },
        },
    }
    _assert_json_round_trip(report)
    return report


def canonical_report_bytes(report: Mapping[str, Any]) -> bytes:
    return json.dumps(
        report, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def report_content_hash(report: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_report_bytes(report)).hexdigest()


def _count(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ReportProjectionUnavailable((name,))
    return value


def _structural_groups(
    facts: Mapping[str, PersistedLabsFact], physical: int
) -> list[dict[str, Any]]:
    fact = facts.get("behavior_groups")
    if (
        fact is None
        or fact.authority != "DETERMINISTIC"
        or not isinstance(fact.value, list)
    ):
        raise ReportProjectionUnavailable(("behavior_groups",))
    groups: list[dict[str, Any]] = []
    for value in fact.value:
        if not isinstance(value, dict) or set(value) != {
            "group_id",
            "label",
            "summary",
            "support_count",
            "share_basis_points",
            "structural_pattern",
            "source_evidence_ids",
        }:
            raise ReportProjectionUnavailable(("behavior_groups",))
        support = _count(value["support_count"], "behavior_groups")
        share = _count(value["share_basis_points"], "behavior_groups")
        evidence_ids = value["source_evidence_ids"]
        if (
            not all(
                isinstance(value[key], str) and value[key]
                for key in ("group_id", "label", "summary", "structural_pattern")
            )
            or not isinstance(evidence_ids, list)
            or evidence_ids != sorted(evidence_ids)
            or not all(isinstance(item, str) and item for item in evidence_ids)
            or support != len(evidence_ids)
        ):
            raise ReportProjectionUnavailable(("behavior_groups",))
        groups.append(
            {
                **value,
                "support_count": support,
                "share_basis_points": share,
                "fidelity_label": "STRUCTURALLY_OBSERVED_DETERMINISTIC_DESCRIPTION",
            }
        )
    if (
        [group["group_id"] for group in groups]
        != sorted(group["group_id"] for group in groups)
        or sum(group["support_count"] for group in groups) != physical
        or sum(group["share_basis_points"] for group in groups) != 10_000
    ):
        raise ReportProjectionUnavailable(("behavior_groups",))
    return groups


def _assert_json_round_trip(report: Mapping[str, Any]) -> None:
    if json.loads(canonical_report_bytes(report)) != report:
        raise ReportProjectionUnavailable(("json_serialization",))
