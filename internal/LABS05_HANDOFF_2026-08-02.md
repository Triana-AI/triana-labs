# LABS-04 close and LABS-05 session handoff

Date: 2026-08-02

Status: **canonical restart context; LABS-05 not yet frozen**

Authority: `triana-labs/CHARTER.md` → `internal/DECISION_LOG.md` →
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`

This file exists so a fresh coding-agent session does not rediscover LABS-04,
repeat failed provider experiments, assume an internal POC is a public product,
or silently expand LABS-05. It is a handoff, not an implementation packet.
Before LABS-05 code, replace the closed LABS-04 packet in
`internal/SLICE_PACKET.md` with a separately owner-approved LABS-05 packet.

## 1. Exact ground truth

- Scale-out evidence close commit: `54c94c0`; supported CLI commits:
  `17238b7`, `46e58f3`, and verifier reconciliation `6f93ed7`.
- Full verifier: 408 tests, Ruff, strict mypy, deterministic Observer replay,
  five unchanged canonical Observer hashes, sdist/wheel build, clean CPython
  3.13 installation, and source/wheel parity.
- Final verifier evidence: `/private/tmp/triana-labs-verify.88h0RL`.
- LABS-04 live bundle:
  `/private/var/folders/9p/yg9qq11906q49n6p614_f44r0000gn/T/`
  `triana-labs04-scaleout-close.c5y15ryg/resumed`.
- Durable owner-review copy (portable artifacts only; no private provider
  cache): `/Users/akarshgajbhiye/Documents/`
  `Triana-LABS04-scaleout-close-2026-08-02/`. All 12 artifact hashes and the
  manifest hash were reverified after copying.
- Manifest file SHA-256:
  `817000637daef25bff9bd95eee46a25976f575d1b2d5aa62965a6c6d9c5b6cb9`.
- Case-candidate file SHA-256:
  `06a3a2267f39041d98e08ef24466ffbc695e7833ebb16bd536f19f71c37ecbe4`.
- Readable denominator/case review:
  `internal/LABS04_CASE_REVIEW_2026-08-02.md`; it records that zero production
  traces were used, 50 synthetic source records yielded 25 adapter outputs,
  all 25 were Observer-eligible, and the final panel cites 8 unique traces
  across 6 structural clusters. A byte-identical owner copy is at
  `/Users/akarshgajbhiye/Documents/LABS04_CASE_REVIEW_2026-08-02.md`.
- All 12 manifest-declared artifact hashes match their files.
- Result: five requested, five valid, five deterministically distinct, zero
  gaps, zero repairs, and zero duplicate clusters.
- Accounting: six logical restricted-runtime invocations, fourteen captured
  provider HTTP exchanges, USD `12.000000` conservative reservation under a
  USD `25.000000` ceiling, and unknown actual cost.
- Product status: LABS-04 machinery is complete; the checkpoint is
  `AWAITING_HUMAN_REVIEW` under `LABS04_USEFULNESS_V1`.

## 2. What exists now

| Checkpoint | Shipped boundary | Important limitation |
|---|---|---|
| LABS-01 Trace Observer | Validates synthetic `PreviewTrace` JSONL and publishes five deterministic corpus artifacts | Synthetic only; five canonical artifact hashes are frozen |
| LABS-02 reference adapter | Copyable HRAI normalized-trace-v2 → `PreviewTrace` JSONL executable example | File contract, not an SDK or supported HRAI integration; 25/50 selected smoke records accepted and 25 explicitly rejected |
| LABS-03 structural Corpus Intelligence | Verifies Observer bundles and derives 22 structural clusters plus explicit semantic gaps | No semantic persona/intent/policy derivation by deterministic code |
| LABS-04 Grounded Case Factory | Supported strict config-dispatched `cases generate` plus immutable `cases resume` expose the restricted GLM-5.2 runtime and grounded proposals | Synthetic only; no target execution, real-data path, memory, judge, or UI |

The public CLI now dispatches from the exact config artifact kind. The checked-in
`restricted-case-factory-config.json` selects only the pinned GLM-5.2 runtime;
existing `case_factory_config` inputs retain the legacy path. Unknown kinds or
malformed provider state refuse without fallback. `cases resume` requires the
same exact config bytes, complete bounded answers, the immutable pause bundle,
and the same private cache. This closes LABS-04's synthetic CLI surface; it does
not authorize target-agent execution or real/customer traces.

## 3. Decisions that must not be reopened without new evidence

### Authority

- The model proposes semantic personas, intents, turn policies, cases, future
  turns, rubrics, and explanations.
- Deterministic Triana code owns identity, evidence resolution, support,
  lineage, selection, duplicate arithmetic, budgets, attempt state, HTTP
  accounting, termination, and publication.
- Only a human ruling may turn proposed behavior or evaluation evidence into
  accepted local truth or persistent learning memory.

### Provider and harness

- Current provider/deployment: Microsoft Foundry Fireworks
  `FW-GLM-5.2`, version `1`, with no model fallback.
- Current harness: LangChain `create_agent`, backed by LangGraph, with exactly
  four model-callable tools: `search_evidence`, `get_trace_packet`,
  `inspect_budget`, and `submit_case_batch`.
- DeepAgents was deliberately not used for LABS-04 because its coding,
  filesystem, todo, summarization, and `task` scaffolding expanded the surface.
  It remains a candidate only when LABS-05 demonstrates a need for specialist
  delegation or a long-lived simulator session.
- DeepEval remains a parked leading turn-loop candidate. It is not an accepted
  dependency; adoption requires a bounded conformance comparison against the
  smallest Triana-owned reference loop.

### Execution and failure behavior

- Exact-five scale-out uses five deterministic one-case slots. A slot fails
  fast, later funded slots continue, and every valid and invalid attempt is
  preserved.
- No transport retry, rerun-to-green, hidden repair, provider fallback,
  deterministic semantic synthesis, citation remapping, or silent case-count
  shrinkage is allowed.
- `provider_call_count` means logical GENERATE/REPAIR invocations.
  `provider_http_exchange_count` means captured provider requests inside the
  agent loop. Actual USD stays `null` when the provider does not expose it.
- Owner answers are authoritative across all pending exact-five slots; later
  slots cannot reopen clarification.
- Duplicate cases or future trajectories never increase effective N.

### Privacy and product boundary

- The implemented path is synthetic-only. The HRAI smoke is labeled
  `SYNTHETIC_EXISTING_TRACE_CORPUS`, not real/customer/production evidence.
- No generic SDK, OTel ingestion, hosted ingestion, SaaS, real-data support,
  baseline/candidate diff, release verdict, UI, or global memory is authorized.
- Raw HRAI data, provider payloads, keys, and temporary private diagnostics do
  not enter Git.

## 4. Failed paths already explained by evidence

Do not repeat these as exploratory work:

1. The originally named HRAI `run_50b` file is a legacy schema and produced
   0/50 adapter acceptance. The corrected smoke is the first 50 physical lines
   of tracked v2 `run_200`, selected SHA-256
   `4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c`.
2. The old Azure `gpt-4.1-mini` propose/critique/revise experiment is historical,
   not the current provider design.
3. Asking one model to submit five fully linked cases at once exhausted 32,768
   completion tokens and emitted empty tool arguments. Scale through one-case
   slots, not another monolith.
4. Merely requiring a tool did not make the model submit: literal retrieval
   caused repeated searches and rate limiting. Ranked bounded retrieval plus a
   monotonic search → named trace → named submit transition fixed it.
5. Foundry rejects required tool choice combined with provider-native response
   format. Initial clarification and resumed required-tool execution remain
   separate.
6. Generated IDs are not model responsibilities. The model receives local
   slots/handles; deterministic code derives portable IDs and citations.
7. Logical agent-attempt accounting undercounted HTTP calls. LABS-04 now records
   both; LABS-05 must preserve that distinction across every conversation turn.

Full incident history is in `internal/LABS04_TRIAGE.md` and the append-only
decision log. Read them; do not compress their failures into “prompt quality.”

## 5. LABS-05 product intent

Provisional name: **Adaptive Multi-Turn Runner**.

The smallest useful outcome is not another case generator. It is evidence that
reviewed LABS-04 cases can drive genuinely adaptive conversations against one
existing conversational/tool agent:

```text
reviewed grounded case
  -> deterministic episode controller
  -> simulated user sees the latest target response/tool event
  -> simulated user chooses the next turn under the frozen turn policy
  -> one existing target agent executes
  -> transcript + tool events + budgets + gaps + trajectory identity
  -> deterministic validation and human inspection
