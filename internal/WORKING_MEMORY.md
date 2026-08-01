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
