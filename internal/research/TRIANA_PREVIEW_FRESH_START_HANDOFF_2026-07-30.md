# Triana Preview fresh-start handoff

Date: 2026-07-30  
Status: research handoff for a proposed successor experiment; not canonical
product authority

## Why this packet exists

The preceding research session became too long to carry safely in chat memory.
This document gives a new session an exact starting point for the proposed
open-source Triana Labs experiments without erasing what the Braintrust dogfood
falsified or silently changing the frozen V1.

Read this packet in order:

1. [`BRAINTRUST_HRAI_DOGFOOD_COLD_START_2026-07-30.md`](BRAINTRUST_HRAI_DOGFOOD_COLD_START_2026-07-30.md)
   — what was actually run in Braintrust.
2. [`BRAINTRUST_FALSIFICATION_AND_DOUBT_DRIVEN_DECISION_2026-07-30.md`](BRAINTRUST_FALSIFICATION_AND_DOUBT_DRIVEN_DECISION_2026-07-30.md)
   — what the experiment killed, what it did not kill, and the adversarial
   decision.
3. [`TRIANA_LABS_PREVIEW_GUARD_LEARN_CONCEPT_2026-07-30.md`](TRIANA_LABS_PREVIEW_GUARD_LEARN_CONCEPT_2026-07-30.md)
   — the proposed Preview, Guard, and Learn lineup.
4. This handoff — repository constraints, reusable evidence, and the smallest
   next implementation decision.

Then read the canonical authorities before changing product or code:

