"""Plain, deterministic Markdown and HTML rendering for Behavior Map V0."""

from __future__ import annotations

import html
from typing import Any

JsonObject = dict[str, Any]

_SECTIONS = (
    "Corpus overview",
    "User Demand Map",
    "Agent Behavior Map",
    "Emerging and Unknown Behavior",
    "Questions for You",
    "Evidence",
)


def _text(value: Any) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _gap_explanation(code: str) -> str:
    known = {
        "SEMANTIC_AUDIT_UNAVAILABLE": "Independent semantic audit is unavailable; primary proposals remain unaudited.",
        "SEMANTIC_ANALYSIS_UNAVAILABLE": "Semantic analysis is unavailable; only deterministic observations can be shown.",
        "SEMANTIC_CONTEXT_CITATION_INVALID": "Inferred agent context lacked exact evidence and was withheld.",
        "SEMANTIC_REQUEST_TOO_LARGE": "Some evidence exceeded the bounded semantic request size.",
        "SEMANTIC_BUDGET_EXCEEDED": "The authorized semantic budget could not fund the complete configured run.",
        "SEMANTIC_CHECKPOINT_INVALID": "A semantic checkpoint failed its integrity check and was not reused.",
    }
    return known.get(
        code, "This typed limitation reduces the evidence available in this report."
    )


def _deterministic_tool_summary(
    rows: list[JsonObject],
) -> tuple[str | None, list[JsonObject]]:
    tool_rows = [
        row
        for row in rows
        if row.get("lane") == "DETERMINISTIC" and row.get("action") == "CALLED_TOOL"
    ]
    remaining = [row for row in rows if row not in tool_rows]
    if not tool_rows:
        return None, remaining
    counts: dict[str, int] = {}
    for row in tool_rows:
        name = _text(row.get("object", "tool"))
        counts[name] = counts.get(name, 0) + 1
    breakdown = ", ".join(f"{name} ({count})" for name, count in sorted(counts.items()))
    return f"CALLED_TOOL — {len(tool_rows)} tool calls: {breakdown}.", remaining


