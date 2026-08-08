# Working memory

Updated: 2026-08-07

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
- `internal/DOGFOOD_FAILURE_MEMORY.md` (append-only operational evidence;
  non-authoritative)
- `docs/PROVENANCE.md`

Historical research and suspended-product handoff:

- `internal/Wholistic_Company_View/README.md` (non-authoritative company,
  founder, customer, and narrative synthesis)
- `internal/BRAINTRUST_HRAI_DOGFOOD_REPORT_2026-07-30.md`
- `internal/BRAINTRUST_REPLACEMENT_VERDICT_2026-07-30.md`
- `internal/TRIANA_RESEARCH_CONVERSATION_HANDOFF_2026-07-30.md`
- `docs/PRODUCT.md`

## Accepted four-slice planning frame — 2026-08-07

Akarsh selected Trace-to-Eval Preview as the first complete customer value
loop and authorized repository-wide Agentagon reuse under the provenance
ledger. The immediate product target is:

```text
authorized traces
  -> complete deterministic accounting and evidence coverage
  -> proposed semantic populations and observed behavior
  -> at most three grounded measurement candidates
  -> conversation-level evidence
  -> human Track / Edit / Defer
  -> stable frozen evaluator definition
  -> the same report through CLI, coding agent, backend, and UI
```

The existing frozen-measurement/release-gate machinery is an implementation
asset. The new generalized corpus is the quality and correctness test bench for
that machinery; it is not another customer eval platform and does not delay
the engine behind a broad benchmark project.

The corpus contract is capability-based rather than dataset-named. A case may
declare traces only, official outcome, runnable harness, model/config control,
paired execution, and/or human rulings. Missing truth remains typed missing.
Blitz exercises traces-only discovery; HRAI exercises a controllable real
agent/harness; TAU² exercises a controllable benchmark with official reward and
database-state truth. Product code must not branch on those dataset names.

The four slices are:

0. **Authorization and generalized quality corpus:** update source policy;
   freeze deterministic fixtures plus private/hash-addressed HRAI, TAU², and
   Blitz manifests; establish existing-gate, deterministic-only,
   embedding/clustering, and competent-coding-agent baselines; emit a bounded
   quality report.
1. **Canonical engine:** one Python-owned pipeline for normalization, evidence
   coverage, semantic discovery, deterministic membership/accounting,
   candidate qualification, Track/Edit/Defer, freeze, and capability-gated
   execution/diff.
2. **Backend and product projections:** DBOS invokes the same engine; S3 keeps
   immutable large artifacts; RDS indexes runs/reviews/frozen measurements;
   UI, CLI, and coding-agent workflows consume one canonical report and reuse
   the conversation viewer for evidence.
3. **Comparative proof and launch:** Blitz trace-only usefulness, HRAI A/A and
   controlled A/B, TAU² outcome-grounded A/A and controlled A/B, bounded
   repeated-run stability, and a matched coding-agent ROI comparison.

The owner subsequently directed immediate local implementation with maximum
reuse from the permitted Agentagon source. The quality/correctness defaults,
bounded labeler, split policy, provider/spend limits, dependency-only AWS
boundary, and abort-versus-gap behavior are now frozen in
`internal/TRACE_TO_EVAL_OVERNIGHT_PACKET_2026-08-07.md`; the replacement
`internal/SLICE_PACKET.md` is the active worker contract. Production and test
workers have not started at this point in the record.

The active tranche excludes deployment. App, backend, CLI, and analysis run
locally; only the existing private RDS/S3/DBOS dependencies and the existing
approved Azure configuration may be used. The labeler processes a bounded
blind sample, never every trace. First-broken-link is capability-gated to
outcome-aware corpora, while missing optional semantics, embeddings, auth, CI,
or deployment remain typed gaps rather than blockers.

The grand plan remains a gated progression from trace-to-eval into
production-derived cases, shared-prefix baseline/candidate execution, bounded
multi-turn simulation, comparable behavioral diff, selective L4 failure
explanation, human-confirmed recurrence memory, customer-eval export, and
post-deployment calibration. Slice 3 evidence—not roadmap enthusiasm—decides
which later capability is authorized.

## Current objective

Target-boundary correction is locally complete. The owner-approved
`internal/LABS05_TARGET_CONNECTOR_V1.md` keeps the adaptive controller but
invokes opaque existing agents through restricted HTTP/JSON or a strict
customer executable bridge. HRAI is the first localhost HTTP configuration.
Independent acceptance proves both an HRAI-shaped remote-session endpoint and
a non-HRAI stateless-transcript endpoint: 131 focused tests and 539 complete
repository tests pass the versioned gate.

Triana counts only connector HTTP/executable exchanges it observes. Missing
target-internal HTTP/model/token/cost/tool/global-state evidence is represented
by typed gaps. Triana persistent/global learning memory remains deferred;
target-side state is not silently reclassified as Triana memory.

The one owner-authorized real HRAI canary is consumed. It produced two valid
distinct trajectories, one partial trajectory, and four reviewable adaptation
items. Akarsh ruled Y, N, Y, Y, so LABS-05 closes completed-with-gaps and
unpassed. The N was an exact assistant echo caused by the simulator request
omitting the verified persona, intent, and turn policy and by the absence of a
semantic user-role/anti-copy gate.

Immediate objective completed locally: the owner-frozen synthetic-only
`LABS-06-REGULAR-USER-SIMULATOR-FIDELITY-V1` passed independent RED,
production GREEN, adversarial audit, and the complete 569-test verifier. The
accepted wire is
`internal/LABS06_SIMULATOR_FIDELITY_V1.md`: one attempt, versioned user-owned
context migration, bounded episode state, declared-matcher semantic gates,
structured stop, and a 30-item/24-accepted/zero-critical human fidelity gate.
No provider or target execution was authorized; the 30 human fidelity rulings
remain pending and public sample generation waits for LABS-07. Persistent/
global Triana memory remains deferred. Akarsh passed
`LABS04_USEFULNESS_V1` on 2026-08-02 by
answering yes to all six frozen questions for all five cases and confirming
that none depends on a hidden or fabricated fact. The canonical restart
context and carried backlog are in `internal/LABS05_HANDOFF_2026-08-02.md`.

Public-rollout amendment: Akarsh now wants a public/YC-demonstrable and then
externally usable Preview, with the allowlisted Triana demo adapted as the Labs
UI. The current ordered proposal is LABS-06 fidelity repair, LABS-07 report
contract plus LABS-08 UI as one vertical slice, LABS-09 public synthetic demo,
and LABS-10 local-sensitive stranger installation. The full blocker/deferred register is
`internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md`. UI provenance,
license, accepted wireframes, and the report-as-evidence boundary precede UI
code; the report and UI are no longer separate milestones. Persistent/global
memory is not a first-public-proof blocker.

The planning-first LABS-06 handoff is complete: Akarsh accepted every
recommended option and directed implementation with maximum safe parallelism.
The exact active contract is `internal/SLICE_PACKET.md` plus
`internal/LABS06_SIMULATOR_FIDELITY_V1.md`; LABS-05 connector and retained
episode/artifact rules remain inherited. The selected cases are context
recovery, cross-client refusal, and bounded status verification; each runs as
exactly U1/A1/U2/A2/U3/A3 against an opaque configured target. The supported
local `triana episodes run` surface and both connector kinds are implemented.
No further provider or target experiment is authorized by the failed smoke.

