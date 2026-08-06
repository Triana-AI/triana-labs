"""Offline report-projection acceptance for structural PreviewTrace analysis."""

# ruff: noqa: S101

from __future__ import annotations

import json
from typing import Any

from triana_backend.services.report_projection import (
    PersistedLabsFact,
    ReportProjectionInput,
    project_labs_report,
)


def _fact(kind: str, value: Any) -> PersistedLabsFact:
    return PersistedLabsFact(f"fact-{kind}", kind, value, "DETERMINISTIC", 1)


def _source(
    *, compiler_version: str, facts: tuple[PersistedLabsFact, ...]
) -> ReportProjectionInput:
    return ReportProjectionInput(
        report_id="rpt_tau57",
        run_id="run_tau57",
        evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS",
        source_sha256="a" * 64,
        facts=facts,
        conversations=(),
        gaps=(),
        created_at="2026-08-06T00:00:00Z",
        compiler_version=compiler_version,
        compiler_result_hash="b" * 64,
    )


def test_preview_trace_report_exposes_only_deterministic_structural_authority() -> None:
    groups = [
        {
            "group_id": "group_one",
            "label": "Observed structure 1",
            "summary": "User message, lookup_order tool exchange, assistant message.",
            "support_count": 57,
            "share_basis_points": 10_000,
            "structural_pattern": (
                "USER_MESSAGE > TOOL_CALL:lookup_order > TOOL_RESULT > "
                "ASSISTANT_MESSAGE"
            ),
            "source_evidence_ids": [f"trace-{index:02d}" for index in range(57)],
        }
    ]
    projected = project_labs_report(
        _source(
            compiler_version="preview-trace-structural-v1",
            facts=(
                _fact("physical_record_count", 57),
                _fact("accepted_record_count", 57),
                _fact("rejected_record_count", 0),
                _fact("usable_conversation_count", 57),
                _fact("source_status_counts", {"ACCEPTED": 57}),
                _fact("rejection_summary", {}),
                _fact("behavior_groups", groups),
            ),
        )
    )

    assert projected["setup"]["understanding"]["physical_record_count"] == 57
    assert projected["setup"]["understanding"]["accepted_record_count"] == 57
    assert projected["setup"]["understanding"]["rejected_record_count"] == 0
    assert projected["behavior"] == {
        "derivation_kind": "STRUCTURAL_GROUPING",
        "membership_authority": "DETERMINISTIC",
        "semantic_summary_authority": "DETERMINISTIC",
        "population_claim": "NOT_ESTABLISHED",
        "groups": [
            {
                **groups[0],
                "fidelity_label": "STRUCTURALLY_OBSERVED_DETERMINISTIC_DESCRIPTION",
            }
        ],
    }
    assert projected["results"]["learned"]["group_count"] == 1
    assert projected["cases"] == []
    assert projected["conversations"] == []
    assert projected["reviews"] == []
    assert projected["run"]["privacy_egress"]["provider"] == "NONE"
    report_text = json.dumps(projected, sort_keys=True)
    assert "MODEL_PROPOSED" not in report_text
    assert '"population_claim": "NOT_ESTABLISHED"' in report_text

    legacy = project_labs_report(
        _source(
            compiler_version="labs08-hrai-accounting-v1",
            facts=(
                _fact("physical_record_count", 1),
                _fact("usable_conversation_count", 1),
                _fact("source_status_counts", {"COMPLETED": 1}),
                _fact("rejected_record_count", 0),
                _fact("rejection_summary", {}),
            ),
        )
    )
    assert legacy["behavior"]["groups"] == []
    assert legacy["behavior"]["derivation_kind"] == "NOT_PERFORMED"
    assert legacy["behavior"]["semantic_summary_authority"] == "NOT_PERFORMED"
