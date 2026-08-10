"""Acceptance contract for strict facet enums at the semantic boundary."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from triana_labs.trace_to_eval.semantic import run_staged_analysis

HANDLING_VALUES = {
    "INFORMATION_RETURNED",
    "INFORMATION_REQUESTED",
    "TOOL_ACTION_OBSERVED",
    "HANDOFF_OR_ESCALATION",
    "REFUSAL_OR_LIMIT",
    "STALLED_OR_REPEATED",
    "NO_CLEAR_HANDLING",
}
CLAIMED_ACTION_VALUES = {"TRUE", "FALSE", "UNKNOWN"}


class _FacetProposingModel:
    model_id = "synthetic-facet-enum-proposer"

    def __init__(self, *, handling_mode: str, claimed_action: str) -> None:
        self.handling_mode = handling_mode
        self.claimed_action = claimed_action
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
                        "demand_summary": "Obtain synthetic account information.",
                        "goal_label": "synthetic account inquiry",
                        "handling_mode": self.handling_mode,
                        "claimed_action": self.claimed_action,
                        "terminal_summary": "The agent returned account information.",
                        "evidence_quotes": ["USER_MESSAGE: Show account details."],
                    }
                    for row in payload["traces"]
                ]
            }
        else:
            proposed = {
                "populations": [
                    {
                        "label": "Synthetic account inquiry",
                        "description": "Users request synthetic account information.",
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
            {
                "event_kind": "USER_MESSAGE",
                "content": "Show account details.",
            },
            {
                "event_kind": "ASSISTANT_MESSAGE",
                "content": "Here are the synthetic account details.",
            },
        ],
    }


def test_requested_schema_and_prompt_exactly_name_deterministic_enum_values() -> None:
    model = _FacetProposingModel(
        handling_mode="INFORMATION_RETURNED", claimed_action="FALSE"
    )

    result = run_staged_analysis(model, [_trace()])

    assert model.facet_schema is not None
    properties = model.facet_schema["$defs"]["_Facet"]["properties"]
    handling_enum = properties["handling_mode"]["enum"]
    claimed_action_enum = properties["claimed_action"]["enum"]
    assert len(handling_enum) == 7 and set(handling_enum) == HANDLING_VALUES
    assert (
        len(claimed_action_enum) == 3
        and set(claimed_action_enum) == CLAIMED_ACTION_VALUES
    )
    assert model.facet_system is not None
    instruction = " ".join(model.facet_system.split())
    assert "handling_mode" in instruction and "claimed_action" in instruction
    assert all(
        value in instruction for value in HANDLING_VALUES | CLAIMED_ACTION_VALUES
    )
    assert result["semantic_gap_count"] == 0
    assert result["populations"][0]["evidence_trace_ids"] == ["synthetic-trace"]
    handling = next(
        row
        for row in result["behavior_candidate_inventory"]
        if row["signal"] == "HANDLING_MODE"
    )
    assert handling["distribution"] == {"INFORMATION_RETURNED": 1}


@pytest.mark.parametrize(
    ("handling_mode", "claimed_action"),
    [
        ("Returned some information", "FALSE"),
        ("INFORMATION_RETURNED", "No action was claimed"),
    ],
)
def test_free_form_enum_output_is_rejected_before_deterministic_projection(
    handling_mode: str, claimed_action: str
) -> None:
    model = _FacetProposingModel(
        handling_mode=handling_mode, claimed_action=claimed_action
    )

    with pytest.raises(ValidationError):
        run_staged_analysis(model, [_trace()])