Latest local LABS-06 objective completed: the final provider-conformance slice
keeps the three-field simulator wire and all critical semantic rules, but now
returns one exact structural detail and a closed text-free diagnostic instead
of collapsing every malformed response into an opaque reason. It preserves
normalized usage when the envelope is trustworthy, gives privacy first
precedence, and prevents a third target/simulator slot after two distinct
first-turn episodes prove the same structural defect. Independent results are
43/43 focused, 143/143 historical adaptive, and 594/594 complete repository
tests plus Ruff, strict mypy, build, and clean-wheel installation at
`/private/tmp/triana-labs-verify.qLDTKk`. No provider, HRAI, target, or real
data ran. Dogfood incident `DF-2026-08-03-001` remains open until a separately
authorized simulator-only synthetic check achieves Structural Continuation
Yield `3/3`; human fidelity remains owner-only and unpassed.

Active closure objective: Akarsh approved
`LABS-046-GROUNDED-WORKFLOW-CLOSURE-V1`. It adds a separately versioned
twelve-case path with six directly observed production workflows and six
multi-trace grounded expansions. Every goal, done condition, behavior, and
world identifier must resolve to authorized trace evidence or the captured
HRAI inventory; no AI-authored invention is eligible. LABS-04 emits a tiered
case Markdown view, LABS-06 emits a tiered conversation/result view, and the
simulator advances goal before persona. Legacy pinned behavior remains exact.
Implementation is local/test-first; read-only RDS discovery is authorized,
while provider and target execution still wait for local GREEN and exact
pre-egress owner approval.

Historical superseded 2026-08-02 diagnostic: Akarsh authorized one synthetic episode
against a localhost HRAI endpoint using OpenRouter. The checked-out HRAI commit
is `728f6c5`, but its production model builder is Bedrock-backed and its `.env`
points to remote RDS/Redis, so Codex did not start that configuration. A
disposable localhost bridge instead combined the pinned v3 recruiter prompt
and Triana's four-tool in-memory synthetic world with a single no-fallback
OpenRouter `deepseek/deepseek-v3.2` boundary. The first A1 attempt received HTTP
401. After Akarsh refreshed the key, authentication succeeded and the target
made live model calls, but it returned `ModelCallLimitExceededError` at the
frozen four-call ceiling before producing A1. No U2/U3 ran; no remote database,
Redis, real data, or persistent memory was touched; the endpoint was stopped.
The leading hypothesis is a protocol/prompt mismatch: the pinned
`candidate-screening-v3-decision-followthrough` prompt mandates
`submit_evaluation`, memory, and sometimes decision terminal tools, while the
synthetic LABS-05 adapter intentionally exposes only four read-only lookup
tools. Do not retry or relax budgets until the owner chooses whether to freeze
a chat-specific prompt overlay or expand the target tool/world contract.

2026-08-03 real-endpoint smoke update: Akarsh explicitly authorized starting
unchanged HRAI commit `728f6c5` with its configured Redis/Postgres startup side
effects and one synthetic read-only connector turn. Startup completed only
after its configured Postgres endpoint timed out; the startup seed was skipped.
The `/health` route unexpectedly made one target-internal OpenRouter diagnostic
call and returned after the 30-second client deadline, so its model usage and
cost are unavailable. Triana then attempted exactly one `POST /sessions`; HRAI
returned HTTP 500 because its configured Redis hostname did not resolve. No
session, chat turn, tool call, target response, or persistent target state was
created, and HRAI shut down cleanly. The non-JSON 500 exposed a Triana status
classification defect; an independent 131st regression froze it, production
now reports create failure before parsing a non-success body, and the complete
539-test gate is GREEN. The observed smoke itself remains failed infrastructure
evidence and does not pass `LABS05_ADAPTATION_V1`. Do not rerun without a new
owner authorization after HRAI connectivity is repaired.

Memory decision: immutable accepted case evidence is read-only; transcript and
target state are episode-only and discarded after publication; HRAI persistent
memory is disabled; persistent/global evaluated memory remains deferred until
a reviewed result has a concrete next-run consumer.

Final independent LABS-05 acceptance: 108/108 focused cases and 516/516 full
repository cases pass. The final eight test-owned files/2,792 lines are frozen
at content SHA-256
`e3eb48819cc0bd098a0ed6b270317d964512f29181a56f391cad30347377f196`
and per-file hash-stream SHA-256
`347bf5d65b743e40291ba8f526ef34ccac06ab9368fd3593bb4cce16be3eab27`.
The full verifier evidence is `/private/tmp/triana-labs-verify.LZNfkB`.

The older long-horizon objective below remains strategic context, not the next
implementation authorization.

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

