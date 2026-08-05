<!-- Hallmark · pre-emit critique: P5 H5 E4 S5 R5 V4 -->

# Triana Labs public Preview rollout and deferred-work register

Date: 2026-08-03

Status: **OWNER-DIRECTED ROADMAP; LABS-06 CLOSED; COMBINED LABS-07/08 WIREFRAMES ACCEPTED**

This plan turns the completed LABS-04 machinery and the closed-but-unpassed
LABS-05 evidence into the shortest honest path to a public, YC-demonstrable
Triana Labs Preview. It also consolidates work deliberately deferred by the
charter, canonical plan, LABS-04, and LABS-05 so that shipping the first public
surface does not erase the longer roadmap.

This is a planning slice only. It adds no provider call, target execution,
real-data support, UI code, dependency, public license, or release claim.

## 1. Product outcome

The first public iteration should let a developer see and reproduce this value
moment:

> Triana turns an authorized conversational trace corpus into grounded user
> situations, runs adaptive simulated users against an existing agent, and
> shows the resulting conversations, coverage, cost, fidelity, and gaps without
> inventing a pass, regression, or release verdict.

The rollout has two distinct exits.

### Exit A — public proof and YC surface

- public static read-only demo URL with publication-safe synthetic evidence;
- local `triana preview demo` from a clean clone without a provider key;
- machine-readable report and the same report rendered in the UI;
- installation, architecture, privacy, and connector documentation;
- no account, trace upload, hosted execution, or claim that arbitrary real
  customer traces are supported.

This exit is suitable for a YC application, demo video, public repository, and
early developer feedback. It proves the product shape and deterministic local
workflow, not self-serve real-agent onboarding.

### Exit B — usable design-partner alpha

- an authorized real/local-sensitive trace path with pre-hash redaction and
  provider-named egress consent;
- one documented BYOK simulator configuration;
- restricted HTTP/JSON and executable target connector setup;
- a qualified external developer completes a real-agent run without
  founder-written integration;
- the existing M3.5 gate: report within 90 minutes, no more than 200 adapter
  lines, understood fidelity/denominators/gaps, and plausible repeat use.

Exit B, not the static demo, proves the self-serve claim.

## 2. What comes after LABS-05

The historical plan already placed three capabilities after the runner:

1. M3A report schema, static HTML, and paired transcript projection;
2. M3B one-command public demo and documentation;
3. M3.5 stranger installation gate;
4. only after M3.5, M4 persistent rulings and ProtectedCase draft promotion.

The UI category is therefore not new. The new decision is to prioritize the
specific allowlisted Triana demo visual package as the public Labs surface and
to insert the supported simulator-fidelity repair exposed by LABS-05 before
making the adaptive-generation claim.

The new checkpoint sequence is:

| Checkpoint | Outcome | Public blocker? |
|---|---|---:|
| LABS-06 | Regular-user simulator fidelity — closed with accepted backlog | Cleared for the bounded adaptive claim |
| LABS-07/08 | Canonical report and full-journey Triana Labs UI vertical slice | Yes |
| LABS-09 | One-command demo, packaging, docs, license, CI, and static publication | Yes for Exit A |
| LABS-10 | Authorized local-sensitive data path and stranger installation | Yes for Exit B |
| LABS-11 | Persistent human rulings and next-run application | No; begins only after LABS-10 |

Baseline/candidate comparison remains the longer product roadmap. It is not
required to publish the generated-multi-turn Preview honestly.

## 3. LABS-06 — regular-user simulator fidelity

This checkpoint closes the supported R2 failure before UI polish amplifies a
bad adaptive turn.

The new-session planning and owner-question entry protocol is frozen in
`internal/LABS06_HANDOFF_2026-08-03.md`. The first LABS-06 turn must produce
the LLD/spec, essential edge cases, minimal-test proposal, and material owner
questions, then wait. It may not begin implementation before Akarsh answers and
the LABS-06 slice packet replaces the closed LABS-05 packet.

Minimum scope:

- pass verified persona, intent, known facts, and **user-owned** turn policy to
  every simulator request;
- add bounded episode-local interaction state: patience, trust, urgency,
  confusion, goal satisfaction, and remaining disclosures;
