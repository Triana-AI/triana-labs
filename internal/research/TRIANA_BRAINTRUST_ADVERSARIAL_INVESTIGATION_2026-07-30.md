# Should Triana exist independently?

Date: 2026-07-30  
Research posture: doubt-driven and adversarial  
Status: evidence report; no change to frozen V1 or canonical product documents

> **Live-account correction:** Braintrust credentials became available after
> the first draft. The account-tested Track A findings in
> [`braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md`](braintrust_hrai_dogfood_2026-07-30/LIVE_RESULTS.md)
> supersede this document's earlier statements that remote experiments,
> tracing, prompt versions, online scoring, feedback, and trace-to-dataset
> behavior were access-blocked. The external evidence collections and
> complaint taxonomy below remain part of the investigation. No product
> document or frozen V1 was changed.

## 1. Executive verdict

**Verdict: gap exists but current wedge is wrong.**

Confidence: **78%**.

The recurring job in the central hypothesis is real. The evidence does not show
that the frozen V1 is yet a product rather than a Braintrust/LangSmith feature
plus GitHub policy glue.

The three strongest reasons:

1. **Incumbents already solve almost all evaluation mechanics.** Braintrust
   natively covers traces, production logs, versioned datasets, production
   trace curation, deterministic and model-graded scorers, experiments,
   persistent baselines, repeated trials, custom comparison keys, online
   scoring, human review, CI comments, prompt/dataset environments, dashboards,
   alerts, APIs, export, and webhooks. Dropbox uses 150 pre-merge tests, a
   10,000+ post-merge suite, and online scoring; Box uses an 80% launch
   threshold and a 330-question golden dataset. These are not toy workflows.
2. **The residue is consequential, but teams usually implement it in existing
   control planes.** OpenAI's 2025 sycophancy release, Anthropic's 2025
   infrastructure regressions, Spotify's 42% experiment rollback rate, Uber's
   deployment-readiness score, and Schneider Electric's LangSmith-backed
   maturity gates all show that “the eval passed” is not the complete release
   decision. They also show the usual solution: GitHub, deployment controls,
   product experiments, observability, and internal policy—not a second eval
   ontology.
3. **The HRAI dogfood exposed policy work, not a clear independent system of
   record.** Braintrust's local SDK made a 12-case, 3-trial experiment easy.
   Seventy-eight lines of ordinary CI policy blocked the worse model. The same
   policy also blocked an A/A control because the model was nondeterministic and
   the baseline already violated absolute thresholds. That is a real release
   qualification problem, but the current evidence does not show customers
   will buy it separately instead of improving their test/policy code.

The strongest surviving product thesis is narrower than frozen V1:

> A read-only, cross-stack release-evidence manifest that references incumbent
> artifacts in place, validates identity/comparability/completeness, records
> explicit human exceptions, and later attaches production outcomes.

It fails as a product if it copies behaviors, datasets, scorers, traces, or
prompt/configuration versions into a second ontology.

## 2. Method and important constraints

### What was actually done

- Read Triana's canonical product, architecture, engineering, provenance,
  working-memory, decision-log, and slice documents.
- Located the independent HRAI repository at
  `/Users/akarshgajbhiye/Documents/hr_ai`; did not use Agentagon
  implementation or artifacts.
- Inspected HRAI's existing synthetic 200-case model-change runs.
- Installed Braintrust Python SDK `0.31.0` and autoevals `0.3.0` in a disposable
  Python 3.13 environment.
- Ran three Braintrust `no_send_logs=True` experiments:
  an A/A control, approved baseline, and model candidate.
- Ran seven deterministic scorers over a fixed 12-case dataset with three
  Braintrust trials per case.
- Wrote and executed a small fail-on-regression/absolute-threshold CI gate.
- Attempted a bounded model-graded scorer on four synthetic security cases.
- Attempted Braintrust app access in the available browser.
- Ran two independent external evidence collections, one optimized for the
  null hypothesis and one optimized for the central hypothesis.
- Separately collected Braintrust, LangSmith, and CodeRabbit complaint and
  workflow evidence.

### What could not be tested

- The available Braintrust browser session was not authenticated.
- HRAI had no `BRAINTRUST_API_KEY`.
- Braintrust account creation was not inferred as authorized.
- Therefore remote experiment storage, web UI comparisons, annotations,
  online scoring, alerts, webhooks, remote evals, sandboxes, dataset snapshots,
  environments, and trace-to-dataset UI/API behavior were not account-tested.
- The model-graded scorer reached the configured OpenRouter endpoint but
  received `401 User not found` for all four cases. Braintrust returned no
  scores. This is an evidence gap, not a zero.
- No production deployment or new HRAI agent run occurred. Existing synthetic
  HRAI outputs were replayed to avoid additional model spend and side effects.

These access constraints weaken claims about ease, not claims about capability.
Official documentation is used for account-gated feature existence.

## 3. Complete HRAI workflow report

### Release change

| Field | Approved baseline | Candidate |
|---|---|---|
| Agent model | `qwen.qwen3-235b-a22b-2507-v1:0` | `qwen.qwen3-32b-v1:0` |
| Agent/prompt | v0 agent; `candidate-screening-v2-reliability` | same |
| Temperature | `0` | `0` |
| Scenario universe | same 200 HRAI scenarios | same |
| Fixed dogfood subset | same 12 case IDs | same |
| Baseline source SHA-256 | `76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b` | — |
| Candidate source SHA-256 | — | `57a9d10412ad6ca13bb686b8628b42a7963dd09b3c5e9fd8c23db9b94681d7ca` |
| Dataset SHA-256 | `b92f119e604e7e5d2377ecb0910348a81f24e43ba61f015a80b7c412c6e00628` | same |
| Declared change | — | model and SQL-generator model changed to Qwen3-32B |
| Unresolved identity issue | baseline manifest identifies exporter commit `ca52bc8`, not a complete agent-code commit | candidate says agent files reverted to baseline commit `20c6de1` through base `69096f0`; this is better but still not a container digest |

The model-only causal claim is plausible but not perfect. Prompt, scenarios, and
flags match. The two manifests do not contain identical forms of complete
runtime identity, so the weakest accurate claim is “declared model change with
matched observed configuration,” not proof that no other environmental factor
changed.

### Dataset

The fixed set contains 12 cases:

- normal rubric work: `hr_0124`, `hr_0131`;
- evidence-grounded edge cases: `hr_0125`, `hr_0130`;
- release-critical decisions: `hr_0126`, `hr_0127`, `hr_0128`, `hr_0129`,
  `hr_0133`;
- prior-decision recall: `hr_0132`;
- missing-data refusal: `hr_0135`;
- prompt-injection resistance: `hr_0136`.

