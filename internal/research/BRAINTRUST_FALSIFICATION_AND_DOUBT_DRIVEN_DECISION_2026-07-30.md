# Braintrust falsification and the doubt-driven decision after it

Date: 2026-07-30  
Status: research memo; **not** a product decision  
Audience: a reader with no prior Triana context  
Scope: what the Braintrust HRAI dogfood did and did not falsify, why the next
idea is still doubtful, and the smallest external test that should precede a
successor product decision

## Read this first

Triana began with a plausible claim: after an AI team runs evals, someone must
still decide whether a specific change should ship. That job can involve
identifying the exact candidate, deciding which known failures matter,
checking whether required evidence is complete and comparable, recording a
human decision, and later connecting the release to production outcomes.

The Braintrust experiment did **not** show that this job is imaginary. It
showed that, for the bounded HRAI model change we tested, Braintrust plus
ordinary CI handled nearly all of it. The residual release logic was real but
small enough that it currently looks more like internal glue than a standalone
product.

We then considered a different direction: use historical conversations to
preview how a baseline and candidate agent behave before release, manage a
controlled canary, and compare the pre-release expectation with what production
actually did. In plain language:

```text
Preview: What might break if we ship this candidate?
Guard:   How should we expose it safely?
Learn:   Were our pre-release expectations right?
```

This is promising enough to test, but not established enough to call the new
Triana. HRAI had already built much of the simulation machinery, Kairos-AI had
already described failure memory, and external products occupy adjacent or
overlapping territory. Our current confidence that **Deployment Preview alone
deserves an independent product is 35%**. That number is a judgment under
uncertainty, not a measured probability.

The right next action is not a large product build. It is a small open-source
artifact plus a bounded external test that can reveal whether the reusable
value is preview, rollout evidence, calibration, an integration layer, or
nothing.

## Evidence labels used in this memo

Every important statement below is labeled so that interpretation does not
silently become fact.

| Label | Meaning |
|---|---|
| **Observed fact** | Directly produced by the live Braintrust dogfood or found in repository artifacts |
| **External fact** | A current public product capability or firsthand report; useful but not directly reproduced here |
| **Inference** | The most economical explanation of observed facts; it can be wrong |
| **Hypothesis** | A claim that still needs a test |
| **Accepted decision** | Recorded in `internal/DECISION_LOG.md` and binding on the repository |
| **Proposed successor work** | A possible experiment or product shape that has not been accepted |

## 1. The original adversarial question

### Central hypothesis

After AI teams run evals, a consequential release-decision job remains:

1. identify the exact change;
2. determine which known production failures and requirements matter;
3. assemble sufficient evidence across systems;
4. expose missing, invalid, or non-comparable evidence;
5. make and record a release decision;
6. connect production outcomes back to future releases.

### Null hypothesis

Braintrust, LangSmith, CodeRabbit, PostHog, Sentry, GitHub Actions, deployment
controls, and ordinary scripts already solve this sufficiently. Any residue is:

- trivial or modest glue;
- an incumbent feature;
- an internal process choice;
- or too infrequent to support another independent product.

### Why the test had to be hostile

A release manifest can always be made to look important by adding concepts.
That does not make it a company. The investigation therefore treated the
following as anti-evidence:

- a few lines of YAML;
- a compact policy script;
- storing generic JSON in another database;
- recreating datasets or scorers already owned by an eval platform;
- moving approval out of GitHub without a demonstrated reason;
- calling manually maintained labels an automatically derived control plane.

## 2. What was actually tested in Braintrust

**Observed fact:** The live dogfood used synthetic, non-sensitive HRAI cases.
It did not deploy anything to production or modify HRAI production behavior.

The bounded release change was:

| Identity | Baseline | Candidate |
|---|---|---|
| Model | `qwen.qwen3-235b-a22b-2507-v1:0` | `qwen.qwen3-32b-v1:0` |
| Prompt | `candidate-screening-v2-reliability` | same |
| Dataset | 12 fixed HRAI cases | same |
| Trials | 3 per case in Braintrust | 3 per case in Braintrust |
| Declared change | approved baseline | model change |

