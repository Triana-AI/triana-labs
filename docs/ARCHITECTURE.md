# Architecture and trust contracts

This document fixes the V1 boundaries without choosing a programming language
or cloud architecture prematurely.

## Authority map

```text
CUSTOMER TRACE DATA
        │
        ▼
DETERMINISTIC SURFACING
membership, signal values, ranking, deduplication
        │
        ▼
HUMAN INCIDENT SELECTION
        │
        ▼
OPTIONAL LLM DRAFTING
risk name, expected/prohibited behavior, candidate assertions
        │
        ▼
HUMAN APPROVAL + PROMOTION
semantic truth and policy authority
        │
        ▼
DETERMINISTIC QUALIFICATION
READY / NEEDS_FIXTURE / NOT_YET
        │
        ▼
CUSTOMER AGENT REPLAY
customer code, credentials, environment, and usually an LLM
        │
        ├──────────────┐
        ▼              ▼
TRIANA ASSERTIONS   CUSTOMER CHECK COMMAND
deterministic       may include an LLM judge
        └──────┬───────┘
               ▼
DETERMINISTIC COMPARISON + POLICY
trial membership, denominators, rates, gaps, comparability
               │
               ▼
ADVISORY RECOMMENDATION + IMMUTABLE RECORD
```

An LLM may propose meaning. It cannot create truth, approve a case, alter trial
membership or denominators, decide comparability, or write a release outcome
unsupported by the record.

## Execution boundary

```text
GitHub pull request
        │
        ▼
customer-hosted GitHub Actions runner
  ├─ checkout approved baseline ref
  ├─ checkout candidate SHA
  ├─ start isolated runtime for each
  ├─ run the same pinned protected case N times
  ├─ collect exact trace IDs
  ├─ run deterministic assertions
  ├─ invoke optional customer evaluator command
  └─ emit normalized evidence
        │
        ▼
Triana hosted control plane
  ├─ validate submitted identities and evidence
  ├─ render repository policy
  ├─ append immutable record to chain
  ├─ post PR summary
  └─ serve permanent evidence page
```

The hosted control plane receives neither repository access nor customer
credentials. It must not claim that uploaded summaries prove observations
outside their declared scope.

## Conceptual objects

These are contracts to implement, not copied schemas.

### Trace contract

Minimum information:

- trace ID and source;
- agent/release identity when available;
- ordered model and tool observations;
- tool name, arguments, result, status, and error;
- terminal output and terminal state;
- timestamps, cost, and latency when available;
- parent/child relationships;
- metadata binding a replay to case, trial, side, and code ref.

An adapter converts a provider export to this normalized contract. Parsing
remains provider-specific; product logic consumes only the normalized form.

### Protected case

Stable identity over:

- source evidence;
- replay request and fixture contract;
- expected, prohibited, and allowed behavior;
- executable checks and versions;
- approval;
- qualification state.

Changing semantic content creates a new case version.

### Trial result

One execution includes:

- case version;
- side (`baseline` or `candidate`);
- code ref and composite runtime fingerprint;
- trial index and randomization controls;
- trace identity;
- assertion results;
- customer evaluator results;
- execution and evaluation gaps.

### Comparison

Comparison is valid only when case version, fixture/configuration, reset policy,
and execution contract match. It preserves:

- pass count and evaluable count;
- end-to-end success count;
- typed gaps;
- absolute rates and baseline-to-candidate movement;
- evidence strength;
- approved threshold.

### Release Evidence Record

The record binds release identity, case and evaluator versions, policy version,
per-trial evidence, comparison, gaps, recommendation, approvals, and chain
hashes. It is immutable. Corrections append a superseding record.

## Failure and refusal behavior

- Missing baseline → `FIRST_OBSERVATION`.
- Mismatched execution contracts → `MOVED`, not regression.
- Missing tool-dispatch visibility → negative tool assertions unevaluable.
- Agent cannot run safely → `NOT_YET`.
- Required state can be created with a bounded fixture → `NEEDS_FIXTURE`.
- Evaluator errors or timeouts → evidence gap, not behavioral failure and not
  pass.
- Insufficient trials → REVIEW with the limitation shown.
- Hash or identity mismatch → reject the record append.

## Initial interfaces

The first implementation should make these seams explicit:

1. trace adapter;
2. candidate signal engine;
3. protected-case store and versioning;
4. qualification runner;
5. customer agent command contract;
6. deterministic assertion engine;
7. customer evaluator JSONL adapter;
8. paired baseline/candidate orchestrator;
9. comparison and policy renderer;
10. immutable record and verifier;
11. GitHub Action wrapper;
12. evidence page.

Do not build all twelve before testing the vertical slice. Phase 0 defines
schemas and a hand-built round trip. The next slice runs one case on one
reference agent and produces one verifiable record.
