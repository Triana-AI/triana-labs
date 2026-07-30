# Working memory

Updated: 2026-07-30

## Active strategic position

Triana is not being repositioned as an automatic eval-improvement loop.
Customer-owned evals and production-derived cases are evidence inputs. The
unproven independent boundary is the cross-stack Release Review and retained
release lineage:

```text
Release Change                          exact candidate under review
Release Obligation                      human-approved behavior requirement
Protected Case                          V1 executable form of one obligation
required + received evidence            Triana and customer-owned lanes
Release Evidence Record                 immutable pre-decision artifact
Release Policy                          evidence-to-recommendation rules
PASS / REVIEW / BLOCK                   advisory recommendation
Release Review                          recurring V1 product
human approval / hold / exception       Release Decision
Decision Attestation                    immutable human-decision link
rollout + production outcome            future Release Control lifecycle
future protection                       human-reviewed feedback loop
```

Frozen V1 implements the chain through the human Release Decision. It accepts a
customer-declared Release Change, requires a human-selected obligation, and
does not automatically infer impact or applicability. Production outcome,
calibration, and automatic policy learning remain outside V1.

This becomes a company only if eligible teams use it as a recurring release
ritual, retain it across releases, value it alongside—not instead of—their eval
stack, and eventually ask it to govern rollout or enforcement.

Canonical handoff:

- `internal/TRIANA_RESEARCH_CONVERSATION_HANDOFF_2026-07-30.md`
- `internal/BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md`
- `internal/DISCOVERY_ASK_GUIDE.md`
- `internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md`
- `internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md`

The next strategic work should reconstruct real release and rollout decisions,
then stress-test Braintrust's extension path against those workflows. Do not
resolve the distinction through internal reasoning alone.

## Current objective

Prove that an eligible team can receive a decision-changing Release Review on a
real PR that states the exact Release Change, one human-approved Release
Obligation, required and received evidence, gaps, policy reasoning, and human
decision state—without Triana-authored integration code.

Do not optimize the long-term platform before proving this loop.

## Frozen

- Narrow CI-runnable ICP: conversational, tool-using agents only.
- Offline document-processing, batch, coding, research, and other
  non-conversational autonomous agents are outside V1.
- The replay unit is one bounded conversational episode, not open-ended
  multi-turn simulation.
- One exact incident, not representative production coverage.
- Human-approved Release Obligation carried by one Protected Case.
- Customer-declared Release Change; no automatic impact or applicability
  inference.
- Explicit approved baseline and GitHub candidate.
- Execution inside customer CI.
- Triana deterministic assertions plus one customer-owned JSONL evaluator
  command.
- Separate behavioral failures, evaluation gaps, and non-comparability.
- Advisory PASS/REVIEW/BLOCK as the Release Recommendation, never the human
  Release Decision.
- Immutable Release Evidence Record.
- One Release Review joining evidence, gaps, policy reasoning, recommendation,
  and any linked Decision Attestation.
- Existing GitHub/release workflow remains the V1 human authority surface.
- One case free; $500/month design-partner pilot.
- Closed-source distribution.

## Active hypotheses

| ID | Hypothesis | Evidence required | Status |
|---|---|---|---|
| H1 | At least one-third of important incidents for eligible teams become `READY` without Triana engineering | Qualification attempts across first three eligible teams | Untested |
| H2 | A new engineer reaches the first real record in under one working day | Timed external M1 | Untested |
| H3 | The Release Review changes a merge/release action or materially improves the release conversation | Before/after decision interview tied to a real PR | Untested |
| H4 | Teams retain protected cases across at least three releases | Longitudinal partner usage | Untested |
| H5 | Teams will pay $500/month for repeated records before mandatory enforcement exists | Direct pilot purchase | Untested |
| H6 | After advisory trust, at least one team asks for enforcement | Partner request backed by usage | Untested |
| H7 | The customer-command lane adds a unique release action rather than duplicating Braintrust/DeepEval/LangSmith | Side-by-side workflow on customer stack | Untested |
| H8 | A consequential release's change, obligations, evidence, decision, and later outcome are fragmented across systems or people in a way that creates measurable cost, delay, uncertainty, or escaped failures | Artifact-based reconstruction using the discovery ask guide | Untested |

## Immediate build sequence

Every slice below uses the three-role protocol in `docs/ENGINEERING.md` and the
live `internal/SLICE_PACKET.md`: main orchestrator → independent test author
with valid RED → orchestrator test freeze → independent implementation author
→ orchestrator seed/adversarial/full-gate verification. Worker edits are
serial in the shared worktree.

### Phase 0: record-first visible kernel

Keep four small top-level, versioned contracts:

1. normalized trace;
2. protected case;
3. release evidence record;
4. record chain.

Nested typed primitives include execution contract, trial result, assertion
result, customer-evaluator result, Release Change, Release Obligation fields,
evidence requirements, evidence gap, comparison, Release Policy evaluation,
recommendation, and Decision Attestation. Do not turn every nested type into a
separately deployed service or storage system.

#### Slice 0A: contract kernel

- strict parsing and versioning;
- canonical serialization;
- stable identity and hashing;
- golden A/A, A/B, gap, and tampered fixtures;
- record round-trip verifier.