The criticality designation came from existing scenario tags such as
`commit_decision`, `injection`, and `missing_data`; the research harness did
not ask an LLM to invent it.

### Scorers

| Scorer | Authority | Meaning | Limitation |
|---|---|---|---|
| `execution_complete` | Deterministic | HRAI status is `COMPLETED` | Completion is not task success |
| `within_turn_budget` | Deterministic | User turns do not exceed case budget | Does not measure unnecessary assistant work |
| `required_decision` | Deterministic + human-authored tag | `commit_decision` cases produced a persisted decision | Only as good as the scenario tag |
| `missing_data_no_fabrication` | Deterministic + human-authored tag | Missing-data cases created neither evaluation nor decision | Conservative; a typed abstention record could be valid in another contract |
| `injection_refusal_proxy` | Deterministic proxy | Assistant transcript includes explicit refusal/untrusted-content markers | Keyword proxy can miss semantically correct refusals and reward boilerplate |
| `tool_efficiency` | Deterministic | Fewer than 20 recorded tool calls | HRAI's normalized trace may omit some span detail |
| `task_success` | Deterministic composite | All applicable checks pass | Conjunction is intentionally strict |
| `security_requirement_judge` | Model-graded attempt | Nuanced satisfaction of security expectations | Unavailable: endpoint authentication failed; no score |

### A/A and A/B result

Scores below are means over 12 cases. Braintrust executed three trials per
case, but every trial replayed the same frozen trace, so within-run variance was
zero by construction.

| Score | A/A older 235B run | Approved 235B baseline | 32B candidate | Candidate vs baseline |
|---|---:|---:|---:|---:|
| Execution complete | 91.7% | 91.7% | 91.7% | 0.0 pp |
| Required decision | 66.7% | 83.3% | 58.3% | **-25.0 pp** |
| Missing-data non-fabrication | 100.0% | 91.7% | 91.7% | 0.0 pp |
| Injection-refusal proxy | 75.0% | 83.3% | 75.0% | -8.3 pp |
| Tool efficiency | 91.7% | 100.0% | 100.0% | 0.0 pp |
| Composite task success | 41.7% | 50.0% | 33.3% | **-16.7 pp** |

Operational measurements over the unique 12 cases:

| Metric | Approved 235B baseline | 32B candidate | Change |
|---|---:|---:|---:|
| Mean latency | 17.43 s | 10.21 s | -41.4% |
| p95 nearest-rank latency | 35.83 s | 17.76 s | -50.4% |
| Recorded token total | 1,386,329 | 1,171,660 | -15.5% |
| Recorded cost | $0.3079 | $0.1525 | -50.5% |
| Recorded tool calls | 102 | 88 | -13.7% |

The candidate is materially cheaper and faster. It is also materially worse on
the release-critical behavior: completing a required hiring decision.

### Real trial variance

Braintrust's `trial_count=3` feature worked, but replaying a frozen output does
not measure live-model variance. HRAI's independent same-code/same-model
Qwen3-235B runs are the valid A/A signal:

- committed decisions: 23 versus 17;
- approximate eval-to-stop movement: seven percentage points;
- on this 12-case subset, required-decision score moved from 66.7% to 83.3%;
- one missing-data case moved from safe abstention to a fabricated zero-score
  evaluation.

This is large enough that a single-run “no regression” gate is not trustworthy.
Paired repeated live trials or a tolerance/statistical policy is required.

### CI workflow and result

The gate requires:

- no drop in execution completion, required decision, missing-data safety,
  injection refusal, or composite task success;
- absolute minimums for the same checks;
- missing scores become `MISSING`, never pass.

Result:

- **A/B: BLOCK.** The 32B candidate regressed required decision by 25 pp and
  composite task success by 16.7 pp.
- **A/A: BLOCK.** The same model's independent run regressed the missing-data
  check by 8.3 pp, while unchanged absolute failures remained below policy.

The A/A block is not a harness error. It shows that the naive gate is too
brittle for a nondeterministic agent and that “fail on any movement” needs a
trial-aware policy. Braintrust made the evidence easy to generate; it did not
choose the valid release policy.

### Production-style monitoring and trace-to-dataset loop

| Step | Result |
|---|---|
| Production-like traces | HRAI traces contain turns, tool sequence, sub-agents, timestamps, tokens, cost, decision DB truth, model, prompt version, and session IDs |
| Braintrust production logging | Not account-tested; official docs say logs and experiments share the same trace structure |
| Online scoring | Not account-tested; official docs support filtered/sampled trace- or span-scoped asynchronous scoring |
| Trace-to-dataset | Local transformation from a frozen HRAI trace/scenario to `EvalCase` worked; Braintrust-native UI/API promotion was access-blocked |
| Human annotation | Account-blocked; official docs support review queues, assignments, comments, corrections, tags, expected values, and production feedback |
| Feedback cycle | Demonstrated conceptually by selecting known HRAI failures; not completed in Braintrust because no account/API key |

### Exact manual steps

One-time:

1. Select and document the approved baseline.
2. Select 12 cases and mark which are release-critical.
3. Translate scenario requirements into deterministic scorers.
4. Normalize HRAI traces into Braintrust eval inputs/outputs.
5. Define a threshold policy in CI.
6. Install and pin the SDK.

Per release:

1. Declare candidate identity and verify observable fields.
2. Run baseline/candidate trials.
3. Inspect case-level regressions and scorer gaps.
4. Decide whether A/A noise invalidates the comparison.
5. Review failed required cases.
6. Approve, hold, or accept an exception in GitHub.
7. Carry the release ID into Sentry/PostHog/production tracing.
8. Review later outcomes and manually decide whether to change a requirement or
   dataset.

Braintrust removes much of steps 2–3 when fully configured. It does not remove
the semantic decisions in steps 1, 4–8.

### Exact custom glue

| Artifact | Lines | Why it exists |
|---|---:|---|
| Offline HRAI → Braintrust adapter and seven scorers | 375 | HRAI was not Braintrust-instrumented and its requirements needed executable checks |
| CI policy | 78 | Convert scores/gaps into PASS/REVIEW/BLOCK-like process exit |
| Model-graded scorer attempt | 126 | Test a nuanced security scorer through an OpenAI-compatible endpoint |
| Reproduction guide | 82 | Commands, identities, caveats |

Total executable research code: **579 lines**. The relevant release-policy
glue is 78 lines; much of the 375-line adapter disappears for a
Braintrust-native application. Conversely, the experiment did not implement
GitHub approval, external evidence ingestion, immutable cross-stack lineage, or
production-outcome calibration. Counting this harness as proof of a company
would be artificial.

### Reproducible artifacts

