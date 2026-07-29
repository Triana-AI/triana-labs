# Triana self-serve V1

Status: **frozen build boundary**

Frozen on 2026-07-29 by Akarsh. Transferred into this clean-room repository on
2026-07-30. This document governs shipping scope until customer evidence
produces an explicit successor decision.

## Product in one sentence

Triana turns one approved production failure into a release check, reruns it
against an approved baseline and a candidate inside the customer's CI, and
returns an advisory PASS, REVIEW, or BLOCK recommendation with permanent
evidence.

Production replay is the check mechanism. The Release Evidence Record is the
durable artifact. The release recommendation is the decision-facing output.

## Who V1 is for

The self-serve customer has:

- a customer-facing or operationally consequential agent;
- existing structured traces through Langfuse, JSONL, or OTel;
- at least one production or staging failure worth preventing;
- an agent a new engineer can run from a repository checkout in CI;
- a bounded single-turn request path;
- a test environment where repeated executions are safe;
- releases frequent enough that a recurring check matters.

Agents requiring production-only state, uncontrolled third-party side effects,
long multi-turn simulation, or reconstruction of a large enterprise world are
not eligible for the self-serve promise.

## First-use loop

1. Connect Langfuse read-only, upload JSONL/OTel, or use local mode.
2. State in one line what the agent is supposed to do.
3. Triana surfaces a ranked, deduplicated list of mechanically suspicious
   traces.
4. The user chooses one known incident.
5. Triana proposes one exact protected case and executable assertions.
6. The user edits and Promotes the case.
7. Qualification assigns `READY`, `NEEDS_FIXTURE`, or `NOT_YET`.
8. For a `READY` case, CI runs an explicit approved baseline and the PR
   candidate under the same execution contract.
9. Triana emits an advisory recommendation, PR comment, evidence page, JSON
   record, and verifiable hashes.

Promotion alone never implies replayability. One promoted trace protects one
exact case; V1 makes no behavior-family or representative-coverage claim.

## Candidate surfacing

V1 uses deterministic signals:

- tool error;
- terminal error;
- repeated tool loop;
- redundant calls;
- aborted execution;
- unbacked action claim;
- cost or latency spike;
- customer-flagged trace.

LLMs may later help describe or group candidates, but the V1 candidate
membership and ranking must remain reproducible and inspectable.

## Protected case

A versioned case contains:

- risk name;
- source trace and environment;
- replay input;
- expected behavior;
- prohibited behavior;
- allowed alternatives;
- policy or business context;
- executable checks;
- approver and approval time;
- qualification state.

The human owns semantic correctness. An LLM may draft these fields but cannot
activate them.

## Two evidence lanes

### Lane A: Triana deterministic assertions

- `tool_called(name)`
- `tool_not_called(name)`
- `tool_called_before(a,b)`
- `arg_matches(tool,field,rule)`
- `no_loop(threshold)`
- `no_unbacked_claim(rule)`
- `output_matches(regex_or_schema)`
- `terminal_state(no_error)`

Negative assertions are evaluable only after the relevant tool-dispatch
boundary passes observability qualification.

### Lane B: customer-owned check command

The customer may run DeepEval, Braintrust, LangSmith, Promptfoo, or custom code
and emit normalized JSONL:

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

The evaluator may itself use an LLM. Triana records its identity, result,
evidence reference, and gaps. Triana does not reimplement it or treat it as a
Triana-owned judgment.

## Paired CI contract

1. The customer selects an approved `baseline_ref`.
2. GitHub supplies the candidate ref.
3. Both refs run in isolated worktrees or containers using customer-declared
   commands.
4. Both sides use the same pinned case, fixture/configuration fingerprint,
   reset policy, and execution contract.
5. Every trial binds run ID, case ID, trial ID, side, and code ref into root
   trace metadata.
6. Triana fetches the exact traces and evaluates both evidence lanes.
7. It records pass/evaluable rate, end-to-end success, and gaps separately.

Without an approved baseline, the result is `FIRST_OBSERVATION`, never a
regression. Without matched execution conditions, Triana says behavior
`MOVED`; it does not say the candidate regressed.

## Release policy

V1 uses a small repository-owned policy:

```yaml
policy:
  regression: block
  insufficient_evidence: review
  observed_only: review
```

