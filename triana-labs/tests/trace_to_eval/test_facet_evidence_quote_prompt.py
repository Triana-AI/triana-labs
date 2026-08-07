"""Acceptance contract for facet evidence-quote cardinality guidance."""

from __future__ import annotations

from typing import Any

from triana_labs.trace_to_eval.semantic import run_staged_analysis


class _PromptCapturingModel:
    model_id = "synthetic-prompt-capture"

    def __init__(self) -> None:
        self.facet_system: str | None = None
        self.facet_schema: dict[str, Any] | None = None

    def complete_json(
        self,
        *,
        stage: str,
        system: str,
        payload: dict[str, Any],
        schema: type[Any],
    ) -> dict[str, Any]:
        if stage.startswith("facets-"):
            self.facet_system = system
            self.facet_schema = schema.model_json_schema()
            return {
                "facets": [
                    {
                        "trace_id": row["trace_id"],
                        "demand_summary": "Synthetic demand",
                        "goal_label": "synthetic-goal",
                        "handling_mode": "INFORMATION_RETURNED",
                        "claimed_action": "FALSE",
                        "terminal_summary": "Synthetic response",
                        "evidence_quotes": ["USER_MESSAGE: Synthetic request"],
                    }
                    for row in payload["traces"]
                ]
            }
        return {
            "populations": [
                {
                    "label": "Synthetic goal",
                    "description": "Synthetic demand population.",
                    "kind": "PROPOSED_GOAL",
                    "member_labels": [row["label"] for row in payload["labels"]],
                }
            ]
        }

    def lineage(self) -> dict[str, Any]:
        return {}


def test_facet_prompt_plainly_matches_three_quote_schema_limit() -> None:
    model = _PromptCapturingModel()
    trace = {
        "trace_id": "synthetic-trace",
        "events": [
            {"event_kind": "USER_MESSAGE", "content": "Synthetic request"},
            {"event_kind": "ASSISTANT_MESSAGE", "content": "Synthetic response"},
        ],
    }

    run_staged_analysis(model, [trace])

    assert model.facet_schema is not None
    quote_schema = model.facet_schema["$defs"]["_Facet"]["properties"][
        "evidence_quotes"
    ]
    assert quote_schema["maxItems"] == 3

    assert model.facet_system is not None
    instruction = " ".join(model.facet_system.lower().split())
    assert "one to three exact evidence quote substrings per facet" in instruction