- [Dogfood README](braintrust_hrai_dogfood_2026-07-30/README.md)
- [Baseline result](braintrust_hrai_dogfood_2026-07-30/artifacts/baseline.json)
- [Candidate result](braintrust_hrai_dogfood_2026-07-30/artifacts/candidate.json)
- [A/A result](braintrust_hrai_dogfood_2026-07-30/artifacts/aa_control.json)
- [A/B CI gate](braintrust_hrai_dogfood_2026-07-30/artifacts/ci_gate.json)
- [A/A CI gate](braintrust_hrai_dogfood_2026-07-30/artifacts/aa_gate.json)
- [Failed model-judge evidence](braintrust_hrai_dogfood_2026-07-30/artifacts/baseline_model_judge.json)

## 4. Braintrust capability matrix

Classification:

- A: native and easy;
- B: native but operationally difficult;
- C: possible through normal Braintrust configuration;
- D: small ordinary CI glue;
- E: substantial custom product logic;
- F: not supported;
- G: not actually needed.

| Capability | Official claim | Actual HRAI result | Setup/manual burden | Limitation / restriction | Triana relevance | Class |
|---|---|---|---|---|---|---|
| Tracing and agent instrumentation | SDK/OTel integrations capture nested spans and use the same structure in logs and experiments | Braintrust eval task/scorer spans executed locally; HRAI production tracing itself was not re-instrumented | Low for supported SDKs; moderate for custom LangGraph trace mapping | Account required for persisted trace UI | Commodity evidence source | A/C |
| Production logs and filtering | Searchable traces, metadata filters, SQL/BTQL, full-text search, API | Not account-tested | Low after instrumentation | Discoverability and schema quality matter | Undermines a trace-view wedge | A |
| Datasets and versioning | Every insert/update/delete versioned; versions can be pinned | Local fixed `EvalCase` dataset worked | Low in native app | Named snapshots are Pro/Enterprise | Undermines dataset ownership wedge | A |
| Dataset snapshots/environments | Named snapshots; pin/promote dataset versions across dev/staging/prod | Not account-tested | Low–medium | Pro/Enterprise | Direct incumbent encroachment on approved-version semantics | C |
| Production trace → dataset | UI/API mapping retains trace origin and annotations | Local trace-to-case transform worked; native action blocked | Some human curation | Ground truth still human | Acquisition path is incumbent feature | A/C |
| Playgrounds | No-code side-by-side prompt/model/scorer/dataset iteration | Access-blocked | Low for prompts; higher for full agents | Account/UI; remote code configuration for agents | Undermines experimentation wedge | A |
| Prompts and workflows | Versioned prompts and chained playground workflows | Not account-tested | Low | Python environment assignment needs UI/API | Prompt identity can be referenced, not copied | A/C |
| Deterministic scorers | Python/TS/HTTP/custom code scorers | Seven scorers ran successfully | 1–2 hours for this bounded suite after data understanding | Application-specific semantics still custom | Evaluation lane, not independent product | A |
| Model-graded scorers | Built-in/autoevals/custom prompt scorers | Attempted on four cases; endpoint auth failed; no scores | Low code, provider credential required | Cost, calibration, provider reliability | Gap must remain typed; no Triana-owned judge needed | C |
| Human annotation/feedback | Review queues, assignments, scores, comments, tags, corrections, expected values, production feedback | Access-blocked | Recurring human work | Starter only one human-review score/project; playground annotations Pro+ | Braintrust already owns review workflow | A/B |
| Experiments | Immutable comparable eval-run records | Local experiment execution worked; no remote immutable record | Low | `no_send_logs` intentionally creates no server experiment | Undermines evidence-record novelty | A |
| Explicit baselines | Persistent experiment/project baselines; automatic branch fallback if none set | Baseline identity passed as local metadata; native persisted baseline not tested | Low | Auto-selected same-branch baseline is not equivalent to human approval; explicit baseline exists | Triana cannot claim Braintrust lacks baselines | A/C |
| Candidate comparisons | Per-case/aggregate comparison, regression sorting, diffs | Scores generated; 78-line local script compared them | Low in UI; small glue for policy | Remote UI not tested | Basic comparison is commodity | A/D |
| Repeated trials/variance | Global or per-case trial count; groups identical inputs | Three trials/case executed and aggregated | One parameter | Frozen replay produced zero variance; live trials cost money | Trial mechanics are native; policy remains hard | A |
| Custom comparison key | SQL expression matches rows when inputs contain volatile fields | Docs verified only | One project setting | Misconfiguration can hide/mismatch rows | Undermines identity-matching wedge | C |
| Pairwise comparison | Pairwise human/model scoring supported in 2026 | Docs verified only | Moderate reviewer/judge work | Preference is not release authority | Evidence lane | C |
| Remote evals | Braintrust UI triggers customer-hosted agent code | Access-blocked | Moderate server/auth setup | Dataset controlled by playground; endpoint must remain available | Undermines customer-infra execution wedge | B |
| Sandboxes | Isolated Lambda/Modal execution artifacts controlled from playground | Access-blocked | Moderate | Beta; Pro/Enterprise; Lambda invocation 15-minute cap | Undermines managed-execution differentiation | B |
| CI/CD regression gates | `bt eval`, JSON output, `eval-action`, `fail_on_regression`, `min_score` | Local CI gate worked; official action not run | Small YAML + policy | Valid thresholds and A/A noise remain customer work | Core null-hypothesis evidence | A/D |
| GitHub integration | Eval action posts PR comparison comment | Not run | Small YAML | Comment/check is not necessarily approval or deployment | GitHub remains natural authority | D |
| Online scoring | Async trace/span scoring with sampling and SQL filters | Access-blocked | Moderate scorer/filter/cost setup | Missing scores can result from filters, sampling, span-end timing, or permissions | Strong incumbent production loop | B/C |
| Dashboards | Requests, latency, tokens, costs, scores, custom metrics/charts | Access-blocked | Low–medium | Custom charts Pro+ | Not a Triana wedge | A/C |
| Alerts | Spend alerts; environment Slack/webhook alerts; monitor workflows | Access-blocked | Low–medium | Environment alerts Pro+ | Incumbent can trigger release workflows | C |
| Prompt/config versioning | Content-addressed prompt versions; parameters; rollback | Docs verified | Low if Braintrust owns configuration | Code/tool/retrieval/runtime identity still external | Composite identity remains partial | A/C |
| Environments/promotion | Dev/staging/prod for prompts, datasets, parameters; webhooks | Access-blocked | Low–medium | Pro/Enterprise | Direct threat to release-control positioning | C |
| Experiment/production metadata | Arbitrary metadata/tags and git metadata | Model, prompt, hashes, labels, offline flag logged locally | Low | Metadata does not prove completeness | Useful substrate; Triana must validate, not duplicate | A/D |
| Cost/token/error/latency analysis | Native trace metrics, dashboards, experiment comparisons | HRAI values captured and compared in artifact | Low when instrumentation is correct | HRAI's fields came from its own exporter | Commodity | A |
| Topics | Automatically classify/cluster production logs | Docs verified | Low–medium plus model cost | Custom topics Pro+ | Weakens issue-discovery wedge | C |
| Loop | Agent analyzes logs, creates datasets/scorers/views, optimizes prompts | Access-blocked | Low interaction; human confirmation by default | LLM output remains proposal | Weakens maintenance/analysis wedge | C |
| APIs and export | REST/Data API, BTQL, JSON/Parquet, cloud export | Docs verified; no authenticated call | Low for normal export; enterprise automation higher | Export automation Enterprise | Cross-stack assembly is feasible | C/D |
| Webhooks | Environment-change webhooks/Slack; API-driven automations | Access-blocked | Small handler | No webhook for every prompt change; environment promotion events available | Ordinary glue can connect GitHub/Sentry/PostHog | D |
| Pricing/plan | Starter: $0, 1 GB, 10k scores, 14-day retention; Pro: $249/month; unlimited projects/datasets/playgrounds/experiments | No account created | Free dogfood would fit usage | Snapshots, environments, annotations, charts, sandboxes restricted as documented | A separate $500/month V1 faces a strong bundle | — |

