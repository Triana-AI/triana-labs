"""Acceptance contract for bounded hierarchical population consolidation."""

from __future__ import annotations

from typing import Any

from triana_labs.trace_to_eval.semantic import run_staged_analysis


class _ConsolidatingModel:
    model_id = "synthetic-bounded-consolidator"

    def __init__(self, *, omit_one_from_intermediate: bool = False) -> None:
        self.omit_one_from_intermediate = omit_one_from_intermediate
        self.consolidation_calls: list[tuple[str, list[str]]] = []
        self.omissions: list[tuple[str, int]] = []

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: dict[str, Any],
        schema: type[Any],
    ) -> dict[str, Any]:
        del system
        if stage.startswith("facets-"):
            proposed = {
                "facets": [
                    {
                        "trace_id": row["trace_id"],
                        "demand_summary": f"Demand for {row['trace_id']}",
                        "goal_label": f"goal-{row['trace_id']}",
                        "handling_mode": "INFORMATION_RETURNED",
                        "claimed_action": "FALSE",
                        "terminal_summary": "Information was returned.",
                        "evidence_quotes": [
                            f"USER_MESSAGE: Request for {row['trace_id']}"
                        ],
                    }
                    for row in payload["traces"]
                ]
            }
        else:
            labels = [row["label"] for row in payload["labels"]]
            self.consolidation_calls.append((stage, labels))
            members = labels
            if (
                self.omit_one_from_intermediate
                and stage != "population-consolidation-final"
                and len(labels) > 1
            ):
                members = labels[:-1]
                self.omissions.append((labels[-1], len(self.consolidation_calls) - 1))
            proposed = {
                "populations": [
                    {
                        "label": f"Consolidated {stage}",
                        "description": "A bounded synthetic population.",
                        "kind": "PROPOSED_GOAL",
                        "member_labels": members,
                    }
                ]
            }
        return schema.model_validate(proposed, strict=True).model_dump(mode="json")

    def lineage(self) -> dict[str, Any]:
        return {}


def _traces(count: int) -> list[dict[str, Any]]:
    return [
        {
            "trace_id": f"trace-{index:02d}",
            "events": [
                {
                    "event_kind": "USER_MESSAGE",
                    "content": f"Request for trace-{index:02d}",
                },
                {
                    "event_kind": "ASSISTANT_MESSAGE",
                    "content": "Synthetic information returned.",
                },
            ],
        }
        for index in range(count)
    ]


def _population_evidence(result: dict[str, Any]) -> list[str]:
    return [
        trace_id
        for population in result["populations"]
        for trace_id in population["evidence_trace_ids"]
    ]


def test_more_than_four_labels_use_bounded_hierarchy_and_preserve_membership() -> None:
    traces = _traces(9)
    model = _ConsolidatingModel(omit_one_from_intermediate=True)

    result = run_staged_analysis(model, traces)

    assert len(model.consolidation_calls) > 1
    assert all(len(labels) <= 4 for _, labels in model.consolidation_calls)
    assert any(
        stage.startswith("population-consolidation-0-")
        for stage, _ in model.consolidation_calls
    )
    assert model.consolidation_calls[-1][0] == "population-consolidation-final"
    assert model.omissions
    assert all(
        any(
            omitted_label in later_labels
            for _, later_labels in model.consolidation_calls[omitted_at + 1 :]
        )
        for omitted_label, omitted_at in model.omissions
    )
    expected_trace_ids = sorted(trace["trace_id"] for trace in traces)
    evidence = _population_evidence(result)
    assert sorted(evidence) == expected_trace_ids
    assert len(evidence) == len(set(evidence)) == 9
    assert result["semantic_gap_count"] == 0


def test_four_labels_retain_one_final_consolidation_call() -> None:
    traces = _traces(4)
    model = _ConsolidatingModel()

    result = run_staged_analysis(model, traces)

    assert model.consolidation_calls == [
        (
            "population-consolidation-final",
            [f"goal-trace-{index:02d}" for index in range(4)],
        )
    ]
    assert sorted(_population_evidence(result)) == sorted(
        trace["trace_id"] for trace in traces
    )
    assert result["semantic_gap_count"] == 0