1. [`../../docs/PRODUCT.md`](../../docs/PRODUCT.md)
2. [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
3. [`../../docs/CONTRACTS.md`](../../docs/CONTRACTS.md)
4. [`../WORKING_MEMORY.md`](../WORKING_MEMORY.md)
5. [`../../docs/PROVENANCE.md`](../../docs/PROVENANCE.md)
6. [`../DECISION_LOG.md`](../DECISION_LOG.md)

## Plain-English conclusion from the session

Braintrust proved that Triana should not compete by running ordinary evals,
comparing baseline and candidate, storing release metadata, or wrapping those
results in a generic PASS/REVIEW/BLOCK report. Braintrust already owns most of
that work, and the missing policy checks were small enough to implement with
ordinary CI.

HRAI also proved that “simulate realistic users, run baseline and candidate,
and compare behavior” is not a new idea for us. We already built a substantial
domain-specific version.

The proposed response is not to claim a newly discovered moat. It is to ship a
small open-source learning artifact:

```text
Preview: use historical situations to compare a proposed agent with its baseline
Guard: observe a small controlled rollout and recommend continue, hold, or rollback
Learn: compare pre-release expectations with observed outcomes and improve the next test
```

The purpose is to create something installable, produce credible public
artifacts, and accelerate real feedback. The first release is allowed to be
shallow. It must be honest about where it overlaps existing tools.

## The unresolved canonical conflict

The frozen V1 currently says:

- Triana is closed-source.
- The V1 unit is one bounded production-derived conversational incident.
- Open-ended multi-turn user simulation and managed world reconstruction are
  outside V1.
- V1 stops at a human Release Decision.
- Canary, rollout, rollback, post-release validation, and outcome calibration
  are future Release Control work.

Preview–Guard–Learn proposes:

- an open-source distribution wedge;
- historical-traffic replay and optional simulation;
- controlled-rollout observation;
- post-release prediction-versus-outcome learning.

These cannot silently coexist as one frozen V1. Before implementation, the
owner must explicitly choose one of two interpretations:

1. **Separate experimental project:** Triana Labs is an open-source research
   and acquisition surface. It does not replace or redefine the frozen
   closed-source V1.
2. **Successor product decision:** Preview–Guard–Learn supersedes part or all
   of the frozen V1. This requires an append-only decision entry and matching
   canonical-document changes before implementation.

Until that choice is recorded, the research packet is descriptive and the
proposed lineup is non-canonical.

## Evidence already available

### Braintrust dogfood

Primary directory:
[`braintrust_hrai_dogfood_2026-07-30/`](braintrust_hrai_dogfood_2026-07-30/)

The live result:
[`braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md`](braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md)

Important artifacts:

- baseline experiment:
  [`artifacts/remote/v2_baseline.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/v2_baseline.json)
- A/A control:
  [`artifacts/remote/v2_aa_control.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/v2_aa_control.json)
- candidate:
  [`artifacts/remote/v2_candidate.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/v2_candidate.json)
- missing-required-scorer case:
  [`artifacts/remote/gate_missing_required.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/gate_missing_required.json)
- dataset-drift case:
  [`artifacts/remote/gate_dataset_drift.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/gate_dataset_drift.json)
- generic cross-stack record:
  [`artifacts/remote/cross_stack_release_record.json`](braintrust_hrai_dogfood_2026-07-30/artifacts/remote/cross_stack_release_record.json)

The tested generic release layer was 282 executable/configuration lines:

- `remote_ci_gate.py`: 130 lines;
- `build_release_record.py`: 97 lines;
- `release_review_input.json`: 55 lines.

A separate logging adapter stored the result back in Braintrust. The current
file is 89 physical lines; the earlier live note recorded 73 lines before that
file's present state. The 282-line generic subtotal is unchanged. These counts
are evidence against treating simple aggregation and policy arithmetic as the
company.

### HRAI historical-traffic experiment

Source repository:
`/Users/akarshgajbhiye/Documents/hr_ai`

Observed commit:
`728f6c5058efe40a16e2aecc9b528b3353f4df4f`

Experiment directory:
`/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0`

Start with:

- `EXPERIMENT_PLAN.md`
- `CHANGE_HYPOTHESIS.md`
- `DIFF_REPORT.md`
- `runner/`
- `scenarios_200.jsonl`
- the `RUN_MANIFEST.json` file inside each selected output directory.

The ten Python runner files contain 3,593 lines. They cover scenario
generation, user simulation, candidate-world seeding, HRAI execution,
normalization, cost accounting, and preflight checks. That number is a warning:
the existing implementation is evidence and a source-mining candidate, not
proof of a general reusable architecture.

Canonical HRAI result:

- baseline: Qwen3-235B;
- candidate: Qwen3-32B;
- 200 common case IDs;
- candidate was substantially cheaper;
- candidate evaluated more candidates but committed fewer decisions;
- independent baseline runs showed meaningful A/A noise;
- environment and simulator fidelity remained explicit limitations.

### Kairos-AI

Permitted repository:
`/Users/akarshgajbhiye/kairos-ai`

Observed commit:
`4167194431570a91c23c72c50b5997f7af61d251`

Relevant concept:
`docs/kairos-failure-memory-thesis.md`

Kairos-AI contains the earlier shape:

```text
goal → trace → attribution → failure memory → regression eval
```

It is relevant to Learn, incident-derived cases, and release memory. Do not
copy anything until the exact source file and commit are inspected and the
reuse is recorded in [`../../docs/PROVENANCE.md`](../../docs/PROVENANCE.md).

## What the first open-source artifact should be

The smallest coherent artifact is **Preview**, not all three systems.

Suggested first command shape:

```sh
triana preview \
  --traces production.jsonl \
  --baseline "python agent.py --model old" \
  --candidate "python agent.py --model new" \
  --trials 3 \
  --output report.html
```

The exact interface is not accepted. It expresses the intended outcome:

1. ingest existing historical situations;
2. execute the approved baseline and candidate under a declared replay mode;
3. preserve paired case and trial identities;
4. show behavioral, tool, cost, latency, and task-result movement;
5. show execution errors, missing observations, and non-comparability
   separately from behavioral failures;
6. produce a portable human-readable report and machine-readable artifact.

### Fidelity must be explicit

Preview should not use the word “simulation” as though every execution has the
same evidentiary strength.

| Mode | Meaning | Initial claim |
|---|---|---|
| Frozen replay | Historical user turns and recorded tool results are reused | The candidate behaved differently on these recorded situations |
| Safe live replay | Candidate runs against read-only, sandboxed, or stubbed tools | The candidate behaved differently in this declared safe environment |
| Generative simulation | A simulated user and environment react dynamically | The candidate may behave this way under the declared model of production |

Missing environment fidelity is evidence, not a hidden implementation detail.

## Suggested implementation sequence for a fresh session

### Step 0: decide repository and product authority

Before code:

- decide whether Triana Labs is a separate experimental open-source surface or
  a successor to frozen V1;
- decide whether it lives in this repository or a new repository;
- record the accepted choice in the append-only decision log;
- update canonical documents only if the decision changes them.

This is the only blocking owner decision.

### Step 1: provenance inventory, not a port

HRAI is evidence and a design reference, but it is **not currently a permitted
source-mining repository under `AGENTS.md`**. Before any HRAI code is copied,
Akarsh must explicitly authorize that repository as a source and the clean-room
and provenance checks below must pass.

For each authorized HRAI file and each potentially reusable Kairos/Kairos-AI
file:

1. record exact path and commit;
2. inspect authorship and license;
3. confirm it does not contain an Agentagon-derived port;
4. classify the capability as copy, adapt, or clean reimplementation;
5. append the destination and method to the provenance ledger.

Do not begin by moving all 3,593 HRAI runner lines. Until authorization is
recorded, do not move any of them.

### Step 2: freeze one Preview acceptance example

Use synthetic HRAI data and no production deployment. The acceptance example
should contain:

- an explicit baseline;
- a candidate;
- an A/A control;
- at least one paired behavior regression;
- at least one cost or latency improvement;
- an execution gap;
- a non-comparable example;
- a fidelity label;
- a machine-readable result;
- a readable static report.

The report must explain what is known, what is predicted, and what cannot be
claimed.

### Step 3: implement only frozen replay

Initial adapters should be deliberately narrow:

- one JSONL trace shape or an explicitly mapped existing normalized trace;
- one command/endpoint execution contract;
- one scorer/result adapter;
- local-only output.

Do not start with Braintrust, LangSmith, OTel, and every agent framework at
once. Add the second adapter only after an external user attempts the first.

### Step 4: publish the artifact as a learning probe

The first public proof should include:

- repository and install command;
- HRAI example configuration;
- exact reproducible command;
- machine-readable output;
- static report;
- comparison with Braintrust/AgentClash/Maxim rather than an unsupported
  uniqueness claim;
- a request for users to try one real release;
- a documented path for submitting only non-sensitive feedback.

### Step 5: earn Guard and Learn

Build Guard only after someone asks to use Preview during a controlled rollout.
Initially integrate with an existing flag/deployment provider; do not own
traffic.

Build Learn only after at least one Preview artifact and one observed rollout
outcome can be joined by a shared release identity. Do not build a generic
outcome warehouse first.

## Learning scorecard

Measure the public experiment by behavior, not attention:

| Signal | Why it matters |
|---|---|
| Successful external installation | Tests whether the artifact is usable |
| Time to first report | Exposes integration burden |
| Customer-specific adapter lines | Tests whether simulation is a product or services |
| Existing traces accepted without dataset recreation | Tests the proposed distribution advantage |
| Material difference missed by existing evals | Tests incremental value |
| Repeat use on another release | Tests recurrence |
| Request for rollout monitoring | Earns Guard |
| Outcome attached to a prior Preview | Earns Learn |
| Willingness to pay or sponsor development | Tests commercial value |

Stars, impressions, and compliments are distribution signals, not product
validation.

## Hard stopping rules

Stop or reposition Preview if:

- two external integrations each require more than one engineering day of
  bespoke world simulation;
- users must recreate datasets, scorers, or behavior definitions already held
  in Braintrust or LangSmith;
- AgentClash, Maxim, or ordinary scripts reproduce the useful result with less
  effort;
- the report is only another eval dashboard;
- no external team completes a second release comparison;
- teams prefer a canary in every eligible use case;
- the tool cannot distinguish environment failure, missing evidence, and
  behavioral regression;
- the open-source surface creates no qualified conversation after an agreed
  distribution period.

Do not change the stopping rule after observing an unfavorable result without
recording why.

## Questions the next session must not answer from intuition

1. Can one trace format cover enough real agents to produce a report without
   bespoke integration?
2. Which replay fidelity level do teams actually want?
3. Will teams supply historical contexts even when execution stays local?
4. What outcome makes a Preview report decision-changing?
5. Is the buyer asking for replay, safer rollout, or incident memory?
6. Does a customer want Guard to recommend, enforce, or merely document?
7. Can Learn use existing Sentry/PostHog/flag-provider data by reference?
8. Is an open-source project the acquisition path for the closed-source V1, or
   has the product thesis actually changed?

## Fresh-session prompt

Use this prompt to resume:

> Read `AGENTS.md`, the six canonical authority documents, and the four-file
> Triana Preview research packet dated 2026-07-30. Treat Preview–Guard–Learn as
> a proposed experimental successor track, not frozen V1. First resolve whether
> Triana Labs is a separate open-source acquisition project or a successor
> product decision. Then inventory provenance-safe HRAI/Kairos reuse and freeze
> the smallest frozen-replay Preview acceptance slice. Do not implement Guard,
> Learn, a hosted service, or a universal simulator.
