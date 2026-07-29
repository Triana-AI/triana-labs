# Working memory

Updated: 2026-07-30

## Current objective

Prove that an eligible team can turn one important production incident into a
retained release check and receive decision-changing evidence on a real PR
without Triana-authored integration code.

Do not optimize the long-term platform before proving this loop.

## Frozen

- Narrow CI-runnable ICP.
- One exact incident, not representative production coverage.
- Human-approved protected case.
- Explicit approved baseline and GitHub candidate.
- Execution inside customer CI.
- Triana deterministic assertions plus one customer-owned JSONL evaluator
  command.
- Separate behavioral failures, evaluation gaps, and non-comparability.
- Advisory PASS/REVIEW/BLOCK.
- Immutable Release Evidence Record.
- One case free; $500/month design-partner pilot.
- Closed-source distribution.

## Active hypotheses

| ID | Hypothesis | Evidence required | Status |
|---|---|---|---|
| H1 | At least one-third of important incidents for eligible teams become `READY` without Triana engineering | Qualification attempts across first three eligible teams | Untested |
| H2 | A new engineer reaches the first real record in under one working day | Timed external M1 | Untested |
| H3 | The record changes a merge/release action or materially improves the release conversation | Before/after decision interview tied to a real PR | Untested |
| H4 | Teams retain protected cases across at least three releases | Longitudinal partner usage | Untested |
| H5 | Teams will pay $500/month for repeated records before mandatory enforcement exists | Direct pilot purchase | Untested |
| H6 | After advisory trust, at least one team asks for enforcement | Partner request backed by usage | Untested |
| H7 | The customer-command lane adds a unique release action rather than duplicating Braintrust/DeepEval/LangSmith | Side-by-side workflow on customer stack | Untested |

## Immediate build sequence

### Phase 0: contracts

Define four small, versioned contracts:

1. normalized trace;
2. protected case;
3. release evidence record;
4. record chain.

Proof: one hand-built reference trace becomes a case, produces a baseline and
candidate comparison, serializes a record, and verifies after round-trip.

### Phase 1: Connect → Surface → Promote

Mine only permitted Kairos/Kairos-AI code after provenance review. Build:

- one trace adapter;
- deterministic candidate signals and ranking;
- a six-to-nine-field protected-case proposal;
- human review and Promotion;
- qualification state.

Proof: one real incident becomes a promoted case in under 15 minutes.

### Phase 2: local `triana check`

Implement the paired execution contract:

- explicit baseline and candidate refs;
- isolated runtimes;
- same case and fixture fingerprint;
- repeated trials;
- deterministic assertions;
- optional customer JSONL evaluator;
- gap/comparability logic;
- record and verification.

Proof: the reference agent produces honest A/A and planted A/B rates.

### M0: public reproducibility

Publish the reference agent and every customer-visible artifact. Keep Triana
source private. A skeptic must reproduce the record using the shipped
container.

### M1: real partner

Run one retained case on one real PR with no bespoke Triana integration code.

### Alpha

Open only after M0 and one successful M1.

## Do not build yet

- full scan, clustering, and coverage maps;
- behavior-family inference;
- Triana-owned LLM judges;
- automatic ground truth;
- simulation platform or managed sandbox;
- provider-specific evaluator adapters;
- visual release policy;
- automatic blocking;
- rollout and rollback;
- compliance packaging;
- dashboards;
- SDK/re-instrumentation layer;
- open-source core.

## Customer evidence log

Add one row per real qualification or release attempt.

| Date | Customer/agent | Eligibility | Incident | Qualification | Time to record | Decision changed? | Retained? | Payment signal | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Change rule

- One request: record it.
- Repeated blocker among eligible teams: create a focused discovery test.
- Paying team cannot complete core loop: test ICP or contract.
- Record changes no release behavior: reconsider the wedge.
- Nice-to-have feedback: preserve scope.

Only an explicit decision may modify `docs/PRODUCT.md`.
