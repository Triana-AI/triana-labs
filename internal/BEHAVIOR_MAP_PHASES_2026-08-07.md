# Triana Behavior Map — Phase 1 and Phase 2

Date: 2026-08-07

Status: **Phase 1 self-serve preview passed on TAU²; Blitz/HRAI generalization and Phase 2 remain pending**

Authority: `triana-labs/CHARTER.md`, `internal/DECISION_LOG.md`, and this
bounded product decision. The implementation entry gate remains
`internal/SLICE_PACKET.md`; its local implementation gate is green and its live
The TAU² product-value proof passed on report
`sha256:df7222f892a637ed8a9eb3ea788ae73205efe79be4fc5b365168852d8b1911f4`
with the bounded claim “proposed behavior map, evidence, emerging observations,
and unresolved questions.” This is not an exhaustive or accepted taxonomy.

## Product sentence

> Give Triana one authorized conversational trace corpus. Triana shows what
> users are trying to accomplish, how the agent handles those demands, which
> behavior is emerging or unresolved, and the exact evidence behind every
> semantic claim.

The first release is a behavior-understanding product. It is not an eval
generator, before/after comparison, release verdict, deployment simulation, or
human-labeling system.

## TAU² Retail agent context

The current proof corpus is the exact authorized TAU² Retail archive already
adapted by Triana. Its agent context is:

> A retail customer-support agent helps customers identify their account,
> inspect products and orders, answer product/order questions, modify or cancel
> pending orders, return or exchange delivered items, update permitted account
> or order details, calculate requested amounts, and transfer to a human when a
> request cannot safely be completed. A good interaction resolves the user's
> complete and sometimes changing multi-request scope, gathers only necessary
> identity or order information, follows retail policy and confirmation
> requirements, performs only supported actions with correct arguments, reports
> what actually happened, and does not silently drop parts of the request.

This context is a non-blocking optional input in the generalized product. When
the user supplies no description, Triana may infer a `PROPOSED_AGENT_CONTEXT`
from authorized traces and tools, cite its evidence, list unknown authority or
policy, and continue. An inferred context is never accepted policy or ground
truth.

## Phase 1 — ship now: self-serve Behavior Map

### Input

- one authorized trace path or one existing self-serve upload;
- optional plain-language agent context;
- adapter and privacy/egress declaration;
- source outcome metadata may be preserved in lineage but is not used to
  create behavior-difference or causal claims in this phase.

No existing eval suite, baseline/candidate pair, human labels, outcome rubric,
or deployment configuration is required.

### Semantic unit

`DemandEpisodeV0` is the primary semantic unit. One conversation may contain
multiple episodes. Each episode contains:

- a concise observed user goal;
- relevant constraints, preferences, changes of mind, and dependencies;
- exact user evidence spans;
- conversation and turn boundaries;
- zero or more evidence-linked agent behavior occurrences;
- `PROPOSED`, `UNKNOWN`, or `UNSUPPORTED` semantic status.

Each sufficiently supported episode receives one primary proposed user
population. A conversation may therefore participate in multiple populations.
Conversation-level source outcomes must not be attributed to a subgoal as if
they were goal-level truth.

### Human-facing output

The canonical machine artifact remains strict JSON. The launch surfaces are a
readable Markdown report and a mechanically rendered plain HTML report with
tables and evidence anchors:

1. **Corpus overview** — accepted/rejected accounting, evidence availability,
   agent context, method identity, and limitations.
2. **User Demand Map** — population name and definition, episode support,
   representative demands, variation, and evidence.
3. **Agent Behavior Map** — multiple observed behaviors per episode or
   conversation, with deterministic versus semantic source visibly separated.
4. **Emerging and Unknown Behavior** — populations with support below three,
   outliers, ambiguous membership, abstentions, missing evidence, and unstable
   semantics.
5. **Evidence** — representative and boundary conversations with exact cited
   spans and tool events.
6. **Questions for You** — editable, bounded questions asking whether proposed
   populations and behaviors match the evidence and what wording or boundaries
   should change.

Phase 1 deliberately contains no behavior-difference section. It describes one
uploaded corpus. It may show counts and prevalence inside that corpus but does
not compare cohorts, versions, source-success/failure slices, baseline and
candidate, or time windows.

### Population visibility

- Three or more grounded demand episodes: visible proposed population.
- One or two grounded episodes: `EMERGING`, never promoted by padding or forced
  merging.
