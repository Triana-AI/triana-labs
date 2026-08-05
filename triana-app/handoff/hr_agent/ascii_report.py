"""RESULT.json -> the boxed ASCII release-gate report.

Same format as the committed `data/gate/{codefix,model}.ascii.txt` fixtures in the
agentagon-demo repo — this module was written by reverse-engineering those two files
byte-for-byte, then verified to reproduce them exactly from their source
`{codefix,model}.json` (the same `behavioral-evals-diff-v0.1` schema `run_gate.py`
writes). `run_gate.py` imports `render_ascii_report` from here so the PR-comment output
and the demo UI's pre-baked fixtures are always the same generator, not two hand-synced
copies.

Column widths (id 39, each side 12, 46 dashes) and the trailing "~" marker are fixed to
match those fixtures. Real gates would vary the marker per `finding` (CHANGED/SAME/NEW);
every row in both fixtures is CHANGED, so this generator always prints "~" — a
simplification worth calling out, not a silent guess.
"""

from __future__ import annotations

from typing import Any

_ID_WIDTH = 39
_SIDE_WIDTH = 12
_DASH_WIDTH = 46


def _top_label_pct(side: dict[str, Any]) -> tuple[str, int]:
    """Largest-share label in a distribution, as `(label, rounded_pct)`. Mirrors
    `topShare()` in agentagon-demo's `lib/gate.ts` — always reads the raw counts in
    `distribution`, even for PERCENT measurements that also carry a `rate` field."""
    distribution = side.get("distribution") or {}
    total = sum(distribution.values())
    if total == 0:
        return "n/a", 0
    label, count = max(distribution.items(), key=lambda item: item[1])
    return label, round(count / total * 100)


def render_ascii_report(result: dict[str, Any]) -> str:
    """`result` is a `behavioral-evals-diff-v0.1` bundle (the `RESULT.json` shape
    `run_gate.py` writes, and what `data/gate/*.json` already are)."""
    lines = [
        f"  agentagon release gate — {result['pair_label']}",
        f"  {'-' * _DASH_WIDTH}",
    ]
    for row in result["diff"]:
        base_label, base_pct = _top_label_pct(row["baseline"])
        cand_label, cand_pct = _top_label_pct(row["candidate"])
        base_str = f"{base_label} {base_pct}%"
        cand_str = f"{cand_label} {cand_pct}%"
        lines.append(
            f"  {row['id']:<{_ID_WIDTH}} {base_str:>{_SIDE_WIDTH}} -> {cand_str:>{_SIDE_WIDTH}}  ~"
        )
    return "\n".join(lines)
