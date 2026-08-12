# Triana public alpha — repository and install release slice

Date: 2026-08-11
Status: **AUTHORIZED; ENTRY GATE FROZEN**
Parent: `internal/TRIANA_PUBLIC_GATE_1_SESSION_PACKET_2026-08-11.md`

## Outcome

Make the verified Gate 1 snapshots usable from a fresh session for a later
50-conversation ABCD trial. This slice may create public GitHub repositories,
initialize clean Git histories, publish the exact Preview alpha package, and
verify the pinned skill journey. It does not execute ABCD traces or make a
provider call.

GitHub Actions test matrices are explicitly deferred. A minimal release-only
workflow is allowed only if PyPI Trusted Publishing requires it and no existing
local PyPI credential is available; it is release transport, not general CI.

## Input and output contract

Inputs are the Gate 1 canonical snapshots at:

- `/Users/akarshgajbhiye/triana-preview`
- `/Users/akarshgajbhiye/triana-skills`

Outputs are two clean Git histories and public GitHub repositories, an exact
installable `triana-preview==0.1.0a1` candidate when publication credentials
permit, one validated install path for the `onboard` skill, and a content-free
new-session handoff for the later authorized ABCD subset.

## Authority and refusal

Deterministic code owns package bytes, hashes, command exits, call counts,
custody checks, and report verification. The skill supplies instructions only.
The future operator owns trace authorization, provider-egress authorization,
the exact 50-conversation subset, and provider credentials. No model or human
ruling is created in this slice.

Stop publication rather than weakening a pin, using ambient credentials,
printing a secret, bypassing Git branch protections, or claiming an unrun clean
install. Provider calls, customer traces, Docker publication, hosted uploads,
telemetry, CI matrices, semantic changes, and monorepo cleanup are excluded.

## Change budget

Preview repository: Git metadata and release/install corrections within
`README.md`, `pyproject.toml`, `uv.lock`, `.github/workflows/release.yml`,
`src/**`, and `tests/**` only when a reproduced clean-install or `uvx` blocker
requires the smallest repair. Runtime dependencies remain frozen.

Skills repository: Git metadata and corrections within manifests,
`plugins/triana/skills/onboard/**`, public documents, and its frozen tests only
when validation or forward use proves a contract defect. No scripts or runtime
code may be added.

Private monorepo: this packet, `internal/SLICE_PACKET.md`, canonical governance
documents required by an executed durable decision, and ignored decision
memory. Existing dirty implementation files remain untouched.

External effects authorized by Akarsh: public GitHub repository creation and
push for `triana-preview` and `triana-skills`, plus TestPyPI/PyPI publication of
the verified Preview alpha. Repository deletion, force-push, secret creation,
provider egress, customer-data reads, and authenticated-console automation are
not authorized.

## Acceptance

1. Gate 1 frozen suites remain green after any correction.
2. The exact Preview candidate installs into a fresh Python 3.13 environment.
3. Local published-style `uvx --python 3.13 --from ... triana-preview --help`
   succeeds without the monorepo on `PYTHONPATH`.
4. Skill validators pass and a fresh agent can derive the safe no-provider
   onboarding path from only the public skill.
5. Both repositories contain only their allowlisted inventories and have clean
   Conventional Commit histories with authenticated public remotes.
6. Any TestPyPI/PyPI artifact is hash-related to the accepted build and installs
   by exact version. If credentials or name ownership block publication, record
   the exact human action and do not claim success.
7. No ABCD trace or provider call occurs.

## Local release evidence — 2026-08-11

Status: **LOCAL GREEN; EXTERNAL AUTHENTICATION REQUIRED**.

Preview was rebuilt from the permanent snapshot with no source edit. The exact
artifacts remain:

- wheel SHA-256
  `ca4d644bc70a87d0c93b832b14f32e34f59097bf0898b965518acc18ceed773a`;
- sdist SHA-256
  `12cb1b579a49e95276f9da14f6f6d5f21ccf64d1c1a71045fb71ba2473b838bd`.

A fresh Python 3.13.14 environment installed the wheel and 36 public
dependencies, `uv pip check` passed all 37 installed distributions, and the
installed package resolved from that environment rather than the monorepo. A
published-style exact-wheel `uvx` invocation passed help, synthetic
no-provider analysis (`COMPLETED_WITH_GAPS`, exit 10, zero provider calls), and
report verification (`VERIFIED_WITH_GAPS`, exit 0).

