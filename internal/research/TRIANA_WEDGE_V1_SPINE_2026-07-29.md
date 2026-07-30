# Triana Wedge V1 Spine — "Incident to Evidence"

> **Shipping scope superseded:** read
> `TRIANA_SELF_SERVE_V1_SHIP_SPEC_2026-07-29.md` for the final V1 product
> boundary. This document remains the research spine and open-thread rationale.

Status: DRAFT FOR FREEZE (v2 of this document, 2026-07-29). Rewritten after the
case-study steals (Anterior, Chime, Portola, Community Signal Corpus, LangSmith
IssueBench) and the entry-door correction (connect-first, not upload-first).
Supersedes the positioning (not the mechanics) of
`TRIANA_SELF_SERVE_V0_FROZEN_2026-07-29.md`: production replay stays as the
mechanism; the Release Evidence Record becomes the product; the incident becomes
the entry point. Grounded in `RELEASE_CONTROL_PLANE_MARKET_RESEARCH_2026-07-29.md`
(Thesis B verdict, 2–4 quarter window, 90-day kill criteria).

---

## 1. Thesis in one line

> Production replay is how we check; the evidence record is what we sell; the
> incident is where we start.

The customer owns what "correct" means and where things run. Triana owns the
memory, the measurement protocol, and the permanent record. The record — not a
verdict — is the product. Verdicts are a later rendering of records.

### Positioning discipline (from the market research + LangSmith Engine)

Discovery (traces → issues) is incumbent territory — LangSmith Engine ships it
in the background of a product teams already pay for. The rule is NOT "vacate
discovery"; it is "never make discovery the differentiated paid claim." We ship
connect-and-surface proudly, free, as plumbing. We charge only for the layer
verified empty across 11 platforms: composite release identity, the immutable
evidence record, and neutral orchestration of the customer's own execution.

> Engine turns traces into a to-do list. Triana turns incidents into permanent
> release protection with proof.

### The promise ladder (never promise above the current rung)

| Rung | Promise | When |
|---|---|---|
| 1 | "The same regression will never ship twice." | Day 1 (incident cases, provable) |
| 2 | "Your most important behaviors can't regress silently." | Month 2–3 (scan-driven coverage) |
| 3 | "Every release's whole behavior is compared to the last." | Platform future (distribution diff) |

### pass@k vs pass^k (the measurement stance)

Demos are graded pass@k (at least one of k attempts succeeds — capability).
Customers experience pass^k (all attempts succeed — reliability). `triana check`
estimates the per-run pass rate p over k runs and records it against a baseline.
p = 0.9 looks perfect at pass@8 (~100%) and fails most users at pass^8 (~43%).
The record always reports rates, never single-run pass/fail.

### What the record attests (and never claims)

| Statement | Record? |
|---|---|
| "This failure happened in production" | Yes — incident record, trace as evidence |
| "This team decided this behavior must hold" | Yes — protected case, approver named |
| "Candidate X was re-tested k times; rate R; person P approved" | Yes — release record |
| "This won't happen in production" | NEVER — prediction is marketing, the check is fact |

---

## 2. The spine (frozen v1, end to end)

Entry rule: **ingest broad, approve narrow.** The customer never hunts or
uploads a bad trace — we connect, surface candidates, they point. The approval
atom stays one trace + one expected behavior.

