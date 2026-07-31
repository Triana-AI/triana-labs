# Triana self-serve V1

Status: **suspended build boundary** (frozen 2026-07-29; suspended 2026-07-31)

Frozen on 2026-07-29 by Akarsh. Transferred into this clean-room repository on
2026-07-30. The V1 ICP was narrowed on 2026-07-30 to conversational,
tool-using agents.

**Suspension notice (2026-07-31, Akarsh):** After the Braintrust HRAI dogfood
falsified the generic release layer as a standalone wedge (see
`internal/research/BRAINTRUST_FALSIFICATION_AND_DOUBT_DRIVEN_DECISION_2026-07-30.md`
and the 2026-07-31 decision-log entries), implementation of V1 slices beyond
the completed Slice 0A contract kernel is suspended. The active build surface
is **Triana Labs Preview**, governed by `triana-labs/CHARTER.md`. This
document is retained as the specification of the suspended V1: it is not
deleted, its decisions are not silently rewritten, and resuming it requires an
explicit decision-log entry. Where this document and the Labs charter
conflict, the charter governs Labs work and this document governs nothing
until resumed. The Slice 0A kernel in `triana-core/` remains shared, live
infrastructure.

## Product in one sentence

Triana produces a Release Review for a conversational, tool-using agent change
by combining an approved production-derived replay case with any available
customer-owned evaluation results, comparing an approved baseline and candidate
inside customer CI, applying a customer-approved Release Policy, and returning
an advisory recommendation with permanent evidence.

Production issue discovery is the acquisition path. Production replay is one
check mechanism. The Release Evidence Record is the durable artifact. The
Release Review is the decision-facing product surface. The human, not Triana,
makes the Release Decision.

The canonical product logic is:

```text
declared Release Change
        ↓
human-approved Release Obligation
        ↓
required and received Evaluation Evidence
        ↓
Release Policy recommendation
        ↓
human Release Decision
        ↓
future production outcome and updated protection
```

V1 implements the chain through the human Release Decision. Production outcome
calibration and automatic updates to future protection remain future Release
Control work.

## Product hierarchy and vocabulary

Use these terms consistently in product, code, UI, and customer conversations:

| Term | Exact meaning in Triana | It is not |
|---|---|---|
| **Production issue discovery** | Free trace-to-candidate acquisition path used to find an incident worth protecting | The differentiated paid product |
| **Release Change** | The declared baseline-to-candidate delta plus the composite identities and unresolved differences needed to describe the exact candidate under review | Automatic impact analysis or proof that only the declared component changed |
| **Release Obligation** | A human-approved statement of behavior that must be preserved for the release, including why it matters and what evidence is required | A score, dataset row, or automatically invented requirement |
| **Protected Case** | The V1 executable form of one Release Obligation: a versioned production-derived risk, replay input, expected behavior, and checks | Automatic ground truth, a complete obligation graph, or a representative behavior family |
| **Evidence Requirement** | A customer-approved statement of which checks or evaluator results are required for an obligation in the current review | The evidence result itself |
| **Production replay** | Re-execution of a Protected Case against a declared customer runtime | Literal time travel, full production-world reconstruction, or the whole product |
| **Evaluation evidence** | Versioned results from Triana assertions or customer-owned evaluators, including typed gaps | A release decision by itself |
| **Release Evidence Record** | Immutable facts about the Release Change, obligation, required and received evidence, identity, execution, gaps, comparison, policy version, and references | A verdict, approval, or dashboard |
| **Release Policy** | Customer-approved rules that map sufficient evidence to an advisory recommendation | An evaluator or a deployment system |
| **Release Recommendation** | Mechanically rendered `PASS`, `REVIEW`, or `BLOCK` guidance | The human Release Decision or mandatory enforcement |
| **Release Review** | The PR comment and permanent page where change, obligation, required and received evidence, gaps, recommendation, and any Decision Attestation are reviewed together | Another eval report |
| **Release Decision** | A human action such as approve, hold, or approve with an exception, linked to the reviewed evidence | Something Triana silently infers from a score |
| **Decision Attestation** | An append-only reference to the human Release Decision and optional exception rationale | A mutation of the Release Evidence Record |
| **Release Control** | The long-term lifecycle joining policy, review, human authority, rollout evidence, and post-release learning | A V1 claim that Triana deploys or rolls back software |
| **Evaluation-set maintenance** | A supporting feedback loop that can turn approved production evidence into future protection | Triana's product center or an automatic fix loop |

## Who V1 is for

The self-serve customer has:

- a customer-facing or internal conversational agent;
- a text or voice conversation surface, with replayable structured turns or a
  transcript plus ordered tool activity;
- one or more tools through which the agent retrieves information, changes
  state, takes an action, or escalates;
- existing structured traces through Langfuse, JSONL, or OTel;
- at least one production or staging failure worth preventing;
- an agent a new engineer can run from a repository checkout in CI;
- a bounded conversational episode that can be recreated without a live user
  or an open-ended user simulator;
- a test environment where repeated executions are safe;
- releases frequent enough that a recurring check matters.

