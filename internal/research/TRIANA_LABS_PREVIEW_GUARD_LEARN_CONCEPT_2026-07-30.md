# Triana Labs: Preview, Guard, and Learn

Date: 2026-07-30  
Status: proposed open-source successor experiment; not an accepted product
decision  
Authority: research only; `docs/PRODUCT.md` remains the frozen V1 authority

## Read this first

This document describes a possible way to get Triana into developers' hands
quickly:

```text
Preview a candidate on production-like situations
→ Guard its initial production exposure
→ Learn whether the preview was right
→ improve the next preview
```

The proposal is deliberately shallow at first. The goal is not to build a
universal simulator, another evaluation platform, or another feature-flag
system. The goal is to release small, useful artifacts, observe real usage,
and discover which part—if any—deserves to become a product.

This is **not** the current frozen V1. In particular:

- frozen V1 is closed-source;
- frozen V1 protects one bounded production-derived case;
- frozen V1 ends at a human Release Decision;
- representative simulation, canary control, post-release validation, and
  outcome calibration are explicitly outside frozen V1.

Open-sourcing Triana Labs or replacing the frozen V1 would require an explicit
successor decision and synchronized changes to the decision log and canonical
documents. Nothing in this research note makes that decision.

## Why this proposal exists

The live Braintrust dogfood materially weakened the original wedge. Braintrust
plus ordinary CI solved the bounded HRAI release workflow. Braintrust already
handled experiments, datasets, explicit baselines, repeated trials, per-case
comparison, traces, online scoring, human feedback, prompt versions, and
arbitrary metadata.

The remaining release semantics were real but compact:

- a 130-line CI gate caught omitted required scorers and dataset-version drift;
- a 97-line builder plus a 55-line declaration produced a cross-stack release
  record;
- an optional logging adapter stored that record in Braintrust; its current
  file is 89 physical lines, while the earlier live note recorded 73.

That evidence makes "another eval orchestrator" or "a prettier release record"
a poor independent wedge. See
[`braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md`](braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md).

At the same time, the HRAI historical-traffic experiment demonstrated a useful
workflow that was not merely an eval dashboard:

- create a frozen set of realistic scenarios and synthetic world state;
- run the unchanged baseline and a candidate on the same case identities;
- preserve model, code, prompt, environment, scenario, and run manifests;
- compare behavior, task outcomes, tool use, cost, latency, and execution
  failures;
- measure A/A noise before interpreting A/B movement.

That work found a consequential trade-off: the smaller model was about 46%
cheaper in the canonical regenerated run, but evaluated more candidates and
committed fewer decisions. It also found that identical-code baseline runs
moved by roughly six decisions and seven percentage points, making naive
regression rules untrustworthy.

HRAI therefore proves that we can build this machinery. It does **not** prove
that the machinery generalizes, that its scenarios represent production, or
that another team wants it.

## The simple product story

### Preview

> Before I release this candidate, what changes when it encounters situations
> like the ones my users already created?

Preview takes existing conversations or traces, an explicit baseline, and a
candidate. It runs comparable executions where possible and shows:

- task outcomes that changed;
- tool calls, arguments, order, and side effects that changed;
- cost and latency movement;
- repeated-trial variance;
- concrete improved and regressed examples;
- missing observations, failed runs, and non-comparable conditions;
- exactly what the report can and cannot claim.

Preview is the first artifact to ship because most of the proof machinery
already exists in the HRAI experiment.

### Guard

> Now that I am releasing it, how do I limit exposure and know whether to
> continue, hold, or roll back?

Guard consumes a customer-declared rollout plan and observations from the
customer's existing deployment system. It can recommend:

- continue to the next exposure step;
- hold for more evidence;
- stop expansion;
- ask the customer's deployment system to roll back, but only after the
  customer explicitly delegates that authority.

The first Guard must not be a traffic router. LaunchDarkly, cloud deployment
systems, Kubernetes, Argo, and custom feature flags already own traffic.
Triana should produce and monitor an evidence-bearing rollout plan through
adapters.

### Learn

> Did the pre-release preview predict what happened, and what should change
> before the next release?

Learn binds the exact Preview candidate to its Guard exposure and compares:

