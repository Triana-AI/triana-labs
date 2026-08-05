"""The Measurements tab — renders a run_behavioral_evals() result.

Replaces the old goal_observables 'suggestions' and 'library' tabs. Standalone,
self-contained HTML for now; wiring this into the multi-tab shell that also
renders overview/behavior/context/gaps/method (agentagon/goal_observables/report.py)
is a follow-up once this pipeline is fed by enriched traces in the live app.
"""

from __future__ import annotations

import html
from typing import Any


COLORS = ("#17845f", "#3d7fb1", "#d29a2e", "#8b6ab4", "#aab5bb", "#c45c57")

_DIMENSION_LABELS = {
    "GOAL_CORRECTNESS": "Goal correctness",
    "TOOL_CALL_RELIABILITY": "Tool call reliability",
    "PERFORMANCE_UNDER_LOAD": "Performance under load",
    "FAULT_TOLERANCE": "Fault tolerance",
    "TRACE_OBSERVABILITY": "Trace observability",
    "SAFETY": "Safety",
}
_DIMENSION_ORDER = tuple(_DIMENSION_LABELS)


def render_behavioral_evals_report(result: dict[str, Any]) -> str:
    profile = result.get("agent_profile", {})
    measurements_by_id = {row["id"]: row for row in result.get("measurements", [])}
    results_by_id = result.get("results", {})
    coverage_map = result.get("coverage_map", {"populated": {}, "gaps": []})

    cards = "".join(
        _measurement_card(measurements_by_id[measurement_id], results_by_id.get(measurement_id, {}))
        for dimension in _DIMENSION_ORDER
        for measurement_id in coverage_map.get("populated", {}).get(dimension, [])
        if measurement_id in measurements_by_id
    )
    if not cards:
        cards = "<div class='callout'>No measurement populated any dimension yet.</div>"

    coverage_panel = "".join(_dimension_row(dimension, coverage_map) for dimension in _DIMENSION_ORDER)
    enriched_note = (
        "Traces are enriched (tool I/O + sub-agent spans + timestamps): all six dimensions were attempted."
        if result.get("has_enriched_traces")
        else "Traces are NOT enriched yet: TOOL_CALL_RELIABILITY, PERFORMANCE_UNDER_LOAD, and FAULT_TOLERANCE "
        "are expected as coverage gaps until enriched traces land."
    )

    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{_e(profile.get('agent_name', 'Agent'))} behavioral evals</title><style>{_CSS}</style></head><body>
<main>
<header><div><small>BEHAVIORAL EVALS</small><h1>{_e(profile.get('agent_name', 'Imported agent'))}</h1><p>{_e(profile.get('purpose', ''))}</p></div><div class='kpi'><b>{result.get('trace_count', 0)}</b><span>traces</span></div></header>
<div class='callout'>{_e(enriched_note)}</div>
<h2>Coverage map</h2>
<div class='coverage'>{coverage_panel}</div>
<h2>Measurements</h2>
<div class='cards'>{cards}</div>
</main></body></html>"""


def render_behavioral_evals_diff_report(result: dict[str, Any]) -> str:
    """Diff-mode Measurements tab: each card shows baseline vs candidate side by side +
    delta + n on both sides, for a frozen measurement set re-run on two trace sets
    (see gate.run_release_gate). Same shell/CSS as render_behavioral_evals_report."""
    profile = result.get("agent_profile", {})
    coverage_map = result.get("coverage_map", {"populated": {}, "gaps": []})
    rows = result.get("diff", [])
    cards = "".join(_diff_card(row) for row in rows) or "<div class='callout'>No measurements in this frozen set.</div>"
    coverage_panel = "".join(_dimension_row(dimension, coverage_map) for dimension in _DIMENSION_ORDER)
    changed = sum(1 for row in rows if row.get("finding") == "CHANGED")

    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{_e(profile.get('agent_name', 'Agent'))} behavioral evals diff</title><style>{_CSS}{_DIFF_CSS}</style></head><body>
<main>
<header><div><small>BEHAVIORAL EVALS — BASELINE VS CANDIDATE</small><h1>{_e(profile.get('agent_name', 'Imported agent'))}</h1><p>{_e(result.get('pair_label', ''))}</p></div>
<div class='kpi'><b>{result.get('baseline_trace_count', 0)}</b><span>baseline traces</span></div>
<div class='kpi'><b>{result.get('candidate_trace_count', 0)}</b><span>candidate traces</span></div>
<div class='kpi'><b>{changed}</b><span>of {len(rows)} changed</span></div>
</header>
<h2>Coverage map</h2>
<div class='coverage'>{coverage_panel}</div>
<h2>Measurements — baseline vs candidate</h2>
<div class='cards diff-cards'>{cards}</div>
</main></body></html>"""