The first immutable RED freeze was paused immediately after production began
when the isolated tester found that `INPUT_TOO_LARGE` lacked exact config and
intelligence artifact byte/line ceilings. Production did not choose a value.
The wire correction fixes 64-KiB config, 1-MiB manifest/report/index, 16-MiB
cluster, and single-line canonical JSON ceilings while literally inheriting the
unchanged Observer reader limits. The test author added 33 black-box cases
without changing the original 109. The initially recorded 140/2 result was
contaminated by the implementation author's untracked partial package in the
shared worktree. After moving that partial tree outside the repository, both
Codex and the implementation author reproduced the clean authoritative state:
142 collected, 141 intended RED failures, one normative-schema pass, all 188
prior tests green, and unchanged corrected aggregate SHA-256
`0d71c4146d10e54b7d5eed22c85e14d38855919766196ac0028e3b627af74c90`.
Production is reauthorized only against that corrected immutable suite.
The owner first superseded the independently imposed 1,500-line production
ceiling with 2,000, then raised the maximum to 3,000 after the readable
implementation reached 1,796 lines before six legitimate adversarial fixes.
The limit is a blast-radius alarm, not a product-quality metric or compression
target. The 14-file limit, exact owned paths, no-dependency rule, immutable
tests, and all behavioral gates remain unchanged.
Candidate `2c6aeb8` passed all 142 frozen acceptance and 188 prior tests but is
rejected by six isolated adversarial regressions: forged self-consistent
intelligence acceptance, both later-stage request-too-large reason mappings,
raw invalid provider-cost exception leakage, missing staging-directory fsync,
and output-target TOCTOU replacement. The independent tester authored the new
292-line file; Codex reproduced exact 6/6 RED and SHA-256
`d9b42b3650d2c6ee9abc492e485d21369ab4de8af078a393b9c6c6da6266c276`
before returning production to the implementation author.
The first production correction made those six cases green. A second isolated
tester pass then added a 305-line file with SHA-256
`4e6e7502cfb0866f598beabe78e09f31208d3936b0a69fce55a1781450e2f50a`;
Codex reproduced the combined suite at 17 collected, seven passed, and ten RED.
The remaining failures cover true atomic no-replace publication, pre-egress
PROPOSE size classification, exact API-key response scanning, secret and DNS
configuration validation, and post-proposal interruption custody. Production
must not replace these with check-then-rename, a visible claim directory, or
another unsafe fallback.
The implementation-author correction changes only three authorized production
files and is independently green at 17/17 adversarial, 142/142 acceptance,
188/188 historical, Ruff, and strict mypy. Production is 1,779 counted lines.
Native Darwin/Linux no-replace publication fails closed when unavailable; the
remaining mechanical work is the complete clean-wheel/privacy/hash gate and
the single preserved Azure/HRAI smoke, not further contract invention.
The first combined full-suite gate then found a test-only module-cache collision:
three runtime `from conftest` statements resolved to LABS-03's already imported
module. The independent test author changed only import timing in the three
affected files, preserving every assertion and expectation, and proved 142/142
isolated plus 347/347 combined. The corrected acceptance aggregate hashes are
`0044aab6adc61a5f1c65184e98be2ee7b84fb4f0f404288315c4043c2bee8fd5`
and `df4d1aaacd24c8049e47bda6594b09697ced68af02b820507075cf984be4ec73`.
The updated versioned verifier subsequently passed 347/347 tests plus Ruff,
strict mypy, lock, build, clean CPython 3.13.14 wheel install, source/wheel
parity, prior handoffs, five canonical Observer hashes, governance, and both
LABS-04 acceptance/adversarial hash gates. Local mechanics are green; live
Azure/HRAI evidence, final secret scan, artifact inspection, and owner review
remain.
The first smoke command preserved a zero-call `CONFIG_INVALID` receipt caused
by Codex omitting `api_key_env` from the private config. After exact local config
preflight, the valid command preserved a second zero-call refusal:
`EVIDENCE_TOO_LARGE(3)`. The HRAI evidence root was 73,650 bytes, but its 424
singleton citations made the exact PROPOSE request 193,867 bytes. The test
author stopped rather than inventing a 100-total-citation limit that conflicts
with `internal/LABS04_WIRE_CONTRACT.md`. The frozen correction instead keeps
the 90,000-byte root pass, then tail-removes selected traces with existing
`EVIDENCE_BYTE_LIMIT_REACHED` gaps until the exact request fits 100,000 bytes;
one oversized trace remains a typed refusal. Pre-test replay predicts nine
retained priority traces, 198 citations, and 93,166 request bytes for HRAI.
The independent tail-fit suite is frozen at SHA-256
`9219b756e9f7c386cfadc4b74a0775a9716593c8e803bcd1e1144f88aba148cd`.
Codex reproduced one passing exact-100,000 boundary and two intended RED cases
for exact-100,001 and repeated tail removal. The prior single-trace refusal and
the 347-case suite excluding this deliberate RED remain green. Production may
now implement only the corrected request-fitting wire.
The implementation-author correction changes only `generate.py`. The author
and Codex independently reproduced 3/3 new tail-fit, 20/20 adversarial,
142/142 acceptance, 188/188 historical, Ruff, and strict mypy GREEN at 1,810
production lines. Pinned-HRAI preflight now yields nine selected traces, 198
citations, 16 explicit byte-limit exclusions, and a 93,166-byte request with
Azure calls still zero. Full verifier and the actual provider smoke remain.
The subsequent actual provider run is preserved unfavorable: one HTTP 200 call,
28,295 Azure-observed input tokens, exactly 4,096 output tokens, 34.6 seconds,
`PROVIDER_FAILED(8)`, and no output directory. Because raw response bytes are
intentionally not retained, hitting the exact output ceiling is strong
telemetry-backed truncation evidence, not a quoted finish reason. The next
contract correction permits no retry and exactly three calls at 240,000 input
bytes/12,000 output tokens each with a USD 8.70 run cap. Worst-case corrected
reservation is USD 8.64; adding the first call's USD 1.095500 reservation gives
USD 9.735500 cumulative. The full 25-trace/424-citation HRAI proposal is 193,867
bytes and fits the corrected bound. Independent tests must refreeze every
changed budget/wire literal before production or another provider call.
The corrected independent suite is now frozen: 163 LABS-04 cases produce 131
intended RED/32 pass against unchanged production while 188 historical tests
remain green. The full 14-file test/fixture content hash is
`877924718cb90cbcf05fe8179c3fefdb5f44f75e89f7e84b66d232e6fc81d1b9`;
the per-file hash-list hash is
`22c42e65e3ebb902cd8c558586a9bfddfb76cd742bdd3f2f3074aa4088ac7a65`.
Production may now implement only the three-call/no-retry/240,000-byte/
12,000-token/USD 8.70 correction. No further provider call precedes GREEN.
Mechanical GREEN may later be produced unattended, but the product checkpoint
remains
`AWAITING_HUMAN_REVIEW` until Akarsh clears the frozen usefulness rubric. No
runtime, DeepEval, memory, UI, real-data support, or LABS-05 work is authorized.

The independent audit subsequently removed the brittle `240,055` fixture
equality: that test's product duty is a sole-trace request above 240,000 bytes
refusing before egress, not a magic serialized size. Exact 240,000 acceptance
and 240,001 tail fitting remain covered by the separate request oracle. The
corrected test hash is
`3d3afc582aafdf45e0cdcbc812987355a50b00170e1d0bf64b2a8bdaeb1d2a07`;
the complete LABS-04 aggregates are
`fd3d310166742fd67469fb68f068a5a6296ff724eb87a444a2f47ca2d4edf2be`
and `399aa3010821083cd2e87a073fffe7381eeb11b75d0c4eee4eb90b8496dda315`.
All 163 LABS-04 and 188 historical tests are green. This is an operational
guard only; checkpoint success still depends on live HRAI outputs clearing the
frozen grounding, realism, adaptive multi-turn readiness, distinctness,
target-relevance, and unjustified-assumption usefulness review.

The corrected HRAI run was preserved as another `PROVIDER_FAILED(8)`: one
Azure HTTP 200 request, 58,855 input tokens, 4,877 output tokens, 42.7 seconds,
and no published cases. It did not hit the 12,000-token ceiling. Code inspection
then found a wire violation: valid Azure `usage` extras were rejected although
wire section 8 requires extra response metadata to be ignored after validated
projection. Independent RED `8da6fca` and production fix `18748af` now prove
164/164 LABS-04 plus 188/188 historical GREEN without another provider call.
Because raw responses are deliberately not retained, this defect is a strong
explanation rather than proof of the exact failed response fields. The active
failure history is in `internal/LABS04_TRIAGE.md`. Before any changed-version
live run, reconcile consumed conservative reservations and the no-rerun rule
against the original cumulative USD 10 ceiling; usefulness remains unproven.

The post-repair versioned gate is fully GREEN: 352 tests, Ruff, strict mypy,
lock integrity, all frozen hashes, source build, clean CPython 3.13 wheel
installation, and source/wheel parity. Evidence is
`/private/tmp/triana-labs-verify.jO4xK6`. The two preserved provider calls carry
conservative reservations of USD 1.095500 and USD 2.418680, totaling USD
3.514180. One further unchanged three-stage run could reserve USD 8.640000,
for a cumulative maximum of USD 12.154180; no call is authorized under the
current USD 10 ceiling. The recommended owner decision is one explicitly
labeled changed-version repair-validation run with identical
corpus/model/prompt/seed, no retry or alternate selection, prior failures
preserved, and a USD 13 cumulative cap. This is pending, not accepted.

Akarsh approved USD 15 cumulative and directed immediate execution of exactly
one repair-validation run. The identical evidence/model/prompt/schema/seed,
three-call/USD 8.70 per-run limit, zero retries, prior failure preservation, and
no-subsequent-run boundary remain unchanged. Maximum cumulative conservative
reservation is USD 12.154180.