The 12 cases covered normal work, known failure modes, release-critical
decisions, missing-data behavior, evidence-grounding edge cases, and a
prompt-injection case. Seven deterministic scorers checked completion,
required decisions, missing-data non-fabrication, an injection-refusal proxy,
tool efficiency, and composite task success. Model-graded scoring was tested
separately and preserved two failed configurations before a compatible
OpenRouter model returned structured scores.

### Experiments completed

**Observed fact:** The live sequence included:

- CLI authentication and direct OpenRouter model access;
- production-style traced model calls;
- a versioned 12-case Braintrust dataset;
- trace-to-dataset promotion with origin linkage;
- a persisted baseline experiment;
- an independent A/A comparison;
- a baseline-versus-candidate comparison;
- repeated trials;
- per-case and aggregate regressions;
- a missing-required-scorer test;
- a changed-dataset-version comparability test;
- a CI threshold/recommendation script;
- deterministic and model-graded scorers;
- online scoring, including a preserved failed scorer return shape;
- human/API feedback;
- three prompt revisions and loading an exact historical prompt version;
- a cross-stack release record containing Braintrust, GitHub, and Sentry-style
  references;
- storage and query of that record as normal Braintrust trace metadata.

### Release result

| Score | Baseline | A/A | Candidate | Candidate delta |
|---|---:|---:|---:|---:|
| Execution complete | 91.7% | 91.7% | 91.7% | 0.0 pp |
| Required decision | 83.3% | 66.7% | 58.3% | **-25.0 pp** |
| Missing-data non-fabrication | 91.7% | 100.0% | 91.7% | 0.0 pp |
| Injection-refusal proxy | 83.3% | 75.0% | 75.0% | -8.3 pp |
| Tool efficiency | 100.0% | 100.0% | 100.0% | 0.0 pp |
| Composite task success | 50.0% | 41.7% | 33.3% | **-16.7 pp** |

**Observed fact:** The smaller candidate was materially cheaper and faster in
the HRAI source artifacts, but materially worse at completing the
release-critical hiring decision.

**Observed fact:** Braintrust's three trials replayed fixed outputs, so they
showed no within-run variance. Independent HRAI runs of the same model and code
showed substantial A/A movement: approximately six decisions and seven
percentage points of stop-rate movement. A strict no-regression policy
therefore blocked both the candidate and an A/A control.

**Inference:** Running trials is commodity functionality. Choosing a defensible
variance policy remains customer-specific release work.

## 3. What Braintrust handled natively

The dogfood or current official capability inventory showed that Braintrust can
own or support:

- agent and model tracing;
- searchable production logs and BTQL queries;
- versioned datasets and exact transaction IDs;
- production-trace-to-dataset workflows;
- prompts and exact prompt revisions;
- deterministic and model-graded scorers;
- experiments, explicit baselines, per-case diffs, and aggregate comparisons;
- repeated trials;
- production scoring;
- human feedback and review primitives;
- experiment, code, model, prompt, release, and arbitrary metadata;
- cost, token, error, tool, and latency analysis;
- APIs, exports, and ordinary CI integration;
- generic storage of a cross-stack release record.

Some adjacent capabilities were plan-gated, UI-oriented, or inventoried but not
run in this CLI-focused test, including named dataset snapshots, sandboxes,
remote evals, some review-queue workflows, and environments/promotion.

**Observed fact:** These restrictions affect convenience and price. They do
not establish an independent Triana system-of-record need.

## 4. The exact limitations Braintrust exposed

The strongest observed gaps were:

1. **A required scorer could be omitted without a warning.**
2. **Experiments using different dataset versions could still be compared
   without Braintrust downgrading the comparison.**
3. **A naive no-regression policy could block a noisy A/A control.**
4. **Braintrust could store arbitrary requirement and release metadata, but it
   did not know which requirements were mandatory for this change or why.**
5. **The tested structured approval-metadata path was unreliable, although
   ordinary feedback worked and GitHub is already a natural approval
   authority.**
6. **A broad online-scoring rule scored an unrelated release-record trace,
   showing that production automation needs deliberate filters.**

These limitations are real. Their commercial meaning is the disputed part.

## 5. What the generic release layer cost

**Observed fact:** The HRAI-specific Braintrust adapter was 328 executable
lines. Most of that work existed because HRAI was not a Braintrust-native
application and its semantics had to become scorers.

The reusable release layer was:

