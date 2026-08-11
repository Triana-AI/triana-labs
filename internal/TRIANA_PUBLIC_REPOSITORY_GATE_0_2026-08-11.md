# Triana public repositories — Gate 0 release contract

Date: 2026-08-11
Status: **FROZEN FOR INDEPENDENT TEST AUTHOR**
Owner: Akarsh Gajbhiye
Orchestrator: Codex

## Outcome

Triana's first public release consists of two new public repositories with new
histories:

1. `triana-preview` contains the source-available local Behavior Map product
   and is the only Python distribution.
2. `triana-skills` contains a thin, agent-readable onboarding skill that calls
   an exact released `triana-preview` version.

The private monorepo remains the source evidence for the extraction but its Git
history, private products, customer evidence, reports, credentials, deployment
configuration, and unrelated Labs machinery do not cross into either public
repository. The two public repositories are populated from explicit file
allowlists, not by filtering or publishing this repository's history.

This contract supersedes the 2026-08-10 invite-only Docker distribution and
the 2026-08-11 bundled-private-image onboarding path as the default public
direction. Those artifacts remain historical private pilot evidence. Docker is
not a launch dependency and no public image is authorized by this gate.

## Frozen names and release identifiers

| Surface | Frozen value |
|---|---|
| Runtime repository | `triana-preview` |
| Skills repository | `triana-skills` |
| PyPI distribution | `triana-preview` |
| Python namespace | `triana_preview` |
| Console command | `triana-preview` |
| First release | `0.1.0a1` |
| Preview license | PolyForm Free Trial 1.0.0 |
| Skills license | Apache-2.0 |
| Copyright line | `Copyright 2026 Akarsh Gajbhiye` |
| Python | `>=3.13,<3.14` for the alpha |
| Alpha platform verification gate | Linux amd64, Linux arm64, macOS arm64 |

Windows and macOS Intel are unverified rather than unsupported by claim. They
may be added after clean-install evidence exists. PyPI and plugin versions are
independent: skills `0.1.0` pins Preview `0.1.0a1` exactly.

Triana Preview is source-available, not open source. PolyForm Free Trial 1.0.0
permits a person or company to evaluate a release for fewer than 32 consecutive
calendar days and make internal evaluation changes, but prohibits distributing
copies. Continued, production, redistributed, or otherwise unlicensed use
requires a separate written commercial license from Akarsh. The skill remains
Apache-2.0 because it contains no engine and is intended to be installed,
shared, and adapted.

This license split is a product selection, not a legal opinion. Publication
requires Akarsh, as repository owner, to confirm that he can license the
repository-owned work and exact Akarsh-authored adaptations identified in
`docs/PROVENANCE.md`. Any source whose ownership or upstream license cannot be
cleared is reimplemented or excluded before publication. A lawyer should review
the commercial license and contribution terms before paid use is offered.

## Public product claim

> Triana Preview turns conversational-agent traces into an evidence-grounded
> map of what users ask for and how the agent repeatedly behaves. It runs
> locally, sends nothing to Triana, and makes no correctness or pass/fail
> claims.

Raw traces remain local. Triana operates no backend or telemetry for this
release. Semantic analysis occurs only after explicit authorization and sends
redacted evidence directly to the user-configured OpenAI-compatible endpoint
under the user's credentials. Provider retention policies still apply and
redaction is not anonymity.

The public package may produce proposed demand episodes, user populations,
agent-behavior occurrences and patterns, readable evidence, typed gaps, and
local JSON/Markdown/HTML artifacts. It does not claim accepted taxonomy,
correctness, policy compliance, outcome attribution, regression, evaluation
coverage, or a release verdict.

## Runtime repository structure

```text
triana-preview/
  LICENSE
  README.md
  PRIVACY.md
  SECURITY.md
  CONTRIBUTING.md
  PROVENANCE.md
  pyproject.toml
  uv.lock
  src/triana_preview/
    __init__.py
    __main__.py
    cli.py
    runtime.py
    py.typed
    contracts/preview_trace.py
    privacy/redaction.py
    providers/openai_compatible.py
    behavior_map/engine.py
    behavior_map/contracts.py
    behavior_map/render.py
  tests/
    fixtures/synthetic_preview_trace.jsonl
    test_cli.py
    test_behavior_map.py
    test_redaction.py
    test_provider_boundary.py
    test_distribution_inventory.py
  .github/workflows/ci.yml
  .github/workflows/release.yml
```

