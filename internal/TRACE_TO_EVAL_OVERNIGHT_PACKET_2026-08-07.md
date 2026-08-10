# Trace-to-Eval V0 overnight execution packet

Date frozen: 2026-08-07

Status: **READY FOR GOAL-MODE EXECUTION**

Owner: Akarsh

## Morning outcome

The overnight target is one local product loop:

```text
trace path
-> strict adapter and accepted/rejected accounting
-> grounded proposed user populations and behavior measurements
-> at most three proposed evals with cited conversations
-> small blind calibration/review queue
-> persisted report
-> the same result through CLI, local backend, and local UI
```

Copy and adapt as much proven owner-authorized Agentagon code as is useful.
Run the app, backend, CLI, and analysis locally. AWS is dependency-only: reuse
the existing private RDS, S3/KMS, and DBOS runtime when needed. The already
approved Azure model endpoint may be called under the bounded policy below.
There is no deployment, ECR, GitHub Actions, Terraform, Supabase setup, public
ingress, or replacement infrastructure in this tranche.

## Labeler

A labeler is required, but nobody labels the corpus. Analysis covers every
accepted conversation. Deterministic stratified sampling creates:

1. twelve blind population-pair items, four per proof corpus, answered
   `SAME`, `DIFFERENT`, `AMBIGUOUS`, or `INSUFFICIENT_EVIDENCE`;
2. up to nine proposed-eval items, at most three per corpus, answered `TRACK`,
   `EDIT`, or `DEFER`;
3. first-broken-link items only for HRAI/TAU cases with official outcome and
   sufficient trajectory evidence. They are never required for trace-only data.

The queue hides method names and hidden truth. Rulings are append-only and
linked to immutable item/evidence hashes. Only a human can promote a proposal
to `TRACKED`.

## Every startup question, already decided

| Question | Frozen answer |
|---|---|
| First deliverable | `Trace-to-Eval Review V0`, not deployment simulation. |
| Customer input | Trace file/directory path, authorization, agent name, optional goal, optional existing eval metadata. |
| Required format | Known adapters normalize exports; PreviewTrace JSONL is the canonical escape hatch, not mandatory preprocessing. |
| Public contract | `EvidenceBundleManifestV0`: source/privacy/capabilities/grouping/outcomes/existing-evals/egress. |
| Internal benchmark | `BenchmarkCaseV0` wraps the manifest with hidden truth, split, rubric, invariants, and allowed claims. It is not customer-facing. |
| Primary semantic mechanism | Copy/adapt Agentagon Generic Exploration V1: facet extraction, bounded hierarchical consolidation, exhaustive candidate inventory, fixed qualification, Track/Edit/Defer. |
| Embeddings/HDBSCAN | Optional sensitivity/discovery challenger, never semantic truth. It cannot block the first green path or force a new dependency. |
| Deterministic authority | Parsing, redaction result, identity, grouping, splits, samples, evidence links, denominators, support, qualification, budgets, hashes, lineage, gaps, persistence. |
| LLM authority | Propose facets, consolidated labels, descriptions, eval wording, and grounded explanations. |
| Human authority | Pairwise meaning, Track/Edit/Defer, final eval wording, first-broken-link rulings. |
| Eval output | At most three primary proposals; preserve/download the full qualified inventory. |
| Existing evals | Map them to observed populations/evidence and report coverage/weakness/gaps; never require reinvention. |
| Proof corpora | HRAI: harness/model controllable. TAU57: harness/model controllable with official reward. Blitz: traces only. |
| Split unit | Highest dependency group: paired case across arms, then task/session/user/template/time; never individual events or sibling trials. |
| Split ratio | Stable salted-hash 60% development, 20% calibration, 20% locked holdout; tiny sets use deterministic largest remainder. |
| Population truth | Small pairwise judgments about same user need, not one exhaustive universal taxonomy and not every trace. |
| Repeatability | Ten cached runs byte-identical; three fresh semantic runs compared for co-membership/proposal/evidence stability, with disagreement shown. |
| Baselines | Deterministic-only, copied Agentagon source behavior, optional embedding challenger, competent coding-agent report, official harness truth, and supplied customer evals. |
| Primary KPI | Validated Eval Yield per expert minute and model dollar. |
| L4/first-broken-link | Outcome-aware benchmark lane only; it cannot block trace-only value. |
| Auth | Preserved but outside the overnight critical path. Local operator mode tests the core. |
| Production deploy | Outside scope. Local UI plus private dependency persistence is the acceptance target. |
| AWS identity | Profile `akarsh-deepprobe`, principal `hr-traffic-provisioner`, account `854847082059`, region `ap-south-1`. |
| AWS CLI | Use `/Users/akarshgajbhiye/miniforge3/bin/aws`; the Homebrew binary is broken locally. |
| Provider | Tests use fakes/caches. Optional live semantic run uses only the existing Microsoft Foundry Fireworks `FW-GLM-5.2` configuration when present and authorized. No fallback. |
| Spend | Maximum USD 25 conservative reservation, no retry-to-green or alternate model. |
| Data custody | Raw data stays local/private. Only an authorized redacted provider projection may leave custody; validate/redact before hashing and calling. |
| Missing optional dependency | Emit a typed gap and continue. Never convert missing evidence to pass. |
| New owner decision needed only for | Public ingress, new cloud resources, new provider/model, spend above USD 25, general real-data egress, destructive data change, or authority-boundary change. |