| Artifact | Lines | Purpose |
|---|---:|---|
| `remote_ci_gate.py` | 130 | Required scores, thresholds, dataset comparability, and recommendation |
| `build_release_record.py` | 97 | Join Braintrust and external evidence and hash the record |
| `release_review_input.json` | 55 | Declare change, requirements, criticality, reasons, and external evidence |
| **Generic release layer subtotal** | **282** | Gate plus cross-stack record |
| `log_release_record.py` | 73 | Store the record back in Braintrust |

**Observed fact:** Braintrust accepted and returned the generic release record
as ordinary trace metadata.

**Inference:** Storage is not the wedge. A separate product cannot be defended
merely by placing the same experiment, GitHub, and Sentry URLs in another JSON
object or UI.

**Inference:** For a competent Braintrust-native team, the mechanical residue
is small enough to build internally. The difficult part is recurring semantic
maintenance: who declares applicable requirements, which evidence counts,
which differences invalidate comparison, and what later outcome should change
future protection.

**Hypothesis:** That semantic maintenance becomes painful enough, frequent
enough, and sufficiently standardized across companies to buy independently.
The Braintrust experiment did not prove this.

## 6. What the experiment falsified

The word “falsified” must be used narrowly.

### Strongly weakened

**Inference:** The experiment strongly weakens all of these standalone wedges:

- another experiment runner;
- another baseline/candidate comparison UI;
- another trace viewer;
- another dataset store;
- another scorer framework;
- another generic PR eval gate;
- another place to save release metadata;
- a release record whose only differentiation is combining links;
- approval duplicated from GitHub;
- a claim that Braintrust cannot connect production traces to regression data.

### Likely internal glue, on current evidence

**Inference:** A static release-evidence declaration plus completeness and
dataset-comparability checks looks like internal glue when:

- requirements are manually listed;
- applicability is manually selected;
- the gate is approximately 130 lines;
- the cross-stack record is approximately another 152 lines of code/config;
- GitHub already owns merge and approval;
- Braintrust can store and query the result.

This is the basis for the live report's **72% confidence in “likely internal
glue” for the frozen V1**. It is not a statistical confidence interval.

### Not falsified

The experiment did **not** establish:

- that requirements can be derived automatically from a real code, prompt,
  model, retrieval, or tool change;
- that teams routinely lose important evidence across systems;
- that missing or non-comparable evidence causes consequential escaped
  failures;
- that release records are retained and used across multiple releases;
- that production outcomes reliably update future obligations;
- that an external product can reconstruct these semantics without bespoke
  consulting;
- that a team will install or pay for such a layer;
- that realistic pre-release simulations predict production behavior;
- that Preview is more useful than a guarded canary;
- that any of this generalizes beyond HRAI.

**Observed fact:** No external customer used the workflow, changed a release
decision because of it, repeated it, or paid for it.

## 7. Why Deployment Preview was not a clean escape

After the generic release layer looked weak, a more concrete idea emerged:

> Use existing production conversations or traces to run a baseline and
> candidate agent before release, show behavioral, tool-use, cost, latency, and
> requirement differences, then connect those predictions to a canary and
> later production outcome.

That sounds new only if the prior HRAI and Kairos work is ignored.

### HRAI overlap

**Observed fact:** The HRAI historical-traffic experiment already created:

- 24 synthetic candidates and corresponding world state;
- 200 fixed production-like scenarios;
- user personas, hidden facts, goal tags, and turn budgets;
- a simulated user driven through DeepEval's conversation simulator;
- the actual HRAI agent, tools, and database;
- baseline, code-fix candidate, and model-change candidate identities;
- paired case IDs and run manifests;
- behavioral, tool, cost, latency, completion, and database-truth metrics;
- A/A/noise evidence;
- a normalized trace exporter and safe preflight.

It found that the smaller model was approximately 46% cheaper in the canonical
regenerated comparison but evaluated more candidates while committing fewer
decisions. It also found that a prompt/skill framing fix improved the
evaluation-to-decision stop rate beyond the observed single-run noise band.

**Inference:** “Generate realistic cases and compare baseline with candidate”
is not a new Triana invention. Triana Preview would initially productize an
experiment we already built.

### Kairos-AI overlap

**Observed fact:** The Kairos-AI Failure Memory thesis already described:

```text
GoalSpec
→ Trace
→ AttributionRecord
→ FailureMemory
→ RegressionEval
```

It proposed versioning the agent, prompt, model, tool contract, goal, eval, and
dataset, and explicitly asked:

> Before I ship this change, which regression evals should run?

**Inference:** Incident-to-regression memory and version comparison are also
not clean new wedges. A Preview/Learn product must avoid merely renaming the
same Kairos loop.

### External overlap

**External fact:** Braintrust, LangSmith, and Harness AI Evals cover most eval
lifecycle mechanics. Coval markets simulation and production evaluation.
LaunchDarkly AgentControl occupies configuration, progressive exposure,
guardrails, and rollback territory. OpenAI Deployment Simulation uses recent
production conversation prefixes, preregistered predictions, candidate
resampling, and post-release comparison. OpenAI Presence joins policy, sims,
graders, production sessions, suggested updates, approval, and controlled
rollout in an integrator-led enterprise product.

**Inference:** “Agent simulation” and “safe rollout” are not empty categories.
An open-source Preview can still be useful, but usefulness does not establish
venture-scale differentiation.

## 8. Doubt-driven attack on Preview

### Doubt 1: What exactly is being predicted?

A replay can establish:

> The candidate behaved differently from the baseline on these supplied
> situations under this execution contract.

It cannot automatically establish:

> Production incidence will move by this amount.

Historical conversation prefixes omit counterfactual user reactions. Frozen
tool outputs can become inconsistent with candidate actions. Generative users
and environments introduce model error. Rare failures may never appear in a
small sample.

**Hypothesis:** A pre-release preview can predict the direction of at least one
decision-relevant production metric better than the team's current eval
conclusion.

### Doubt 2: Is realistic simulation a product or services?

Open-ended, tool-using agents depend on customer-specific world state,
permissions, side effects, data, and tool contracts.

**Inference:** If every useful integration requires a custom world simulator,
the business initially behaves like forward-deployed engineering or a testing
service. That may be a valid company shape, but it contradicts a broad
self-serve infrastructure claim.

**Hypothesis:** At least two unrelated agents can be integrated in one
engineering day each with a stable trace/runtime adapter and without a custom
simulator rewrite.

### Doubt 3: Why not use a canary?

A canary observes real traffic and real environments. When failures are
recoverable and exposure controls exist, a 1% rollout with guardrails may be
more representative and cheaper than elaborate simulation.

**Hypothesis:** Preview changes a decision before any safe canary can answer
it, or it materially reduces the initial canary's blast radius, time, or
required exposure.

### Doubt 4: Does “calibration” matter to a buyer?

Prediction error is scientifically useful but not automatically valuable.
Teams buy fewer escaped failures, faster releases, lower blast radius, and less
manual investigation.

**Hypothesis:** Connecting Preview predictions to observed outcomes produces a
specific change to the next release test or rollout rule, rather than merely a
post-hoc report.

### Doubt 5: Is this just an incumbent feature?

All required primitives—traces, datasets, experiments, scoring, release IDs,
feature flags, production analytics, and error monitoring—already exist across
incumbents.

**Hypothesis:** The value comes from a reusable workflow and evidence contract
that references those artifacts in place, not from duplicating their data.

### Doubt 6: Does it generalize beyond HRAI?

HRAI is evidence of technical feasibility. Because we authored the agent,
simulation, scenarios, and analysis, it is weak evidence of self-serve
installation and market demand.

**Hypothesis:** An external team can provide enough existing conversations,
runtime access, and outcome data for a useful result without Triana engineers
already understanding its domain.

## 9. Evidence for and against the Preview direction

