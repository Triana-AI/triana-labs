# Trace-to-Eval Review V0 vertical slice

Date frozen: 2026-08-07

Status: **IMPLEMENTED — LOCAL EXIT VERIFIED WITH TYPED OPTIONAL GAPS**

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

The frozen public Python seam is:

```text
run_trace_to_eval(manifest_path, output_dir, *, semantic_model=None) -> report
append_human_ruling(output_dir, ruling) -> accepted_ruling
```

Both are exported from `triana_labs.trace_to_eval`. The first reads the
manifest-declared source path, writes canonical report/review artifacts, and
returns the same report object. The second validates against the exact report
and review queue and appends without rewriting prior rulings. A semantic model
is a duck-typed structured-JSON boundary so tests need no provider dependency.

The local operator HTTP/UI seam is `POST /api/v1/trace-to-eval/runs`,
`GET /api/v1/trace-to-eval/reports/{report_id}`,
`POST /api/v1/trace-to-eval/reports/{report_id}/rulings`, and `/analysis`.
These routes are local-only in this tranche and do not change authenticated
self-serve authorization.

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

### Orchestrator clarification after first engine GREEN

Inspection of the first implementation showed four already-frozen outcomes
were still absent rather than optional: the permitted Agentagon staged semantic
mechanism, an executable approved-Azure boundary, direct known-source adapters,
and reloadable review state. The production budget is clarified to permit:

- `triana-labs/src/triana_labs/trace_to_eval/semantic.py` for copied/adapted
  facet extraction, bounded hierarchical consolidation, candidate inventory,
  and the approved Azure structured-model boundary;
- `triana-labs/src/triana_labs/trace_to_eval/adapters.py` for PreviewTrace,
  Blitz, HRAI, and TAU source-to-manifest/canonicalization behavior;
- bounded additions to the existing CLI, local backend service/routes, and
  `/analysis` page for direct source-path selection, provider activation, queue
  reload, and persisted ruling projection.

No dependency, migration, infrastructure, deployment, raw-data commit, auth
change, or additional UI page is allowed. This is completion of the frozen
input/product contract; a manifest-only UI backed only by a test fake is not
an acceptable substitute.

### Orchestrator clarification for the local product loop

The final integration check established that the existing backend entrypoint
requires deployment-only PostgreSQL, S3, KMS, and DBOS settings before it can
mount any route. The slice may therefore make one bounded addition to
`triana-backend/src/triana_backend/main.py` (and the existing composition/API
seams) so `TRIANA_TRACE_TO_EVAL_LOCAL=1` can boot the trace-to-eval routes on
`127.0.0.1` with local content-addressed artifacts and without inventing cloud
credentials. This mode must not weaken or replace the existing deployed
composition, listen publicly, imply remote persistence, or hide the typed
`REMOTE_PERSISTENCE_UNAVAILABLE` gap. No second application or dependency is
permitted.

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

## Independent RED freeze — 2026-08-07

The independent test author owns exactly
`triana-labs/tests/trace_to_eval/test_trace_to_eval_v0.py`, SHA-256
`f2217bec08c2dd1eb07adca430215f789e0cddbd200373d192aa7818eb1f99a9`.
It freezes five black-box engine behaviors: grounded accounting and group-safe
splits; optional typed gaps; ungrounded semantic rejection; cached replay plus
fresh disagreement visibility; and deterministic review with append-only
rulings. Backend/UI route tests remain an explicit orchestrator integration
responsibility because no pre-existing route seam could produce behavior RED.

Valid RED command:

```text
cd triana-labs && UV_CACHE_DIR=/private/tmp/triana-uv-cache \
  uv run --locked pytest -q tests/trace_to_eval
```

Observed result: five failures, each at the first product boundary because
`triana_labs.trace_to_eval` does not exist. There were no syntax, fixture,
dependency, or collection failures. The test-owned file is now frozen; the
implementation author may read but not edit it.

The orchestrator's additional exit-only adversarial matrix is:

