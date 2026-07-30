# Triana Self-Serve V1 — Final Ship Specification

Status: **FINAL SHIP BOUNDARY — 2026-07-29**

This specification supersedes the shipping scope in:

- `TRIANA_SELF_SERVE_V0_FROZEN_2026-07-29.md`
- `TRIANA_WEDGE_V1_SPINE_2026-07-29.md`

Those documents remain research and rationale. This document is the concise
product that Triana will build, dogfood, put in front of design partners, and
then release as a narrow self-serve alpha.

## 1. Product in one sentence

> Triana turns one approved production failure into a release check, reruns it
> against an approved baseline and a candidate in the customer's CI, and
> returns an advisory PASS, REVIEW, or BLOCK recommendation with permanent
> evidence.

Production replay is the check mechanism. The Release Evidence Record is the
durable artifact. The release recommendation is the decision-facing output.

## 2. Who V1 is for

V1 is deliberately not for every agent team.

The self-serve ICP has:

- a customer-facing or operationally consequential agent;
- an existing trace store or structured JSONL/OTel export;
- at least one production or staging failure worth preventing;
- an agent a new engineer can run from a repository checkout in CI;
- a bounded single-turn request path;
- a test environment in which repeated executions are safe;
- releases frequent enough that a recurring check matters.

Teams whose agents require production-only state, uncontrolled third-party
side effects, long multi-turn user simulation, or a large enterprise world are
not self-serve V1 customers. They may enter the incident library, but Triana
does not promise a runnable check.

## 3. The first-use loop

```text
Connect Langfuse or upload JSONL/OTel
        ↓
Enter one line: what is this agent supposed to do?
        ↓
Triana surfaces a short list of mechanically suspicious traces
        ↓
The user points at one known incident
        ↓
Triana proposes one exact protected case and deterministic assertions
        ↓
The user edits and Promotes it
        ↓
Qualification proves that the case can be replayed and measured
        ↓
The next PR receives an advisory release recommendation and evidence record
```

The first value moment is not trace discovery or case creation by itself. It is:

> “This approved production failure passed 10/10 on the approved baseline and
> only 6/10 on this PR; here are the failed executions and the exact evidence.”

## 4. What ships

### 4.1 Connect and candidate surface

- Read-only Langfuse connection.
- Generic JSONL/OTel upload.
- Local mode for privacy-sensitive teams.
- Deterministic candidate signals only: tool error, terminal error, repeated
  tool loop, redundant calls, aborted execution, unbacked action claim, cost or
  latency spike, and customer-flagged trace.
- A ranked, deduplicated proposal list.

V1 does not claim complete issue discovery, representative traffic coverage,
or protected behavior families. One promoted trace protects one exact case.

### 4.2 Protected case

A versioned case contains:

- risk name;
- source trace and source environment;
- replay input;
- what the agent should do;
- what is prohibited;
- allowed alternatives;
- policy or business context;
- one or more executable checks;
- approver and approval time;
- replayability state: `READY`, `NEEDS_FIXTURE`, or `NOT_YET`.

A case becomes `READY` only after a successful qualification run. Promotion
alone never implies replayability.

### 4.3 Two evidence lanes

V1 supports two normalized evidence sources.

**Lane A — Triana deterministic assertions**

- `tool_called(name)`
- `tool_not_called(name)`
- `tool_called_before(a,b)`
- `arg_matches(tool,field,rule)`
- `no_loop(threshold)`
- `no_unbacked_claim(rule)`
- `output_matches(regex_or_schema)`
- `terminal_state(no_error)`

Negative assertions are enabled only when the relevant tool dispatch boundary
has passed an observability qualification. Otherwise they are unevaluable.

**Lane B — customer-owned check command**

The customer may provide one command that runs an existing DeepEval,
Braintrust, LangSmith, Promptfoo, or custom check and emits normalized JSONL:

```json
{
  "check_id": "preserve-refund-escalation",
  "status": "pass",
  "score": 1.0,
  "evaluator": "customer-owned",
  "evaluator_version": "sha256:...",
  "evidence_url": "https://..."
}
```

