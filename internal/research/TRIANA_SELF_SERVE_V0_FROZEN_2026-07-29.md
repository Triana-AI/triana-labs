# Triana Self-Serve V0 — Frozen Product Boundary and Open Decisions

**Status:** Product boundary frozen by Akarsh on 2026-07-29.  
**Scope:** This document freezes the first usable self-serve product and
separates it from implementation and policy questions that remain open.

## The frozen product

### One-sentence definition

Triana connects to an AI agent's existing production traces and creates and
continuously updates a reviewable, release-ready production replay dataset that
captures the production behavior the next release should face.

### First usable product: instant acquisition

The first thing a user can use is:

> Connect production traces and generate a reviewable, release-ready production
> replay dataset.

This is the first self-serve offering. It must deliver value before the customer
installs a GitHub Action, changes its agent code, or replaces its existing
observability and evaluation stack.

The product category is **Production Replay Dataset**. The bounded, versioned
artifact shown to a user for review and a specific release is a **Release Replay
Set**.

### Customer promise

Triana turns production history into a small, explainable set of cases that an
engineer can inspect, approve, and run against the next agent version.

For every proposed case, Triana must answer:

1. What happened in production?
2. Why was this case selected?
3. What evidence supports the selection?
4. What behavior or outcome may be worth protecting?
5. Can the case actually be replayed?
6. What state, fixtures, tools, or credentials would replay require?
7. Has a human approved it as release protection?

### Frozen first-product workflow

```text
Connect existing trace provider or upload traces
        ↓
Normalize production sessions without replacing the source system
        ↓
Find candidate production behaviors and evidence
        ↓
Generate a bounded Release Replay Set
        ↓
Engineer reviews, edits, approves, defers, or rejects cases
        ↓
Approved cases become versioned release protection
        ↓
New production evidence proposes additions, replacements, or retirement
```

Triana proposes dataset changes. The customer remains responsible for deciding
what correct or important behavior means.

## What the production replay dataset contains

The dataset may include:

- representative successful production behavior worth preserving;
- confirmed failures that must not recur;
- cases with explicit or behavioral evidence of user frustration;
- new or rapidly growing user workflows;
- rare but consequential cases;
- low-confidence or ambiguous outcomes needing review;
- cases missing from the customer's existing eval set;
- cases likely to exercise behavior affected by a model, prompt, tool,
  retrieval, policy, or harness change.

The dataset is not a random trace sample and not a dump of every production
session. It is a bounded, evidence-backed selection for release use.

### Minimum case record

Each proposed case should retain:

- stable case ID and source-trace reference;
- redacted input and relevant conversation or trajectory;
- user/workflow population;
- selection reason;
- supporting evidence;
- candidate protected outcome or behavior;
- replayability status;
- required starting state, fixtures, and tool policy;
- existing-eval coverage status;
- human review and approval state;
- artifact, adapter, and source versions.

## Production issue discovery is inside the offering

Production issue discovery is not a separate first product. It is one reason a
production trace enters the replay dataset.

When Triana detects a recurring misclassification, unresolved request, tool
failure, costly loop, or returning known failure, it should show the issue and
its affected traces, then let the engineer promote the confirmed behavior into
future release protection.

```text
production issue
→ evidence and affected cases
→ human confirmation or correction
→ approved replay case
→ future release protection
```

The durable value is not only finding the issue. It is preventing the
organization from forgetting the issue at the next release.

## User-frustration evidence

User frustration is a supported selection signal, not a self-sufficient truth
label or release metric.

Possible evidence includes:

- explicit negative feedback or support escalation;
- repeated rephrasing or retries;
- user correction or manual override;
- abandonment after an unsuccessful step;
- repeated refusal, loop, or unresolved outcome;
- a successful outcome reached only after excessive turns, latency, cost, or
  tool calls.

Triana must show the evidence, confidence, frequency, and affected traces. The
case should protect the underlying behavior or outcome, not attempt to preserve
an opaque "frustration score."

## How this connects to a release decision

The production replay dataset is the evidence input to the release product. It
is not, by itself, proof that a candidate release is safe.

Once cases are approved and executable, Triana can:

```text
freeze Release Replay Set
→ execute approved production version and candidate on comparable cases
→ apply the same frozen measurements
→ show improvements, regressions, unchanged behavior, uncertainty, and gaps
→ apply customer-owned Release Policy
→ support PASS, REVIEW, or BLOCK with evidence
```

The customer owns correctness standards, policy thresholds, exceptions, and
the final authority to ship. Triana owns case identity, evidence lineage,
versioning, comparison, and decision traceability.

## What is not part of the first instant product

The instant product does not need to:

- replace LangSmith, Langfuse, Raindrop, Braintrust, Datadog, or another trace
  provider;
- require a new instrumentation SDK when the existing provider exposes enough
  trace data;
- execute arbitrary customer agents in Triana's cloud;
- automatically know every domain rule;
- label every anomaly as a failure;
- generate an autonomous safe-to-ship verdict;
- build a generic eval framework, judge marketplace, or observability
  dashboard;