The final authorized repair-validation call also failed: one Azure HTTP 200,
58,855 processed prompt tokens, 4,444 generated tokens, 57.2 seconds, no second
stage, and no artifacts. No further provider call is authorized. The exact raw
failure is unknowable because response bytes are intentionally not retained.
The decisive design evidence is that provider strict JSON covers a materially
weaker proposal schema than deterministic `convert_lane` acceptance; many
required counts, formats, ordering, cardinality, reference, claim-use, reaction,
and observed-anchor rules exist only after generation. Thus schema-valid model
output can be discarded before critique with only `PROVIDER_FAILED(8)`.
LABS-04 produced no simulation designs and fails the current smoke; usefulness
cannot be judged. Recovery is a new eval-first design decision, not another
retry or silent semantic weakening. See TRIAGE-11.

Akarsh approved the minimal recovery contract at
`internal/LABS04_RECOVERY_CONTRACT.md`: secret-safe raw/intermediate artifact
custody, typed path-specific defects, exact response replay, provider cached
token accounting, and deterministic-defect-guided critique/revision without
weakening final acceptance. Azure `cacheReadInputTokens` telemetry contained no
observed hits for the three preserved calls. No UI, framework, model change,
memory layer, generic provider abstraction, prompt optimization, or LABS-05
work is authorized. One final live run may occur only after independent RED,
full local GREEN, and replay-only proof; cumulative worst case remains below
the existing USD 15 ceiling.

Latest LABS-04 state (2026-08-01): the grounding-handle correction is locally
implemented through LangChain `create_agent`/LangGraph with exactly four tools;
DeepAgents is parked for future multi-agent simulation. Provider conformance
passed, 361 tests pass, and the five canonical Observer artifacts remain
unchanged. The bounded GLM-5.2 HRAI smoke nevertheless produced zero cases:
after Akarsh answered three material questions, the model used no tools and
repeated the same questions, so deterministic one-pause authority returned
`QUESTION_LIMIT_EXCEEDED`. Exact details are TRIAGE-16 through TRIAGE-20.
LABS-04 and Corpus Intelligence remain blocked; no further provider call is
authorized under the USD 3 slice.

Latest controlled canary (2026-08-01): one-case action selection is now
mechanically correct and locally green, including provider-compatible
separation of initial structured clarification from resumed required tools.
The live supported-protocol run still produced zero cases. GLM retrieved the
correct T011 evidence but looped through 17 literal searches and never
submitted before the seventh resumed HTTP exchange hit Foundry rate limiting.
The runtime reports logical agent attempts rather than underlying HTTP calls,
so its USD 10 budget primitive is not yet agent-loop-safe. TRIAGE-21 through
TRIAGE-24 preserve the evidence. Further provider calls and Corpus
Intelligence remain blocked pending a deliberate retrieval/transition/budget
slice.

Post-launch mandatory eval backlog accepted on 2026-08-01: build a representative
retrieval-quality set; calibrate human case-usefulness review and any model
judge; compare prompts/models on frozen inputs; measure case and trajectory
duplication; test multi-turn rubric quality; and verify HTTP-level budget
accounting across agent loops. These are deliberately not expanded before the
first useful LABS-04 case bundle. The current launch hardening retains only
focused regressions for the observed retrieval and research-transition bugs.

Latest launch-hardening result (2026-08-02): the first useful repeatable
Grounded Case Factory artifact now exists. One GLM-5.2 case is valid and
distinct with no gaps; exact bundle and gate evidence are recorded in
TRIAGE-28. This clears the zero-case product blocker but does not prove batch
scaling or human usefulness. A five-at-once follow-up reached forced submit but
used 32,768 completion tokens and emitted empty tool arguments; see TRIAGE-29.
The next scaling discussion must choose among smaller deterministic batches,
context/output reduction, or a different capable provider. Do not make that
choice implicitly inside bug fixing.

Add to the mandatory later backlog: evaluate material relevance of model-authored
clarification questions against the selected evidence and owner target. The
five-case initial call asked an unrelated capital-city question carried through
untrusted evidence; Codex used the owner's already-approved case-construction
direction rather than answering the injected question. This is not accepted
product behavior and is not silently treated as resolved by the usable
one-case proof.

LABS-04 closing decision (2026-08-02): freeze `ea94d26` as the semi-stable
one-case kernel and test deterministic five-slot scale-out rather than another
five-case monolith. One global answer set applies to every slot; each slot
fails fast independently, later funded slots continue, valid partial results
remain publishable with gaps, and cross-slot dedupe remains deterministic.
The sole live closing experiment has a USD 25 ceiling. Machinery requires at
least three distinct valid cases; human usefulness remains an owner-only blind
review and LABS-05 stays blocked until it clears.

LABS-04 closing result (2026-08-02): exact-five deterministic scale-out passed
with five valid distinct cases, no gaps, no repair, and no duplicate clusters.
The run made six logical invocations and fourteen captured provider HTTP
exchanges, reserving USD 12 conservatively under the USD 25 ceiling; actual
cost is unknown. The supported restricted `cases generate` and immutable
`cases resume` CLI closure is implemented with explicit legacy dispatch,
strict config/environment refusal, and no fallback. The 408-test full gate and
all five canonical Observer hashes are green. The only remaining LABS-04 gate is Akarsh's
`LABS04_USEFULNESS_V1` review; no paid rerun or further L4 engineering is
needed before that judgment.

Fresh-session rule: use `internal/LABS05_HANDOFF_2026-08-02.md` for the exact
LABS-04 result, current implementation boundary, failed paths, proposed
LABS-05 checkpoint, seven material owner decisions, and categorized backlog.
Earlier open-blocker paragraphs in this working memory are chronological
history and are superseded by the final LABS-04 close where they conflict.

Latest LABS-06 live evidence (2026-08-03): Akarsh inspected and authorized the
exact three-context migration bundle before one private HRAI/Foundry run. HRAI
returned one assistant turn for every opening, but all three first Foundry
continuations were rejected as `SIMULATOR_INVALID_RESPONSE`; no simulator user
turn entered custody. The run ended `COMPLETED_WITH_GAPS` with 0 valid/effective
trajectories, 13 gaps, 9 target plus 3 simulator HTTP exchanges, and USD
8.666664 reserved. No retry or rerun is authorized. The provider response bytes
are intentionally not retained, so the structural subcause cannot be recovered
from artifacts and must not be guessed. Akarsh owns any grading of the retained
opening/assistant conversations; local LABS-06 mechanics stay GREEN while live
compatibility and the human fidelity gate remain unpassed.

Latest LABS-06 intent-first repair evidence (2026-08-03): the bounded
three-field proposal and intent-first prompt are locally GREEN (15 focused, 143
historical adaptive, 566 complete verifier). The one authorized repaired live
run was consumed without rerun and reproduced the same earlier boundary shape:
three successful HRAI opening responses followed by three
`SIMULATOR_INVALID_RESPONSE` first continuations, 13 gaps, 12 total HTTP
exchanges, USD 8.666664 reserved, and 0 valid/effective trajectories. No
generated user turn entered custody and no episode reached A2, so structural
yield and Accepted Continuation Rate are unpassed before human scoring. The
three-field provider response bytes are intentionally unavailable in published
artifacts; diagnosing the exact provider envelope/schema incompatibility would
require a separately authorized evidence-custody slice, not another rerun or
semantic weakening.