- manifest/source hash mismatch refuses before semantic execution and leaves
  no valid report;
- duplicate trace identity produces content-free rejection/accounting without
  raw-value leakage;
- a stale or wrong review `item_hash` refuses without changing the ruling
  ledger bytes;
- trace text containing instructions to change schemas or reveal other rows is
  treated only as evidence content and cannot alter output structure;
- one dependency group uses deterministic largest-remainder allocation without
  splitting or division errors;
- a missing semantic row or non-object model response becomes an explicit gap,
  never an invented population or pass.

These checks do not alter frozen test semantics. The orchestrator runs them
against public boundaries after GREEN and records exact artifacts/results.

## Orchestrator exit — 2026-08-07

The independent test-author contract remains byte-identical at
`f2217bec08c2dd1eb07adca430215f789e0cddbd200373d192aa7818eb1f99a9`.
An independent adapter/outcome regression set was subsequently frozen at
`04ba2fee4c6b1bc88aa857d2deda67feb031c831aa129e0954a38fb8ba192407`.
The implementation author changed only production-owned surfaces; the
orchestrator added exit-only tests, real-source audits, documentation, and
integration wiring inside the clarified budget.

Focused Labs acceptance is 16/16 GREEN. The adversarial artifact at
`/private/tmp/triana-trace-to-eval-adversarial-_v4vi4ut/results.json`
(`sha256:7f72a826d08e80b2902d6a215788bc84696abbef63604cea4b2c7766c92e2735`)
passes all seven refusal/integrity/leakage checks. CLI, backend, and `/analysis`
use the same canonical engine and report identity; the existing
`ConversationViewer` renders cited DEVELOPMENT evidence, and append-only
rulings survive reload. Local backend and UI listen only on loopback.

Real audited outputs:

- Blitz: 1,519 upstream rows reconstruct to 624 conversations, 0 rejects,
  3,339 user/assistant turns, and 622 tool calls/results; report
  `sha256:bf7eaf78a6baad04d986569bb9494f23a0d16135b4109f663c51cc784c3eb331`.
  Outcomes and semantic provider output are absent and remain typed gaps.
- TAU²: 57 conversations, 0 rejects, 604 turns, and 399 tool calls/results;
  official reward evidence yields 39 successes, 18 failures, and mean reward
  `0.6842105263157895`; report
  `sha256:aa1ec7f44f217614394bbef65bbdbc82649caaa299937105dc4b244706339c7e`.
  This is outcome accounting, not L4 or first-broken-link judgment.
- HRAI: 200 physical records produce 185 accepted conversations and 15 typed
  rejects, 1,008 turns, and 1,430 tool calls/results; report
  `sha256:088824172c09c240bb4cce5c5ca1cb19c8621918540dc69290e6a481945832b2`.
  Completion state is not treated as reward.

One authorized no-retry Azure canary failed before semantic completion and is
retained as `SEMANTIC_ANALYSIS_FAILED`; no provider fallback ran. Conservative
maximum reservation is USD 0.15 and actual charge is unknown. No deployment,
provisioning, ingress, remote write, secret exposure, or holdout opening
occurred. Remaining optional gaps are live semantic populations/eval proposals
for customer data, embeddings, existing-eval import, remote persistence, Blitz
outcomes, HRAI outcome mapping, and Kairos L4/first-broken-link analysis.

## Owner extension: authenticated self-serve integration

After the local engine exit was evidenced, Akarsh extended the same goal to a
fresh-customer path. This addendum does not weaken or replace the engine exit;
it adds a second serial integration gate before the overall task may close.

Outcome: an authenticated owner can create or select an agent, upload a fresh
authorized trace file, start the canonical trace-to-eval run without supplying
an internal manifest/report ID, and revisit agent-scoped import/run history,
overview, canonical report, cited conversations, typed gaps, and the bounded
label/review queue. CLI/SDK and UI use the same backend identities. Every
mechanical step is automatic; only reward-definition approval when no
authoritative outcome exists, semantic proposal acceptance/editing, and human
rulings remain judgment-bound.

