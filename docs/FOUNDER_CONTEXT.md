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
→ normalized existing eval + production replay evidence
→ Release Evidence Record
→ Release Policy recommendation
→ Release Review
→ human Release Decision
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

Production issue discovery is acquisition. The Protected Case is an approved
input. Production replay is a check mechanism. The Release Evidence Record is
the durable artifact. The recurring product is the Release Review where a
customer evaluates the evidence, recommendation, gaps, and human decision
together.

## Why Braintrust does not automatically make Triana irrelevant

Braintrust and adjacent products already provide traces, datasets, scorers,
experiments, production-derived cases, remote execution patterns, and CI
surfaces. “Observability plus evals plus a GitHub Action” is not a company.
Braintrust documents this workflow across
[systematic evaluation](https://www.braintrust.dev/docs/evaluate),
[experiment comparison](https://www.braintrust.dev/docs/evaluate/compare-experiments),
and [production scoring](https://www.braintrust.dev/docs/evaluate/score-online).

The concise answer is:

> Braintrust tells you how a candidate performed. Triana tells you whether this
> exact change has satisfied the organization's obligations and is ready for a
> human release decision.

The object-level distinction is:

```text
Braintrust:
Dataset → Task → Scorer → Experiment → Score

Triana:
Release Change → Release Obligation → Evidence
→ Release Recommendation → Human Release Decision
→ future Production Outcome → future protection
```

Triana's hypothesis is narrower:

- begin with the exact Release Change rather than an experiment;
- take a failure the customer approves;
- represent the human-approved requirement as a Release Obligation carried by
  one executable Protected Case in V1;
- prove that it is runnable under a declared execution contract;
- compare an explicitly approved baseline and candidate in customer custody;
- normalize Triana and customer-owned evaluation evidence;
- distinguish behavioral failure, evaluation gap, and non-comparability;
- render a customer-owned release policy;
- present a Release Review that links the recommendation to human authority;
- preserve the evidence and recommendation in an immutable Release Evidence
  Record and the later human outcome in a separate Decision Attestation.

This remains only a hypothesis. Braintrust could compose many of these
capabilities. Triana earns a company only if teams adopt it as a recurring
release ritual, retain protected cases, value the independent evidence record,
and eventually make the check required.

The defensible claim is not that Braintrust is technically incapable. A team
fully standardized on Braintrust may reproduce the workflow with Braintrust,
GitHub, deployment tools, and custom glue. Discovery must determine whether the
change-to-obligation-to-decision chain exists in actual releases, whether it
spans multiple systems, and whether its fragmentation changes cost, delay,
ownership, uncertainty, or escaped failures.

The decisive interview question is not “would this feature be useful?” It is:

> Tell me about the last agent change whose release decision was genuinely
> difficult. What evidence did you assemble, who interpreted it, what remained
> unknown, and what would have changed the decision?

Then test whether Triana's proposed record would have changed an action,
conversation, owner, or time-to-decision.

The early interviews support different parts of the ladder and must not be
overread:

- Priyanshu's workflow supports the acquisition wedge. Problems are often
  found through user reports, manual trace inspection, and post-release
  watching; exact failing cases and causes matter more than aggregate scores.
- Ashutosh at Risa supports the broader release-lifecycle hypothesis. Their
  process combines a changing golden dataset, deterministic rules, LLM judges,
  human review, CI/CD, shadow deployment, occasional A/B testing, and a final
  human call.

Neither interview alone proves willingness to buy a separate release-control
product. Together they justify testing whether production-derived evidence can
enter a recurring Release Review without replacing the customer's eval stack.

Use the [discovery ask guide](../internal/DISCOVERY_ASK_GUIDE.md) for the
artifact-first interview and quantitative capture sequence. Use the
[worked hiring-agent model-upgrade example](../internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md)
to test whether the proposed Release Review would have changed a real action.

## How OpenAI Deployment Simulation fits

[OpenAI Deployment Simulation](https://openai.com/index/deployment-simulation/)
replays production-like contexts against a candidate, estimates undesired
behavior, and later compares predictions with production observations. This
strongly supports production-derived replay and outcome calibration as useful
evidence methods.

It does not establish the entire Triana product. Deployment Simulation belongs
inside the Evidence stage; it does not by itself define the customer's complete
Release Change, obligations, required cross-stack evidence, human decision, or
retained release lineage.

If Triana only replays production traces and compares candidate rates, it is
too close to productizing Deployment Simulation plus an eval platform. The
frozen boundary therefore keeps production replay as one check mechanism and
refuses representative-coverage claims.

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
→ rollout and post-release evidence
→ production confirmation, refutation, and future protection
```

The long-term category is Release Control for AI agents: an independent
evidence and authorization boundary spanning review, human decision,
progressive exposure, post-release observation, and retained learning. V1
proves only the Release Review before deployment. It does not own deployment or
collapse into an automatic eval-maintenance loop.

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
- Show how the candidate was shadowed, canaried, staged, watched, paused, or
  rolled back, if any of those happened.
- Identify the approved production baseline.
- Attempt to turn one incident into a runnable case together.
- Count every manual edit, fixture, secret, mock, and missing observation.
- Run A/A before A/B.
- Present the Release Review and ask what action it changes.
- Ask whether they would retain it for the next three releases.
- Ask for payment only after the first real record.

Record disconfirming evidence with equal weight. Scope changes require repeated
evidence from eligible teams, not excitement during a demo.

The complete interview script, Braintrust-specific probes, and quantitative
capture sheet live in the
[discovery ask guide](../internal/DISCOVERY_ASK_GUIDE.md). Future expansion
gates live in
[Future Release Control considerations](../internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md).
