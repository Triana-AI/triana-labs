"""Deterministic structural grouping acceptance for PreviewTrace corpora."""

from __future__ import annotations

import json
from typing import Any

from triana_labs import report


def _trace(trace_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "contract_kind": "preview_trace",
        "schema_version": 1,
        "privacy_class": "SYNTHETIC",
        "trace_id": trace_id,
        "source_trace_id": f"tau2://synthetic/{trace_id}",
        "events": [dict(event, sequence=index) for index, event in enumerate(events)],
    }


def _jsonl(records: list[dict[str, Any]]) -> bytes:
    return b"".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        for record in records
    )


def test_preview_trace_compiler_groups_only_ordered_event_and_tool_structure() -> None:
    hrai = report.compile_hrai_normalized_trace_v2(
        b'{"case_id":"legacy","schema_version":"normalized-trace-v2",'
        b'"status":"COMPLETED","turns":[{"role":"user"}]}\n',
        evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS",
    )
    assert {fact.fact_kind: fact.value for fact in hrai.facts} == {
        "physical_record_count": 1,
        "source_status_counts": {"COMPLETED": 1},
        "usable_conversation_count": 1,
    }

    records = [
        _trace(
            "trace-c",
            [
                {"event_kind": "USER_MESSAGE", "content": "PRIVATE_C"},
                {
                    "event_kind": "TOOL_CALL",
                    "call_id": "call-c",
                    "tool_name": "lookup_order",
                    "arguments": {"private": "SECRET_C"},
                },
                {
                    "event_kind": "TOOL_RESULT",
                    "call_id": "call-c",
                    "result_state": "SUCCEEDED",
                    "result": {"private": "RESULT_C"},
                },
                {
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "PRIVATE_REPLY_C",
                    "is_final": True,
                },
            ],
        ),
        _trace(
            "trace-b",
            [
                {"event_kind": "USER_MESSAGE", "content": "PRIVATE_B"},
                {
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "PRIVATE_REPLY_B",
                    "is_final": True,
                },
            ],
        ),
        _trace(
            "trace-a",
            [
                {"event_kind": "USER_MESSAGE", "content": "PRIVATE_A"},
                {
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "PRIVATE_REPLY_A",
                    "is_final": True,
                },
            ],
        ),
    ]
    source = _jsonl(records)
    compile_preview = report.compile_preview_trace_v1
    first = compile_preview(source, evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS")
    second = compile_preview(source, evidence_class="SYNTHETIC_EXISTING_TRACE_CORPUS")
    assert first.to_mapping() == second.to_mapping()

    facts = {fact.fact_kind: fact.value for fact in first.facts}
    assert facts["physical_record_count"] == 3
    assert facts["accepted_record_count"] == 3
    assert facts["rejected_record_count"] == 0
    assert facts["usable_conversation_count"] == 3
    groups = facts["behavior_groups"]
    assert isinstance(groups, list) and len(groups) == 2
    assert [group["group_id"] for group in groups] == sorted(
        group["group_id"] for group in groups
    )
    assert sorted(group["support_count"] for group in groups) == [1, 2]
    assert sum(group["support_count"] for group in groups) == 3
    assert sum(group["share_basis_points"] for group in groups) == 10_000
    for group in groups:
        assert group["source_evidence_ids"] == sorted(group["source_evidence_ids"])
        assert group["share_basis_points"] in {
            round(group["support_count"] * 10_000 / 3),
            10_000 - round((3 - group["support_count"]) * 10_000 / 3),
        }
        assert set(group) == {
            "group_id",
            "label",
            "summary",
            "support_count",
            "share_basis_points",
            "structural_pattern",
            "source_evidence_ids",
        }
    rendered_groups = json.dumps(groups, sort_keys=True)
    for private_value in (
        "PRIVATE_A",
        "PRIVATE_B",
        "PRIVATE_C",
        "PRIVATE_REPLY_A",
        "PRIVATE_REPLY_B",
        "PRIVATE_REPLY_C",
        "SECRET_C",
        "RESULT_C",
    ):
        assert private_value not in rendered_groups
