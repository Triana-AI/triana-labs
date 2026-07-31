# Braintrust live HRAI dogfood results

Date: 2026-07-30  
Account: Triana / My Project  
Data: synthetic HRAI cases; sensitive fields stayed local  
Status: completed Track A evidence; no production deployment or product change

## Provisional replacement verdict

**Braintrust plus ordinary CI can solve this bounded HRAI release job.**

The current evidence therefore leans **likely internal glue** for the frozen
V1, confidence **72%**. This is not a finding that the release-decision job is
fake. It is a finding that the observed residue was implementable with generic
Braintrust records, GitHub-style policy, and **227 executable lines plus a
55-line policy/evidence declaration**.

The three strongest reasons:

1. Braintrust natively handled persisted experiments, explicit baselines,
   repeated trials, per-case regressions, trace-to-dataset origin, production
   tracing, online scoring, human feedback, prompt versions, BTQL queries, and
   arbitrary cross-stack metadata.
2. The important gaps were real but compact: Braintrust did not flag an
   omitted required scorer and compared different dataset versions without a
   non-comparability warning. A 130-line CI script detected both and produced
   PASS/REVIEW/BLOCK-like output.
3. A 97-line builder plus 55 lines of declared requirements assembled a
   cross-stack record, and a 73-line adapter stored it intact in Braintrust as
   a normal trace. Storage is not the wedge. The possible wedge is maintaining
   trustworthy requirement/evidence semantics across many releases without
   making customers maintain a second ontology.

## Experiments actually run

| # | Experiment | Result | What it established |
|---:|---|---|---|
| 1 | CLI setup and auth | Passed after browser sign-in; CLI `0.15.1` | CLI-only operation is viable after one authentication step |
| 2 | Direct OpenRouter smoke test | Passed with `deepseek/deepseek-v3.2` | Provider credentials worked; negligible synthetic spend |
| 3 | Braintrust AI secret | Existing `OPENROUTER_API_KEY` confirmed | Braintrust can hold provider configuration |
| 4 | Braintrust gateway route | Failed with 404 “no provider configured” | A stored secret did not automatically make this model routable through the gateway; direct OpenRouter plus Braintrust tracing worked |
| 5 | Production-style traced model call | Passed | Braintrust stored the traced request/result and model metadata |
| 6 | Versioned remote dataset | Passed: 12 redacted cases | Dataset changes receive exact transaction/version IDs |
| 7 | Named dataset snapshot | Failed with 403 | Named snapshots were unavailable on the current plan |
| 8 | Trace-to-dataset | Passed | One traced production-style example became a dataset row with its origin link |
| 9 | Remote baseline experiment | Passed: 12 cases × 3 trials × 7 scorers | Persisted experiment/scorers/trials work |
| 10 | A/A control | Passed technically; behavioral noise observed | Same-model movement was large enough to break a naive zero-regression gate |
| 11 | A/B candidate | Passed technically; candidate regressed | Braintrust surfaced score deltas and regression counts |
| 12 | Missing required scorer | Braintrust omitted the metric without warning | “Required evidence” is not a native release-policy concept |
| 13 | Dataset-version drift | Braintrust compared normally without warning | Versions are recorded, but comparison did not refuse or downgrade moved evidence |
| 14 | Ordinary CI gate | Candidate BLOCK; A/A BLOCK; drift REVIEW | 130 lines supplied required-score, absolute-threshold, and comparability semantics |
| 15 | Model-graded scorer v1 | Failed: synchronous client used as async | Scorer failures remained missing, not zero |
| 16 | Model-graded scorer v2 | 1/4 structured results with DeepSeek | Judge/provider compatibility materially affects evidence availability |
| 17 | Model-graded scorer v3 | 4/4 structured results with GPT-4.1 mini via OpenRouter | Model-graded scoring works when provider/model setup is compatible |
| 18 | Online scorer v1 | Automation error on documented `{score, metadata}` return | The failed automation was visible as an error span |
| 19 | Online scorer v2 | Passed after returning a bare float | Async online score appeared after about 33 seconds |
| 20 | Human/API feedback | Numeric score and comment passed | Feedback can be attached to a production trace |
| 21 | Prompt revisions and exact pin | Three revisions pushed; v2 loaded by exact xact ID after v3 | Prompt identity is reproducible natively |
| 22 | Cross-stack release record | Passed locally | Braintrust experiment facts, GitHub/Sentry references, requirements, gaps, and a recommendation fit in 282 lines of ordinary code/config |
| 23 | Store cross-stack record in Braintrust | Passed | Generic trace metadata can hold and query the whole record |
| 24 | Structured approval through metadata feedback | Calls accepted, fields not present on read-back; metadata-only call also rejected without score/tag/expected/comment | This specific SDK/API path was unreliable; it is a product/configuration limitation, not proof that Braintrust cannot record human review |
| 25 | Over-broad online-scoring rule | Release-record trace received an irrelevant marker score of zero | Filters are necessary; online automation can pollute unrelated traces if configured broadly |

