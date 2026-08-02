# Triana Labs charter

Date: 2026-07-31
Status: **active build authority for Triana Labs surfaces**
Owner: Akarsh

## What this document is

The governing specification for Triana Labs work. It exists because the
suspended V1 specification (`docs/PRODUCT.md`) and Labs cannot share one
frozen boundary. Precedence for Labs work: this charter → the append-only
`internal/DECISION_LOG.md` → the current canonical execution plan
(`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`). Repository governance
(`AGENTS.md`, provenance ledger, decision-memory hooks) applies unchanged.

## Narrative (owner-frozen)

> Triana Preview takes your production traces, builds a grounded case panel
> from observed reference behavior and failure signals, mixes shared-context
> resampling with labeled expansion, runs your baseline and candidate on the
> same panel, and reports ranked divergences — including behaviors your evals
> never covered — with every claim backed by a paired transcript and every
> non-claim labeled. Confirmed findings become must-checks for the next run.

## Immediate launch cut (owner-frozen, 2026-08-01)

For the first public developer preview, the value moment is narrower and
supersedes the immediate baseline/candidate sequence above without erasing the
longer-term comparison product:

> Supply authorized conversational traces; Triana derives grounded proposed
> user personas and behaviors, synthesizes a diverse panel of new situations,
> runs genuinely adaptive multi-turn conversations against one existing
> conversational/tool agent, and returns inspectable transcripts, coverage,
> cost, fidelity, and uncertainty. Reviewed local evidence compounds into the
> next run.

This mode is labeled `GENERATED_MULTI_TURN_SIMULATION`. It is not F0 or F1,
does not compare baseline and candidate, and cannot make regression, release,
or accepted-behavior claims. The launch remains local-first and initially
synthetic-only. A model may propose personas, cases, turns, rubrics, and memory;
deterministic code owns identity, support, lineage, selection, duplicate
arithmetic, budgets, and publication; a human supplies the judgment that can
promote, reject, supersede, or revoke persistent local memory.

The launch cut explicitly defers baseline/candidate execution, divergence
reporting, global or managed memory, autonomous model/prompt training, coding
and other universal-agent support, hosted ingestion, and a SaaS control plane.
Those surfaces require later evidence and a new accepted checkpoint.

### First launch checkpoint — Grounded Case Factory

The owner froze LABS-04 on 2026-08-01 as the first checkpoint in this launch
cut. It consumes only the shipped synthetic Observer and structural
intelligence bundles. The completed closing experiment uses the explicitly
authorized Microsoft Foundry Fireworks `FW-GLM-5.2` deployment through a
restricted LangChain `create_agent` four-tool runtime. One initial
clarification is followed by five independent bounded one-case slots;
deterministic code owns evidence projection, citations, support, identities,
slot orchestration, duplicate arithmetic, budget, HTTP accounting, lineage,
and publication. Model output remains `PROPOSED`; semantic usefulness requires
a blind owner review. The 2026-08-02 close produced five valid distinct cases
with no gaps and therefore clears machinery, but LABS-04 remains
`AWAITING_HUMAN_REVIEW`. A failed review still blocks multi-turn runtime work.
The closure includes a supported, strict config-dispatched
`triana cases generate` path for the pinned restricted runtime plus immutable
`triana cases resume`; legacy configs remain explicit and no fallback exists.

The required smoke input is the first 50 physical lines of the existing
tracked HRAI v2 `run_200` historical-traffic corpus, exact selected SHA-256
`4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c`,
labeled `SYNTHETIC_EXISTING_TRACE_CORPUS`. It is not production or real-user
evidence. LABS-04 does not expand the privacy boundary, execute the target
agent, create persistent memory, expose a generic agent framework, or by
itself authorize LABS-05. The
exact contract, final USD 25 ceiling, edge cases, outputs, and independent test-first
roles live in `internal/SLICE_PACKET.md` and
`internal/LABS04_WIRE_CONTRACT.md`.

The canonical restart context for the owner review and proposed LABS-05
Adaptive Multi-Turn Runner is `internal/LABS05_HANDOFF_2026-08-02.md`. It does
not authorize implementation; a new owner-approved slice packet must replace
the closed LABS-04 packet first.

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
5. **Open-source distribution** after the redaction, egress-validation, and
   provenance checks pass. Local-first: nothing is sent to Triana. Redaction
   and egress validation run before hashing and before trace content is sent
   to a model provider. Customer-held keys do not imply authorization;
   configuration or consent must name the provider and permitted egress.
6. **The Slice 0A kernel (`triana-core/`) is shared infrastructure.** Labs
   defines its own document kinds (e.g. PreviewTrace) using the kernel's
   canonicalization and hashing; the five frozen V1 contracts are not
   modified.

## Evidence rules (carried over from repository discipline)

- Divergence-first reporting; verdict language never replaces the human.
- Universal-invariant hits are high-priority flags, not verdicts; a human
  confirmation converts a flag class into a persistent ruling.
- Baseline is reference behavior, not automatically accepted behavior.
  Acceptance requires a human ruling or explicit acceptance evidence. A case
  carrying confirmed failure evidence marks the baseline `KNOWN_FAILURE`;
  divergence then defaults to a candidate-improvement candidate, not a
  verdict.
- Explicit denominators; paired claims only from two-sided intersections;
  gaps, non-comparable, and unstable cases reported separately, never folded
  into scores.
- No rerun-to-green: machinery acceptance is proven on constructed
  nondeterministic fixtures; real-data milestones pass by reporting honestly,
  whatever the data shows.
- Fidelity badge on every report: shared-prefix resampling, simulated
  continuation, and generated-corpus evidence are labeled and never
  conflated.

## Accepted outcome and stability boundary

The owner accepted the typed outcome, pass^3 stability, comparability,
observed-baseline-variation, and evidence-gap machinery in the active plan on
2026-07-31. Outcome fields use `NOT_APPLICABLE`, `MISSING`, or
`PRESENT(value)`; missing required evidence cannot block valid lower-field
observations from being shown, but it prevents a complete-outcome claim. The
plan is normative for the complete mechanism.

The external usability gate is M3.5: a developer who did not build Triana must
install the public repository, adapt their traces within the stated line
budget, and produce an honest report within 90 minutes before persistent label
storage or promotion work proceeds.

## Relationship to suspended V1

V1 (`docs/PRODUCT.md`) is suspended, not deleted. Its incident→ProtectedCase
loop survives inside Labs as the must-check promotion path. Resuming V1 or
merging it with Labs requires an explicit decision-log entry.
