"""Pure artifact rendering for an already-accounted corpus profile."""

from __future__ import annotations

import json
from typing import Any

JsonObject = dict[str, Any]


def compact_json(value: Any) -> bytes:
    """Return portable compact JSON with exactly one terminal LF."""

    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def render_markdown(profile: JsonObject) -> bytes:
    """Project the machine profile without performing independent arithmetic."""

    lines = [
        "# Triana Labs Corpus Profile",
        "",
        "**Fidelity:** `SYNTHETIC`",
        "",
        "## Accounting",
        "",
        "| Measure | Count |",
        "| --- | ---: |",
        f"| Input lines | {profile['input_count']} |",
        f"| Accepted traces | {profile['accepted_count']} |",
        f"| Rejected traces | {profile['rejected_count']} |",
        (
            "| Case-generation eligible traces | "
            f"{profile['case_generation_eligible_count']} |"
        ),
        "",
        "## Event kinds",
        "",
        "| Event kind | Count |",
        "| --- | ---: |",
    ]
    lines.extend(
        f"| {name} | {count} |" for name, count in profile["event_kind_counts"].items()
    )
    lines.extend(["", "## Tool calls", ""])
    if profile["tool_call_counts"]:
        lines.extend(["| Tool name | Count |", "| --- | ---: |"])
        lines.extend(
            f"| {name} | {count} |"
            for name, count in profile["tool_call_counts"].items()
        )
    else:
        lines.append("None observed.")
    lines.extend(
        [
            "",
            "## Terminal states",
            "",
            "| Terminal state | Count |",
            "| --- | ---: |",
        ]
    )
    lines.extend(
        f"| {name} | {count} |"
        for name, count in profile["terminal_state_counts"].items()
    )
    lines.extend(["", "## Rejections", ""])
    if profile["rejection_code_counts"]:
        lines.extend(["| Rejection code | Count |", "| --- | ---: |"])
        lines.extend(
            f"| {name} | {count} |"
            for name, count in profile["rejection_code_counts"].items()
        )
    else:
        lines.append("None rejected.")
    lines.extend(
        [
            "",
            "## Explicitly not evaluated",
            "",
            "Language and distress analysis were not evaluated.",
            "Personas, intents, and cases were not evaluated.",
            "Agent execution and release comparison were not evaluated.",
            "",
            "## Portable artifacts",
            "",
            "- `manifest.json`",
            "- `normalized_traces.jsonl`",
            "- `rejected_traces.jsonl`",
            "- `corpus_profile.json`",
            "- `corpus_profile.md`",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")
