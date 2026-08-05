# LABS-08 HRAI backend acceptance

`test_labs08_hrai_vertical_slice.py` is the smallest shipping gate for the
first backend-backed Labs report. It deliberately uses the complete tracked
HRAI `run_200` source in place; no trace bytes or secrets are checked into this
repository.

The values most likely to change while the HLD/LLD is frozen—CLI spelling,
API paths, and SQL schema/table names—live only in
`labs08_hrai_contract.json`. Changing that fixture is a contract change and
must return to the independent test-author lane; production authors must not
edit the test to fit their implementation.

## Required environment

- `TRIANA_ACCEPTANCE_DATABASE_URL`: a disposable PostgreSQL database with the
  production migrations applied.
- `TRIANA_ACCEPTANCE_SOURCE_S3_URI`: a private object containing the exact
  source bytes, uploaded before the test with SSE-KMS and SHA-256 object
  metadata.
- `TRIANA_ACCEPTANCE_API_ORIGIN`: optional; defaults to
  `http://127.0.0.1:8000` and must address the running FastAPI service.
- `TRIANA_ACCEPTANCE_WORKSPACE_SLUG`: optional; defaults to `local`.

The backend test environment must include its locked `boto3`, `psycopg`, and
test dependencies. The test neither provisions nor destroys AWS or RDS
resources. The infrastructure lane owns creation and teardown of disposable
acceptance resources.

Run from `triana-backend`:

```text
uv run pytest -q tests/acceptance/test_labs08_hrai_vertical_slice.py
```

The paired UI contract is
`triana-app/tests/labs08-backend-ui.test.mjs`. It calls the TypeScript data
loader with a deterministic backend response and a connection failure; it
does not start a browser or duplicate report arithmetic.

## What this one gate proves

1. The source bytes still have the frozen hash, 200 physical records, 186
   `COMPLETED`, 14 `HARNESS_ERROR`, and 186 usable conversations.
2. S3 contains exactly those bytes under SSE-KMS rather than a reconstructed
   UI fixture.
3. A normal repeated import and run reuse their immutable identities;
   `--rerun` creates a distinct DBOS workflow/run attempt without changing the
   source import.
4. RDS relates the source artifact, import, deterministic analysis facts, run,
   run artifacts, and report without silently defaulting unavailable values to
   zero.
5. FastAPI returns the canonical report artifact body itself and one exact raw
   HRAI source record, with the same IDs, counts, evidence class, and hashes.
   When the report contains a retained Labs execution conversation, its
   standalone endpoint must return a value-equivalent member with report
   lineage.

## Explicitly deferred test infrastructure

The first ship does not add a broad load, chaos, migration-rollback,
cross-region, browser, auth, multi-tenant, provider, queue-concurrency, or
disaster-recovery suite. Those remain backlog.

The implementation must still fail closed with typed states. In particular:

- malformed JSONL or a source hash mismatch cannot create a completed run;
- missing report/source objects return `ARTIFACT_UNAVAILABLE` for the affected
  run and never turn into a pass, zero, or fabricated report;
- an affected artifact does not make unrelated reports unavailable;
- a partial RDS/S3 publication is not visible as a completed report;
- raw conversations are available only through the trusted SSH-tunneled API
  boundary selected for this no-auth demo.

These behaviors require focused component tests during implementation. Only
the first source-to-UI value-flow gate is required for the initial ship.
