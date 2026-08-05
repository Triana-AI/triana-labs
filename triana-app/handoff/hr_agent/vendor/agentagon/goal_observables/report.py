"""Exhaustive report for goal-to-observable discovery.

Only the 'suggestions' (proposed measurements) and 'library' (all candidates) tabs and
the functions that render them (_measurement, _behavior, _selection) are DEPRECATED —
slated for deletion, replaced by behavioral-evals pipeline (see
internal/DELETION_MANIFEST_behavioral_evals.md). The 'overview', 'behavior', 'context',
'gaps', and 'method' tabs are NOT measurement-generation and stay.
"""

from __future__ import annotations

import html
import json
from typing import Any

from agentagon.slate_v3.report import _CSS as BASE_CSS


COLORS = ("#17845f", "#3d7fb1", "#d29a2e", "#8b6ab4", "#aab5bb", "#c45c57")


def render_goal_observable_html(result: dict[str, Any]) -> str:
    profile = result["agent_profile"]
    evidence: dict[str, list[str]] = {}
    populations = "".join(_population(row, result["trace_count"], evidence) for row in result["populations"])
    # DEPRECATED below: shortlist/goal_library/behavior_library/rejected feed the
    # 'suggestions' and 'library' tabs — slated for deletion, see
    # internal/DELETION_MANIFEST_behavioral_evals.md.
    shortlist = "".join(_measurement(row, evidence, review=True) for row in result["shortlist"])
    if not shortlist:
        shortlist = "<div class='callout'><strong>No proposal qualified.</strong> Inspect observed-only candidates and evidence gaps before adding a scorer.</div>"
    goal_library = "".join(_measurement(row, evidence, review=False) for row in result["goal_candidate_library"])
    behavior_library = "".join(_behavior(row, evidence) for row in result["behavior_candidate_library"])
    gaps = "".join(_gap(row) for row in result["unsupported_goal_questions"] + result["typed_gaps"])
    gaps = gaps or "<div class='callout'>No typed evidence gaps were recorded.</div>"
    context = result["context_preflight"]
    composition = "".join(_composition(name, row) for name, row in context["composition"].items())
    criteria = "".join(
        f"<article class='criterion'><div><strong>{_e(row['name'])}</strong><p>{_e(row['explanation'])}</p></div><span class='badge {'gap' if row['status']=='NOT_EVALUABLE' else 'ok'}'>{_label(row['status'])}</span></article>"
        for row in context["criteria"]
    )
    behavior_map = result["behavior_evidence_map"]
    behavior_rows = "".join(
        f"<tr><td>{_e(row['population_label'])}</td><td>{_label(row['category'])}</td><td>{_e(row['label'])}</td><td>{row['numerator']} / {row['denominator']}</td></tr>"
        for row in behavior_map["cells"][:100]
    )
    rejected = "".join(
        f"<tr><td><code>{_e(row['proposal_id'])}</code></td><td>{_label(row['reason'])}</td></tr>"
        for row in result["proposal_rejections"]
    ) or "<tr><td colspan='2'>No proposal schema rejections.</td></tr>"
    payload = json.dumps(evidence).replace("</", "<\\/")
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{_e(profile.get('agent_name','Agent'))} measurement discovery</title><style>{BASE_CSS}{_EXTRA_CSS}</style></head><body>
<aside><div class='brand'>Agentagon<small>Goal-linked cold start</small></div><nav><button data-tab='overview' class='active'>Agent understanding</button><button data-tab='behavior'>Behavior evidence</button><button data-tab='suggestions'>Proposed measurements</button><button data-tab='library'>All candidates</button><button data-tab='context'>Context preflight</button><button data-tab='gaps'>Evidence gaps</button><button data-tab='method'>How it works</button></nav></aside><main>
<section id='overview' class='tab active'><header><div><small>INFERRED, CUSTOMER-CORRECTABLE</small><h1>{_e(profile.get('agent_name','Imported agent'))}</h1><p>{_e(profile.get('purpose','Purpose inferred from supplied context and traces.'))}</p></div><div class='kpi'><b>{result['trace_count']}</b><span>normalized traces</span></div></header><div class='callout'><strong>What this stage does.</strong> It learns observed demand and execution vocabulary, then proposes dimensions worth comparing across releases. It does not decide whether behavior is acceptable.</div><h2>Observed demand populations</h2><div class='table-wrap'><table><thead><tr><th>Population</th><th>Kind</th><th>Support</th><th>Observed handling</th><th></th></tr></thead><tbody>{populations}</tbody></table></div></section>
<section id='behavior' class='tab'><header><div><small>FACTUAL SUPPORTING INVENTORY</small><h1>Behavior evidence map</h1><p>Observed actions, endings, claims, repetitions, and checkpoints. These explain outcomes; they do not automatically become the release slate.</p></div><span class='badge'>{len(behavior_map['cells'])} cells</span></header><div class='table-wrap'><table><thead><tr><th>Population</th><th>Evidence family</th><th>Observed state</th><th>Rate</th></tr></thead><tbody>{behavior_rows}</tbody></table></div></section>
<section id='suggestions' class='tab'><header><div><small>BOUNDED CUSTOMER REVIEW</small><h1>Proposed release measurements</h1><p>Domain outcomes and decision integrity first; behavioral explanations support them.</p></div><span class='badge opinion'>Proposed · Opinion</span></header><div class='callout'><strong>Not golden evals.</strong> The model proposes observable definitions; code computes every displayed count. Qualified cards have support and contrast; Observed Only cards are evidence-grounded but need customer confirmation or more data. Track or Edit freezes the definition for repeated comparison.</div>{_selection(result)}<div class='cards'>{shortlist}</div></section>
<section id='library' class='tab'><header><div><small>AUDITABLE INVENTORY</small><h1>All candidates</h1><p>Goal-linked proposals plus the older deterministic behavioral inventory. Nothing is silently deleted.</p></div></header><h2>Goal-linked candidates</h2><div class='cards'>{goal_library}</div><h2>Supporting behavioral candidates</h2><div class='cards'>{behavior_library}</div><h2>Proposal schema rejections</h2><div class='table-wrap'><table><thead><tr><th>Proposal</th><th>Reason</th></tr></thead><tbody>{rejected}</tbody></table></div></section>
<section id='context' class='tab'><header><div><small>PRE-BEHAVIOR DIAGNOSTIC</small><h1>Context preflight</h1><p>What evidence is visible in this export before interpreting behavior.</p></div><span class='badge gap'>{_label(context['static_candidate_preflight'])}</span></header><div class='callout'><strong>Boundary:</strong> {_e(context['boundary'])}</div><div class='two'><div class='panel'><h2>Captured composition</h2>{composition}</div><div><h2>Quality checks</h2><div class='criteria one'>{criteria}</div></div></div></section>
<section id='gaps' class='tab'><header><div><small>HONEST NON-RESULTS</small><h1>Evidence gaps</h1><p>High-value questions that cannot be answered from the current export are retained here, not converted into fake scores.</p></div></header><div class='cards'>{gaps}</div></section>
<section id='method' class='tab'><header><div><small>MECHANISM AND AUTHORITY</small><h1>How this report was calculated</h1><p>The model proposes and classifies bounded semantics. Code owns membership, counts, qualification, freezing, and provenance.</p></div></header><pre>{_e(_METHOD)}</pre></section>
</main><dialog id='evidenceDialog'><button class='close'>×</button><h2>Evidence references</h2><ol id='evidenceList'></ol></dialog><script id='evidenceData' type='application/json'>{payload}</script><script>{_JS}</script></body></html>"""


def render_goal_observable_markdown(result: dict[str, Any]) -> str:
    profile = result["agent_profile"]
    lines = [f"# {profile.get('agent_name', 'Agent')} — Goal-linked measurement discovery", "", f"- Traces: **{result['trace_count']}**", f"- Goal-linked candidates: **{len(result['goal_candidate_library'])}**", f"- First-review slate: **{len(result['shortlist'])}**", f"- Unsupported questions: **{len(result['unsupported_goal_questions'])}**", "", "## Proposed release measurements", ""]
    for row in result["shortlist"]:
        display = row.get("display")
        summary = row.get("numeric_summary")
        lines += [f"### {row['title']}", "", row["developer_question"], "", f"- Concern: `{row['goal_kind']}`", f"- Type: `{row['value_type']}`"]
        if summary:
            lines.append(
                f"- Numeric summary: n=`{summary['n']}` mean=`{summary['mean']}` "
                f"median=`{summary['median']}` stdev=`{summary['stdev']}` "
                f"min=`{summary['min']}` max=`{summary['max']}`"
            )
        elif display:
            lines.append(f"- Display: `{display['mode']}` · {display['chip']}")
            lines += [f"  - {text}" for text in display.get("phrases", {}).values()]
        else:
            lines.append(f"- Distribution: `{row['distribution']}`")
        lines += [f"- Evaluable / unknown: `{row['evaluable']} / {row['unknown']}`", f"- Release use: {row['release_change']}", f"- Cannot establish: {row['known_gap']}", ""]
    lines += ["## Evidence gaps", ""]
    for row in result["unsupported_goal_questions"] + result["typed_gaps"]:
        lines.append(f"- **{row.get('title') or row.get('kind', 'Gap')}:** {row.get('unsupported_reason') or row.get('reason') or row.get('known_gap')}")
    return "\n".join(lines) + "\n"


# DEPRECATED — renders the 'suggestions'/'library' tabs; slated for deletion, replaced by
# behavioral-evals pipeline (see internal/DELETION_MANIFEST_behavioral_evals.md).
def _measurement(row: dict[str, Any], evidence: dict[str, list[str]], *, review: bool) -> str:
    key = f"measurement-{row['frozen_definition']['measurement_id']}"
    evidence[key] = list(row.get("evidence_ids", []))[:30]
    actions = "<div class='actions'><button class='primary'>Track</button><button>Edit</button><button>Defer</button></div>" if review else ""
    return f"<article class='measurement'><div class='card-top'><div><small>{_label(row['goal_kind'])} · {_e(row['population_label'])} · {_label(row['value_type'])}</small><h3>{_e(row['title'])}</h3></div><span class='badge {'ok' if row['qualification']=='QUALIFIED' else 'gap'}'>{_label(row['qualification'])}</span></div><p class='question'>{_e(row['developer_question'])}</p>{_display_block(row)}<p class='denom'>Denominator: {row.get('evaluable',0)} evaluable · {row.get('unknown',0)} unknown</p><div class='why'><div><strong>Why compare it</strong><p>{_e(row['why_review'])}</p></div><div><strong>Release use</strong><p>{_e(row['release_change'])}</p></div></div><p class='boundary'><strong>Cannot establish:</strong> {_e(row['known_gap'])}</p><button class='link' data-evidence='{_e(key)}'>Review evidence</button>{actions}</article>"


# DEPRECATED — renders the 'library' tab; slated for deletion, replaced by
# behavioral-evals pipeline (see internal/DELETION_MANIFEST_behavioral_evals.md).
def _behavior(row: dict[str, Any], evidence: dict[str, list[str]]) -> str:
    key = f"behavior-{row['candidate_id']}"
    evidence[key] = list(row.get("evidence_ids", []))[:30]
    return f"<article class='measurement supporting'><div class='card-top'><div><small>Supporting behavior · {_e(row['population_label'])}</small><h3>{_e(row['title'])}</h3></div><span class='badge'>{_label(row['qualification'])}</span></div><p>{_e(row['developer_question'])}</p>{_distribution(row.get('distribution',{}), int(row.get('evaluable',0)))}<p class='boundary'>Available for explanation or customer promotion; it cannot crowd out domain outcomes.</p><button class='link' data-evidence='{_e(key)}'>Review evidence</button></article>"


def _population(row: dict[str, Any], total: int, evidence: dict[str, list[str]]) -> str:
    key = f"population-{row['population_id']}"
    evidence[key] = list(row.get("evidence_ids", []))[:30]
    return f"<tr><td><strong>{_e(row['label'])}</strong><small>{_e(row.get('definition',''))}</small></td><td>{_label(row['kind'])}</td><td>{row['support']}<small>{row['support']/total:.1%} of corpus</small></td><td>{_distribution(row.get('handling_distribution',{}), int(row['support']))}</td><td><button class='link' data-evidence='{_e(key)}'>Evidence</button></td></tr>"


# DEPRECATED — renders the 'suggestions' tab; slated for deletion, replaced by
# behavioral-evals pipeline (see internal/DELETION_MANIFEST_behavioral_evals.md).
def _selection(result: dict[str, Any]) -> str:
    qualified = sum(row["qualification"] == "QUALIFIED" for row in result["goal_candidate_library"])
    observed = sum(row["qualification"] == "OBSERVED_ONLY" for row in result["shortlist"])
    return f"<div class='selection'><div><b>{len(result['goal_candidate_library'])}</b><span>goal-linked candidates</span></div><i>→</i><div><b>{qualified}</b><span>qualified by support + contrast</span></div><i>→</i><div><b>{len(result['shortlist'])}</b><span>balanced first review ({observed} evidence-limited)</span></div></div>"


def _gap(row: dict[str, Any]) -> str:
    title = row.get("title") or _label(row.get("kind", "Evidence gap"))
    reason = row.get("unsupported_reason") or row.get("reason") or row.get("known_gap") or "Evidence unavailable."
    needed = f"<small>Needs: {_e(', '.join(row.get('missing_evidence', [])))}</small>" if row.get("missing_evidence") else ""
    return f"<article class='gap-card'><strong>{_e(title)}</strong><p>{_e(reason)}</p>{needed}</article>"


def _composition(name: str, row: dict[str, Any]) -> str:
    return f"<div class='composition'><div><strong>{_label(name)}</strong><span>{row['estimated_tokens']} estimated tokens</span></div><b>{(row['share'] or 0):.1%}</b><div class='bar'><i style='width:{(row['share'] or 0):.2%}'></i></div></div>"


def _display_block(row: dict[str, Any]) -> str:
    summary = row.get("numeric_summary")
    if summary:
        return _numeric_block(summary)
    display = row.get("display")
    distribution = row.get("distribution", {})
    evaluable = int(row.get("evaluable", 0))
    unknown = int(row.get("unknown", 0))
    if not display:
        return _distribution(distribution, evaluable)
    chip = f"<span class='badge {'ok' if display['tracking_role']=='TRACKABLE' else 'gap'} chip'>{_e(display['chip'])}</span>"
    mode = display["mode"]
    if mode == "RATE":
        body = _distribution(distribution, evaluable, unknown=unknown)
    else:
        body = "".join(f"<p class='phrase'>{_e(text)}</p>" for text in display.get("phrases", {}).values())
    return f"<div class='display-mode'>{chip}</div>{body}"


def _numeric_block(summary: dict[str, Any]) -> str:
    if not summary.get("n"):
        return "<span class='muted'>No numeric observations</span>"
    stats = (
        ("mean", summary.get("mean")),
        ("median", summary.get("median")),
        ("stdev", summary.get("stdev")),
        ("min", summary.get("min")),
        ("max", summary.get("max")),
        ("n", summary.get("n")),
    )
    cells = "".join(
        f"<span><em>{_e(label)}</em><b>{_e(value)}</b></span>" for label, value in stats if value is not None
    )
    return f"<div class='numeric'>{cells}</div>"


def _distribution(values: dict[str, int], total: int, *, unknown: int = 0) -> str:
    if not values or not total:
        return "<span class='muted'>Not evaluable</span>"
    ordered = sorted(values.items(), key=lambda item: (-item[1], item[0]))
    bars = "".join(f"<i style='width:{value/total:.2%};background:{COLORS[index%len(COLORS)]}'></i>" for index, (_, value) in enumerate(ordered))
    unknown_suffix = f", {unknown} unknown" if unknown else ""
    legend = "".join(f"<span><em style='background:{COLORS[index%len(COLORS)]}'></em>{_label(key)} <b>{value}</b> ({value/total:.1%}{unknown_suffix})</span>" for index, (key, value) in enumerate(ordered))
    return f"<div class='stack'>{bars}</div><div class='legend'>{legend}</div>"


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _label(value: Any) -> str:
    return str(value).replace("_", " ").strip().title()


_METHOD = """AGENT PURPOSE + ROLES + AUTHORITY                [PINNED MODEL / CUSTOMER-CORRECTABLE]
HISTORICAL TRACE BUNDLES                          [ADAPTER + CODE]
    +--> demand populations                       [PINNED MODEL + CODE]
    +--> observed handling / tools / endings      [PINNED MODEL + CODE]
    +--> context and evidence availability        [CODE]
    v
