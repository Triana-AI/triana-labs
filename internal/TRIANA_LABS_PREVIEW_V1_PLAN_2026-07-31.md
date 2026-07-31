# Triana Labs Preview v1 — implementation plan (v3)

Date: 2026-07-31 (v3 — after two internal adversarial reviews + Codex
cross-model pass, ~42 findings reconciled, and Akarsh's scope rulings)
Status: active plan under `triana-labs/CHARTER.md`
Open blocker: outcome/stability machinery (section below) — needs Akarsh's
acceptance before the diff engine is built

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

1. **Divergence-first.** Primary verdict surface is the per-case stable flip.
   Aggregates are context beside measured noise, never verdicts.
2. **Comparison depth is tiered by fidelity, and labeled:**
   - Tier F0 — shared prefix, first divergent action: frozen replay,
     strongest claim.
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
5. **Ground truth, direction-aware:** baseline = accepted behavior except on
   cases carrying failure evidence (incident anchors, confirmed invariant
   hits), where divergence defaults to candidate-improvement-candidate.
   Invariant hits are high-priority flags, human-confirmed into rulings —
   never verdicts in the report's own voice.
6. **Honest denominators.** Paired claims from two-sided intersections only;
   gaps/non-comparable/unstable reported separately; per-arm totals never
   mixed with paired deltas; panels under 30 cases show counts, not
   percentages.
7. **Local-first, precisely stated:** customer traces go only to model
   providers the customer already uses, under customer keys; nothing to
   Triana. Redaction is fail-closed and runs before identity hashing.
8. **No rerun-to-green.** Machinery acceptance on constructed nondeterministic
   fixtures; real-data milestones pass by reporting honestly.

## OPEN BLOCKER — outcome and stability machinery (proposal, not accepted)

**Outcome of a case** = typed tuple, compared field-by-field with declared
precedence:

```text
outcome := (
  terminal_status,        # completed / errored / abandoned
  commitment,             # domain-observable terminal action if the trace
                          # declares one (e.g. persisted decision), else ⊥
  tool_signature,         # ordered multiset of tool names, args excluded
  turn_count_band,        # bucketed, not exact
)
```

Precedence for "the outcome changed": commitment > terminal_status >
tool_signature > turn_count_band. A field marked ⊥ on either side is not
compared (gap, not diff).

**Stable flip** (k trials per arm, k≥3): candidate outcome differs from the
*baseline modal outcome* in ≥⌈2k/3⌉ candidate trials, AND baseline agrees
with its own modal outcome in ≥⌈2k/3⌉ baseline trials. Baseline
self-disagreement → case labeled `unstable`, excluded from tier 1.

**Noise floor**: derived from baseline trial self-agreement per measure (not
from one A/A realization). Aggregate deltas smaller than the cross-trial
spread on the same measure are demoted `inside noise`. Multiple-comparison
honesty: the report states how many measures were tested.

**First-divergence alignment**: events aligned on the shared recorded prefix;
divergence = first position where the compared outcome fields differ;
execution-contract mismatches (different fixtures, seeds, schema) classify
the case `non-comparable` (kernel `MOVED` semantics), never as divergence.

Akarsh accepts, amends, or replaces this before component 3 is built.

## Pipeline

```text
Stage 0  Data: fresh HRAI runs — baseline ×k, candidate ×k, current exporter
         (tool results, per-call latency), spend-capped, self-triggered
Stage 1  Understand: cluster corpus → derive personas, intents, turn
         policies, accepted-behavior envelope, incident anchors; mine blitz
         corpus for distress vocabulary and realism grounding
Stage 2  Panel: stratified selection + change-declaration weighting +
         scenario truth extraction; diversity budget declared
Stage 3  Run: F0 shared-prefix comparison; on divergence, F1 continuation via
         next-turn generator; k trials; dedup/diversity check across runs
Stage 4  Report: tiers (stable flips on failure evidence → improvements →
         high-magnitude diffs) · demoted (inside-noise, unstable) · gaps ·
         fidelity badges (F0/F1/generated-corpus) · label pass →
         promotion draft → human completes ProtectedCase
```

## Components

| # | Component | Notes | Milestone |
|---|---|---|---|
| 0 | Demo dataset | Fresh HRAI runs via OpenRouter-compatible route; k=3 per arm; redacted; spend cap default USD 50/panel until Akarsh sets one | M0 |
| 1 | PreviewTrace contract | New Labs document kind (case_id, trial_index, arm, events); built on triana-core canonicalization/hashing; frozen V1 contracts untouched; HRAI converter | M1 |
| 2 | Corpus understanding | Clustering (explainable rules first), persona/intent/turn-policy derivation, envelope, anchors; blitz distress mining (fidelity-labeled) | M1 |
| 3 | Diff engine | Pairing, outcome tuples, stability, noise floor, alignment, tiers — per accepted machinery spec | M2 |
| 4 | Next-turn generator | Prompted generator over derived personas/intents + scenario truth; diversity measurement + dedup; per-turn cost metering | M2 |
| 5 | Report | Divergence-first snapshot schema (tiers, gaps, lineage, fidelity, denominators); verdict logic replaced (no SHIP/BLOCK language); two adapted triana-demo screens (diff page + paired-transcript overlay) | M3 |
| 6 | Redaction | Fail-closed, pre-hashing; verified before anything public | M3 |
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
  configured rates, denominator honesty, inside-noise demotion); next-turn
  generator produces continuations judged realistic on a hand-checked sample
  of 30, with duplicate-trajectory rate below the declared budget.
- **M3** — end-to-end honest report on the M0 dataset renders in the adapted
  UI from `make demo`; every claim carries its fidelity badge; public-ready
  after redaction gate.
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