Additional contracts and refusal behavior:

- authentication and workspace membership remain backend-enforced; URL IDs,
  report IDs, import IDs, and conversation IDs never bypass owner scope;
- analysis is bound to the exact agent, agent version, import/source hash, and
  canonical report identity and is idempotent for the same request;
- a user may switch agents without leaking cached state or results from another
  agent; every list/detail endpoint rechecks workspace ownership;
- accepted source formats are explicit, and unsupported or invalid files retain
  content-free typed rejection facts rather than partial invented success;
- upload/analysis progress, provider absence/failure, persistence absence, and
  reward absence are typed states, never passes or infinite polling;
- report/review/conversation retrieval validates stored identity and hashes;
- review writes remain append-only and require the exact item hash;
- deployment configuration must fail closed when auth, database, artifact,
  public-origin/TLS, migration, or browser-bundle settings are absent. No secret
  enters source, client bundles, logs, screenshots, or committed artifacts.

Extended test-author ownership:

- additive focused files under `triana-backend/tests/acceptance/**` and
  `triana-app/tests/**` only.

Extended implementation ownership:

- bounded changes to existing self-serve application/persistence/API/composition
  seams and one additive migration if durable analysis indexing requires it;
- bounded additions to the existing self-serve API types/client/components and
  agent/import routes; reuse `/analysis` report components and
  `ConversationViewer` rather than creating an unrelated UI;
- bounded CLI/SDK commands that call the same backend contract;
- existing Docker/Compose/deployment/configuration files and runbook checks only
  for deploy readiness. Actual external rollout is allowed only when the
  existing authorized environment supplies all required tenant/domain/secret
  choices and no new infrastructure, ingress, provider fallback, or spend above
  the existing USD 25 ceiling is required.

Still untouched: Release Review V1 and `triana-core/**`, provider retry/fallback,
locked holdout contents, raw customer data in git, destructive infrastructure,
new auth vendor/project creation, broad team/billing/admin features, and
unrelated cleanup or redesign.

Extended acceptance:

1. One fresh synthetic/customer-authorized file goes from authenticated agent
   upload through persisted canonical analysis and is reloadable after process
   restart without an operator-provided filesystem path.
2. Two agents and two owners prove list/detail/report/conversation/review
   isolation, including guessed cross-scope IDs and stale cached UI state.
3. Agent overview and run history reconcile import/source/report identities and
   deterministic accounting; retrying the same run is idempotent.
4. Overview, behavior/outcome, populations/evals, evidence, gaps/lineage, and
   label/review states are usable from real report data. Empty/absent semantic
   or outcome lanes remain explanatory typed states.
5. A correct Track/Edit/Defer ruling persists and a stale item hash leaves the
   ledger unchanged. No user is asked to label every trace.
6. CLI/SDK and UI retrieve the same agent/run/report/ruling identities.
7. Authenticated local smoke, schema migration/render, artifact/DB inspection,
   frontend build, container/config checks, and deployment preflight pass or
   expose one exact external configuration gate.

### Independent self-serve RED freeze — 2026-08-07

The independent test author owns exactly
`triana-backend/tests/acceptance/test_trace_to_eval_self_serve.py`, SHA-256
`bcd09e97ddc4804d265d1abb7c1cfbfeb2f548f78801f7341bbaa1975f69e720`.
Its ten cases freeze the authenticated upload `analysis` envelope, AVAILABLE
auto-run versus LOCKED/REQUESTED abstention, owner+agent idempotency and
cross-agent isolation, agent-scoped history, canonical report identity,
immutable report plus append-only review, stale-hash refusal, report evidence,
and cross-owner non-disclosure.

Observed RED is eight failures and two valid controls. The failures identify
only the missing authenticated upload-to-analysis bridge, history route, and
owned report/evidence routes. Existing self-serve/auth controls remain 7/7
GREEN; Ruff and diff checks pass. The frozen response is
`analysis: {feature_state, run}`, with `run: null` when analysis is not
AVAILABLE. Production may return a typed nonterminal state for a real
asynchronous run, but it may not omit the envelope, auto-run while locked, or
claim completion before a canonical report exists.