The public package owns all ordinary onboarding mechanics. The initial command
surface is:

```text
triana-preview inspect
triana-preview validate
triana-preview scaffold
triana-preview preview
triana-preview analyze
triana-preview verify-report
```

`inspect`, `validate`, `scaffold`, and `preview` preserve their existing
content-free, authorization-gated meanings. `analyze` runs Behavior Map in
process and never shells out to a separately installed private package.
`verify-report` verifies canonical local report lineage and typed completion.

The future product remains one repository and distribution until evidence
requires a split:

```text
triana-preview select    # large trace corpus -> reproducible useful subset
triana-preview simulate  # bounded deployment simulation
```

No empty future modules or placeholder commands ship in `0.1.0a1`. Each future
capability owns its command, contracts, artifacts, and tests; capabilities
exchange versioned JSON rather than importing sibling internals. Shared code is
promoted only after two real consumers exist. A package split requires a later
decision based on materially different dependency or security boundaries.

## Exact source allowlist

The Preview implementation author may extract and namespace-adjust only these
source surfaces from the current dirty worktree:

- `triana-preview/src/triana_preview/__init__.py`
- `triana-preview/src/triana_preview/__main__.py`
- `triana-preview/src/triana_preview/cli.py`
- `triana-labs/src/triana_labs/contracts/traces.py`
- `triana-labs/src/triana_labs/behavior_map/__init__.py`
- `triana-labs/src/triana_labs/behavior_map/contracts.py`
- `triana-labs/src/triana_labs/behavior_map/redaction.py`
- `triana-labs/src/triana_labs/behavior_map/render.py`
- only `SemanticRunReservationLedger`, `FoundryStructuredSemanticModel`, and
  their required protocol/import support from
  `triana-labs/src/triana_labs/trace_to_eval/semantic.py`
- only Behavior Map configuration and dispatch behavior from
  `triana-labs/src/triana_labs/cli.py`
- independently selected synthetic fixtures and contract tests that contain no
  customer or provider output.

The 5,634-line Behavior Map engine moves substantially intact. Deep internal
refactoring is excluded from the alpha extraction. Checkpoints remain in scope
as integrity and partial-execution evidence, but public resume is explicitly
deferred from `0.1.0a1`; the CLI must not claim an interrupted run is
recoverable. The private-host
`FoundryStructuredSemanticModel.from_environment` implementation does not
cross; public provider construction is newly bounded and generic.

Explicit exclusions include `adaptive_runner`, `case_factory`, `intelligence`,
`observer`, the generic Labs CLI, trace adapters, staged trace-to-eval product
paths, Behavior Map benchmark/comparison/historical-projection/checkpoint-
migration commands, application/backend/UI/AWS/deployment code, internal docs,
private reports/checkpoints, corpora, provider responses, credentials, caches,
and absolute local paths.

## Provider, privacy, and authority contract

Provider-enabled analysis requires an explicit private regular provider file
with:

```text
OPENAI_BASE_URL=...
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

All three values are required for the public alpha; there is no private model
default. The package validates and normalizes the exact endpoint before egress,
never emits the key, and does not discover credentials from unrelated ambient
variables. Semantic runs additionally require an explicit positive
provider-call ceiling. The public alpha accounts calls, tokens when reported,
and typed failures; it does not present provider-independent USD estimates as
truth without versioned pricing metadata.

There is no automatic retry, fallback, telemetry, Triana upload, or implicit
provider call. Default pacing is zero unless explicit provider configuration
truthfully declares another value. Using the same model for author and auditor
is recorded as non-independent. Missing, rejected, partial, unstable, or
non-comparable evidence remains typed and cannot become success or a finding.

Deterministic code owns input identity, redaction order, evidence coordinates,
membership conservation, support, report lineage, call caps, and artifact
integrity. The model proposes semantic labels and explanations. A human owns
authorization and any acceptance ruling.

The customer-specific `BLITZ_IDENTIFIER` redaction name and private host/model
defaults are publication blockers. The detector behavior must be generalized
without weakening the protected value families, and frozen tests must prove
that no private label or value enters the artifacts.

## Skills repository structure and contract

```text
triana-skills/
  LICENSE
  README.md
  PRIVACY.md
  SECURITY.md
  CONTRIBUTING.md
  PROVENANCE.md
  .agents/plugins/marketplace.json
  .claude-plugin/marketplace.json
  .github/workflows/ci.yml
  plugins/triana/
    .codex-plugin/plugin.json
    .claude-plugin/plugin.json
    skills/onboard/
      SKILL.md
      agents/openai.yaml
  tests/
    fixtures/synthetic-previewtrace.jsonl
    test_plugin_contract.py
