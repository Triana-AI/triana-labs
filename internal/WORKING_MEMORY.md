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

The primary product surface is a CLI designed for setup by the customer's
coding agent; the human consumes a generated local HTML report backed by the
same machine-readable artifact. Initial acquisition is a bounded application
for five qualified design-partner teams, paced at one or two onboardings per
week. A thin generated landing page is acceptable for that funnel, but hosted
accounts, trace uploads, execution, and product dashboards are not.

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

The plan-first delivery decision is implemented in
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`. LABS-01 replaced the
historical packet and shipped the first component at `92f65a1` under an
independent 106-case acceptance freeze plus six orchestrator-reserved
adversarial cases. LABS-01A made its boundaries human- and agent-readable at
`42043ab`. LABS-01B made the code match those responsibilities at `c87a521`,
with six additional independently authored architecture tests. LABS-02 then
shipped one standalone, synthetic-only HRAI `normalized-trace-v2` reference
mapping into PreviewTrace JSONL. It is exactly 200 counted adapter lines, uses
only the standard library, and is accepted by both source and installed-wheel
Observer commands. LABS-03 now consumes that Observer bundle and publishes
deterministic structural clusters plus explicit semantic gap indexes. The
complete suite has 188 passing tests and the five canonical Observer hashes
remain frozen. The current packet records exact edge cases, hashes, role
handoffs, generated evidence, and exit gates.

Current component checkpoint:

```text
SYNTHETIC PreviewTrace JSONL
  → cli.py
  → observer/observe.py        orchestration and line accounting
      → contracts/traces.py    one-trace parsing and validation
      → observer/profile.py    deterministic corpus aggregation
      → observer/publication.py
          → observer/renderer.py
  → normalized_traces.jsonl
  → rejected_traces.jsonl
  → corpus_profile.json
  → corpus_profile.md
  → manifest.json
  → corpus derive
      → intelligence/input.py        Observer bundle integrity
      → intelligence/derive.py       structural membership and gaps
      → intelligence/publication.py  atomic bundle publication
  → clusters.json
  → derivation_report.json
  → personas/intents/turn_policies indexes (NOT_DERIVED)
```

Observed Observer result remains five physical lines, three accepted, two
rejected, and two mechanically eligible; all five hashes are unchanged.
LABS-03 is complete as the first bounded M1B checkpoint, with 188 tests passing
and source/clean-wheel artifact parity. It derives only observable structural
clusters. Persona, intent, turn policy, language, and distress semantics remain
explicit NOT_DERIVED gaps. Full semantic M1B, LLM/provider use, real data,
redaction, Blitz mining, Case Generator, SDK, OTel, hosted ingestion, and UI
are not authorized by this completed packet.

Next-session handoff prompt:

```text
Continue Triana after the completed LABS-03 structural Corpus Intelligence
checkpoint.

Read AGENTS.md, triana-labs/CHARTER.md, the current plan named by the charter,
docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/CONTRACTS.md,
internal/WORKING_MEMORY.md, docs/PROVENANCE.md, the full
internal/DECISION_LOG.md, docs/ENGINEERING.md, and internal/SLICE_PACKET.md.

Ground truth: the synthetic-only path now runs reference adapter → Trace
Observer → structural Corpus Intelligence. `triana corpus derive` verifies the
Observer bundle and publishes deterministic clusters plus explicit NOT_DERIVED
semantic indexes. The suite has 188 passing tests; all five Observer hashes and
prior acceptance aggregates are frozen. There is still no real-data path,
redaction/egress layer, semantic persona/intent/turn-policy derivation,
language/distress mining, Case Generator, SDK/OTel, provider call, or UI.

Start with the next material product decision inside M1B: what authorized
evidence and privacy/egress boundary could support semantic asset proposals
without inventing customer truth. Do not skip directly to Case Generator while
persona, intent, policy, fidelity, and correction authority remain explicit
gaps. Any implementation requires a new slice packet and the same independent
test-author → implementation-author → orchestrator protocol.
```

The frozen product component flow is:

```text
Trace Observer
  → Corpus Intelligence
  → Case Generator
  → Panel Builder
  → F0 Paired Runner
  → bounded F1 Next-Turn Generator
  → Evidence Engine
  → Local Report
  → Human Rulings only after M3.5