### Authenticated self-serve orchestrator exit — 2026-08-07

The test-author file remains byte-identical at
`bcd09e97ddc4804d265d1abb7c1cfbfeb2f548f78801f7341bbaa1975f69e720`.
The implementation author changed only the bounded backend persistence/API,
CLI, app report/navigation, and deployment-readiness surfaces; no migration or
new dependency was required. The orchestrator reconciled the production diff
against the extension budget and retained Release Review V1, `triana-core/**`,
provider fallback, holdouts, infrastructure creation, and unrelated UI/design
outside it.

Verified locally:

- 17/17 frozen auth/self-serve and bridge cases;
- 16/16 canonical Trace-to-Eval Labs cases;
- 38/38 non-live backend tests, with the exact environment-dependent HRAI live
  test deselected rather than reported as passing;
- backend Ruff and strict mypy over 34 source files;
- 5/5 focused app acceptance cases, TypeScript, and production Next build;
- deployment asset, content-secret, shell-syntax, and explicit-variable
  Compose configuration gates.

The implemented path is real rather than a placeholder: import responses carry
the entitlement-aware run, RDS indexes agent/import/run/report/artifact
identity, workspace SSE-KMS S3 stores source/report/review/conversation/ruling
bytes, the report route renders all five tabs using `ConversationViewer`, and
the authenticated CLI reads and rules the same backend objects. The default
self-serve execution deliberately supplies no semantic model, so a fresh trace
can truthfully produce structural behavior and empty semantic/review lanes with
typed gaps.

External exit evidence is incomplete. A private real-RDS/S3 smoke reached the
production service, then failed at the first `workspaces/*` `s3:PutObject`
because the existing EC2 runtime role covers only legacy prefixes. No source,
import, run, or report artifact was persisted in that attempt. The exact
non-delete additive policy is in `docs/SELF_SERVE_V0_RUNBOOK.md`. A real emailed
magic link and authenticated browser smoke also cannot run until an external
Supabase tenant supplies project/build/JWKS/public-origin configuration. These
are typed launch gates; they do not weaken the local product-loop evidence or
permit a less isolated storage path.

### Local replay and visible-product audit — 2026-08-07

After the integration commit, the orchestrator replayed a valid checked-in
synthetic PreviewTrace through all three local surfaces. Direct CLI, loopback
backend, and browser UI agreed on report
`sha256:328bc47d527fbf7c01d2c2546dd1c468710eb77decbe44f5ebc336db42f3191d`,
1/1 acceptance, three turns, observed tool activity, and the same five typed
gaps. The CLI artifacts are retained under
`/private/tmp/triana-cli-smoke-20260807`; report, queue, and conversation file
SHA-256 values are respectively
`6bfa4d605954375a1d6f55b917dda22d19d8ddbc0478cb8abd4cdec0d33ad7b6`,
`2deaeb31368f10ba872d27d61f3e721e9cb16b9bf4bbaefa1d10849aebec0d74`,
and `4cee94ac3e4158e100f95f30aebd30643cd2ca963b557ee2edc4d1e130576880`.

The browser then loaded retained controlled-semantic report
`sha256:33d050ea6fffd32dbcf4a0fb2f50751c0f0d4da2488236bd75ca5babe79acc19`:
12 conversations, three proposed populations, exactly three primary evals,
stable three-run test semantics, a bounded pair/eval review queue, and cited
`trace-01` DEVELOPMENT evidence rendered by `ConversationViewer`. This is a
test-model projection proof, not a new Azure result. No human ruling was
invented during the audit.

The subsequent read-only instance-role check again returned `AccessDenied` for
`s3:ListBucket` on the workspace prefix. No remote object write was attempted.

## Owner micro-slice: Foundry JSON-object compatibility and TAU handling patterns

