"""Aggregate deterministic corpus facts from already accounted trace records.

The Observer supplies accepted normalized traces, safe rejection records, and the
mechanical eligibility count. This module owns only the closed corpus profile and its
count maps; it performs no parsing, rendering, hashing, filesystem, or CLI behavior.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, cast

from triana_labs.contracts.traces import EVENT_KINDS, TERMINAL_STATES

JsonObject = dict[str, Any]


def build_profile(
    *,
    input_count: int,
    accepted: list[JsonObject],
    rejected: list[JsonObject],
    eligible_count: int,
) -> JsonObject:
    """Derive the closed profile solely from accounted accepted/rejected lists."""

    # Only accepted traces contribute behavioral counts; all rejected lines contribute
    # only their safe rejection code. Closed maps are seeded with zeroes, and every
    # dynamic map is sorted before rendering to remove input-dictionary/locale effects.
    event_counts = Counter({kind: 0 for kind in EVENT_KINDS})
    terminal_counts = Counter({state: 0 for state in TERMINAL_STATES})
    tool_counts: Counter[str] = Counter()
    for trace in accepted:
        for event in cast(list[JsonObject], trace["events"]):
            kind = cast(str, event["event_kind"])
            event_counts[kind] += 1
            if kind == "TOOL_CALL":
                tool_counts[cast(str, event["tool_name"])] += 1
            elif kind == "TERMINAL":
                terminal_counts[cast(str, event["terminal_state"])] += 1
    rejection_counts = Counter(cast(str, record["code"]) for record in rejected)
    return {
        "artifact_kind": "corpus_profile",
        "schema_version": 1,
        "input_count": input_count,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "case_generation_eligible_count": eligible_count,
        "event_kind_counts": dict(sorted(event_counts.items())),
        "tool_call_counts": dict(sorted(tool_counts.items())),
        "terminal_state_counts": dict(sorted(terminal_counts.items())),
        "rejection_code_counts": dict(sorted(rejection_counts.items())),
        "language_analysis": "NOT_EVALUATED",
        "distress_analysis": "NOT_EVALUATED",
    }
