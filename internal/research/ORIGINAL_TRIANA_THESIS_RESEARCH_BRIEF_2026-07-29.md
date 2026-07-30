You are helping me rigorously investigate and sharpen the thesis for my startup, **Triana**.

## Founder and startup context

I am Akarsh, a solo technical founder. I have spent the last few years building production AI systems, agentic workflows, large-scale backend systems, and reliability infrastructure.

Triana’s current thesis is:

> AI teams have evaluation tools and deployment tools, but no strong change-aware control plane that connects evidence to release decisions, progressive exposure, rollback, and future release policy.

Triana is not meant to be another eval platform or observability dashboard.

The product direction I am exploring is a release-control system for AI agents and probabilistic systems.

The core user question is:

> “Can I safely release this specific change?”

The system may eventually:

* understand what changed across prompts, models, tools, retrieval, memory, orchestration, permissions, dependencies, and business policy;
* determine which behaviours and production segments may be affected;
* collect evidence from eval tools, production traces, monitoring systems, incidents, support tickets, business metrics, security tools, and human review;
* decide whether a release should be blocked, reviewed, shadowed, canaried, segment-restricted, supervised, rolled out gradually, or fully released;
* observe post-release outcomes;
* pause, roll back, or expand deployment;
* learn which evidence was predictive for future similar releases;
* preserve institutional release memory.

## The existential question

The most important objection is:

> Why is Triana not merely a feature inside Braintrust, LangSmith, Langfuse, Arize, Humanloop, or another eval/observability platform?

Do not answer this with superficial feature differentiation.

Braintrust and similar platforms can build features.

The actual question is whether there is a distinct product category, system boundary, workflow, buyer, and compounding asset.

We need to determine:

1. What is structurally missing in the current AI deployment ecosystem?
2. What can existing eval, observability, CI/CD, feature-flag, and deployment tools already solve?
3. What should application developers reasonably build themselves?
4. What should they not repeatedly rebuild?
5. What problem remains even if eval platforms become excellent?
6. What creates a durable company rather than a thin feature?
7. What evidence supports or falsifies the Triana thesis?

## Current working distinction

The working distinction is:

> Evaluation tools measure whether an AI change appears better. Triana would determine the safest way to expose that change to production, using evidence from across the stack, and learn whether the release decision was correct.

A sharper version:

> AI teams have testing tools and deployment tools, but no change-aware control plane connecting evidence to progressive exposure, rollback, and future release policy.

However, this is only a hypothesis. Do not protect it. Try to disprove it.

## Current proposed product boundary

Potential architecture:

```text
Evidence providers

Braintrust
LangSmith
Langfuse
Arize
Custom evals
Security tools
Datadog
Product analytics
Support systems
Incident systems
Human review

        ↓

Triana release-control plane

- change-impact analysis
- affected-behaviour mapping
- evidence-plan generation
- evidence aggregation
- uncertainty and coverage assessment
- release policy
- progressive exposure
- approval and override workflow
- rollback and pause conditions
- outcome ingestion
- release-memory calibration

        ↓

Deployment actions

- block
- manual review
- shadow
- internal-only
- canary
- customer segment restriction
- percentage rollout
- human-supervised rollout
- full release
- pause
- rollback
```

The critical strategic test is:

> If a customer already uses Braintrust, does Triana become more valuable or redundant?

If it becomes redundant, Triana is probably just a Braintrust feature.

If it becomes more valuable because it consumes Braintrust as one evidence source among many and controls deployment, the products may be complementary.

## Important prior research conclusions

The following claims emerged from earlier research, but they must now be verified from primary sources.

### 1. Static evals may not predict deployment behaviour

The working belief is that real production behaviour depends on:

* actual user distributions;
* long trajectories;
* tool state;
* permissions;
* external APIs;
* retrieved context;
* retry behaviour;
* conversation history;
* side effects;
* rare but high-severity cases.

Therefore:

```text
Static test suite != production distribution
```

The relevant unanswered product problem may be:

> Given a specific change, what production-relevant distribution should be replayed, simulated, or monitored?

Potential example:

```text
Change:
New refund-agent prompt

Potentially affected:
- high-value orders
- multilingual refund requests
- partial refunds
- conversations longer than 8 turns
- tool calls with irreversible side effects

Required evidence:
- replay relevant production traces
- simulate adversarial refund sequences
- verify tool-side effects
- inspect business-policy violations
- release initially to 5% of eligible traffic
```

An eval platform can run and score tests.