Entry gate: **FROZEN 2026-08-07**. Akarsh selected handling and failure patterns
instead of first-broken-link/L4 for the immediate product and authorized a
bounded live TAU² semantic run using the existing HR-AI Azure configuration.
The first one-call synthetic preflight attempted exactly one request, reserved
USD 0.15, made no retry or fallback, and failed before a schema-valid result.
This isolates the provider wire rather than TAU data.

Repository evidence identifies the smallest falsifiable compatibility
hypothesis. HR-AI commit `9c00cae4576080174d0e741edd8af700c31bc4ca`
uses `ChatOpenAI(model, api_key, base_url)` directly against the Foundry
`/openai/v1` surface with no `api-version` query or duplicate `api-key` header.
Kairos-AI commit `a37e5c0760d8a49996381b93c26dcfa7599c3f5e`
uses `response_format={"type":"json_object"}` followed by deterministic JSON
and schema validation. Triana currently requests strict `json_schema` through
LangChain and adds the legacy query/header shape. The hypothesis is that this
wire—not trace semantics—is incompatible with the pinned GLM deployment.

Outcome: preserve the exact staged facet/consolidation Pydantic schemas and all
grounding, membership, qualification, stability, split, budget, no-retry,
no-fallback, and human-authority behavior while replacing only the provider
wire with HR-AI-compatible OpenAI-v1 JSON-object generation. Deterministic code
must parse and validate the returned JSON against the exact requested Pydantic
schema before any semantic row can enter a report. Provider content remains
untrusted proposal data.

Input/output authority:

- input remains the DEVELOPMENT-only trace projection plus stage and requested
  schema; calibration/holdout bodies remain unopened;
- the model may author only values conforming to the requested schema;
- deterministic code owns request byte/call/cost ceilings, parsing, strict
  schema validation, evidence substrings, membership, qualification, report
  identity, and typed failure;
- humans own population meaning, accepted taxonomy, eval acceptance/editing,
  and any reward mapping not supplied by the TAU harness;
- TAU official reward remains the only authoritative outcome joined in this
  run. Handling/failure patterns are observable/proposed categories, not causal
  first-broken-link judgments.

Privacy/execution: the exact verified TAU² archive is synthetic and already
authorized for the pinned `FW-GLM-5.2` provider. Execution and artifacts remain
local/private. No AWS write, deployment, Supabase, fallback provider/model,
retry, repair, raw provider response persistence, or secret output is allowed.
The cumulative Trace-to-Eval semantic reservation remains below USD 25.

Change budget:

- test author: one additive focused file under
  `triana-labs/tests/trace_to_eval/`, at most eight black-box cases;
- implementation author: only
  `triana-labs/src/triana_labs/trace_to_eval/semantic.py`, at most 150 changed
  physical lines;
- orchestrator: slice/decision/provenance/runbook evidence plus a bounded
  handling/failure-pattern report projection only after provider compatibility
  is GREEN;
- no dependency, schema migration, app redesign, backend/auth change, raw data,
  or unrelated cleanup.

Acceptance:

1. The Foundry client matches the HR-AI OpenAI-v1 connection shape and sends
   `response_format={"type":"json_object"}` with the requested JSON schema in
   the instruction; it sends no legacy `api-version`, duplicate `api-key`,
   retry, or fallback.
2. Valid JSON is strictly validated by the requested Pydantic model and then
   projected exactly as before. Invalid JSON, unknown/missing fields, or wrong
   types produce closed content-free failure codes and no semantic row.
3. Attempted/successful calls, usage when returned, reserved cost, and the
   most specific failure stage remain visible without response bodies or
   secrets; a generic outer failure cannot erase a specific wire/schema code.
4. Existing staged semantic, grounding, stability, review, and no-provider
   tests remain GREEN and frozen hashes remain unchanged.
5. Only after local GREEN, one new synthetic transport preflight may make one
   call. Only after that passes may one TAU² semantic run execute. Neither is a
   retry of the consumed failed request; each has a distinct stage/input and
   the same no-retry policy.