def _gap_counts(gaps: list[JsonObject]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for gap in gaps:
        code = _text(gap["code"])
        counts[code] = counts.get(code, 0) + 1
    return sorted(counts.items())


def _readable_value(value: Any) -> str:
    if isinstance(value, dict):
        return "; ".join(
            f"{_text(key)}: {_readable_value(item)}"
            for key, item in sorted(value.items())
        )
    if isinstance(value, list):
        return ", ".join(_readable_value(item) for item in value)
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "true" if value else "false"
    return _text(value)


def _markdown_escape(value: Any) -> str:
    escaped = (
        _text(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    escaped = escaped.replace("\\", "\\\\")
    for marker in ("`", "*", "_", "[", "]"):
        escaped = escaped.replace(marker, f"\\{marker}")
    return escaped


def _markdown_truncation(row: JsonObject) -> str:
    metadata = row.get("truncation")
    if not isinstance(metadata, dict):
        return ""
    return (
        f" Truncated field {_markdown_escape(metadata.get('field'))}: "
        f"{metadata.get('original_bytes')} original bytes; "
        f"{metadata.get('displayed_bytes')} displayed bytes; "
        f"max {metadata.get('max_bytes')} bytes; "
        f"string byte limit {metadata.get('string_byte_limit')}."
    )


def _html_truncation(row: JsonObject) -> str:
    metadata = row.get("truncation")
    if not isinstance(metadata, dict):
        return ""
    note = (
        f" Truncated field {_text(metadata.get('field'))}: "
        f"{metadata.get('original_bytes')} original bytes; "
        f"{metadata.get('displayed_bytes')} displayed bytes; "
        f"max {metadata.get('max_bytes')} bytes; "
        f"string byte limit {metadata.get('string_byte_limit')}."
    )
    return f" <small>{html.escape(note)}</small>"


def _markdown_excerpt(excerpt: list[JsonObject]) -> list[str]:
    lines: list[str] = []
    for row in excerpt:
        sequence = row["event_sequence"]
        kind = row["display_kind"]
        if kind == "USER_MESSAGE":
            lines.append(
                f"- **User message** · Event sequence {sequence}: {_markdown_escape(row.get('content', ''))}"
                + _markdown_truncation(row)
            )
        elif kind == "TOOL_CALL":
            lines.append(
                f"- **Tool call** · Event sequence {sequence}: {_markdown_escape(row.get('tool_name', 'tool'))}"
            )
            lines.append(
                f"- **Tool input** · Event sequence {sequence}: {_markdown_escape(_readable_value(row.get('tool_input')))}"
                + _markdown_truncation(row)
            )
            if row.get("tool_result_status"):
                lines.append(
                    f"- **Tool result** · Event sequence {sequence}: {_markdown_escape(row['tool_result_status'])}"
                )
        elif kind == "TOOL_RESULT":
            details = _readable_value(row.get("result"))
            state = _text(row.get("result_state", "UNKNOWN"))
            error = row.get("error_code")
            if error:
                details = f"{details}; error: {_text(error)}"
            lines.append(
                f"- **Tool result** · Event sequence {sequence} · {_markdown_escape(state)}: {_markdown_escape(details)}"
                + _markdown_truncation(row)
            )
        elif kind == "AGENT_RESPONSE":
            lines.append(
                f"- **Agent response** · Event sequence {sequence}: {_markdown_escape(row.get('content', ''))}"
                + _markdown_truncation(row)
            )
        elif kind == "NEXT_USER_MESSAGE":
            lines.append(
                f"- **Next user message** · Event sequence {sequence}: {_markdown_escape(row.get('content', ''))}"
                + _markdown_truncation(row)
            )
    return lines


def _html_excerpt(excerpt: list[JsonObject]) -> str:
    items: list[str] = []
    for row in excerpt:
        sequence = row["event_sequence"]
        kind = row["display_kind"]
        label = ""
        details = ""
        if kind == "USER_MESSAGE":
            label, details = "User message", _text(row.get("content", ""))
        elif kind == "TOOL_CALL":
            items.append(
                f"<li><strong>Tool call</strong> · Event sequence {sequence}: "
                f"{html.escape(_text(row.get('tool_name', 'tool')))}</li>"
            )
            label, details = "Tool input", _readable_value(row.get("tool_input"))
            if row.get("tool_result_status"):
                items.append(
                    f"<li><strong>Tool result</strong> · Event sequence {sequence}: "
                    f"{html.escape(_text(row['tool_result_status']))}</li>"
                )
        elif kind == "TOOL_RESULT":
            label = "Tool result"
            details = _readable_value(row.get("result"))
            if row.get("error_code"):
                details += f"; error: {_text(row['error_code'])}"
            details = f"{_text(row.get('result_state', 'UNKNOWN'))}: {details}"
        elif kind == "AGENT_RESPONSE":
            label, details = "Agent response", _text(row.get("content", ""))
        elif kind == "NEXT_USER_MESSAGE":
            label, details = "Next user message", _text(row.get("content", ""))
        if label:
            items.append(
                f"<li><strong>{label}</strong> · Event sequence {sequence}: "
                f"{html.escape(details)}{_html_truncation(row)}</li>"
            )
    return "<ol>" + "".join(items) + "</ol>"


def _markdown_raw_excerpt_values(excerpt: list[JsonObject]) -> list[str]:
    """Render lossless values as indented code, never as active Markdown/HTML."""

    values: list[str] = []
    for row in excerpt:
        if "content" in row:
            values.append(_text(row["content"]))
        if "tool_input" in row:
            values.append(_readable_value(row["tool_input"]))
        if "result" in row:
            values.append(_readable_value(row["result"]))
    return [f"    {value}" for value in values]


def render_markdown(report: JsonObject) -> str:
    lines = ["# Triana Behavior Map", ""]
    accounting = report["accounting"]
    context = report["agent_context"]
    episodes = {row["episode_id"]: row for row in report["episodes"]}
    surviving_conversations = len(
        {str(row["conversation_id"]) for row in report["episodes"]}
    )
    assigned_episodes = len(
        {
            str(episode_id)
            for row in report["populations"]
            for episode_id in row["episode_ids"]
        }
    )
    lines.extend(
        [
            f"## {_SECTIONS[0]}",
            "",
            f"- Accepted conversations: {accounting['accepted_conversation_count']}",
            f"- Rejected conversations: {accounting['rejected_conversation_count']}",
            f"- Agent context ({context['status']}): {_text(context['text'])}",
            f"- Grounded episode coverage: {surviving_conversations}/{accounting['semantic_conversation_count']}",
            f"- Population assignment coverage: {assigned_episodes}/{len(report['episodes'])}",
            f"- Typed gaps: {len(report['gaps'])}",
            "",
            "### Method and limitations",
            "",
            f"- Method: {_text(report['method']['method_version'])}",
            f"- Primary model: {_text(report['method'].get('primary_model_id'))}",
            f"- Audit model: {_text(report['method'].get('audit_model_id'))}",
            "- Semantic labels are proposals grounded in observed evidence; they are not correctness or policy rulings.",
            "- Independent audit checks sampled proposal support; it does not verify every member.",
            "",
            "#### Typed gaps",
            "",
            *[
                f"- `{code}` ({count}) — {_gap_explanation(code)}"
                for code, count in _gap_counts(report["gaps"])
            ],
            "",
            f"## {_SECTIONS[1]}",
            "",
            "| Population | Meaning | Episodes | Visibility | Supporting material |",
            "|---|---|---:|---|---|",
        ]
    )
    for row in report["populations"]:
        anchor = (
            row["representative_evidence_ids"][0]
            if row["representative_evidence_ids"]
            else ""
        )
        evidence = f"[View](#{anchor})" if anchor else "Unavailable"
        lines.append(
            f"| {_text(row['label'])} | {_text(row['definition'])} | {row['support']} | "
            f"{row['visibility']} | {evidence} |"
        )
    for row in report["populations"]:
        members = [episodes[item] for item in row["episode_ids"] if item in episodes]
        lines.extend(
            [
                "",
                f"### Representative demands — {_text(row['label'])}",
                "",
                *[f"- {_text(item['goal'])}" for item in members[:3]],
                "",
                "#### Variations",
                "",
                *[
                    f"- {_text(item['requested_action'])} · {_text(item['subject'])}"
                    + (
                        f" · {', '.join(map(_text, item['constraints']))}"
                        if item["constraints"]
                        else ""
                    )
                    for item in members
                ],
            ]
        )
    if not report["populations"]:
        lines.append(
            "| No supported semantic populations | — | 0 | UNKNOWN | Unavailable |"
        )
    lines.extend(
        [
            "",
            f"## {_SECTIONS[2]}",
            "",
            f"Pattern analysis status: `{_text(report['pattern_analysis']['status'])}`",
            "",
            "| Behavior | Meaning | Occurrences | Source | Supporting material |",
            "|---|---|---:|---|---|",
        ]
    )
    occurrences = {row["occurrence_id"]: row for row in report["behavior_occurrences"]}
    for row in report["behavior_patterns"]:
        members = [
            occurrences[item] for item in row["occurrence_ids"] if item in occurrences
        ]
        lanes = ", ".join(sorted({item["lane"] for item in members})) or "UNKNOWN"
        evidence_id = next(
            (item["evidence_ids"][0] for item in members if item["evidence_ids"]), ""
        )
        evidence = f"[View](#{evidence_id})" if evidence_id else "Unavailable"
        lines.append(
            f"| {_text(row['label'])} | {_text(row['definition'])} | {row['support']} | "
            f"{lanes} | {evidence} |"
        )
    if not report["behavior_patterns"]:
        status = _text(report["pattern_analysis"]["status"])
        if status == "NO_RECURRING_PATTERN_OBSERVED":
            lines.append(
                "| No supported recurring patterns | — | 0 | UNKNOWN | Unavailable |"
            )
        else:
            lines.append(f"| {status} | — | — | UNKNOWN | Unavailable |")
    lines.extend(["", "### Occurrences and attachments", ""])
    tool_summary, detailed_occurrences = _deterministic_tool_summary(
        report["behavior_occurrences"]
    )
    if tool_summary:
        lines.append(f"- **{tool_summary}** Deterministic evidence.")
    for row in detailed_occurrences:
        evidence_kind = (
            "Deterministic evidence"
            if row["lane"] == "DETERMINISTIC"
            else "Semantic evidence"
        )
        evidence_links = (
            ", ".join(f"[View](#{evidence_id})" for evidence_id in row["evidence_ids"])
            or "Unavailable"
        )
        lines.append(
            f"- `{_text(row['occurrence_id'])}` — **{_text(row['action'])} {_text(row['object'])}** — {_text(row['condition'])}; "
            f"conversation `{_text(row['conversation_id'])}`; attached episodes: "
            f"{len(row['episode_ids'])}; {evidence_kind}; evidence: {evidence_links}."
        )
    lines.extend(["", f"## {_SECTIONS[3]}", ""])
    if report["emerging_unknown"]:
        for row in report["emerging_unknown"]:
            lines.append(
                f"- `{row['reason']}` — episode `{row['episode_id']}`: {_text(row['description'])}"
            )
    else:
        lines.append("- None observed.")
    lines.extend(["", f"## {_SECTIONS[4]}", ""])
    for question in report["questions"]:
        lines.extend([f"- {question}", "  - Answer:", ""])
    lines.extend([f"## {_SECTIONS[5]}", ""])
    for row in report["evidence"]:
        lines.extend(
            [
                f'<a id="{row["evidence_id"]}"></a>',
                f"### {row['conversation_id']} · {row['kind']} · {row['ordinal']}",
                "",
            ]
        )
        excerpt = row.get("conversation_excerpt")
        if isinstance(excerpt, list) and excerpt:
            lines.extend(_markdown_excerpt(excerpt))
            lines.extend(
                [
                    "",
                    "<details><summary>Raw canonical event JSON</summary>",
                    "",
                    "    " + _text(row["text"]),
                    "",
                    "Raw bounded excerpt values:",
                    "",
                    *_markdown_raw_excerpt_values(excerpt),
                    "",
                    "</details>",
                    "",
                ]
            )
        else:
            lines.extend([f"> {_text(row['text'])}", ""])
    if not report["evidence"]:
        lines.append("No publishable semantic evidence is available.\n")
    return "\n".join(lines).rstrip() + "\n"


def render_html(report: JsonObject) -> str:
    accounting = report["accounting"]
    context = report["agent_context"]
    episodes = {row["episode_id"]: row for row in report["episodes"]}
    surviving_conversations = len(
        {str(row["conversation_id"]) for row in report["episodes"]}
    )
    assigned_episodes = len(
        {
            str(episode_id)
            for row in report["populations"]
            for episode_id in row["episode_ids"]
        }
    )
    parts = [
        '<!doctype html><html lang="en"><head><meta charset="utf-8">',
        "<title>Triana Behavior Map</title>",
        (
            "<style>body{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem}"
            "table{border-collapse:collapse;width:100%;margin-bottom:2rem}th,td{border:1px solid #bbb;"
            "padding:.55rem;text-align:left;vertical-align:top}code{font-family:ui-monospace}</style>"
        ),
        "</head><body><h1>Triana Behavior Map</h1>",
        f"<h2>{_SECTIONS[0]}</h2>",
        f"<p>Accepted conversations: {accounting['accepted_conversation_count']}<br>",
        f"Rejected conversations: {accounting['rejected_conversation_count']}<br>",
        (
            f"Agent context ({html.escape(_text(context['status']))}): "
            f"{html.escape(_text(context['text']))}</p>"
        ),
        f"<p>Grounded episode coverage: {surviving_conversations}/{accounting['semantic_conversation_count']}<br>",
        f"Population assignment coverage: {assigned_episodes}/{len(report['episodes'])}<br>",
        f"Typed gaps: {len(report['gaps'])}</p>",
        "<h3>Method and limitations</h3>",
        f"<p>Method: {html.escape(_text(report['method']['method_version']))}<br>",
        f"Primary model: {html.escape(_text(report['method'].get('primary_model_id')))}<br>",
        f"Audit model: {html.escape(_text(report['method'].get('audit_model_id')))}<br>",
        "Semantic labels are evidence-grounded proposals, not correctness or policy rulings.<br>",
        "Independent audit checks sampled proposal support; it does not verify every member.</p>",
        "<h4>Typed gaps</h4><ul>",
        *[
            f"<li><code>{html.escape(code)}</code> ({count}) — "
            f"{html.escape(_gap_explanation(code))}</li>"
            for code, count in _gap_counts(report["gaps"])
        ],
        "</ul>",
        f"<h2>{_SECTIONS[1]}</h2>",
        (
            "<table><thead><tr><th>Population</th><th>Meaning</th><th>Episodes</th>"
            "<th>Visibility</th><th>Supporting material</th></tr></thead><tbody>"
        ),
    ]
    for row in report["populations"]:
        anchor = (
            row["representative_evidence_ids"][0]
            if row["representative_evidence_ids"]
            else ""
        )
        evidence = (
            f'<a href="#{html.escape(anchor)}">View</a>' if anchor else "Unavailable"
        )
        parts.append(
            "<tr>"
            f"<td>{html.escape(_text(row['label']))}</td>"
            f"<td>{html.escape(_text(row['definition']))}</td>"
            f"<td>{row['support']}</td><td>{html.escape(_text(row['visibility']))}</td>"
            f"<td>{evidence}</td></tr>"
        )
        members = [episodes[item] for item in row["episode_ids"] if item in episodes]
        representative = "".join(
            f"<li>{html.escape(_text(item['goal']))}</li>" for item in members[:3]
        )
        variations = "".join(
            f"<li>{html.escape(_text(item['requested_action']))} · "
            f"{html.escape(_text(item['subject']))} · "
            f"{html.escape(', '.join(map(_text, item['constraints'])) or 'No explicit constraint')}</li>"
            for item in members
        )
        parts.append(
            f'<tr><td colspan="5"><strong>Representative demands</strong><ul>{representative}</ul>'
            f"<strong>Variations</strong><ul>{variations}</ul></td></tr>"
        )
    if not report["populations"]:
        parts.append(
            "<tr><td>No supported semantic populations</td><td>—</td><td>0</td><td>UNKNOWN</td><td>Unavailable</td></tr>"
        )
    parts.extend(
        [
            "</tbody></table>",
            f"<h2>{_SECTIONS[2]}</h2>",
            (
                "<p>Pattern analysis status: <code>"
                f"{html.escape(_text(report['pattern_analysis']['status']))}"
                "</code></p>"
            ),
            (
                "<table><thead><tr><th>Behavior</th><th>Meaning</th><th>Occurrences</th>"
                "<th>Source</th><th>Supporting material</th></tr></thead><tbody>"
            ),
        ]
    )
    occurrences = {row["occurrence_id"]: row for row in report["behavior_occurrences"]}
    for row in report["behavior_patterns"]:
        members = [
            occurrences[item] for item in row["occurrence_ids"] if item in occurrences
        ]
        lanes = ", ".join(sorted({item["lane"] for item in members})) or "UNKNOWN"
        evidence_id = next(
            (item["evidence_ids"][0] for item in members if item["evidence_ids"]), ""
        )
        evidence = (
            f'<a href="#{html.escape(evidence_id)}">View</a>'
            if evidence_id
            else "Unavailable"
        )
        parts.append(
            "<tr>"
            f"<td>{html.escape(_text(row['label']))}</td>"
            f"<td>{html.escape(_text(row['definition']))}</td>"
            f"<td>{row['support']}</td><td>{html.escape(lanes)}</td><td>{evidence}</td></tr>"
        )
    if not report["behavior_patterns"]:
        status = _text(report["pattern_analysis"]["status"])
        if status == "NO_RECURRING_PATTERN_OBSERVED":
            parts.append(
                "<tr><td>No supported recurring patterns</td><td>—</td><td>0</td><td>UNKNOWN</td><td>Unavailable</td></tr>"
            )
        else:
            parts.append(
                f"<tr><td>{html.escape(status)}</td><td>—</td><td>—</td>"
                "<td>UNKNOWN</td><td>Unavailable</td></tr>"
            )
    parts.extend(["</tbody></table>", "<h3>Occurrences and attachments</h3><ul>"])
    tool_summary, detailed_occurrences = _deterministic_tool_summary(
        report["behavior_occurrences"]
    )
    if tool_summary:
        parts.append(
            f"<li><strong>{html.escape(tool_summary)}</strong> Deterministic evidence.</li>"
        )
    for row in detailed_occurrences:
        evidence_kind = (
            "Deterministic evidence"
            if row["lane"] == "DETERMINISTIC"
            else "Semantic evidence"
        )
        evidence_links = (
            ", ".join(
                f'<a href="#{html.escape(_text(evidence_id))}">View</a>'
                for evidence_id in row["evidence_ids"]
            )
            or "Unavailable"
        )
        parts.append(
            f"<li><code>{html.escape(_text(row['occurrence_id']))}</code> — "
            f"<strong>{html.escape(_text(row['action']))} {html.escape(_text(row['object']))}</strong> — "
            f"{html.escape(_text(row['condition']))}; conversation "
            f"<code>{html.escape(_text(row['conversation_id']))}</code>; attached episodes: "
            f"{len(row['episode_ids'])}; {evidence_kind}; evidence: {evidence_links}.</li>"
        )
    parts.append("</ul>")
    parts.extend([f"<h2>{_SECTIONS[3]}</h2><ul>"])
    if report["emerging_unknown"]:
        for row in report["emerging_unknown"]:
            parts.append(
                f"<li><code>{html.escape(_text(row['reason']))}</code> — episode "
                f"<code>{html.escape(_text(row['episode_id']))}</code>: "
                f"{html.escape(_text(row['description']))}</li>"
            )
    else:
        parts.append("<li>None observed.</li>")
    parts.extend(["</ul>", f"<h2>{_SECTIONS[4]}</h2><ul>"])
    for question in report["questions"]:
        parts.append(f"<li>{html.escape(question)}<p>Answer:</p></li>")
    parts.extend(["</ul>", f"<h2>{_SECTIONS[5]}</h2>"])
    for row in report["evidence"]:
        excerpt = row.get("conversation_excerpt")
        body = (
            _html_excerpt(excerpt)
            + "<details><summary>Raw canonical event JSON</summary><code>"
            + html.escape(_text(row["text"]))
            + "</code></details>"
            if isinstance(excerpt, list) and excerpt
            else f"<blockquote>{html.escape(_text(row['text']))}</blockquote>"
        )
        parts.append(
            f'<article id="{html.escape(row["evidence_id"])}"><h3>'
            f"{html.escape(_text(row['conversation_id']))} · {html.escape(_text(row['kind']))} · "
            f"{row['ordinal']}</h3>{body}</article>"
        )
    if not report["evidence"]:
        parts.append("<p>No publishable semantic evidence is available.</p>")
    parts.append("</body></html>\n")
    return "".join(parts)
