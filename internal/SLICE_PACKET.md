# TAU57 non-auth DBOS behavior dry-run slice

Date frozen: 2026-08-06

Status: **COMPLETE — LIVE PRIVATE CANARY VERIFIED**

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

## Exit evidence — 2026-08-06

- Exact archive export: 57 PreviewTrace records, 745,960 bytes, SHA-256
  `f757851296f1770248623e274f20c18ea8bd0dff34a1a4910ae199c78db1447d`.
- Private staging: bucket `triana-artifacts-854847082059-ap-south-1`, SSE-KMS,
  checksum `91eFEpbxdwJIYj4nTyDBjqi9Df80oaSRCuGZx42xRH0=`.
- Import: `imp_37e742f4d6947028cd167c4a52478c50`; artifact
  `art_529a16c5b9da207979c0013294b98f4c`; 57 physical, 57 accepted,
  zero rejected.
- RDS was observed at Alembic `0001_labs08_storage` and was transactionally
  upgraded through the already-reviewed migrations to
  `0003_feature_entitlements (head)`.
- Live failures were retained rather than hidden: attempt 1 exposed the stale
  schema; attempt 2 exposed the removed artifact conflict target; attempt 3
  exposed duplicate PreviewTrace rejection facts. Independent RED regressions
  and bounded production corrections protect the latter two failures.
- Successful DBOS attempt 4: run `run_6e99b23c29175715b5d1ba5a18761b4c`,
  workflow `labs08-run-8e8b1b297b4e0fe3d21ca9186fa68df4dba103f75c9ff353e2dfb55de0ab7562`,
  report `rpt_70718d7e6cfe538b5a99bc4a44bb536c`, state
  `COMPLETED_WITH_GAPS`.
- Canonical report: 57 physical, 57 accepted, zero rejected, 54 structural
  groups, support total 57, share total 10,000 basis points, deterministic
  membership and descriptions, `population_claim=NOT_ESTABLISHED`, provider
  `NONE`.
- Deployed digests: backend
  `sha256:c24dc75b3359c39c0afe2e7ddf1ce80c2a423447bbfa566df3ff04060d753c38`;
  app `sha256:8b54879a915764e2bc23966188c70bf4215f3c72433679a8ccccf3edf40f169c`;
  release SHA `0d4407946d86ef0d9888de2fb961ded4b51b8156`.
- Production containers, backend readiness, canonical report reads, and
  `/behavior` passed on-host and through refreshed local SSM tunnels. The UI
  visibly renders deterministic descriptions and nonzero observed groups.
- Focused integrated acceptance passed 17/17; exporter, compiler, UI,
  TypeScript, Next production build, Ruff, and mypy checks passed during the
  independently owned implementation and reconciliation steps.

No LLM/provider/target call, semantic population claim, auth bridge, new
infrastructure, or public ingress was introduced. The temporary host ECR-push
statement may now be removed; the runtime requires ECR pull only.
