# Trace-to-Eval Review V0 vertical slice

Date frozen: 2026-08-07

Status: **READY — WORKERS NOT STARTED**

Slice ID: `TRACE-TO-EVAL-REVIEW-V0`

Canonical base: `40a27e208abf7e24b5c29b3d5e5978cf44d9bba5` on
`codex/selfserve-v0`, plus the owner-authorized documentation changes in the
current worktree. Commit the documentation freeze before freezing RED tests.

Authority: `triana-labs/CHARTER.md`, the canonical Labs plan, the append-only
decision log, and `internal/TRACE_TO_EVAL_OVERNIGHT_PACKET_2026-08-07.md`.

## Outcome

One authorized trace path produces grounded proposed user populations,
behavior measurements, at most three eval candidates, a bounded human review
queue, one canonical persisted report, and identical CLI/backend/local-UI
projections using the existing conversation viewer.

This is not baseline/candidate execution, deployment simulation, a release
verdict, exhaustive taxonomy, or autonomous golden eval suite.

## Contracts

Input `EvidenceBundleManifestV0` declares source/adapter identity, hashes,
agent/workspace, privacy/authorization/execution/egress, grouping keys,
capability flags, optional outcomes, and optional existing eval metadata.

Outputs:

- `TraceToEvalReportV0`: accounting, capabilities, gaps, proposed populations,
  behavior analytics, full qualified inventory, at most three eval proposals,
  evidence handles, method/run lineage, stability/cost, and review state;
- `ReviewQueueV0`: deterministic blind pairwise and proposal-review items;
- `HumanRulingV0`: append-only ruling/edit/reviewer/time/item hash/supersession;
- internal `BenchmarkCaseV0`: manifest plus split, hidden truth, rubric,
  invariants, and allowed/forbidden claims.

Strict parsing, canonical serialization, domain-separated hashes, and typed
unknown/non-computable states are mandatory.

## Public behavior

| Condition | Behavior |
|---|---|
| valid authorized source | reconcile accounting and publish inspectable report |
| mixed valid/invalid rows | retain accepted conversations plus content-free rejection facts |
| no outcome/harness truth | omit outcome/L4 claims and emit capability gaps |
| provider absent | publish deterministic report plus `SEMANTIC_ANALYSIS_UNAVAILABLE` |
| provider authorized | call only named model with redacted projection and hard budget |
| semantic runs disagree | show stability/disagreement; never rerun-to-green |
| review pending | proposals remain `PROPOSED` |
| human tracks/edits | append ruling linked to exact evidence/method identity |
| tamper detected | refuse affected artifact |
| AWS dependency unavailable | retain complete local artifact path plus typed persistence gap |

## Authority and privacy

Deterministic code owns parsing, redaction result, identity, splits, samples,
evidence, denominators, support, qualification, budgets, hashes, persistence,
lineage, and gaps. The LLM proposes semantic content. Humans own pairwise
meaning, Track/Edit/Defer, final wording, and first-broken-link rulings.

Raw data stays local/private; fixtures are synthetic. Redaction and exact
provider authorization precede provider-bound hashing/calls. Tests use
fakes/caches. One live Foundry `FW-GLM-5.2` canary is allowed only with existing
configuration, explicit manifest permission, no fallback/retry, and USD 25
maximum reservation. Reuse existing private RDS/S3/DBOS only. No deployment,
new infrastructure, Supabase, GitHub configuration, or public ingress.

## Split policy

Group the highest dependency key, including paired arms and sibling trials,
before split assignment. Sort canonical group IDs and assign by
`sha256("triana-split-v0" || corpus_hash || group_id)` to 60/20/20 development,
calibration, and locked holdout using deterministic largest remainder. Review
sampling uses `sha256("triana-review-v0" || report_id || item_id)`. Locked
holdout identities are never opened during implementation/debugging.

## Provenance

Permitted copying/adaptation:

- Agentagon commit `063ad3ed54f4a9646e7040cc6a203615b0de8dcd`, especially
  `agentagon/exploration_v1/{pipeline.py,llm.py,prompts.py,report_ui.py}` and
  `experiments/blitz_seed/{adapter_v1.py,GENERIC_EXPLORATION_V1_VERIFICATION.md}`;
- Kairos-AI first-broken-link/L4 only for the optional outcome-aware benchmark;
- existing Triana backend/report/auth and
  `triana-app/components/conversation/ConversationViewer.tsx`.

Record exact source file/commit, destination, copy versus adaptation,
dependency/license, and data boundary in `docs/PROVENANCE.md`. Do not add
Agentagon as a runtime dependency or copy generated reports, caches, raw Blitz
data, or embedded third-party material.

## Change budget

Test-author ownership:

- `triana-labs/tests/trace_to_eval/**`
- `triana-backend/tests/acceptance/test_trace_to_eval*.py`
- additive `triana-app/tests/trace-to-eval*.test.mjs`
- purpose-built synthetic fixtures below those test areas.

Implementation-author ownership:

- `triana-labs/src/triana_labs/trace_to_eval/**`
- bounded additions to `triana-labs/src/triana_labs/cli.py` and exports;
- bounded additions under `triana-backend/src/triana_backend/{api,application,domain,persistence,services,workflows}/**`;
- one additive Alembic revision only if append-only rulings require it;
- one additive local report/review route under `triana-app/app/analysis/**`,
  bounded API proxy/components, and existing ConversationViewer reuse;
- required canonical docs, provenance, decision log, working memory, slice
  packet, and local decision journal.

Untouched: `triana-core/**`, Release Review V1, existing auth/JWT/membership
semantics, LABS-04/05/06 artifacts, existing migrations, cloud provisioning,
security groups, billing, teams, GitHub deployment, and raw corpus/provider data.

No new production dependency for the first green path. Optional embeddings
cannot force one. Maximum scope expansion is one new file per owned layer and
one additive migration after an orchestrator note. No unrelated cleanup.

## Acceptance

1. Trace-only and paired/outcome synthetic fixtures reconcile accounting,
   preserve group splits, prevent leakage, and type missing capabilities.
2. Fake semantic responses create grounded proposed populations; malformed,
   overclaiming, or uncited output is rejected/gapped.
3. Ten cached replays are byte-identical; varied semantic fakes produce an
   explicit stability comparison.
4. The bounded blind queue is deterministic; rulings append and survive refresh.
5. CLI, backend, and UI project identical report/ruling IDs; cited evidence
   opens in ConversationViewer.
6. Optional provider, embeddings, outcomes, existing evals, auth, CI, and deploy
   absence cannot create failure or false pass.
7. Bounded Blitz/HRAI/TAU dry runs complete or preserve exact typed gaps without
   data leakage or opening holdouts.

## Verification

RED minimum:

```text
cd triana-labs && uv run --locked pytest -q tests/trace_to_eval
cd triana-backend && uv run pytest -q tests/acceptance/test_trace_to_eval*.py
cd triana-app && node --test tests/trace-to-eval*.test.mjs
```

Final minimum:

```text
cd triana-labs && uv run --locked pytest -q tests/trace_to_eval
cd triana-labs && uv run --locked ruff check src tests/trace_to_eval
cd triana-labs && uv run --locked mypy src
cd triana-backend && uv run pytest -q tests/acceptance/test_trace_to_eval*.py
cd triana-backend && uv run ruff check src tests && uv run mypy src
cd triana-app && npm run typecheck && npm run build
./scripts/verify-governance.sh
git diff --check
```

The orchestrator commits this freeze, then one independent test author proves
valid RED. After the test bytes are frozen, one independent implementation
author works only in production-owned paths. The orchestrator alone verifies,
inspects, reconciles, and declares completion. Optional gaps do not stop work;
privacy/integrity/authority/budget violations do.
