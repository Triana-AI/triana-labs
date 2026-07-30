# Future Release Control considerations

Status: gated future direction; explicitly outside frozen V1
Updated: 2026-07-30

## Purpose

Preserve the plausible expansion path without turning it into current scope.
Every stage requires observed customer behavior and an explicit successor
decision before implementation.

The long-term chain is:

```text
Release Change
→ applicable Release Obligations
→ required and received evidence
→ recommendation
→ human Release Decision
→ rollout and production outcome
→ calibrated future obligations and evidence requirements
```

Frozen V1 ends at the human Release Decision.

## Stage 0 — prove the Release Review

Current scope:

- one declared Release Change;
- one human-selected obligation carried by one Protected Case;
- Triana deterministic evidence plus a generic customer-owned evidence lane;
- comparable baseline/candidate execution;
- typed gaps;
- advisory recommendation;
- immutable Release Evidence Record;
- human Decision Attestation.

Do not advance unless a real team retains the case and the review changes a
release action, owner, scope, timing, or material conversation.

## Stage 1 — multiple obligations, still manually selected

Candidate capability:

- several customer-approved obligations attached to one Release Change;
- obligation-level required-versus-received evidence matrix;
- explicit conflicts and trade-offs;
- no automatic applicability claim.

Entry evidence:

- customers repeatedly assemble several release-critical requirements;
- one-case reviews omit consequential evidence;
- teams can maintain the obligations without Triana services work.

Refuse if the result is merely a larger eval dashboard.

## Stage 2 — assisted applicability and evidence planning

Candidate capability:

- inspect a declared component delta;
- propose which approved obligations may apply;
- propose an evidence plan;
- require human confirmation;
- preserve unknown dependencies and rationale.

Entry evidence:

- manual selection repeatedly misses relevant obligations or consumes
  meaningful release time;
- changes and obligations have stable enough metadata to support useful
  proposals;
- customers reject running every check on every release.

Do not claim automatic impact analysis. An LLM may propose; deterministic code
and humans retain authority.

## Stage 3 — rollout and production-outcome observations

Candidate capability:

- append references to canary, shadow, staged rollout, pause, rollback, support,
  incident, and business-metric evidence;
- bind observations to the exact released identity;
- preserve observation windows and exposure denominators;
- keep the original pre-release record immutable.

Entry evidence:

- teams already conduct staged releases or post-release watching;
- the evidence is fragmented enough to delay detection or confuse ownership;
- customers want the Release Review retained after merge.

Triana should consume customer deployment systems before attempting to replace
their traffic mechanics.

## Stage 4 — outcome calibration

Candidate capability:

- compare predicted and observed behaviour incidence;
- measure directional accuracy and rate calibration;
- identify checks that were predictive, noisy, or blind;
- propose revisions for human review.

Entry evidence:

- enough comparable releases and labeled outcomes exist;
- observation windows and denominators are trustworthy;
- customers use the result to change later release requirements.

Do not describe sparse history as machine learning or infer causality from
confounded releases.

## Stage 5 — optional enforcement and progressive control

Candidate capability:

- required GitHub check after an advisory trust period;
- customer-approved exception workflow;
- progressive exposure recommendations;
- delegated pause or rollback through existing deployment tools.

Entry evidence:

- customers explicitly request enforcement;
- advisory recommendations have demonstrated acceptable false-block and
  missed-regression rates;
- authority, override, audit, and recovery responsibilities are clear.

Never make Triana the silent deployment authority.

## Deployment Simulation relationship

OpenAI-style Deployment Simulation is an evidence-generation method:
production-like contexts are replayed against a candidate and predictions are
checked against later production rates. It can support Stages 2–4.

It is not the entire Release Control lifecycle. Triana should not make
representative deployment simulation a V1 claim, and should prefer consuming a
customer or vendor simulation result before building a simulation platform.

## Quantities to accumulate

- releases per team per month;
- changed and unresolved components per release;
- obligations selected, missed, and retained;
- required, received, invalid, and missing evidence;
- manual hours and decision latency;
- recommendations overridden by humans;
- escaped known failures;
- predicted versus observed incidence;
- time to detect, pause, or roll back;
- obligations that caught a real candidate regression;
- obligations removed or revised after outcome evidence.

These measurements determine whether the compounding asset is the obligation
library, evidence history, policy authority, outcome calibration, or none of
them.

## Kill conditions

Do not expand if:

- Braintrust plus CI and deployment tooling already supplies the complete
  workflow with negligible effort;
- Release Reviews do not change actions;
- cases are not retained;
- release frequency is too low;
- outcome data cannot be bound to exact releases;
- customers do not ask for required checks or enforcement;
- maintaining obligations becomes a high-touch consulting service.