Proof: changing any protected field invalidates verification while a valid
record survives serialize, reload, and verify without semantic drift.

Initial orchestrator seed/fixture matrix:

- canonical A/A control;
- planted A/B regression;
- missing approved baseline;
- mismatched execution contract;
- partial evidence or evaluator timeout;
- protected-field tampering;
- order permutation that must preserve canonical identity;
- same declared input repeated twice to detect nondeterminism.

#### Slice 0B: comparison and Release Policy

- explicit comparability;
- pass and evaluable denominators;
- typed gaps and weakest supported claim;
- deterministic PASS/REVIEW/BLOCK;
- record-chain verification.

Proof: A/A passes, planted A/B blocks, missing baseline becomes
`FIRST_OBSERVATION`, mismatched execution becomes `MOVED`, missing evidence
reviews, and tampering is rejected.

#### Slice 0C: first visible Release Review

Build one permanent-page projection over the exact same fixture records and
Decision Attestation contracts used by the core verifier. Show identity,
declared change, obligation, required and received baseline/candidate evidence,
named risks, gaps, policy reasoning, recommendation, hash verification, and
decision state.

Proof: a human can inspect the planted regression and understand what changed,
why the policy recommends BLOCK, what remains unknown, and whether a human
decision is pending. The UI performs no independent release arithmetic.

The product is visible and usable against deterministic fixtures by the end of
the third slice. Do not wait for real trace ingestion, authentication, billing,
or paired customer execution before showing the Release Review.

### Phase 1: acquisition — Connect → Surface → Promote

Mine only permitted Kairos/Kairos-AI code after provenance review. Build:

- one trace adapter;
- deterministic candidate signals and ranking;
- a six-to-nine-field protected-case proposal;
- human review and Promotion;
- qualification state.

Proof: one real incident becomes a promoted case in under 15 minutes.

### Phase 2: recurring product — local `triana check` → Release Review

Implement the paired execution contract:

- explicit baseline and candidate refs;
- isolated runtimes;
- same case and fixture fingerprint;
- repeated trials;
- deterministic assertions;
- optional customer JSONL evaluator;
- gap/comparability logic;
- Release Evidence Record and verification;
- Release Policy recommendation;
- Release Review with a linked GitHub Decision Attestation.

Proof: the reference agent produces honest A/A and planted A/B rates, a policy
recommendation, and a Release Review that keeps the human decision separate
through an append-only Decision Attestation.

### M0: public reproducibility

Publish the reference agent and every customer-visible artifact. Keep Triana
source private. A skeptic must reproduce the record using the shipped
container.

### M1: real partner

Run one retained case on one real PR with no bespoke Triana integration code.

### Alpha

Open only after M0 and one successful M1.

## Do not build yet

- authentication or billing before a slice needs them;
- microservices, Kubernetes, event buses, or a general workflow engine;
- a broad dashboard or large design system;
- performance infrastructure without a measured bottleneck and target;
- full scan, clustering, and coverage maps;
- behavior-family inference;
- Triana-owned LLM judges;
- automatic ground truth;
- simulation platform or managed sandbox;
- provider-specific evaluator adapters;
- automatic eval-set maintenance, issue-to-fix generation, or agent
  self-modification;
- visual release policy;
- automatic blocking;
- rollout and rollback;
- compliance packaging;
- dashboards;
- SDK/re-instrumentation layer;
- open-source core.

## Open implementation decisions

- **Language and monorepo shape:** TypeScript across contracts, core, CLI, API,
  and UI is the current speed/readability candidate because it minimizes
  cross-language contract duplication. It is not accepted yet. Decide with a
  short Slice 0A spike against canonical serialization, hashing, CLI
  distribution, container size, test speed, and code readability.
- **Persistence:** fixtures and files are sufficient for Slice 0A–0C unless
  record-chain acceptance tests prove otherwise. Do not select hosted storage
  before that evidence exists.
- **UI framework:** choose only after the contract kernel exposes the exact
  Release Review projection. The UI must consume core outputs rather than own
  domain logic.

## Engineering dogfood

Adopt the proven shape of Kairos-AI's CI practices, not its product semantics:

- one local command shared by CI;
- format, lint, strict type, complete tests, and build/package gates;
- deterministic round-trip, seeded sampling, corpus/fixture hashes, and
  tamper rejection;
- negative architecture and redaction guards;
- artifact-derived published-claim consistency when M0 values appear.

Do not inherit unlocked dependency installs, informational-only coverage,
moving CI action tags, fail-fast-only CI reporting, or silent integration-test
skips.

Kairos-AI coding-agent and development-session corpora are outside the frozen
conversational-agent V1. They may later stress an adapter or reproducibility
tool under an explicit `engineering_dogfood` label, pinned source ref, runtime,
fixture hash, and refusal to make a V1 product claim.

## Customer evidence log

Add one row per real qualification or release attempt.

| Date | Customer/agent | Eligibility | Incident | Qualification | Time to Release Review | Decision changed? | Retained? | Payment signal | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Change rule

- One request: record it.
- Repeated blocker among eligible teams: create a focused discovery test.
- Paying team cannot complete core loop: test ICP or contract.
- Record changes no release behavior: reconsider the wedge.
- Nice-to-have feedback: preserve scope.

Only an explicit decision may modify `docs/PRODUCT.md`.