Latest grounded-workflow closure state (2026-08-03): local implementation is
GREEN with 9/9 new acceptance cases, 43/43 preserved LABS-06 cases, and the
complete 603-test verifier at `/private/tmp/triana-labs-verify.eLaFCb`. The
synthetic tiered previews demonstrate six observed/six grounded-expanded cases
and twelve U1/A1/U2/A2/U3/A3 trajectories, but they are not HRAI production
evidence and carry no owner completion rulings. Live execution is blocked
before RDS/provider/target egress because the current Observer/Intelligence
trace contracts and both closure inventory validators admit only `SYNTHETIC`.
The next bounded question is whether Akarsh authorizes a real-data contract
slice covering read-only RDS export, truthful privacy class, private custody,
inventory lineage, and the exact provider/target budget. Do not relabel real
evidence as synthetic.

Latest owner-authorized real-data plumbing state (2026-08-04): the accidental
synthetic-only block is removed locally for exactly
`OWNER_AUTHORIZED_REAL_DATA_CANARY`. The class now remains truthful across
Observer, Intelligence, Case Factory, world inventory, runner artifacts, and
tiered reports under private `/private/tmp` custody. Unknown, mixed,
non-private, and cross-stage mismatches refuse before transport or target
creation. Independent focused acceptance, Ruff, strict mypy, and the complete
613-test/build/install verifier at `/private/tmp/triana-labs-verify.ccgGCu` are
GREEN. No RDS export, provider, HRAI, target, or real-data run occurred; the
next step is exact live-bundle inspection and a separate egress/cost decision.

Latest LABS-06 owner grading update (2026-08-04): Akarsh accepted final live
Conversations 3 and 4. Conversation 4 is green for this round while its
unsupported uploaded-file claim remains backlog; Conversation 7 and the
partial/unavailable conversations remain unrated, and LABS-06 is not thereby
passed. The bounded candidate fix is a generic authorized-world-mutation gate,
not a file-action allowlist. It remains unimplemented. For any separately
authorized future twelve-case run, use a recommended 1,800-second overall
deadline instead of 600 seconds, retain per-call deadlines and no retry, and
continue to report timeout/network attribution as owner context rather than a
proven technical cause.

LABS-06 final disposition (2026-08-04): Akarsh closed the checkpoint as
`CLOSED_WITH_ACCEPTED_BACKLOG` and directed a local-main merge followed by
LABS-07 discussion. The old 30-item/24-accepted gate is optional future
population calibration, not a remaining checkpoint blocker. Do not reopen
LABS-06 merely to rerun unavailable cases. Carry forward only the recorded
world-mutation authority, intent-precondition, aggregate-deadline, and target
availability backlog, with Conversation 7 and partial/unavailable episodes
remaining visible evidence. LABS-07 is discussion-only until a new bounded
slice packet and owner decisions are frozen.

Roadmap consolidation (2026-08-04): Akarsh combined LABS-07 and LABS-08 into
one report-and-UI vertical slice and directed full-journey wireframe discussion
before implementation. The journey must cover authorized trace setup, corpus
understanding, grounded personas/intents/cases, execution preflight/progress,
adaptive conversations, coverage/cost/gaps/lineage, human review, and carried
backlog. The report remains the only evidence authority, but its minimum schema
and deterministic projection should be built with the UI rather than as a
standalone milestone. Reuse only file-level provenance-cleared tokens, layout,
navigation, drawers, and responsive behavior from the allowlisted Triana demo;
do not carry Release Review semantics or data. LABS-09 numbering and packaging
scope remain unchanged. No UI code, source copy, dependency, or implementation
is authorized until wireframes, provenance, and a replacement slice packet are
accepted.

Accepted LABS-07/08 design update (2026-08-04): Akarsh accepted the complete
full-journey terminology and ASCII wireframes in
`internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md`. Setup currently
selects one local file; adapter understanding is shown through transparent
counts and rejection reasons; current structural groups are not mislabeled as
semantic populations; intuitive case labels explain why each case exists;
`World availability` is retained with `Case data items` as its first specified
subsection; each case maps to one Conversation run; transcripts are primary;
and review records four independent realism/adaptation/completion/boundary
rulings with no aggregate verdict or automatic memory mutation. The
fresh-session prompt and remaining owner gates are in
`internal/LABS07_08_BUILD_HANDOFF_2026-08-04.md`.

LABS-06 deferred behavior, testing, and evaluation obligations are now
consolidated in `internal/LABS06_BACKLOG_2026-08-04.md`. They include generic
world-mutation authority, intent-precondition enforcement, a longer future
aggregate deadline, target protocol/tool-budget readiness, population-fidelity
calibration, semantic population derivation, case/retrieval/duplicate quality,
and accounting/custody hardening. This register is required debt, not an
implicit LABS-06 reopening or live-run authorization.

Self-serve V0 active state (2026-08-06): Akarsh authorized the narrow hosted
trace-viewer checkpoint and directed fast parallel delivery with minimal tests.
The frozen path is managed login, one personal workspace, add agent, upload one
attested PreviewTrace JSONL file, inspect exact accepted/rejected accounting,
and browse accepted conversations through a reusable viewer. Backend and
frontend/viewer proceed as two isolated slices from `ba44e8e`; analysis,
simulation, HRAI ingestion, model egress, teams, billing, adapters, queues, and
cloud deployment remain outside the active change budget. The managed OIDC
vendor, production region/DNS, and final retention automation remain deployment
configuration to resolve after the local integrated gate.

Self-serve V0 local exit update (2026-08-06): the parallel backend and
frontend/viewer slices plus the same-origin routing correction are integrated
on `codex/selfserve-v0`. Focused backend acceptance, Ruff, strict mypy, offline
Alembic render, production parser spot check, frontend acceptance, TypeScript,
existing LABS-08 no-fallback acceptance, Next production build, governance, and
diff checks are GREEN. The browser now calls same-origin `/api/v1`, Next proxies
through server-only `TRIANA_BACKEND_API_ORIGIN`, and `/` enters `/login`.
Public launch is not yet claimed: choose/configure the managed OIDC tenant,
apply migration 0002 to a live database, verify S3/KMS and JWKS, run an
authenticated browser upload, and put the app behind TLS. The current
provider-JWT login is an explicit developer/invite-beta scaffold.

Magic-link/entitlement active state (2026-08-06): Akarsh selected open email
magic-link authentication with no signup waitlist and requested staged feature
access. The active slice replaces the JWT-paste scaffold with Supabase Auth and
keeps the FastAPI JWKS verifier. V0 remains one `OWNER` per workspace; rollout
uses separate workspace entitlements. `TRACE_INGESTION` and
`CONVERSATION_VIEWER` default available. `ANALYSIS`, `SIMULATION`,
`TEAM_COLLABORATION`, and `API_ACCESS` default locked and may be requested.
Request records do not grant access. Admin approvals, extra roles, teams,
billing, and actual staged-feature implementations remain deferred.

Magic-link/entitlement local exit update (2026-08-06): the independent
backend and frontend contracts and implementations are integrated on
`codex/selfserve-v0`. Focused self-serve tests, Ruff, strict mypy, offline
Alembic `0001` through `0003` render, frontend TypeScript, existing LABS-08
acceptance, Next production build, and the production dependency audit are
GREEN; the audit reports zero vulnerabilities. Public launch remains
unverified and blocked on Supabase project/email/redirect configuration,
asymmetric JWT signing with a usable JWKS, live migration `0003`, and an
authenticated two-owner smoke. The current Docker/deploy build does not yet
inject `NEXT_PUBLIC_SUPABASE_URL` and
`NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`; runtime-only Compose values cannot
repair a browser bundle built without them.