- **PASS:** all enforced checks have sufficient comparable evidence and none
  crosses an approved regression limit.
- **REVIEW:** evidence is incomplete, observed-only, non-comparable, or within a
  configured small-movement band.
- **BLOCK:** a bound, comparable, enforced check crosses its
  customer-approved regression limit.

All three are advisory by default. `BLOCK` means Triana recommends blocking; it
does not fail the GitHub job unless the customer later opts into enforcement.

## Release Evidence Record

Every run records:

- baseline and candidate refs;
- runtime binding and observation scope;
- case and evaluator versions;
- fixture/configuration fingerprint;
- per-trial and per-assertion results;
- pass/evaluable rate, end-to-end success, and gaps;
- evidence-strength labels;
- expected, observed, and reason for each failure;
- advisory recommendation;
- PR and approval references where available;
- previous-record and current-record hashes.

Record language must use the weakest supported claim. Missing evidence never
becomes a pass.

## Distribution and privacy

Triana V1 is closed-source:

- versioned compiled CLI in a minimal container;
- thin GitHub Action wrapper;
- hosted API for organizations, cases, normalized results, record chains,
  evidence pages, and billing;
- hosted web application for connect, review, Promote, and history.

Customer-visible integration:

- workflow YAML and `triana.yml`;
- customer request template;
- optional customer-owned check command;
- protected case files when repository storage is selected;
- evidence JSON and record hashes.

The hosted service receives no repository access. Source, credentials, and
fixtures remain in customer CI. Privacy mode uploads only approved case
definitions, normalized results, evidence references, and hashes.

Nothing is open-sourced at launch.

## Free and paid

- Connect, surfacing, case creation, and Promotion are free.
- One protected case completes the entire loop free forever.
- Design-partner pilot: $500/month flat for 60–90 days with unlimited records.
- Later pricing is not frozen.

## Deliberately outside V1

- representative production coverage;
- behavior-family protection claims;
- full behavior clustering and coverage maps;
- automatic ground truth;
- Triana-owned LLM judges;
- multi-turn user simulation;
- managed sandboxes, mocks, or world reconstruction;
- provider-specific evaluator integrations;
- visual policy authoring;
- automatic case expansion, retirement, or release-specific selection;
- mandatory blocking by default;
- canary, rollout, rollback, or post-release validation;
- compliance packets and dashboards;
- SDK or required re-instrumentation layer;
- open-source implementation.

## Go-out sequence

### M0: public reference proof

Publish a reference agent with:

- three readable protected cases;
- an A/A control;
- one planted A/B regression;
- exact baseline and candidate refs;
- reproducible JSON records and a static evidence page;
- every gap, weak label, cost, and refused claim.

The public repository contains the sample agent, workflow, configuration,
cases, records, and reproduction instructions. It invokes Triana's shipped
container but contains no Triana source.

### M1: external proof

On one real partner PR:

- no Triana-authored customer integration code;
- connect-to-proposal in under 15 minutes;
- eligible-case qualification in under one hour;
- first record in under one working day;
- the partner retains the case for a later release.

### Self-serve alpha

Open after M0 and one successful M1. Public qualifier:

> Can a new engineer run your agent from a repository checkout today, and do
> its tool calls appear in your trace store?

## Success and kill criteria

Measure:

- auto-qualification rate;
- time to first promoted case and first release record;
- important-incident share that becomes `READY`;
- gap and comparability rates;
- whether the record changes a release action or conversation;
- retention of a case across releases;
- willingness to pay;
- requests for enforcement after an advisory trust period;
- unique value of the customer-command lane over incumbents.

Stop or materially change the wedge if, across the first three eligible teams:

- fewer than one-third of important incidents qualify without Triana
  engineering;
- time to first real record is measured in weeks;
- the record changes no release conversation or action;
- no team retains a case across three releases;
- no team pays for the pilot;
- no team asks for enforcement after trust is established;
- the customer-command lane merely duplicates an incumbent.

## Change control

One customer request is recorded, not shipped. Repeated blockers among
qualified customers create a focused discovery test. A paying customer unable
to complete the core loop is evidence against the ICP or contract. Changes
require observed evidence, an explicit successor decision, and updates to both
the decision log and this document.
