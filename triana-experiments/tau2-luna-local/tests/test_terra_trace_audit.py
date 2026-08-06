from __future__ import annotations


def test_trace_audit_keeps_core_import_and_labs_analysis_as_separate_lanes() -> None:
    from tau2_luna_local.terra_smoke import audit_trace_suitability

    audit = audit_trace_suitability(
        records=[
            {"task_id": 83, "state": "COMPLETED", "bundle_valid": True},
            {"task_id": 113, "state": "PARTIAL", "bundle_valid": False},
            {"task_id": 5, "state": "INVALID", "bundle_valid": False},
            {"task_id": 52, "state": "SKIPPED", "bundle_valid": True},
        ],
        normalized_trace_required_fields=("trace_id", "messages", "tool_calls"),
        normalized_trace_observed_fields=("messages",),
    )

    assert audit["denominators"] == {
        "requested": 4,
        "completed": 1,
        "partial": 1,
        "invalid": 1,
        "skipped": 1,
    }
    assert audit["TRIANA_CORE_IMPORT"] == {
        "classification": "GAP",
        "adapter_authorized": False,
        "missing_required_fields": ["trace_id", "tool_calls"],
    }
    assert audit["TRIANA_LABS_ANALYSIS"]["classification"] == (
        "LABELED_THIRD_PARTY_SYNTHETIC_BENCHMARK_EVIDENCE"
    )
    assert audit["TRIANA_LABS_ANALYSIS"]["verifier_valid_completed_bundles"] == 1


def test_labs_audit_forbids_product_and_improvement_claims() -> None:
    from tau2_luna_local.terra_smoke import audit_trace_suitability

    audit = audit_trace_suitability(
        records=[{"task_id": 83, "state": "COMPLETED", "bundle_valid": True}],
        normalized_trace_required_fields=(),
        normalized_trace_observed_fields=(),
    )

    assert set(audit["TRIANA_LABS_ANALYSIS"]["prohibited_claims"]) == {
        "PRODUCTION_TRACE",
        "ACCEPTED_BEHAVIOR",
        "PRODUCT_PASSAGE",
        "REGRESSION_EVIDENCE",
        "SCORE_IMPROVEMENT",
    }
    assert audit["TRIANA_LABS_ANALYSIS"]["human_semantic_judgment_required"] is True
