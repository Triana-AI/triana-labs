"""Acceptance contract for deterministic facet evidence-quote projection."""

from __future__ import annotations

from typing import Any

from triana_labs.trace_to_eval.semantic import _extract_facets, run_staged_analysis

_TRANSCRIPT = (
    "USER_MESSAGE: Alpha request\n"
    "ASSISTANT_MESSAGE: Beta response\n"
    "TOOL_CALL: lookup {}\n"
    "TOOL_RESULT: OK {}\n"
    "TERMINAL: COMPLETE"
)


class _QuoteProposingModel:
    model_id = "synthetic-quote-proposer"

    def __init__(self, quotes: list[str]) -> None:
        self.quotes = quotes
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
            proposed = {
                "facets": [
                    {
                        "trace_id": row["trace_id"],
                        "demand_summary": "Synthetic demand",
                        "goal_label": "synthetic-goal",
                        "handling_mode": "INFORMATION_RETURNED",
                        "claimed_action": "FALSE",
                        "terminal_summary": "Synthetic response",
                        "evidence_quotes": self.quotes,
                    }
                    for row in payload["traces"]
                ]
            }
        else:
            proposed = {
                "populations": [
                    {
                        "label": "Synthetic goal",
                        "description": "Synthetic demand population.",
                        "kind": "PROPOSED_GOAL",
                        "member_labels": [row["label"] for row in payload["labels"]],
                    }
                ]
            }
        return schema.model_validate(proposed, strict=True).model_dump(mode="json")

    def lineage(self) -> dict[str, Any]:
        return {}


def _trace() -> dict[str, Any]:
    return {
        "trace_id": "synthetic-trace",
        "events": [
            {"event_kind": "USER_MESSAGE", "content": "Alpha request"},
            {"event_kind": "ASSISTANT_MESSAGE", "content": "Beta response"},
            {
                "event_kind": "TOOL_CALL",
                "tool_name": "lookup",
                "arguments": {},
            },
            {
                "event_kind": "TOOL_RESULT",
                "result_state": "OK",
                "result": {},
            },
            {"event_kind": "TERMINAL", "terminal_state": "COMPLETE"},
        ],
    }


def test_provider_prompt_keeps_bound_but_schema_does_not_reject_overage() -> None:
    model = _QuoteProposingModel(["USER_MESSAGE: Alpha request"])

    run_staged_analysis(model, [_trace()])

    assert model.facet_system is not None
    instruction = " ".join(model.facet_system.lower().split())
    assert "one to three exact evidence quote substrings per facet" in instruction
    assert model.facet_schema is not None
    quote_schema = model.facet_schema["$defs"]["_Facet"]["properties"][
        "evidence_quotes"
    ]
    assert "maxItems" not in quote_schema


def test_overlong_proposal_projects_first_three_exact_quotes_in_stable_order() -> None:
    quotes = [
        "not present one",
        "USER_MESSAGE: Alpha request",
        "ASSISTANT_MESSAGE: Beta response",
        "not present two",
        "TOOL_CALL: lookup {}",
        "TOOL_RESULT: OK {}",
        "TERMINAL: COMPLETE",
    ]
    model = _QuoteProposingModel(quotes)
    units = [
        {
            "trace_id": "synthetic-trace",
            "transcript": _TRANSCRIPT,
            "tool_observed": True,
            "turn_count": 2,
        }
    ]

    facets, invalid = _extract_facets(model, units)

    assert invalid == 0
    assert facets[0]["evidence_quotes"] == [
        "USER_MESSAGE: Alpha request",
        "ASSISTANT_MESSAGE: Beta response",
        "TOOL_CALL: lookup {}",
    ]

    public_result = run_staged_analysis(_QuoteProposingModel(quotes), [_trace()])
    assert public_result["semantic_gap_count"] == 0
    assert public_result["populations"][0]["evidence_trace_ids"] == ["synthetic-trace"]


def test_no_exact_quote_is_excluded_as_a_semantic_gap() -> None:
    result = run_staged_analysis(
        _QuoteProposingModel(["not a transcript substring"]), [_trace()]
    )

    assert result == {
        "populations": [],
        "eval_candidates": [],
        "behavior_candidate_inventory": [],
        "semantic_gap_count": 1,
    }
