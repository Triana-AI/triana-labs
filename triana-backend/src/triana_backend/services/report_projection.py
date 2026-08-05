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
    if (
        rejection_summary is None
        or rejection_summary.authority != "DETERMINISTIC"
        or rejection_summary.value != {"SOURCE_EXECUTION_INCOMPLETE": rejected}
    ):
        raise ReportProjectionUnavailable(("rejection_summary",))
    if source.rejected_evidence and len(source.rejected_evidence) != rejected:
        raise ReportProjectionUnavailable(("rejected_evidence",))
    if physical != usable + rejected:
        raise ReportProjectionUnavailable(("rejected_evidence",))

    report: dict[str, Any] = {
        "artifact_kind": "labs_report",
        "schema_version": 1,
        "report_id": source.report_id,
        "title": "HRAI run_200 retained trace accounting",
        "evidence_class": source.evidence_class,
        "mode": "RETAINED_TRACE_ACCOUNTING",
        "privacy_class": "PRIVATE_OPERATOR_TUNNEL",
        "sample_class": "COMPLETE_RETAINED_CORPUS",
        "sample_disclosure": (
            "All 200 retained synthetic-corpus records were accounted for; "
            "no behavior grouping, simulation, outcome judgment, or ruling "
            "was performed."
        ),
        "created_at": source.created_at,
        "lineage": {
            "report_contract": "LABS07_08_REPORT_V1",
            # This identifies the compiler result used by the projection. The
            # immutable artifact content hash is verified against RDS on reads.
            "report_hash": source.compiler_result_hash,
            "source_sha256": source.source_sha256,
            "source_artifact_hashes": [
                {"artifact_kind": "SOURCE_TRACE_JSONL", "hash": source.source_sha256},
                {
                    "artifact_kind": "LABS_ANALYSIS_FACTS",
                    "hash": source.compiler_result_hash,
                },
            ],
            "compiler": {"name": "triana-labs-report", "version": "1"},
        },
        "setup": {
            "source": {
                "source_kind": "S3_RETAINED_JSONL",
                "display_name": "normalized_traces.jsonl",
                "authorization": "OWNER_AUTHORIZED_RETAINED_SYNTHETIC_CORPUS",
                "custody": "PRIVATE_S3_SSE_KMS",
            },
            "adapter": {
                "adapter_id": "hrai-normalized-trace-v2",
                "adapter_version": source.compiler_version,
                "mapping_status": "PARTIAL",
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
                "unassessed_semantics": [
                    "No semantic behavior groups, cases, simulations, or human "
                    "rulings were created by this accounting import."
                ],
            },
        },
        "behavior": {
            "derivation_kind": "NOT_PERFORMED",
            "membership_authority": "DETERMINISTIC",
            "semantic_summary_authority": "NOT_PERFORMED",
            "population_claim": "NOT_ESTABLISHED",
            "groups": [],
        },
        "cases": [],
        "conversations": [dict(item) for item in source.conversations],
        "reviews": [],
        "limitations": [
            {
                "limitation_id": "limit-accounting-only",
                "title": "Accounting-only import",
                "detail": (
                    "This run validates retained-source accounting and lineage only; "
                    "semantic analysis and simulation were not run."
                ),
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
                "headline": "Retained-source accounting completed",
                "detail": "No behavioral learning was performed.",
                "group_count": 0,
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


def _assert_json_round_trip(report: Mapping[str, Any]) -> None:
    if json.loads(canonical_report_bytes(report)) != report:
        raise ReportProjectionUnavailable(("json_serialization",))