Triana does not reimplement or own the evaluator. It records its identity,
result, gaps, and evidence reference. Direct provider-specific integrations
are out of V1.

### 4.4 Paired CI check

For a claim about regression:

1. The customer explicitly selects an approved `baseline_ref`.
2. GitHub supplies the candidate ref.
3. The Action resolves and launches both refs in isolated worktrees or
   containers using customer-declared commands.
4. The same pinned case version and fixture/configuration fingerprint apply to
   both sides.
5. Every trial carries run ID, case ID, trial ID, side, and code ref into the
   root trace metadata.
6. The Action fetches the exact traces and evaluates both evidence lanes.
7. It records pass/evaluable, end-to-end success, and gaps separately.

There is no implicit merge-base baseline. Without an approved baseline, the
result is `FIRST_OBSERVATION`, never a regression.

`COMPARABLE` requires matched case, fixture/configuration, reset policy, and
execution contract. If those conditions are absent, Triana reports that the
behavior `MOVED`; it does not say the candidate regressed.

### 4.5 Minimal release policy and recommendation

V1 includes a small repository-owned policy, not a policy dashboard:

```yaml
policy:
  regression: block
  insufficient_evidence: review
  observed_only: review
```

The recommendation is rendered mechanically:

- **PASS** — all enforced checks have sufficient comparable evidence and none
  crosses an approved regression limit.
- **REVIEW** — evidence is incomplete, observed-only, non-comparable, or inside
  the configured small-movement band.
- **BLOCK** — a bound, comparable, enforced check crosses its customer-approved
  regression limit.

V1 is advisory by default. `BLOCK` means “Triana recommends blocking”; it does
not fail the GitHub job or become a required check unless the customer
explicitly enables enforcement later.

### 4.6 Release Evidence Record

Every run produces one immutable record containing:

- baseline and candidate code refs;
- runtime binding and observation scope;
- case and evaluator versions;
- fixture/configuration fingerprint;
- per-trial and per-assertion results;
- pass/evaluable, end-to-end success, and gaps;
- evidence-strength labels;
- expected, observed, and reason for each failure;
- advisory PASS/REVIEW/BLOCK recommendation;
- PR link and approving reviews when available;
- previous-record hash and current-record hash.

The record language is generated from evidence. It uses the weakest supported
claim and never turns missing evidence into a pass.

The hosted outputs are:

- one PR comment containing the named risk, recommendation, and link;
- one permanent evidence page;
- one downloadable JSON record;
- `triana verify` for local hash-chain verification.

## 5. What does not ship in V1

- Full production-behavior clustering or coverage percentages.
- “One case protects a behavior family.”
- Automatic ground truth.
- Triana-owned LLM judges.
- Multi-turn user simulation.
- Managed sandboxes, mocks, or world reconstruction.
- Direct Braintrust, DeepEval, LangSmith, or business-metric integrations.
- A visual release-policy builder.
- Automatic case expansion, retirement, or release-specific selection.
- Canary, rollout, rollback, or post-release validation.
- Compliance packets.
- Dashboards.
- An SDK or required re-instrumentation layer.

## 6. Free and paid boundary

- Connect, candidate surfacing, case creation, and Promotion are free.
- One protected case may complete the entire check-and-record loop free
  forever.
- Design-partner pilot: **$500/month flat for 60–90 days**, unlimited records.
- Pricing beyond the pilot is not frozen.

The pilot tests whether evidence plus an advisory recommendation changes
release behavior and commands payment before enforcement becomes mandatory.

## 7. Distribution and code-ownership boundary

V1 is **closed-source**. Running inside customer CI does not require publishing
Triana's implementation.

Triana ships as:

- a versioned compiled CLI distributed in a minimal container image;
- a thin GitHub Action wrapper that pulls and invokes that image;
- a hosted API for organizations, promoted cases, normalized results, record
  chains, evidence pages, and billing;
- a hosted web application for connect, review, Promote, and release history.

The customer-visible integration contains:

- workflow YAML;
- `triana.yml`;
- protected case files when the customer chooses repository storage;
- the declared request template;
- the optional customer-owned check command;
- downloadable evidence JSON and record hashes.