- predicted direction against observed direction;
- predicted rate or range against observed incidence;
- cases that were predictive;
- cases that were noisy;
- production outcomes that Preview never represented;
- missing or confounded outcome evidence.

Learn proposes new cases, revised thresholds, or changed evidence requirements.
A human approves any durable protection. It never silently invents ground
truth or rewrites the original pre-release artifact.

## The complete journey

```text
Existing traces or conversations
            ↓
        Triana Preview
baseline vs candidate under a declared fidelity mode
            ↓
Preview Report + machine-readable evidence
            ↓
        Human decision
            ↓
         Triana Guard
observe a customer-owned staged rollout
            ↓
Guard observations + exposure denominators
            ↓
         Triana Learn
predicted behavior vs observed outcome
            ↓
human-reviewed additions or changes for the next Preview
```

The product should remain useful if a customer runs only Preview. Guard and
Learn are follow-on experiments, not prerequisites for adoption.

## Proposed Preview CLI

The smallest credible workflow:

```bash
triana-labs preview init
```

This generates one readable configuration:

```yaml
release:
  id: hiring-agent-model-upgrade-2026-08-01
  baseline:
    command: ./run-agent --model qwen3-235b
    ref: git:abc123
  candidate:
    command: ./run-agent --model qwen3-32b
    ref: git:def456

contexts:
  source: traces.jsonl
  adapter: open-telemetry
  mode: frozen_replay

trials:
  count: 3
  seed: "20260801"

checks:
  command: ./existing-evaluators

output:
  directory: .triana/preview
```

Then:

```bash
triana-labs preview run triana-preview.yml
triana-labs preview inspect .triana/preview/report.json
triana-labs preview serve .triana/preview
```

The output directory should contain:

```text
manifest.json
attempts.jsonl
case-results.jsonl
comparison.json
gaps.json
report.html
```

The HTML report answers:

1. What baseline and candidate were actually executed?
2. Which contexts ran on both sides?
3. Which declared dimensions were fixed, changed, or unknown?
4. Which outcomes improved, regressed, or moved within measured noise?
5. Which tool trajectories changed?
6. What did execution cost?
7. Which evidence was missing or non-comparable?
8. What claim is supported at this fidelity level?

Preview should consume existing scorer outputs through a simple command or
JSONL contract. It should not require users to recreate Braintrust or
LangSmith datasets, rewrite scorers, or upload raw traces to Triana.

## Proposed Guard CLI

Guard should initially generate and observe a plan:

```bash
triana-labs guard plan \
  --preview .triana/preview/manifest.json \
  --steps 1,5,20,50,100 \
  --metric task_success \
  --hold-below 0.72 \
  --rollback-below 0.65
```

The generated plan declares:

- exact candidate identity;
- exposure steps;
- minimum observations and time window per step;
- metrics and denominators;
- continue, hold, and rollback rules;
- data source and expected observation delay;
- human owner and exception path;
- whether Triana is advisory or delegated.

An adapter then reads LaunchDarkly, a cloud deployment system, custom flags, or
an ordinary JSONL stream:

```bash
triana-labs guard observe \
  --plan .triana/guard/plan.yml \
  --source launchdarkly
```

The first release should stop at an advisory recommendation. Automatic traffic
changes are a later capability requiring demonstrated trust and explicit
customer delegation.

## Proposed Learn CLI

```bash
triana-labs learn compare \
  --preview .triana/preview \
  --guard .triana/guard \
  --output .triana/learn
```

Learn produces:

- a mapping from Preview measures to production measures;
- exposure counts and observation windows;
- directional accuracy;
- prediction intervals and observed values where statistically defensible;
- newly observed failure examples;
- confounders such as concurrent code, traffic, policy, or tool changes;
- proposed changes for human review;
- an explicit refusal when released identity or outcome attribution is weak.

The initial version need not claim sophisticated forecasting. A useful first
artifact can simply state:

> Preview predicted task success would decrease. The guarded rollout also
> observed a decrease. The size was not comparable because production used a
> different retrieval configuration.

## Three fidelity modes

Preview must name the mode prominently. These modes do not support equivalent
claims.

