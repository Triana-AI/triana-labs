# Triana research conversation handoff

Date: 2026-07-30
Founder: Akarsh Gajbhiye
Purpose: preserve the complete strategic context needed to continue the Triana
thesis, Braintrust differentiation, customer discovery, positioning, and
fundraising discussion in the clean-room `~/triana` repository.

## Successor clarification — 2026-07-30

Akarsh subsequently accepted the following clarification of the frozen V1:

```text
Release Change
→ Release Obligation
→ required and received Evaluation Evidence
→ Release Recommendation
→ human Release Decision
```

The Protected Case is the V1 executable form of one human-approved obligation.
Production outcome, calibration, automatic applicability, and rollout remain
gated future Release Control work. Use `docs/PRODUCT.md`,
`docs/ARCHITECTURE.md`, `internal/DISCOVERY_ASK_GUIDE.md`, and
`internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md` for the
current definitions. The remaining material below preserves the research trail
and should not override that accepted clarification.

This is a synthesis, not a successor product decision. The frozen V1 in
`docs/PRODUCT.md` remains authoritative. Questions and proposed positioning in
this document require customer evidence before they can change that boundary.

## 1. How this investigation began

The original thesis was:

> AI teams have evaluation tools and deployment tools, but no strong
> change-aware control plane connecting evidence to release decisions,
> progressive exposure, rollback, and future release policy.

The existential question was deliberately stronger than feature comparison:

> Why is Triana not merely a feature inside Braintrust, LangSmith, Langfuse,
> Arize, Humanloop, LaunchDarkly, or another evaluation, observability, or
> deployment platform?

The requested research tried to disprove the thesis rather than protect it. The
original founder brief is preserved in
`research/ORIGINAL_TRIANA_THESIS_RESEARCH_BRIEF_2026-07-29.md`.

## 2. Research verdict

The primary-source investigation concluded:

> **Right long-term category, weak current wedge.**

The problem is real. The standalone-company claim is not yet established.

The strongest original whitespace statement is false. LaunchDarkly
AgentControl publicly connects agent configuration, offline evaluation,
thresholds, progressive exposure, online evaluation, experimentation, and
rollback. Braintrust publicly covers traces, datasets, scorers, experiments,
remote/custom agent execution, CI comparison, online scoring, and
production-to-dataset feedback. OpenAI Presence bundles policies, simulations,
evaluation, approval, managed deployment, and continuous improvement for
enterprise voice and chat agents.

The surviving strategic hypothesis is narrower:

> Teams may still lack a vendor-neutral way to turn a heterogeneous agent
> change or confirmed production failure into an explicit protected behavior,
> a justified evidence requirement, a release-specific decision record, and
> future organizational release memory across their existing stack.

That hypothesis is meaningful but unproven. It has no demonstrated standalone
budget, mandatory authority, or moat yet.

Canonical detailed source:

- `research/TRIANA_THESIS_INVESTIGATION_2026-07-29.md`

## 3. The four claims that must not be collapsed

| Claim | Current status |
|---|---|
| Agent changes create real release uncertainty | Strongly alive |
| Nobody connects evaluation and deployment | False |
| Incident-to-release protection may be a distinct workflow | Plausible, unproven |
| Cross-stack release memory can become a standalone system of record | Long-term hypothesis, unproven |

Incumbent activity is simultaneously positive and negative.

Positive:

- serious companies believe the problem matters;
- buyers already fund adjacent evaluation and delivery infrastructure;
- market education is happening;
- production-agent release frequency and consequence should grow.

Negative:

- generic evaluation execution and CI gates are commoditizing;
- progressive delivery belongs naturally to LaunchDarkly, Argo, Harness, and
  cloud platforms;
- an evidence dashboard plus PASS/BLOCK can be bundled;
- Triana must prove a recurring workflow and budget not naturally absorbed by
  the customer's current stack.

The conclusion is not "the market is dead." It is:

> The market is real, but the easiest version of the startup is vulnerable.

## 4. Frozen V1 and why it should not expand prematurely

The frozen V1 is intentionally one exact loop:

```text
confirmed production incident
→ human-approved protected case
→ qualification
→ explicit approved baseline and PR candidate
→ comparable execution inside customer CI
→ deterministic and customer-owned evidence
→ permanent Release Evidence Record
→ versioned Release Policy
→ advisory PASS / REVIEW / BLOCK recommendation
→ Release Review
→ append-only Decision Attestation for human approval / hold / exception
```

One incident protects one exact case. V1 does not claim:

- representative production coverage;
- behavior-family protection;
- automatic ground truth;
- broad change-impact inference;
- universal replay;
- autonomous evaluation-set maintenance;
- simulation or managed sandboxes;
- canary or rollback control;
- mandatory blocking.