The following remain Triana-owned and undisclosed:

- candidate surfacing and ranking implementation;
- deterministic assertion-engine implementation;
- paired orchestration and language-gate implementation;
- hosted record, chain, and evidence-page services;
- provider adapters and product analytics.

The CLI/container receives only the permissions needed inside the job. Customer
repository code is checked out by GitHub Actions and executed locally; Triana's
hosted service receives no repository access. Trace credentials remain customer
CI secrets. Depending on privacy mode, the CLI uploads only promoted case
definitions, normalized check results, evidence references, and hashes.

Open sourcing any schema, SDK, runner, or evaluator is a later distribution
decision based on adoption and trust needs. Nothing is MIT-licensed at launch.

## 8. Go-out sequence

### M0 — public reference proof

Use `hr_agent` to publish:

- three readable protected cases;
- an A/A control;
- one planted A/B regression;
- baseline and candidate launched from exact refs;
- a reproducible local record JSON and static evidence page;
- every gap, weaker label, cost, and refused claim.

The public reference repository contains the sample agent, workflow YAML,
configuration, cases, generated records, and verification instructions. It
invokes the same versioned Triana CLI/container customers receive; it does not
contain Triana's proprietary source. A skeptic must be able to clone the
reference repository and regenerate the result through the shipped artifact.

### M1 — external proof

Run the same contract on one real partner PR with:

- no Triana-authored customer integration code;
- connect-to-proposal in under 15 minutes;
- eligible-case qualification in under one hour;
- first release record in under one working day;
- a check the partner chooses to retain on the next release.

### Self-serve alpha

Open the alpha after M0 and one successful M1. The public qualifier is:

> “Can a new engineer run your agent from a repository checkout today, and do
> its tool calls appear in your trace store?”

Teams that answer no join the design-partner or waitlist path rather than
receiving a weakened product presented as the full experience.

## 9. YC F26 alignment

| YC thesis | V1 implementation |
|---|---|
| CI release gate for AI agents | GitHub Action produces an advisory release recommendation |
| PASS / REVIEW / BLOCK with evidence | Minimal repository policy renders the recommendation from the record |
| Existing production traces | Langfuse, JSONL, or OTel inlet |
| Existing evals and custom scorers | Generic customer-owned check command and normalized result schema |
| Compare current production with candidate | Explicit approved baseline ref and candidate run in paired CI |
| Replay relevant production cases | Human-approved exact incident cases; no representativeness claim |
| Keep checks current from production | New incidents can be proposed and Promoted into future checks |
| Human owns correctness | Case, assertion, evaluator, threshold, and policy approval remain customer-owned |
| Release evidence compounds | Immutable per-release records chain into release history |

The company thesis remains broader: release intelligence decides whether an
agent change should reach users and preserves the evidence and learning behind
that decision. V1 proves one narrow production-to-release loop; it does not
pretend to implement the entire category.

## 10. Public-claim changes required before alpha

The current site must not claim capabilities beyond V1:

- “returns PASS, REVIEW, or BLOCK” must say **advisory recommendation** until
  enforcement is enabled.
- “unsafe release being blocked” must become **BLOCK recommended**.
- “replays 18 approved production checks” must use a real M0/M1 count.
- “91% of traffic explained,” production-behavior coverage, and confirmed
  regressions must remain labeled demo/roadmap until Phase 4 is real.
- Existing-evaluator and business-metric claims require the generic customer
  command adapter; until it ships, remove them.
- “No repository access” may remain: the Action runs in customer CI from its
  checkout; the hosted Triana service never receives repository access.

## 11. Kill criteria

Stop or materially change the wedge if, across the first three eligible teams:

- fewer than one-third of important incidents qualify as `READY` without
  Triana engineering;
- time to first real record is measured in weeks rather than a working day;
- the record does not change a release conversation or action;
- no team retains a protected case across three releases;
- no team will pay for the pilot;
- no team asks for enforcement after an advisory trust period;
- the customer-command lane merely duplicates an incumbent workflow with no
  unique release action.