```
                    TRIANA WEDGE V1 — "INCIDENT TO EVIDENCE"
─────────────────────────────────────────────────────────────────────────────────

 FREE ───────────────────────────────────────────────────────────────────────
 ┌────────────────────────────────────────────┐
 │ ①  CONNECT (read-only) or upload export    │   Langfuse · LangSmith ·
 │    + ONE LINE: "what is this agent         │   OTel / JSONL. Local-CLI
 │    supposed to do?"                        │   ingest for the privacy-
 └───────────────────┬────────────────────────┘   sensitive.
                     ▼
 ┌────────────────────────────────────────────┐
 │ ②  INGEST window · SURFACE CANDIDATES      │   Deterministic signals we
 │    tool errors · loops · aborted sessions  │   already have, $0: a ranked
 │    cost spikes · their flagged traces      │   LIST. Full clustering /
 └───────────────────┬────────────────────────┘   coverage map = Phase 4.
                     ▼
 ┌────────────────────────────────────────────┐
 │ ③  THEY POINT: "that one — that's the      │   The incident found IN
 │    thing from the postmortem"              │   their data, not uploaded.
 └───────────────────┬────────────────────────┘
                     ▼
 ┌────────────────────────────────────────────┐
 │ ④  SIX-FIELD CASE BUILDER (Chime schema)   │   Legal-legible AND machine-
 │     · risk name                            │   readable. Mechanical shadow
 │     · what the agent should do             │   proposed FIRST (action
 │     · what is prohibited                   │   assertion, not prose) —
 │     · policy / legal context               │   severe wild incidents are
 │     · allowed alternatives                 │   blast-radius = action-
 │     · example user questions               │   checkable (corpus S2).
 │    + replayability tier auto-assigned:     │
 │      READY / NEEDS-FIXTURE / NOT-YET       │
 └───────────────────┬────────────────────────┘
                     ▼
 ┌────────────────────────────────────────────┐
 │ ⑤  ONE trace · ONE proposed expected       │   Approval is always on a
 │    behavior · one button:  [ PROMOTE ]     │   concrete example, never an
 │    (Anterior's verb)                       │   abstraction (Chime).
 └───────────────────┬────────────────────────┘   Triana never invents
                     ▼                            ground truth.
        PROTECTED CASE LIBRARY (named risks, grows forever)
                     │
 PAID ═══════════════╪══════════  EVERY AGENT PR / RELEASE  ══════════════════
                     ▼
 ┌────────────────────────────────────────────┐
 │ ⑥  THEIR CI · THEIR INFRA · THEIR KEYS     │   ~6 lines of YAML
 │    one step: `triana check`                │   (GitHub Action wrapping
 │    a. runs each READY case k times         │   the CLI). Tool behavior
 │       (default 5–10, per-case config)      │   during runs = their
 │       against the candidate                │   runtime's problem (staging,
 │    b. observes identity from those runs:   │   their mocks). No Triana
 │       model id · prompts · tool schemas    │   replay harness in v1.
 │       + git SHA → composite hash           │
 │    c. results + identity up; raw traces    │
 │       can stay local                       │
 └───────────────────┬────────────────────────┘
                     ▼
 ┌─────────────────────────────────────────────────────┐
 │ ⑦  RELEASE EVIDENCE RECORD  (hash-chained, immutable)│
 │                                                     │
 │   HEADLINE — named risk, never a score:             │
 │   "refund-escalation regressed: 6/10, was 10/10     │
 │    last release"                                    │
 │                                                     │
 │   per failure: EXPECTED vs OBSERVED vs REASON       │
 │   (Anterior's two outputs — never a bare 0.42)      │
 │   identity hash + observation scope                 │
 │   ("seen across N calls; components: …")            │
 │   evidence class per result (see ladder)            │
 │   sign-off: PR approving review, bound in           │
 │   coverage: "N protected cases · M distinct         │
 │   candidate mechanisms observed" (the "X of Y       │
 │   behaviors" phrasing arrives with Phase-4 taxonomy)│
 └──────────┬─────────────────────────┬────────────────┘
            ▼                         ▼
 ┌────────────────────┐      ┌─────────────────────┐
 │ ⑧  PR COMMENT      │      │ ⑨  EVIDENCE PAGE    │
 │  headline + link   │      │  permanent URL,     │
 │  advisory only —   │      │  tamper-evident,    │
 │  NEVER blocks in v1│      │  forwardable to boss│
 └────────────────────┘      └──────────┬──────────┘
                                        │
                     ┌──────────────────┘
                     ▼
 GROWTH LOOP: new incident → ③ · Phase-4 scan gaps → ④ · library grows →
              coverage number on every record grows → promise ladder climbs

─────────────────────────────────────────────────────────────────────────────────
 DEAL:  ① – ⑤  free  (connect + surface + incident conversion = the wow)
        ⑦ – ⑨  paid  (records on real releases) — EXCEPT one protected case
        forever-free end to end, so they feel the full loop before paying.
        Pilot anchor: $500/mo flat, 60–90 days.
─────────────────────────────────────────────────────────────────────────────────
```

### Onboarding at scale — the 50k-trace funnel (zero labelers)

The approval atom is human-per-BEHAVIOR, not human-per-trace. Traces are fuel
for ranking, not a labeling backlog. One approved case protects the behavior
behind its whole cluster (the mechanical shadow asserts the decision rule, not
the transcript). Status of each funnel stage, verified against code 2026-07-29:

```
 50,000 traces
    ▼  deterministic pass ($0, all traces)          VERIFIED IN CODE
    ▼  ~2–3k candidate traces (Blitz rates:
       loops 11.9%, error-terminal 3%,
       unbacked action claims 0.6%)
    ▼  signature dedup + auto-resolve               AUTO-RESOLVE VERIFIED;
    ▼  ~15–30 distinct mechanisms                   SIGNATURE WIRING MISSING
    ▼  rank by frequency × severity × blast-radius  NOT BUILT — Phase 1 item
    ▼  ONE SCREEN: ~15 proposed cases, one
       exemplar trace each
    ▼  one engineer, one sitting → ~10 Promotes     EXTRAPOLATED, unproven
```

Honest boundary: the bottom of the funnel is proven at 624 conversations
(Blitz). The compression from thousands of candidates to a one-screen decision
set is THE Phase 1 product work — two missing links (signature wiring, ranking)
— and "families saturate at ~8–15" plus "45 minutes" are reasoning, not
measurement, until a real 10k+ onboarding tests them.

### The 2-minute demo (Anterior's loop — our wedge as a story)

1. Connect; candidates surface. 2. Team points at the postmortem trace.
3. Six-field case drafted; reviewer clicks Promote. 4. Weeks later a PR changes
that behavior. 5. The case fails at 4/10 (was 10/10). 6. The record explains —
expected vs observed vs reason. 7. Click-through lands on the ORIGINAL
production trace. Same mistake, provably impossible to ship silently twice.

---

## 2b. The execution contract (7 steps, FINAL — supersedes all earlier check descriptions)