| Mode | What is replayed | What reacts to the candidate? | Useful claim | Important limit |
|---|---|---|---|---|
| **Frozen replay** | Recorded inputs and optionally recorded tool results | Candidate agent/model only | "The candidate behaved differently on these historical inputs under frozen evidence." | It cannot reveal a user or world reacting differently to the candidate |
| **Safe live replay** | Historical contexts against sandboxed, read-only, stubbed, or disposable tools | Candidate and bounded test environment | "The candidate behaved differently in this declared safe environment." | Fixture fidelity and state reset determine comparability |
| **Generative simulation** | Scenario truth plus a user/world simulator | Candidate, simulated user, and modeled environment | "The candidate behaved this way under this simulator and scenario distribution." | Simulator bias, environment fidelity, and distribution shift may dominate the result |

The report must refuse stronger language:

- Frozen replay is not a production forecast.
- A synthetic persona count is not a production incidence estimate.
- A safe live environment is not automatically production-equivalent.
- Generative simulation is not ground truth.
- Zero observed rare failures does not prove absence.

## What existing conversations provide

Existing conversations can provide:

- realistic starting contexts and vocabulary;
- common task and user-intent distributions;
- real tool-use and failure patterns;
- production cases that static benchmark authors did not imagine;
- prefixes on which a candidate can be resampled;
- anchors for evaluator and simulator calibration;
- evidence of which behaviors occurred under the old system.

They cannot provide by themselves:

- the correct response for a new candidate;
- a live world that reacts to different tool calls;
- counterfactual user turns after the candidate diverges;
- representative coverage of unseen users or new product affordances;
- reliable incidence for very rare failures without sufficient sample size;
- proof that tool state, retrieval, policy, and runtime stayed comparable;
- causal attribution when several release components changed;
- the production outcome of a release that has not happened.

The input should therefore be called a **context source**, not automatic
ground truth.

## Scoring and measurement

Preview should make measurement pluggable and boring. It can report:

- deterministic task completion;
- business-state transition;
- tool selected, arguments, ordering, retries, loops, and duplicate actions;
- policy or safety assertion results;
- evaluator scores supplied by Braintrust, LangSmith, or customer code;
- human labels;
- latency, tokens, model cost, and tool cost;
- execution completion, timeout, refusal, and harness failure;
- per-case paired movement and aggregate movement;
- A/A variance and repeated-trial spread.

The customer decides which behavioral or business outcome matters. Triana
owns identity, pairing, denominators, gaps, comparability, and honest claim
strength. An LLM judge may supply a score, but it does not own those facts.

Learn can later compare a pre-release measure with a production measure only
when their definitions, windows, populations, and identities are compatible.
Otherwise it records a relationship without pretending they are the same
metric.

## Reuse: what is actually available

### HRAI historical-traffic experiment

Useful reference mechanics exist under:

`/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/`

Potentially reusable ideas include:

- frozen scenario manifests and attempt preservation;
- scenario truth separated from generated user wording;
- safe state isolation and reset policies;
- paired case identities;
- execution-gap attribution;
- trace normalization;
- run manifests and cost ledgers;
- output-side diversity checks;
- baseline/candidate diff reports;
- A/A noise measurement.

Relevant implementation references include `runner/gen_scenarios.py`,
`runner/gen_scenarios_ext.py`, `runner/bedrock_sim.py`,
`runner/seed_candidate_world.py`, `runner/hr_bridge.py`,
`runner/otel_normalizer.py`, and `runner/run_preflight.py`.

However, HRAI is **not currently listed as a permitted source-mining
repository in `AGENTS.md`**. This document does not authorize copying it.
Before reuse, Akarsh must explicitly authorize the source; the exact source
file and commit must be inspected; ownership, license, and possible Agentagon
ancestry must be checked; and the reuse must be recorded in
`docs/PROVENANCE.md`. Until then it is evidence and design reference only.

### Kairos and Kairos-AI

Kairos and Kairos-AI are permitted source-mining repositories subject to the
provenance ledger. Potentially reusable concepts include:

- versioned goal and failure identities;
- trace normalization and deterministic evidence;
- first-broken-link attribution;
- failure recurrence;
- failure-to-regression-case proposals;
- deterministic fixtures, seeded runs, repeatability, and tamper checks.

Do not import the Kairos "Failure Memory" ontology wholesale. Preview should
not require customers to maintain a second behavior or failure ontology. Any
code reuse still requires the exact source path and commit, license and
authorship checks, a no-Agentagon-derivation check, a destination entry in
`docs/PROVENANCE.md`, and Triana-specific acceptance tests.