Primary Braintrust sources:

- [Evaluate systematically](https://www.braintrust.dev/docs/evaluate)
- [Run evaluations](https://www.braintrust.dev/docs/evaluate/run-evaluations)
- [Compare experiments](https://www.braintrust.dev/docs/evaluate/compare-experiments)
- [Observe](https://www.braintrust.dev/docs/observe)
- [Datasets](https://www.braintrust.dev/docs/annotate/datasets)
- [Human review](https://www.braintrust.dev/docs/annotate/human-review)
- [Online scoring](https://www.braintrust.dev/docs/evaluate/score-online)
- [Remote evals and sandboxes](https://www.braintrust.dev/docs/evaluate/remote-evals)
- [Environments](https://www.braintrust.dev/docs/deploy/environments)
- [Loop](https://www.braintrust.dev/docs/loop)
- [API/export](https://www.braintrust.dev/docs/api-reference)
- [Plans and limits](https://www.braintrust.dev/docs/plans-and-limits)
- [Changelog](https://www.braintrust.dev/docs/changelog)

## 5. Complete release-question classification

| Release question | Best honest implementation | Class | Finding |
|---|---|---:|---|
| What exactly changed? | Git SHA/diff plus explicit model/prompt/tool/retrieval/runtime metadata | D | Braintrust can store it; Git owns the exact code change |
| Can baseline/candidate identities be reproduced? | Braintrust object versions + container/code/config hashes | D/E | Easy when standardized; proving completeness is custom |
| Which known failures are release-critical? | Dataset tags/metadata plus human policy | C | Native storage; semantic selection remains human |
| Why are they critical? | Dataset metadata, comment, linked incident/issue | C/D | Easy to record, not automatically true |
| Which checks are required for this change? | Human-maintained mapping or diff-aware policy | E | The hardest residue; CodeRabbit can propose, not prove |
| Which checks are optional? | Same policy object | E | Not an eval-platform primitive by itself |
| What evidence ran? | Braintrust experiment + GitHub checks | A/D | Native for Braintrust evidence |
| What failed? | Case-level scorer results and regression sorting | A | Native and easy |
| What was missing/invalid/non-comparable? | Braintrust errors plus CI validation of expected rows/identity/conditions | D/E | Braintrust exposes many errors; release sufficiency is custom |
| Does evidence authorize release? | GitHub required check/environment policy | D | Small glue if policy is simple |
| Who approved/held/accepted exception? | GitHub review/environment deployment record/comments | D | GitHub already owns this well |
| Where is the decision recorded? | GitHub PR/deployment plus linked experiment | D | A second approval UI is unnecessary |
| Can outside evidence participate? | Links/metadata/API query + GitHub checks | D/E | Easy for links/status; hard for typed semantic normalization |
| Can a production outcome tie to release? | Shared release/Git SHA in Sentry/PostHog/Braintrust | D | Small instrumentation/schema glue |
| Does outcome change a future requirement? | Human issue/dataset/policy update | E | No incumbent automatically creates trustworthy meaning |

No row is F. The null hypothesis is therefore technically viable. The open
question is recurring operational burden, not impossibility.

## 6. Braintrust replacement verdict

### Could a competent team solve the complete job with Braintrust and GitHub?

**Yes, for the frozen V1 job.** The team would need:

- explicit release metadata;
- dataset tags or a small policy file for critical cases;
- scorer/gap validation;
- a GitHub required check;
- GitHub reviews/environments for approval and exception;
- shared release IDs in production telemetry.

This is credible at tens to low hundreds of lines once the application is
already Braintrust-native. HRAI required more because it was not.

### Glue and recurring work

- Minimal observed release-policy glue: **78 Python lines**.
- HRAI-specific normalization/scorers: **375 lines**.
- Expected Braintrust-native GitHub YAML/metadata glue: roughly **20–80 lines**.
- Cross-Sentry/PostHog link propagation: usually **a few metadata fields and API
  calls**, not a company.
- Recurring manual steps: **six to eight**, dominated by criticality,
  applicability, A/A interpretation, exception approval, and outcome-driven
  requirement maintenance.

### How much time does Braintrust save?

The local SDK ran 36 replay rows per variant in under a second because model
outputs were frozen; this does not measure real eval runtime. More persuasive
external outcomes are:

- Dropbox: 150 pre-merge tests, 10,000+ post-merge tests, real-time online
  regression detection.
- Box: replaced manual spreadsheet testing with nightly runs and made failure
  clusters legible.
- Wordsmith/LangSmith: compared Claude 3.5 with GPT-4o within an hour and
  released the same day.

Braintrust saves the majority of experiment storage, comparison, review, and
production-feedback plumbing. It does not save the organization from deciding
what matters.

### What remains painful enough to buy separately?

Not yet proven:

- change-specific required-evidence selection across many systems;
- typed proof that expected evidence was absent rather than silently skipped;
- composite identity completeness;
- explicit cross-system exception semantics;
- pre-release prediction versus post-release outcome calibration;
- retained lineage across tools after vendors/configuration change.

These are painful at frontier and large-enterprise scale. Public evidence that
three ordinary Braintrust-native conversational-agent teams will pay for them
separately is absent.

### Would a Braintrust-native customer rationally install Triana?

Not the frozen V1 as currently described. Box, Dropbox, and a competent
Braintrust/GitHub team can reproduce its one-case advisory review without
moving data. They might install a thin read-only evidence manifest if it:

- requires no duplicated case, dataset, scorer, prompt, or trace;
- configures from existing Braintrust/GitHub metadata;
- exposes a missing/non-comparable fact Braintrust/GitHub currently hides;
- materially changes an actual release action;
- later joins production outcomes without becoming another dashboard.

## 7. Ten strongest pieces of evidence for redundancy

### 1. Dropbox's Braintrust pipeline

- Source/date/version: [Braintrust customer report](https://www.braintrust.dev/customers/dropbox),
  live 2026-07-30; current platform.
- Provenance: attributed firsthand workflow, vendor-edited.
- Workflow/outcome: 150 tests block pre-merge regressions; 10,000+ run after
  merge; the same rubrics score sampled production traffic; feedback traces
  become new tests.
- Frequency/severity: every PR/merge plus real-time production.
- Workaround/complexity: specialized graders and a custom pipeline, but no
  separate release-control product.
- Fixed/incumbent status: current success.
- Supports/weaken: strongly supports null; weakens missing production loop and
  eval-gate claims.
- Confidence: 4/5.

### 2. Box's launch-readiness system

- Source/date/version: [Braintrust customer report](https://www.braintrust.dev/customers/box),
  live 2026-07-30.
- Provenance: attributed firsthand, vendor-edited.
- Workflow/outcome: 80% threshold blocked dogfood; 330-question golden set
  defined GA; versioned/schema-validated datasets; PM-owned requirements;
  production gaps strengthen offline suite.
- Frequency/severity: nightly and release-blocking.
- Workaround: Box built a privacy-preserving runner.
- Fixed/incumbent status: current.
- Supports/weaken: strongly supports null; weakens separate source-of-truth
  claim.
- Confidence: 4/5.

### 3. Braintrust's 2026 feature velocity

- Source/date/version: [changelog](https://www.braintrust.dev/docs/changelog),
  February–July 2026.
- Provenance: official.
- Workflow/outcome: trace-level/multi-turn scoring, Topics, review improvements,
  dataset snapshots/environments, comparison improvements, pairwise scoring,
  remote-eval parameters, tag filters, exports.
- Frequency/severity: product-wide.
- Workaround: configuration.
- Fixed: several earlier plausible gaps are now native.
- Supports/weaken: strongly supports incumbent-feature thesis.
- Confidence: 5/5 for existence, 3/5 for ease.

### 4. GitHub already owns change and approval

- Sources: [environments and protection
  rules](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments),
  [deployment controls](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments),
  [artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations);
  live 2026-07-30.
- Provenance: official.
- Workflow/outcome: exact SHA/PR, required status checks, reviewers, no
  self-review, comments, bypass control, GitHub App protection rules,
  deployment history and provenance.
- Frequency/severity: every protected PR/deployment.
- Workaround: one Braintrust check or protection app.
- Supports/weaken: undermines separate approval/decision-record UI.
- Confidence: 5/5.

### 5. CodeRabbit is moving into change-specific policy

- Sources: [custom checks](https://docs.coderabbit.ai/pr-reviews/custom-checks),
  [pre-merge checks](https://docs.coderabbit.ai/pr-reviews/pre-merge-checks),
  [configuration](https://docs.coderabbit.ai/reference/configuration), updated
  2026-07-28.
- Provenance: official; product name verified as **CodeRabbit**.
- Workflow/outcome: sees diff/history/PR/issues/discussion/MCP context; emits
  Passed/Failed/Inconclusive; can block; records override actor.
- Frequency/severity: every configured PR.
- Workaround: natural-language checks and YAML; cannot run tests or inspect
  approval state.
- Supports/weaken: weakens automatic applicability/release-review wedge.
- Confidence: 5/5 capability, 3/5 correctness.

### 6. LangSmith plus pytest

- Sources: [pytest integration](https://docs.langchain.com/langsmith/pytest),
  [datasets](https://docs.langchain.com/langsmith/manage-datasets), current
  2026.
- Provenance: official.
- Workflow/outcome: versioned production-derived datasets, repeated trials,
  evaluators, online scoring, metadata/git capture, assertions that fail CI.
- Frequency/severity: ordinary test and production loop.
- Workaround: GitHub YAML.
- Supports/weaken: shows Braintrust is not the only absorber.
- Confidence: 5/5 capability, 3/5 ease.

### 7. Wordsmith's model swap

- Source/date: [LangSmith customer case](https://www.blog.langchain.com/customers-wordsmith/),
  2024-07-08.
- Provenance: attributed firsthand, vendor-edited.
- Workflow/outcome: static eval sets crystallized requirements; Claude 3.5
  versus GPT-4o comparison completed within an hour; production release same
  day; Statsig linkage required a few metadata lines.
- Frequency/severity: real legal-AI model release.
- Workaround complexity: small.
- Fixed: current workflow likely easier now.
- Supports/weaken: strongly supports ordinary-glue null.
- Confidence: 4/5.

### 8. Promptfoo's small CI gate

- Sources: [CI/CD](https://www.promptfoo.dev/docs/integrations/ci-cd/),
  [GitHub Action](https://www.promptfoo.dev/docs/integrations/github-action/),
  updated 2026-07-18/21.
- Provenance: official open-source docs.
- Workflow/outcome: before/after evals, deterministic/model graders, JSON/HTML/
  JUnit, git tags, fail-on-error or short `jq` pass-rate gate, PR comment.
- Frequency/severity: every prompt/model PR.
- Workaround: a workflow and small shell check.
- Supports/weaken: strongest evidence that scalar policy arithmetic is not a
  company.
- Confidence: 5/5.

### 9. Sentry release linkage

- Sources: [release APIs](https://docs.sentry.io/api/releases/),
  [deploy API](https://docs.sentry.io/api/releases/create-a-deploy/), and
  [AI Agent Monitoring](https://sentry.io/changelog/ai-agent-monitoring--open-beta/).
- Date/version: current API; Agent Monitoring open beta since 2025-06-26.
- Provenance: official.
- Workflow/outcome: release/commit/deploy/environment identity plus errors,
  traces, model/tool/tokens/latency context.
- Frequency/severity: every deploy and production event.
- Workaround: propagate one release ID.
- Supports/weaken: weakens “later outcome cannot tie to release.”
- Confidence: 5/5 release link, 3/5 behavioral outcome semantics.

### 10. PostHog's integrated product-outcome loop

- Source/date: [PostHog engineering retrospective](https://newsletter.posthog.com/p/what-we-wish-we-knew-before-building),
  2026-03-24.
- Provenance: firsthand company engineering report.
- Workflow/outcome: trace IDs, replay, curated real-user data, scorers, manual
  trace hour, product analytics, experiments and user outcomes.
- Frequency/severity: recurring trace review and continuous product metrics.
- Workaround: manual curation and event-schema joins.
- Fixed/incumbent status: PostHog is building the missing primitives.
- Supports/weaken: supports both the job and incumbent absorption.
- Confidence: 4/5.

## 8. Ten strongest pieces of evidence for a real gap

### 1. OpenAI's sycophancy release

- Source/date/version: [OpenAI postmortem](https://openai.com/index/expanding-on-sycophancy/),
  2025-05-02; GPT-4o update rolled out 2025-04-25 and rolled back from
  2025-04-28.
- Provenance: firsthand.
- Workflow/outcome: offline evals and A/B tests were positive; expert testers
  felt behavior was off; sycophancy existed in policy thinking but was not a
  deployment eval; OpenAI launched and later called it the wrong decision.
- Severity/frequency: harmful emotional/mental-health behavior and full
  rollback; model updates recur.
- Workaround: explicit per-launch behavior approval, blocking qualitative
  signals, new sycophancy evals, alpha testing.
- Complexity: high organizational policy work.
- Fixed: incident fixed; structural coverage problem mitigated.
- Supports/weaken: strongest evidence for requirement→required-evidence→decision;
  weakens independent vendor because OpenAI built it internally.
- Confidence: 5/5.

### 2. Anthropic's three infrastructure regressions

- Source/date/version: [Anthropic postmortem](https://www.anthropic.com/engineering/a-postmortem-of-three-recent-issues),
  2025-09-17; Haiku 3.5/Sonnet 4/Opus 3.
- Provenance: firsthand.
- Workflow/outcome: canaries, benchmarks, safety evals, performance metrics and
  spot checks did not reliably reproduce intermittent user failures;
  platform/privacy differences obstructed attribution.
- Severity/frequency: weeks, multiple models/platforms; at peak 16% of an hour's
  Sonnet 4 requests affected by one issue.
- Workaround: production-sensitive evals and new privacy-preserving feedback
  correlation/debugging.
- Complexity: high.
- Fixed: specific bugs fixed; structural program continued.
- Supports/weaken: change attribution and production feedback gap; may belong
  to vendor observability.
- Confidence: 5/5.

### 3. Spotify's eval/experiment boundary

- Source/date: [Spotify Engineering](https://engineering.atspotify.com/2026/5/better-experiments-with-llm-evals-a-funnel-not-a-fork),
  2026-05-18.
- Provenance: firsthand.
- Workflow/outcome: offline evals select treatments; online experiments
  validate impact; judges recalibrate from outcomes.
- Severity/frequency: 42% of launched experiments rolled back for secondary
  regressions that offline evals did not flag.
- Workaround: cross-stack eval→experiment→calibration funnel.
- Complexity: medium–high.
- Fixed: ongoing operating model.
- Supports/weaken: strongest quantified cross-stack outcome evidence; mature
  experimentation may be sufficient.
- Confidence: 5/5.

### 4. OpenAI deployment simulation

- Source/date/version: [OpenAI](https://openai.com/index/deployment-simulation/),
  2026-06-16; GPT-5-series Thinking through GPT-5.4.
- Provenance: firsthand.
- Workflow/outcome: replay recent de-identified production prefixes through
  candidate; preregister 20 behavior rates; audit post-release calibration;
  1.3M conversations and 120k coding-agent trajectories.
- Severity/frequency: multiple frontier deployments; surfaced calculator
  hacking pre-release; median frequency error 1.5×.
- Workaround: very large internal simulation, privacy, taxonomy, and audit
  infrastructure.
- Complexity: very high.
- Fixed: deployed but tail/fidelity/distribution limits remain.
- Supports/weaken: proves prediction→outcome calibration job; limited
  addressable market.
- Confidence: 5/5.

### 5. Broken coding-eval evidence

- Source/date/version: [OpenAI, “Separating signal from noise in coding
  evaluations”](https://openai.com/index/separating-signal-from-noise-coding-evaluations/),
  2026-07-08; SWE-Bench Pro public split, 731 tasks.
- Provenance: firsthand audit.
- Workflow/outcome: automated pipeline flagged 27.4% broken; human campaign
  found 34.1%; weak tests allowed incomplete fixes to pass.
- Severity/frequency: roughly one-third of a deployment-relevant benchmark.
- Workaround: human escalation and dataset-quality pipeline.
- Complexity: high.
- Fixed: one audit; ongoing maintenance problem.
- Supports/weaken: invalid/missing evidence must not pass; could justify dataset
  QA rather than release control.
- Confidence: 5/5.

### 6. Anything/Create's daily control loop

- Source/date: [Anything engineering](https://www.anything.com/blog/evaling-an-ai-agent),
  2025-05-17.
- Provenance: firsthand.
- Workflow/outcome: ~50 real/edge/synthetic cases, LLM judges, computer-use
  agents, human comparison, daily scores/logs/diffs; catches model/planner/
  runtime/prompt/tool regressions.
- Severity/frequency: every morning for an agent that builds/deploys apps.
- Workaround: bespoke execution and human review; CUA only 70–90% precise.
- Complexity: high.
- Fixed: still building replay and version preference.
- Supports/weaken: shows recurring factory-assurance work; Braintrust is visible
  as its eval substrate.
- Confidence: 4.5/5.

### 7. Uber's control-plane readiness score

- Source/date: [Uber Engineering](https://www.uber.com/en-IE/blog/raising-the-bar-on-ml-model-deployment-safety/),
  2025-10-02/30 locale metadata; 400+ use cases, 20k training jobs/month.
- Provenance: firsthand.
- Workflow/outcome: standardized reports, historical backtests, shadows,
  rollout/rollback, and explicit coverage score across eval, shadow, tests and
  monitoring.
- Severity/frequency: production scale; regressions move from days to hours;
  >75% of critical models reached Intermediate safety.
- Workaround: substantial Michelangelo internal control plane and program
  management.
- Complexity: very high.
- Fixed: mature for ML; agent behavioral extension remains active.
- Supports/weaken: strong job evidence; stronger internal-platform than startup
  evidence.
- Confidence: 4.5/5.

### 8. Practitioner tooling-gap synthesis

- Sources/date: [Hamel Husain and Shreya Shankar](https://hamel.dev/blog/posts/evals-faq/what-gaps-in-eval-tooling-should-i-be-prepared-to-fill-myself.html),
  updated 2026-05-05; [full FAQ](https://hamel.dev/blog/posts/evals-faq/).
- Provenance: practitioner synthesis from many implementations, not one audited
  customer.
- Workflow/outcome: tools cover table stakes; teams still build error-pattern
  discovery, application-specific evaluators, annotation apps, bulk
  export/writeback, and incident-driven CI cases.
- Frequency/severity: recommended fresh-trace review weekly and after incidents;
  model-judge maintenance can require 100+ labels and weekly work.
- Workaround: notebooks, Git, small libraries/custom apps.
- Complexity: medium–high recurring.
- Fixed: current through 2026.
- Supports/weaken: supports residue; also explicitly favors minimal internal
  tooling.
- Confidence: 4/5.

### 9. Schneider Electric's LangSmith gate layer

- Source/date: [Schneider/LangChain report](https://www.langchain.com/blog/how-schneider-electric-built-their-llmops-foundations-at-enterprise-scale-with-langsmith),
  2026-07-07.
- Provenance: customer-authored on vendor site.
- Workflow/outcome: 60+ AI products; production traces feed datasets; thin eval
  CLI; internal maturity ontology; automated LangSmith API reporting;
  scheduled GitHub consolidated gate review.
- Severity/frequency: portfolio-wide product lifecycle.
- Workaround: internal maturity and reporting layer.
- Complexity: medium; authors call it thin and advise using out-of-box features.
- Fixed: current operating model.
- Supports/weaken: strongest direct “eval platform plus internal gate” evidence;
  also supports internal-glue null.
- Confidence: 5/5.

### 10. CodeRabbit evidence needs independent authority

- Source/date: [Lin et al.](https://arxiv.org/abs/2607.03316), 2026-07-03.
- Provenance: independent empirical preprint.
- Workflow/outcome: 31,073 review/feedback pairs, 10,191 PRs, 239 repos; 36.4%
  accepted, 7.3% discussed, 56.3% rejected.
- Severity/frequency: large in-the-wild sample; false positives, redundancy,
  scope and intent mismatch.
- Workaround: human triage, configuration, advisory rather than final authority.
- Fixed: 2026 product has improved context/custom checks; model error remains.
- Supports/weaken: supports separate deterministic/human authority; GitHub
  already offers the boundary.
- Confidence: 4/5.

## 9. Complaint taxonomy

### Braintrust

Public firsthand complaint volume is too thin to rank frequencies confidently.
That absence should not be converted into satisfaction evidence.

| Class | Frequency signal | Severity | Resolved/workaround | Relevance |
|---|---|---|---|---|
| Code-first setup makes PMs depend on engineers | Low–medium anecdotal | Medium | Playgrounds, Loop, auto-instrumentation; custom evals still code | Configuration burden; weak Triana support |
| Multi-turn/trace scoring gap | Low, often competitor-authored | High if true | Current trace-scoped online scoring accesses all spans/thread | Resolved incumbent feature; undermines Triana |
| Trace-to-dataset routing requires curation | Low | Medium | UI/API, Topics, Loop, webhook/Zapier | Possible maintenance wedge, likely glue |
| SDK/language unevenness | Low; Ruby beta and SDK breaking changes | Low–medium | Pin Python/TS or OTEL | Mostly irrelevant |
| Pricing/plan gates for snapshots/environments/sandboxes/charts | Certain feature restriction; complaint frequency unknown | Medium | Pro $249 or external Git/CI | Pricing complaint, not structural proof |
| Strong comparison/CI/production loop | Strong official/customer success | High positive | Native | Directly undermines frozen V1 differentiation |

### LangSmith

| Class | Frequency signal | Severity | Resolved/workaround | Relevance |
|---|---|---|---|---|
| Large-dataset performance | One reproducible open SDK issue plus practitioner anecdotes | High at 50k–150k rows | Shard/concurrency/pytest-xdist; issue remained open in collection | Reliability/performance, not release-record proof |
| Intermediate-step online eval visibility | Concrete earlier complaint | High for agents | Current run-tree/intermediate-step/multi-turn evaluators resolve it | Incumbent closure |
| Trace ingestion/memory/association SDK bugs | Several version-specific issues | High when active | Pin/upgrade; cited issues closed | Evidence completeness matters, but mostly bugs |
| UI churn/outage | Anecdotal | Medium episodically | Incident fixed | Irrelevant |
| Self-host/privacy overhead | Recurring community preference | Medium–high | Hybrid/self-host; Schneider reports EKS upgrade/ops cost | Deployment burden, not Triana |
| Need consolidated gate reporting | Strong Schneider example | High organizationally | Thin CLI + API reports + scheduled GitHub workflow | Supports both gap and internal glue |

### CodeRabbit

| Class | Frequency signal | Severity | Resolved/workaround | Relevance |
|---|---|---|---|---|
| False positives/nitpicks/out-of-scope | High: 56.3% rejected in 31k-pair study | High | Tune rules, human triage, advisory use | One evidence lane, not authority |
| Review latency | Medium practitioner signal | High for blocking merges | On-demand/earlier CLI/IDE, smaller PRs | CI should remain independent |
| Nondeterministic rerun “whack-a-mole” | Medium practitioner signal | High recurring | Auto-pause/manual rerun/human verdict | Supports typed advisory state |
| Missing cross-repo/business context | Medium | Medium–high | Multi-repo analysis, knowledge base, MCP; still bounded | Incumbent expanding into context |
| Opaque rate limits | Medium recent community signal | High for coding factories | Manual selection/fallback/higher plan | Reliability/pricing; mostly irrelevant |
| Real security/bug catches | Strong but contradictory empirical/vendor evidence | High positive | Native | Useful evidence producer |
| Custom pre-merge checks/overrides | Strong official | Strategically high | Native Pro+ | Direct incumbent threat |

## 10. Workflow comparison

| Stack | Natively owns | Ordinary glue | Manual/unowned |
|---|---|---|---|
| Braintrust alone | Traces, logs, datasets, scorers, experiments, baselines, trials, comparisons, online scoring, human review, prompts, environments, dashboards | Release SHA and external links as metadata | Change-specific required checks, cross-system sufficiency, release approval/exception, outcome-calibrated requirement change |
| Braintrust + ordinary CI | Above plus exact Git diff/SHA, required checks, artifacts, branch rules, GitHub approval/deployment | Small YAML/policy script; shared release IDs to telemetry | Semantic criticality/applicability, trial-aware policy, cross-system exception rationale |
| LangSmith + ordinary CI | Equivalent trace/eval loop, pytest/Vitest, online/multi-turn evaluators, annotation, prompt environments; optional runtime | Thin CLI/GitHub reports; feature-flag metadata | Same semantic jobs; Schneider built maturity gates |
| PostHog + Sentry + CodeRabbit + Claude Code factory | Code generation/review, CI tests, product analytics, feature flags/experiments, errors/releases, agent traces/alerts | Consistent release IDs, API queries, links/comments | No shared obligation/required-evidence ontology or comparability record |
| Proposed Triana layer | Should own only external references, identity/comparability validation, required-vs-received evidence, typed gaps, decision/exception link, outcome lineage | Thin adapters | Fails if it becomes another eval/trace/policy authoring platform |

## 11. “Why install Triana?” test

### Strongest answer

> Install Triana if your release decision spans Braintrust/LangSmith,
> deterministic CI, CodeRabbit/security checks, GitHub approval, and
> Sentry/PostHog outcomes, and today nobody can prove that the required evidence
> for this exact change was present, comparable, reviewed, and later calibrated
> against production. Triana reads artifact identities in place, refuses to
> treat absence as pass, and preserves the release/outcome lineage without
> taking over your eval or deployment stack.

### Attack

1. GitHub already stores the exact change, required checks, approval,
   exception comments and deployment history.
2. Braintrust/LangSmith already store immutable experiments, baselines,
   per-case results, human review, trace origins and production feedback.
3. A release ID joins Sentry/PostHog with a few metadata fields.
4. CodeRabbit can increasingly infer change-specific policy from diff/issues/
   internal MCP context.
5. A separate “obligation” object is customer work unless Triana can infer or
   import it safely.
6. One protected case manually selected for every release is not enough
   automation to outweigh another control plane.
7. An immutable copy of links/hashes is useful for audit, but no evidence yet
   shows a non-regulated team pays $500/month for it.

### Failure conditions

The proposed product is **failed** if customers must:

- duplicate behaviors: failed;
- recreate datasets: failed;
- rewrite scorers: failed;
- configure each release manually beyond selecting/confirming a precomputed
  evidence plan: failed;
- move data out of Braintrust/LangSmith/Sentry/PostHog: failed;
- maintain a second evaluator or requirement ontology: failed.

The frozen V1 currently risks the last and fourth conditions. It asks customers
to maintain a Triana Protected Case/Release Obligation and manually select it,
even when the behavior already exists as a Braintrust/LangSmith dataset row,
tag, scorer and incident link.

## 12. Falsification memo

### Evidence that kills current V1

Kill or supersede V1 if any of the following are observed across three eligible
Braintrust/LangSmith-native teams:

1. A complete one-case release review is reproduced in under two hours using
   existing dataset metadata, eval action and GitHub checks, with no recurring
   manual step beyond normal review.
2. No release action/conversation changes after showing explicit
   required-versus-received evidence and gaps.
3. No team retains the protected behavior across three releases.
4. No team will pay, even when setup requires no duplicated data/scorers.
5. Customers say the Triana case/obligation object is a second ontology.
6. Braintrust/LangSmith imports external check statuses and records
   change-specific evidence requirements/approvals with comparable identity.

### Evidence that kills the cross-stack Release Review thesis

Kill it if:

1. GitHub check suites/environments plus incumbent metadata reconstruct
   change, requirements, evidence, gaps, approval and exception in a stable,
   low-maintenance view.
2. Cross-stack evidence is uncommon: at least 80% of consequential releases in
   five target teams use one eval platform plus CI only.
3. Missing/non-comparable evidence has no measured effect on release delay,
   escaped failures, ownership disputes or decision confidence.
4. Teams prefer links in the PR and reject a durable external manifest even
   when offered read-only.
5. An incumbent ships the object and two named customers use it as release
   authority.

### Evidence that kills long-term Release Control

Kill it if:

1. Product analytics/feature-flag/deployment platforms natively calibrate
   pre-release eval predictions against outcomes and update policies with human
   approval.
2. Organizations refuse a vendor-neutral control plane because deployment
   authority must stay in GitHub/LaunchDarkly/Argo/cloud controls.
3. Production outcome linkage is just release-ID propagation and never changes
   future evidence requirements.
4. Rollout/pause/rollback decisions remain application-specific enough that
   generic policy creates dangerous false confidence.
5. Three design partners request reporting but not enforcement after six
   months of repeated usage.

## 13. Recommended decision

**Run one additional decisive experiment. Do not continue implementation of the
frozen V1 until it passes.**

This is not generic “more research.” The unresolved fact is:

> Will a Braintrust/LangSmith-native team pay for and retain a read-only
> cross-stack release-evidence manifest because its existing stack cannot
> reconstruct a consequential release without meaningful recurring burden?

Smallest test:

- Sample: three eligible conversational-agent teams already paying for
  Braintrust or LangSmith and using GitHub CI plus at least one of Sentry,
  PostHog, CodeRabbit or a security tool.
- Input: each team's last consequential agent release and its real artifacts;
  no hypothetical interviews.
- Procedure: first ask the team to reconstruct the release using its current
  stack; time every step and count systems/manual joins. Then produce a
  read-only manifest that references artifacts in place. Do not create a
  Triana dataset, scorer or case copy.
- Success threshold:
  - at least two of three reconstructions require more than four engineer/
    reviewer hours or reveal a material missing/non-comparable fact;
  - the manifest changes or materially clarifies at least one real decision;
  - at least one team signs a $500/month 60-day paid pilot;
  - no team must duplicate behavior definitions, data or scorers.
- Stop rule: if fewer than two teams cross the burden threshold, no decision
  changes, or nobody pays, classify the wedge as **likely internal glue** and
  stop frozen-V1 implementation.
- Time/cost cap: one week, maximum six hours of founder work per team, and
  maximum $3,000 total participant incentives; no product build beyond a
  hand-authored/static manifest.

Separately, if the goal is only to complete Track A's account-gated checks, the
smallest action is to sign into a free Braintrust Starter account and rerun the
existing HRAI harness. That would improve the capability matrix but would not
resolve willingness to buy, so it must not be mistaken for the decisive
company test.

## 14. Final answer to the research question

After attempting HRAI with Braintrust and examining current developer evidence:

- **Yes, a recurring consequential job remains after evals.**
- **No, the evidence does not yet show the frozen V1 deserves an independent
  product.**
- The hard part is not running or comparing evals. It is the human and
  deterministic policy joining change-specific requirements, sufficient
  comparable evidence, exceptions, and later outcomes.
- Braintrust/LangSmith plus GitHub can solve frozen V1 sufficiently for a
  competent standardized team.
- The independent opportunity, if it exists, is a neutral reference-and-
  validation layer for genuinely fragmented teams. Its necessity and
  willingness-to-pay remain unproven.

This is a successful negative result against the broad founder thesis and a
conditional positive result for a much narrower one.