The possible missing layer is determining what must be tested for this particular change and how that evidence should govern rollout.

### 2. Evals are only one source of release evidence

The real release decision may depend on:

```text
Offline evals
+ production replay
+ business KPIs
+ latency
+ cost
+ human review
+ incidents
+ user complaints
+ security findings
+ affected customer segments
+ reversibility
= release decision
```

Existing eval platforms tend to organise around:

* datasets;
* scorers;
* experiments;
* traces;
* online monitoring.

The potentially distinct native object for Triana is:

```text
Release Candidate

- change set
- affected behaviours
- evidence requirements
- evidence received
- coverage
- uncertainty
- unresolved risks
- rollout constraints
- approvers
- decision
- deployment policy
- observed outcome
- rollback event
- future policy update
```

### 3. AI applications can change without application-code changes

Model providers can alter:

* model aliases;
* tool-use behaviour;
* reasoning behaviour;
* structured-output adherence;
* latency;
* token consumption;
* safety behaviour;
* context handling;
* endpoint availability;
* model defaults.

Therefore, a deployment may become riskier even when the application repository does not change.

Potential missing workflow:

```text
External provider change
        ↓
Affected agents and behaviours
        ↓
Relevant production traces
        ↓
Required revalidation
        ↓
Fallback, canary, pause, or migration policy
```

This resembles dependency-aware release impact analysis.

### 4. Pre-deployment and post-deployment systems are disconnected

Many tools support offline evaluation and production monitoring.

That alone is not the gap.

The potentially missing closed loop is:

```text
Pre-release prediction
        ↓
Deployment policy
        ↓
Limited exposure
        ↓
Observed outcome
        ↓
Prediction calibration
        ↓
Expand, pause, or roll back
        ↓
Future release requirements
```

The system should learn which release evidence was actually predictive.

### 5. Institutional release memory may be the compounding asset

The strongest potential moat is not storing eval results.

It is storing and learning:

> What evidence was considered sufficient for this class of change, who approved it, what deployment policy was used, what happened in production, what was missed, and what should be required next time?

Potential graph:

```text
Change
  ↓
Expected behaviour
  ↓
Evidence
  ↓
Decision
  ↓
Rollout
  ↓
Outcome
  ↓
Incident or success
  ↓
Updated future release policy
```

This could become organisation-specific release intelligence.

## Why developers may not want to build this themselves

Do not claim developers are incapable of building release gates. They can.

A developer can write:

```yaml
if eval_score < 0.85:
  fail_pipeline()
```

The build-versus-buy argument must instead be about repeated, cross-cutting, organisation-wide infrastructure.

Possible non-differentiated internal-platform work:

* change-to-risk mapping;
* production-trace selection;
* dataset and evidence provenance;
* evaluator-version tracking;
* prompt/model/tool lineage;
* rollout segmentation;
* canary orchestration;
* human approval;
* override tracking;
* rollback triggers;
* audit logs;
* incident-to-regression conversion;
* evidence-quality calibration;
* release-policy learning;
* integration across GitHub, CI, eval platforms, monitoring, support, and deployment systems.

The possible claim is:

> This is not impossible application logic. It is undifferentiated release-control-plane work whose value compounds through integrations and accumulated release history.

Verify whether this is true in practice.

## Major threat: Braintrust already covers much of the obvious wedge

Assume Braintrust already supports or can support:

* CI/CD evals;
* regression detection;
* datasets;
* experiments;
* online scoring;
* production traces;
* production-to-eval workflows;
* quality gates;
* baseline-versus-candidate comparisons;
* incident-to-test-case workflows;
* immutable experiment history.

Therefore, none of the following is independently sufficient differentiation:

* GitHub Action that blocks regressions;
* PASS / REVIEW / BLOCK output;
* production trace replay;
* baseline comparison;
* eval generation;
* eval maintenance;
* online scoring;
* regression memory limited to test cases;
* a release dashboard.

The research must identify where Braintrust’s natural product boundary stops, if it stops at all.

## Research objective

Conduct an exhaustive, primary-source-led investigation into whether the Triana thesis is real.

Prioritise official sources from:

### Model labs

* OpenAI
* Anthropic
* Google DeepMind / Gemini / Vertex AI
* DeepSeek
* Meta
* Microsoft
* AWS
* Cohere
* Mistral

### Eval and observability platforms