| Evidence | Type | Supports Preview | Attacks Preview |
|---|---|---|---|
| HRAI ran 200 paired, production-like scenarios through the real agent/tools/DB | Observed fact | Technical feasibility and reusable code exist | It was bespoke and built by the agent owner |
| HRAI exposed a cheaper model that behaved worse on the terminal decision | Observed fact | Pre-release comparisons can reveal decision-relevant tradeoffs | An ordinary eval report may be enough |
| HRAI measured large same-model variance | Observed fact | Honest preview needs paired trials and uncertainty | Prediction becomes expensive and harder to explain |
| Braintrust made experiments and evidence storage easy | Observed fact | Preview can integrate instead of rebuilding infrastructure | Experiment management is not a moat |
| Missing-scorer and dataset-drift gaps required only 130 CI lines | Observed fact | Evidence validity matters | The gap may be too small to monetize |
| Real production conversations can seed relevant cases | External fact/inference | Less synthetic authoring than a blank simulator | Past traffic may miss new tasks and changing distributions |
| OpenAI Deployment Simulation reports useful forecast accuracy at very large scale | External fact | The mechanism can work | OpenAI used resources and data most customers lack |
| OpenAI Presence is integrator-led | External fact/inference | There is enterprise demand for joined release workflows | Workflow-by-workflow engineering may dominate |
| LaunchDarkly owns progressive exposure primitives | External fact | Triana can integrate rather than route traffic | Guard risks becoming a thin wrapper |
| A canary supplies real outcome evidence | Inference | Preview can reduce initial exposure risk | Canary may make preview unnecessary |
| No external team has used or paid for Preview | Observed fact | — | Demand, repeat use, and distribution are unproven |

## 10. Why confidence is only 35%

The 35% refers narrowly to:

> The probability, based on current evidence and judgment, that a deployment
> preview product built from the HRAI machinery becomes a valuable independent
> wedge rather than a demo, services project, or incumbent feature.

### Reasons confidence is not lower

- HRAI proved the core mechanism can expose meaningful behavioral/cost
  tradeoffs.
- Production-derived contexts are more compelling than another manually
  curated eval suite.
- Tool-using agents make environment, side-effect, and terminal-action failures
  increasingly consequential.
- A useful open-source artifact can create concrete conversations even before
  the final company boundary is known.
- The Preview → Guard → Learn loop could compound if predicted and observed
  outcomes improve future release tests.

### Reasons confidence is not higher

- No external installation, repeated usage, or payment exists.
- HRAI was bespoke and already contained most of the proposed implementation.
- Simulation realism may demand forward-deployed engineering.
- Braintrust and other incumbents own the experiment substrate.
- OpenAI, Coval, Harness, and others occupy adjacent simulation/evaluation
  territory.
- LaunchDarkly and ordinary canaries may answer the release question more
  directly.
- Rare-event prediction may require far more traffic and spend than a small
  team can support.
- The phrase “predict production” is stronger than the current evidence allows.

## 11. The exact external blinded test

The test must separate a convincing demo from a decision-changing forecast.
It should use the existing HRAI-style machinery manually before a universal
platform is built.

### Sample

Recruit **three external teams**, each with:

- a conversational or tool-using agent;
- one completed historical release with a baseline and candidate;
- 200–500 redacted pre-release production conversation prefixes or comparable
  contexts;
- a safely executable historical environment, sandbox, or read-only tool
  contract;
- one predeclared behavioral or business outcome;
- the actual post-release result, withheld from the Triana operator until the
  forecast is frozen.

Three teams is not market proof. It is the smallest sample that can expose
whether one success was a special case.

### Procedure

For each team:

1. Freeze the exact baseline and candidate identities.
2. Freeze the input sample and record how it was selected.
3. Record the team's existing eval conclusion without changing it.
4. Run paired baseline/candidate trials using the safest available mode:
   frozen replay, read-only live replay, or generative simulation.
5. Record missing, invalid, and non-comparable evidence.
6. Before seeing production results, preregister:
   - predicted direction of the declared outcome;
   - a predicted magnitude or honest range where possible;
   - confidence;
   - expected failure classes;
   - whether Triana would expand, hold, narrow, or reject the release/canary;
   - exactly how this differs from the team's existing eval conclusion.
7. Freeze and timestamp the prediction artifact.
8. Reveal the actual post-release exposure and outcome.
9. Calculate directional correctness, magnitude error, missed outcomes, and
   false alarms.
10. Ask whether the Preview would have changed release timing, scope, rollout,
    monitoring, or rollback.
11. Ask the team to schedule and pay for a prospective second run.

### Budgets

- **Timebox:** 21 calendar days for all three teams.
- **Integration:** no more than 8 engineering hours per team.
- **Customer-specific code:** no more than 200 lines of adapter or fixture code
  per team.
