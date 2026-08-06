# LABS-08 backend-backed HRAI vertical slice

Date reconciled: 2026-08-05

Status: **COMPLETE — ENTRY-GATE MISS DISCLOSED; RECONCILIATION AND LIVE EXIT GATES GREEN**

Slice ID: `LABS08-HRAI-RDS-S3-REPORT-V1`

Canonical base: `08a8338` on `codex/labs-07-08-app-boundary`.

Integration branch: `codex/labs08-integration`.

## Process disclosure

The LABS-08 architecture, independent acceptance contract, and initial
production lanes began while this file still contained the closed LABS-06
packet. That violated the required entry-gate order. This packet records the
actual accepted owner decisions, completed parallel lanes, observed diff, and
remaining blockers. It does not retroactively claim that implementation was
properly authorized by the stale packet. No image deployment or HRAI upload may
proceed until the exit gate below is green.

## Product outcome

Store the authorized HRAI `run_200` corpus in private SSE-KMS S3, register its
identity and deterministic Labs-owned facts in a new `triana` PostgreSQL
database on the existing RDS instance, serve the report and retained records
through the private backend, and render only backend-served values in Triana
App.

The source contract is fixed:

- evidence class: `SYNTHETIC_EXISTING_TRACE_CORPUS`;
- SHA-256: `76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b`;
- 200 physical records;
- 186 `COMPLETED` usable conversations;
- 14 `HARNESS_ERROR` typed incomplete records.

## Input and output contracts

Input:

1. exact hash-verified HRAI normalized JSONL staged in private S3;
2. explicit workspace, agent, agent version, evidence class, and idempotency
   identity;
3. operator calls through `/api/v1` over a private tunnel.

Output:

1. content-addressed SSE-KMS S3 source, fact, and report artifacts;
2. PostgreSQL import, version, run, fact, artifact, and report lineage;
3. deterministic ordinary idempotency and distinct explicit rerun attempts;
4. canonical report, raw retained record, and retained conversation APIs;
5. Triana App pages that fail closed when the configured backend report is
   unavailable and never substitute the bundled fixture.

## Authority and refusal behavior

- Triana Labs owns deterministic source accounting, fact identity, rejected
  evidence, lineage, and any later semantic analysis.
- The backend owns orchestration, persistence, artifact verification, workflow
  state, versioned API projection, and typed availability. It may copy stored
  Labs facts but may not invent labels, cases, outcomes, costs, human rulings,
  or release truth.
- DBOS owns durable workflow identity and replay history, not evidence meaning.
- An LLM may propose only the fields allowed by the Labs charter after explicit
  provider egress authorization. No provider call is required for the initial
  retained HRAI accounting import.
- A human owns persistent rulings. None are created by this slice.
- Missing, corrupt, or KMS-inaccessible artifacts degrade only their dependent
  import/report. Missing compiler capability is `LABS_ANALYSIS_NOT_READY`, not
  a pass or fabricated report.

## Privacy and execution location

- App, FastAPI, and DBOS run on one EC2 host.
- App and API bind to loopback and are reached only through an approved private
  tunnel. Ports 3000, 8000, and 5432 are never public.
- RDS remains private. S3 blocks public access and uses SSE-KMS.
- AWS instance roles and GitHub OIDC replace committed/static AWS credentials.
- No `.env`, private key, raw corpus, transcript, provider body, IDE file, or
  internal experiment artifact may be committed or included in images.

## Frozen deployment boundary

Initial launch uses one ARM64 EC2 host, Docker Compose, the existing RDS
instance with a new logical `triana` database, private S3, KMS, ECR, Azure
OpenAI as the primary provider adapter, and explicit OpenRouter selection only.

Initial non-goals: ECS, ALB, Lambda, SQS, Redis, Temporal, Terraform,
application authentication, public HTTP, multi-tenancy behavior, automatic
provider fallback, autoscaling, and high availability.

## Change budget and ownership

Architecture/orchestration ownership:

- `docs/BACKEND_ARCHITECTURE.md`
- `docs/AWS_SINGLE_EC2_RUNBOOK.md`
- `internal/DECISION_LOG.md`
- `internal/SLICE_PACKET.md`

Independent test ownership:

- `triana-backend/tests/acceptance/**`
- `triana-app/tests/labs08-backend-ui.test.mjs`

Storage implementation ownership:

- `triana-backend/migrations/**`
- `triana-backend/src/triana_backend/{application,artifacts,domain,persistence}/**`
- backend package/lock files and operator CLI only as required by those ports

Workflow/API/composition implementation ownership:

- `triana-backend/src/triana_backend/{api,services,workflows}/**`
- `triana-backend/src/triana_backend/{composition,config,main}.py`

Labs compiler ownership:

- `triana-labs/src/triana_labs/report/**`