* Braintrust
* LangSmith
* Langfuse
* Arize Phoenix
* Humanloop
* Galileo
* Patronus
* Weights & Biases Weave
* HoneyHive
* Maxim
* Confident AI / DeepEval
* Promptfoo
* OpenAI Evals

### Deployment and release infrastructure

* LaunchDarkly
* Harness
* GitHub Actions
* GitLab
* Argo Rollouts
* Flagger
* Spinnaker
* Datadog
* Sentry
* PagerDuty
* Incident.io
* Unleash
* Statsig
* Split
* Cloud providers’ canary and progressive-delivery products

### Production AI companies and internal platforms

Look for engineering posts, talks, documentation, conference presentations, case studies, or open-source repositories from companies running real agents in production.

Examples:

* Anthropic
* OpenAI
* Google
* Microsoft
* Intercom
* Decagon
* Sierra
* Ada
* Cresta
* Harvey
* Glean
* Klarna
* Cursor
* Cognition
* Replit
* Notion
* Perplexity
* Ramp
* Stripe
* Block
* Uber
* Airbnb
* DoorDash
* Netflix
* Meta

## Research questions

Answer each rigorously.

### A. What does the current ecosystem already solve?

Create a capability matrix covering:

```text
Capability
Eval platform
Observability platform
Feature-flag platform
CI/CD platform
Deployment platform
Incident platform
Internal developer-built system
Potential Triana layer
```

Capabilities should include:

* offline eval execution;
* online eval execution;
* baseline comparison;
* production trace replay;
* simulation;
* synthetic data generation;
* judge evaluation;
* human review;
* trace storage;
* model monitoring;
* prompt versioning;
* model versioning;
* change detection;
* impact analysis;
* affected-segment identification;
* evidence planning;
* evidence aggregation;
* confidence or uncertainty estimation;
* risk classification;
* release approval;
* policy enforcement;
* canary rollout;
* shadow deployment;
* segment restriction;
* automatic pause;
* automatic rollback;
* release provenance;
* incident linking;
* incident-to-regression creation;
* audit trail;
* release-memory learning;
* calibration of whether pre-release evidence predicted production outcomes.

For each capability:

* identify current vendors;
* cite exact official documentation;
* explain how complete the capability is;
* state whether it is native, partial, integration-dependent, or absent.

### B. Is “release intelligence” already an established product category?

Search for terminology such as:

* AI release engineering;
* agent release engineering;
* LLM deployment safety;
* AI deployment control plane;
* AI change management;
* AI progressive delivery;
* model release governance;
* agent rollout;
* behavioural release diff;
* AI release gate;
* probabilistic software deployment;
* AI canary deployment;
* AI release risk;
* eval-driven deployment;
* deployment simulation;
* production replay;
* AI regression management;
* agent change-impact analysis.

Determine:

* whether the category already exists;
* whether it is emerging under another name;
* whether no buyer recognises it;
* whether it is currently split across multiple categories.

### C. Where do model labs admit that current eval methods are insufficient?

Find primary-source evidence on:

* static evals versus real deployments;
* long-horizon agent behaviour;
* distribution mismatch;
* evaluation contamination;
* judge unreliability;
* model drift;
* production monitoring;
* human escalation;
* adversarial evaluation;
* deployment simulation;
* incidents missed by offline evaluation;
* provider-side behavioural changes;
* system-card limitations;
* agent autonomy;
* side-effect risk;
* tool-use failures;
* context-dependent behaviour.

For every claim:

* give the exact source;
* include the publication date;
* quote only the minimum necessary text;
* explain the implication for Triana;
* distinguish explicit statements from our inference.

### D. What do sophisticated teams actually do before releasing agent changes?

Find concrete workflows used by real teams.

Investigate:

* what triggers re-evaluation;
* whether they replay production traces;
* how they select datasets;
* how they handle model upgrades;
* whether they use canaries;
* whether they segment users;
* whether they require human approval;
* how they define rollback conditions;
* whether production incidents feed back into evals;
* whether they track release decisions over time;
* where the final ship/no-ship decision happens;
* who owns the decision;
* whether the process lives in Slack, spreadsheets, dashboards, CI, internal tools, or meetings.

Look for evidence from:

* engineering blogs;
* conference talks;
* public architecture docs;
* job descriptions;
* open-source systems;
* customer case studies;
* podcasts;
* vendor documentation describing customer workflows.

### E. What is the exact unsolved workflow?

Produce at least five candidate formulations.

For each candidate:

1. define the user;
2. define the trigger;
3. define the current workflow;
4. define the pain;
5. define why existing tools fail;
6. define what Triana would do;
7. identify which incumbent could add it;
8. estimate whether it is a feature, product, or company;
9. identify the compounding asset;
10. specify falsification criteria.

Potential candidate workflows:

* model-provider upgrade impact analysis;
* prompt or tool change to affected-behaviour mapping;
* evidence-plan generation for a release;
* multi-source release approval;
* progressive exposure controlled by behavioural evidence;
* automatic pause and rollback based on agent-specific outcomes;
* release-decision history and policy calibration;
* customer-segment-specific agent rollout;
* incident-to-future-release-policy conversion;
* cross-model fallback validation;
* third-party-agent dependency changes;
* human-supervised rollout for high-risk tool actions.

### F. Why would Braintrust not own this?

Analyse Braintrust specifically.

Map:

* product primitives;
* current positioning;
* buyer;
* workflow;
* integrations;
* data model;
* pricing;
* deployment features;
* roadmap signals;
* architectural incentives;
* organisational incentives.

Then answer:

* Which Triana features are trivial for Braintrust?
* Which are adjacent but plausible?
* Which would force Braintrust to become a deployment-control product?
* Would Braintrust benefit from owning the release decision?
* Would customers trust an eval vendor to control rollout?
* Is vendor neutrality meaningful?
* Does cross-platform evidence create a real wedge?
* Is there a conflict between being the scorer and being the release authority?
* Could Braintrust simply acquire or copy the category?
* Is Triana’s only defensibility execution speed and distribution?
* Does an organisation-specific release-memory graph create switching costs?
* Is that memory portable?
* Is it valuable before significant scale?

Do not manufacture differentiation. If Braintrust can naturally absorb the entire product, say so.

### G. Why would deployment incumbents not own this?

Analyse:

* LaunchDarkly;
* Harness;
* GitHub;
* GitLab;
* Argo;
* Statsig;
* Datadog;
* cloud providers.

Ask:

* Why would LaunchDarkly not add AI-specific release gates?
* Why would Harness not add agent eval integration?
* Why would GitHub Actions not become the orchestration layer?
* Why would Datadog not connect monitoring to rollback?
* Is Triana just an AI-specific configuration layer on top of progressive delivery?
* Is AI behaviour different enough to justify a separate control plane?
* Which abstraction belongs to Triana and which should remain delegated?

### H. Who is the buyer?

Determine whether the buyer is:

* AI engineer;
* staff AI engineer;
* AI platform lead;
* ML platform team;
* engineering manager;
* VP Engineering;
* safety or risk lead;
* product engineering;
* compliance;
* enterprise architecture;
* release engineering.

For each:

* pain intensity;
* authority;
* budget;
* current tools;
* urgency;
* maturity threshold;
* likely company stage;
* buying trigger;
* reason not to buy.

### I. At what maturity does the pain become real?

Determine whether the pain exists at:

* pre-product startups;
* seed companies;
* Series A;
* Series B/C;
* enterprises;
* regulated industries;
* high-volume consumer agents;
* customer-support agents;
* coding agents;
* financial agents;
* healthcare agents;
* internal automation agents.

Investigate whether early teams actually want:

* more eval tooling;
* a manual release report;
* a CI gate;
* a canary system;
* an internal release-review workflow;
* a managed service;
* a forward-deployed engineer;
* nothing until they have incidents.

### J. What is the minimum viable wedge?

Generate a ranked list of possible wedges.

For every wedge, score:

* pain;
* urgency;
* frequency;
* integration difficulty;
* buyer clarity;
* incumbent threat;
* time to value;
* ability to demo;
* ability to sell before building;
* data moat;
* expansion path.

Potential wedges:

1. GitHub Action producing release evidence.
2. Model-upgrade impact report.
3. Production-trace replay for affected behaviours.
4. Release candidate evidence packet.
5. AI-specific canary policy.
6. Automatic rollback based on behavioural metrics.
7. Incident-to-regression and release-policy memory.
8. Cross-eval-platform release approval.
9. Regulated-agent release audit trail.
10. High-risk tool-action release gate.

Reject weak wedges.

## Required outputs

### 1. Executive verdict

Provide one of:

* strong company;
* plausible but unproven;
* feature masquerading as a company;
* wrong abstraction;
* right problem, wrong buyer;
* right long-term category, weak current wedge.

Explain the verdict plainly.

### 2. Ecosystem map

Create a detailed map of:

* evaluation;
* observability;
* simulation;
* CI/CD;
* progressive delivery;
* model monitoring;
* incident response;
* release governance;
* internal tooling.

Show where workflows overlap and where the handoffs break.

### 3. Capability matrix

Produce the matrix described earlier.

No vague checkmarks. Use:

* native;
* partial;
* integration;
* absent;
* unclear.

### 4. Source dossier

Create a table:

```text
Source
Organisation
Date
Primary claim
Exact implication
Supports or weakens Triana
Confidence
URL
```

Primary sources should dominate.

### 5. Braintrust threat memo

Write a direct memo answering:

> “Why is Triana not a Braintrust feature?”

Include:

* strongest answer;
* weakest answer;
* what Braintrust already does;
* what Braintrust can build in six months;
* what Triana must own;
* what cannot be the wedge;
* kill criteria.

### 6. Developer-build memo

Answer:

> “What should developers build themselves, and what should they buy?”

Separate:

* simple scripts;
* company-specific business logic;
* generic infrastructure;
* control-plane functionality;
* organisation-specific policy;
* integration-heavy workflows.

### 7. Five product theses

Each thesis must be written as:

```text
User:
Trigger:
Current workaround:
Pain:
Product:
Why now:
Why incumbent cannot easily absorb it:
Compounding asset:
Initial wedge:
Expansion:
Kill test:
```

### 8. Customer interview plan

Create 20 highly diagnostic questions.

Do not ask:

* “Would you use this?”
* “Do you like this idea?”
* “Would release intelligence help?”

Ask about real recent behaviour:

* last risky agent release;
* evidence checked;
* people involved;
* tools opened;
* time spent;
* surprises;
* rollback;
* model upgrades;
* incident response;
* who made the final call;
* where the decision was recorded;
* what was rebuilt manually.

### 9. Kill criteria

Define explicit conditions under which I should stop pursuing this thesis.

Examples:

* teams already treat Braintrust as the release authority;
* no separate budget exists;
* release decisions are too infrequent;
* progressive delivery is not used for agents;
* teams prefer internal scripts;
* the workflow only matters at huge enterprises with long sales cycles;
* the buyer does not feel pain before building an internal platform;
* the necessary integrations make time-to-value too slow;
* the supposed release memory does not change future decisions.

### 10. Recommended next step

End with:

* the single best wedge;
* the single best customer profile;
* the single best demo;
* the single best outreach message;
* the three most important questions to validate next week;
* the exact evidence that would change your conclusion.

## Reading-list requirement

Every high-value primary source used in the analysis should be collected in a structured reading-list table with:

```text
Title
Organisation
Author
Publication date
URL
Category
Priority
Why it matters
Relevant Triana hypothesis
Supports / weakens / neutral
Key quote
Notes
```

Prioritise articles from:

* OpenAI;
* Anthropic;
* Google;
* DeepSeek;
* Braintrust;
* LaunchDarkly;
* Harness;
* Datadog;
* major production-agent teams.

The OpenAI material is especially important.

Look specifically for official OpenAI research or engineering work related to:

* deployment simulation;
* contextual evals;
* production incidents;
* adversarial evals;
* monitoring internal coding agents;
* agent misalignment;
* evaluation limitations;
* long-horizon behaviour;
* real-world deployment distributions;
* release safety.

## Research standards

* Use primary sources wherever possible.
* Prefer official documentation, research papers, engineering blogs, system cards, release notes, conference talks, and repositories.
* Use secondary sources only to discover primary sources or triangulate market behaviour.
* Cite every meaningful claim.
* Include dates.
* Distinguish facts, interpretation, and speculation.
* Do not use generic AI-industry prose.
* Do not protect my thesis.
* Search for evidence that invalidates it.
* Do not confuse a technically real problem with a viable company.
* Do not call something a moat merely because it stores data.
* Do not call integrations a moat without explaining why they compound.
* Do not call “release intelligence” a category unless buyers behave as if it is one.
* Do not assume regulated industries are automatically good customers.
* Do not assume enterprise complexity means willingness to buy.
* Do not treat feature breadth as product differentiation.
* Do not give me a list of features without defining the workflow and owner.
* Be direct.

## Final framing to test

The strongest current formulation is:

> Triana is a change-aware release-control system for AI agents. It maps changes to affected behaviours, determines required evidence, controls progressive exposure, and learns from production outcomes to improve future release policy.

The strongest objection is:

> This is an eval-platform feature combined with LaunchDarkly and internal scripts.

Your job is to determine which statement is more accurate.
