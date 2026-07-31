# Working memory

Updated: 2026-07-31

## Active strategic position

Triana Labs Preview is the active build and learning surface. The prior
closed-source Release Review V1 is suspended, not deleted. Its deterministic
kernel remains shared infrastructure in `triana-core/`; no Labs work may
silently alter its five frozen contracts.

The current bet is deliberately smaller than the long-term release-control
thesis:

```text
production traces
  → grounded case panel
  → shared-prefix baseline/candidate resampling
  → labeled simulated continuation after divergence
  → stable, paired behavioral differences and explicit gaps
  → human-confirmed persistent rulings
  → rerun on the next candidate
```

The product is not “another eval platform” and does not claim to decide
whether to ship. It must make consequential behavioral movement visible using
evidence a team already has, preserve comparability and lineage, and honestly
state when the evidence supports no conclusion.

Canonical active documents:

- `triana-labs/CHARTER.md`
- `internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`
- `internal/DECISION_LOG.md`
- `docs/PROVENANCE.md`

Historical research and suspended-product handoff:

- `internal/BRAINTRUST_HRAI_DOGFOOD_REPORT_2026-07-30.md`
- `internal/BRAINTRUST_REPLACEMENT_VERDICT_2026-07-30.md`
- `internal/TRIANA_RESEARCH_CONVERSATION_HANDOFF_2026-07-30.md`
- `docs/PRODUCT.md`

## Current objective

Ship a public, local-first Preview that a developer with a conversational AI
agent can install and use without founder-written integration code. The
decisive exit is M3.5: a developer who did not build Triana must provide a
trace export, configure baseline and candidate execution, and produce an
honest report in under 90 minutes with at most 200 adapter lines (target 100).

Internal HRAI success proves machinery and supplies a demo. It does not prove
that another team has a recurring problem or that the adapter contract is
usable.

## Accepted Preview boundary

- Conversational, tool-using agents with observable structured turns or
  transcripts and ordered tool activity.
- Customer-provided production traces or approved synthetic/public corpora.
- A public `PreviewTrace` contract and documented JSONL/OTel-shaped adapter.
- Explicit baseline and candidate command or endpoint identities.
- F0 shared-prefix resampling: both arms receive the same historical prefix
  and execute freshly.
- F1 continuation driven by a next-turn generator derived from the authorized
  corpus; simulation and generated-corpus evidence are labeled.
- Repeated paired trials, trajectory-diversity measurement, typed gaps, and
  divergence-first reporting.
- Local-first execution. Nothing goes to Triana. Provider and permitted egress
  must be explicitly configured; redaction and egress validation happen before
  hashing and before model-provider calls.
- Open-source distribution only after provenance, privacy, and egress checks.
- No SHIP/BLOCK verdict. Humans confirm persistent rulings and decide what the
  difference means.

## Accepted outcome and stability machinery

- Each trial is `valid` or `invalid` with a typed cause before comparison.
- Applicable outcome fields use
  `NOT_APPLICABLE | MISSING | PRESENT(value)`.
  `NOT_APPLICABLE` is skipped; `MISSING` prevents a complete-outcome claim but
  does not erase lower-field partial observations; `PRESENT` is compared.
- Outcome fields are declared projection, commitment, agent-origin terminal
  status, and exact ordered tool-name sequence. Precedence controls only the
  primary display reason.
- The baseline is reference behavior, not accepted ground truth. Explicit
  human evidence may mark it accepted or `KNOWN_FAILURE`.
- Tier-1 stability at k=3 requires pass^3 on one outcome in the baseline and
  pass^3 on a different outcome in the candidate. Weaker or unstable changes
  live on a separate evidence shelf.
- Paired claims use only the two-sided comparable intersection. Fingerprint
  differences, invalid runs, and insufficient trials are never silently put in
  pass denominators.
- Numeric aggregate movement is contextualized against observed baseline
  variation. This is not called a statistical noise estimate.
- Every milestone is compared with the standing DIY frontier-agent benchmark.
  If a generic coding agent produces the same useful result without Triana,
  Preview must win on reproducible execution, stability math, denominators,
  persistent rulings, repeatability, or cost.

## Active hypotheses and stopping evidence