## HRAI change and results

Baseline:
`qwen.qwen3-235b-a22b-2507-v1:0`.

Candidate:
`qwen.qwen3-32b-v1:0`.

Kept fixed as observed: prompt
`candidate-screening-v2-reliability`, agent/tool/retrieval/harness declaration,
12-case dataset, and scorer definitions. The manifests do not prove a complete
container/runtime identity, so “model-only change” is a declared and
substantially controlled claim, not cryptographic proof.

| Score | Baseline | A/A | Candidate | Candidate delta |
|---|---:|---:|---:|---:|
| Execution complete | 91.7% | 91.7% | 91.7% | 0.0 pp |
| Required decision | 83.3% | 66.7% | 58.3% | **-25.0 pp** |
| Missing-data non-fabrication | 91.7% | 100.0% | 91.7% | 0.0 pp |
| Injection-refusal proxy | 83.3% | 75.0% | 75.0% | -8.3 pp |
| Tool efficiency | 100.0% | 100.0% | 100.0% | 0.0 pp |
| Composite task success | 50.0% | 41.7% | 33.3% | **-16.7 pp** |

The candidate was faster and cheaper in the frozen HRAI source artifacts:
mean latency -41.4%, p95 latency -50.4%, tokens -15.5%, cost -50.5%, and tool
calls -13.7%. Source operational metrics were queryable with BTQL after custom
mapping, but the CLI comparison summarized eval execution duration rather than
these replayed source metrics.

Braintrust's three repeated trials replayed frozen outputs, so their within-run
variance was zero by construction. The independent HRAI A/A run is the real
noise signal and moved required-decision performance by 16.7 percentage
points on this subset.

## Capability matrix

Classification:

- A: native and easy
- B: native but operationally difficult
- C: normal Braintrust configuration
- D: small ordinary CI glue
- E: substantial custom product logic
- F: unsupported in this test
- G: not needed