This narrow build is a validation instrument. It tests whether a real incident
can become retained release protection, whether a Release Review changes a
real release action, and whether the workflow is additive to the customer's
current evaluation stack.

Vocabulary discipline from the successor canonical decision:

- production issue discovery is acquisition;
- the Protected Case is a production-derived evidence input;
- production replay is a checking mechanism;
- the Release Evidence Record is the immutable artifact;
- `PASS`, `REVIEW`, and `BLOCK` are advisory Release Recommendations;
- the Release Review is the recurring V1 product surface;
- the customer makes the human Release Decision, captured separately as a
  Decision Attestation;
- evaluation-set maintenance is a supporting feedback loop;
- rollout and post-release validation are future Release Control territory.

Do not expand the build merely because the long-term thesis needs a stronger
moat. The unproven change-impact and evidence-planning layer is semantically
hard and risks becoming services-heavy. Test it manually or as a concierge
workflow before automating it.

Canonical sources:

- `docs/PRODUCT.md`
- `research/TRIANA_SELF_SERVE_V1_SHIP_SPEC_2026-07-29.md`
- `research/TRIANA_WEDGE_V1_SPINE_2026-07-29.md`

## 5. The Braintrust question

People repeatedly ask Akarsh:

> "How are you different from Braintrust?"

The reason the answer feels difficult is that the honest answer cannot be a
simple feature checklist. Much of frozen V1 can be assembled using Braintrust,
GitHub Actions, and internal glue.

### Short answer

> Braintrust helps teams build and run evaluations. Triana turns a confirmed
> production failure into a Release Review for the next candidate, using
> Braintrust or whatever evaluation stack the team already has.

### Slightly deeper answer

> Braintrust primarily manages the evaluation lifecycle: traces, datasets,
> scorers, experiments, CI evaluation, and production scoring. Triana starts
> with something that failed in production and owns the path from that failure
> to a human-approved protection, an explicit baseline-versus-candidate release
> comparison, an evidence-backed Release Review, a linked human decision, and
> the eventual outcome. Braintrust can be an evidence source underneath
> Triana.

### Honest skeptical answer

If asked, "Couldn't Braintrust build this?", answer:

> Yes. Braintrust could compose many of these capabilities, and a team fully
> standardized on Braintrust may not need Triana. We are building for teams
> whose release evidence is spread across an evaluation platform, custom
> harnesses, GitHub, production traces, incidents, business metrics, and human
> approval. We are testing whether the lineage and decision workflow across
> those systems becomes an independent system of record.

This concession is important. It defines the initial customer rather than
pretending overlap does not exist.

### What each product primarily owns

| Braintrust | Triana hypothesis |
|---|---|
| Trace | Confirmed production incident |
| Dataset item | Approved protected case with source lineage |
| Scorer | Customer-owned definition of acceptable behavior |
| Experiment | Explicit release comparison under a pinned contract |
| Eval result | Evidence bound to a particular candidate release |
| CI report | Release Review joining evidence, gaps, policy, recommendation, and human authority |
| Production feedback | Outcome used to revise later protection |
| Project history | Vendor-neutral organizational regression history |

The central distinction is:

> Braintrust's primary object is the evaluation lifecycle. Triana's intended
> V1 object is the Release Review; its intended compounding object is the
> organization's learned release protection and history across releases.

This distinction becomes a company only if customers repeatedly use and pay
for it.

## 6. Evaluation fundamentals

### Offline evaluation

Offline evaluation runs selected cases before deployment.

It usually:

- uses a dataset or scenario set;
- runs a prompt, model, workflow, or agent configuration;
- applies deterministic, human, or model-based scorers;
- compares candidate configurations;
- detects regressions on the selected test distribution.

It answers:

> How did this candidate perform on these selected tests?

It does not automatically answer:

- why each check exists;
- whether these are the right checks for this particular change;
- whether the tested system identity exactly matches production;
- whether evidence is sufficient for exposure;
- who may accept an exception;
- whether the decision proved correct after release.

### Online evaluation

Online evaluation scores or reviews production traces.

It usually:

- monitors quality, safety, cost, latency, and business outcomes;
- detects failures and edge cases;
- segments production behavior;
- surfaces examples for human review;
- feeds useful traces into offline datasets.

It answers:

> What appears to be happening in production?

It does not automatically answer:

- which observation becomes permanent release protection;
- what exact fixture makes the incident replayable;
- how a confirmed incident applies to a pending release;
- whether baseline and candidate are comparable;
- which owner has authority over the trade-off;
- how an override or wrong prediction modifies future release policy.

