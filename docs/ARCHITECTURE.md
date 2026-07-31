# Architecture and trust contracts

This document fixes the V1 authority and system boundaries without choosing a
cloud architecture prematurely. The accepted implementation split is Python
for the deterministic core, CLI, backend APIs, integrations, and future
AI-assisted packages, with TypeScript for the web UI and versioned JSON Schema
as the enforced language boundary. `docs/CONTRACTS.md` owns the exact Slice 0A
wire representation.

## Active Labs execution boundary

For active Triana Labs work, `triana-labs/CHARTER.md` and the current Labs plan
supersede the suspended V1 flow below. The shipped local synthetic pipeline is:

```text
source-specific synthetic JSONL
  -> standalone reference transform
  -> PreviewTrace JSONL
  -> Trace Observer
  -> verified Observer manifest + normalized traces
  -> structural Corpus Intelligence
  -> deterministic clusters + explicit semantic gaps
```

`triana traces observe` owns raw PreviewTrace accounting and five deterministic
corpus artifacts. `triana corpus derive` accepts only that Observer manifest,
verifies all sibling hashes/counts/traces, and publishes a separate atomic
intelligence bundle. `intelligence/input.py` owns input integrity,
`intelligence/derive.py` owns fingerprints, membership, IDs, support and gap
artifacts, `intelligence/publication.py` owns atomic filesystem publication,
and `cli.py` owns invocation, safe terminal events, and exits.

The current structural fingerprint contains counts, ordered safe tool names,
terminal presence/state, unmatched calls, and mechanical case eligibility. It
does not consume conversation text, opaque tool values, error prose, or source
trace IDs. Personas, intents, turn policies, language, and distress remain
typed `NOT_DERIVED`/`NOT_EVALUATED` states. No provider, LLM, real-data path,
redaction/egress path, Case Generator, or UI exists in this checkpoint.

## Authority map

```text
ACQUISITION / CASE CREATION

CUSTOMER PRODUCTION TRACES
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

RECURRING RELEASE REVIEW

CUSTOMER-DECLARED RELEASE CHANGE
baseline + candidate + declared delta + observable fingerprints
        │
        ▼
HUMAN-SELECTED RELEASE OBLIGATION
one approved Protected Case + required evidence
        │
        ▼
CUSTOMER AGENT REPLAY ───── CUSTOMER-OWNED EVALUATORS
customer code, credentials, environment, and usually an LLM
        │
        ├──────────────┐
        ▼              ▼
TRIANA ASSERTIONS   CUSTOMER CHECK COMMAND
deterministic       may include an LLM judge
        └──────┬───────┘
               ▼
DETERMINISTIC EVIDENCE NORMALIZATION + COMPARISON
identity, trial membership, denominators, rates, gaps, comparability
               │
               ▼
VERSIONED RELEASE POLICY
               │
               ▼
ADVISORY PASS / REVIEW / BLOCK
               │
               ▼
APPEND IMMUTABLE RELEASE EVIDENCE RECORD
evidence + policy version + recommendation
               │
               ▼
RELEASE REVIEW
record + gaps + recommendation + decision state
               │
               ▼
HUMAN RELEASE DECISION
approve / hold / approve with exception
               │
               ▼
APPEND IMMUTABLE DECISION ATTESTATION
```

An LLM may propose meaning. It cannot create truth, approve a case, alter trial
membership or denominators, decide comparability, or write a release outcome
unsupported by the record.

The recommendation and the Release Decision are different authorities.
Deterministic policy renders the recommendation. A human makes the decision.
V1 may link an existing GitHub review, merge, hold, or exception reference; it
does not infer approval from `PASS` or infer a hold from `BLOCK`. The link is a
separate append-only Decision Attestation, never a mutation of the Release
Evidence Record.

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
  ├─ append immutable record to chain
  ├─ render the versioned Release Policy
  ├─ append the immutable Release Evidence Record
  ├─ post the Release Review summary
  ├─ serve the permanent Release Review page
  └─ append a Decision Attestation when a human decision is available