| Capability | Official capability | Actual result | Burden / restriction | Release relevance | Class |
|---|---|---|---|---|---|
| Agent tracing | Nested SDK/OTel traces with model/tool metrics | Direct OpenRouter call traced successfully | Low after instrumentation | Strong incumbent substrate | A |
| Production logs/filtering | Logs, filters, BTQL/SQL, metadata/tags | Queried trace, scores, metrics, and release record by CLI | Schema discipline required | Undermines a trace-view wedge | A |
| Datasets | Versioned eval cases | 12 redacted cases uploaded | Low | Native evidence source | A |
| Exact dataset versions | Every mutation has xact/version | Version changed after one metadata edit and was recorded on experiments | Easy to record; must be checked | Useful but insufficient alone | A/D |
| Named snapshots | Named checkpoints and pinning | 403 on current plan | Plan restriction | Promotion semantics are bundled on paid plans | C |
| Trace-to-dataset | Promote production traces retaining origin | Passed with one row | One curation step | Native feedback loop | A |
| Dataset pipelines | Declarative bulk trace transforms | Docs/CLI inventoried, not run | Beta/configuration | Likely incumbent feature | C |
| Playground | Side-by-side prompts/models/scorers | Not used because research was CLI-only | UI-oriented | Not needed for release gate | G |
| Prompts | Versioned saved prompts | Three revisions pushed | Initial runner/environment error; then easy | Composite identity can reference Braintrust version | A |
| Exact prompt pin | Load historical prompt by xact ID | v2 loaded after v3 became current | One version field | Native reproducibility for prompt-owned state | A |
| Workflows/functions/tools | Versioned deployable functions | Scorer pushed and invoked by automation | Packaging/runtime setup | Incumbent owns evaluator deployment | C |
| Deterministic scorers | Python/TS/custom scorers | Seven ran on all cases/trials | Application semantics still custom | Evaluation, not Triana moat | A |
| Model-graded scorers | Built-in/custom LLM judges | Succeeded after two preserved failures | Provider/model calibration and cost | Missing/error must stay typed | B/C |
| Human feedback | Scores/comments/tags/expected/metadata | Numeric annotation/comment succeeded | Structured approval metadata path was unreliable | Generic review exists; approval semantics remain custom | B |
| Human review queues | Assignment/reviewer workflows | Official docs only; CLI-only test did not use UI | Some features plan-gated | Weakens a separate review UI | C |
| Experiments | Persisted eval runs | Baseline/A/A/candidate persisted | Easy | Native evidence record | A |
| Explicit baseline | Candidate can name exact baseline | Candidate linked to approved baseline ID | Must be explicit | Essential; native when configured | A |
| Automatic baseline | Recent same-branch experiment fallback | Observed auto comparison when explicit base omitted | Can select a non-approved run | Configuration hazard | B |
| Per-case/aggregate comparison | Deltas, improvement/regression counts, diffs | CLI comparison passed | Easy | Commodity | A |
| Repeated trials | Trial grouping and aggregation | 3 trials per case | Live trials cost model usage | Mechanics native; policy remains hard | A |
| Variance policy | Interpret stochastic movement | A/A failed naive gate | Customer-defined | Real residue, but ordinary policy code | D |
| Custom comparison key | SQL key instead of full input | Official docs only; setup is project UI setting | CLI did not expose project setting | Mostly configuration | C |
| Missing-required evidence | Errors are visible; scorers produce scores when run | Omitted required scorer silently disappeared | Braintrust does not know “required” | Central observed gap | D |
| Dataset comparability | Experiment stores dataset ID/version | Different versions compared normally | Custom version equality check required | Central observed gap | D |
| Remote evals | Braintrust triggers customer-hosted code | Inventoried, not launched | Server/auth setup | Native but operationally harder | B |
| Sandboxes | Lambda/Modal isolated eval execution | Not attempted due plan/spend boundary | Beta, Pro/Enterprise | Incumbent feature | B |
| CI/CD | `bt eval`, eval action, reporters | Local CI command and policy script ran | 130 lines for honest policy | GitHub can enforce result | D |
| GitHub integration | PR comment and eval action | Docs verified; no external PR write performed | Small YAML | Existing approval/change authority | D |
| Online scoring | Async sampled/filtered production scoring | Passed after one failed scorer shape | Push scorer, create/filter automation; async delay | Native production loop | B/C |
| Dashboards | Scores/cost/latency/error charts | Data queried with BTQL; UI not used | Custom views/charts may be plan-gated | Not a wedge | A/C |
| Alerts/webhooks | Spend, environment, monitoring actions | Docs/API inventoried, not fired | Configuration and some plan gates | Ordinary integration path | C/D |
| Environments/promotion | Pin prompts/datasets/parameters across stages | Not available on current plan | Pro/Enterprise | Strong incumbent encroachment | C |
| Experiment metadata | Arbitrary identity, git, tags | Model/prompt/code/hash/release fields logged | Does not prove completeness | Good reference substrate | A/D |
| Cost/token/error/latency | Native when instrumented | Live trace native; replay source fields required mapping | Low live, moderate replay | Commodity | A |
| Topics | Cluster/classify logs | Official docs only | Model credits/plan considerations | Dataset-maintenance feature | C |
| Loop | Analyze logs, propose datasets/scorers/views/optimizations | Official docs only | LLM proposal, human confirmation | Weakens maintenance wedge | C |
| APIs/export | REST, SDK, BTQL, JSON/CSV/Parquet | REST, SDK, CLI, BTQL all exercised | Low | Makes ordinary glue credible | A/D |
| Generic cross-stack record | Arbitrary JSON metadata and scores | Entire record stored and queried intact | 73-line logging adapter | Storage is not an independent moat | D |
| Release requirement semantics | Required/optional/why/applicability | Manually declared in 55-line JSON | Recurring human/custom ontology | Only plausible independent residue | E unless standardized |
| Release approval/exception | Comments, scores, metadata, audit history primitives | Comment worked; structured metadata feedback did not read back | GitHub is a better natural authority | Likely link, not duplicate | D |
| Production outcome → future requirement | Shared IDs and trace/dataset updates are possible | Not automated; record held a null link | Human decision and workflow needed | Real job; independent value unproven | E |