### Evaluation versus release governance

An evaluation produces evidence.

A release workflow must decide:

- which evidence is relevant to this change;
- whether the evidence is sufficient;
- which gaps remain;
- who owns and approves the interpretation;
- what exposure is acceptable;
- whether a known failure returned;
- what was shipped or overridden;
- whether the prediction matched production;
- what the next similar release must do differently.

Triana is attempting to own this second workflow without rebuilding the first.

## 7. Why "feature versus company" matters

A useful feature can still be a bad independent company when:

- the existing vendor can bundle it into an existing contract;
- no distinct buyer or budget exists;
- customers can reproduce it with a small script;
- switching costs are low;
- onboarding requires services;
- the product is another dashboard rather than a control point.

A feature can support an independent company when it develops:

- a distinct recurring workflow and owner;
- cross-vendor neutrality;
- deep domain focus incumbents will not prioritize;
- accumulated history or organizational knowledge;
- mandatory use at a decision point;
- a system-of-record role;
- a credible expansion path.

The question is not whether Braintrust can technically add Triana-like
features. It can. The question is whether mature teams need a neutral release
ritual and record across systems badly enough to adopt, retain, mandate, and
pay for it separately.

## 8. Funding posture

The existence of incumbents is not a reason to stop considering Triana or to
avoid pre-seed fundraising.

Pre-seed capital can fund an unresolved product and market hypothesis. The
fundable framing is not:

> Give us money to discover whether anyone cares.

The stronger framing is:

> The market for production-agent reliability is clearly forming. Existing
> platforms commoditize evidence generation and traffic control. We have
> identified a specific unresolved workflow—incident-to-release protection and
> cross-stack release memory—and a falsifiable product for proving whether it
> becomes a separate system of record.

Recommended posture:

- do not abandon Triana;
- do not hide for months building the long-term platform;
- finish only enough frozen V1 for M0 and real M1 trials;
- conduct 15 qualified interviews and three instrumented trials;
- begin investor conversations quietly in parallel;
- launch a serious raise when real usage provides a stronger answer to the
  independence question.

Strong fundraising evidence:

- three qualified teams onboard in under two days each;
- at least two change an evidence plan, merge, or rollout;
- at least one asks to make the check mandatory;
- one customer pays while retaining its existing eval and delivery stack;
- release history changes a later evidence requirement or avoids a repeated
  miss;
- customer-specific services do not dominate.

Weak evidence:

- interest without a real release;
- value only in replay execution or a GitHub report;
- easy reproduction inside Braintrust or LangSmith;
- no changed decision;
- no repeated use;
- no independent owner or budget;
- bespoke semantic consulting for every customer.

## 9. Website positioning

The live site at `https://trytriana.com` currently presents a broader product:

- "Know what this release breaks";
- broad production-behavior discovery;
- an automatically maintained evaluation set;
- 18 approved checks;
- evaluator and business-metric integrations;
- versioned release-policy surfaces.

Those screens are a long-term product narrative but exceed the frozen V1.

Recommended current positioning:

> **Production failures should only happen once.**

Supporting line:

> Triana turns one confirmed agent failure into an approved CI protection for
> future releases, using the evals and harnesses your team already runs.

CTA:

> **Bring one failure and your next PR.**

This is a positioning correction, not a product pivot. The public site should
not imply representative discovery, broad eval maintenance, or automatic
release authority before the product proves them.

No website change has been executed as part of this handoff.

## 10. Customer discovery

When someone asks how Triana differs from Braintrust, answer briefly and then
turn the objection into evidence:

> Show me how you handle this in Braintrust today. Take the last important
> production failure: where was it recorded, did it become a permanent check,
> how was it selected for the next relevant release, and where does the
> approval and production-outcome history live?

Do not debate what Braintrust theoretically can do. Ask to see the actual
workflow.

### Core Mom Test sequence

1. Tell me about the last agent release whose decision was genuinely difficult.
2. What changed?
3. Which evidence did you assemble?
4. Who selected that evidence?
5. Which systems did that person inspect?
6. What remained unknown when the team shipped?
7. Tell me about the last important production failure.
8. Where is that lesson stored now?
9. Did it become a permanent regression case?
10. Who maintains it?
11. How is it selected for the next relevant release?
12. Has a known failure ever returned?
13. Could your existing Braintrust or LangSmith setup reproduce the complete
    workflow in under one week?
14. Would you attach one Triana-protected incident to the next real PR?
15. If the record changed the decision, would you retain it for the next three
    releases?

### Do not ask

- Would release intelligence be useful?
- Would you pay for this product?
- Do you want safer AI releases?
- Would a cross-platform control plane help?

