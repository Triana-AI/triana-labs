# Triana Labs charter

Date: 2026-07-31
Status: **active build authority for Triana Labs surfaces**
Owner: Akarsh

## What this document is

The governing specification for Triana Labs work. It exists because the
suspended V1 specification (`docs/PRODUCT.md`) and Labs cannot share one
frozen boundary. Precedence for Labs work: this charter → the append-only
`internal/DECISION_LOG.md` → the current plan
(`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`). Repository governance
(`AGENTS.md`, provenance ledger, decision-memory hooks) applies unchanged.

## Narrative (owner-frozen)

> Triana Preview takes your production traces, learns accepted agent behavior
> and user-signaled failures from them, builds a case panel that mixes real
> replay with grounded expansion, runs your baseline and candidate on the same
> panel, and reports ranked divergences — including behaviors your evals never
> covered — with every claim backed by a paired transcript and every
> non-claim labeled. Confirmed findings become must-checks for the next run.

## Scope decisions (Akarsh, 2026-07-31)

1. **User simulation is in scope.** The core intelligence layer is the
   **next-turn generator**: read the historical trace corpus, cluster how
   users actually behave, derive persona and intent files from those
   clusters, and generate the most realistic next user turn when a candidate
   diverges from the recording. Multi-turn comparison is a goal, not a
   deferral.
2. **Diversity control is a first-class requirement.** Independent simulated
   runs must not silently converge on duplicate trajectories. The panel and
   the generator must measure and bound trajectory duplication so N runs
   represent N distinct situations.
3. **Provider: OpenRouter (or equivalent API provider) with the operator's
   keys.** Customer deployments use customer keys. Spend is metered and
   capped per panel.
4. **Real-user grounding comes from mined corpora.** Blitz data (Akarsh's
   own, referenced in agentagon/HRAI/Kairos-AI) is the primary mining target
   for distress markers and persona realism; public corpora (ABCD, tau-bench)
   are acceptable supplements; generated corpora are acceptable when labeled
   as such. Fidelity labels on every derived asset.
5. **Open-source distribution** after the redaction and provenance checks
   pass. Local-first: customer traces go only to model providers the
   customer already uses, under customer keys; nothing is sent to Triana.
6. **The Slice 0A kernel (`triana-core/`) is shared infrastructure.** Labs
   defines its own document kinds (e.g. PreviewTrace) using the kernel's
   canonicalization and hashing; the five frozen V1 contracts are not
   modified.

## Evidence rules (carried over from repository discipline)

- Divergence-first reporting; verdict language never replaces the human.
- Universal-invariant hits are high-priority flags, not verdicts; a human
  confirmation converts a flag class into a persistent ruling.
- Baseline is accepted behavior **except** on cases carrying failure
  evidence, where divergence defaults to candidate-improvement-candidate.
- Explicit denominators; paired claims only from two-sided intersections;
  gaps, non-comparable, and unstable cases reported separately, never folded
  into scores.
- No rerun-to-green: machinery acceptance is proven on constructed
  nondeterministic fixtures; real-data milestones pass by reporting honestly,
  whatever the data shows.
- Fidelity badge on every report: frozen replay, simulated continuation, and
  generated-corpus evidence are labeled and never conflated.

## Open blocker (owner-acknowledged)

**Outcome and stability machinery is undesigned.** What counts as a case's
outcome, what makes a flip stable, and how noise bands are derived at small n
have no accepted specification yet. This is the single design blocker before
implementation; the current proposal lives in the plan and must be accepted
or amended by Akarsh before the diff engine is built.

## Relationship to suspended V1

V1 (`docs/PRODUCT.md`) is suspended, not deleted. Its incident→ProtectedCase
loop survives inside Labs as the must-check promotion path. Resuming V1 or
merging it with Labs requires an explicit decision-log entry.