GOAL-TO-OBSERVABLE PROPOSALS                      [ONE PINNED MODEL CALL]
    |  definitions only; the model writes no numbers
    v
EVIDENCE ROUTER                                   [CODE]
    |  unavailable truth becomes an evidence gap
    v
PINNED TRACE CLASSIFIER                           [PINNED MODEL]
    |  one category or ABSTAIN + exact quote
    v
COUNTS + DENOMINATORS + QUALIFICATION             [CODE]
    v
TRACK / EDIT / DEFER                              [CUSTOMER]
    v
FROZEN DEFINITION FOR EVERY FUTURE DIFF           [CODE]"""

_EXTRA_CSS = ".question{font-size:15px;font-weight:650}.denom{font-size:12px;color:#64737b}.supporting{border-left:4px solid #829098}.one{grid-template-columns:1fr}.gap-card small{margin-top:9px}.display-mode{margin:6px 0}.chip{font-size:11px}.phrase{font-size:13px;margin:4px 0;color:#3a4750}.numeric{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}.numeric span{display:flex;flex-direction:column;padding:6px 10px;background:#f2f5f6;border-radius:6px;min-width:56px}.numeric em{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#64737b;font-style:normal}.numeric b{font-size:15px;color:#17323f}"
_JS = """const data=JSON.parse(document.getElementById('evidenceData').textContent);const dialog=document.getElementById('evidenceDialog');const list=document.getElementById('evidenceList');function show(id){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.id===id));document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));history.replaceState(null,'','?tab='+id)}document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>show(b.dataset.tab));const initial=new URLSearchParams(location.search).get('tab');if(document.getElementById(initial))show(initial);document.querySelectorAll('[data-evidence]').forEach(b=>b.onclick=()=>{list.innerHTML=(data[b.dataset.evidence]||[]).map(x=>`<li><code>${x}</code></li>`).join('')||'<li>No retained references.</li>';dialog.showModal()});document.querySelector('.close').onclick=()=>dialog.close();"""