TAU57 non-auth DBOS behavior canary (2026-08-06): Akarsh authorized immediate
use of the existing private AWS runtime through profile `akarsh-deepprobe`.
Preflight corrected the stale-account assumption: account `854847082059` has a
running SSM-only `triana-demo` host, available encrypted `db-pg-1`, existing
KMS and healthy app/backend containers. The retained HRAI report remains
accounting-only with 200 physical, 186 accepted, 14 rejected, and zero behavior
groups. The active bounded slice adapts the exact local 57-task TAU² archive to
synthetic PreviewTrace and derives deterministic structural groups through real
DBOS/RDS/S3 for `/behavior`; no LLM, semantic population claim, auth bridge, or
new infrastructure is included.

TAU57 live exit (2026-08-06): the exact 57-task archive is deployed through
the private non-auth operator path. RDS is at Alembic 0003. Import
`imp_37e742f4d6947028cd167c4a52478c50` accounts for 57/57 accepted traces;
DBOS attempt 4 completed as run `run_6e99b23c29175715b5d1ba5a18761b4c`
and report `rpt_70718d7e6cfe538b5a99bc4a44bb536c`. The report contains 54
deterministic structural groups reconciling to 57 support and 10,000 basis
points, with no provider egress and no population claim. Backend/app digest
deployment and local SSM-tunneled `/behavior` verification are green. Two live
migration-compatibility failures now have independent regression coverage:
targetless deterministic artifact convergence after migration 0002, and
conditional legacy rejection supplements that do not duplicate compiler-owned
PreviewTrace facts. The authenticated workspace-safe analysis bridge remains
deferred and must not reuse these unscoped operator routes.

Trace-to-Eval Review V0 local exit (2026-08-07): the canonical local engine,
CLI, loopback backend, and `/analysis` UI now project the same content-addressed
report, bounded blind review queue, append-only rulings, and DEVELOPMENT-only
ConversationViewer evidence. Real dry runs produced 624 Blitz conversations,
57 TAU² conversations with official 39/18 reward accounting, and 185 accepted
HRAI conversations with 15 rejects. Blitz has no outcome source and HRAI
completion is not reward; both remain explicit capability gaps. A single
no-retry Azure canary failed before semantic completion, so current real reports
do not claim semantic populations or eval proposals. Optional next work is
provider compatibility, customer outcome/eval mapping, embeddings challenger,
remote persistence, Kairos L4 attribution, and matched coding-agent ROI proof;
none is silently converted into current product truth.

Authenticated Trace-to-Eval self-serve state (2026-08-07): the independent
ten-case bridge contract is GREEN. A successful upload always returns the
analysis entitlement envelope; `AVAILABLE` starts one idempotent agent-bound
canonical run, while `LOCKED` and `REQUESTED` do not run. Owner-scoped history,
report, review, report-bound ConversationViewer evidence, append-only rulings,
agent switching, and authenticated backend CLI reads now share the same IDs.
The UI projects Overview, User behavior, Eval proposals, Review, and Lineage &
gaps from the stored report. The default self-serve run makes no provider call,
so semantic populations/evals and absent rewards remain typed gaps rather than
invented value.

Local and deployment-readiness gates are GREEN: 17 focused auth/self-serve
tests, 16 canonical Labs tests, backend Ruff and strict mypy, 38 non-live
backend tests with the environment-specific HRAI live test deselected, five
focused app tests, TypeScript, production Next build, deployment-asset check,
secret scan, shell syntax, and Compose render with explicit fixture variables.
The real private RDS/S3 replay reached production code but stopped at the first
workspace S3 write because `triana-demo-ec2-role` lacks the additive
`workspaces/*` list/read/write policy recorded in the runbook. Live email
magic-link verification also remains externally blocked because no Supabase
project URL, publishable key, issuer, audience, JWKS URL, and public TLS origin
are configured. Neither gap authorizes a workaround, deployment, or invented
pass.

Trace-to-Eval local morning replay (2026-08-07): the checked-in valid synthetic
PreviewTrace produced the identical canonical report ID
`sha256:328bc47d527fbf7c01d2c2546dd1c468710eb77decbe44f5ebc336db42f3191d`
through direct CLI, loopback backend, and the visible `/analysis` flow. The
retained controlled-semantic report
`sha256:33d050ea6fffd32dbcf4a0fb2f50751c0f0d4da2488236bd75ca5babe79acc19`
rendered 12 conversations, three populations, three primary eval proposals, a
bounded review queue, and cited `trace-01` evidence in the reusable
ConversationViewer. The former proves deterministic runtime parity; the latter
proves semantic/report/review UI projection only and is not a live-provider
quality claim.

AWS policy read-check command `039aec91-5ae6-4c01-b15c-f7fed315a08e`
confirmed the runtime role still lacks `s3:ListBucket` for `workspaces/`.
Operator IAM introspection is itself unavailable, so the check ran read-only
from the existing instance role and performed no object write. Do not rerun the
real persistence smoke until the exact runbook policy is confirmed added.

TAU semantic checkpoint audit (2026-08-07): request-shape compatibility,
byte-bounded facet batches, grounded evidence projection, exact handling/action
enums, strict-valid checkpoint/resume, and four-label bounded consolidation are
GREEN. The four-label value is only a conservative operating bound for the exact
prompt/schema/payload/deployment/model combination; it is not a Foundry or GLM
maximum. The cumulative conservative reservation reached approximately USD
24.60, so provider execution stopped without fallback. Strict checkpoints hold
two complete 34-conversation DEVELOPMENT runs and 20 stages of run three. Both
complete runs collapse intent to `Mixed or unresolved demand`, and their
handling distributions differ slightly; reliable intent populations and stable
eval proposals therefore remain unproved. A checkpoint-only audit does show a
useful outcome-linked handling signal in run one: tool-observed handling is
19/22 successful, handoff/escalation 2/6, information-requested 1/3, and the
single stalled/repeated trace failed. The active correction is to preserve this
as proposal-only `PARTIAL` evidence without creating populations, evals, review
items, passes, or causal claims.

TAU partial-handling product exit (2026-08-07): the correction is now real in
the canonical engine and both local/authenticated UI report paths. Provider-
disabled checkpoint replay produced report
`sha256:59e42ad3fe20474ed1cd82bf65cd34a356853c575ccb4922c12d636629269592`:
57 accepted, official 39/18 outcomes, two completed 34-trace DEVELOPMENT runs,
88 checkpoint hits, zero provider calls, `PARTIAL`/`PROPOSAL_ONLY`, and the
original semantic-budget gap. Browser verification opened the report and
`tau2-54` ConversationViewer evidence with no console errors. This is the
current release wow: observable handling patterns tied to authoritative
outcomes while uncertainty remains visible. It is not yet a reliable intent
taxonomy or eval-generation result. The UI is dense at 34 trace citations per
run; later progressive disclosure may improve usability without changing the
contract. The focused engine/UI gates, TypeScript, and production build are
GREEN. Full `npm test` retains 14 unrelated legacy static-export/LABS-09
contract failures that predate this slice and remain separately visible.

Final verification debugging record (2026-08-07): observed failure was the
repository Ruff format gate on exactly five previously changed Python files.
Hypothesis: canonical formatting alone would clear the gate without changing
acceptance. One formatter invocation changed only whitespace/layout in those
files; 43/43 focused tests, all-files format check, Ruff, and mypy then passed.
The two affected focused test file hashes were superseded in the decision log;
the partial-handling acceptance hash remained identical. No semantic default,
assertion, dependency, provider call, or UI behavior changed.

