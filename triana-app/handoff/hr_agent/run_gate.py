"""Thin runner for the hr_agent GitHub Action: computes a deterministic-only
behavioral-evals diff over a committed baseline-vs-candidate trace pair, writes
RESULT.json, prints the ASCII report, and writes a one-line verdict.

DETERMINISTIC ONLY -- unlike an earlier draft of this script, there is no
FrozenLabelModel / frozen-labels replay path here, because this Action's
committed corpus (`traces/{baseline,candidate}/normalized_traces.jsonl`, schema
`normalized-trace-otel-v1`) has no frozen judge labels to replay. Every
measurement below is computed straight from `bundle.events` /
`bundle.provenance` -- no LLM, no Bedrock, no OpenRouter, no network call of
any kind. `agent_looping_label` is imported unmodified from agentagon's real
`agentagon.behavioral_evals.event_signals` (the same formula a live gate's
AGENT_LOOPING_RATE STATIC measurement uses); this script only adds the extra
plumbing to fold in a recursion-crash flag and the corpus's own
`repeated_tool_calls` duplicate-count field, since neither of those has a
deterministic formula upstream yet.

Traces are read with `hr_ai_adapter_otel_v1.HrAiNormalizedTraceOtelV1Adapter`
(copied from agentagon's `experiments/hr_ai_seed/adapter_otel_v1.py`) -- the
committed demo traces are OTel-span-sourced `normalized-trace-otel-v1` rows
(flat `events` list, `kind` in {"tool","model","generate-sql"}, plus a
corpus-computed `repeated_tool_calls` summary and, for crashed runs, an
`error` string even though `status` stays "COMPLETED"), not the
historical_traffic_v0 `turns`/`events` shape the older `adapter_v1`/`adapter_v2`
parse.

Requires `vendor/agentagon/` to exist (run `vendor/sync_agentagon.sh` once --
see `vendor/README.md`) and `traces/{baseline,candidate}/normalized_traces.jsonl`
to be committed. `vendor/agentagon/` is imported only for
`event_signals.agent_looping_label` and the trace-bundle/adapter plumbing it
depends on; importing the `agentagon.behavioral_evals` package (a Python
package import always runs its `__init__.py`) pulls in the judge-pipeline
modules too, which is why `litellm` stays in requirements.txt even though this
script never calls it -- see `vendor/README.md`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))
sys.path.insert(0, str(HERE))

from agentagon.behavioral_evals.event_signals import agent_looping_label  # noqa: E402
from agentagon.evals.identity import digest_value  # noqa: E402
from agentagon.evals.trace_bundle import NormalizedTraceBundle  # noqa: E402

from ascii_report import render_ascii_report  # noqa: E402
from hr_ai_adapter_otel_v1 import HrAiNormalizedTraceOtelV1Adapter  # noqa: E402

# The gate watches agent_looping_rate as its primary (block-worthy) signal --
# matches `WATCH_ID`/`BLOCK_THRESHOLD_PTS` in agentagon-demo's `lib/gate.ts`.
# duplicate_tool_call_rate and recursion_crash_rate are secondary evidence:
# they explain WHY agent_looping_rate moved, and recursion_crash_rate can turn
# an otherwise-clean improvement into a REVIEW verdict (see `_verdict` below).
WATCH_ID = "agent_looping_rate"
RECURSION_ID = "recursion_crash_rate"
BLOCK_THRESHOLD_PTS = 15


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=HERE / "traces/baseline/normalized_traces.jsonl")
    parser.add_argument("--candidate", type=Path, default=HERE / "traces/candidate/normalized_traces.jsonl")
    parser.add_argument("--out", type=Path, default=HERE / "RESULT.json")
    parser.add_argument("--verdict-out", type=Path, default=HERE / "verdict.txt")
    parser.add_argument("--ascii-out", type=Path, default=HERE / "ascii.txt")
    return parser


def _is_looping(bundle: NormalizedTraceBundle) -> bool:
    """TRUE if the real agentagon formula flags this trace as looping (repeated
    identical tool call, or an excessive raw tool-call count), OR the run
    crashed out via a LangGraph recursion-limit error -- a recursion crash is
    every bit as much "the agent couldn't stop" as a detected repeat, it just
    means the loop ran long enough to hit the harness's hard ceiling before a
    signature repeated. `agent_looping_label` itself has no opinion on
    recursion crashes (it only sees `bundle.events`), so this one extra
    `or` is this script's entire addition to agentagon's real formula."""
    return agent_looping_label(bundle) == "TRUE" or bool(bundle.provenance.get("recursion_crash"))


def _has_duplicate_tool_call(bundle: NormalizedTraceBundle) -> bool:
    repeated = bundle.provenance.get("repeated_tool_calls") or {}
    return bool(repeated.get("duplicate_count", 0))


def _is_recursion_crash(bundle: NormalizedTraceBundle) -> bool:
    return bool(bundle.provenance.get("recursion_crash"))


def _rate_row(
    id_: str,
    title: str,
    dimension: str,
    developer_question: str,
    baseline_bundles: tuple[NormalizedTraceBundle, ...],
    candidate_bundles: tuple[NormalizedTraceBundle, ...],
    predicate: Callable[[NormalizedTraceBundle], bool],
) -> dict[str, Any]:
    def side(bundles: tuple[NormalizedTraceBundle, ...]) -> dict[str, Any]:
        n = len(bundles)
        true_n = sum(1 for bundle in bundles if predicate(bundle))
        return {
            "n": n,
            "distribution": {"true": true_n, "false": n - true_n},
            "rate": (true_n / n) if n else None,
        }

    return {
        "id": id_,
        "title": title,
        "dimension": dimension,
        "kind": "STATIC",
        "value_type": "PERCENT",
        "display": "SMALL_PERCENT_BAR",
        "developer_question": developer_question,
        "finding": "CHANGED",
        "baseline": side(baseline_bundles),
        "candidate": side(candidate_bundles),
    }


def _total_duplicate_tool_calls(bundles: tuple[NormalizedTraceBundle, ...]) -> int:
    return sum((bundle.provenance.get("repeated_tool_calls") or {}).get("duplicate_count", 0) for bundle in bundles)


def _verdict(diff_rows: list[dict[str, Any]]) -> tuple[str, str]:
    """Three-way verdict, not a BLOCK/PASS binary -- a clean binary can't say
    "the primary metric improved but a secondary one regressed" without either
    hiding the regression (fake PASS) or blocking a real improvement (fake
    BLOCK). Mirrors `gateVerdict()`'s BLOCK threshold in agentagon-demo's
    `lib/gate.ts` for the primary signal, and adds REVIEW on top for the
    recursion-crash caveat.

      BLOCK  -- agent_looping_rate regressed >= BLOCK_THRESHOLD_PTS pts.
      REVIEW -- agent_looping_rate did not regress that badly (or improved),
                but recursion_crash_rate rose -- worth a human look before
                calling it a clean win.
      PASS   -- neither triggered. Includes a clean improvement.

    Returns (verdict, headline) where headline is the one-line, honest summary
    -- e.g. "IMPROVED-WITH-CAVEAT" for the REVIEW case, never softened to a
    plain PASS-shaped label.
    """
    by_id = {row["id"]: row for row in diff_rows}
    looping = by_id[WATCH_ID]
    recursion = by_id[RECURSION_ID]
    looping_delta_pts = (looping["candidate"]["rate"] - looping["baseline"]["rate"]) * 100
    recursion_baseline_n = recursion["baseline"]["distribution"]["true"]
    recursion_candidate_n = recursion["candidate"]["distribution"]["true"]
    recursion_regressed = recursion_candidate_n > recursion_baseline_n

    if looping_delta_pts >= BLOCK_THRESHOLD_PTS:
        return "BLOCK", f"{WATCH_ID} regressed {looping_delta_pts:+.1f}pts (>= {BLOCK_THRESHOLD_PTS}pt threshold)"
    if recursion_regressed:
        return (
            "REVIEW",
            f"IMPROVED-WITH-CAVEAT: {WATCH_ID} moved {looping_delta_pts:+.1f}pts but "
            f"recursion crashes rose {recursion_baseline_n} -> {recursion_candidate_n}",
        )
    if looping_delta_pts < 0:
        return "PASS", f"IMPROVED: {WATCH_ID} moved {looping_delta_pts:+.1f}pts, no recursion-crash regression"
    return "PASS", f"{WATCH_ID} moved {looping_delta_pts:+.1f}pts, no regression triggered"


def main() -> int:
    args = build_arg_parser().parse_args()

    adapter = HrAiNormalizedTraceOtelV1Adapter()
    baseline_result = adapter.load(args.baseline)
    candidate_result = adapter.load(args.candidate)
    baseline_bundles = baseline_result.bundles
    candidate_bundles = candidate_result.bundles
    print(f"[gate] baseline: {len(baseline_bundles)} traces from {args.baseline} ({len(baseline_result.gaps)} gaps)")
    print(f"[gate] candidate: {len(candidate_bundles)} traces from {args.candidate} ({len(candidate_result.gaps)} gaps)")
    print("[gate] deterministic only -- zero live model calls, zero secrets")

    diff_rows = [
        _rate_row(
            WATCH_ID,
            "Agent Looping Rate",
            "PERFORMANCE_UNDER_LOAD",
            "What percentage of traces show agent looping behavior (repeated identical "
            "tool call, excessive tool-call count, or a recursion-limit crash)?",
            baseline_bundles,
            candidate_bundles,
            _is_looping,
        ),
        _rate_row(
            "duplicate_tool_call_rate",
            "Duplicate Tool-Call Rate",
            "TOOL_CALL_RELIABILITY",
            "What percentage of traces issued at least one duplicate tool call "
            "(same tool, same canonical arguments, called more than once)?",
            baseline_bundles,
            candidate_bundles,
            _has_duplicate_tool_call,
        ),
        _rate_row(
            RECURSION_ID,
            "Recursion Crash Rate",
            "FAULT_TOLERANCE",
            "What percentage of traces crashed out via a LangGraph recursion-limit error?",
            baseline_bundles,
            candidate_bundles,
            _is_recursion_crash,
        ),
    ]

    total_duplicate_calls = {
        "baseline": _total_duplicate_tool_calls(baseline_bundles),
        "candidate": _total_duplicate_tool_calls(candidate_bundles),
    }

    bundle_hash = digest_value(
        {
            "baseline": sorted((bundle.case_id, _is_looping(bundle)) for bundle in baseline_bundles),
            "candidate": sorted((bundle.case_id, _is_looping(bundle)) for bundle in candidate_bundles),
        }
    )

    result = {
        "schema_version": "behavioral-evals-diff-v0.1-deterministic-only",
        "pair_label": f"{args.baseline.parent.name} (baseline) vs {args.candidate.parent.name} (candidate)",
        "baseline_source": str(args.baseline),
        "candidate_source": str(args.candidate),
        "baseline_trace_count": len(baseline_bundles),
        "candidate_trace_count": len(candidate_bundles),
        "diff": diff_rows,
        "total_duplicate_tool_calls": total_duplicate_calls,
        "gate_bundle_hash": bundle_hash,
        "watch_id": WATCH_ID,
        "block_threshold_pts": BLOCK_THRESHOLD_PTS,
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"[gate] wrote {args.out}")

    verdict, headline = _verdict(diff_rows)
    args.verdict_out.write_text(verdict + "\n", encoding="utf-8")
    print(f"[gate] verdict: {verdict} -- {headline}")

    ascii_report = render_ascii_report(result)
    banner = (
        f"  verdict: {verdict} -- {headline}\n"
        f"  total duplicate tool calls: {total_duplicate_calls['baseline']} -> {total_duplicate_calls['candidate']}\n"
    )
    full_ascii = ascii_report + "\n" + banner
    args.ascii_out.write_text(full_ascii, encoding="utf-8")
    print()
    print(full_ascii)

    return 1 if verdict == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
