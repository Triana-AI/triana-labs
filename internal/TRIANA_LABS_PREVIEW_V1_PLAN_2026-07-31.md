# Triana Labs Preview v1 — implementation plan (v3)

Date: 2026-07-31 (v3 — after two internal adversarial reviews + Codex
cross-model pass, ~42 findings reconciled, and Akarsh's scope rulings)
Status: active accepted plan under `triana-labs/CHARTER.md`

## Narrative

Frozen in the charter. Not repeated here.

## Akarsh's scope rulings (2026-07-31)

1. Fresh HRAI reruns are authorized and self-triggered (OpenRouter or
   equivalent provider, operator keys, metered).
2. **User simulation is in scope.** The next-turn generator is the core
   intelligence layer, not a deferral.
3. Distress/persona grounding mined from blitz data (agentagon/HRAI/Kairos-AI
   references), supplemented by ABCD/tau-bench or generated corpora, all
   fidelity-labeled.
4. UI adaptation is not treated as a blocker.
5. Canonical conflict fixed: `docs/PRODUCT.md` suspended, charter created.
6. Outcome/stability machinery acknowledged as the one real open blocker.

## Fixed positions

1. **Divergence-first.** Primary report surface is the per-case stable flip.
   Aggregates are context beside observed baseline variation, never verdicts.
2. **Comparison depth is tiered by fidelity, and labeled:**
   - Tier F0 — shared-prefix resampling, first divergent action: both arms
     receive the same historical prefix and execute freshly; the strongest
     supported claim is the first observed divergence under shared context.
   - Tier F1 — continuation past divergence driven by the **next-turn
     generator**: simulated claim, labeled, never conflated with F0.
   Multi-turn comparison ships; it just cannot borrow frozen-replay
   authority.
3. **Next-turn generator contract.** Inputs: full corpus clusters, persona
   files, intent files, scenario truth, conversation so far. Output: the most
   realistic next user turn. Derived assets (personas, intents, turn
   policies) are generated from the customer's own trace corpus — this
   derivation step is a shipped component, not manual authoring.
4. **Diversity control.** Trajectory-similarity measurement across the panel;
   duplicate-converging runs are detected, deduplicated or down-weighted, and
   the report states effective distinct-trajectory count next to raw N.
5. **Reference behavior, direction-aware:** the baseline is reference
   behavior, not automatically accepted behavior. It is accepted only where
   a human ruling or explicit acceptance evidence says so. A case carrying
   confirmed failure evidence marks the baseline `KNOWN_FAILURE`; divergence
   then defaults to a candidate-improvement candidate, not a verdict.
   Invariant hits are high-priority flags, human-confirmed into rulings —
   never verdicts in the report's own voice.
6. **Honest denominators.** Paired claims from two-sided intersections only;
   gaps/non-comparable/unstable reported separately; per-arm totals never
   mixed with paired deltas; panels under 30 cases show counts, not
   percentages.
7. **Local-first, precisely stated:** nothing is sent to Triana. Redaction
   and egress validation are fail-closed and run before identity hashing and
   before trace content is sent to any model provider. Customer-held keys do
   not imply authorization: configuration or consent must name the provider
   and permitted egress.
8. **No rerun-to-green.** Machinery acceptance on constructed nondeterministic
   fixtures; real-data milestones pass by reporting honestly.

## Outcome and stability machinery (v3 — accepted 2026-07-31)

**Execution validity comes first.** Each trial is classified before any
comparison: `valid` (agent-origin behavior observed) or `invalid` with a
typed cause (timeout, provider failure, harness failure, malformed trace).
Invalid trials enter gap denominators only; they never form outcomes. A
terminal-status "flip" caused by rate limits is a gap, not a finding.

**Outcome of a case** = typed record over valid trials:

```text
outcome := (
  commitment,           # field_state[domain-observable terminal action]
  terminal_status,      # completed / abandoned (agent-origin only)
  tool_name_sequence,   # ordered, duplicates preserved, exact equality
  declared_projection,  # field_state[case-specific human-declared observable]
)

field_state[T] := NOT_APPLICABLE | MISSING | PRESENT(T)
```

- Every applicable field is compared and every changed field is retained in
  the report. Precedence (declared_projection ≥ commitment > terminal_status
  > tool_name_sequence) ranks the *primary display reason only* — it never
  suppresses lower-field changes.
- `NOT_APPLICABLE` skips that field and comparison continues to the next
  applicable field. `MISSING` means a required observation was absent: the
  case is reported as `outcome evidence incomplete` at that field, with
  lower fields retained as partial observations only. `PRESENT(value)` is
  compared normally. Mechanical fields matching is reported as "no change
  detected in observed fields" — never "unchanged behavior."
- turn count and cost/latency move to aggregate context measures; they are
  not outcome fields.

**Tier-1 stable flip** (k=3 per arm), stated in pass^k/pass@k semantics
(Akarsh, 2026-07-31; consistent with the 07-29 wedge decision "pass^k not
pass@k"): baseline achieves **pass^3** on outcome value O1 *at the field
level under test*, candidate achieves **pass^3** on O2, and O1 ≠ O2 — two
reliability claims pointing at different behaviors. Stability is judged per
field — harmless tool-order variation cannot destabilize a unanimous
commitment change. Candidate failing pass^3 while the new behavior appears
at **pass@3** is reported as a **reliability regression/change** on the
weak-evidence shelf ("baseline reliably A; candidate only sometimes A"),
with trial counts — its own report section, never tier 1. Rationale: under a
90/10 A/A outcome distribution, a 2-of-3 rule fabricates ~11 false tier-1
findings per 200 cases; pass^3-vs-pass^3 fabricates ~0.1. Fewer than three
valid trials on either side → `insufficient trials`, a gap. Report rows
print the semantics explicitly ("pass^3 both arms").

**Standing DIY-agent benchmark (Akarsh, 2026-07-31).** Recurring success
criterion for the tool itself: hand the raw job — two trace sets, "what
changed?" — to a frontier coding agent (Claude Code or Codex) with no
Triana. If the agent's answer matches the report's useful findings, the diff
engine is commodity and the tool must improve where the agent structurally
loses: reproducible k-trial execution, correct pass^k stability math,
honest denominators, persistent rulings across runs, identical answers on
identical inputs, and cost. Run this benchmark at every milestone exit;
failure to beat the DIY agent on those axes is a kill signal, not a
positioning problem.

**Divergence localization is separate from outcome classification.** Both
arms' event sequences are aligned on the shared recorded prefix; the
divergence point is the first unequal aligned event (event type, role, tool
name, normalized consequential arguments, explicit observation gaps).
Terminal fields say *whether* behavior changed; the aligned sequence says
*where*.

**Comparability = closed execution fingerprint.** Case/prefix hash, fixture
content hash, reset policy, tool/world contract version, simulator and
derived-asset (persona/intent file) versions, randomization policy, runtime
identities. Any undeclared fingerprint difference between arms →
`non-comparable` (kernel `MOVED` semantics), never a divergence.

**Observed baseline variation, deterministic rule:** numeric aggregates are
computed per trial index over one fixed two-sided case intersection; the
baseline's per-index value range is reported as observed baseline variation,
not as a statistical noise estimate. Candidate aggregate movement inside that
range is `inside observed baseline variation`. Categorical measures get no
aggregate variation label — they are covered by the per-case 3/3 rule. The
report states how many measures were tested.

Codex findings 1–13 reconciled: all four blockers and nine majors accepted
with the fixes above; no finding rejected. Full transcript:
scratchpad `codex-outcome-review.txt` (session-local).

## Pipeline

```text
Stage 0  Data: fresh HRAI runs — baseline ×k, candidate ×k, current exporter
         (tool results, per-call latency), spend-capped, self-triggered
Stage 1  Understand: cluster corpus → derive personas, intents, turn
         policies, accepted-behavior envelope, incident anchors; mine blitz
         corpus for distress vocabulary and realism grounding
Stage 2  Panel: stratified selection + change-declaration weighting +
         scenario truth extraction; diversity budget declared
Stage 3  Run: F0 shared-prefix resampling; on divergence, F1 continuation via
         next-turn generator; k trials; dedup/diversity check across runs
Stage 4  Report: tiers (stable flips on failure evidence → improvements →
         high-magnitude diffs) · demoted (inside observed baseline variation,
         unstable) · gaps ·
         fidelity badges (F0/F1/generated-corpus) · label pass →
         promotion draft → human completes ProtectedCase
```

## Components

| # | Component | Notes | Milestone |
|---|---|---|---|
| 0 | Demo dataset | Fresh HRAI runs via OpenRouter-compatible route; k=3 per arm; redacted; spend cap default USD 50/panel until Akarsh sets one | M0 |
| 1 | PreviewTrace + adapter contract | New Labs document kind (case_id, trial_index, arm, events); built on triana-core canonicalization/hashing; frozen V1 contracts untouched; public JSONL/OTel-shaped adapter plus explicit baseline/candidate command or endpoint contract; HRAI is the first converter, not the product boundary | M1–M3.5 |
| 2 | Corpus understanding | Clustering (explainable rules first), persona/intent/turn-policy derivation, envelope, anchors; blitz distress mining (fidelity-labeled) | M1 |
| 3 | Diff engine | Pairing, outcome tuples, stability, observed baseline variation, alignment, tiers — per accepted machinery spec | M2 |
| 4 | Next-turn generator | Prompted generator over derived personas/intents + scenario truth; diversity measurement + dedup; per-turn cost metering | M2 |
| 5 | Report | Divergence-first snapshot schema (tiers, gaps, lineage, fidelity, denominators); verdict logic replaced (no SHIP/BLOCK language); two adapted triana-demo screens (diff page + paired-transcript overlay) | M3 |
| 6 | Redaction + egress validation | Fail-closed before hashing and before any model-provider call; provider and permitted trace egress must be explicit; verified before anything public | M3 |
| 7 | Runner | Subprocess contract, k trials, timeouts, gap rows; nondeterministic stub fixture with configured flip rates | M3 |
| 8 | Label store + promotion | Identity = (case lineage, divergence class); versioned; promotion emits a ProtectedCase *draft* the human completes | M4 |
| 9 | CLI + config | `triana-labs preview` entrypoints; one YAML; versioned on-disk formats | M1–M4 |

## Milestones

- **M0** — three-arm fresh dataset exists on current schema; baseline
  self-agreement measured; redaction sample verified.
- **M1** — PreviewTrace + corpus understanding: personas/intents/turn
  policies derived from the 200-case corpus and inspectable as files; blitz
  mining report with fidelity labels.
- **M2** — diff engine passes the constructed-fixture suite (flip detection at
  configured rates, denominator honesty, inside-observed-baseline-variation
  demotion); next-turn generator produces continuations judged realistic on a
  hand-checked sample of 30, with duplicate-trajectory rate below the declared
  budget.
- **M3** — end-to-end honest report on the M0 dataset renders in the adapted
  UI from `make demo`; every claim carries its fidelity badge; public-ready
  after redaction gate.
- **M3.5 — stranger installation.** One developer who did not build Triana
  installs the public repository, supplies a trace export, configures a
  baseline and candidate, and produces an honest report in under 90 minutes.
  The integration requires no more than 200 adapter lines (target: 100), the
  report identifies either a useful difference or an honest no-difference,
  and the developer answers whether they would use it on another release.
  Failure blocks M4 and triggers a scope or installation-contract correction,
  not bespoke founder integration.
- **M4** — label once, rerun with changed candidate: prior rulings
  auto-apply, only new divergence classes surface; promotion drafts
  well-formed.

## Non-goals (v1)

Hosted anything; eval-suite import; automatic change→impact inference;
production-incidence prediction; live/side-effectful tool execution
(simulated continuation covers the user side, not the world side — tool
results in F1 come from recorded/stubbed contracts); refusal/semantic text
classification in Layer 0; SHIP/BLOCK verdict language; Guard; Learn.

## Risks (owned)

1. Fresh runs may weaken the demo regression — story follows honest data
   (M0 exit review).
2. Next-turn generator realism may be poor on first pass — M2's 30-sample
   hand check is the gate; failure narrows F1 claims, not the ship date.
3. F1 world-side fidelity (frozen tool results under simulated continuation)
   is the known weakest link — labeled, and candidate actions that exceed
   recorded tool coverage classify as gaps.
4. Blitz corpus may prove unusable for distress mining — fallback: ABCD /
   tau-bench / generated-with-label.
5. UI adaptation overrun — timebox, fall back to server-rendered static HTML.
