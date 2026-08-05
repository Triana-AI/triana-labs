# agentagon release gate for hr_agent

A self-contained GitHub Action for the `hr_agent` repo: on every PR (or a
`/agentagon run` comment), it runs a deterministic-only agentagon behavioral-evals
release gate against committed demo traces and posts the ASCII report as a PR comment.

**Fully runnable today, on real data.** `run_gate.py` loads the committed
`traces/{baseline,candidate}/normalized_traces.jsonl` (200 real HR-AI agent traces per
side, schema `normalized-trace-otel-v1`), computes `agent_looping_rate`,
`duplicate_tool_call_rate`, and `recursion_crash_rate` straight from
`bundle.events`/`bundle.provenance` using agentagon's real
`agentagon.behavioral_evals.event_signals.agent_looping_label` formula (vendored under
`vendor/agentagon/`), writes `RESULT.json`/`verdict.txt`/`ascii.txt`, and prints the
ASCII report. Zero LLM calls, zero secrets, zero network access.

## What's here

```
handoff/hr_agent/
  .github/workflows/agentagon-gate.yml   the Action itself
  run_gate.py                            runs the diff, writes RESULT.json/verdict.txt/ascii.txt
  ascii_report.py                        RESULT.json -> the boxed ASCII report
  hr_ai_adapter_otel_v1.py               copy of agentagon's experiments/hr_ai_seed/adapter_otel_v1.py
                                          (parses the normalized-trace-otel-v1 trace shape)
  requirements.txt                       litellm only (see "Why litellm is here" below)
  traces/                                COMMITTED: baseline/candidate normalized_traces.jsonl (200 each)
  vendor/
    README.md                           what's vendored and why
    sync_agentagon.sh                   regenerates vendor/agentagon/ from a local agentagon checkout
    agentagon/                          COMMITTED: the vendored agentagon packages run_gate.py imports
```

`frozen/` does not exist and is not needed -- there is no live-model judge path in this
gate. An earlier draft of this Action replayed frozen EVAL judge labels through
`FrozenLabelModel`; this version only computes STATIC, event-derived measurements, so
there is nothing to freeze or replay.

## Why litellm is here

`run_gate.py` only ever calls `agentagon.behavioral_evals.event_signals.agent_looping_label`
-- a pure function over `bundle.events`, no model call. But importing
`agentagon.behavioral_evals.event_signals` runs `agentagon/behavioral_evals/__init__.py`
first (how Python package imports work), which imports the judge-pipeline modules
(`pipeline.py` -> `agentagon.exploration_v1.llm`) even though this script's code path
never reaches them. `litellm` has to be importable for that import chain to succeed; it
is never called.

## Verified

Ran `run_gate.py` end to end in a clean venv (`python3 -m venv` + `pip install -r
requirements.txt`, nothing else) against the committed 200-trace corpus:

```
$ python3 run_gate.py
[gate] baseline: 200 traces from traces/baseline/normalized_traces.jsonl (0 gaps)
[gate] candidate: 200 traces from traces/candidate/normalized_traces.jsonl (0 gaps)
[gate] deterministic only -- zero live model calls, zero secrets
[gate] wrote RESULT.json
[gate] verdict: REVIEW -- IMPROVED-WITH-CAVEAT: agent_looping_rate moved -8.0pts but recursion crashes rose 4 -> 7

  agentagon release gate — baseline (baseline) vs candidate (candidate)
  ----------------------------------------------
  agent_looping_rate                         false 62% ->    false 70%  ~
  duplicate_tool_call_rate                   false 64% ->    false 74%  ~
  recursion_crash_rate                       false 98% ->    false 96%  ~
  verdict: REVIEW -- IMPROVED-WITH-CAVEAT: agent_looping_rate moved -8.0pts but recursion crashes rose 4 -> 7
  total duplicate tool calls: 184 -> 146
```

Read as counts: agent_looping_rate 75/200 (38%) -> 59/200 (30%); duplicate-call traces
73/200 (36%) -> 53/200 (26%); total duplicate tool calls 184 -> 146; recursion crashes
4/200 (2%) -> 7/200 (3.5%). The looping rate improved, but recursion crashes regressed --
this Action reports that honestly as `REVIEW`, not a silent `PASS`.

`run_gate.py`, `ascii_report.py`, and `hr_ai_adapter_otel_v1.py` all pass `python3 -m
py_compile`. `.github/workflows/agentagon-gate.yml` was validated with `yaml.safe_load`.

## Verdicts

Three-way, not BLOCK/PASS binary, because a binary can't say "primary metric improved,
secondary metric regressed" honestly:

- **BLOCK** -- `agent_looping_rate` regressed >= 15pts baseline -> candidate. Fails the
  GitHub check.
- **REVIEW** -- `agent_looping_rate` did not regress that badly (here it *improved*), but
  `recursion_crash_rate` rose. Posted as a warning annotation and a `⚠️ REVIEW` PR
  comment; does not fail the check, but is not a silent pass either.
- **PASS** -- neither triggered.

## Morning steps

1. **Copy this directory into `hr_agent`.** From this repo:
   ```bash
   cp -r handoff/hr_agent/. /path/to/hr_agent/
   cd /path/to/hr_agent
   ```

2. **Re-vendor agentagon if it has changed** (already committed here, but regenerate
   any time agentagon's `behavioral_evals`/`evals`/`core` packages change):
   ```bash
   AGENTAGON_SRC=/path/to/your/agentagon/checkout vendor/sync_agentagon.sh
   git add vendor/agentagon
   ```
   See `vendor/README.md` for what this copies and why.

3. **Traces are already committed** (`traces/{baseline,candidate}/normalized_traces.jsonl`,
   200 real HR-AI traces per side). Swap them for a different pair by overwriting those
   two files with any `normalized-trace-otel-v1` export -- no other config to touch.

4. **Sanity-check locally** before pushing (this is exactly what the Action runs):
   ```bash
   pip install -r requirements.txt
   python3 run_gate.py
   cat verdict.txt   # BLOCK, REVIEW, or PASS
   cat ascii.txt     # what the PR comment will show
   ```

5. **Point the release-diff link at your deployment.** `.github/workflows/agentagon-gate.yml`
   defaults `releaseDiffUrl` to `http://localhost:3000/release/fix` (this repo's local
   dev UI). Swap it for your deployed agentagon-demo URL's `/release/<pair>` page once
   you have one.

6. **Push the branch and open the demo PR.** No repo secrets needed -- the workflow
   never calls a live model. On `pull_request: [opened, synchronize]` it runs
   automatically; you can also re-trigger it any time by commenting `/agentagon run` on
   the PR.

## Placeholders you must fill in

- `releaseDiffUrl` in `.github/workflows/agentagon-gate.yml` (step "Post PR comment") --
  currently `http://localhost:3000/release/fix`, a local-dev default. Point it at your
  deployed URL once you have one.