## Complete release-question test

| Question | Result with Braintrust + CI | Class |
|---|---|---:|
| What changed? | Git/code identity plus Braintrust model/prompt metadata | D |
| Are baseline/candidate identities reproducible? | Prompt/dataset/experiment versions are; complete runtime identity needs external hashes | D |
| Which known failures are critical, and why? | Stored easily, but humans/policy must declare them | C/D |
| Which checks are required for this change? | 55-line policy declaration; not inferred by Braintrust | E for inference, D for static mapping |
| Which are optional? | Same policy declaration | D |
| What ran and failed? | Native experiment/scorer evidence | A |
| What was missing? | Custom gate caught omitted scorer; Braintrust did not | D |
| What was non-comparable? | Custom gate caught dataset-version drift; Braintrust did not | D |
| Does evidence authorize release? | 130-line gate produced advisory recommendation | D |
| Who approved/held/excepted? | Better owned by GitHub; Braintrust can hold generic annotations | D |
| Can external evidence participate? | Yes as references/status metadata | D |
| Can later production outcomes tie back? | Yes through shared release ID/reference | D |
| Does an outcome change a future requirement? | Human/custom workflow; no trustworthy automatic meaning | E |

No question was technically impossible. The central issue is recurring semantic
maintenance, not missing storage or eval execution.

## Exact glue and recurring manual work

| Artifact | Lines | Purpose |
|---|---:|---|
| `run_remote_redacted_eval.py` | 328 | HRAI-specific redaction, adapter, task, seven scorers, remote experiment artifact |
| `remote_ci_gate.py` | 130 | Required scores, thresholds, dataset-version comparability, recommendation |
| `build_release_record.py` | 97 | Join Braintrust gate facts with external evidence and hash the record |
| `release_review_input.json` | 55 | Manually declare change, requirements, criticality, reasons, and external evidence |
| `log_release_record.py` | 73 | Store the generic record back in Braintrust |

The relevant generic release layer is **282 lines**:
130 gate + 97 record builder + 55 declaration. Logging it in Braintrust adds
73 lines. The 328-line HRAI adapter mostly disappears for a Braintrust-native
application.

Recurring manual steps in this bounded workflow:

1. Confirm the approved baseline identity.
2. Confirm the change identity and fixed dimensions.
3. Maintain which known requirements/checks apply.
4. Review A/A variance and choose a valid tolerance.
5. Inspect required case regressions and typed gaps.
6. Record approval, hold, or exception in GitHub.
7. Propagate a release ID to production telemetry.
8. Decide whether a later outcome changes a case, scorer, or requirement.

Braintrust removes most experiment plumbing, but not these semantic decisions.

## Preserved failures and limitations

- Gateway route failed although the OpenRouter secret existed.
- Named dataset snapshot failed with a plan 403.
- Initial operational metrics were logged at the wrong level for comparison.
- Automatic comparison selected a recent experiment when no explicit approved
  baseline was supplied.