Ask for artifacts, historical behavior, a real upcoming release, and a paid
trial after the first record.

## 11. Kill criteria

Stop the broad thesis if any two are true after 15 qualified interviews and
three instrumented trials:

1. Fewer than 5/15 describe a painful repeated decision between "evals ran" and
   "fully released."
2. Fewer than 3/15 spend at least one engineer-day per month coordinating
   release-specific evidence.
3. The same affordable full eval suite is sufficient for nearly every change.
4. Braintrust/LangSmith plus CI/LaunchDarkly reproduces the desired workflow in
   under one week.
5. No partner changes a release decision during a 30-day shadow period.
6. No partner asks for mandatory use after the system earns trust.
7. Onboarding the customer's harness takes more than two engineer-days.
8. More than half of implementation becomes customer-specific services.
9. Release memory does not change a later evidence plan or decision.
10. No distinct buyer, budget, or urgent champion exists.

The frozen wedge has an especially simple two-part M1 test:

1. Given one incident and the existing staging setup, can Triana produce a
   trusted Release Review on a real PR without changing the agent?
2. If it can, is the Release Review different enough from the incumbent stack
   that the team keeps it on every release?

Yes to the first and no to the second is the feature-not-company verdict.

## 12. Current mind map

The argument map is preserved separately in:

- `BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md`

Its reasoning ladder is:

```text
isn't this just evals?
→ understand offline and online evaluation
→ understand Braintrust's evaluation lifecycle
→ identify the release-governance questions left after evidence exists
→ define Triana's proposed Release Review and incident-to-protection input
→ admit the overlap and incumbent extension risk
→ test independent workflow, budget, mandatory use, and compounding history
```

## 13. Notion context

- Triana database:
  https://app.notion.com/p/b78c0713b2e54da68acfebe92733eab5
- Frozen V1:
  https://app.notion.com/p/3acf41c1f7d781868502d8fcddf08890
- Thesis investigation:
  https://app.notion.com/p/3acf41c1f7d781d892f9d476d1f4cc6f
- Wedge V1 open threads and Mom Test question bank:
  https://app.notion.com/p/3acf41c1f7d7816e840ddb28d023f4b1
- Thesis reset:
  https://app.notion.com/p/3a6f41c1f7d78195a2b5f4b075e37e69
- Engineering at AI Speed → Release Intelligence:
  https://app.notion.com/p/3a9f41c1f7d78124a17ed560fa812d91
- YC F26:
  https://app.notion.com/p/3aaf41c1f7d78017bee0c8610004870c

The detailed thesis dossier was added to the Triana Notion database on
2026-07-29. The source reading list was narrowed to 15 must-read entries; the
other 29 were moved to a recoverable Notion archive.

The Mom Test page still needs the latest Braintrust-independence and funding
questions added if the Notion connector becomes available in a future session.

## 14. Source files transferred

The following exact documentation-only sources were transferred under Akarsh's
explicit authorization. They are historical rationale and research, not
implementation authority:

1. `research/ORIGINAL_TRIANA_THESIS_RESEARCH_BRIEF_2026-07-29.md`
2. `research/RELEASE_CONTROL_PLANE_MARKET_RESEARCH_2026-07-29.md`
3. `research/TRIANA_THESIS_INVESTIGATION_2026-07-29.md`
4. `research/TRIANA_SELF_SERVE_V0_FROZEN_2026-07-29.md`
5. `research/TRIANA_SELF_SERVE_V1_SHIP_SPEC_2026-07-29.md`
6. `research/TRIANA_WEDGE_V1_SPINE_2026-07-29.md`
7. `research/TRIANA_DEMO_VIDEO_SCRIPT.md`

Clean-room rule:

- no Agentagon code;
- no tests or prompts;
- no schemas or fixtures;
- no UI, CSS, or generated reports;
- no configuration or infrastructure;
- no Git history.

If a transferred historical document conflicts with `docs/PRODUCT.md`,
`docs/PRODUCT.md` wins.

## 15. Continuation point

The next strategic work should deepen the Braintrust mind map rather than
generate another broad thesis.

Recommended order:

1. stress-test "Braintrust could extend into this";
2. map the exact workflow of a Braintrust-native team;
3. identify what changes when evidence comes from mixed systems;
4. define which object Triana uniquely persists;
5. connect each proposed differentiation to a customer artifact and question;
6. run the answer against three knowledgeable practitioners;
7. revise the public answer only from observed objections.

The unresolved company question is:

> Does the Release Review and its incident-to-decision lineage become an
> independent recurring workflow and system of record, or is it merely
> configuration inside the evaluation platform?

Do not resolve that question through further internal reasoning alone.