What v1 produces, honestly named: **bound, paired, manifest-conditional
evidence** in the default mode — and explicitly weaker labels in every
fallback mode.

1. Customer CI resolves an approved **baseline ref** (default: merge-base of
   the PR with the default branch; overridable to a pinned tag or
   last-green-record SHA) and the **candidate PR ref**.
2. It builds and boots BOTH in isolated runtimes from those exact checkouts.
   **Each runtime must attest the expected git SHA** — v1 method: CI passes
   the SHA as an env var; the agent echoes it into root trace metadata and/or
   a `/version` health response; the CLI compares expected vs attested. No
   echo → that side is OBSERVED, mechanically.
3. Triana maps the protected case input into the customer's **declared
   request template** (their schema, their field names, ~5 lines) and assigns
   a unique run ID to every baseline/candidate trial.
4. Existing instrumentation writes each execution to the customer's trace
   store. **run ID, case ID, trial ID, side and SHA must survive into root
   trace metadata** — every trace independently attributable; an auditor can
   reconstruct the record from the trace store alone.
5. Triana fetches and evaluates those traces with the closed deterministic
   assertion set. **Negative assertions only for tools verified at an
   exhaustively instrumented dispatch boundary** — v1 verification: customer
   declares the boundary in config (e.g. LangGraph ToolNode, single executor
   wrapper); we verify the framework pattern where known; upgrade path is a
   root-span tool-count marker. Consequence accepted: negatives become rarer
   and bulletproof. A negative result reads "X not observed in trace
   (boundary-verified)," never "X did not happen."
6. The record separately reports **pass/evaluable, end-to-end success, and
   gaps**. Labels — BOUND, COMPARABLE, REGRESSED, OBSERVED, ENFORCED,
   DOCUMENTED-ONLY — are **mechanically selected from evidence, never written
   manually**. Headline claim composes as the WEAKEST relevant dimension:
   "regressed" only when BOUND ∧ COMPARABLE ∧ threshold.
7. When runtime binding, trace completeness, or environmental comparability
   is absent, the record **drops that dimension to its weaker label** —
   per-dimension degradation, not a single ladder.

### The qualification run (READY is earned)