- Missing required scorer produced no Braintrust warning.
- Dataset-version drift produced no comparison warning.
- A/A noise blocked the naive zero-regression policy.
- Two model-judge configurations failed before a compatible model succeeded.
- First online scorer return shape produced an automation error.
- Over-broad online rule scored an unrelated release-record trace.
- Structured metadata feedback did not appear on read-back, despite accepted
  calls; metadata-only feedback raised an SDK validation error.
- The release-record hash is tamper-evident only if retained elsewhere; it is
  not a trusted signature.
- The data is synthetic and the trials replay frozen HRAI outputs.
- No production deployment, paid-plan upgrade, material spend, or GitHub write
  occurred.

## Artifact locations

- Remote artifacts:
  [`artifacts/remote/`](artifacts/remote/)
- Baseline:
  [`artifacts/remote/v2_baseline.json`](artifacts/remote/v2_baseline.json)
- A/A:
  [`artifacts/remote/v2_aa_control.json`](artifacts/remote/v2_aa_control.json)
- Candidate:
  [`artifacts/remote/v2_candidate.json`](artifacts/remote/v2_candidate.json)
- Candidate gate:
  [`artifacts/remote/gate_candidate.json`](artifacts/remote/gate_candidate.json)
- Dataset-drift gate:
  [`artifacts/remote/gate_dataset_drift.json`](artifacts/remote/gate_dataset_drift.json)
- Missing-required gate:
  [`artifacts/remote/gate_missing_required.json`](artifacts/remote/gate_missing_required.json)
- Cross-stack record:
  [`artifacts/remote/cross_stack_release_record.json`](artifacts/remote/cross_stack_release_record.json)
- Remote eval:
  [`run_remote_redacted_eval.py`](run_remote_redacted_eval.py)
- CI gate:
  [`remote_ci_gate.py`](remote_ci_gate.py)
- Record builder:
  [`build_release_record.py`](build_release_record.py)
- Record input:
  [`release_review_input.json`](release_review_input.json)
- Braintrust record logger:
  [`log_release_record.py`](log_release_record.py)
- Model judge:
  [`run_remote_synthetic_judge.py`](run_remote_synthetic_judge.py)
- Online scorer:
  [`online_marker_scorer.py`](online_marker_scorer.py)
- Prompt revisions:
  [`synthetic_prompt_v1.py`](synthetic_prompt_v1.py),
  [`synthetic_prompt_v2.py`](synthetic_prompt_v2.py),
  [`synthetic_prompt_v3.py`](synthetic_prompt_v3.py)

Remote Braintrust identifiers:

- Dataset: `99bbec29-967e-4a78-a7e2-d0a6b24fda90`
- Feedback dataset: `66d50b6a-f12c-4183-95bf-ab001db8edef`
- Baseline experiment: `d000c668-d26a-4af5-846b-62747a801062`
- A/A experiment: `19a3880b-0af4-4045-af3d-8d3355f98781`
- Candidate experiment: `313c8734-b05b-4c52-9a0e-359cfac5fcdd`
- Dataset-drift experiment: `0e565f45-206e-4f52-ba9c-12871abab55c`
- Online scorer: `938f1ac2-4f10-4d74-8700-e4ae1a1f5916`
- Online rule: `9428f357-dd70-426d-852d-ced5e4948b40`
- Prompt: `05b6a2be-9c14-4155-8212-40a27a75a3bd`
- Cross-stack record span: `173f909d-8b11-42e7-acc3-a41bafb6a90b`

## Current falsification result

The live dogfood has **not** killed the broad observation that a consequential
job remains after evals. It has materially weakened the claim that frozen V1
must be an independent product.

The independent wedge survives only if a reference-only layer can:

- derive applicable requirements without per-release manual configuration;
- catch missing/non-comparable evidence across several systems;
- preserve GitHub as approval/deployment authority;
- avoid copying datasets, cases, scorers, prompts, or traces;
- connect outcomes to future requirements with less recurring work than the
  282-line ordinary solution;
- change real release behavior often enough that teams pay for it.

If it cannot do those things, the correct classification is internal glue.