### Existing Triana contracts

The current deterministic identity, evidence-gap, comparison, hashing, and
record concepts may eventually be useful. They belong to frozen V1, however.
Triana Labs must not silently change their semantics or make its experimental
artifacts appear owner-approved V1 records.

## Incumbent comparison

The market already contains most component capabilities. This is a reason to
ship narrowly and learn, not a reason to claim an invented category.

| Product | What it already covers | Direct overlap | Honest remaining experiment |
|---|---|---|---|
| [Braintrust](https://www.braintrust.dev/docs/evaluate) | Traces, datasets, experiments, scorers, baselines, trials, CI comparison, online scoring, feedback, prompts | Nearly all evaluation and comparison mechanics | Whether a local replay artifact spanning existing tools is simpler or reveals anything Braintrust-native workflows miss |
| [LangSmith](https://docs.langchain.com/langsmith/evaluation-concepts) | Offline regression/backtesting, production traces, online evaluation, datasets, experiment comparison, human and model evaluation | Preview evidence generation and production feedback | Same test as Braintrust; do not duplicate its datasets or evaluators |
| [Maxim](https://www.getmaxim.ai/docs/offline-evals/via-sdk/simulation) | Turn-by-turn agent simulation, local output functions, evaluators, test runs, CI paths | Generative simulation and agent evaluation | Whether production-context replay plus explicit fidelity/gap reporting is easier or meaningfully different |
| [Coval](https://www.coval.ai/) | Voice-agent simulation, production evaluation, human QA, continuous feedback | Preview, production observation, and learning loop for voice | Do not target voice simulation as an undifferentiated wedge |
| [AgentClash](https://www.agentclash.dev/platform/agent-regression-testing) | OTel trace/dataset import, baseline/candidate replay, correctness/cost/latency comparison, CI gates, failure promotion | Extremely close to Preview | Triana must win on installability, fidelity transparency, a better artifact, or the Guard/Learn connection—not on "trace replay" |
| [OpenAI Deployment Simulation](https://openai.com/index/deployment-simulation/) | Replays prior conversation prefixes with a candidate and checks predicted behavior against deployment | The central Preview and Learn idea | A local developer tool using the customer's own contexts and agent may be accessible where OpenAI's internal method is not |
| [OpenAI Presence](https://openai.com/index/introducing-openai-presence/) | Policies, simulations/evals, production signals, suggested updates, comparison, approval, controlled rollout | Broadly spans Preview, Guard, and Learn | Presence is limited-GA and FDE/integrator-led, not self-serve; the open-source experiment tests whether a local path matters |
| [LaunchDarkly AgentControl](https://launchdarkly.com/platform/agent-control/) | Versioned agent configs, offline and online evals, progressive exposure, production metrics, guarded rollout, rollback | Guard and much of the full lifecycle | Triana should integrate with rollout infrastructure; replacing it is not a credible first move |

OpenAI's results also warn us not to oversell. Its published work identifies
simulation fidelity and prompt-distribution shift as major error sources,
reports that realistic tool simulation needed the original rollout,
repository, tool-call/response data, and read-only connectors, and says rare
failures still require adversarial and targeted evaluation. Triana Labs cannot
erase those limits with a CLI.

## The defense question

### Strongest answer

> Braintrust and LangSmith tell you how your candidate scored on an eval set.
> Triana Preview gives you a local, release-shaped replay of your candidate on
> contexts drawn from actual usage, while making the replay fidelity,
> identities, variance, and missing evidence explicit. Guard then connects
> that pre-release evidence to a staged rollout in your existing deployment
> system, and Learn checks what the preview got right or missed.

### Immediate attack

1. Braintrust and LangSmith can already use production traces as datasets,
   compare candidates, run repeated trials, and score production.
2. AgentClash already describes production-trace import, baseline/candidate
   replay, CI gates, and failure promotion.
3. Maxim and Coval already sell simulation.
4. LaunchDarkly already joins offline evals, production metrics, progressive
   rollout, and rollback.
5. OpenAI has demonstrated the Preview-to-Learn idea directly.
6. A local HTML report is not a company.
7. If realistic world construction requires custom engineering for every
   workflow, this becomes a services business.
8. If teams prefer a 1% canary to simulation, Preview may be unnecessary.

### What would make the answer defensible

At least one of these must become true in real usage:

- installation plus first replay is materially faster than the incumbent path;
- Preview exposes a consequential behavior the team's current eval process
  missed;
- fidelity and non-comparability reporting prevents a false release claim;
- developers repeatedly use the local artifact without moving data or
  recreating evaluators;
- Guard makes a canary safer while keeping traffic authority in the incumbent;
- Learn changes the scenarios, checks, or rollout policy for a later release;
- the open-source adapters and evidence format become useful across incumbent
  stacks.

Until that happens, Triana Labs is a learning vehicle, not proven
differentiation.

## Open-source distribution strategy

The initial release should be framed as **Triana Labs Preview**, an
experimental developer tool:

- intended to be local-first and open-source after an explicit successor and
  license decision;
- one install command;
- one HRAI-derived public demonstration rebuilt with provenance-safe assets;
- JSONL and OTel input first;
- customer command for baseline and candidate;
- customer command for existing evaluators;
- static HTML and machine-readable artifacts;
- no hosted account required;
- no raw trace upload;
- every failed execution and discarded attempt preserved;
- a prominent fidelity badge on every report.

The repository README should say:

> Replay a proposed agent change against situations drawn from existing usage,
> compare it with an explicit baseline, and produce an honest report of what
> changed and what the replay cannot prove.

It should not say:

- "predict production" without calibrated evidence;
- "production digital twin";
- "complete release assurance";
- "replaces Braintrust, LangSmith, or LaunchDarkly";
- "representative" merely because contexts came from production;
- "safe to deploy" based only on a simulation score.

The public artifact is valuable even if shallow: it demonstrates technical
taste, creates something developers can try, and generates more specific
feedback than a category pitch. Stars and social reactions are not product
validation; completed external replays and repeated use are.

## Staged sequence

### Lab 1 — Preview: frozen replay

Ship:

- JSONL/OTel context import;
- explicit baseline/candidate commands and identities;
- paired trials;
- existing evaluator command;
- tool/cost/latency/task comparison;
- gaps and fidelity labels;
- static report.

Do not ship a user simulator yet.

### Lab 2 — Preview: safe live replay

Add only after external frozen-replay attempts reveal that recorded tool
results hide consequential divergence:

- declared sandbox/read-only/stub adapters;
- reset and contamination checks;
- state-before/state-after references;
- safe refusal when side effects cannot be bounded.

### Lab 3 — Preview: generative simulation

Add only for one narrow agent shape where a changing user/world is necessary:

- deterministic scenario truth;
- bounded simulator;
- hidden-fact controls;
- simulator retry and failure attribution;
- diversity and realism audits;
- separate simulator and agent cost/evidence.

### Lab 4 — Guard

Add one read-only rollout adapter and advisory plan after users ask to connect
Preview to an actual release. Prefer LaunchDarkly or a plain JSONL adapter.

### Lab 5 — Learn

Add prediction-versus-outcome comparison after at least two users retain
candidate identity and trustworthy exposure denominators. Do not build
forecasting infrastructure before this data exists.

## Adoption and learning metrics

Measure behavior, not attention:

| Metric | Why it matters |
|---|---|
| Time from install to first report | Tests self-serve usability |
| Customer-specific adapter lines | Reveals whether the tool is reusable or consulting |
| Percentage of contexts paired successfully | Tests execution and identity fit |
| Percentage of evidence marked missing/non-comparable | Tests whether the report is honest and whether inputs are adequate |
| A/A movement and trial spread | Prevents false A/B conclusions |
| Consequential findings missed by existing evals | Tests incremental value |
| Report opened or shared in a release discussion | Tests decision relevance |
| Second Preview by the same team | Stronger than stars or first-run curiosity |
| Request to connect a rollout | Tests demand for Guard |
| Preview identity successfully joined to production outcome | Tests feasibility of Learn |
| Later test/policy changed because of Learn | Tests the compounding loop |
| Willingness to pay for hosted history, collaboration, or recurring automation | Tests company potential |

Proposed first thresholds:

- median install-to-report under 60 minutes for eligible repositories;
- no more than 200 lines of customer-specific adapter code;
- at least 50% of external installers who finish setup complete one report;
- at least two of the first five external teams run a second Preview;
- at least one of five finds a consequential difference absent from its
  existing eval conclusion;
- at least one asks to connect a staged rollout or post-release outcome.

These numbers are experiment thresholds, not market facts.

## Kill and narrowing criteria

Stop or materially narrow Preview if, across the first five eligible external
attempts:

- fewer than two reach a report without Triana-authored integration work;
- median setup exceeds one engineering day;
- customer-specific simulation or fixture code routinely exceeds 200 lines;
- users must duplicate datasets or rewrite scorers;
- Braintrust, LangSmith, or AgentClash reproduces the useful result in an
  afternoon with less work;
- reports show no consequential information beyond existing eval output;
- no team performs a second run;
- users consistently choose a guarded canary and see no reason to preview;
- realistic replay requires production-only mutable state that cannot be made
  safe.

Do not build Guard if no Preview user asks to connect a real rollout.

Stop Guard if:

- teams already understand and trust their LaunchDarkly or deployment-system
  view;
- Triana cannot bind observations to exact candidate identity;
- observation delay makes recommendations misleading;
- no team follows a Guard recommendation.

Do not build Learn if exposure and outcome denominators cannot be retained.

Stop Learn if:

- pre-release and production metrics are usually incomparable;
- observed outcomes do not change later tests or release behavior;
- there are too few comparable releases for the history to compound;
- teams will not retain the release identity across systems.

## Explicit non-goals

Triana Labs initially does not:

- replace Braintrust or LangSmith;
- own datasets, scorers, prompts, or trace storage;
- become a generic observability dashboard;
- become a universal synthetic-data factory;
- reconstruct arbitrary enterprise worlds;
- promise representative production coverage;
- estimate rare catastrophic-event incidence from small samples;
- infer ground truth automatically;
- hide simulator, evaluator, or harness failures;
- create a second behavior ontology;
- own feature flags or traffic routing;
- automatically deploy or roll back;
- call PASS a human approval;
- upload customer code, credentials, fixtures, or raw traces by default;
- claim that a replay proves causality;
- mutate a pre-release record after observing production.

## The decision this document supports

The near-term proposal, if Akarsh accepts a successor experiment, is:

> Ship a small open-source Triana Labs Preview built around production-context
> replay, paired baseline/candidate evidence, fidelity labels, and an honest
> static report. Treat Guard and Learn as gated follow-on labs. Let completed
> external runs—not category arguments—decide which capability deserves more
> investment.

This is intentionally different from saying "Preview is the new Triana."

The learning logic is:

```text
If nobody can run Preview, fix or stop the integration shape.
If people run it but learn nothing, stop the product claim.
If realistic environments dominate, test one narrow adapter market.
If people repeatedly run Preview, deepen that workflow.
If they ask to connect release exposure, build Guard.
If they retain release outcomes and revise future tests, build Learn.
```

## Evidence used

Repository evidence:

- [`braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md`](braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md)
- [`../FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md`](../FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md)
- [`../BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md`](../BRAINTRUST_DIFFERENTIATION_MIND_MAP_2026-07-30.md)
- `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/EXPERIMENT_PLAN.md`
- `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/DIFF_REPORT.md`
- `/Users/akarshgajbhiye/kairos-ai/docs/kairos-failure-memory-thesis.md`

Current official/product sources checked on 2026-07-30:

- [Braintrust evaluation](https://www.braintrust.dev/docs/evaluate)
- [Braintrust experiment comparison](https://www.braintrust.dev/docs/evaluate/compare-experiments)
- [LangSmith evaluation concepts](https://docs.langchain.com/langsmith/evaluation-concepts)
- [Maxim simulation](https://www.getmaxim.ai/docs/offline-evals/via-sdk/simulation)
- [Coval](https://www.coval.ai/)
- [AgentClash regression testing](https://www.agentclash.dev/platform/agent-regression-testing)
- [OpenAI Deployment Simulation, 2026-06-16](https://openai.com/index/deployment-simulation/)
- [OpenAI Presence, 2026-07-22](https://openai.com/index/introducing-openai-presence/)
- [LaunchDarkly AgentControl](https://launchdarkly.com/platform/agent-control/)