Behavior Map release reset (2026-08-07): Akarsh split the product into an
immediate one-upload Phase 1 and deferred eval-oriented Phase 2. Phase 1 uses
`DemandEpisodeV0` so one conversation may contain several user goals and
several evidence-linked agent behaviors. It outputs only Corpus overview, User
Demand Map, Agent Behavior Map, Emerging and Unknown Behavior, Evidence, and
editable Questions for You through canonical JSON plus Markdown/plain HTML.
Minimum proposed-population support is three; smaller grounded groups are
`EMERGING`. Agent context is optional and non-blocking. There is no behavior
difference, outcome slice, eval suggestion, existing-eval coverage,
Track/Edit/Defer, L4, simulation, or new application UX in Phase 1. The exact
product and BM0-BM7 checkpoint plan is
`internal/BEHAVIOR_MAP_PHASES_2026-08-07.md`. Before production edits, replace
the completed Trace-to-Eval slice packet with a bounded Behavior Map packet and
run the independent test-author -> implementation-author -> orchestrator gate.
Terra is the selected primary semantic author; Luna is a separately identified
calibration auditor and never silent fallback. Deterministic code validates
evidence and owns accounting. The cumulative semantic budget is now USD 50.
The owner reports upgraded Luna capacity, so the historical capacity-10 code
assertion must be replaced only after current read-only Azure identity/capacity
preflight; the local CLI could confirm the active subscription but returned no
matching cognitive-account inventory during this planning turn.

Behavior Map local implementation exit (2026-08-07): the independently frozen
38-case contract is GREEN together with all 43 adjacent Trace-to-Eval tests.
The engine now performs per-conversation multi-goal extraction, bounded lossless
global population/behavior consolidation, exact evidence validation, explicit
unknown/emerging routing, independent audit handling, deployment-bound immutable
checkpoint reuse, whole-run cumulative budget preflight, post-call lineage, and
equivalent JSON/Markdown/plain-HTML reports. The local CLI uses separately bound
Terra primary and Luna auditor configuration with no retry or fallback. No live
provider call occurred during implementation. The next gate is the single
authorized DEVELOPMENT-only TAU² Retail run followed by a human usefulness and
evidence audit; application UI/backend work remains deferred until that report
passes.

Behavior Map first TAU proof finding (2026-08-07): exact deployment preflight
and a DEVELOPMENT-only derivative manifest passed with 34 semantic
conversations and 23 sealed conversations. The first no-fallback run produced
three valid Terra checkpoints for `tau2-10`, then Terra consistently failed the
next independent conversation and Luna failed its first audit item. One explicit
checkpoint continuation charged the prior reservation forward and reproduced
both failures; execution stopped rather than loop. The partial map correctly
separated an aggregate two-order return demand, revised refund destinations,
and later human-transfer demand, but one failed unit aborted all later work.
The active correction is per-conversation and per-audit-item typed isolation so
unaffected evidence continues without retrying or hiding the failed unit.

Behavior Map live isolation implementation exit (2026-08-07): the correction
is GREEN across 40 Behavior Map and 43 adjacent tests with independent review.
A failed extraction is attempted once, has no checkpoint, becomes a scoped
unknown, and later conversations continue. A failed audit item is attempted
once, becomes item-scoped uncertainty, is removed from primary publication, and
later items continue with no PENDING leakage. The next operator continuation
must charge the cumulative reservation forward, reuse exact successful
checkpoints, and remain no-retry/no-fallback per failed unit.

Behavior Map corrected TAU continuation finding (2026-08-07): report
`sha256:2f25bc3faa9341dd9a867fc2315289950c28a17f582e20d8fbcf13bb817c4497`
proved per-unit continuation but failed the product-value gate. It retained 38
grounded episodes across 20 of 34 eligible DEVELOPMENT conversations, including
useful multi-goal and supersession examples, but published zero populations and
zero recurring patterns because all 18 independent Luna audits failed. One
bounded provider diagnostic found the precise adapter defect: Luna rejects the
explicit `temperature=0` shared by the OpenAI-v1 client and supports only its
default temperature. The frozen provider-wire RED and one-line production
correction are GREEN across the 83 focused Behavior Map/Trace-to-Eval checks.
The report also exposed follow-up quality debt that must remain visible during
the next human audit: misleading surviving-episode coverage language, episode
boundaries that do not always contain later supporting citations, a semantically
wrong cross-goal citation in `tau2-6`, and a human report dominated by repeated
machine gaps and generic tool occurrences. Do not call the current report a
launch artifact.

Behavior Map first useful TAU draft (2026-08-07): after omitting the unsupported
Luna temperature, report
`sha256:208f62a7e87d66e73191eba9fbc89e6970a6afeb6822fc179f32b2c44a5481d2`
published 45 demand episodes across 25/34 eligible conversations, two user
populations, three recurring agent patterns, six questions, and 11/11 successful
Luna audits. The continuation newly reserved USD 4.93 and reported a cumulative
conservative reservation of USD 39.43/50; actual provider cost remained unknown.
Independent review accepted the content as a useful analyst draft but withheld
self-serve launch on deterministic report truth. The launch-honesty correction
is now locally GREEN: citation bounds enclose accepted evidence; coverage and
population assignment denominators are explicit; audit is labeled sampled;
gaps are aggregated; questions precede the evidence appendix. Semantic relevance
is still a proposal boundary: the known `tau2-6` water-bottle/desk-lamp citation
mismatch must not be described as deterministically solved.

Behavior Map final trust-gate reset (2026-08-07): the launch-honest preview
reached five user populations, four agent behavior entries, 27/34 grounded
conversation coverage, 38/51 population assignment, and USD 44.47 cumulative
conservative reservation, but independent review found the known `tau2-6`
water-bottle member still carried desk-lamp-only evidence and a support-one
observation still appeared as recurring. The final local correction is GREEN:
explicit distinct sibling-subject citations are detached from the wrong episode
with typed uncertainty, and support-below-two pattern claims are demoted to
emerging/review when real recurrence exists elsewhere in the same taxonomy.
The correction does not solve paraphrased semantic relevance; ambiguous cases
remain proposals and sampled audit remains explicitly limited.

Behavior Map Phase 1 product exit (2026-08-07): final report
`sha256:df7222f892a637ed8a9eb3ea788ae73205efe79be4fc5b365168852d8b1911f4`
passed independent artifact review for the preview claim “upload traces and
receive a proposed behavior map, exact evidence, emerging observations, and
unresolved human questions.” It contains 50 episodes over 27/34 eligible
conversations, four demand groups (two proposed populations and two support-two
emerging groups), three recurring agent patterns with support 2/4/3, 36
emerging/unknown rows, eight questions, and 610 evidence records. The wrong
water-bottle/desk-lamp citation is detached in the live artifact and no
support-one pattern is published. Six extraction failures, unassigned demand,
audit disagreement/missing evidence, citation rejection, hierarchy limits, and
unpublishable behaviors remain typed partial evidence. Final conservative
reservation is USD 48/50; actual cost is unknown and no further paid run is
implied. Phase 2 eval generation, comparison/diff, UI productization, and
accepted taxonomy remain deferred.