```

LABS-05 should initially use one explicit target-agent protocol and one target
agent. It should not claim universal coding-agent, browser-agent, voice-agent,
or multi-agent support.

### Recommended minimum checkpoint shape

- Input: owner-reviewed subset of the five LABS-04 cases, exact Case Factory
  manifest/hash, one target-agent runner config, one simulator-provider config,
  hard episode/turn/call/token/USD/time limits, and a declared reset policy.
- Execution: at least three truly multi-turn episodes. Every generated user
  turn must consume the latest target response and any normalized tool event;
  static prewritten dialogue does not pass.
- Output: immutable episode attempts, normalized multi-turn transcript,
  target/tool events, termination reason, provider/model/prompt lineage,
  token/HTTP/cost ledger, fidelity label, gap records, and trajectory
  fingerprint/duplicate clusters.
- Passage: at least three valid, inspectable, nonduplicate trajectories; no
  missing/invalid/refused episode becomes a pass; one human inspection confirms
  that later user turns actually react to the target behavior.
- Scope exclusions: model judge, persistent learning memory, global memory,
  broad eval suite, UI, real data, baseline/candidate comparison, hosted runner,
  generic SDK, and automatic prompt optimization.

This is a recommendation, not a frozen implementation contract. The next
session must discuss and freeze the material choices below before tests/code.

## 6. Material decisions still required for LABS-05

1. **LABS-04 owner review:** approve/reject cases under the frozen rubric. No
   agent may approve on Akarsh's behalf.
2. **Target agent and protocol:** name the exact existing agent and choose one
   invocation surface (recommended: local subprocess JSONL unless the real
   target already has a more bounded supported interface).
3. **Episode size:** reviewed case count, minimum/maximum turns, and termination
   rules. Recommended first experiment: three cases, 4–8 user/assistant turns.
4. **Budget:** exact per-episode and whole-experiment call/token/USD/time caps.
   Do not inherit LABS-04's USD 25 automatically.
5. **World/tool boundary:** whether target tools are real safe local tools,
   deterministic stubs, or read-only projections; uncontrolled side effects
   are refused.
6. **Harness:** reuse `create_agent` for a single simulator by default. Run a
   disposable DeepAgents conformance check only if the accepted design truly
   requires runtime delegation, specialist subagents, or long-lived shared
   state. Do not adopt a framework for architectural aesthetics.
7. **Minimal evaluation:** exact observable proof that turns are adaptive,
   policy-consistent, grounded, nonduplicate, and stopped correctly. Avoid a
   judge/eval treadmill before transcripts exist.

## 7. Backlog carried forward

### Required during or immediately after LABS-05

- enforce material relevance of model-authored clarification questions;
- freeze the target runner/reset/isolation contract and side-effect refusals;
- define transcript, turn, tool-event, termination, trajectory, and episode
  artifact schemas;
- preserve logical versus HTTP-level provider accounting across long loops;
- define exact prompt/request caching and prohibit stale target-response reuse;
- measure trajectory duplicates across the same batch and repeated batches;
- test simulator policy compliance and whether later turns react to target
  responses rather than replaying a script;
- run the DeepEval conformance experiment only after the reference loop has
  observable transcripts;
- make the owner-review input/output reproducible rather than relying on chat.

### Mandatory evaluation backlog after the first working transcript

- representative retrieval-quality set;
- human case-usefulness calibration and any later model-judge calibration;
- frozen-input prompt/model comparison;
- clarification relevance and injection resistance;
- case and trajectory duplication/coverage measurement;
- multi-turn rubric quality and context-specific rubric proposal quality;
- seeded target mutations and negative/ambiguous/missing-evidence anchors;
- budget/caching correctness across provider errors and long conversations;
- compare DeepEval, direct `create_agent`, and DeepAgents only on the same
  conformance artifacts if all remain credible candidates.

### Defined primitive, implementation deferred

Evaluated learning memory has six operations: `propose`, human/evidence-gated
`promote`, retrieve from a pinned snapshot, `supersede`, `revoke/delete`, and
record attribution from memory item to affected run. Episode memory is allowed
inside LABS-05; persistent learning memory is implemented only when a reviewed
result has a real next-run consumer. Mem0, global organization memory,
cross-customer memory, autonomous reflection promotion, and model fine-tuning
remain parked.

### Explicitly parked

- real/customer/local-sensitive traces and general redaction productization;
- baseline/candidate diff, F0/F1 release comparison, and verdict language;
- coding-agent, browser, voice, long-running, and multi-agent universality;
- hosted ingestion/execution, UI/dashboard, accounts, SaaS, OTel, and generic
  adapter/provider SDKs;
- judge ensembles, automatic rubric promotion, autonomous prompt training,
  global novelty memory, and cross-customer learning.

## 8. Start-of-session protocol

1. Read `AGENTS.md`, the charter, current plan, Product, Architecture,
   Contracts, Working Memory, Provenance, full Decision Log, Engineering, the
   closed Slice Packet, readable case review, this handoff, Agent Architecture,
   and LABS-04 triage.
2. Inspect Git and verify the LABS-04 closing commits and untracked user files.
3. Perform or obtain the owner usefulness ruling; append it to the decision log
   and update charter/plan in the same change.
4. Discuss only the seven material LABS-05 choices above.
5. Freeze a new LABS-05 `internal/SLICE_PACKET.md` with exact I/O, authority,
   privacy, refusal/partial behavior, budgets, provenance, acceptance, and
   change budget.
6. Use serial independent test author → implementation author roles with Codex
   orchestrating. Do not let production redefine acceptance.
7. Do not start judges, memory, UI, real-data work, or a broad eval program
   before the first valid adaptive transcript exists.

## 9. Copyable next-session prompt

```text
Continue Triana from local main after the LABS-04 Grounded Case Factory close.
Read AGENTS.md, triana-labs/CHARTER.md, the current plan named by the charter,
docs/PRODUCT.md, docs/ARCHITECTURE.md, docs/CONTRACTS.md,
internal/WORKING_MEMORY.md, docs/PROVENANCE.md, the full
internal/DECISION_LOG.md, docs/ENGINEERING.md, internal/SLICE_PACKET.md,
internal/LABS04_CASE_REVIEW_2026-08-02.md,
internal/LABS05_HANDOFF_2026-08-02.md, internal/AGENT_ARCHITECTURE.md, and
internal/LABS04_TRIAGE.md.

