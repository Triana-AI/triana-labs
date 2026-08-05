"""Deterministic event-derived signals for STATIC measurements the generic
state-schema inspector (``measurement_promotion.state_signal``) cannot see — it only
walks ``state_after_ref``/``state_before_ref``, never the raw event/tool-call sequence.

This module adds a second, equally deterministic surface: a small, closed set of pinned
formulas computed directly from ``bundle.events`` (no model call, no per-trace guessing),
plus a structural availability profile the proposer payload can read to decide whether an
enriched-only failure category (silent tool errors, malformed tool args, failed error
recovery, context explosion, response truncation) is groundable on this corpus or must
come back as a typed coverage gap.

A measurement that uses one of these formulas sets ``state_field`` to the fixed sentinel
``EVENT_SIGNAL_STATE_FIELD`` ("events") rather than a discovered state-schema path — there
is no real per-trace state path to name, the formula reads the whole event list itself.
"""

from __future__ import annotations

from collections import Counter
import json
from typing import Any

from agentagon.evals.trace_bundle import EventKind, NormalizedTraceBundle

EVENT_SIGNAL_STATE_FIELD = "events"

# A tool call repeated with identical name+arguments at least this many times in one
# trace, or a raw tool-call count above the excessive threshold, counts as looping.
AGENT_LOOPING_REPEAT_THRESHOLD = 2
AGENT_LOOPING_EXCESSIVE_TOOL_CALL_COUNT = 20


def _tool_call_signature(event: Any) -> str:
    data = event.data if isinstance(event.data, dict) else {}
    arguments = data.get("arguments")
    return f"{event.name}:{json.dumps(arguments, sort_keys=True, default=str)}"


def agent_looping_label(bundle: NormalizedTraceBundle) -> str:
    """TRUE if this trace repeats an identical (tool name + arguments) call, or racks up
    an excessive raw tool-call count; FALSE otherwise. Always contributes a value — every
    completed trace has a tool-call sequence, possibly empty, so there is nothing to abstain
    on here."""
    tool_events = [event for event in bundle.events if event.kind is EventKind.TOOL]
    if not tool_events:
        return "FALSE"
    counts = Counter(_tool_call_signature(event) for event in tool_events)
    repeated = any(count >= AGENT_LOOPING_REPEAT_THRESHOLD for count in counts.values())
    excessive = len(tool_events) > AGENT_LOOPING_EXCESSIVE_TOOL_CALL_COUNT
    return "TRUE" if (repeated or excessive) else "FALSE"


EVENT_SIGNAL_FORMULAS = {
    "AGENT_LOOPING_RATE": agent_looping_label,
}


def compute_event_signal_measurement(
    formula_ref: str, bundles: tuple[NormalizedTraceBundle, ...]
) -> dict[str, Any]:
    """Same result shape as ``state_signal.compute_state_measurement``'s CATEGORY branch,
    for a ``formula_ref`` this module computes directly from events rather than a
    discovered state field. Every bundle contributes a label — see ``agent_looping_label``."""
    formula = EVENT_SIGNAL_FORMULAS.get(formula_ref)
    if formula is None:
        raise ValueError(f"unknown event-signal formula_ref: {formula_ref!r}")
    counts: Counter[str] = Counter()
    evidence_ids: list[str] = []
    for bundle in bundles:
        counts[formula(bundle)] += 1
        evidence_ids.append(bundle.trace_id)
    distribution = dict(sorted((label.lower(), count) for label, count in counts.items()))
    n = sum(counts.values())
    return {
        "value_type": "CATEGORY",
        "numeric_summary": None,
        "distribution": distribution,
        "eligible": n,
        "evaluable": n,
        "evidence_ids": evidence_ids[:30],
    }


def _tool_status_or_result_available(bundle: NormalizedTraceBundle) -> bool:
    return any(
        isinstance(event.data, dict) and bool(event.data.get("result_available"))
        or (isinstance(event.data, dict) and any(key in event.data for key in ("status", "result", "error")))
        for event in bundle.events
        if event.kind is EventKind.TOOL
    )


def _per_turn_token_counts_available(bundle: NormalizedTraceBundle) -> bool:
    return any(
        isinstance(event.data, dict) and isinstance(event.data.get("tokens"), dict) and event.data["tokens"]
        for event in bundle.events
    )


def _truncation_flag_available(bundle: NormalizedTraceBundle) -> bool:
    return any(isinstance(event.data, dict) and "truncated" in event.data for event in bundle.events)


def event_availability_profile(bundles: tuple[NormalizedTraceBundle, ...]) -> dict[str, Any]:
    """Corpus-wide booleans naming exactly which enriched-only event-derived signal each
    of the five NEEDS-ENRICHED failure categories requires, so the proposer can ground a
    real measurement when the data is present and emit an honest, specifically-named
    coverage gap (never a guess) when it is not."""
    return {
        "tool_status_or_result_available": any(_tool_status_or_result_available(b) for b in bundles),
        "per_turn_token_counts_available": any(_per_turn_token_counts_available(b) for b in bundles),
        "truncation_flag_available": any(_truncation_flag_available(b) for b in bundles),
    }


__all__ = [
    "EVENT_SIGNAL_STATE_FIELD",
    "EVENT_SIGNAL_FORMULAS",
    "agent_looping_label",
    "compute_event_signal_measurement",
    "event_availability_profile",
]