- install an MCP server;
- automatically modify the approved replay dataset during a release run.

## Evidence from the first three conversations

### Risa / Ashutosh

Risa already uses a golden dataset in CI/CD, updates it with new and
low-confidence cases, and uses shadow deployments. This strongly validates
release-evidence maintenance as real work, while proving that generic
trace-to-dataset-to-CI functionality is insufficient. Triana must show which
important production behavior the current release evidence still misses and
why the proposed cases would change a release review.

### Priyanshu

Priyanshu uses Raindrop traces, manual sanity checks, user reports, and coding
agents for one-off trace investigation. He values exact problems and affected
traces over aggregate scores and wants issues surfaced before users report them.
This validates the trace-first acquisition path and production-issue input into
the replay dataset. His current workaround is adequate at small scale, so
willingness to pay and continuous-system value remain unproven.

### Ollive

Ollive supplied an example where existing evals missed undocumented domain
rules until customer use exposed the failure. This supports turning expert
correction and incidents into persistent release protection, but it is partner
evidence rather than customer purchase validation.

## Frozen naming and positioning

### Product category

**Production Replay Dataset**

### User-visible artifact

**Release Replay Set**

### First-product sentence

> Connect your production traces. Triana builds the production replay set your
> next agent release should face.

### Full-product sentence

> Triana converts production behavior into an evidence-backed Release Replay
> Set, compares the approved production agent and candidate on that set, and
> keeps confirmed cases as protection for every future release.

## Open decisions that must be discussed

The following are not frozen by this document.

### 1. Minimum trace contract

- Which trace providers are supported first?
- What minimum fields make a session admissible?
- How are multi-turn sessions, tool spans, user feedback, business outcomes,
  and missing fields normalized?
- What should the product do when a provider export lacks enough evidence?

### 2. Dataset construction policy

- How many cases should the first set contain?
- What mixture of representative success, confirmed failure, frustration,
  emerging demand, rare risk, and coverage gaps should be used?
- How are duplicate and near-duplicate cases handled?
- How does Triana prove that a selected set represents important behavior
  without pretending it covers all production use?

### 3. Updating and retirement

- What production changes trigger a proposal?
- When should an old case be replaced, retained permanently, or retired?
- How are new proposals compared with the already approved set?
- What changes require human approval?

### 4. Replayability

- What counts as exact replay, reconstructed replay, simulation, or
  observation-only evidence?
- How are starting state, tools, retrieval results, external APIs, and
  side effects controlled?
- What typed gap is shown when a production case cannot be reproduced?

### 5. Protected outcomes and evaluators

- Who defines what each case protects?
- When is a deterministic check sufficient?
- When is an LLM judge justified, and how is it calibrated?
- How are customer scorers and existing evals imported?
- What is allowed to remain review-only?

### 6. Baseline identity

- Is the approved baseline a stored case-level result, a deployed endpoint, a
  source revision, or a complete versioned agent manifest?
- When may stored baseline results be safely reused?
- Which model, prompt, tool, retrieval, harness, data, and environment changes
  invalidate baseline reuse?

### 7. Minimal GitHub Action

The current candidate is a workflow-only Action that:

- fetches a frozen approved Release Replay Set;
- invokes one customer-declared case-runner command inside the customer's CI;
- keeps customer code and credentials in the runner;
- captures normalized candidate results;
- compares them with a compatible approved baseline;
- publishes a GitHub Step Summary, machine-readable artifact, and deep-report
  link;
- begins in advisory mode and later supports enforced PASS, REVIEW, or BLOCK.

Still to decide:

- exact runner input/output contract;
- stored baseline versus paired baseline/candidate execution;
- behavior of REVIEW in branch protection;
- advisory-to-enforcement activation criteria;
- artifact retention, reruns, cancellation, fork PRs, and missing secrets.

### 8. Data custody and security

- Which raw traces, redacted excerpts, derived cases, and results enter Triana?
- Can dataset construction run inside customer infrastructure?
- How are deletion, retention, regional storage, and sensitive fields handled?
- What evidence can safely appear in GitHub?

### 9. First ICP and activation threshold

- Is the first user a beta-stage team without evals or a mature team already
  maintaining a golden set?
- What trace volume and release frequency make continuous updating valuable?
- What is the smallest commitment that counts as product validation?

### 10. Packaging and pricing

- Is the first replay-set generation free?
- Is pricing based on trace volume, approved cases, releases, seats, or runner
  usage?
- What event marks conversion from acquisition product to paid release product?

## Immediate validation experiment

For one real customer:

1. Ingest a bounded historical production trace window.
2. Hide two or three known post-release issues from Triana.
3. Generate a proposed Release Replay Set without those labels.
4. Ask the engineer to review every proposed case.
5. Measure whether Triana surfaces a consequential missed behavior, whether the
   engineer approves it, and whether it would have changed an actual release
   review.
6. Attempt to make the approved cases executable against the next candidate.

The experiment succeeds when the customer approves at least one previously
missing case, commits it to the next release, and supplies the access or runner
needed to execute it. Interest, positive language, or intent clustering alone
does not count.