Offline document-processing pipelines, background batch agents, coding agents,
research agents, and other non-conversational autonomous workflows are outside
V1 even if they could technically satisfy the generic contracts. Voice agents
qualify only when the text/transcript, turn structure, tool activity, and
outcome needed by the protected case are observable; raw acoustic quality,
latency of turn taking, and telephony behavior are not V1 evaluation surfaces.

Agents requiring production-only state, uncontrolled third-party side effects,
open-ended multi-turn simulation, or reconstruction of a large enterprise
world are not eligible for the self-serve promise.

## Product flow

### Acquisition and case creation

1. Connect Langfuse read-only, upload JSONL/OTel, or use local mode.
2. State in one line what the agent is supposed to do.
3. Triana surfaces a ranked, deduplicated list of mechanically suspicious
   traces.
4. The user chooses one known incident.
5. Triana proposes one exact protected case and executable assertions.
6. The user edits and Promotes the case.
7. Qualification assigns `READY`, `NEEDS_FIXTURE`, or `NOT_YET`.

Everything through qualification is the acquisition and onboarding path. It
creates one trusted production-derived input for a future release; it is not
yet the recurring release product.

### Recurring Release Review

1. A PR or release candidate invokes `triana check`.
2. The customer declares the intended Release Change. Triana binds the
   approved baseline, candidate, composite runtime fingerprints, and any
   unresolved differences without claiming automatic impact analysis.
3. The user selects the approved Protected Case whose Release Obligation
   applies. V1 does not automatically infer applicability.
4. Customer CI runs the explicit approved baseline and the candidate under the
   same execution contract.
5. Triana evaluates the pinned Protected Case and, when configured, imports the
   customer's existing evaluator results through the customer-owned check
   command.
6. Triana organizes the required and received evidence by Release Obligation,
   then normalizes facts, gaps, identity, and comparability.
7. The versioned Release Policy renders an advisory `PASS`, `REVIEW`, or
   `BLOCK` recommendation.
8. Triana appends an immutable Release Evidence Record binding the Release
   Change, obligation, normalized evidence, policy version, and recommendation.
9. The Release Review appears as a PR comment and permanent page showing the
   change, obligation, required and received evidence, failures, unknowns, and
   policy reasoning.
10. A human approves, holds, or accepts an exception through the existing
   GitHub review/release workflow; Triana appends a separate Decision
   Attestation linking that decision and rationale to the record.

V1 stops at a reviewable, recorded Release Decision. It does not deploy,
progressively expose, pause, or roll back the candidate.

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

- Release Obligation statement;
- obligation source, such as a confirmed incident or customer policy;
- severity and owner;
- customer-declared applicability conditions;
- required evidence for V1 review;
- risk name;
- source trace and environment;
- conversation prefix or bounded replay input;
- relevant turn and tool context;
- expected behavior;
- prohibited behavior;
- allowed alternatives;
- required escalation or human handoff when applicable;
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

1. The customer declares the intended Release Change.
2. The customer selects an approved `baseline_ref`.
3. GitHub supplies the candidate ref.
4. Triana records the declared delta, the composite baseline and candidate
   fingerprints it can observe, and any unresolved identity difference.
5. Both refs run in isolated worktrees or containers using customer-declared
   commands.
6. Both sides use the same pinned case, fixture/configuration fingerprint,
   reset policy, and execution contract.
7. Every trial binds run ID, case ID, trial ID, side, and code ref into root
   trace metadata.
8. Triana fetches the exact traces and evaluates both evidence lanes.
9. It records pass/evaluable rate, end-to-end success, and gaps separately.

Without an approved baseline, the result is `FIRST_OBSERVATION`, never a
regression. Without matched execution conditions, Triana says behavior
`MOVED`; it does not say the candidate regressed. An incomplete composite
identity remains an explicit limitation and cannot silently validate the
customer's causal claim.

## Release Policy

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

All three are Release Recommendations and are advisory by default. `BLOCK`
means Triana recommends holding the release; it is not itself the human Release
Decision and does not fail the GitHub job unless the customer later opts into
enforcement.

## Release Evidence Record

Every run records:

- declared Release Change;
- baseline and candidate refs;
- observable composite runtime fingerprints and unresolved differences;
- runtime binding and observation scope;
- Release Obligation and Protected Case versions;
- required evidence and received evidence status;
- case and evaluator versions;
- fixture/configuration fingerprint;
- per-trial and per-assertion results;
- pass/evaluable rate, end-to-end success, and gaps;
- evidence-strength labels;
- expected, observed, and reason for each failure;
- advisory recommendation;
- Release Policy version;
- PR reference;
- previous-record and current-record hashes.

Record language must use the weakest supported claim. Missing evidence never
becomes a pass. A later human decision never mutates this record.

## Decision Attestation

After reviewing the record, the release owner may approve, hold, or approve
with an exception through the existing GitHub/release workflow. Triana appends
a separate immutable attestation containing:

- the Release Evidence Record hash;
- decision type;
- actor and time;
- source reference such as a GitHub review, merge, hold, or release approval;
- exception rationale when supplied;
- previous-attestation and current-attestation hashes.

Absence of an attestation is displayed as `DECISION PENDING`; it is not
inferred from the recommendation or repository state.

## Release Review

The V1 product surface is one Release Review, not a dashboard. It must answer,
in order:

1. What Release Change is being considered, what is the approved baseline, and
   which identity differences remain unresolved?
2. Which Release Obligation applies, why does it matter, and who approved it?
3. What evidence was required for that obligation?
4. What evidence was received from Triana and customer-owned evaluators?
5. Which named risks improved, regressed, stayed unchanged, or could not be
   evaluated?
6. Is the evidence comparable and sufficient, and what remains unknown?
7. Which Release Policy rule produced the recommendation?
8. Who made the human Release Decision, and was an exception accepted?

The evidence page and PR comment are two views of the same Release Review. The
view may update from `DECISION PENDING` when a Decision Attestation is appended;
the underlying Release Evidence Record does not change.

## Distribution and privacy

Triana V1 is closed-source:

- versioned compiled CLI in a minimal container;
- thin GitHub Action wrapper;
- hosted API for organizations, cases, normalized results, record chains,
  Release Reviews, and billing;
- hosted web application for connect, Promote, Release Review, and history.

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
- One protected case completes one recurring Release Review loop free forever.
- Design-partner pilot: $500/month flat for 60–90 days with unlimited records.
- Later pricing is not frozen.

## Deliberately outside V1

- automatic Release Change discovery or impact analysis;
- automatic obligation applicability or evidence-plan generation;
- multi-obligation dependency graphs and organization-wide obligation
  management;
- representative production coverage;
- behavior-family protection claims;
- full behavior clustering and coverage maps;
- offline document-processing agents and batch pipelines;
- coding, research, and other non-conversational autonomous agents;
- raw audio quality, telephony, interruption, and turn-taking evaluation;
- automatic ground truth;
- Triana-owned LLM judges;
- multi-turn user simulation;
- managed sandboxes, mocks, or world reconstruction;
- provider-specific evaluator integrations;
- visual policy authoring;
- automatic case expansion, retirement, or release-specific selection;
- automatic evaluator maintenance, fix generation, or self-modification;
- mandatory blocking by default;
- canary, rollout, rollback, or post-release validation;
- outcome-calibrated policy learning;
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
- a static Release Review showing recommendation and a linked Decision
  Attestation;
- every gap, weak label, cost, and refused claim.

The public repository contains the sample agent, workflow, configuration,
cases, records, and reproduction instructions. It invokes Triana's shipped
container but contains no Triana source.

### M1: external proof

On one real partner PR:

- no Triana-authored customer integration code;
- connect-to-proposal in under 15 minutes;
- eligible-case qualification in under one hour;
- first Release Review in under one working day;
- the partner retains the case for a later release.

### Self-serve alpha

Open after M0 and one successful M1. Public qualifier:

> Can a new engineer run one bounded conversation with your agent from a
> repository checkout today, and do its turns and tool calls appear in your
> trace store?

## Future Release Control direction

Future work may extend the V1 chain only after repeated customer evidence:

1. multiple obligations selected for a specific Release Change;
2. assisted applicability and evidence planning with human approval;
3. rollout and production-outcome references attached without mutating the
   original Release Evidence Record;
4. predicted-versus-observed outcome calibration;
5. human-approved updates to future obligations and evidence requirements;
6. optional enforcement, progressive exposure, pause, or rollback through
   customer-owned deployment systems.

None of these items is an active V1 commitment. Entry criteria and refusal
conditions live in
[`internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md`](../internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md).

## Success and kill criteria

Measure:

- auto-qualification rate;
- time to first promoted case and first Release Review;
- declared Release Change identity completeness and unresolved differences;
- required-versus-received evidence completeness for the approved obligation;
- engineering hours, reviewer hours, systems involved, and decision latency;
- important-incident share that becomes `READY`;
- gap and comparability rates;
- whether the Release Review changes a release action or conversation;
- retention of a case across releases;
- willingness to pay;
- requests for enforcement after an advisory trust period;
- unique value of the customer-command lane over incumbents;
- whether the existing stack can reproduce the complete change-to-decision
  record without material custom glue.

Stop or materially change the wedge if, across the first three eligible teams:

- fewer than one-third of important incidents qualify without Triana
  engineering;
- time to first Release Review is measured in weeks;
- the Release Review changes no release conversation or action;
- no team retains a case across three releases;
- no team pays for the pilot;
- no team asks for enforcement after trust is established;
- the customer-command lane merely duplicates an incumbent;
- actual releases show no measurable fragmentation, delay, uncertainty,
  ownership gap, or escaped failure across the ontology.

## Change control

One customer request is recorded, not shipped. Repeated blockers among
qualified customers create a focused discovery test. A paying customer unable
to complete the core loop is evidence against the ICP or contract. Changes
require observed evidence, an explicit successor decision, and updates to both
the decision log and this document.
