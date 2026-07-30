# Triana discovery ask guide

Status: working discovery instrument, not a product decision
Updated: 2026-07-30

## Purpose

Discover whether real AI-agent releases already follow this chain, where it
breaks, and what the break costs:

```text
Release Change
→ Release Obligation
→ required and received evidence
→ recommendation and human decision
→ production outcome
→ future protection
```

Do not ask whether the interviewee likes Triana or agrees that the category
should exist. Reconstruct one recent release using artifacts, dates, owners,
systems, and actual actions.

## Opening

> I am studying how teams decide whether an AI-agent change is ready to ship.
> I am not asking you to evaluate a product idea. Could we reconstruct the last
> release that felt uncertain, consequential, or unusually manual?

Ask permission to inspect the PR, eval report, incident, release checklist,
Slack thread, deployment record, or equivalent artifact. Redacted examples are
enough.

## 1. Choose one real release

- What was the last model, prompt, tool, retrieval, policy, or harness change
  that made the team pause?
- When did it happen?
- Who proposed it, who implemented it, and who could stop it?
- How frequently does the team make changes of this class?
- What would have happened if the change were delayed for a week?

Reject generalized answers such as “we usually run evals.” Return to one
specific release.

## 2. Reconstruct the Release Change

- What did the team believe changed?
- What else changed in practice: provider, parameters, prompt, tools, data,
  evaluator, fixture, or runtime?
- Where was the complete baseline and candidate identity recorded?
- Could somebody reproduce both versions today?
- Which differences were unknown or discovered later?

Quantify:

- number of components believed to have changed;
- number actually changed;
- number not pinned or not reproducible;
- number of people required to determine the complete change;
- engineering hours spent reconstructing identity.

## 3. Find the obligations

- Which behaviours were considered non-negotiable for this release?
- Why did each matter: production incident, customer promise, policy,
  compliance requirement, or general quality target?
- Where were those requirements written?
- Who approved them?
- How did the team decide which previous incidents or eval cases applied?
- Was anything important remembered only by one person?

Ask:

> Show me one past production failure that affected what you required before
> this release.

Quantify:

- number of named release-critical behaviours;
- number linked to confirmed incidents;
- number with an owner and severity;
- number with executable checks;
- number selected manually;
- number discovered after the release.

## 4. Reconstruct the evidence plan

- What evidence did the team require before making the decision?
- Who decided that this was enough?
- Which systems produced it: Braintrust, LangSmith, custom evals, unit tests,
  security checks, human review, shadow traffic, or another source?
- Did the team rerun a known failure against both baseline and candidate?
- Did it run A/A or repeated trials to understand variance?
- What could not be executed or compared?

Quantify:

- required checks;
- checks completed, failed, missing, invalid, or inconclusive;
- systems queried;
- manual exports or transformations;
- evaluator cost and wall-clock time;
- engineering and reviewer hours;
- evidence discovered only after somebody asked.

## 5. Reconstruct the decision

- Who made the final approve, hold, or exception decision?
- What rule or threshold controlled it?
- Did an overall score hide any release-critical regression?
- What remained unknown when the decision was made?
- Was an exception accepted? By whom and why?
- Where is the decision and rationale recorded now?

Quantify:

- time from candidate-ready to decision;
- people and handoffs involved;
- number of exceptions;
- delay caused by missing evidence;
- whether the evidence changed the action, owner, scope, or rollout.

## 6. Follow the production outcome

- How was the candidate exposed: full release, shadow, internal users, segment,
  canary, or staged rollout?
- What did the team watch?
- Did a known failure recur?
- What new failure appeared?
- How long did detection and mitigation take?
- Was the pre-release prediction compared with the observed rate?

Quantify:

- initial exposure;
- observation window;
- known-failure recurrence;
- new severe failures;
- predicted and observed failure rates when available;
- time to detect, pause, or roll back.

## 7. Test whether anything tied back

- Did this outcome create or change a future eval, policy, checklist, or owner?
- Could the next engineer discover why that protection exists?
- Did a noisy check get removed or weakened?
- Has the same incident escaped more than once?
- Show the artifact that changed for the next release.

Quantify:

- new or revised protections;
- repeated incidents;
- obsolete checks retained;
- checks that caught a real candidate regression;
- later releases that reused the same protection.

## 8. Braintrust-specific probe

If the team uses Braintrust:

- Show the exact dataset, scorer, experiment, comparison, and CI result used.
- Where is the complete release identity?
- Where is the statement that a particular behaviour is release-critical?
- How is required evidence distinguished from optional evidence?
- Where are missing or non-comparable checks represented?
- Where does the approve, hold, or exception decision live?
- Can the record join evidence produced outside Braintrust?
- Where is the production outcome tied back to the release and future
  requirement?

Do not ask whether Braintrust could theoretically add these capabilities. Ask
whether the team completed the workflow in its actual release.

## Quantitative capture sheet

| Measure | Value |
|---|---|
| Releases of this class per month | |
| Components changed / unpinned | |
| Named obligations / incident-derived obligations | |
| Required / received / missing evidence items | |
| Evaluation systems involved | |
| Engineering hours | |
| Reviewer hours | |
| Time to release decision | |
| Exceptions accepted | |
| Escaped failures | |
| Time to detect or mitigate | |
| Protections retained across later releases | |
| Would the current stack reproduce the complete record? | |

## Interpretation

### Strongest signal

The complete chain matters, but it is assembled manually across several
systems, leaves consequential gaps, consumes recurring time, changes release
actions, and is retained for later releases.

### Weak signal

The workflow is comfortably reproduced inside the incumbent stack, evidence is
cheap and complete, the human decision is straightforward, and no durable
cross-release record is needed.

### No-demand signal

The chain does not exist, but its absence causes no meaningful delay,
uncertainty, escaped failure, ownership problem, or business consequence.

### Services-risk signal

Every case requires Triana to reconstruct a bespoke environment, author the
customer's evaluator, or decide semantic truth on the customer's behalf.

## Close

Do not ask “Would you buy this?” before showing work on a real release. Ask:

> If we returned this release as one review showing the exact change,
> obligation, required and received evidence, gaps, policy reasoning, and
> decision state, what action or conversation would have changed?

For a design partner, the next commitment is an artifact and a real PR—not
verbal enthusiasm.