- keep personality stable while interaction state changes deterministically;
- require exactly one natural user utterance and structured stopping;
- reject assistant-role inversion, exact/near target echo, hidden-fact leakage,
  fixed-fact conflict, and unauthorized action as typed semantic gaps;
- evaluation mode records failure without repair or fallback;
- generation mode may permit one separately counted regeneration while
  retaining the original rejection;
- freeze `REGULAR_USER_SIMULATION_FIDELITY_V1`: 30 stratified teacher-forced
  items, at least 24 accepted by the owner-approved rubric, and zero critical
  semantic violations;
- retain free-running adaptive episodes as the secondary feedback-loop test.

Persistent/global memory, judges, model tournaments, and broad eval import are
not part of LABS-06.

### LABS-06 closure — 2026-08-04

LABS-06 is `CLOSED_WITH_ACCEPTED_BACKLOG`. The final owner-authorized
twelve-case run created three valid/effective trajectories: one valid
single-turn stop and two genuine six-role-turn conversations. Akarsh accepted
Conversations 3 and 4. The checkpoint may support the bounded statement that
Triana enforces deterministic simulator controls, is compatible with the named
live provider boundary, and generated genuine adaptive multi-turn execution.
It may not support universal realism, production-grade fidelity, or a
twelve-of-twelve success claim.

The original 30-item/24-accepted/zero-critical gate is no longer required to
exit LABS-06; it remains future calibration before any population-level
fidelity claim. Accepted backlog comprises a generic claimed-world-mutation
authority guard, explicit intent-precondition enforcement, a longer aggregate
deadline for future twelve-case runs, and separately scoped target
protocol/tool-budget readiness. These items do not block the combined
LABS-07/08 slice, but its report and UI must expose them as limitations and
typed gaps.

## 4. LABS-07/08 — canonical report and full-journey Labs UI

LABS-07 and LABS-08 are one vertical slice. The UI must remain a projection of
evidence rather than a second reasoning engine, but the minimum report contract
and real UI are designed, implemented, and verified together. This avoids a
speculative reporting layer while preserving a strict machine boundary.

The complete owner-accepted terminology, behavior, and ASCII screens are
`internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md`. The exact
decision-driving prompts and copyable build-session restart are
`internal/LABS07_08_BUILD_HANDOFF_2026-08-04.md`. They supersede any earlier
informal wireframe summary where wording or route structure differs.

Accepted top-level rail: Overview, User behavior, Cases, Runs, and Review.
Setup precedes the persistent rail; conversation and evidence views are
drill-down surfaces. Setup supports one local trace file only. Trace
understanding exposes explicit denominators rather than an opaque score.
`World availability` remains the umbrella, with `Case data items` as its
currently specified subsection. Each case produces one independent
conversation. Human review records four independent rulings for realism,
adaptation, goal completion, and scope/privacy/boundary compliance; there is no
aggregate verdict or automatic memory mutation.

### Complete user journey

The wireframes must cover the product from first contact to retained review:

1. understand the local-first privacy model and authorize a trace source;
2. inspect ingestion, normalization, exclusions, redaction, and lineage;
3. understand the observed corpus and derived personas, intents, and behaviors;
4. inspect observed and grounded-expanded cases plus selection and dedupe;
5. review provider, target, privacy, world, budget, and execution preflight;
6. follow run progress and distinguish complete, partial, unavailable, and
   not-started episodes;
7. inspect adaptive conversations as the primary evidence object;
8. understand coverage, cost, HTTP/tool accounting, fidelity, and typed gaps;
9. inspect human review without inventing a ruling; and
10. understand known limitations, carried backlog, and next-run implications.

Exit A remains read-only: setup explains and previews the journey but accepts
no uploads, credentials, provider calls, target execution, or mutable review.
Interactive local setup and execution remain later packaging/onboarding work.

### Canonical report boundary

Required machine-readable report sections:

- run identity, mode, privacy/fidelity labels, target connector, simulator
  identity, budget, and lineage;
- source denominator and accepted/rejected trace counts;
- personas, intents, turn policies, cases, selection/exclusion reasons, and
  duplicate clusters;
- episode status, transcript turns, observed tool events, termination, cost,
  HTTP accounting, and typed gaps;
- adaptation and simulator-fidelity review states;
- explicit unsupported claims and unavailable target-internal evidence;
- links/hashes from every visible fact to its source artifact.