6. The resulting TAU report must reconcile 57 conversations and official
   39/18 outcomes, expose grounded populations plus at most three evals or
   exact typed gaps, and support a bounded review queue and cited
   ConversationViewer evidence without L4/causal language.

### Independent Foundry compatibility RED freeze — 2026-08-07

The independent test author owns exactly
`triana-labs/tests/trace_to_eval/test_foundry_json_object_compatibility.py`,
SHA-256
`a1c3370ff29128312ac7e4e2eafb09d44e463a3287e7a84b37c0907a764fc03b`.
Seven black-box cases freeze the HR-AI-compatible client constructor,
JSON-object response binding, canonical requested schema in the instruction,
strict local validation, closed JSON/content/schema/provider failure codes,
specific failure preservation, usage/attempt/success/reservation accounting,
and zero retry/fallback. No network or secret is used.

Observed RED is 7/7 failures at the exact legacy production seam:
`FoundryStructuredSemanticModel` still supplies `default_headers`,
`default_query`, and strict `json_schema` through `with_structured_output`.
There is no collection, fixture, syntax, import, network, or unrelated failure.
Ruff and diff checks pass. The frozen test may not be edited by the
implementation author.

### Provider GREEN and byte-bounded TAU batching correction — 2026-08-07

The independently implemented compatibility boundary passed all seven frozen
cases, all 23 Trace-to-Eval cases, Ruff, and mypy. A new one-call synthetic
preflight then passed on its first and only call with 356 input tokens, 121
output tokens, USD 0.15 reserved, no retry/fallback, and a schema-valid facet.

The authorized 57-conversation TAU run subsequently failed closed on its first
and only real facet request: zero successful calls, zero returned tokens, USD
0.15 reserved, `SEMANTIC_PROVIDER_CALL_FAILED`, and no retry/fallback. All 57
conversations and official 39/18 outcomes remained intact in deterministic
report `sha256:252aa7b0a175f4c8b85e0addfa87fa5f7848faae9712154c3b7a65dda54c4a9d`.
Local measurement falsifies a corpus or credential explanation: the fixed
12-trace batches serialize to 174,356, 125,499, and 119,509 payload bytes,
whereas the successful single-trace request is small. The next hypothesis is
that fixed record-count batching exceeds the pinned deployment's practical
context/request limit.

Frozen correction: facet extraction must greedily preserve trace order while
enforcing both the existing maximum 12 traces and a 60,000-byte canonical
request-content ceiling. A single trace that cannot fit must fail before a
provider attempt with `SEMANTIC_REQUEST_TOO_LARGE`; no truncation, splitting of
one conversation, retry, fallback, or silent omission is allowed. Accounting,
schemas, consolidation, evidence validation, and all product authority remain
unchanged.

Correction change budget:

- independent test author: one additive test file, at most five cases;
- implementation author: only
  `triana-labs/src/triana_labs/trace_to_eval/semantic.py`, at most 100 changed
  physical lines;
- orchestrator: append-only governance and local evidence records;
- no provider call until the new tests and full suite are GREEN; after GREEN,
  one distinct TAU analysis may run with at most 30 calls and USD 4.50 newly
  reserved, still without retry or fallback. This supersedes the preliminary
  15-call/USD 2.25 estimate: the GREEN batcher deterministically projects the
  34 DEVELOPMENT conversations into nine facet batches, so three independent
  semantic runs require `3 × (9 facet + 1 consolidation) = 30` calls. Exact
  planned batch sizes are 4/3/3/5/5/5/5/3/1 and all canonical request contents
  are at or below 59,856 bytes.

Independent acceptance is frozen in
`triana-labs/tests/trace_to_eval/test_semantic_byte_bounded_batching.py` at
SHA-256 `e7b48a860777ff97a2cab1626297e13bf8744633cf2483181c9737680bd0becd`.
Its three black-box cases cover greedy order/exactly-once preservation under
both ceilings, unchanged 12/12/1 small-corpus behavior, and pre-attempt refusal
for one oversized unit. Observed RED is the intended two failures: production
still sends the first 12 large units together and does not refuse one oversized
unit; the small-corpus compatibility case already passes. Ruff and diff checks
are GREEN.