def _diff_card(row: dict[str, Any]) -> str:
    finding = row.get("finding", "UNCHANGED")
    badge = "ok" if finding == "UNCHANGED" else "gap"
    display = row.get("display")
    baseline = row.get("baseline", {})
    candidate = row.get("candidate", {})
    if display == "SMALL_PERCENT_BAR":
        body = _diff_percent(baseline, candidate)
    else:
        body = _diff_stacked(baseline, candidate)
    return (
        f"<article class='measurement'><div class='card-top'>"
        f"<small>{_e(row.get('kind'))} · {_e(row.get('value_type'))} · {_e(_label(row.get('dimension', '')))}</small>"
        f"<h3>{_e(row.get('title'))}</h3></div>"
        f"<p>{_e(row.get('developer_question', ''))}</p>"
        f"<span class='badge {badge}'>{_e(finding)}</span>"
        f"{body}{_diff_scope_suffix(baseline, candidate)}</article>"
    )


def _diff_scope_suffix(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    """Surface each side's excluded-trace count (behavioral_evals' EVAL executor calls
    this `not_applicable` -- see gate._rename_unknown_to_not_applicable) so an EVAL
    measurement's percentage is never read as computed over the full trace count when a
    real share of traces went unjudged. Only rendered when at least one side has any."""
    base_excluded = int(baseline.get("not_applicable") or 0)
    cand_excluded = int(candidate.get("not_applicable") or 0)
    if not base_excluded and not cand_excluded:
        return ""
    return f"<p class='denom'>not_applicable — baseline = {base_excluded} · candidate = {cand_excluded}</p>"


def _diff_percent(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    base_rate, cand_rate = baseline.get("rate"), candidate.get("rate")
    if base_rate is None or cand_rate is None:
        return "<span class='muted'>Not evaluable on one or both sides</span>"
    base_pct, cand_pct = round(100 * base_rate), round(100 * cand_rate)
    delta = cand_pct - base_pct
    sign = "+" if delta > 0 else ""
    return (
        f"<div class='diff-row'><div><small>Baseline</small><b>{base_pct}%</b>"
        f"<span class='denom'>n = {baseline.get('n', 0)}</span></div>"
        f"<div class='arrow'>→</div>"
        f"<div><small>Candidate</small><b>{cand_pct}%</b>"
        f"<span class='denom'>n = {candidate.get('n', 0)}</span></div>"
        f"<div class='delta'>{sign}{delta} pts</div></div>"
    )


def _diff_stacked(baseline: dict[str, Any], candidate: dict[str, Any]) -> str:
    base_dist, cand_dist = baseline.get("distribution") or {}, candidate.get("distribution") or {}
    if not base_dist and not cand_dist:
        return "<span class='muted'>Not evaluable on either side</span>"
    labels = sorted(set(base_dist) | set(cand_dist))
    base_total, cand_total = sum(base_dist.values()), sum(cand_dist.values())
    rows = "".join(
        _diff_label_row(label, base_dist.get(label, 0), base_total, cand_dist.get(label, 0), cand_total)
        for label in labels
    )
    return (
        f"<div class='diff-legend'>"
        f"<div class='diff-legend-head'><span>baseline n={baseline.get('n', 0)}</span><span>candidate n={candidate.get('n', 0)}</span></div>"
        f"{rows}</div>"
    )


def _diff_label_row(label: str, base_count: int, base_total: int, cand_count: int, cand_total: int) -> str:
    base_pct = round(100 * base_count / base_total) if base_total else None
    cand_pct = round(100 * cand_count / cand_total) if cand_total else None
    delta_text = ""
    if base_pct is not None and cand_pct is not None:
        delta = cand_pct - base_pct
        sign = "+" if delta > 0 else ""
        delta_text = f"<span class='delta-inline'>{sign}{delta} pts</span>"
    base_text = f"{base_pct}%" if base_pct is not None else "—"
    cand_text = f"{cand_pct}%" if cand_pct is not None else "—"
    return (
        f"<div class='diff-legend-row'><span class='label'>{_e(_label(label))}</span>"
        f"<span>{base_text} ({base_count})</span><span>→ {cand_text} ({cand_count})</span>{delta_text}</div>"
    )


def _dimension_row(dimension: str, coverage_map: dict[str, Any]) -> str:
    label = _DIMENSION_LABELS[dimension]
    populated = coverage_map.get("populated", {}).get(dimension)
    if populated:
        body = f"<b>{len(populated)}</b><span>measurement{'s' if len(populated) != 1 else ''} populated</span>"
        badge = "ok"
    else:
        gap = next((row for row in coverage_map.get("gaps", []) if row.get("dimension") == dimension), None)
        needs = gap["needs"] if gap else "no data"
        body = f"<b>Coverage gap</b><span>needs {_e(needs)}</span>"
        badge = "gap"
    return f"<article class='dimension {badge}'><strong>{_e(label)}</strong>{body}</article>"


def _measurement_card(measurement: dict[str, Any], result: dict[str, Any]) -> str:
    display = measurement.get("display")
    n = result.get("n", 0)
    body = {
        "SMALL_PERCENT_BAR": _percent_bar,
        "STACKED_BAR": _stacked_bar,
        "NUMBER": _number_block,
    }.get(display, _stacked_bar)(result)
    return (
        f"<article class='measurement'><div class='card-top'>"
        f"<small>{_e(measurement.get('kind'))} · {_e(measurement.get('value_type'))}</small>"
        f"<h3>{_e(measurement.get('title'))}</h3></div>"
        f"<p>{_e(measurement.get('developer_question', ''))}</p>"
        f"{body}<p class='denom'>n = {n}{_scope_suffix(result)}</p></article>"
    )


def _scope_suffix(result: dict[str, Any]) -> str:
    """Only rendered when non-zero — most measurements have no excluded traces at all,
    and a permanent "not_applicable = 0 · abstained = 0" on every card would be noise."""
    not_applicable = int(result.get("not_applicable") or 0)
    abstained = int(result.get("abstained") or 0)
    parts = []
    if not_applicable:
        parts.append(f"not_applicable = {not_applicable}")
    if abstained:
        parts.append(f"abstained = {abstained}")
    return f" · {' · '.join(parts)}" if parts else ""


def _percent_bar(result: dict[str, Any]) -> str:
    rate = result.get("rate")
    if rate is None:
        return "<span class='muted'>Not evaluable</span>"
    pct = round(100 * rate)
    return f"<div class='metric'><b>{pct}%</b></div><div class='bar'><i style='width:{pct}%'></i></div>"


def _stacked_bar(result: dict[str, Any]) -> str:
    distribution = result.get("distribution") or {}
    total = result.get("n", 0)
    if not distribution or not total:
        return "<span class='muted'>Not evaluable</span>"
    ordered = sorted(distribution.items(), key=lambda item: (-item[1], item[0]))
    bars = "".join(
        f"<i style='width:{value / total:.2%};background:{COLORS[index % len(COLORS)]}'></i>"
        for index, (_, value) in enumerate(ordered)
    )
    legend = "".join(
        f"<span><em style='background:{COLORS[index % len(COLORS)]}'></em>{_e(_label(key))} <b>{value}</b> ({value / total:.1%})</span>"
        for index, (key, value) in enumerate(ordered)
    )
    return f"<div class='stack'>{bars}</div><div class='legend'>{legend}</div>"


def _number_block(result: dict[str, Any]) -> str:
    summary = result.get("numeric_summary")
    if not summary or not summary.get("n"):
        return "<span class='muted'>No numeric observations</span>"
    stats = (("mean", summary.get("mean")), ("median", summary.get("median")), ("min", summary.get("min")), ("max", summary.get("max")))
    cells = "".join(f"<span><em>{_e(label)}</em><b>{_e(value)}</b></span>" for label, value in stats if value is not None)
    return f"<div class='numeric'>{cells}</div>"


def _e(value: Any) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def _label(value: Any) -> str:
    return str(value).replace("_", " ").strip().title()


_CSS = """
*{box-sizing:border-box}body{margin:0;background:#f4f6f7;color:#162027;font:14px Inter,ui-sans-serif,system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:30px 38px}
header{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;margin-bottom:18px}
h1{font-size:28px;margin:4px 0 6px}h2{font-size:17px;margin:26px 0 12px}h3{font-size:16px;margin:5px 0}
p{line-height:1.5}small,.muted{display:block;color:#66757d}
.kpi{background:white;border:1px solid #d9e0e3;border-radius:7px;padding:14px 20px}
.kpi b{display:block;font-size:24px}
.callout{background:white;border:1px solid #d9e0e3;border-left:4px solid #d29a2e;border-radius:7px;padding:13px 16px;margin:10px 0}
.coverage{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.dimension{background:white;border:1px solid #d9e0e3;border-radius:7px;padding:14px}
.dimension.ok{border-left:4px solid #17845f}.dimension.gap{border-left:4px solid #c45c57}
.dimension b{display:block;font-size:18px;margin-top:4px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.measurement{background:white;border:1px solid #d9e0e3;border-radius:7px;padding:16px}
.card-top{display:flex;flex-direction:column;gap:2px}
.metric b{font-size:24px}
.bar,.stack{height:9px;background:#e2e7e9;border-radius:3px;display:flex;overflow:hidden;margin-top:6px}
.bar i,.stack i{display:block;height:100%;background:#17845f}
.legend{display:flex;flex-wrap:wrap;gap:5px 12px;margin-top:8px;font-size:11px;color:#5e6d75}
.legend span{display:flex;align-items:center;gap:5px}.legend em{width:8px;height:8px;border-radius:2px}
.numeric{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.numeric span{display:flex;flex-direction:column;padding:6px 10px;background:#f2f5f6;border-radius:6px;min-width:56px}
.numeric em{font-size:10px;text-transform:uppercase;color:#64737b;font-style:normal}
.numeric b{font-size:15px;color:#17323f}
.denom{font-size:12px;color:#64737b;margin-top:10px}
.badge{display:inline-block;border:1px solid #cbd5d9;border-radius:4px;padding:3px 7px;font-size:11px;font-weight:700;background:white;margin:6px 0}
.badge.ok{color:#126c50;background:#eaf7f1;border-color:#b8dfd0}
.badge.gap{color:#855d08;background:#fff7df;border-color:#e8d28e}
"""

_DIFF_CSS = """
.diff-cards .measurement{padding:16px 18px}
.diff-row{display:flex;align-items:center;gap:14px;margin-top:10px}
.diff-row>div:not(.arrow):not(.delta){display:flex;flex-direction:column}
.diff-row b{font-size:22px}
.diff-row .arrow{color:#95a2a8;font-size:18px}
.diff-row .delta{margin-left:auto;font-weight:700;color:#3d7fb1}
.diff-legend{margin-top:10px;font-size:12px}
.diff-legend-head{display:flex;justify-content:space-between;color:#8b979d;font-size:10px;text-transform:uppercase;margin-bottom:4px}
.diff-legend-row{display:grid;grid-template-columns:1fr auto auto auto;gap:8px;padding:4px 0;border-top:1px solid #eef1f2;align-items:center}
.diff-legend-row .label{font-weight:650;color:#3a4750}
.delta-inline{font-weight:700;color:#3d7fb1;text-align:right}
"""