The Skills README now contains exact Codex and Claude marketplace/install
commands for `Triana-AI/triana-skills`. The skill clarifies stdout receipts,
first-resolution package-index access, scaffold outputs, and exact report
filenames. Seven contract cases, Skill Creator validation, and both official
Claude validators pass without warnings. Independent fresh-session review
confirmed the authorization and six-stage workflow is derivable without
private context.

Clean local Git histories now exist on `release/0.1.0a1`:

- Preview commit `0b202f16d010bd08ba34053fea7fcc1a19694423`;
- Skills commit `9535bc26b571839252f0f2f55c5b57a4392f4e56`.

The non-main branch prevents the checked-in deferred CI workflows from running.
Both worktrees are clean. PyPI and TestPyPI currently return 404 for the exact
project name, consistent with no existing published project at verification
time. `uv publish --dry-run` accepted both artifact paths; no local PyPI token
is configured.

The first sandboxed GitHub check reported inaccessible keyring tokens and
correctly stopped before remote mutation. The continuation below supersedes
that preliminary diagnosis after an approved keyring-visible check. No package
upload occurred during the preliminary check.

## Public repository continuation — 2026-08-11

The prior authentication failure was sandbox/keyring isolation, not an expired
owner session. An approved keyring-visible check confirmed active account
`akar5h` is an active `Triana-AI` administrator with the required repository and
workflow scopes.

The following repositories are public with `release/0.1.0a1` as their default
branch and the exact local commits as their remote heads:

- `https://github.com/Triana-AI/triana-preview` at `0b202f16d010bd08ba34053fea7fcc1a19694423`;
- `https://github.com/Triana-AI/triana-skills` at `9535bc26b571839252f0f2f55c5b57a4392f4e56`.

No configured CI matrix ran because both workflows target `main`; GitHub's
built-in dependency-graph indexing is not the repository CI workflow. The
public Preview ref installed successfully through clean `uvx`, resolving the
exact commit and 37 packages before returning CLI help. The public Skills
marketplace and `triana@triana-skills` plugin version `0.1.0` were installed and
enabled in Codex from the exact release ref.

A secret-free GitHub environment named `pypi` now exists. Final package
publication waits only for the owner to register PyPI pending Trusted Publisher
fields: project `triana-preview`, owner `Triana-AI`, repository
`triana-preview`, workflow `release.yml`, environment `pypi`. No package upload
has occurred.

## Final publication evidence — 2026-08-11

Status: **RELEASE GREEN; READY FOR FRESH-SESSION TRIAL**.

The first release run stopped before building because the frozen repository
inventory test did not exclude the checkout's required `.git` metadata. The
smallest reproduction showed 30 passing cases and one extra-name failure. The
falsifiable hypothesis was that `.git` is checkout metadata rather than a
public artifact; the original test author added only `.git` to the transient
set. The focused test and 31/31 suite passed, the artifact hashes remained
unchanged, and commit `10bcbca0e7c47ffc2324248af9a100e244454033`
was pushed to the non-main release branch.

Two initial PyPI exchanges returned `invalid-publisher` while all four visible
publisher fields matched GitHub's signed claims. Recreating the exact pending
publisher removed the stale/hidden mismatch. Release run
`https://github.com/Triana-AI/triana-preview/actions/runs/31468675330`
then passed build, 31 tests, artifact upload, OIDC exchange, and PyPI upload.
The Node 20-to-24 action compatibility notices were non-failing warnings.

PyPI now serves `triana-preview==0.1.0a1` with:

- wheel SHA-256
  `ca4d644bc70a87d0c93b832b14f32e34f59097bf0898b965518acc18ceed773a`,
  71,823 bytes;
- sdist SHA-256
  `12cb1b579a49e95276f9da14f6f6d5f21ccf64d1c1a71045fb71ba2473b838bd`,
  65,123 bytes;
- Python `>=3.13,<3.14` and only direct dependencies `pydantic>=2,<3`
  and `langchain-openai==1.4.0`.

A fresh PyPI-only `uvx` cache installed 37 distributions and completed the
public skill's synthetic no-provider path: help/inspect/validate/preview exit
0; analyze exit 10 with `COMPLETED_WITH_GAPS` and zero provider calls; report
verification exit 0 with `VERIFIED_WITH_GAPS`. No ABCD data, credential,
provider call, or semantic claim was used in release verification.
