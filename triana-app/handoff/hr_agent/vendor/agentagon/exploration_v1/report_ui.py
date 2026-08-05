"""Product-shaped HTML report for generic Exploration V1 artifacts."""

from __future__ import annotations

import html
import json
from typing import Any


COLORS = {
    "handoff_or_escalation": "#2b9a70",
    "information_returned": "#4d8abf",
    "information_requested": "#8f74bd",
    "tool_action_observed": "#d3a13c",
    "no_clear_handling": "#aeb8bf",
    "stalled_or_repeated": "#c65d55",
    "refusal_or_limit": "#b86d50",
    "true": "#2b9a70",
    "false": "#4d8abf",
}


def render_behavioral_analysis(result: dict[str, Any]) -> str:
    """Render current artifacts in the founder-demo behavioral-analysis shape."""
    analytics = result["behavior_analytics"]
    total = int(result["trace_count"])
    grounding = analytics["semantic_grounding"]
    grounded = total - int(grounding.get("NONE", 0))
    qualified = [
        row for row in result["candidate_measurements"]
        if row["qualification"] == "QUALIFIED"
    ]
    suggested_ids = {
        row["candidate_id"] for row in result["suggested_measurements"]
    }
    profile = result["agent_profile"]
    agent_name = str(profile.get("agent_name") or "Imported agent")
    adapter_version = str(result.get("trace_adapter", {}).get("version", ""))
    simulated = "simulated" in adapter_version.lower()
    baseline_label = "Simulated cold-start baseline" if simulated else "Cold-start behavioral baseline"
    source_callout = (
        '<div class="callout"><strong>Simulated corpus boundary.</strong>'
        "Counts describe this test distribution, not production prevalence. "
        "Tool calls are observed, but tool correctness and world-state correctness are not available from this export.</div>"
        if simulated
        else ""
    )
    evidence: dict[str, list[str]] = {}

    population_rows = []
    for row in analytics["top_populations"]:
        evidence[f"population:{row['population_id']}"] = row["evidence_ids"][:40]
        segments = _segments(row["handling_distribution"], row["support"])
        population_rows.append(f"""
        <article class="population-row">
          <div><strong>{_e(row['label'])}</strong><small>{_e(row['kind'])} · {_e(row['population_id'])}</small></div>
          <button class="number-link" data-evidence="population:{_e(row['population_id'])}">{row['support']}<small>{row['support'] / total:.1%}</small></button>
          <div>{_bar(segments)}{_legend(segments, compact=True)}</div>
          <button class="icon-button" data-evidence="population:{_e(row['population_id'])}" title="Review evidence">›</button>
        </article>""")

    tool_rows = "".join(
        f"<li><strong>{_e(row['name'])}</strong><span>{row['count']} observed calls</span></li>"
        for row in analytics["top_tools"]
    ) or "<li><span>No tool events were captured.</span></li>"
    transition_rows = "".join(
        f"<li><strong>{_label(row['from'])}</strong><i>→</i><strong>{_label(row['to'])}</strong><span>{row['count']}</span></li>"
        for row in analytics["checkpoint_transitions"]
    ) or "<li><span>No checkpoint transitions available.</span></li>"
    if analytics["tool_order_trustworthy"]:
        pair_title = "Recurring ordered tool pairs"
        pair_note = "The source preserves event order; arrows describe observed order, not required paths."
        pair_rows = "".join(
            f"<li><strong>{_e(row['first'])}</strong><i>→</i><strong>{_e(row['second'])}</strong><span>{row['count']}</span></li>"
            for row in analytics["ordered_tool_pairs"]
        )
    else:
        pair_title = "Recurring tool co-occurrence"
        pair_note = "The source does not preserve trustworthy tool order. + means co-occurrence only."
        pair_rows = "".join(
            f"<li><strong>{_e(row['left'])}</strong><i>+</i><strong>{_e(row['right'])}</strong><span>{row['count']}</span></li>"
            for row in analytics["tool_cooccurrence"]
        )
    pair_rows = pair_rows or "<li><span>No recurring tool pairs were captured.</span></li>"

    suggestion_cards = []
    semantic_measurements = result.get("semantic_measurements", result["suggested_measurements"])
    for row in semantic_measurements:
        evidence[f"candidate:{row['candidate_id']}"] = row["evidence_ids"][:40]
        suggestion_cards.append(
            _measurement_card(
                row,
                suggested=row["candidate_id"] in suggested_ids,
                library=row["candidate_id"] not in suggested_ids,
            )
        )
    if not suggestion_cards:
        suggestion_cards.append(
            '<div class="callout"><strong>No advisory shortlist.</strong>'
            "No proposed question passed support and contrast gates. Unsupported questions and observed analytics remain visible.</div>"
        )

    unsupported_cards = []
    for row in result.get("unsupported_questions", []):
        missing = ", ".join(_label(value) for value in row["missing_evidence"])
        unsupported_cards.append(f"""
        <article class="measurement">
          <div class="measurement-top"><div><small>{_e(row['dimension'])} · UNSUPPORTED</small><h3>{_e(row['developer_question'])}</h3></div><span class="badge rejected">Needs evidence</span></div>
          <p>{_e(row['priority_reason'])}</p>
          <div class="developer-use"><div><strong>Missing evidence</strong><p>{_e(missing)}</p></div><div><strong>Why it matters in a release</strong><p>{_e(row['release_use'])}</p></div></div>
          <p class="gap"><strong>Why Agentagon did not score it:</strong> {_e(row['unsupported_reason'])}</p>
          <small>{_e(row['proposal_id'])} · PROPOSED QUESTION, NOT A RESULT</small>
        </article>""")
    unsupported_html = "".join(unsupported_cards) or (
        '<div class="callout"><strong>No evidence-starved questions proposed.</strong>'
        "Every proposed question could be backfilled from this trace contract.</div>"
    )

    library_cards = []
    for row in sorted(
        result["candidate_measurements"],
        key=lambda item: (
            item["qualification"] != "QUALIFIED",
            item["population_id"] != "GLOBAL",
            item["population_label"],
            item["signal"],
        ),
    ):
        evidence[f"candidate:{row['candidate_id']}"] = row["evidence_ids"][:40]
        library_cards.append(
            _measurement_card(row, suggested=row["candidate_id"] in suggested_ids, library=True)
        )

    unresolved = sum(
        row["support"] for row in result["populations"]
        if row["kind"] == "MIXED_UNRESOLVED"
    )
    rejections = len(result["advisory_proposal_rejections"])
    method = """TRACE EXPORT
    |
    v
VERSIONED TRACE ADAPTER                         [CUSTOMER-SPECIFIC CODE]
    |
    v
NORMALIZED TRACE BUNDLES                        [STABLE CONTRACT]
    |
    +--> turns, tools, errors, local checkpoints [DETERMINISTIC CODE]
    |
    v
DEMAND + OBSERVED HANDLING + QUOTES             [PINNED, CACHED LLM]
    |
    v
BOUNDED HIERARCHICAL POPULATIONS                [PINNED, CACHED LLM]
    |
    v
PRIMITIVE OBSERVED ANALYTICS                    [DETERMINISTIC CODE]
    |
    +--> counts, percentages, denominators, unknowns, evidence IDs
    |
    v
AGENT-SPECIFIC RELEASE QUESTIONS                [PINNED, CACHED LLM]
    |
    +--> purpose + authority + tools + populations
    |
    v
EVIDENCE ROUTING                                [DETERMINISTIC CODE]
    |
    +--> backfillable from trace/tool calls
    +--> unsupported: needs result/state/outcome/label
    |
    v
PINNED SEMANTIC BACKFILL                        [PINNED, CACHED LLM]
    |
    +--> one typed value or ABSTAIN per trace
    +--> exact supporting quote required
    |
    v
FIXED SUPPORT + CONTRAST GATES                  [DETERMINISTIC CODE]
    |
    +--> complete library retained, including typed rejections
    |
    v
0-5 QUALIFIED RELEASE MEASUREMENTS              [CODE FROM PROPOSAL ORDER]
    |
    v
TRACK / EDIT / DEFER                            [CUSTOMER JUDGMENT]
    |
    v
FROZEN MEASUREMENT DEFINITIONS FOR LATER DIFF"""

    template = _TEMPLATE
    replacements = {
        "__AGENT__": _e(agent_name),
        "__PURPOSE__": _e(str(profile.get("purpose", "Proposed from trace evidence"))),
        "__BASELINE_LABEL__": baseline_label,
        "__SOURCE_CALLOUT__": source_callout,
        "__TRACE_COUNT__": str(total),
        "__POPULATION_COUNT__": str(len(result["populations"])),
        "__GROUNDED_PERCENT__": f"{grounded / total:.1%}",
        "__QUALIFIED_COUNT__": str(len(qualified)),
        "__UNRESOLVED__": str(unresolved),
        "__UNGROUNDED__": str(grounding.get("NONE", 0)),
        "__POPULATION_ROWS__": "".join(population_rows),
        "__TOOL_ROWS__": tool_rows,
        "__TRANSITION_ROWS__": transition_rows,
        "__PAIR_TITLE__": _e(pair_title),
        "__PAIR_NOTE__": _e(pair_note),
        "__PAIR_ROWS__": pair_rows,
        "__REPEATED_RESPONSES__": str(analytics["repetition"]["repeated_agent_response"]),
        "__REPEATED_TOOLS__": str(analytics["repetition"]["repeated_tool_call"]),
        "__SUGGESTION_COUNT__": str(len(result["suggested_measurements"])),
        "__SUGGESTION_CARDS__": "".join(suggestion_cards),
        "__UNSUPPORTED_COUNT__": str(len(result.get("unsupported_questions", []))),
        "__UNSUPPORTED_CARDS__": unsupported_html,
        "__LIBRARY_COUNT__": str(len(result["candidate_measurements"])),
        "__LIBRARY_CARDS__": "".join(library_cards),
        "__REJECTION_COUNT__": str(rejections),
        "__MODEL__": _e(str(result["model_id"])),
        "__METHOD__": _e(method),
        "__PROFILE__": _e(json.dumps(profile, indent=2, sort_keys=True)),
        "__EVIDENCE_JSON__": json.dumps(evidence).replace("</", "<\\/"),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def _measurement_card(
    row: dict[str, Any], *, suggested: bool, library: bool = False
) -> str:
    distribution = row["distribution"]
    segments = _segments(distribution, int(row["evaluable"]))
    signal = str(row["signal"])
    value_type = str(row["value_type"])
    title = str(row.get("developer_question") or _question(row))
    default_copy = _copy(signal)
    explanation = {
        "why": str(row.get("why_review") or default_copy["why"]),
        "diff": str(row.get("release_change") or default_copy["diff"]),
        "gap": str(row.get("known_gap") or default_copy["gap"]),
    }
    category = str(row.get("category") or (
        "INVESTIGATION_CUE" if value_type == "TEXT" else "COMPUTED_CANDIDATE"
    ))
    status = str(row["qualification"])
    status_class = "observed" if status == "QUALIFIED" else "rejected"
    headline = _headline(row)
    details = _distribution_details(distribution, int(row["evaluable"]))
    suggested_badge = '<span class="badge suggested">Suggested</span>' if suggested else ""
    filter_values = " ".join((value_type.lower(), status.lower(), signal.lower()))
    actions = "" if library else f"""
      <div class="actions">
        <button class="button primary" data-decision="TRACK" data-id="{_e(row['candidate_id'])}">Track</button>
        <button class="button" data-evidence="candidate:{_e(row['candidate_id'])}">Review evidence</button>
        <button class="button" data-decision="EDIT" data-id="{_e(row['candidate_id'])}">Edit</button>
        <button class="button" data-decision="DEFER" data-id="{_e(row['candidate_id'])}">Defer</button>
      </div>"""
    return f"""
    <article class="measurement" data-filter="{_e(filter_values)}">
      <div class="measurement-top"><div><small>{_e(value_type)} · {_e(category)} · {_e(row['executor'])}</small><h3>{_e(title)}</h3></div><div class="badges">{suggested_badge}<span class="badge {status_class}">{_e(status)}</span></div></div>
      <div class="metric-line">{_e(headline)}</div>
      {_bar(segments) if value_type in {'BOOLEAN', 'CATEGORY'} else ''}
      {_legend(segments) if segments else ''}
      {details}
      <p class="denominator">Denominator: {row['evaluable']} evaluable · {row.get('unknown', row['support'] - row['evaluable'])} abstained/unknown · {row['support']} scoped traces</p>
      <div class="developer-use"><div><strong>Why inspect it</strong><p>{_e(explanation['why'])}</p></div><div><strong>Release comparison</strong><p>{_e(explanation['diff'])}</p></div></div>
      <p class="gap"><strong>Cannot establish:</strong> {_e(explanation['gap'])}</p>
      <small>{_e(row['candidate_id'])} · {_e(row['qualification_reason'])}</small>
      {actions}
    </article>"""


def _segments(distribution: dict[str, Any], total: int) -> list[dict[str, Any]]:
    if total <= 0 or not distribution or "examples" in distribution or "mean" in distribution:
        return []
    rows = []
    for index, (key, value) in enumerate(
        sorted(distribution.items(), key=lambda item: (-int(item[1]), item[0]))
    ):
        color = COLORS.get(str(key).lower(), ("#657680", "#2b9a70", "#4d8abf", "#8f74bd", "#d3a13c")[index % 5])
        rows.append({"label": _label(key), "value": int(value), "pct": int(value) / total, "color": color})
    return rows


def _bar(segments: list[dict[str, Any]]) -> str:
    if not segments:
        return ""
    spans = "".join(
        f'<span style="width:{row["pct"]:.3%};background:{row["color"]}" title="{_e(row["label"])} {row["value"]}"></span>'
        for row in segments
    )
    return f'<div class="distribution" aria-label="Distribution">{spans}</div>'


def _legend(segments: list[dict[str, Any]], *, compact: bool = False) -> str:
    limit = 4 if compact else len(segments)
    rows = "".join(
        f'<span><i style="background:{row["color"]}"></i>{_e(row["label"])}: {row["value"]} ({row["pct"]:.1%})</span>'
        for row in segments[:limit]
    )
    if compact and len(segments) > limit:
        rows += f"<span>+{len(segments) - limit} categories</span>"
    return f'<div class="legend">{rows}</div>'


def _distribution_details(distribution: dict[str, Any], total: int) -> str:
    if "mean" in distribution:
        return "".join((
            '<div class="number-grid">',
            _number("Minimum", distribution["minimum"]),
            _number("Median", distribution["median"]),
            _number("Mean", round(float(distribution["mean"]), 2)),
            _number("Maximum", distribution["maximum"]),
            "</div>",
        ))
    if "examples" in distribution:
        examples = "".join(f"<li>{_e(value)}</li>" for value in distribution["examples"])
        return f'<div class="examples"><strong>{distribution["non_empty"]} evidence-linked summaries</strong><ul>{examples}</ul></div>'
    return ""


def _number(label: str, value: Any) -> str:
    return f'<div><small>{_e(label)}</small><strong>{_e(value)}</strong></div>'


def _headline(row: dict[str, Any]) -> str:
    distribution = row["distribution"]
    if row["value_type"] == "BOOLEAN":
        true = int(distribution.get("true", 0))
        return f"{true / max(1, row['evaluable']):.1%} true across {row['evaluable']} evaluable traces"
    if row["value_type"] == "CATEGORY":
        return f"{len(distribution)} observed categories across {row['evaluable']} evaluable traces"
    if row["value_type"] == "NUMBER":
        return f"Median {distribution['median']:g} · mean {distribution['mean']:.2f}"
    return f"{distribution.get('non_empty', 0)} evidence-linked summaries"


def _question(row: dict[str, Any]) -> str:
    names = {
        "HANDLING_MODE": "How was this demand population handled?",
        "ACTION_OBSERVED": "Did the trace contain an observable action event?",
        "CLAIM_WITHOUT_ACTION_EVIDENCE": "Did the agent claim an action without matching trace evidence?",
        "TURN_COUNT": "How long were the reconstructed conversations?",
        "BEHAVIOR_SUMMARY": "Which recurring conversation examples deserve investigation?",
    }
    return f"{names.get(row['signal'], _label(row['signal']))} · {row['population_label']}"


def _copy(signal: str) -> dict[str, str]:
    return {
        "HANDLING_MODE": {"why": "Shows the observed response mix for one demand population.", "diff": "Compare category share and inspect conversations that move between categories.", "gap": "Correctness, resolution, policy compliance, or world-state success."},
        "ACTION_OBSERVED": {"why": "Shows whether a release changes how often the agent reaches visible actions.", "diff": "Compare action-present share and inspect affected cases.", "gap": "Authorization, argument correctness, or successful external state change."},
        "CLAIM_WITHOUT_ACTION_EVIDENCE": {"why": "Surfaces explicit completion claims without matching visible action evidence.", "diff": "Compare mismatch share and inspect each positive case.", "gap": "That no external action occurred when instrumentation is incomplete."},
        "TURN_COUNT": {"why": "Surfaces interaction-cost and long-conversation changes.", "diff": "Compare distributions and inspect long-tail cases alongside terminal handling.", "gap": "That shorter is better or longer is failure."},
        "BEHAVIOR_SUMMARY": {"why": "Provides evidence navigation before a trusted scorer exists.", "diff": "Surface qualitative examples for investigation, not aggregate scoring.", "gap": "A numerical quality score or correctness judgment."},
    }.get(signal, {"why": "A computed behavior candidate.", "diff": "Compare baseline and candidate distributions.", "gap": "Correctness or user success."})


def _label(value: Any) -> str:
    return str(value).replace("_", " ").strip().title()


def _e(value: Any) -> str:
    return html.escape(str(value))


_TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentagon | __AGENT__ behavioral analysis</title><style>
:root{--bg:#f4f6f8;--surface:#fff;--surface2:#f8fafb;--ink:#182026;--muted:#64717d;--line:#d9e0e5;--green:#167552;--blue:#2767a5;--amber:#966313;--red:#ad3e37;--shadow:0 1px 2px rgba(24,32,38,.06),0 8px 24px rgba(24,32,38,.05)}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 Inter,system-ui,sans-serif;letter-spacing:0}button,input{font:inherit;letter-spacing:0}.app{min-height:100vh;display:grid;grid-template-columns:224px minmax(0,1fr)}
.sidebar{position:sticky;top:0;height:100vh;padding:22px 14px;background:#162027;color:#eef3f5}.brand{display:flex;align-items:center;gap:10px;padding:0 9px 21px;font-size:17px;font-weight:750}.mark{width:24px;height:24px;display:grid;place-items:center;border-radius:5px;background:#2b9a70;color:#fff}.nav{display:grid;gap:3px}.nav button{border:0;padding:10px 11px;border-radius:5px;background:transparent;color:#becbd2;text-align:left;cursor:pointer}.nav button.active{background:#2a3943;color:#fff;box-shadow:inset 3px 0 #45b88b}.agent{margin:20px 6px;padding:11px;border:1px solid #34444f;border-radius:6px;background:#1d2a32}.agent span{display:block;color:#93a5af;font-size:11px;margin-top:3px}
main{min-width:0}.topbar{height:64px;padding:0 28px;display:flex;align-items:center;justify-content:space-between;background:#fffffff2;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:4}.status{display:flex;align-items:center;gap:7px;color:var(--muted)}.dot{width:7px;height:7px;border-radius:50%;background:#2b9a70}.content{width:min(1240px,calc(100vw - 224px));padding:30px 32px 64px;margin:auto}.tab{display:none}.tab.active{display:block}.page-head{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:24px}h1{margin:0 0 6px;font-size:27px}h2{margin:0;font-size:18px}h3{margin:4px 0;font-size:15px}.lede,.muted{color:var(--muted)}.lede{max-width:780px}
.badge{display:inline-flex;padding:3px 7px;border:1px solid var(--line);border-radius:4px;background:var(--surface2);color:var(--muted);font-size:10px;font-weight:750;text-transform:uppercase;white-space:nowrap}.badge.observed{border-color:#bcd9cc;background:#e7f4ee;color:#176248}.badge.suggested{border-color:#b9cfe2;background:#eaf2fa;color:#275f91}.badge.rejected{border-color:#e4b9b5;background:#fbeceb;color:#8e302b}.badges{display:flex;gap:5px;flex-wrap:wrap;justify-content:end}.kpis{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:6px;background:#fff;box-shadow:var(--shadow);margin-bottom:26px}.kpi{padding:18px 20px;border-right:1px solid var(--line)}.kpi:last-child{border:0}.kpi small{display:block;color:var(--muted)}.kpi strong{display:block;font-size:25px;margin-top:4px}
.section{margin-top:27px}.section-head{display:flex;justify-content:space-between;gap:14px;align-items:baseline;margin-bottom:12px}.population-table,.panel,.measurement,.callout{border:1px solid var(--line);border-radius:6px;background:#fff;box-shadow:var(--shadow)}.population-row{display:grid;grid-template-columns:minmax(190px,1.15fr) 80px minmax(310px,2fr) 34px;gap:14px;align-items:center;padding:12px 15px;border-bottom:1px solid var(--line)}.population-row:last-child{border:0}.population-row small,.measurement small{display:block;color:var(--muted);font-size:10px}.number-link{border:0;background:transparent;color:var(--blue);font-weight:750;text-align:left;cursor:pointer}.icon-button{width:30px;height:30px;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:pointer}.distribution{display:flex;height:10px;margin:14px 0 7px;border-radius:3px;overflow:hidden;background:#edf1f3}.distribution span{min-width:2px}.legend{display:flex;flex-wrap:wrap;gap:5px 12px;color:var(--muted);font-size:10px}.legend span{display:inline-flex;align-items:center;gap:4px}.legend i{width:7px;height:7px;border-radius:2px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.panel{padding:17px}.clean-list{list-style:none;padding:0;margin:8px 0 0}.clean-list li{display:flex;align-items:center;gap:9px;padding:9px 0;border-bottom:1px solid #edf0f2}.clean-list li span{margin-left:auto;color:var(--muted)}.clean-list i{color:#91a0aa}.callout{padding:14px 16px;border-left:3px solid var(--amber);background:#fff7df;margin:18px 0}.callout strong{display:block}
.measurement-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.measurement{padding:17px}.measurement-top{display:flex;justify-content:space-between;gap:12px}.metric-line{margin-top:11px;font-weight:700;color:#34424c}.denominator,.gap{color:var(--muted);font-size:11px}.number-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:14px 0}.number-grid div{padding:10px;border:1px solid var(--line);border-radius:5px;background:var(--surface2)}.number-grid strong{display:block;font-size:19px}.examples{margin:13px 0;padding:12px;background:var(--surface2);border-radius:5px}.examples ul{margin:7px 0 0;padding-left:18px}.developer-use{display:grid;grid-template-columns:1fr 1fr;gap:13px;margin:14px 0;padding:13px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}.developer-use strong{font-size:10px;text-transform:uppercase;color:var(--muted)}.developer-use p{margin:3px 0 0;font-size:12px}.actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:13px}.button{padding:7px 10px;border:1px solid var(--line);border-radius:5px;background:#fff;cursor:pointer}.button.primary{border-color:var(--green);background:var(--green);color:#fff}.button.selected{background:#e7f4ee;color:#176248;border-color:#75b79d}
.toolbar{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:16px 0}.toolbar input{width:min(360px,100%);padding:9px 11px;border:1px solid var(--line);border-radius:5px}.method-grid{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px}.method-grid pre{margin:0;padding:17px;overflow:auto;border-radius:6px;background:#172128;color:#d9e6eb;font:12px/1.45 ui-monospace,monospace;white-space:pre}.profile{white-space:pre-wrap;background:var(--surface2);padding:14px;overflow:auto}.truth{padding:14px;border-left:3px solid var(--green);background:#fff}.truth.warn{border-color:var(--amber)}
dialog{width:min(760px,calc(100vw - 28px));border:0;border-radius:7px;padding:0;box-shadow:0 24px 80px #0005}dialog::backdrop{background:#0d1419aa}.modal-head{display:flex;justify-content:space-between;padding:17px 20px;border-bottom:1px solid var(--line)}.modal-body{padding:18px 20px;max-height:60vh;overflow:auto}.evidence-id{padding:9px 0;border-bottom:1px solid var(--line);font:11px ui-monospace,monospace;overflow-wrap:anywhere}
@media(max-width:980px){.app{grid-template-columns:76px minmax(0,1fr)}.brand span,.nav span,.agent{display:none}.nav button{text-align:center}.content{width:calc(100vw - 76px);padding:24px 18px}.grid,.measurement-grid,.method-grid{grid-template-columns:1fr}.population-row{grid-template-columns:1fr 70px 34px}.population-row>div:nth-child(3){grid-column:1/-1;grid-row:2}.kpis{grid-template-columns:1fr 1fr}.kpi:nth-child(2){border-right:0}}
@media(max-width:600px){.topbar{padding:0 13px}.content{padding:20px 12px}.page-head{display:block}.page-head .badge{margin-top:10px}.kpi{padding:13px}.developer-use,.number-grid{grid-template-columns:1fr 1fr}.population-table{overflow-x:auto}.population-row{min-width:560px}.toolbar{align-items:stretch;flex-direction:column}}
</style></head><body><div class="app"><aside class="sidebar"><div class="brand"><div class="mark">A</div><span>Agentagon</span></div><nav class="nav"><button class="active" data-tab="behavior">01 <span>Behavioral analysis</span></button><button data-tab="suggestions">02 <span>Release measurements</span></button><button data-tab="library">03 <span>Observed analytics</span></button><button data-tab="method">04 <span>How it works</span></button></nav><div class="agent"><strong>__AGENT__</strong><span>__PURPOSE__</span></div></aside><main><div class="topbar"><span>__BASELINE_LABEL__</span><span class="status"><i class="dot"></i>__TRACE_COUNT__ traces processed</span></div><div class="content">
<section id="behavior" class="tab active"><div class="page-head"><div><h1>Agent behavioral analysis</h1><p class="lede">What users ask __AGENT__ to do, how the agent responds, and which recurring local patterns appear in the imported traces.</p></div><span class="badge">Observed baseline · semantic labels proposed</span></div>__SOURCE_CALLOUT__<div class="kpis"><div class="kpi"><small>Traces analyzed</small><strong>__TRACE_COUNT__</strong></div><div class="kpi"><small>Demand populations</small><strong>__POPULATION_COUNT__</strong></div><div class="kpi"><small>Quote-grounded facets</small><strong>__GROUNDED_PERCENT__</strong></div><div class="kpi"><small>Qualified candidates</small><strong>__QUALIFIED_COUNT__</strong></div></div><div class="section"><div class="section-head"><div><h2>Top user intents and demand populations</h2><p class="muted">LLM proposes labels; code owns membership, counts, percentages, and evidence.</p></div></div><div class="population-table">__POPULATION_ROWS__</div></div><div class="callout"><strong>Uncertainty is retained.</strong>__UNRESOLVED__ traces remain mixed/unresolved and __UNGROUNDED__ semantic rows lack an exact quote. They stay visible but do not enter semantic denominators.</div><div class="grid section"><div class="panel"><h2>Common tools</h2><ul class="clean-list">__TOOL_ROWS__</ul></div><div class="panel"><h2>Behavioral checkpoint transitions</h2><p class="muted">Observed local transitions, not an ideal trajectory.</p><ul class="clean-list">__TRANSITION_ROWS__</ul></div><div class="panel"><h2>__PAIR_TITLE__</h2><p class="muted">__PAIR_NOTE__</p><ul class="clean-list">__PAIR_ROWS__</ul></div><div class="panel"><h2>Loop and repetition cues</h2><p><strong>__REPEATED_RESPONSES__</strong> traces repeat an identical agent response.</p><p><strong>__REPEATED_TOOLS__</strong> traces repeat a tool name.</p><p class="muted">These are investigation cues; repetition can be a valid retry.</p></div></div></section>
<section id="suggestions" class="tab"><div class="page-head"><div><h1>Proposed release measurements</h1><p class="lede">__SUGGESTION_COUNT__ agent-specific questions passed evidence, support, and contrast checks for one bounded customer review.</p></div><span class="badge">Proposed · Opinion</span></div><div class="callout"><strong>These are not golden evals.</strong>The LLM proposed observable questions from this agent's purpose, authority, tools, and demand populations. A pinned judge backfilled them; code owns denominators and gates. Track, edit, or defer based on what matters to your releases.</div><div class="measurement-grid">__SUGGESTION_CARDS__</div><div class="section"><div class="section-head"><div><h2>Unsupported questions</h2><p class="muted">__UNSUPPORTED_COUNT__ potentially valuable questions were retained rather than scored from evidence this corpus does not contain.</p></div></div><div class="measurement-grid">__UNSUPPORTED_CARDS__</div></div></section>
<section id="library" class="tab"><div class="page-head"><div><h1>Observed analytics</h1><p class="lede">All __LIBRARY_COUNT__ primitive population × signal quantities. These describe execution and handling; they are not automatically release criteria.</p></div><span class="badge">__REJECTION_COUNT__ schema rejections retained</span></div><div class="toolbar"><input id="libraryFilter" placeholder="Filter by population, signal, type, or status"><span class="muted">Useful context, separate from proposed release measurements</span></div><div class="measurement-grid" id="libraryGrid">__LIBRARY_CARDS__</div></section>
<section id="method" class="tab"><div class="page-head"><div><h1>How this report was produced</h1><p class="lede">Customer-specific parsing is isolated in the adapter. Stable artifacts preserve the LLM/code/human authority boundary.</p></div><span class="badge">Model: __MODEL__</span></div><div class="method-grid"><pre>__METHOD__</pre><div><div class="truth"><h3>Deterministic authority</h3><p>Membership, denominators, arithmetic, exhaustive enumeration, qualification, typed gaps, and artifact identity.</p></div><div class="truth warn"><h3>Proposed semantics</h3><p>Demand labels, handling labels, summaries, profile, and advisory importance remain proposed until reviewed.</p></div><div class="panel" style="margin-top:14px"><h2>Proposed profile</h2><pre class="profile">__PROFILE__</pre></div></div></div></section>
</div></main></div><dialog id="evidenceDialog"><div class="modal-head"><div><h2>Evidence references</h2><p class="muted" id="evidenceTitle"></p></div><button class="icon-button" id="closeDialog">×</button></div><div class="modal-body" id="evidenceBody"></div></dialog><script>
const evidence=__EVIDENCE_JSON__;const decisions=JSON.parse(localStorage.getItem('agentagon-v1-decisions')||'{}');
function activate(tab){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.id===tab));document.querySelectorAll('.nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===tab));history.replaceState(null,'','?tab='+tab)}
document.querySelectorAll('.nav button').forEach(button=>button.onclick=()=>activate(button.dataset.tab));const initial=new URLSearchParams(location.search).get('tab');if(document.getElementById(initial))activate(initial);
document.querySelectorAll('[data-decision]').forEach(button=>{const id=button.dataset.id;if(decisions[id]===button.dataset.decision)button.classList.add('selected');button.onclick=()=>{decisions[id]=button.dataset.decision;localStorage.setItem('agentagon-v1-decisions',JSON.stringify(decisions));button.parentElement.querySelectorAll('[data-decision]').forEach(x=>x.classList.remove('selected'));button.classList.add('selected')}});
const dialog=document.getElementById('evidenceDialog');document.querySelectorAll('[data-evidence]').forEach(button=>button.onclick=()=>{const key=button.dataset.evidence;document.getElementById('evidenceTitle').textContent=key;const rows=evidence[key]||[];const body=document.getElementById('evidenceBody');body.replaceChildren();if(rows.length){rows.forEach(value=>{const item=document.createElement('div');item.className='evidence-id';item.textContent=value;body.append(item)})}else{const empty=document.createElement('p');empty.textContent='No evidence references retained for this item.';body.append(empty)}dialog.showModal()});document.getElementById('closeDialog').onclick=()=>dialog.close();
document.getElementById('libraryFilter').oninput=event=>{const query=event.target.value.toLowerCase();document.querySelectorAll('#libraryGrid .measurement').forEach(card=>card.hidden=!card.textContent.toLowerCase().includes(query)&&!card.dataset.filter.includes(query))};
</script></body></html>'''