Ground truth: LABS-04 deterministic machinery is complete. The sole scale-out
run produced 5 requested / 5 valid / 5 distinct grounded synthetic cases, no
gaps, repairs, or duplicates, using 6 logical invocations and 14 provider HTTP
exchanges with USD 12 conservative reservation under USD 25. The final suite
has 408 passing tests and the five canonical Observer hashes are unchanged.
The public triana cases generate command now selects the restricted GLM-5.2
runtime only through an explicit strict restricted config; legacy config
dispatch remains explicit. triana cases resume verifies exact config bytes,
answers, immutable pause evidence, and private cache with no fallback. Do not
rediscover or rerun LABS-04 provider experiments.
The portable owner-review bundle is durably copied to
~/Documents/Triana-LABS04-scaleout-close-2026-08-02/ with all hashes verified.

First, obtain and record my LABS04_USEFULNESS_V1 ruling; do not approve it for
me. Then discuss and freeze the smallest LABS-05 Adaptive Multi-Turn Runner
checkpoint. It must run an owner-reviewed subset of LABS-04 cases as genuinely
adaptive multi-turn conversations against one explicitly named existing
conversational/tool agent through one bounded protocol. Preserve deterministic
identity, budgets, trajectory dedupe, provenance, HTTP accounting, typed gaps,
fail-fast/no-fallback behavior, and synthetic-only privacy. Use episode-only
memory; persistent/global memory, judges, UI, real-data support,
baseline/candidate diff, generic SDKs, and broad eval expansion remain deferred.

Resolve only: target agent/protocol, reviewed case count, 4–8-turn episode
shape and termination, tool/world/reset boundary, exact run budget, whether
current create_agent is sufficient or a disposable DeepAgents conformance POC
is earned, and the minimum transcript-based acceptance proof. Start with
product/technical discussion and an ASCII architecture, not implementation.
After I accept the checkpoint, replace the closed slice packet and execute
serial independent test author → implementation author roles with Codex
orchestrating. Prioritize the first valid inspectable adaptive transcript;
do not enter an eval treadmill.
```