A case becomes READY only after one successful rehearsal: input sent, trace
fetched by run ID, every assertion evaluable, baseline recorded — against the
current approved version, never the incident version (that would normalize
the broken behavior; if the fix hasn't shipped, the record says "failing at
baseline — protection pending"). The qualification run is also the
world-sufficiency test: it scopes fixtures per case, so we never claim to
rebuild "their world" — only enough world for the promoted cases, proven by
rehearsal.

### Metric semantics

- Trial passes iff ALL its assertions pass; per-assertion results shown.
- Rate = passing / evaluable trials. Gapped trials excluded from the rate,
  never from the display: "7 pass · 2 fail · 1 gap."
- Timeout taxonomy: no response / error response = **FAIL** (reliability);
  response received but trace unusable = **GAP** (instrumentation). Negative
  assertions never evaluate on an incomplete trace (completeness gate first —
  missing instrumentation can never masquerade as tool_not_called).
- Gap ceiling: >2 gaps out of k → comparison marked "insufficient evidence,"
  no delta claimed. A candidate cannot improve by producing unevaluable
  traces: crashes are fails; excess gaps void the comparison.
- Assertion edit → case version bump → baseline reset → chain records who
  and when. Baseline and candidate always evaluate under the same pinned
  case version.
- Cost, measured: paired mode ≈ 2× single (~$1.50/check at Blitz rates,
  10 cases × k=10). The price of the word "regressed."

### The evidence floor ladder (why anyone can use it)

| Rung | You need | You get |
|---|---|---|
| 4 — full | Laptop-runnable agent + trace store + id passthrough | BOUND paired runs, "regressed," all 8 assertions |
| 3 | Trace store; agent only as staging endpoint | OBSERVED label, all assertions, "moved since last observation" |
| 2 | Just an HTTP endpoint | Output assertions + latency + observed identity, said plainly |
| 1 — floor | Only exported traces | Cases proposed and Promoted; checks wait |

Every setup gets exactly the strength it supports, printed. The record's
sentences match the rung — that is the entire anti-bullshit design.

### Sandbox and world-building stance

The execution substrate is an **ephemeral eval sandbox in the customer's CI**:
GitHub Actions job + their docker-compose (their dev-environment command),
Testcontainers as the documented pattern for dependencies. We build no
sandbox product; wrappers (Dagger, E2B, cloud sandboxes) rejected — adoption
friction or wrong custody. Self-serve qualifier, asked at minute one: **"Can
a new engineer run your agent on a laptop today?"** Yes → BOUND self-serve
(~an afternoon). No → OBSERVED mode, honestly labeled.

World tiers: A (model + read-only tools: hours) · B (own DB/vector store:
compose + seed script, a day, their effort) · C (third-party SaaS tools:
NEEDS-FIXTURE, partner-assisted — where self-serve ends) · D (multi-service
enterprise state: declined in v1, said at onboarding). Incident cases are
world-light by nature — assertions are about the agent's DECISION (call
escalate, don't call approve), which needs the tool boundary reachable, not
the backend real. Verified competitor posture: every horizontal vendor
(Braintrust remote evals, LangSmith pytest path, DeepEval) pushes
world-building onto the customer; only vertical players (Coval: simulated
caller) or internal builds (DoorDash, 6–10 eng-weeks) construct worlds. Our
differentiation is making world-sufficiency VISIBLE per case (qualification
run, tiers, itemized fixtures), not pretending to solve it. Coverage %:
unknown — one data point (Blitz ≈ tier A/B); measured as auto-qualification
rate across first partners, never quoted before then.

---

## 3. Product model

### Objects

| Object | Question it answers | Owner |
|---|---|---|
| Incident Record | What actually went wrong? (trace = fact) | Customer points; Triana preserves |
| Protected Case (six fields) | What behavior must hold, and what does "holds" mean? | Triana proposes; customer defines + Promotes |
| Candidate Surface (connect) | Which traces look like problems worth protecting? | Triana ranks (deterministic); customer points |
| Case Check (k runs) | Does the candidate hold each behavior — at what rate vs baseline? | Customer CI executes; Triana defines protocol + scores |
| Release Identity | What exactly is shipping? (observed composite hash) | Triana observes; scope stated |
| Sign-off | Who accepted shipping, knowing these results? | Customer (PR approving review) |
| Release Evidence Record | What was checked, what happened, who approved — permanent | Triana computes + chains; nobody edits |

### Evidence-class ladder (printed on every record)

| Class | Meaning | Strength |
|---|---|---|
| Deterministic assertion | Action/decision checked mechanically | Fact |
| Judge-scored | Team-written rubric, LLM-scored, marked | Weaker, visible — NOT in v1 checks (see deferred: customer-evaluator route) |
| Customer-evaluator | Result of THEIR eval (their endpoint, their key, their rubric); Triana records, never runs | Their authority, labeled (v1.1) |
| Human-checked | Named person reviewed this release's output | Attestation |
| Observed-production case | Case came from a real trace | Fact-grounded |
| Synthetic-variant case | Grounded persona/behavior permutation (v1.5) | Hypothesis, labeled |

Refusal-then-violation warning (Chime's Response C): "I can't give investment
advice, but Nvidia has been on a tear" must FAIL — naive evaluators reward the
disclaimer. Judge full behavior; label judge-class results honestly.

### Replayability tiers (auto-assigned at case build, one enum — no harness)

| Tier | Condition | Day-1 promise |
|---|---|---|
| READY | Runs in their environment as-is; mechanical-shadow outcome | Fully self-serve |
| NEEDS-FIXTURE | Missing tool responses / candidate diverges from recorded calls | Case exists; waits on customer-supplied mock, itemized |
| NOT-YET | Multi-turn user-conditioned, or trace below contract floor | Stored as incident record + coverage gap |

The services trap is promising every incident becomes a case. V1 claims only
READY. Metric: **auto-qualification rate** — % of real incidents landing in
READY with zero Triana-human minutes.

### Mapping to the earlier five-object model

| Old object | V1 disposition |
|---|---|
| Production Replay Dataset | Shrunk to Protected Case library; grows incrementally |
| Evaluation Registry | Deferred (their eval RESULT formats stay out; their existing golden-set CASES import hand-converted in Phase 3) |
| Execution Runtime | Settled: their CI, their keys, one CLI step |
| Release Policy | Deferred (no verdict; advisory-first by design) |
| Release Decision | Replaced by the Release Evidence Record; verdict = later rendering |

---

## 4. Personas and pitch

| | Solo dev, greenfield | Big team, production agent (ICP) |
|---|---|---|
| Entry door | Dev traces (labeled) + identity from release #1 | Connect → candidates → point at the incident |
| First wow | 6/10 rate on a case they thought solid | Candidate list + incident case with lineage |
| Recurring value | Reliability teammate they don't have | Forwardable proof page + per-release delta |
| Money | Free tier — distribution | Paid records — the business |
| What they teach us | Whether self-serve is truly zero-touch | Time-to-first-record; pay-before-verdict |

Door ① accepts any trace source (prod / staging / dev); the source is labeled
on the record.

### Per-persona demo rule (pitch ordering)

The case builder is a DOOR, never a pitch — case compilation is commoditized
(LangSmith, Confident, Datadog). The paid value is **ritual + rate + identity +
proof**; the case is the unit they operate on.

| Persona | Show first | Builder appears as |
|---|---|---|
| Solo / small team | Connect → candidates → Promote (the magic) | The product itself, initially |
| Enterprise / ICP | A finished Release Evidence Record from a real release | "…and feeding this takes fifteen minutes" |

Four return questions for the "we already compile cases" skeptic:
1. Did your last incident become a check that runs on every release — or a
   paragraph in a postmortem doc? (ritual)
2. When that check passes, does it pass once — or do you know its rate? (rate)
3. Can you say exactly what shipped when it passed — prompts, model, tools, as
   one hash bound to the result? (identity)
4. If a customer asked you to prove the fix was checked before last Thursday's
   release, what would you show them? (proof)

### Pitch language (stolen, verbatim)

- Market's own words (Reddit r/LangChain, unprompted — use everywhere):
  *"I've changed three prompts in the last week and I don't remember which
  changes helped and which hurt."*
- Velocity (Chime): compliance signals "within hours" vs "days or weeks" lost
  at a blocked late gate — evidence accumulates BEFORE the gate, so the gate
  stops being a fight.
- Measurement: "Demos are graded pass@k. Your customers grade you pass^k.
  Triana gates releases on the second one."
- GTM negative (corpus S5 = 0): no frustrated-eval-tool-refugee segment
  exists. Sell to the burned un-evaled with duct-tape guards; never pitch
  eval-stack replacement.

---

## 5. Greenfield build plan (phases, with done-when gates)

Principle: build the PAID loop first, partner-driven; full scan intelligence is
acquisition and comes after the loop works. Milestone M1 — "first real record
on a partner release" — is the company's heartbeat metric.

### Phase 0 — Contracts (the data model IS the product)

| Build | Notes |
|---|---|
| Minimum trace contract | REQUIRED: session_id · ordered events · per-event role/type · tool events carry tool_name + args + result · model output text. OPTIONAL-BUT-UNLOCKS: model id (identity) · prompts (identity) · timestamps (drift, later) · user text (judge-class, later). Each missing optional maps to a named degradation row. Floor known empirically: otel-v1 corpus had no text → 8/13 rows unjudgeable |
| Protected case format | The Chime six fields + replayability tier + evidence class + lineage + approval state |
| Release record schema | Identity hash + scope, per-case rates + baselines, expected/observed/reason per failure, headline finding, evidence classes, sign-off ref, coverage, prev-record hash |
| Hash-chain design | Record hashes contents + previous record; per-customer chain head at a public URL; each page shows own + prev hash; `triana verify` recomputes locally. Sigstore later |
| Assertion vocabulary (closed v1 set, all deterministic, all lift from kairos-ai signals) | `tool_called(name)` · `tool_not_called(name)` · `tool_called_before(a,b)` · `arg_matches(tool, field, rule)` · `no_loop(threshold)` · `no_unbacked_claim(claim_rule)` · `output_matches(regex/schema)` · `terminal_state(no_error)`. A case = trace ref + 1..n assertions. Nothing else in v1 — no shadow → NOT-YET tier |

Done when: all four schemas versioned in repo, round-trip tested, one synthetic
end-to-end record built by hand from a Blitz trace.

Reuse: agentagon trace adapters (v1 / v2 / otel-v1), `langfuse_source.py`,
frozen-labels discipline for anything judge-scored.

### Phase 1 — Doors ①–⑤: connect → surface → point → six-field case → Promote

| Build | Notes |
|---|---|
| Connect/ingest | Read-only Langfuse API + generic JSONL upload; local-CLI ingest mode for privacy-sensitive. One goal-line prompt at connect |
| Candidate surfacing | Deterministic signals — LIFT from kairos-ai (verified working: `action_claim.py` unbacked-claim rules, `ops_recommendations.py` loops/redundancy, `bundle.py` error-terminal/cost/latency). Cross-repo lift, not new build. NOT clustering/coverage map — Phase 4 |
| **Signature dedup wiring (MISSING LINK 1)** | `kairos/memory/signature.py` exists but is DISJOINT from the conversation path — Blitz grouping is flat `groupby(mechanism)`. Conversation strict key v0: `intent_or_demand_family × mechanism × tool_name` (task_shape has no conversation analog; use goal-line + facet label, upgrade when Phase-4 taxonomy lands) |
| **Candidate ranking (MISSING LINK 2)** | Exists NOWHERE today. v0 formula, deliberately dumb and replaceable: `score = log(1+frequency) × severity × blast` — severity: error-terminal/unbacked-claim 3, loop/redundant 2, cost/latency 1; blast: mutating tool touched 2, else 1 |
| Case builder | Proposes six fields + mechanical shadow first; judge-rubric fallback marked; auto-assigns replayability tier. Auto-resolve pattern (called-tools ∩ required-tools, mechanism-gated) lifts from `bundle.py:342` |
| Promote flow | Web door (one trace, one expected behavior, [Promote]) — the approving champion may never touch a terminal. CLI mirror for dev iteration. UI seed: report B's Confirm/Reject widget, now writing into a real library instead of the void |

Done when: a real Blitz or hr_agent incident goes connect → point → Promote in
under 15 minutes end to end; a 10k+ trace window compresses to a one-screen
proposal list with zero Triana-human minutes.

Reuse reality (verified 2026-07-29): the working pipeline lives in
**kairos-ai** (`src/kairos/analysis/`, `conversation_console/`), NOT agentagon.
agentagon only scrapes the Blitz HTML back out (`experiments/blitz_seed/
breadth_eval.py`). agentagon's own redundancy signal is LLM-judged
(`signals/sequence.py`) — the OPPOSITE of the Blitz deterministic path. Pick
the deterministic implementation; reconcile or retire the divergent one.

### Phase 2 — Door ⑥: `triana check`

| Build | Notes |
|---|---|
| Runner CLI + GitHub Action wrapper | Implements the §2b 7-step contract. Default mode: CI boots BOTH baseline (merge-base) and candidate from exact checkouts, SHA-attested, paired in one job. Fallback: external staging endpoint → OBSERVED mode, mechanically labeled. Replay unit = the case's recorded input via the declared request template — single-turn by construction (multi-turn = NOT-YET tier). k default 5–10, per-case override. Marketed as "add this Action," never "install our tool" |
| Identity | SHA attestation (env → root trace metadata / `/version`) + observed components (model id, prompts, tools from the run's traces). Expected-vs-attested compared; scope printed. No attestation → OBSERVED, stated |
| Rate scoring | Paired mode: baseline computed fresh in the same job → "regressed" permitted (drop ≥3/k red; 1–2/k "moved, small n" amber; k<5 always amber; >2/k gaps voids). Cross-time mode: compare to last default-branch record → strongest language is "moved since previous observation." Three numbers always: pass/evaluable · end-to-end · gaps |
| Result upload | Results + identity up; raw traces may stay local |

Done when: on hr_agent, the codefix PR produces case rates against baseline in
one CI step; wall-clock and cost measured.

Reuse: hr_agent demo Action skeleton (`run_gate.py` shape), NATIVE_SIGNAL
deterministic executor.

### Milestone M0 — the loop closed on our own agent, PUBLIC (between Phases 2 and 3)

Before any design partner: run the entire 7-step contract on **hr_agent** —
public reference repo containing the agent, the workflow, the 15-line config,
3 protected cases as readable files, a real PR where a real change degrades a
case, and the resulting evidence record with chain verifiable. Plus a short
honest write-up: "we gated our own agent; here is every wart" — gaps, amber
labels, OBSERVED-vs-BOUND, the claims we refused to make. The repo is a
**template**: fork, swap the agent, keep the workflow — real utility with
zero sales contact (pairs with the one-case-free tier). Seasoned developers
trust a repo they can clone and numbers they can regenerate; M0 is the
anti-bullshit artifact, and it de-risks M1 by surviving our own teardown
first.

**Open-source decision (agreed in principle):** MIT the small frozen core —
case schema, 8-assertion evaluator, check protocol, record schema + language
gates (~small, fully unit-testable, nothing speculative). Hosted chain
service, evidence pages, and surfacing-at-scale stay the product. Langfuse
playbook: give away the commodity layer, own the record.

### Phase 3 — Doors ⑦⑧⑨: the record, the PR comment, the page  → M1

| Build | Notes |
|---|---|
| Record service | Binds check output + sign-off ref; headline finding computed (named risk, threshold-colored, never a neutral table); appends to hash chain; immutable store |
| Evidence page | One hosted page per record; permanent URL; tamper-evident; forwardable. THE ONLY SURFACE — no dashboard |
| GitHub App/Action | PR comment with headline + link. Sign-off binding: most recent APPROVED review on the PR head SHA at merge time; none (force/admin merge) → record states "merged without approving review" (a feature); multiple → all listed, last highlighted. Advisory only |
| Existing-case import (per-partner, manual) | "Point us at your golden set; we wrap it in rates + identity + records." Hand-convert for design partners; no generic importer |
| Override seed | When a human overrides a check result, record which component the override indicts: agent / case / judge / definition (Chime's four repair paths — one enum, not a flywheel) |

Done when (= MILESTONE M1): a design partner's real agent PR carries a record;
time-to-first-record measured (<2 days target — kill criterion at "weeks").

Reuse: Triana demo `DESIGN_CONTRACT.md` visual language for the page.

### Phase 4 — Full scan intelligence (acquisition)

| Build | Notes |
|---|---|
| Coverage map | Behavior clustering + traffic %, confirmed production failures (never "regressions" without baseline), unprotected behaviors, empty behavior×persona cells SHOWN not filled (v1.5 sells the fill) |
| Self-serve packaging | `triana scan` local mode + web upload; every proposal pre-fills door ④ |
| Internal benchmark (IssueBench pattern) | Frozen synthetic-injection benchmark for our own surfacing/builder: hidden known issues, no-issue class scored, grouping quality scored, cross-corpus (Blitz / HR-AI / ABCD) generalization. Embryo = V0 spec's validation experiment |

Done when: a cold prospect goes connect/export → first proposed case in under
30 minutes without talking to us; benchmark scores the surfacing engine.

Reuse: the two Blitz reports ARE the Phase-4 prototypes, already run on a real
partner's 624 conversations — report A (founder demo): 8 demand clusters +
handling mix + A/A–A/B paired-diff plumbing smoke; report B ("the self-serve
floor"): deterministic ops floor + TnT-LLM facet taxonomy
(`kairos-ai/src/kairos/discovery/taxonomy.py`, replaced the HDBSCAN clio path
which blobbed short chats) + L4 mechanism audit with Confirm/Reject. Caveats
carried forward: taxonomy sample size was a human CLI `--limit`, not a
principled sampler (fix when productizing); frustration facet stays a
selection signal, never a truth label (deterministic gate at
`pipeline.py:84-88` already enforces this); report A is a hand-authored
template with drift tripwires, not a generator — not pipeline evidence.

### Phase 5 — Deal wiring + validation ops

| Build | Notes |
|---|---|
| Free/paid split | ①–⑤ + scan free, PLUS checks + records on ONE protected case forever-free (they feel the full loop before paying). Paid: records beyond the first case. Pilot anchor: **$500/mo flat, 60–90 days, unlimited records** — tests willingness-to-pay-at-all; per-release pricing explored after |
| Partner onboarding | Named: **Blitz** (corpus in hand) · **Coreworks** · **Risa/Ashutosh** (hardest test — has harness) · **Priyanshu's team** (Raindrop traces) · +1 slot from interviews. The 10 non-leading interview questions run in parallel from day 1 |
| Instrumentation | Time-to-first-record, records per release, coverage growth, auto-qualification rate, forward events (page shared) |

Done when: 2+ partners with records on 3+ releases each; first payment
conversation held with a real number.

---

## 5b. Delivery surfaces (friction map)

Principle: the only unavoidable install is one YAML block. Zero-code install
for execution; everything else in the browser. Execution in their CI is not
friction to remove — it IS the privacy/credentials story.

| Door | Surface | Install required |
|---|---|---|
| ①–⑤ connect + point + Promote | Web UI first; CLI mirror | None (read-only API key) / local-CLI ingest for privacy |
| ⑥ `triana check` | GitHub Action wrapping the CLI (`uses: triana/check@v1`); bare CLI for non-GitHub CI | ~6 lines of YAML, zero agent-code changes |
| ⑧ PR comment | GitHub App authorization | Click-through |
| ⑨ evidence page | Hosted URL | None |
| Phase-4 scan | Web upload / local CLI | None / one `pipx run` |

---

## 6. Explicitly OUT of v1 (deferred, with triggers)

| Deferred | Trigger to build |
|---|---|
| PASS/REVIEW/BLOCK verdict | Partners ask (the record's job is to provoke that ask); rendered from existing records in weeks |
| Their eval RESULT formats | Post-M1, per-partner pull (their CASES already import in Phase 3) |
| `triana.yml` multi-evaluator orchestration | Release two of a paying partner |
| Customer-evaluator route (case declares THEIR eval endpoint; we record its result as `customer-evaluator` class — we never run judges, never own ground truth) | v1.1 — first partner with an incident that has no mechanical shadow. This is how "import your evals" becomes literally true |
| Replay harness / cassette auto-mocks | A paying partner's real cases demand it |
| Grounded expansion (behavior×persona fill) | v1.5 — sold via the empty cells the Phase-4 scan shows; needs curation machinery first |
| Multi-turn replay / user simulation | With expansion; fidelity ceiling acknowledged ("Lost in Simulation") |
| Declared-component identity | Hybrid with observed once drift bites |
| Separate `/triana approve` sign-off | First non-engineer stakeholder (PR-approval reuse = KNOWN DILUTION: attests code approval, not risk acceptance) |
| Risk-weighted review queue (Anterior) | Scan proposes more cases than a team reviews in one sitting |
| Validate-the-validator ledger + random audits (Anterior) | Judge-class cases exist in volume |
| Release-specific case selection (Anterior) | Case library > ~20 |
| Post-release decision validation (Anterior) | Verdicts exist to validate |
| Taxonomy / altitude roll-up (Chime) | First non-engineer stakeholder at a partner |
| Legal-authored definitions as second entry door (Chime) | First regulated design partner — potentially the bigger wedge there |
| LangSmith Engine issue-cards as inlet | Post-M1 — their discovery feeds our door ④ |
| MCP server (create cases / query records from Claude Code, Cursor) | After M1 — cheapest acquisition surface once records exist to query |
| Dashboards | Never, if we can help it — the page is the surface |
| SDK | NEVER — re-instrumentation is objection #1; SDK lock-in is competitors' moat, neutrality is ours |

---

## 7. Kill criteria and validation tests (90 days, from the market research)

| Test | Failure looks like |
|---|---|
| 10+ non-leading interviews | Nobody describes pain between "evals ran" and "we shipped"; DIY glue "good enough" |
| Time-to-first-record on 3 teams with custom harnesses | Weeks, not <2 days → services trap |
| Auto-qualification rate on real incidents | Well under ~1/3 land READY with zero Triana-human minutes → consulting wearing a CLI |
| Shadow period on real releases | No partner asks to make it blocking after 30 days advisory |
| Pay-before-verdict | Nobody pays for records without a verdict → verdict pulls forward |
| Incumbent watch | Braintrust/LangSmith ship policy object + evidence record with a named gating customer |

**Open-threads ledger + mom-test question bank live in Notion** ("Wedge V1 —
Open Threads Ledger + Design Partner Question Bank", Triana database,
created 2026-07-29): ten open threads (world-tier distribution is the biggest
unknown), each mapped to the partner question that resolves it. Standing
convention: every unresolved design thread from working sessions gets a row
there — facts from partners over reasoning from us. Design debate is closed
(six contract decisions + the 7-step contract); what remains is measurement.

**M1 acceptance test (the two design-partner questions, verbatim):**
1. Given one real production incident and your existing staging setup, can
   Triana — without changing your agent code — produce a candidate execution
   trace, evaluate an assertion you trust, and attach the result to your next
   real PR?
2. If it can: is that result different enough from what your existing
   observability/eval stack gives you that you would keep it on every release?
A yes/no split between them is the feature-not-company verdict, learned for
the price of one pilot.

Validation experiment (inherited from self-serve V0 spec, still binding):
bounded historical window, 2–3 known issues hidden, blind generation, engineer
reviews every case. Success = at least one previously-missing case approved AND
committed to a real release. Interest and positive language do not count.

Build-vs-buy honesty: Chime, Anterior, Ramp, DoorDash built these loops
internally on existing tools. That proves the WORKFLOW, not the purchase — the
Chime doc itself lists what it doesn't prove ("that teams will buy a separate
release-intelligence product"). Exactly what the pay-before-verdict test exists
to answer.

---

## 8. Known dilutions and open questions (stated, not hidden)

1. PR-approval-as-sign-off attests code approval, not risk acceptance (upgrade
   path scheduled in deferred).
2. Identity: SHA attestation covers the code ref; observed components cover
   only what the cases exercise; scope printed on every record. "One line"
   integration claim RETRACTED — replaced by the declared request template
   (visible, testable, minutes not zero).
3. Case fails and they ship anyway → the record says so, approver named.
   Feature, not bug — but partners must be told before it happens.
4. Judgment-based fixes: mechanical shadow first; judge-scored marked; human-
   checked as the honest maximum. Triana never invents ground truth.
5. k-run compute lands on the customer's CI bill — measured on Blitz:
   $4.66/624 ≈ $0.007 per conversation → 10 cases × k=10 ≈ **$0.75 per check
   run**. Re-cost before the library passes ~20 cases.
6. Read-only connect means trace data touches us — or local mode: ingest +
   surfacing + case build run entirely on their machine; only Promoted case
   definitions, check results, and record hashes go up. That sentence IS the
   privacy contract. The ICP hands read keys to observability vendors
   routinely; the privacy-sensitive get the local path.
7. Records without verdicts must still change behavior: the headline finding
   (named risk, threshold-colored) keeps the record one notch below a verdict —
   never a neutral table. Payment without a verdict is unproven and explicitly
   under test.

---

## 9. Code reality inventory (verified against source, 2026-07-29)

Claim-by-claim verification of the surfacing/compression stack. "kairos-ai" =
`/Users/akarshgajbhiye/kairos-ai`.

| Capability | Status | Where | LLM or deterministic |
|---|---|---|---|
| Unbacked action claims (regex claim-rules vs tool calls) | VERIFIED — Blitz 4/624 computed | kairos-ai `analysis/action_claim.py:100`, rules `:141` | Deterministic, tested |
| Loop / redundant-call detection | VERIFIED — 74/624, 370/624 computed | kairos-ai `analysis/ops_recommendations.py:216` | Deterministic |
| Error-terminal, cost, latency, cache, tokens | VERIFIED — 19/624, $4.66 etc. computed | kairos-ai `conversation_console/bundle.py:287,306` | Deterministic |
| Facet-then-cluster taxonomy (TnT-LLM) | VERIFIED — intent/issue/frustration_cause | kairos-ai `discovery/taxonomy.py` | LLM + deterministic purity gate + frustration gate |
| L4 mechanism audit + auto-resolve | VERIFIED — 29→28 auto-resolved is a coded rule, mechanism-gated | kairos-ai `analysis/conversation_l4.py:209`, `bundle.py:342,37` | LLM audit, deterministic resolve |
| Report generator (blitz-triana.html) | VERIFIED — fully data-driven, no hardcoded stats, inspectability assert | kairos-ai `views/console.py`, `bundle.py:398` | Deterministic render |
| Signature dedup on conversation path | **NOT IN CODE** — signature machinery exists (`memory/signature.py`) but conversation console never imports it; grouping is flat `groupby(mechanism)` | — | Missing link 1 |
| frequency × severity × blast-radius ranking | **NOT IN CODE anywhere** — severity today is frequency-only per metric; render order hardcoded | — | Missing link 2 |
| Founder-demo report A | Hand-authored template + drift tripwires (`build_portable_full_trace_report.mjs` asserts 370/281/12/624, computes nothing else) | agentagon `experiments/founder_demo/` | Not pipeline evidence |

**Defects found during verification (fix during the lift, they are
measurement-integrity bugs in our own shop window):**
1. Two contradictory loop definitions ship in the same Blitz HTML — Home table
   `loop_convos: 0` (per-envelope) vs fix list 74/624 (cross-envelope,
   ≥3 same tool). One metric, two answers, one page.
2. `action_claim.py` docstring claims 32% unbacked-claim rate; shipped bundle
   computes 0.6%. Stale hand-written prose beside correct code.
3. agentagon and kairos-ai implement the same redundancy signal divergently
   (LLM-judged vs deterministic). Converge on the deterministic one.

---

## 10. trytriana.com alignment

| Landing today | V1 reality | Action |
|---|---|---|
| "Know what this release breaks" hero | Record with rates vs baseline | Keep |
| Release Memory | The protected case library, same object | Keep the name |
| PR #181 evidence report at `/app/` | The evidence page IS the paid artifact | Promote from demo to hero artifact |
| PASS/REVIEW/BLOCK + Release Control present-tense | No verdict in v1 (advisory headline finding) | Demote verdict to earned roadmap ("becomes enforceable when you're ready") |
| "3 confirmed regressions" | No baseline = not a regression claim | Change to "confirmed production failures" |