The distinct two-trace content-free schema diagnostic then returned 8,329
input tokens and 771 output tokens and identified exactly two validation
errors: `facets[0].evidence_quotes` and `facets[1].evidence_quotes`, both
`too_long`. No response text, quote, value, trace content, or credential was
printed or persisted. The Pydantic schema permits at most three quotes, while
the system instruction required exact substrings but omitted the plain-language
cardinality. Freeze the next minimal correction: the instruction must require
**one to three** exact evidence substrings per facet. Strict schema validation
remains unchanged; code must not clip, repair, retry, or otherwise accept an
overlong list. Independent acceptance owns one additive focused test and the
implementation author may change only the prompt constant in `semantic.py`.

Independent acceptance is frozen in
`triana-labs/tests/trace_to_eval/test_facet_evidence_quote_prompt.py` at
SHA-256 `a59542994830cd8c1782b1ccbdfca1c3738d5684ee90a326d014e9fcae87e448`.
Its public-boundary case proves the requested schema still carries
`maxItems: 3` and observes valid RED only because the actual facet system
instruction lacks the exact one-to-three-per-facet guidance. Ruff and diff
checks pass.

### Validated semantic checkpoint and explicit resume correction — 2026-08-07

The cardinality-aligned TAU execution completed 25 schema-valid calls before
the 26th provider transport call failed. Lineage retained 26 attempts, 25
successes, 421,091 input tokens, 23,754 output tokens, USD 3.90 reserved, no
retry/fallback, and `SEMANTIC_PROVIDER_CALL_FAILED`; deterministic report
`sha256:5b6cbbd93b9585e2a53fb64ae9141b66909ce8cbbd5d6b64c6679ec314de9c41`
still preserved 57/57 conversations and official 39/18 outcomes. Because the
engine persisted no intermediate validated stages, one late transport failure
discarded all 25 usable responses. This is a product-integrity and cost hole,
not evidence that the population analysis is wrong.

Freeze the correction: each schema-valid semantic stage result is persisted
locally under the run output directory using an identity derived
deterministically from model id, stage, system instruction, canonical payload,
and requested schema. A subsequent **explicit invocation** of the same run may
reuse only an exact-identity, strict-schema-valid checkpoint and call the
provider only for missing stages. There is no automatic retry loop; failed
responses are never cached; raw provider responses are never persisted;
corrupt, mismatched, or schema-invalid checkpoints fail closed and never become
provider success. Lineage separates provider attempts/successes/tokens/cost
from validated checkpoint hits and declares
`resume_policy=EXPLICIT_VALIDATED_CHECKPOINTS_ONLY`.

Checkpoint change budget:

- independent test author: one additive file, at most six black-box cases;
- implementation author: only `trace_to_eval/semantic.py` and
  `trace_to_eval/__init__.py`, at most 180 changed physical lines;
- orchestrator: governance/evidence and explicit local run invocation;
- no dependency, UI/backend/auth/schema migration, provider fallback,
  automatic retry, holdout opening, raw response persistence, or remote write.

Acceptance covers exact cache identity, valid hit with zero provider attempt,
strict corrupt/mismatch refusal, successful-write-only behavior, lineage
separation, output-directory binding, and all existing Trace-to-Eval tests.

Independent acceptance is frozen in
`triana-labs/tests/trace_to_eval/test_semantic_validated_checkpoints.py` at
SHA-256 `280b8fc4288d9d8a86b381af442d7fbd8058e15f837dd306be096efcc60d29d6`.
Four test functions/six cases cover first-run exact checkpoint artifacts and
raw-response exclusion; zero-provider exact resume plus one-missing-stage
execution; failed-stage exclusion; and corrupt, mismatched, or schema-invalid
closed refusal. Observed RED is six failures solely because production has no
checkpoint binding/artifacts/lineage yet. Ruff and diff checks pass.
