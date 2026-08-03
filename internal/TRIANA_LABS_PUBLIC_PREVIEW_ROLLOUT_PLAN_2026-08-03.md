<!-- Hallmark · pre-emit critique: P5 H5 E4 S5 R5 V4 -->

# Triana Labs public Preview rollout and deferred-work register

Date: 2026-08-03

Status: **OWNER-DIRECTED ROADMAP; IMPLEMENTATION SLICES NOT YET FROZEN**

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
| LABS-06 | Regular-user simulator fidelity | Yes for the adaptive claim |
| LABS-07 | Machine-readable public report and static projection contract | Yes |
| LABS-08 | Triana Labs demo UI over the frozen report | Yes |
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

## 4. LABS-07 — report contract and static projection

The UI must be a projection of evidence rather than a second reasoning engine.

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

## 5. LABS-08 — Triana Labs demo UI

### Provenance entry gate

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
| `/` | What did this run test, and what evidence is complete or missing? |
| `/cases` | Which grounded user situations were selected, excluded, or deduplicated? |
| `/episodes/[episode_id]` | How did the simulated user adapt to each target response? |
| `/coverage` | Which personas, intents, behaviors, and trajectories are represented? |
| `/evidence` | What lineage, cost, fidelity, privacy, and gaps support the visible claims? |
| `/setup` | How can a developer reproduce the demo or connect an agent locally? |

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
files are copied during this planning slice.

## 6. LABS-09 — public packaging and one-command demo

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

## 7. LABS-10 — usable design-partner alpha

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

## 8. Consolidated deferred-work register

### A. Required before Exit A

- LABS-06 simulator-fidelity repair and 30-item human gate;
- report JSON and static projection contract;
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

## 9. What is explicitly not blocking the first public proof

- persistent/global or emotional memory;
- baseline/candidate comparison;
- a model judge;
- arbitrary real-data upload;
- generic provider/agent SDKs;
- hosted execution or accounts;
- the old HRAI environment repair;
- broad evaluation expansion;
- PASS/BLOCK or release-control semantics.

## 10. Decisions still needed before implementation

The orchestrator should recommend defaults, but these owner gates remain:

1. Accept the LABS-06 30-item/24-accepted/zero-critical fidelity gate.
2. Choose whether Exit A's public sample is a newly generated synthetic run or
   a fully synthetic reconstruction of the private HRAI canary shape.
3. Clear the Triana demo immutable source snapshot and per-file ancestry, or
   direct clean-room reimplementation of the design system.
4. Confirm Next.js 15 + React 19 + npm as the web stack after dependency audit.
5. Select the open-source license and contribution policy.
6. Select the static hosting destination for the read-only demo.
7. For Exit B, select the first documented BYOK simulator provider boundary
   and the first independent installation participant.

## 11. Planning-slice contract and verification

Active outcome: make the route from LABS-05 evidence to an honest public
Preview explicit while preserving every deferred capability.

Inputs: charter, canonical plan, LABS-05 closure/fidelity review, working
memory, provenance ledger, current CLI/package, and the allowlisted local demo
snapshot.

Outputs: this roadmap, canonical references, and an append-only decision that
public Preview/UI planning is now the immediate product direction.

Authority: deterministic code will own report identities and calculations;
the UI will only project; models may propose cases/turns/explanations; humans
own usefulness, fidelity rulings, and persistent meaning.

Privacy/execution: planning only; no egress. Exit A remains synthetic-only and
read-only. Exit B requires a separately frozen local-sensitive contract.

Gaps/refusal: unclear UI ancestry blocks reuse; failed fidelity blocks the
adaptive claim; missing license blocks public source publication; missing
privacy/egress proof blocks real/local-sensitive use.

Provenance: no external implementation is copied in this slice. The Triana demo
is inspected only as an allowlisted planning source.

Change budget: this document plus `triana-labs/CHARTER.md`, the current Labs
plan, `internal/WORKING_MEMORY.md`, `internal/DECISION_LOG.md`, and `README.md`;
no production, test, dependency, lock, UI, schema, fixture, or provenance-ledger
edit.

Acceptance: governance, decision append-only verification, link/path review,
`git diff --check`, and change-budget reconciliation. The complete Python suite
is not claimed from this documentation-only slice unless it is actually run.