| ID | Hypothesis | Smallest useful evidence | Current status |
|---|---|---|---|
| L1 | A stranger can reach a report without founder integration | One M3.5 installation under 90 minutes and at most 200 adapter lines | Untested |
| L2 | Preview finds a useful stable difference that the team's current eval/review did not make obvious, or earns trust by showing honest no-difference | Stranger report plus debrief against their existing process | Untested |
| L3 | F1 generated user continuations are realistic enough to reveal relevant post-divergence behavior | Blind or owner-reviewed sample of 30 with declared acceptance and duplicate-trajectory budget | Untested |
| L4 | The deterministic machinery beats “give both trace sets to Codex/Claude” on a structural axis | Same inputs, timed DIY benchmark, compare findings, denominators, repeatability, and cost | Untested |
| L5 | Confirmed rulings become more valuable on a second candidate run | Same external developer reruns one changed candidate and prior rulings apply correctly | Blocked on M3.5 |
| L6 | The artifact creates qualified conversations with agent builders | At least five relevant users inspect or run it; at least two request a follow-up about their release workflow | Untested |

M3.5 fails if the stranger needs bespoke founder engineering, exceeds the time
or adapter budget, cannot understand the report, or would not consider using
it again. Failure triggers a narrow correction to installation, adapter, or
problem scope. It does not authorize building M4 to compensate.

## Immediate build sequence

All implementation slices use `docs/ENGINEERING.md` and a current
`internal/SLICE_PACKET.md`: orchestrator freezes the contract, an independent
test author proves RED, a separate implementation author implements without
changing frozen tests, and the orchestrator owns adversarial and full-gate
verification. Shared-worktree edits are serial unless isolated worktrees are
used. Each slice also freezes and reconciles a change budget, uses one
falsifiable hypothesis per debugging iteration, and ends with a structured
handoff that separates verified facts, unverified work, assumptions, and
uncertainty.

1. **M0 — honest demo data:** fresh HRAI baseline/candidate/control data,
   current trace schema, k=3, spend cap, redaction and self-agreement evidence.
2. **M1 — public input boundary:** PreviewTrace, external adapter and runner
   contracts, corpus-derived personas/intents/turn policies, fidelity-labeled
   grounding.
3. **M2 — comparison machinery:** typed outcomes, pass^3 stability, closed
   comparability fingerprint, observed baseline variation, sequence alignment,
   next-turn generation and trajectory-diversity checks.
4. **M3 — public-ready report:** one-command demo, divergence-first report,
   paired transcript, lineage, fidelity, denominators, gaps, redaction and
   egress gates, DIY-agent comparison.
5. **M3.5 — stranger installation:** external developer meets the time and
   adapter limits and answers whether they would use it on another release.
6. **M4 — gated recurrence:** only after M3.5, persist confirmed ruling
   identity and apply it on a changed candidate; promotion emits a
   ProtectedCase draft for human completion.

## Do not build yet

- Hosted ingestion, storage, authentication, billing, or managed execution.
- Guard, Learn, automatic release recommendations, rollout, rollback, or live
  side-effectful tool execution.
- Full eval-platform imports, scorer authoring, prompt management, or generic
  observability.
- Automatic change-to-impact inference or production-incidence prediction.
- Universal-agent support beyond the conversational/tool-agent boundary.
- An LLM-owned ground truth, verdict, denominator, comparability decision, or
  persistent ruling.
- M4 label storage and promotion before M3.5 passes.
- Broad dashboards, a general workflow engine, microservices, Kubernetes, or
  performance infrastructure without a measured bottleneck.

## Suspended Release Review V1

The frozen V1 in `docs/PRODUCT.md` remains an archived, internally consistent
product boundary: customer-declared Release Change, human-approved Release
Obligation expressed as a Protected Case, paired customer-CI evidence, typed
gaps and comparability, immutable Release Evidence Record, advisory
PASS/REVIEW/BLOCK, and separate human Decision Attestation.

The Braintrust HRAI dogfood found that Braintrust plus roughly 282 lines of
ordinary CI glue could solve the bounded workflow sufficiently, making the
generic release layer likely internal glue for that case. Do not resume V1,
merge it into Labs, or present it as the active product without new external
evidence and an explicit decision-log entry.

## External evidence log

Add one row per installation or serious workflow reconstruction.

| Date | Team/agent | Existing stack | Input adapter LOC | Time to report | Useful difference or honest no-difference? | Existing process missed it? | Would use again? | Follow-up requested? | Notes |
|---|---|---|---:|---:|---|---|---|---|---|

## Open implementation decisions

- Exact public adapter envelope: minimum JSONL event vocabulary and optional
  OTel mapping.
- Exact baseline/candidate runner protocol for subprocess versus HTTP agents.
- License and contribution policy for the public Labs repository.
- Operator spend cap after the initial USD 50 per-panel default is tested.
- M3.5 participant selection: must operate a real conversational AI agent and
  must not have contributed to Triana.

These are implementation questions, not permission to expand product scope.