```

The first alpha is reviewed at each component artifact rather than hiding
value behind plumbing milestones. It is bounded to 25–100 traces, 5–10
generated cases, 3–5 selected cases, k=3 paired F0 trials, F1 on at most two
divergent cases, one provider/model, one subprocess protocol, and local
machine-readable plus HTML reports. Exact outputs and authority boundaries are
frozen in the canonical plan.

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

## Active discussion tree — 2026-08-01

The accumulated semantic-agent, evaluator, budget, duplicate-control,
turn-generator reuse, and memory discussion is normalized in
`internal/LABS_NEXT_DECISION_TREE.md`. It is discussion state, not accepted
authority. Its current recommendation is one next checkpoint only: evaluate
grounded semantic asset derivation behind the minimum provider
privacy/egress/budget boundary. DeepEval remains a later F1 conformance
candidate; neither adopting it nor building a custom runtime turn generator is
authorized yet. Memory beyond the minimal record/snapshot lifecycle remains
parked until a consuming milestone passes.

The owner subsequently accepted a different first-launch cut on 2026-08-01:
single-agent `GENERATED_MULTI_TURN_SIMULATION` from authorized traces, with
grounded proposed semantic assets, distinct case synthesis, adaptive multi-turn
execution against one conversational/tool agent, inspectable evaluation and
budget evidence, and versioned local evaluated memory. The decision-log entry
and charter/plan amendment supersede the discussion tree wherever they differ.
Exact checkpoints, human-review workflow, judge calibration, runner protocol,
provider/model, cost bounds, and report cut remain the active discussion before
the next slice packet is frozen.

## Frozen next slice — LABS-04 Grounded Case Factory

Akarsh approved the first implementation checkpoint on 2026-08-01 and Codex
froze it in `internal/SLICE_PACKET.md`. The slice consumes only verified
synthetic Observer and LABS-03 bundles, projects at most 25 eligible traces
through an explicit provider-safe evidence lane, and uses the existing Azure
OpenAI `gpt-4.1-mini` deployment (`2025-04-14`) for one proposal, one critique,
and one revision. It emits five proposed personas/intents/adaptive turn
policies and case designs plus attempts, citations, lineage, diversity, cost,
gaps, and a blind human-review template.

The live smoke uses the first 50 physical lines of the pre-existing tracked
HRAI v2 `run_200` historical-traffic file at commit
`728f6c5058efe40a16e2aecc9b528b3353f4df4f`, exact selected SHA-256
`4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c`.
It is labeled `SYNTHETIC_EXISTING_TRACE_CORPUS`; it cannot support a production
or real-user claim. The provider boundary has three normal/six absolute calls,
a conservative USD 10 cap, strict named Azure egress, and no ambient
credential discovery.

Preflight rejected the previously frozen `run_50b` file as legacy (0/50
adapter acceptance). The corrected v2 subset yielded 25 accepted and 25 typed
source rejections, then 25/25 Observer acceptance and 22 structural clusters.
Those denominators remain visible and the subset cannot be changed to improve
the smoke result.

The independent LABS-04 test author stopped twice before editing rather than
invent byte-affecting behavior. The second correction freezes exact provider
schema values, callable transport/clock/publication seams, raw response hashing,
fixed-config refusal, manifest/evaluation arithmetic, retained gap/duplicate
semantics, blind-review membership, and cleanup-failure behavior. Acceptance
authorship then produced 109 cases. Codex reproduced valid RED at 108 expected
behavioral failures plus one normative-schema pass, all 188 prior tests green,
and aggregate sorted-content SHA-256
`98eab12ef1d85fe1fea18150b729fcc6cf38530cb482a996df80dcc5b92457de`.

The immutable RED contract is frozen and production authorship is authorized
only within the packet's bounded implementation paths. Once production begins,
the tester may attack the frozen contract in an isolated parallel worktree.
Mechanical GREEN may be produced unattended, but the product checkpoint remains
`AWAITING_HUMAN_REVIEW` until Akarsh clears the frozen usefulness rubric. No
runtime, DeepEval, memory, UI, real-data support, or LABS-05 work is authorized.