- **Model/infrastructure spend:** no more than USD 500 per team without explicit
  authorization.
- **Data boundary:** customer-local or approved redacted data; no unrestricted
  production export.
- **Scope:** no production deployment and no mutation of customer systems.

### Pass rule

Continue toward a prospective Preview pilot only if **all** are true:

1. At least two of three teams fit within the integration, code, and spend
   limits.
2. At least two of three forecasts get the declared outcome's direction right.
3. At least one Preview exposes a consequential movement or evidence gap that
   the team's existing eval conclusion missed.
4. At least one team says the result would have changed release timing, scope,
   initial exposure, monitoring, or rollback preparation.
5. At least two teams request a second run on an upcoming release.
6. At least one team commits at least USD 1,000 to a prospective pilot.

### Kill or reposition rule

Stop calling Preview a self-serve product, or reposition it, if any of these
occur:

- two of three integrations exceed 8 hours or 200 customer-specific lines;
- safe execution requires a custom world simulator for two of three teams;
- Braintrust, LangSmith, or ordinary scripts reproduce the useful conclusion
  in one engineer afternoon;
- a normal canary is cheaper, safer, and more decisive for every team;
- Preview does not improve on any team's existing eval conclusion;
- forecast direction is wrong for two of three declared outcomes;
- no result changes a release or rollout action;
- fewer than two teams request a second run;
- no team will pay for the prospective run;
- teams cannot provide representative contexts or outcome denominators.

These are stopping rules, not goals to explain away after the fact.

## 12. Proposed open-source learning lineup

This lineup is a **proposed experiment**, not an accepted successor product.

### Triana Preview

Question:

> What changed when the candidate was run on situations derived from existing
> production conversations?

Initial outputs:

- paired baseline/candidate cases;
- task and requirement results;
- tool-call differences;
- cost and latency;
- repeated-trial variance;
- concrete behavioral regressions;
- missing or non-comparable evidence;
- an honest fidelity label.

The fidelity label should distinguish:

| Mode | Honest claim |
|---|---|
| Frozen replay | Candidate differed on these recorded situations and fixed observations |
| Safe live replay | Candidate differed in this sandbox/read-only environment |
| Generative simulation | Candidate behaved this way under a modeled user/environment |

None of these modes should silently claim production incidence.

### Triana Guard

Question:

> Given the declared risks and available telemetry, should exposure continue,
> pause, expand, or roll back?

Guard should consume existing feature flags and deployment controls. It should
not initially become another traffic router or LaunchDarkly.

### Triana Learn

Question:

> What did production do, how wrong was Preview, and what should change before
> the next release?

Learn should connect the frozen prediction to observed exposure and outcomes.
Its value exists only if the comparison changes a future case, evaluator,
threshold, monitor, or rollout rule.

### Why open source can be rational

**Inference:** A small open-source Preview can:

- turn existing HRAI work into an inspectable artifact;
- create a concrete object for outreach;
- reveal installation and simulation-authoring friction;
- establish whether users ask for Guard, Learn, hosted collaboration, adapters,
  or nothing;
- increase the rate of learning without first asserting a durable moat.

**Risk:** Stars, curiosity, and demo praise are not proof. The test signal is a
real external run, a decision changed, repeat use, and payment.

## 13. Frozen V1 versus the proposed successor

### Accepted decisions that remain binding

The repository decision log currently accepts and `docs/PRODUCT.md` freezes:

- a closed-source V1;
- one human-approved production incident as one Protected Case;
- bounded replay, not open-ended simulation;
- execution inside customer CI;
- explicit approved baseline and candidate;
- Triana assertions plus a customer-owned evaluator lane;
- a Release Review with an advisory recommendation;
- GitHub as the human decision authority;
- an immutable Release Evidence Record and separate Decision Attestation;
- no deployment, progressive exposure, pause, rollback, production-outcome
  calibration, or automatic applicability in V1.

### Conflict introduced by the proposal

The proposed lineup conflicts with the frozen boundary in at least four ways:

1. Preview introduces multi-case production-derived replay and possibly
   open-ended user/environment simulation.
2. Guard introduces rollout observation and recommendations beyond V1's stop
   at the human release decision.
3. Learn introduces production-outcome calibration explicitly deferred from
   V1.
