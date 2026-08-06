# SELF-SERVE-V0 launch slice packet

Date frozen: 2026-08-06

Status: **ACTIVE — CONTRACT FROZEN; WORKER EDITS AUTHORIZED**

Slice ID: `SELF-SERVE-V0-TRACE-INGESTION`

Canonical base: `ba44e8e8aa9c253601ae3938ab1021a4f9b54978` on `main`.

Integration branch: `codex/selfserve-v0`.

## Product outcome

Ship the smallest hosted self-serve loop:

```text
authenticated owner
  -> create an agent
  -> upload one prescribed PreviewTrace JSONL file
  -> inspect deterministic accepted/rejected accounting
  -> browse every accepted conversation in a reusable viewer
```

Analysis, simulation, reports, model/provider calls, teams, billing, adapters,
and HRAI-specific ingestion are not part of this launch.

## Frozen contract

- Managed OIDC authentication; the backend independently verifies bearer JWTs.
- First login creates one personal workspace. Clients never choose a workspace.
- One agent has a display name and one immutable default version.
- One multipart `.jsonl` upload, maximum 16 MiB, 1,000 physical lines, and
  1 MiB per line. One physical line is one PreviewTrace conversation.
- Hosted uploads use the truthful `CUSTOMER_AUTHORIZED_TRACE_DATA` privacy
  class, require explicit owner attestation, remain private, and have no LLM or
  other provider egress.
- The server streams bytes, computes SHA-256, stores the source privately under
  a workspace-scoped immutable key, validates deterministically, and persists
  accepted conversation indices plus safe rejection metadata.
- Terminal import states are `COMPLETED`, `COMPLETED_WITH_REJECTIONS`, and
  `FAILED`. Zero accepted records cannot be `COMPLETED`.
- The generic conversation viewer renders normalized messages, tool calls,
  tool results, terminal events, and typed gaps. The existing report UI uses a
  legacy adapter; uploaded traces do not pretend to be generated reports.

## Public behavior

| Request | Success | Refusal/failure |
|---|---|---|
| `GET /api/v1/me` | owner + personal workspace | 401 invalid authentication |
| `POST /api/v1/agents` | creates agent + default version | 409 duplicate; 422 invalid |
| `GET /api/v1/agents` | owner-scoped list | 401 |
| `GET /api/v1/agents/{id}` | owned agent | non-disclosing 404 |
| `POST /api/v1/agents/{id}/imports` | validated import summary | 413/415/422/typed 503 |
| `GET /api/v1/agents/{id}/imports` | stable import history | non-disclosing 404 |
| `GET /api/v1/imports/{id}` | status and exact counts | non-disclosing 404 |
| `GET /api/v1/imports/{id}/conversations` | ordered accepted records | non-disclosing 404 |
| `GET /api/v1/imports/{id}/rejections` | safe line errors | non-disclosing 404 |
| `GET /api/v1/conversations/{id}` | imported conversation projection | non-disclosing 404 |

## Authority, privacy, and refusal

- Deterministic code owns hashing, identity, line accounting, validation,
  ordering, tool linkage, status, pagination, and tenant scoping.
- The authenticated human attests authorization to upload and owns the agent
  name. No human ruling or accepted behavior is created.
- No LLM participates in this slice.
- Raw traces are private customer data. Logs and errors exclude payloads,
  authorization headers, object keys, and parser exception text.
- Invalid lines are typed rejections; invalid authentication, ownership,
  configuration, unsafe storage, or broken integrity aborts the operation.
- Exact hosting region, DNS, and managed OIDC vendor are deployment
  configuration, not evidence semantics. Production launch requires them.

## Provenance

Implementation is newly authored in Triana. The existing repository-local
PreviewTrace validator, Observer limits, storage ports, UI tokens, and report
conversation visuals may be refactored. No external repository or HRAI code,
schema, fixture, trace, or prose may be copied.

## Parallel slices and ownership

### Backend slice

Test-owned:

- `triana-backend/tests/self_serve/**`

Production-owned:

- `triana-backend/migrations/versions/0002_*.py`
- `triana-backend/src/triana_backend/auth/**`
- `triana-backend/src/triana_backend/api/**`
- `triana-backend/src/triana_backend/application/**`
- `triana-backend/src/triana_backend/artifacts/**`
- `triana-backend/src/triana_backend/domain/**`
- `triana-backend/src/triana_backend/persistence/**`
- `triana-backend/src/triana_backend/{composition,config}.py`
- backend package and lock files only for JWT and multipart support
- `triana-labs/src/triana_labs/contracts/traces.py`

RED command:

```text
uv run pytest -q tests/self_serve
```

### Frontend and reusable-viewer slice

Test-owned:

- `triana-app/tests/self-serve-ui.test.mjs`

Production-owned:

- `triana-app/app/(self-serve)/**`
- `triana-app/app/login/**`
- `triana-app/app/agents/**`
- `triana-app/components/self-serve/**`
- `triana-app/components/conversation/**`
- `triana-app/lib/self-serve/**`
- exact existing conversation route/component changes required for the legacy
  adapter
- `triana-app/components/AppNav.tsx`
- `triana-app/app/globals.css`

RED command:

```text
npm test -- --test-name-pattern self-serve
```

The test author runs before the implementation author in each isolated
worktree. The two slices may proceed in parallel after this packet. Workers
stop before touching another lane or shared canonical documentation.

## Minimal acceptance gate

1. Backend black-box test: authenticated owner creates an agent, uploads a
   two-conversation valid JSONL file, and reads both conversations.
2. Backend boundary test: a mixed-validity upload reports exact accepted and
   rejected counts without exposing raw rejected content.
3. Backend isolation test: another authenticated owner cannot list or read the
   first owner's agent, import, or conversation.
4. Frontend contract test: login, agent creation, upload, import accounting,
   and a conversation timeline are reachable and render typed failure states.
5. Existing report conversation rendering remains available through its
   adapter.
6. Typecheck/build and repository governance pass on the integrated commit.

No coverage target, broad historical suite expansion, provider test, queue,
load test, visual-regression suite, or analysis test is required.

## Required adversarial spot checks

- empty and oversized upload;
- all lines rejected;
- invalid JWT and cross-workspace identifier;
- duplicate idempotency key with changed bytes;
- orphan tool result or missing terminal rendered as a typed gap;
- large tool payload is collapsed and React-escaped.

## Explicit non-goals and untouched areas

- `triana-core/**`
- Labs case factory, intelligence, adaptive runner, simulation, and report
  generation
- HRAI compiler and private retained-report workflow
- analysis, cases, runs, review mutation, teams, billing, SSO, API keys,
  deletion/retention automation, provider settings, queues, and adapters
- cloud mutation or deployment before the integrated local gate is green

No scope expansion beyond one JWT/JWKS dependency and multipart parsing is
permitted without orchestrator review. No worker edits canonical documents,
deployment files, package-wide formatting, or unrelated tests.

## Exit verification

```text
./scripts/verify-governance.sh
cd triana-backend && uv run pytest -q tests/self_serve
cd triana-backend && uv run ruff check src tests/self_serve
cd triana-backend && uv run mypy src
cd triana-app && npm test -- --test-name-pattern self-serve
cd triana-app && npm run typecheck
cd triana-app && npm run build
```

The orchestrator additionally inspects the integrated diff, one real
57-conversation prescribed-format upload if supplied locally, logs for payload
leakage, and the visible browser path. Unrun checks remain unverified.