- Ambiguous, unsupported, ungrounded, or unstable episode: `UNKNOWN` or a typed
  gap.
- No human review is required to produce the report. Future review may rename,
  merge, split, accept, or reject proposals without rewriting the original run.

### Authority

| Owner | Owns |
|---|---|
| Deterministic code | normalization, episode/conversation identity, evidence substring validation, support, counts, ordering, hashes, lineage, typed gaps, artifact rendering |
| Model | proposed agent context, demand-episode boundaries and summaries, proposed population meaning, semantic agent behavior descriptions, uncertainty and questions |
| Human | any accepted agent purpose/policy, corrected population or behavior meaning, and future persistent ruling |

### Explicitly excluded from Phase 1

- eval suggestions or generation;
- existing-eval import or coverage;
- Track/Edit/Defer and evaluator freezing;
- before/after or cohort behavior differences;
- source-reward dashboards or causal explanation;
- first-broken-link/L4 judgment;
- simulation, agent execution, or deployment simulation;
- a new application UX or dashboard redesign.

## Phase 1 implementation checkpoints

### BM0 — contract and acceptance freeze

Freeze `BehaviorMapReportV0`, `DemandEpisodeV0`, `UserPopulationV0`,
`AgentBehaviorOccurrenceV0`, `EvidenceCitationV0`, and typed gap schemas. Freeze
one synthetic multi-goal fixture and one hash-addressed TAU manifest. Independently
author acceptance tests before production changes.

Exit evidence:

- one conversation can yield at least two demand episodes;
- one episode can carry multiple agent behaviors;
- every semantic row has an exact evidence citation or abstains;
- support below three cannot become a population;
- no eval, diff, causal, or accepted-truth field exists in the public report.

### BM1 — canonical episode extraction

Adapt the permitted Agentagon Exploration V1 evidence projection, batching,
strict validation, and unresolved handling into the current Triana adapter,
privacy, checkpoint, and budget shell. Replace the one-goal-per-conversation
assumption with bounded episode arrays. Preserve deterministic tool and event
evidence separately from model interpretation.

Exit evidence: the multi-goal fixture and selected TAU conversations produce
complete cited episode coverage or explicit unknown spans. Episodes may share
a turn when one user utterance contains several independently actionable goals;
the model must not manufacture artificial turn boundaries to make episodes
non-overlapping.

### Model assignment for semantic work

Terra is the primary semantic author for Phase 1. Luna is a separate bounded
auditor, not a silent fallback:

1. Terra proposes demand episodes, episode constraints, and evidence-linked
   agent behavior occurrences from the complete bounded conversation projection.
2. Deterministic code rejects missing turns, non-exact citations, invalid
   boundaries, duplicate identities, unsupported fields, and generic behavior
   wording.
3. Terra consolidates episode goals into proposed user populations and
   behavior occurrences into specific recurring behavior patterns.
4. Luna independently audits a deterministic calibration sample for
   `SUPPORTED`, `MERGE`, `SPLIT`, `UNSUPPORTED`, or `UNCERTAIN`. It does not
   rewrite Terra output or become accepted truth.
5. Code publishes supported proposals, routes disagreements to Emerging and
   Unknown Behavior, owns all counts, and renders the report.

The exact Azure deployment identity, version, SKU, capacity, endpoint, and
credential boundary must be verified before egress and recorded in lineage.
The previously checked-in Luna capacity expectation may be stale after the
owner-reported quota upgrade and must not be treated as current evidence.

### BM2 — user population discovery

Group grounded demand episodes, not whole conversations. Reuse Agentagon's
bounded hierarchical consolidation and unresolved buckets for the first
result. Keep an embedding/clustering challenger optional and non-authoritative;
it must not block today's report. Code assigns support and visibility state.

Exit evidence: all eligible episodes are accounted for exactly once as a
primary proposed population, `EMERGING`, or `UNKNOWN`; no label or evidence is
lost through hierarchy.

### BM3 — multi-label Agent Behavior Map

Build deterministic behavior cells from ordered events and tools, then add
evidence-linked semantic behavior occurrences. Do not use the current terminal
`handling_mode` as the primary product abstraction. A behavior title must be a
specific observable description such as “repeats an unchanged rejected tool
call,” not “tool action observed.”

Exit evidence: one TAU conversation demonstrably carries several behaviors;
deterministic observations remain distinguishable from semantic proposals;
incomplete exports do not become accusations such as fabrication or failure.