4. Open-sourcing Preview conflicts with the accepted closed-source
   distribution decision.

**Accepted decision:** None of those changes is currently authorized.

**Proposed successor work:** An open-source Preview/Guard/Learn experiment may
be pursued only after Akarsh explicitly accepts a successor decision and the
canonical product, architecture, provenance, and decision documents are
updated together.

This memo records the proposal without changing the product.

## 14. Bottom line

### What we know

- Braintrust plus ordinary CI solved the bounded HRAI release workflow.
- The important completeness and comparability gaps were real but compact.
- Generic evaluation orchestration and release-record storage are weak
  standalone wedges.
- HRAI already built most of the proposed deployment-simulation mechanism.
- Kairos-AI already described failure memory and change-aware regression
  selection.

### What we infer

- Repackaging those mechanics without external evidence is unlikely to create
  a defensible company.
- A small open-source Preview may still be an excellent learning and
  distribution artifact.
- The strongest possible compounding loop is Preview → Guard → Learn, because
  it can connect pre-release expectations to real exposure and future tests.
- The largest risks are bespoke simulation work, incumbent absorption, and a
  canary being more useful than a preview.

### What remains a hypothesis

An external team will repeatedly value a customer-local preview that uses its
existing conversations, changes a release or rollout action, and improves when
connected to production outcomes.

### What is actually decided

The frozen closed-source Release Review V1 remains the repository's accepted
product. Preview, Guard, Learn, and an open-source distribution are proposed
successor experiments only.

### The next decisive act

Package only enough existing machinery to conduct the three-team blinded test.
Do not build a universal simulation factory first. Continue only if the test
produces an external run, a decision change, repeat demand, and payment within
the explicit limits above.

## Source and artifact index

### Canonical authority

- [`docs/PRODUCT.md`](../../docs/PRODUCT.md)
- [`docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`docs/CONTRACTS.md`](../../docs/CONTRACTS.md)
- [`internal/DECISION_LOG.md`](../DECISION_LOG.md)
- [`internal/WORKING_MEMORY.md`](../WORKING_MEMORY.md)

### Braintrust investigation

- [`TRIANA_BRAINTRUST_ADVERSARIAL_INVESTIGATION_2026-07-30.md`](TRIANA_BRAINTRUST_ADVERSARIAL_INVESTIGATION_2026-07-30.md)
- [`braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md`](braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md)
- [`braintrust_hrai_dogfood_2026-07-30/README.md`](braintrust_hrai_dogfood_2026-07-30/README.md)
- [`braintrust_hrai_dogfood_2026-07-30/remote_ci_gate.py`](braintrust_hrai_dogfood_2026-07-30/remote_ci_gate.py)
- [`braintrust_hrai_dogfood_2026-07-30/build_release_record.py`](braintrust_hrai_dogfood_2026-07-30/build_release_record.py)
- [`braintrust_hrai_dogfood_2026-07-30/release_review_input.json`](braintrust_hrai_dogfood_2026-07-30/release_review_input.json)
- [`braintrust_hrai_dogfood_2026-07-30/log_release_record.py`](braintrust_hrai_dogfood_2026-07-30/log_release_record.py)

### Prior simulation and failure-memory work

- `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/EXPERIMENT_PLAN.md`
- `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/CHANGE_HYPOTHESIS.md`
- `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/DIFF_REPORT.md`
- `/Users/akarshgajbhiye/kairos-ai/docs/kairos-failure-memory-thesis.md`

### Important external references already collected in the adversarial report

- [OpenAI Deployment Simulation](https://openai.com/index/deployment-simulation/)
- [OpenAI Presence](https://openai.com/index/introducing-openai-presence/)
- [Braintrust documentation](https://www.braintrust.dev/docs)
- [Braintrust changelog](https://www.braintrust.dev/docs/changelog)
- [LangSmith evaluation documentation](https://docs.langchain.com/langsmith/evaluation)
- [GitHub deployment environments and protection rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [LaunchDarkly AgentControl](https://launchdarkly.com/docs/home/agentcontrol)
- [Harness AI Evals](https://www.harness.io/products/ai-evals)
- [Coval](https://www.coval.ai/)
- [IBM, Measuring Agents in Production](https://research.ibm.com/publications/measuring-agents-in-production)
- [Anthropic, Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

