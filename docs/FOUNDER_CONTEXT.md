# Founder context, rationale, and doubts

This file preserves why the frozen product has this shape so future work does
not reopen the same arguments without new evidence.

## The original problem

Agent teams change prompts, models, tools, retrieval, policies, and harnesses.
They often inspect a few examples, run fragmented evals, and deploy. Problems
found in production are manually investigated and inconsistently converted
into future release protection.

Observability systems show what happened. Eval systems run datasets and
scorers. CI runs commands. The proposed missing workflow is:

```text
important production incident
→ human-approved repeatable release case
→ comparable baseline/candidate execution
→ decision-facing release evidence
→ retained protection and release history
```

## Why start with one incident

Earlier versions attempted to promise representative production replay sets,
user-intent clustering, coverage percentages, automatic eval maintenance, and
release control simultaneously. Those may become valuable, but they introduced
unsupported claims before the core loop had been proven.

One exact incident is narrower but honest:

- the customer already agrees it matters;
- the semantic expectation can be approved;
- replayability can be tested rather than assumed;
- the next PR provides a concrete decision moment;
- failure to qualify teaches us where bounded replay breaks.

Production issue discovery is acquisition. The retained protected case and
evidence record are the product.

## Why Braintrust does not automatically make Triana irrelevant

Braintrust and adjacent products already provide traces, datasets, scorers,
experiments, production-derived cases, remote execution patterns, and CI
surfaces. “Observability plus evals plus a GitHub Action” is not a company.

Triana's hypothesis is narrower:

- take a failure the customer approves;
- prove that it is runnable under a declared execution contract;
- compare an explicitly approved baseline and candidate in customer custody;
- normalize Triana and customer-owned evaluation evidence;
- distinguish behavioral failure, evaluation gap, and non-comparability;
- render a customer-owned release policy;
- preserve the whole decision as a durable, verifiable record.

This remains only a hypothesis. Braintrust could compose many of these
capabilities. Triana earns a company only if teams adopt it as a recurring
release ritual, retain protected cases, value the independent evidence record,
and eventually make the check required.

The decisive interview question is not “would this feature be useful?” It is:

> Tell me about the last agent change whose release decision was genuinely
> difficult. What evidence did you assemble, who interpreted it, what remained
> unknown, and what would have changed the decision?

Then test whether Triana's proposed record would have changed an action,
conversation, owner, or time-to-decision.

## Company thesis

A deploy-time gate alone historically collapses into the surrounding platform.
Triana can become a company only if repeated releases create something that is
hard to replace:

```text
useful incident check
→ repeated release ritual
→ organization-specific protected-case library
→ versioned evaluator and decision history
→ required evidence package
→ customer-owned policy and optional enforcement
→ production confirmation, refutation, and maintenance
```

The long-term category is release intelligence for AI agents: an independent
evidence and authorization boundary between an agent change and production.
V1 proves only the first production-to-release loop.

## Evidence inherited as founder context

The current direction was shaped by:

- Akarsh's Triana and YC F26 thesis;
- two strong early user interviews and subsequent founder conversations;
- the observation that custom evaluators often live inside customer stacks
  rather than one vendor;
- existing Kairos work on trace-derived behavioral signals;
- market research showing incumbents cover many component features but rarely
  bind composite release identity, evidence, gaps, policy, and approvals into
  one release record;
- the lack of strong public proof that agent teams currently enforce
  eval-driven release gates at scale.

These points guide discovery; they are not all validated market facts.

Canonical Notion decision:

- Triana Self-Serve V1 — Frozen Ship Boundary:
  https://app.notion.com/p/3acf41c1f7d781868502d8fcddf08890

Related founder sources:

- YC F26:
  https://app.notion.com/p/3aaf41c1f7d78017bee0c8610004870c
- Thesis reset:
  https://app.notion.com/p/3a6f41c1f7d78195a2b5f4b075e37e69
- Wedge V1 open threads and design-partner questions:
  https://app.notion.com/p/3acf41c1f7d7816e840ddb28d023f4b1

## Unknowns that must stay visible

1. What share of important incidents can become `READY` without services work?
2. What exactly does a customer's replay endpoint expose: final answer, tool
   trajectory, state transitions, or all three?
3. Can baseline and candidate be run comparably without reconstructing a
   production world?
4. How many trials are affordable and sufficient for a meaningful release
   statement?
5. Does deterministic assertion coverage address risks customers actually care
   about?
6. Does the generic customer-owned command add release value or merely repeat
   an incumbent experiment?
7. Who approves the protected case, evaluator, threshold, and policy?
8. Does advisory evidence change a real merge or release decision?
9. Will teams retain cases and records across multiple releases?
10. Will anyone pay before enforcement or compliance features exist?
11. After trust develops, do customers ask for mandatory blocking?
12. Is the durable asset the case library, release history, policy authority,
    or none of them?

## Design-partner discovery

Ask for artifacts and stories, not opinions:

- Show the last difficult agent release.
- Show the incident or trace that later mattered.
- Show the current eval, CI, and approval path.
- Identify the approved production baseline.
- Attempt to turn one incident into a runnable case together.
- Count every manual edit, fixture, secret, mock, and missing observation.
- Run A/A before A/B.
- Present the record and ask what action it changes.
- Ask whether they would retain it for the next three releases.
- Ask for payment only after the first real record.

Record disconfirming evidence with equal weight. Scope changes require repeated
evidence from eligible teams, not excitement during a demo.
