# Self-serve V0 launch runbook

Status: local implementation complete; live Supabase and infrastructure
unverified.

## Delivered path

```text
email -> magic link -> /auth/confirm -> /agents
-> add agent -> upload PreviewTrace JSONL
-> import accounting -> conversation list -> reusable conversation viewer

locked feature -> request access -> REQUESTED
```

Signup is open: a valid email can create a Supabase user without a Triana
waitlist or approval. The authenticated personal workspace starts with trace
ingestion and the conversation viewer available. Analysis, simulation, team
collaboration, and API access remain locked but requestable; requesting access
does not grant it.

The backend validates the Supabase JWT, scopes all objects and feature state to
the authenticated owner's workspace, stores source bytes under a private
workspace S3 key, and persists only accepted conversation projections plus
safe rejection metadata. It does not run analysis, simulation, HRAI
compilation, or LLM calls.

## Supabase project configuration

1. Create or select a Supabase project and keep email signup enabled.
2. Configure Site URL to the public Triana app origin and add the exact allowed
   redirect `https://<app-origin>/auth/confirm` (plus the equivalent local URL
   only for development).
3. Configure the email provider and the magic-link email template for the PKCE
   confirmation flow. Do not add a signup approval or invite-only gate.
4. Use asymmetric JWT signing keys. The backend supports `RS256` and `ES256`;
   a legacy symmetric project with no usable public JWKS is not launchable with
   this verifier.
5. Record the project URL and publishable key in the deployment secret/config
   system. Never put a Supabase service-role key in the app.

Relevant provider documentation:

- <https://supabase.com/docs/reference/javascript/auth-signinwithotp>
- <https://supabase.com/docs/guides/auth/server-side/advanced-guide>
- <https://supabase.com/docs/guides/auth/jwts>

## Backend configuration

Required self-serve environment:

```text
TRIANA_DATABASE_URL=postgresql+psycopg://...
TRIANA_ARTIFACT_BUCKET=...
TRIANA_KMS_KEY_ID=arn:aws:kms:...
AWS_REGION=...
TRIANA_OIDC_ISSUER=https://<project-ref>.supabase.co/auth/v1
TRIANA_OIDC_AUDIENCE=<the project's authenticated-user JWT audience>
TRIANA_OIDC_JWKS_URL=https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
TRIANA_BACKEND_HOST=0.0.0.0
TRIANA_BACKEND_PORT=8000
```

Confirm issuer and audience from an actual project-issued access token; do not
copy placeholders blindly. All three `TRIANA_OIDC_*` values are required
together. When configured, the self-serve runtime does not launch DBOS.

Back up the live database, then apply the schema before starting the new image:

```text
cd triana-backend
uv run alembic upgrade head
```

The expected Alembic head is `0003_feature_entitlements`.

## App configuration

The browser bundle requires these public values:

```text
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<publishable-key>
```

They are public client configuration, not service credentials, but Next embeds
them at build time. The current `triana-app/Dockerfile` and deploy workflow do
not pass these values into the build stage. Do not launch that image until the
deployment path supplies them during `npm run build` and verifies they are
present in the resulting login flow.

Set the backend origin only on the Next server/runtime:

```text
TRIANA_BACKEND_API_ORIGIN=http://backend:8000
```

The browser calls same-origin `/api/v1`; Next proxies it internally. Do not
publish the backend host in a `NEXT_PUBLIC_*` variable.

## Feature access contract

| Feature | New workspace state | Requestable now |
|---|---|---|
| Trace ingestion | `AVAILABLE` | No need |
| Conversation viewer | `AVAILABLE` | No need |
| Analysis | `LOCKED` | Yes |
| Simulation | `LOCKED` | Yes |
| Team collaboration | `LOCKED` | Yes |
| API access | `LOCKED` | Yes |

Requests are idempotent and change `LOCKED` to `REQUESTED`; they never grant
access. V0 has only the `OWNER` membership role. There is intentionally no
admin grant UI, billing tier, team role, percentage rollout, or external flag
service in this slice.

## Trace contract

- filename ends in `.jsonl`;
- one physical line is one `preview_trace` schema-version-1 conversation;
- privacy class is `CUSTOMER_AUTHORIZED_TRACE_DATA`;
- 16 MiB per file, 1,000 physical lines, 1 MiB per line;
- the uploader attests ownership or authorization;
- invalid lines produce content-free line/code/pointer/safe-message records;
- zero accepted conversations is `FAILED`, never success.

## Launch gate

1. Complete the Supabase project, redirect, email, asymmetric signing, and app
   image build-time configuration above.
2. Back up the database and apply Alembic revision `0003`.
3. Verify private SSE-KMS upload and immutable workspace keying.
4. Use a real emailed link as owner A, confirm `/auth/confirm` establishes a
   session, add an agent, upload a mixed-validity JSONL file, request analysis,
   and observe `REQUESTED` after refresh.
5. Log out, prove the old session cannot call an API, and prove an expired or
   replayed link fails without exposing raw provider errors.
6. Log in as owner B and prove an empty agent list, default feature states, and
   non-disclosing 404s for owner A's identifiers.
7. Upload the prescribed-format 57-conversation corpus and reconcile every
   physical line.
8. Verify TLS, server-only backend routing, logs without payloads/tokens, and a
   rollback to the preceding image and database backup.
