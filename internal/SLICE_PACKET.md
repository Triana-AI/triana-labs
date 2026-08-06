# SELF-SERVE-V0 magic-link and feature-entitlement slice

Date frozen: 2026-08-06

Status: **ACTIVE — CONTRACT FROZEN; WORKER EDITS AUTHORIZED**

Slice ID: `SELF-SERVE-V0-MAGIC-LINK-ENTITLEMENTS`

Canonical base: `902f0fd` on `codex/selfserve-v0`.

## Product outcome

Replace the developer JWT-paste scaffold with open email magic-link login and
add a backend-owned feature gate for gradual rollout:

```text
email -> magic link -> authenticated personal workspace -> core features
locked feature -> request access -> REQUESTED state
```

There is no signup waitlist or manual approval before using trace ingestion and
the conversation viewer.

## Frozen authentication contract

- Supabase Auth supplies passwordless email magic links and JWT sessions.
- The login form accepts an email and calls `signInWithOtp`; it never reveals
  whether an account previously existed.
- Supabase may create the user automatically. `shouldCreateUser` remains true.
- The magic-link confirmation route exchanges the token/code for a session and
  redirects through the feature gate to `/agents`.
- The browser obtains the current Supabase access token and sends it through
  the existing same-origin `/api/v1` proxy. The FastAPI backend continues to
  verify issuer, audience, expiry, subject, and signature through JWKS.
- No password, homegrown token, service-role key, auth admin API, invite, or
  approval workflow is introduced.
- Auth routes and responses are private/no-store. Logout clears the managed
  session.

## Frozen authorization contract

RBAC and rollout entitlements are separate:

- V0 membership role remains `OWNER`; teams and additional roles are deferred.
- Deterministic backend code owns a closed feature catalog and workspace
  entitlement state.
- Public states are `AVAILABLE`, `LOCKED`, and `REQUESTED`.
- Default available: `TRACE_INGESTION`, `CONVERSATION_VIEWER`.
- Default locked: `ANALYSIS`, `SIMULATION`, `TEAM_COLLABORATION`, `API_ACCESS`.
- A request for a locked feature is owner-scoped and idempotently creates one
  `REQUESTED` record. It does not auto-grant the feature and does not block core
  product access.
- Grant/revoke administration is deliberately deferred; initial grants may be
  applied by a controlled operator/database migration later.
- UI gates improve clarity only. Every future protected backend endpoint must
  call the backend entitlement boundary before work or data access.

## Public API additions

| Request | Success | Refusal |
|---|---|---|
| `GET /api/v1/me/features` | closed catalog with state per feature | 401 |
| `POST /api/v1/me/access-requests` | requested feature becomes `REQUESTED` | 401/404 unknown feature/409 already available |

Existing authenticated self-serve APIs and tenant isolation remain unchanged.

## Authority and privacy

- Supabase Auth owns email delivery and session issuance.
- The backend owns authorization and never trusts a client feature state.
- Deterministic code owns feature keys, defaults, request identity, and state.
- A human requests access; that request is not an entitlement grant.
- Email addresses are not copied into Triana persistence in this slice; the
  existing hashed OIDC subject remains the local user identity.
- No trace-data or LLM/provider egress is added.

## Parallel slices and change budget

### Backend entitlements

Test-owned:

- `triana-backend/tests/self_serve/test_feature_entitlements.py`

Production-owned:

- `triana-backend/migrations/versions/0003_*.py`
- `triana-backend/src/triana_backend/api/{contracts,routes}.py`
- `triana-backend/src/triana_backend/application/**`
- `triana-backend/src/triana_backend/persistence/{models,self_serve}.py`

No dependency is permitted.

RED command:

```text
uv run pytest -q tests/self_serve/test_feature_entitlements.py
```

### Frontend magic link and access gates

Test-owned:

- `triana-app/tests/magic-link-access.test.mjs`

Production-owned:

- `triana-app/app/{login,auth,agents}/**`
- `triana-app/components/self-serve/**`
- `triana-app/lib/{self-serve,supabase}/**`
- `triana-app/components/AppNav.tsx`
- `triana-app/package.json`
- `triana-app/package-lock.json`
- `triana-app/next.config.ts` only if no-store/auth routing requires it

Permitted dependencies: current compatible `@supabase/supabase-js` and
`@supabase/ssr`, with exact versions locked.

RED command:

```text
node --test --test-name-pattern=magic-link tests/magic-link-access.test.mjs
```

Each slice runs independent test author then implementation author. Backend and
frontend may proceed in parallel in isolated worktrees after this packet.

## Minimal acceptance

1. New authenticated owner receives both core features as `AVAILABLE` and the
   four staged features as `LOCKED` without an approval record.
2. Requesting `ANALYSIS` twice yields one owner-scoped request and stable
   `REQUESTED` state; another owner remains `LOCKED`.
3. Unknown features refuse and available features cannot be requested.
4. Login submits an email magic link with open signup, never accepts a pasted
   bearer token, and provides neutral check-your-email feedback.
5. Confirmation establishes the managed session; API requests use its access
   token and logout clears it.
6. The UI shows available/locked/requested states and a working request-access
   control without hiding core trace ingestion.
7. Existing self-serve ingestion/viewer focused tests, typecheck, and build
   remain green.

## Edge cases

- invalid/expired/replayed magic link;
- email enumeration through differing success text;
- duplicate request clicks and concurrent request creation;
- cross-workspace feature/request reads;
- unknown/removed feature key;
- stale UI entitlement after request;
- missing Supabase public configuration;
- refresh/logout followed by an API call;
- redirect target injection; only local fixed destinations are allowed.

## Non-goals

- approval queue/admin UI;
- invite-only signup or signup waitlist;
- teams, member invites, additional roles, SSO, SCIM, billing, paid plans;
- automatic entitlement grants, percentage rollout, experiments, or flags from
  an external feature-flag vendor;
- analysis or simulation implementation;
- cloud/provider project creation or secrets in Git.

## Exit commands

```text
./scripts/verify-governance.sh
cd triana-backend && uv run pytest -q tests/self_serve
cd triana-backend && uv run ruff check src tests/self_serve
cd triana-backend && uv run mypy src
cd triana-app && node --test tests/self-serve-ui.test.mjs tests/magic-link-access.test.mjs
cd triana-app && npm run typecheck
cd triana-app && npm run build
```