Behavior Map readable-evidence continuation (2026-08-07): the original TAU
semantic result was reprojected without provider calls into report
`sha256:986251c0d2315674ae40075ff9e13053988ffefb87dd96181f323bd2408b6d9e`.
All 610 evidence links now carry a deterministic conversation-shaped excerpt:
user message, exact tool call/input/result when present, agent response, and
next user message. Intervening user turns hard-stop attachment; missing tool
results are explicit; transcript citations receive the same readable context;
valid JSON-string results decode only when safely traversable; primary values
are byte-bounded with truthful truncation metadata; hostile Markdown/HTML is
escaped without content loss; and raw canonical event JSON is secondary.
Independent review initially rejected cross-turn, citation, escaping, and
false-bound implementations, then passed the final 51-case module. This is a
deterministic evidence-presentation improvement, not new semantic coverage or
accepted truth, and consumed USD 0 provider spend.

Three-corpus Behavior Map generalization (2026-08-07): the canonical private
TAU² artifact is report
`sha256:4b0e1f76a652656c6586e74118e92b16b750ec97436c08c6d33d63cfde85e6e1`
under `/private/tmp/triana-behavior-map-tau57-live/report`. It accepts all 57
conversations, keeps 23 sealed, maps 50 episodes into four demand groups and
three recurring agent patterns, preserves 37 emerging/unknown observations and
eight questions, and exposes 610 readable evidence records. Its USD 48
conservative reservation is not actual billing.

The HRAI generalization artifact at
`/private/tmp/triana-hrai-behavior-v0/report-clean` is an integrity-valid typed
failure report, not a product demo: 185 normalized conversations were accepted,
34 semantic requests were attempted once through Luna, all failed at the
provider boundary, Terra made zero calls, and no episode, population, or
semantic behavior was published. The upstream 200 physical / 185 normalized /
15 adapter-rejected accounting is not yet representable inside the post-
normalization report and remains a typed accounting limitation.

The canonical private Blitz artifact is report
`sha256:738e3001837f3aba5033c2ecfbf878ceadfe5d01813515f20bf21b4a324d438a`
under `/private/tmp/triana-blitz-behavior-v4/report-clean`, served locally at
`http://127.0.0.1:8910/behavior-map.html`. It accepts 624 conversations, selects
34 untouched DEVELOPMENT conversations, seals 125 calibration and 125 holdout
groups, retains 14 episodes across 12 selected conversations, publishes one
support-one emerging user population and three Terra-supported agent-handling
patterns with support 5/4/4, and exposes 28 emerging/unknown rows, five human
questions, and 106 readable evidence records. Luna made 41 attempts with 35
successful stages and six durable failures; Terra judged 9/9 items. No retry or
fallback occurred. The cumulative conservative reservation is USD 84.22/100;
actual provider billing remains unknown.

Three earlier Blitz reports and one refused projection remain private non-
canonical evidence. Independent audits successively found bare shipment IDs,
generic structured fulfillment IDs, numbered/free-form addresses, and landmark
locations; none was served as canonical. The final projection replaces 30
address/location occurrences and 811 fulfillment-ID occurrences, preserves all
624 trace/source identities and 622 tool call/result relationships, and passes
independent placeholder-aware scans for every frozen identifier, phone, email,
address, and landmark class. The bounded deterministic projection still cannot
claim complete PII removal or cover unseen international/free-form locations.
The final Blitz result is a trustworthy proposed Behavior Map and useful agent-
handling report, but not a wow-complete user taxonomy: only 12/34 conversations
yield surviving episodes and only 1/14 episodes is population-assigned.

Blitz post-audit projection correction (2026-08-07): independent regression
proved that the 1/14 assignment was a deterministic authority bug, not the
semantic result. Two sampled episode-level `UNSUPPORTED` audits incorrectly
caused deletion of their separately `SUPPORTED` parent populations. The
corrected no-provider checkpoint projection detaches only those two members,
recomputes population identities/support/visibility, preserves both episode
audit records as `AUDIT_DISAGREEMENT`, and yields 8/14 assigned: Expected
delivery timing support 4, Delayed or missing delivery support 3, and Order
status inquiries support 1/`EMERGING`. Repeated JSON, Markdown, and HTML bytes
are identical. Each identity-changed population now carries `audit_subject_id`
to its preserved pre-projection `SUPPORTED` audit item; the unchanged emerging
population retains its direct ID. This repairs report consistency; it does not upgrade proposed
semantics to accepted truth or erase the two disputed episodes.

Blitz occurrence-support correction (2026-08-08): the first population-correct
projection still counted two occurrences derived exclusively from the two
episode-level `UNSUPPORTED` items in the independently supported “Request an
AWB or order number” pattern. The no-provider correction retains those two
occurrences as `DISPUTED` evidence, excludes them from eligible pattern
membership, reduces the pattern deterministically from support/occurrence count
4/4 to 2/2, reidentifies it as
`sha256:45ed9df04c931cb9f7f58021d10b42d4e1d3b9be52d1c374c76ab826dfcbb5e6`,
and links it to the preserved pre-projection supported audit subject
`sha256:65b48d428de77fe01c83cd5c421dc47f638cb8d2a405b6590250f5c4a747ad92`.
The other patterns remain support 5 and 4; population assignment remains 8/14.
Corrected report
`sha256:c296a2d8bff204c27b128ea43e3a5f51f9104c894d26e088dc625933fd598507`
replays byte-identically from the sanitized checkpoints with zero provider
calls. JSON/Markdown/HTML SHA-256 values are respectively
`1d46a9905c046e01ad6acff4bc3ef698dbddf39c7d5ae1f6711ce6eefb6187bb`,
`c6b9c03748b9a3596908c78af065bb2c523595f6bc63c0146719b1d8165c02f8`,
and `f7bfaa3712f9b3a554d216dce657396886d5db9d260b26212d066d75dbcdab03`.

Full Blitz DEVELOPMENT Behavior Map (2026-08-08): corrected canonical private
artifact is report
`sha256:9c98854dba09a188600b5de7a6f20e71a86ea01791d61556e31f40f16fd1f021`
under
`/private/tmp/triana-blitz-full-development-corrected-final-20260808/report`,
served locally at `http://127.0.0.1:8910/behavior-map.html`. All 374 visible
conversations extracted successfully; 125 calibration and 125 holdout remain
sealed. The map retains 378 episodes across 230 conversations, 80 directly
supported populations, 61 directly supported agent patterns, 212 unique
population assignments, 953 occurrences, 2,052 evidence records, and 142
review questions. Terra produced 141 supported, 6 uncertain, 2 split, and 1
unsupported rulings; 47 further pattern audits are typed missing and none is
published. The report is useful but partial: grounded-conversation coverage is
61.5% and episode assignment is 56.1%, with visible semantic fragmentation.
Luna uses 4k general, 8k extraction, 8k consolidation, and 20-second pacing;
retry/fallback remain none. Conservative cumulative reservation is USD
69.868/70, actual provider billing unknown. JSON/Markdown/HTML SHA-256 values
are `9821a041d391843bae8885010c6180a58a38646f3bd33d56382e5f18a3a8f0f1`,
`7733ccfb3ea73f20043b00464f2dbc8a8c5df92f91a2d509d058e233b40d72b6`,
and `5e83984622aae54c49c53b6355b3865816f4fac021ccf8a7ff2b694897a26377`.
Independent verdict PASS; full verifier 757 passed at
`/private/tmp/triana-labs-verify.sQKjH2`.