### BM4 — emerging/unknown and quality accounting

Compute grounded coverage, unknown rate, abstention counts, episode-boundary
coverage, population support, behavior support, and exact citation validity.
Run a deterministic calibration sample through an independent semantic audit;
disagreement becomes visible uncertainty rather than a whole-corpus rerun gate.

Exit evidence: the report remains useful when some rows are ambiguous, the
provider is partially unavailable, or a semantic stage stops after valid
checkpoints.

### BM5 — Markdown and plain HTML report

Render the same canonical artifact to `behavior-map.md` and
`behavior-map.html`. HTML is a simple report renderer, not a new application
surface. Evidence anchors open the existing canonical conversation material or
render a bounded transcript excerpt. The Markdown ends with editable questions
and blank answer fields.

Exit evidence: a human can understand the principal user demands and agent
behaviors without reading internal enum names, report IDs, hashes, or raw JSON.

### BM6 — real TAU² Retail proof and product audit

Run the exact authorized 57-conversation TAU² Retail corpus through the frozen
path. Audit episode decomposition, population usefulness, behavior specificity,
evidence validity, unknowns, and the report's plain-language comprehension.
Do not make a live call until the new contract and independent tests are
frozen. The owner-approved cumulative semantic budget is USD 50; the run must
reserve against that cumulative ceiling, preserve actual usage, and stop rather
than retry or fall back when the remaining reservation is insufficient.

Exit evidence:

- exact accounting for all 57 conversations;
- useful populations supported by at least three episodes;
- emerging and unknown episodes visible;
- multiple behaviors may attach to one conversation;
- zero generic primary cards such as `TOOL_ACTION_OBSERVED`;
- all displayed semantic claims resolve to exact evidence;
- one readable Markdown report and one equivalent HTML report;
- documented cost, gaps, reproduction command, and owner questions.

### BM7 — existing self-serve upload bridge

After BM6 passes, point the existing one-upload workflow at the same canonical
engine and expose the generated report artifact for viewing or download. Do not
redesign `/analysis`; a plain report link is sufficient for this release.

Exit evidence: a fresh supported upload starts one idempotent behavior-map run
when analysis is entitled, and returns the exact same report identity as the
local CLI path. Locked/requested access remains non-running.

## Phase 2 — retained product direction: behavior-to-eval maintenance

Phase 2 begins only after Phase 1 produces a useful map on TAU, Blitz, and HRAI.
It adds:

- existing-eval import and coverage mapping;
- grounded eval suggestions;
- evidence routing and semantic backfill;
- deterministic qualification and bounded Track/Edit/Defer review;
- frozen population classifiers and evaluator definitions;
- future-batch known/new/shifted/retired maintenance;
- optional baseline/candidate behavior differences;
- execution through customer-owned or external eval runners;
- later deployment-simulation and release-evidence integration.

Phase 2 reuses the Agentagon goal-observable measurement lifecycle. It is not
part of today's Phase 1 acceptance and must not leave empty placeholder sections
in the Phase 1 report.

## Quality baseline

Phase 1 is evaluated independently from future eval-generation quality:

| Component | Phase 1 check |
|---|---|
| Contract | accounting conservation, stable identity, strict parse, typed refusal |
| Episode extraction | goal/boundary/citation audit on a held-out sample |
| Populations | support, pairwise human audit, coverage, unknown rate, label stability |
| Behaviors | specificity, multiple-behavior support, citation validity, abstention quality |
| Report | comprehension, evidence navigation, no unexplained internal vocabulary |
| Generalization | TAU retail, Blitz trace-only, and HRAI adapter/corpus checks |
| Product ROI | later matched coding-agent comparison on usefulness, grounding, repeatability, time, and cost |

The immediate launch claim stops at an evidence-grounded proposed map. It does
not claim that a population is representative, a behavior is correct or wrong,
or a source outcome was caused by an observed behavior.

## Readable-evidence continuation

The deterministic readable-evidence continuation supersedes only the human
evidence projection and report identity. Report
`sha256:986251c0d2315674ae40075ff9e13053988ffefb87dd96181f323bd2408b6d9e`
preserves the same semantic populations, patterns, gaps, questions, coverage,
and provider lineage while adding bounded conversation-shaped excerpts to all
478 event and 132 transcript evidence rows. It made zero provider calls and
does not change the Phase 1 claim boundary.