```

The hosted control plane receives neither repository access nor customer
credentials. It must not claim that uploaded summaries prove observations
outside their declared scope.

## Conceptual objects

These are contracts to implement, not copied schemas.

### Release Change

The Release Change is a nested, versioned object within the Release Evidence
Record, not a separately deployed service. It preserves:

- approved baseline reference;
- candidate reference;
- customer-declared component delta;
- observable composite baseline and candidate fingerprints across code,
  prompt, model, provider, tools, retrieval/configuration, evaluator, fixture,
  and execution contract when available;
- unresolved or unobservable differences;
- the scope of any causal claim.

V1 accepts a customer declaration and verifies available identity evidence. It
does not infer a complete dependency graph or automatically decide which
obligations apply.

### Release Obligation

A Release Obligation is the human-approved semantic requirement carried by a
Protected Case in V1. It includes:

- the behavior that must be preserved;
- its source, such as a confirmed incident or customer policy;
- severity, owner, and approver;
- customer-declared applicability conditions;
- required evidence;
- the bounded Protected Case used to execute the requirement.

The obligation is not created by an LLM or inferred from a score. In V1, it is
not a standalone organization-wide obligation graph.

### Trace contract

Minimum information:

- trace ID and source;
- conversation, thread, and turn identity;
- ordered user, assistant, tool, and system-visible events needed to reconstruct
  the bounded conversational episode;
- agent/release identity when available;
- ordered model and tool observations;
- tool name, arguments, result, status, and error;
- final response, escalation/handoff outcome, and terminal state;
- timestamps, cost, and latency when available;
- parent/child relationships;
- metadata binding a replay to case, trial, side, and code ref.

An adapter converts a provider export to this normalized contract. Parsing
remains provider-specific; product logic consumes only the normalized form.
V1 does not define a generic contract for offline document-processing or
long-running autonomous jobs.

### Protected case

Stable identity over:

- Release Obligation statement, source, severity, owner, applicability, and
  required evidence;
- source evidence;
- conversation prefix or bounded replay request and fixture contract;
- expected, prohibited, and allowed behavior;
- required escalation or handoff where applicable;
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

The record binds the declared Release Change, observable composite identities,
unresolved identity differences, Release Obligation, required evidence,
Protected Case and evaluator versions, policy version, per-trial evidence,
comparison, gaps, recommendation, PR reference, and chain hashes. It is
immutable. Corrections append a superseding record. Human decisions are linked
through a separate Decision Attestation.

### Release Policy

A versioned, customer-approved mapping from evidence states to an advisory
Release Recommendation. It consumes comparison and gap states; it does not
produce evaluation evidence or execute a deployment.

### Release Recommendation

The deterministic output of the Release Policy: `PASS`, `REVIEW`, or `BLOCK`.
It is advisory in V1 and cannot be represented as the human Release Decision.

### Release Review

The decision-facing projection over one Release Evidence Record and zero or
more Decision Attestations. The PR comment and permanent page must show release
change and unresolved identity differences, applicable obligation, required
and received evidence, named risks, comparability, gaps, the policy rule that
fired, the recommendation, and the linked human decision or its absence.

### Decision Attestation

An immutable, append-only object binding a Release Evidence Record hash to the
customer-controlled approval, hold, merge, or exception reference and optional
rationale. V1 reuses the customer's existing GitHub/release workflow rather
than creating a separate approval engine. `DECISION PENDING` means no
attestation exists.

## Lifecycle boundary

V1 ends after a human decision is linked to a Release Review:

```text
declared Release Change + approved Release Obligation
        ↓
required and received eval evidence + production replay
        ↓
normalized evidence + comparison + typed gaps
        ↓
Release Policy recommendation
        ↓
Release Evidence Record
        ↓
Release Review
        ↓
human Release Decision
        ↓
Decision Attestation
        ╳
deployment / canary / rollout / rollback / post-release validation
```

The lower lifecycle is future Release Control territory. Triana may later
consume rollout and post-release outcomes as evidence, but V1 neither owns
traffic mechanics nor claims that evaluation-set maintenance is the primary
product.

The future extension preserves authority separation:

```text
immutable pre-release record
        ↓
human decision attestation
        ↓
append-only rollout/outcome observation
        ↓
human-reviewed proposal to revise future obligation or evidence requirements
```

A production outcome never rewrites the evidence known at release time, and an
automated observation never silently changes a human-approved obligation.

## Failure and refusal behavior

- Missing baseline → `FIRST_OBSERVATION`.
- Undeclared or unresolved identity difference → explicit limitation; never a
  clean model-only or prompt-only causal claim.
- No human-selected obligation → no Release Review recommendation.
- Required evidence absent → typed evidence gap and `REVIEW` unless a stricter
  customer policy applies.
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
9. comparison engine and Release Policy renderer;
10. immutable record, Decision Attestation, and verifier;
11. GitHub Action wrapper;
12. Release Review renderer and Decision Attestation linker.

Do not build all twelve before testing the vertical slice. Phase 0 defines
schemas and a hand-built round trip. The next slice runs one case on one
reference agent and produces one verifiable record.

## Projection boundary

The deterministic core is the only owner of identity, hashing, comparison,
denominators, gaps, policy evaluation, recommendation, and record chaining.
Every product surface consumes its versioned output:

```text
versioned contracts
        ↓
deterministic core
        ↓
Release Evidence Record + Decision Attestation
        ├─ CLI output and verifier
        ├─ hosted API
        ├─ GitHub Release Review comment
        └─ permanent Release Review page
```

The UI and PR renderer must not reproduce core calculations. A projection may
format, filter, link, and progressively disclose evidence, but the values and
reasons it displays come from the same verified record.

## First vertical slices

1. **Contract kernel:** strict schemas, canonical serialization, stable
   identity, hashing, golden fixtures, and record round-trip verification.
2. **Comparison and Release Policy:** honest A/A, planted A/B, typed gaps,
   comparability, deterministic recommendations, record chaining, and tamper
   rejection.
3. **Release Review projection:** one usable permanent page over the same
   fixture records, showing identity, named risks, evidence, gaps, policy
   reasoning, recommendation, verification state, and `DECISION PENDING` or a
   linked Decision Attestation.

Real trace adapters and paired customer execution replace fixture boundaries
after this kernel is visible. They do not require a second evidence model.
