# ⚠️ READ FIRST — GREEN panel is blocked by a REAL finding, not a bug on our side

**Date:** 2026-07-22 (overnight autonomous run)

## What happened
I was building the GREEN "looping fix works" panel from HR AI's post-fix corpus. The real
numbers **refute the fix** — so I did NOT build a green panel (would have been faking it).

## The data (verified twice, independently)
Candidate = `demo_candidate/` (post-dedup-fix, still running, 34 traces so far).
Baseline = `run_200/` enriched, matched by case_id (same scenarios). Both `normalized-trace-v2`.

- **agent_looping, completed traces only: baseline 19% (6/32) → candidate 21% (6/28).** Flat-to-worse, NOT the drop a working fix should show.
- **3 NEW `GraphRecursionError` crashes** in the candidate (`hr_0036`, `hr_0042`, `hr_0062`) —
  "Recursion limit of 50 reached without hitting a stop condition." These do NOT occur in the
  baseline for the same case_ids. This is the *worst* form of looping: the agent spins until
  LangGraph's step cap kills the run.
- Counting those crashes as looping: candidate ≈ 31%. Either reading = a **regression**.

## Likely cause (hypothesis, for HR AI)
The `session_dedup` memo returns the cached result instantly for a repeated identical tool call.
If the agent's control flow re-issues the same call expecting to make progress, instant cached
returns may let it spin through graph nodes *faster* into the recursion limit instead of stopping.
Tool-level dedup did not stop the agent-level loop — and may have worsened it. Worth checking the
3 recursion cases specifically.

## This is not bad news for the demo — it may be the BEST story
The whole product thesis is "the gate catches bad releases before they ship." Here the gate,
run on real post-fix traces, **caught that a looping fix actually regressed + introduced crashes.**
That's more compelling than a green checkmark.

## Your options (pick in the morning — I did NOT decide this for you)
1. **Reframe the demo:** GREEN panel becomes a second "gate catches the broken fix" → BLOCK. Real,
   honest, strong. (The v2 adapter is built + committed — `agentagon` `022f36e`, `adapter_v2.py`
   + tests — so I can generate this panel from the data in minutes once you say go.)
2. **Fix the fix:** HR AI debugs the dedup regression (start with the 3 recursion cases), re-runs,
   THEN we build a real GREEN.
3. **Wait for the full run** (`demo_candidate` still growing toward ~200) for firmer numbers before
   deciding — the direction is unlikely to flip (recursion crashes won't un-happen), but n grows.

## Meanwhile
- **BLOCK demo (codefix release) is DONE and recordable** — unaffected.
- The v2 adapter works and is tested; whichever panel you want, it's a short step from here.
- I keep polling the candidate run and will append final numbers to DEMO_TODO.md when it completes.

## UPDATE — confirmed on a second run (2026-07-22 ~03:10)
HR AI restarted + parallelized the candidate run (worker shards w0/w1/w2). Aggregated 19 traces:
looping **baseline 21% → candidate 29%**, plus 1 GraphRecursionError (hr_0109). Same regression as
the first 34-trace run (19%→21% + 3 crashes) on different scenarios. The dedup fix regresses looping
across two independent runs. No corrected fix committed (still at 10aec81). Finding is robust.

## UPDATE 2 — regression sharpens at n=41 (2026-07-22 ~03:40)
Candidate now 41 traces: looping **baseline 21% → candidate 37%** + 2 recursion crashes. Third
consecutive confirmation; the gap WIDENS as more traces land (19%→21% at n=34, 21%→29% at n=19,
21%→37% at n=41). The dedup fix clearly makes looping worse. Still no corrected commit (10aec81).

## UPDATE 3 — clean 200-scenario fix-ON candidate analyzed (2026-07-22, otel-v1 schema)
The isolated fix-ON candidate landed (~/Desktop/hr_ai_demo_corpus_backup/candidate/, 200 records,
all COMPLETED, schema normalized-trace-otel-v1, fully enriched with tool arguments+results).
GOTCHA: the schema changed AGAIN (otel-v1 = flat kind=='tool' events, NOT v2's nested tool_calls).
A v2-based extractor reads 0 tool calls → a FALSE "looping 0%". Using HR AI's own precomputed
`repeated_tool_calls` field instead:
- 26% of traces STILL have a repeated identical call (duplicate_count>0); 146 duplicate calls total.
- 16% have >20 tool calls; 7 recursion-limit crashes (4%); 30% any looping signal.
The candidate does NOT demonstrate the fix worked, AND there is no baseline in the same otel-v1
schema to compute a delta. GREEN still NOT built (would be fabrication).
NEEDED for a real GREEN: (1) a fix-OFF baseline over the same 200 scenarios in the SAME otel-v1
pipeline, and (2) HR AI to confirm whether `repeated_tool_calls` counts post-dedup reality or the
agent's attempts (146 duplicates on a "dedup-ON" run needs explaining). LESSON: every comparison
must have baseline+candidate in the identical schema/extractor — schema drift (v1/v2/otel-v1) has
produced false readings three times now.
