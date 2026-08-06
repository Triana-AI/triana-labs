# TAU57 non-auth DBOS behavior dry-run slice

Date frozen: 2026-08-06

Status: **ACTIVE — CONTRACT FROZEN; TEST AUTHOR AUTHORIZED**

Slice ID: `TAU57-NONAUTH-DBOS-BEHAVIOR-DRYRUN`

Canonical base: `83d3e9e` on `codex/selfserve-v0`.

## Product outcome

Prove the non-authenticated analysis core independently of signup:

```text
verified local TAU² 57-task archive
-> deterministic PreviewTrace JSONL adapter
-> private S3 registration
-> real foreground DBOS workflow
-> deterministic structural behavior groups
-> RDS/S3 canonical report
-> /behavior through the private SSM tunnel
```

This is a private operator dry run. It does not grant the self-serve
`ANALYSIS` entitlement or connect authenticated uploads to analysis.

## Exact input

- archive:
  `triana-experiments/tau2-luna-local/runs/downloads/tau2-retail-discovery-v1/2788f37e3fa215548319be116dd1f5b47e70e04b188919e460441ed993a98169.tar.gz`;
- archive SHA-256:
  `2788f37e3fa215548319be116dd1f5b47e70e04b188919e460441ed993a98169`;
- expected task bundles: 57;
- evidence/privacy class: `SYNTHETIC`;
- custody: raw archive stays gitignored; generated PreviewTrace JSONL may exist
  only under `/private/tmp` and private SSE-KMS S3.

## Frozen behavior contract

- The adapter reads only each completed attempt's `tau2-results.json` from the
  verified archive and emits one schema-version-1 `preview_trace` per task.
- Message order is preserved. User/assistant messages and assistant tool calls
  become the corresponding PreviewTrace events; tool results bind in FIFO
  order to the preceding unresolved call because TAU² omits result call IDs.
- Adapter identity, archive hash, task ID, attempt ID, and reward remain
  lineage. Reward is not accepted behavior or a Triana ruling.
- Deterministic grouping uses only observable event-kind and ordered tool-name
  structure. It owns membership, support, group identity, denominator, and
  basis points.
- Group labels and summaries are structural descriptions authored by
  deterministic code. `semantic_summary_authority` is not MODEL_PROPOSED and
  `population_claim` remains `NOT_ESTABLISHED`.
- No model/provider/target call, semantic user-need inference, case generation,
  simulation, aggregate verdict, or human ruling occurs.
- Malformed archives, missing/duplicate tasks, invalid PreviewTrace events,
  hash mismatch, mixed privacy, incomplete denominators, S3/KMS failure, or
  DBOS/compiler failure refuse visibly and cannot create an available report.

## Infrastructure boundary

- AWS profile: `akarsh-deepprobe` / account `854847082059` / region
  `ap-south-1`.
- Reuse running EC2 `i-0f8250d908737b568`, available encrypted RDS `db-pg-1`,
  existing private S3/KMS/ECR configuration, and SSM-only access.
- No Terraform or new infrastructure is authorized because the required
  runtime exists.
- Mutations are limited to one private input object, content-addressed output
  artifacts, application rows/DBOS history, new digest-addressed images, and a
  reversible deployment on the existing Triana host.

## Change budget

Independent test ownership:

- `triana-experiments/tau2-luna-local/tests/test_preview_trace_export.py`
- `triana-labs/tests/report/test_preview_trace_behavior.py`
- `triana-backend/tests/acceptance/test_tau_behavior_pipeline.py`
- `triana-app/tests/labs08-backend-ui.test.mjs` only by additive sibling test;
  the frozen existing test itself remains unchanged.

Implementation ownership:

- `triana-experiments/tau2-luna-local/scripts/export_preview_trace.py`
- `triana-labs/src/triana_labs/report/**`
- `triana-backend/src/triana_backend/{domain,application,services,workflows}/**`
- `triana-backend/src/triana_backend/composition.py`
- `triana-app/app/behavior/page.tsx`
- `triana-app/lib/labs-report.ts` only if required to represent deterministic
  structural authority without widening the report contract.

No dependency or migration is permitted. Self-serve auth, membership,
entitlements, upload/viewer routes, Supabase code, and cloud provisioning are
explicitly untouched.

## Minimal acceptance

1. Exact archive exports 57 valid, ordered, unique synthetic PreviewTrace
   records reproducibly; malformed/missing/duplicate task bundles refuse.
2. Compiler accounting reconciles `physical = accepted + rejected` and emits
   stable structural group IDs, ordered membership, support, and basis points.
3. No report field claims semantic populations, model-written summaries,
   accepted behavior, or a verdict.
4. Existing HRAI accounting compilation remains unchanged and keeps zero
   behavior groups.
5. Real dry run persists the new import/run/report through S3, RDS, and DBOS;
   ordinary repeat converges idempotently.
6. `/behavior` renders the new report over SSM with visible nonzero groups and
   deterministic-authority copy; no fixture fallback occurs.

## Worker protocol and exit

Exactly one independent test author freezes RED acceptance first. Exactly one
implementation author then works against those bytes. The orchestrator alone
integrates, runs the real AWS canary, reconciles the change budget, and records
the final verdict.

Local gates:

```text
cd triana-experiments/tau2-luna-local && uv run --frozen pytest -q tests/test_preview_trace_export.py
cd triana-labs && uv run --locked pytest -q tests/report/test_preview_trace_behavior.py
cd triana-backend && uv run pytest -q tests/acceptance/test_tau_behavior_pipeline.py
cd triana-backend && uv run ruff check src tests && uv run mypy src
cd triana-app && npm run typecheck && npm run build
./scripts/verify-governance.sh
```