## Quality corpus and leakage

| Corpus | Capability shape | Development use | Holdout truth |
|---|---|---|---|
| Blitz | trace-only | adapter portability and human usefulness | no independent portability claim; it influenced the mechanism |
| HRAI | paired arms, controllable harness/model, tools | comparison/eval discovery and incident calibration | group-held-out subset only |
| TAU57 | controllable task/harness/model, official reward | outcome-aware analysis and planted-change detection | locked task groups remain unopened during implementation |

Raw corpus rows never enter Git fixtures. Tests use small synthetic
capability-shaped fixtures. Manifests record hashes, counts, privacy, grouping,
allowed use, and held-out group IDs.

## Engine

```text
adapter -> EvidenceBundleManifestV0 + canonical conversations
        -> deterministic capabilities/signals/gaps
        -> authorized semantic facets -> hierarchical populations
        -> exhaustive candidates -> deterministic qualification
        -> <=3 proposed evals + citations
        -> blind review + append-only rulings
        -> TraceToEvalReportV0
```

The backend and UI consume the same report. They do not reimplement analysis.
The CLI uses the same `triana_labs` public API locally and the backend API for
persisted runs.

## Serial implementation sequence

1. Contracts, three adapters/manifests, leakage-safe split, review queue, and
   synthetic fixtures.
2. Copy/adapt the Agentagon semantic engine into Triana; keep exact provenance
   and typed authority.
3. Local CLI command, local backend/DBOS persistence, and one local UI report
   and review screen using `ConversationViewer`.
4. Focused tests, cached repeatability, then bounded Blitz/HRAI/TAU dry runs
   without opening locked holdouts.

If time expires, leave the highest completed vertical slice runnable and the
next exact command. Do not call scaffolding a completed product loop.

## Preflight

| Dependency | Observed state | Rule |
|---|---|---|
| EC2 `i-0f8250d908737b568` | running; SSM online | dependency only; no deploy |
| RDS `db-pg-1` | available; private PostgreSQL 18.3 | reuse through tunnel/runtime |
| S3 artifact bucket | private, public access blocked, SSE-KMS | reuse content-addressed objects |
| GitHub production configuration | absent | irrelevant to this tranche |
| Supabase live project | unverified | irrelevant to this tranche |
| TAU57 archive | present and hash-pinned | available |
| HRAI baseline/candidate traces | present and private | available under existing authorization |
| Blitz exports | present; anonymized export available | use anonymized provider-bound source |

Abort only for integrity mismatch, privacy/egress violation, cross-workspace
access, denominator mismatch, hidden-truth leakage, tamper failure, unsafe
migration, or change-budget expansion. Missing outcome truth, tool order,
existing evals, embeddings, provider config, or L4 evidence are typed gaps.

## Morning test

1. Paste a trace path and start analysis.
2. Verify physical/accepted/rejected/gap accounting.
3. Inspect proposed populations and cited conversations in ConversationViewer.
4. Complete the twelve blind pair items.
5. Track/edit/defer proposed evals.
6. Refresh and confirm rulings persist.
7. Download the report and read the identical run from CLI.
8. Compare with deterministic-only and copied-source baseline results.

## Goal-mode instruction

```text
Implement internal/SLICE_PACKET.md using this overnight packet. Follow the
orchestrator -> independent test author -> independent implementation author
protocol serially. Take every frozen default without asking again. Copy/adapt
the permitted Agentagon engine aggressively, with exact source/destination
provenance. Run app/backend/CLI locally and use only existing AWS RDS/S3/DBOS
dependencies plus the already-approved Azure configuration. Do not deploy,
provision, open ingress, configure GitHub/Supabase, expose secrets, exceed USD
25, fall back providers, weaken tests, or open locked holdouts. Continue through
typed optional gaps. Finish with the local UI/CLI dry run, exact artifacts,
commands, costs, gaps, and morning test URL.
```

