# Self-serve V0 launch runbook

Status: local implementation complete; live infrastructure unverified.

## Delivered path

```text
/login -> /agents -> add agent -> upload PreviewTrace JSONL
-> import accounting -> conversation list -> reusable conversation viewer
```

The backend validates OIDC JWTs, scopes all new objects to the authenticated
owner's personal workspace, stores source bytes under a private workspace S3
key, and persists only accepted conversation projections plus safe rejection
metadata. It does not run analysis, simulation, HRAI compilation, or LLM calls.

## Backend configuration

Required self-serve environment:

```text
TRIANA_DATABASE_URL=postgresql+psycopg://...
TRIANA_ARTIFACT_BUCKET=...
TRIANA_KMS_KEY_ID=arn:aws:kms:...
AWS_REGION=...
TRIANA_OIDC_ISSUER=https://...
TRIANA_OIDC_AUDIENCE=...
TRIANA_OIDC_JWKS_URL=https://.../.well-known/jwks.json
TRIANA_BACKEND_HOST=0.0.0.0
TRIANA_BACKEND_PORT=8000
```

All three `TRIANA_OIDC_*` values are required together. When configured, the
self-serve runtime does not launch DBOS.

Apply the schema before starting the new image:

```text
cd triana-backend
uv run alembic upgrade head
```

## App configuration

Set only the server-side backend origin:

```text
TRIANA_BACKEND_API_ORIGIN=http://backend:8000
```

The browser calls same-origin `/api/v1`; Next proxies it internally. Do not
publish the backend host in a `NEXT_PUBLIC_*` variable.

The current login page accepts a real provider-issued JWT and keeps it only in
the current tab's session storage. Before a public launch, replace this visible
developer scaffold with the selected provider's hosted login/magic-link
redirect. The backend JWT verification and authorization boundary stay the
same.

## Trace contract

- filename ends in `.jsonl`;
- one physical line is one `preview_trace` schema-version-1 conversation;
- privacy class is `CUSTOMER_AUTHORIZED_TRACE_DATA`;
- 16 MiB per file, 1,000 physical lines, 1 MiB per line;
- the uploader attests ownership or authorization;
- invalid lines produce content-free line/code/pointer/safe-message records;
- zero accepted conversations is `FAILED`, never success.

## Launch gate

1. Configure the managed OIDC tenant and hosted login.
2. Back up the database and apply Alembic revision 0002.
3. Verify private SSE-KMS upload and immutable workspace keying.
4. Log in as owner A, add an agent, upload a mixed-validity JSONL file, and
   inspect both accounting and an accepted conversation.
5. Prove owner B receives an empty agent list and non-disclosing 404s for owner
   A's identifiers.
6. Upload the prescribed-format 57-conversation corpus and reconcile every
   physical line.
7. Verify TLS, server-only backend routing, logs without payloads/tokens, and a
   rollback to the preceding image and database backup.