The renderer may order, filter, and format this artifact. It may not calculate
new acceptance, dedupe, cost, fidelity, or pass/fail truth.

Acceptance requires complete, partial, gaps-only, long-transcript, narrow-
viewport, redacted, and missing-field fixtures. Static-render failure must not
destroy or change the machine-readable report.

The first implementation adds only fields required by an accepted journey
screen or a non-negotiable custody/lineage rule. JSON, Markdown, and UI agree
from the same fixture; the UI cannot become the source of truth.

### Triana demo provenance entry gate

The allowlisted source is currently located at
`/Users/akarshgajbhiye/agentagon/triana-demo-clean-video`. It is a local
untracked directory relative to Agentagon commit
`063ad3ed54f4a9646e7040cc6a203615b0de8dcd`; that commit alone does not identify
the package's file bytes or ancestry.

Before any reuse:

1. freeze an exact hash manifest of proposed source files;
2. establish authorship, license, and upstream ancestry per file;
3. confirm no file is an ineligible Agentagon port;
4. record source, hash/commit or owner-authorized immutable snapshot,
   destination, and copy/adaptation method in `docs/PROVENANCE.md`;
5. exclude any file whose provenance cannot clear and reimplement that part.

The probable reusable surface is the paper-and-ink shell, tokens, layout,
navigation interaction, drawers, and responsive styling—not the old Release
Review data model, PASS/BLOCK logic, snapshots, release memory, or claims.

### Labs information architecture

The active Preview should answer operational questions rather than reproduce
the suspended Release Review screens:

| Route | Question answered |
|---|---|
| `/` | Where am I in the trace-to-review journey, and what can I inspect next? |
| `/setup` | What stays local, what must be authorized, and what preflight is required? |
| `/traces` | What entered, was excluded, was normalized, and was derived from the corpus? |
| `/cases` | Which grounded user situations were selected, excluded, or deduplicated? |
| `/runs/[run_id]` | What was configured, what happened, and which episodes completed or became gaps? |
| `/episodes/[episode_id]` | How did the simulated user adapt to each target response? |
| `/coverage` | Which personas, intents, behaviors, and trajectories are represented? |
| `/evidence` | What lineage, cost, fidelity, privacy, and gaps support the visible claims? |
| `/review` | What did the human accept, reject, leave unavailable, or carry as backlog? |

The first public UI is read-only. No approve, edit-memory, rerun, upload,
credential, billing, or target-control action ships in Exit A.

### Design and verification constraints

- preserve the demo's warm paper, dark ink, restrained green/red/amber,
  compact operational hierarchy, monospace evidence metadata, and row/drawer
  interaction where provenance permits;
- replace Release Review semantics with Labs terms; never show PASS, BLOCK,
  regression, accepted behavior, or release recommendation for Labs evidence;
- make the transcript the primary evidence object, not a decorative card;
- show fidelity and gaps beside the claim they qualify;
- support keyboard operation and 320, 375, 414, 768, 1280, and 1440 widths;
- use named design tokens; no invented customer metrics, logos, testimonials,
  or fake browser/IDE chrome;
- browser smoke verifies every route, no horizontal overflow, no broken asset,
  and source-to-visible-value agreement.

The proposed destination is `triana-labs/web/` using the existing package's
Next.js/React/npm stack only if provenance and dependency review pass. No UI
files are copied during this planning slice. Wireframes must be accepted before
the implementation packet freezes routes or components.

## 5. LABS-09 — public packaging and one-command demo

Exit A requires all of the following:

- `triana preview demo` materializes or opens a checked-in publication-safe
  synthetic run and report without provider credentials;
- a separate live command/config path clearly requests BYOK provider consent;
- a clean clone installs and renders the exact public sample reproducibly;
- root README reflects LABS-04/LABS-05 truth and leads with the public loop;
- quickstart, artifact, target-connector, simulator, privacy/egress,
  troubleshooting, and contribution docs exist;
- one HRAI-shaped connector example and one non-HRAI stateless example use
  synthetic fixtures only;
- local verification and CI execute the same Python and web gates;
- repository license and contribution policy are explicitly accepted;
- dependency licenses, UI provenance, secrets, local absolute paths, private
  artifacts, raw HRAI/Blitz data, and generated provider payloads are audited;