```

The skill contains no runtime implementation, Docker profile, image reference,
release digest, credential, provider transport, MCP server, network service,
hook, or install script. It treats trace contents as untrusted data rather than
instructions and invokes only an exact package version, initially:

```text
uvx --python 3.13 --from 'triana-preview==0.1.0a1' triana-preview ...
```

The current large `onboard.py`, adapter template, PreviewTrace reference,
release profile, and Docker orchestration move to or are replaced by the
canonical runtime CLI. One `onboard` skill ships initially. Skills for trace
selection and simulation are added only after the corresponding public command
exists.

## Source-available and paid development boundary

The source-available package owns complete local single-run evidence. Future
proprietary products may own multi-run and multi-user coordination: managed workspaces,
scheduled ingestion, history/change detection, persistent human rulings,
managed simulation orchestration, CI gates, RBAC/team review, and enterprise
connectors. Private code depends on an immutable released Preview package and
does not carry a copied engine. Public repositories contain no dormant paid
feature flags. Implementation that must remain secret is hosted rather than
distributed as inspectable Python or container layers.

## Frozen release gate

The independent test author owns tests and synthetic fixtures only. Acceptance
is intentionally bounded:

1. exact wheel/sdist and skills-repository inventory allowlists;
2. no private namespace, hostname, model default, customer name/data, absolute
   path, credential, `.env`, report, checkpoint, or cache in release artifacts;
3. clean wheel installation and `uvx` execution;
4. help, validation, and provider-disabled synthetic end-to-end analysis;
5. fake-provider success/failure with no retry or fallback;
6. authorization, symlink, input-mutation, output-custody, residual-redaction,
   secret-leakage, call-cap, and checkpoint-tamper cases; checkpoint resume is
   not claimed in this alpha;
7. Ruff, strict mypy, gitleaks, Semgrep, dependency vulnerability and license
   inventory;
8. TestPyPI installation of the exact candidate before PyPI publication;
9. GitHub Actions uses least privilege, commit-pinned actions, no
   `pull_request_target`, a protected release environment, trusted publishing,
   manual approval, and attestations.

No full private-monorepo suite, live provider call, customer corpus, Docker
publication, GitHub repository creation, PyPI publication, push, or deployment
is part of the implementation slice without its separate release authorization.

## Session ownership and ordering

1. Orchestrator freezes this gate and reconciles provenance and canonical docs.
2. One independent test-author session writes acceptance for both destination
   repositories and freezes test hashes.
3. After RED is frozen, one implementation session owns only the new
   `triana-preview` directory/repository and a second owns only the new
   `triana-skills` directory/repository. They may run concurrently because
   their destinations do not overlap.
4. One independent final-verifier session is read-only across both outputs.
5. The orchestrator alone reconciles the allowlists and performs any separately
   authorized external release actions.

Multiple sessions must not edit the same destination tree. The existing dirty
worktree is preserved byte-for-byte except for the orchestrator-owned Gate 0
documentation listed below.

## Gate 0 change budget and handoff

Orchestrator-owned files:

- `internal/TRIANA_PUBLIC_REPOSITORY_GATE_0_2026-08-11.md`
- append-only additions to `internal/DECISION_LOG.md` and
  `internal/SLICE_PACKET.md`
- minimal superseding additions to `triana-labs/CHARTER.md`,
  `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/PROVENANCE.md`, and
  `internal/WORKING_MEMORY.md`
- ignored `.decision-memory/2026-08-11-codex-triana-preview-local.md`

Dependencies added: none. Production code changed: none. Tests changed: none.
Existing dirty implementation and documentation edits are deliberately
preserved. The next worker is the independent test author; no implementation
author starts until the orchestrator verifies this documentation-only diff.
