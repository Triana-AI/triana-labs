"""Acceptance tests for deterministic byte-bounded semantic facet batches."""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from triana_labs.trace_to_eval.semantic import run_staged_analysis


def _trace(trace_id: str, user_content: str = "synthetic request") -> dict[str, Any]:
    return {
        "trace_id": trace_id,
        "events": [
            {"event_kind": "USER_MESSAGE", "content": user_content},
            {
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "synthetic response",
            },
        ],
    }


def _canonical_request_bytes(stage: str, payload: dict[str, Any]) -> int:
    return len(
        json.dumps(
            {"stage": stage, **payload},
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )


class _RecordingSemanticModel:
    model_id = "synthetic-semantic-model"

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: dict[str, Any],
        schema: type[Any],
    ) -> dict[str, Any]:
        del system, schema
        self.calls.append((stage, deepcopy(payload)))
        if stage.startswith("facets-"):
            return {
                "facets": [
                    {
                        "trace_id": row["trace_id"],
                        "demand_summary": "Synthetic demand",
                        "goal_label": "shared-goal",
                        "handling_mode": "INFORMATION_RETURNED",
                        "claimed_action": "FALSE",
                        "terminal_summary": "Synthetic response",
                        "evidence_quotes": [row["transcript"].splitlines()[0]],
                    }
                    for row in payload["traces"]
                ]
            }
        return {
            "populations": [
                {
                    "label": "Shared goal",
                    "description": "Synthetic shared demand.",
                    "kind": "PROPOSED_GOAL",
                    "member_labels": [row["label"] for row in payload["labels"]],
                }
            ]
        }

    def lineage(self) -> dict[str, Any]:
        return {}


def _facet_calls(
    model: _RecordingSemanticModel,
) -> list[tuple[str, dict[str, Any]]]:
    return [call for call in model.calls if call[0].startswith("facets-")]


def test_facet_batches_preserve_order_once_under_record_and_byte_limits() -> None:
    traces = [_trace(f"trace-{index:02d}", "x" * 8_500) for index in range(13)]
    model = _RecordingSemanticModel()

    run_staged_analysis(model, traces)

    calls = _facet_calls(model)
    assert len(calls) >= 2
    assert len(calls[0][1]["traces"]) < 12, "byte ceiling must bind before count"
    assert all(len(payload["traces"]) <= 12 for _, payload in calls)
    assert all(_canonical_request_bytes(stage, payload) <= 60_000 for stage, payload in calls)
    sent = [row for _, payload in calls for row in payload["traces"]]
    assert [row["trace_id"] for row in sent] == [trace["trace_id"] for trace in traces]
    assert len({row["trace_id"] for row in sent}) == len(traces)
    assert all(row["transcript"].endswith("synthetic response") for row in sent)


def test_tiny_traces_keep_existing_twelve_record_batching() -> None:
    traces = [_trace(f"trace-{index:02d}") for index in range(25)]
    model = _RecordingSemanticModel()

    result = run_staged_analysis(model, traces)

    calls = _facet_calls(model)
    assert [len(payload["traces"]) for _, payload in calls] == [12, 12, 1]
    assert [row["trace_id"] for _, payload in calls for row in payload["traces"]] == [
        trace["trace_id"] for trace in traces
    ]
    assert result["populations"] == [
        {
            "label": "Shared goal",
            "description": "Synthetic shared demand.",
            "evidence_trace_ids": [trace["trace_id"] for trace in traces],
        }
    ]


def test_single_oversized_unit_refuses_before_any_semantic_attempt() -> None:
    model = _RecordingSemanticModel()

    with pytest.raises(ValueError, match="^SEMANTIC_REQUEST_TOO_LARGE$"):
        run_staged_analysis(model, [_trace("trace-" + "z" * 60_000)])

    assert model.calls == []