- public claims regenerate from checked-in inputs and commands;
- the static public site has no upload, auth, database, secret, or execution
  backend;
- YC screenshots/video show only supported public-sample facts.

Exit A does not wait for persistent memory, baseline/candidate diff, judges,
real customer data, or a hosted product backend.

## 6. LABS-10 — usable design-partner alpha

After the public proof is stable:

- add `LOCAL_SENSITIVE`/equivalent authorized local trace handling;
- run redaction and egress validation before hashing and provider calls;
- name the provider, permitted fields, retention, and customer/operator key;
- generalize the simulator only to one documented BYOK OpenAI-compatible or
  equivalent boundary; do not create a broad provider SDK;
- provide restricted declarative HTTP mapping plus strict executable bridge
  templates;
- add preflight diagnostics that make endpoint/session/response mapping errors
  actionable without echoing secrets;
- run the M3.5 stranger protocol with one independent real-agent developer,
  then up to five qualified teams at one or two onboardings per week;
- retain every clarification, intervention, adapter-line count, elapsed time,
  cost, gap, and willingness-to-repeat answer.

Failure narrows onboarding or product scope. It does not justify hosted
infrastructure or founder-written bespoke integrations.

## 7. Consolidated deferred-work register

### A. Required before Exit A

- LABS-06 bounded simulator-fidelity closure — completed with accepted backlog;
- combined canonical report and full-journey read-only UI;
- publication-safe synthetic reference run;
- Triana demo file-level provenance and Labs IA rewrite;
- read-only responsive UI and evidence-linked transcript view;
- one-command no-key demo;
- clean-clone package/build/CI parity;
- public license and contribution policy;
- privacy, egress, secret, provenance, dependency-license, and absolute-path
  publication audit;
- public README, quickstart, connector, artifact, and troubleshooting docs;
- generated YC/demo assets grounded only in the public sample.

### B. Required before Exit B

- authorized local-sensitive/real trace path;
- redaction and provider-named egress consent before hash/call;
- one usable BYOK simulator configuration;
- connector templates and diagnostic preflight;
- adapter line-budget measurement;
- M3.5 independent stranger installation;
- DIY-agent comparison on identical inputs;
- five-team qualification/application funnel and onboarding evidence.

### C. Quality and evaluation backlog

The canonical LABS-06 backlog is
`internal/LABS06_BACKLOG_2026-08-04.md`. It is required deferred work and must
not be erased by this shorter summary.

- representative retrieval-quality set;
- clarification-question material-relevance evaluation;
- persona/intent/turn-policy support and ambiguity calibration;
- emotion/interaction-state realism without persistent emotional memory;
- multi-turn rubric-quality evaluation;
- human case-usefulness calibration;
- optional model-judge calibration only after human ground truth exists;
- frozen prompt/model comparisons;
- case, turn, and trajectory exact/near-duplicate measurement;
- effective-N and diversity thresholds;
- HTTP-level model-call, token, and cost accounting across agent loops;
- target-internal telemetry contract where an endpoint can report it;
- target state-isolation tests and typed uncertainty where it cannot;
- multilingual, homogeneous-corpus, small-corpus, and missing-user-turn cases.

### D. Post-M3.5 product roadmap

- separate simulator validity, behavioral fidelity, and target-agent outcome
  into independently reported evidence lanes;
- deterministic behavioral telemetry for fact front-loading, information
  release, clarification, repetition, pushback/error reaction, recovery or
  abandonment, and turn/conversation length;
- scenario truth that distinguishes essential facts, request-gated facts,
  flexible preferences, and non-negotiable constraints;
- trace-grounded factorial behavior panels, initially information precision,
  assertiveness, and ordinary/stress strata, with deterministic panel identity
  and no unsupported production-frequency claim;
- held-out same-task/same-agent human or authorized real-user calibration,
  including a measured human-human ceiling and separately reported
  communication, information, clarification, error-reaction, and outcome
  calibration dimensions;
- prompt/model comparisons that disclose cross-dimension regressions and
  choose simulators by measured fidelity rather than general capability;
- policy/tool coverage graphs and coherent symbolic world-state fixtures whose
  weights are grounded in authoritative policy, observed traces, or human
  rulings rather than LLM-estimated prevalence;