UI implementation ownership:

- `triana-app/lib/labs-report.ts`
- directly dependent Labs route/page/component files
- `triana-app/next.config.ts`

Deployment implementation ownership:

- `.github/workflows/{ci,deploy}.yml`
- `compose.production.yaml`
- `ops/**`
- `triana-{app,backend}/{Dockerfile,.dockerignore}`

Maximum allowed scope expansion is one separately reviewed reconciliation
commit limited to closing verifier P0/P1 defects inside these paths. New
dependencies require lock updates and direct justification. Provider adapters,
auth, billing, multi-tenancy, unrelated UI redesign, historical experiment
cleanup, and data copies are outside this budget.

## Completed independent checkpoints

- CP0 monorepo App base: `08a8338`.
- CP1 architecture author: `49d4fbf`, integrated as `b3ca03f`.
- AWS/CI read-only audit: `3b56aa6`, integrated as `4b53e9e`.
- CP2 independent tests: `ead2408`, reconciled by `62eef47`, integrated as
  `29e9b3a`.
- CP3 storage author: `88df881`, integrated as `acdc662`.
- CP4/CP5 workflow/API author: `72486ef`, integrated as `cb2d1aa`.
- CP6 UI author: `4685d0a`, integrated as `206f5d9`.
- CP7 deployment author: `07f1485`, integrated as `dbe639b`.
- Production composition author: `4e2f034`, integrated as `1aca5bb`.
- Labs deterministic compiler author: `2eced25`, integrated as `c76cd9b`.
- Independent integration verdict at `1aca5bb`: RED; deployment prohibited.

## Mandatory reconciliation before deployment

1. expose a real module-level ASGI app and align runtime environment names;
2. make the first Alembic migration bootstrap an empty database;
3. integrate the Labs compiler and persist its facts/rejected evidence/lineage;
4. publish a canonical report artifact whose schema is accepted by the real UI;
5. record 14 rejected/incomplete records consistently, never zero;
6. remove guaranteed CI failures and add package typing metadata;
7. verify report body identity/hash before serving and localize conversation
   artifact failures;
8. separate App and Backend environment/secret surfaces;
9. reconcile DBOS migration/runtime privileges and prove foreground recovery;
10. reconcile S3 KMS identity, artifact-kind keying, and acceptance restoration;
11. close or explicitly defer provider caching because no provider call is in
    the initial retained-accounting path;
12. choose and document a safe tunnel/deployment mechanism before EC2 launch.

## Reproducible exit gate

The slice exits only when all are true:

1. governance, decision journal, diff, Ruff, formatting, strict mypy, Python
   compilation, migration bootstrap, UI typecheck/build, and deployment asset
   checks pass;
2. independent offline operator and UI no-fallback acceptance are green;
3. backend and App ARM64 images build from committed files;
4. RDS/S3/KMS resources are exact, private, and migrated by an operator step;
5. the exact HRAI source imports once, repeats idempotently, and explicit rerun
   creates a distinct attempt;
6. RDS stores exact 200/186/14 accounting and Labs fact lineage;
7. source, report, and conversation APIs return the stored identities and
   localize a missing report artifact without breaking another healthy read;
8. the App visibly renders the backend report and does not import or fall back
   to `data/labs-report.json`;
9. no raw data, `.env`, key, secret, internal experiment, or IDE file is staged;
10. an independent verifier returns GREEN with exact commands and artifacts.

Any failed item remains RED or typed partial evidence. No check may be reported
as passing unless it ran against the integrated commit.

## Exit reconciliation

The owner-authorized private AWS launch completed on 2026-08-05 without
opening public ingress. The exact hash-pinned 200-record HRAI source was stored
in the private SSE-KMS bucket, imported through the DBOS-backed workflow into
the new `triana` logical database on the existing RDS instance, and rendered
by Triana App exclusively through the backend API over an SSM tunnel.

- Import: `imp_0bf658de16aed56774fbb1bea8412989`
- Run: `run_f574721d8995265acf6c6b1e6b899696`
- Report: `rpt_183d311b5111fb8bb4b7100d13131148`
- Stored accounting: 200 physical, 186 completed/usable, 14 harness errors
- Report artifact hash:
  `017baeea69046d2e582a9ec47590f5d7a0058e7b45a27320bc939134a69d1ec2`

Offline governance, deployment-asset, secret, decision-memory, backend P0/P1,
App no-fallback, TypeScript, container-build, and live S3-to-RDS-to-DBOS-to-API-
to-UI checks passed. CI was then made Linux-portable without changing product
semantics: current `uv` installs the exact frozen Python, `/private/tmp` is
created explicitly for Labs' private-custody contract, and the App job runs
the active LABS-08 backend/no-fallback acceptance rather than superseded
fixture/static-export suites. No LLM call was made in the retained import.