- optional dimension-specific model judges only after frozen human calibration,
  with recorded identity and no generate/simulate/judge authority monoculture;
- append-only human-confirmed persistent rulings;
- compatible next-run retrieval and stale/conflict handling;
- ProtectedCase draft promotion with human completion;
- baseline/candidate shared-prefix paired execution;
- deterministic diff, stability, comparability, denominators, and divergence;
- labeled F1 continuation after divergence;
- customer-owned evaluators and optional LLM judges with recorded identity;
- real-data support beyond the bounded local-sensitive alpha;
- broader connectors, multi-target orchestration, A2A, or generic SDKs;
- broader eval imports/scorer authoring;
- browser, voice, code, and other universal-agent support;
- managed/global memory, autonomous prompt/model training, and optimization;
- hosted ingestion, accounts, storage, execution, dashboards, auth, billing,
  and SaaS control plane;
- Guard/enforcement, deployment, rollout, rollback, or release verdicts;
- resumption or merger of the suspended Release Review V1.

### E. Historical/optional diagnostics, not launch blockers

- repair the old local HRAI Postgres/Redis environment if it is useful for
  repeatable dogfooding;
- add deeper HRAI target-internal usage/state reporting only if HRAI chooses to
  expose it;
- investigate alternative simulator providers only after the frozen fidelity
  benchmark exists;
- preserve and learn from the consumed real canary; do not rerun it merely to
  obtain a favorable result.

## 8. What is explicitly not blocking the first public proof

- persistent/global or emotional memory;
- baseline/candidate comparison;
- a model judge;
- arbitrary real-data upload;
- generic provider/agent SDKs;
- hosted execution or accounts;
- the old HRAI environment repair;
- broad evaluation expansion;
- PASS/BLOCK or release-control semantics.

## 9. Decisions still needed before implementation

The orchestrator should recommend defaults, but these owner gates remain:

1. ~~Accept the full-journey information architecture and wireframes for the
   combined LABS-07/08 slice.~~ Accepted on 2026-08-04 in the normative
   wireframe specification.
2. Choose whether Exit A's public sample is a newly generated synthetic run or
   a fully synthetic reconstruction of the private HRAI canary shape.
3. Clear the Triana demo immutable source snapshot and per-file ancestry, or
   direct clean-room reimplementation of the design system.
4. Confirm Next.js 15 + React 19 + npm as the web stack after dependency audit.
5. Select the open-source license and contribution policy.
6. Select the static hosting destination for the read-only demo.
7. For Exit B, select the first documented BYOK simulator provider boundary
   and the first independent installation participant.

## 10. Planning-slice contract and verification

Active outcome: turn the completed LABS-04/05/06 evidence path into one
full-journey report-and-UI vertical slice while preserving every deferred
capability.

Inputs: charter, canonical plan, LABS-05 closure/fidelity review, working
memory, provenance ledger, current CLI/package, and the allowlisted local demo
snapshot.

Outputs: this consolidated roadmap, canonical references, and an append-only
decision that LABS-07/08 wireframes and minimum report/UI contract are now the
immediate product direction.

Authority: deterministic code will own report identities and calculations;
the UI will only project; models may propose cases/turns/explanations; humans
own usefulness, fidelity rulings, and persistent meaning.

Privacy/execution: planning only; no egress. Exit A remains synthetic-only and
read-only. Exit B requires a separately frozen local-sensitive contract.

Gaps/refusal: unclear UI ancestry blocks reuse; unaccepted wireframes block UI
implementation; missing license blocks public source publication; missing
privacy/egress proof blocks real/local-sensitive use. LABS-06 accepted backlog
must remain visible but does not block the bounded adaptive claim.

Provenance: no external implementation is copied in this slice. The Triana demo
is inspected only as an allowlisted planning source.

Change budget: this document plus `triana-labs/CHARTER.md`, the current Labs
plan, `docs/ARCHITECTURE.md`, `internal/SLICE_PACKET.md`,
`internal/WORKING_MEMORY.md`, `internal/DECISION_LOG.md`, and `README.md`; no
production, test, dependency, lock, UI, schema, fixture, or provenance-ledger
edit.

Acceptance: governance, decision append-only verification, link/path review,
`git diff --check`, and change-budget reconciliation. The complete Python suite
is not claimed from this documentation-only slice unless it is actually run.
