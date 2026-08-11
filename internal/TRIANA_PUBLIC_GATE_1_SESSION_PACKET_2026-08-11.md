# Triana public alpha — Gate 1 session packet

Date: 2026-08-11
Status: **FROZEN FOR TWO INDEPENDENT TEST AUTHORS**
Parent contract: `internal/TRIANA_PUBLIC_REPOSITORY_GATE_0_2026-08-11.md`

## Gate 1 outcome

Freeze two non-overlapping acceptance contracts so Preview and Skills can be
implemented concurrently afterward. Gate 1 changes tests and synthetic
fixtures only. It does not copy production code, publish, call a provider, or
touch the existing dirty monorepo implementation.

Staging roots:

- `/private/tmp/triana-public-alpha-20260811/triana-preview`
- `/private/tmp/triana-public-alpha-20260811/triana-skills`

After independent RED and implementation pass, the orchestrator copies only
the verified allowlisted snapshots into the already-created permanent local
repository directories:

- `/Users/akarshgajbhiye/triana-preview`
- `/Users/akarshgajbhiye/triana-skills`

No GitHub repository, PyPI project, tag, push, or public release is created in
Gate 1.

## Decisions closed before session split

### Preview command wire

The console program is `triana-preview`. Every trace-reading command requires
`--confirm-authorized-traces`.

```text
triana-preview inspect \
  --source TRACE.jsonl --confirm-authorized-traces

triana-preview validate \
  --source TRACE.jsonl --output VALIDATED.jsonl \
  --confirm-authorized-traces

triana-preview scaffold \
  --source RAW.jsonl --output-dir EMPTY_DIR \
  --confirm-authorized-traces

triana-preview preview \
  --source TRACE.jsonl --confirm-authorized-traces

triana-preview analyze \
  --traces TRACE.jsonl --agent DESCRIPTION --output EMPTY_DIR \
  --confirm-authorized-traces --no-provider

triana-preview analyze \
  --traces TRACE.jsonl --agent DESCRIPTION --output EMPTY_DIR \
  --provider-env PRIVATE_0600_FILE --max-provider-calls POSITIVE_INTEGER \
  --confirm-authorized-traces --confirm-provider-egress

triana-preview verify-report \
  --output-dir REPORT_DIR --confirm-authorized-traces [--require-semantic]
```

`--no-provider` and `--provider-env` are mutually exclusive and one is
required. A provider-enabled run requires `--max-provider-calls`; a
provider-disabled run rejects it. The public provider file requires exactly
nonempty `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`, allows
comments/blank lines, rejects duplicates and unknown keys, must be a private
non-symlinked regular file, and is read directly without a derived environment
file. The base URL must be absolute HTTPS, preserve its path, and contain no
userinfo, query, or fragment.

There is no provider/model/pacing/USD default, ambient credential discovery,
automatic retry, fallback, telemetry, update check, or Triana network request.
The explicit call ceiling is run-wide across author and auditor attempts. The
same configured model may serve both roles but is labeled non-independent.

### CLI results and exit behavior

- `0`: requested deterministic operation or semantically completed report;
- `10`: analysis completed with typed gaps and retained valid artifacts;
- `2`: authorization, input, configuration, privacy, custody, integrity, or
  unsupported-command refusal;
- `1`: unexpected internal failure with content-free diagnostics.

Stdout is one canonical JSON result/receipt. Safe diagnostics go to stderr.
Neither stream contains trace values, provider values, secrets, absolute local
paths, internal `TRIANA_BEHAVIOR_MAP_*` names, private hosts/models, hashes of
raw unredacted values, or stack traces by default.

### Preview dependencies and implementation latitude

Runtime dependencies are limited to:

```text
pydantic>=2,<3
langchain-openai==1.4.0
```

Full `langchain`, `langgraph`, `triana-labs`, network clients beyond the
transitive OpenAI transport, and new runtime dependencies are refused. Python
is `>=3.13,<3.14`. The Behavior Map engine moves substantially intact; tests
must not require a deep refactor or a stable Python library API beyond the CLI
and artifact contracts.

The Preview license is the unmodified PolyForm Free Trial 1.0.0 text. Package
metadata must describe it as source-available and must not use an OSI-approved
license classifier. Copyright is Akarsh Gajbhiye. Legal text itself is
implementation-owned; the test author checks presence and truthful metadata,
not legal interpretation.

### Skills command and trust wire

Every executable example in the skill begins with:

```text
uvx --python 3.13 --from 'triana-preview==0.1.0a1' triana-preview
```

There is exactly one runtime version across the repository. The skill asks for
trace path, short agent description, explicit trace authorization, and either
explicit no-provider mode or private provider file plus provider-egress
authorization and maximum provider calls. It performs inspect, adapt only when
required, validate, preview, analyze, verify, and return-report.

The Skills license is Apache-2.0. The repository contains no executable helper
script, adapter template, duplicated validator, Docker reference/profile,
image/digest, MCP server, app, hook, binary, symlink, `curl`, `wget`, telemetry,
background service, internal environment variable, or provider implementation.
Trace content is explicitly untrusted evidence and cannot override the skill.

### Snapshot and publication boundary

The two local staging roots are independent repository snapshots. Test authors
may inspect the private monorepo but write only their assigned staging
`tests/**` and synthetic fixtures. Customer data, private reports, provider
responses, checkpoints, credentials, private endpoint/model names, and source
absolute paths are forbidden in fixtures and expected values.

## Session A — Preview test author

Ownership:

- `/private/tmp/triana-public-alpha-20260811/triana-preview/tests/**` only.

Required frozen acceptance:

1. six-command help and exact argument contract;
2. PreviewTrace validate byte preservation and typed invalid input;
3. explicit provider-disabled synthetic analysis with local typed gaps;
4. fake-provider success and one-attempt failure with zero retry/fallback;
5. authorization, HTTPS/provider-file permissions, symlink, duplicate/unknown
   provider key, call-cap, input mutation, nonempty output, residual redaction,
   hostile rendering, checkpoint tamper, and secret/path leakage refusals;
6. canonical report verification and exit `0/10/2/1` mapping;
7. clean wheel/sdist inventory and no private namespace/value scan;
8. runtime dependency allowlist and source-available license metadata.

The test author may combine cases to keep the suite small. Tests use only
synthetic values and fakes. Valid RED must fail because production is absent,
not because tests do not collect or contain syntax errors.

## Session B — Skills test author

Ownership:

- `/private/tmp/triana-public-alpha-20260811/triana-skills/tests/**` only.

Required frozen acceptance:

1. exact repository/plugin/skill inventory;
2. one canonical `onboard` skill resolved by both Codex and Claude manifests;
3. one exact `triana-preview==0.1.0a1` pin and six required commands;
4. no script/runtime/Docker/internal-provider duplication or forbidden network
   and execution surfaces;
5. prompt requests only the frozen customer-visible inputs and treats traces as
   untrusted evidence;
6. privacy/security/provenance documents make the same local-custody and direct
   provider-egress claims as Preview;
7. Apache-2.0 skill metadata and no claim that Preview is open source;
8. a static clean-directory workflow contract; actual PyPI execution waits
   until the Preview candidate exists.

Valid RED must fail against an absent skill snapshot while collecting cleanly.

## Orchestrator freeze and next handoff

After both sessions return, the orchestrator:

1. reviews tests for scope and implementation leakage;
2. runs each suite and records valid RED;
3. records SHA-256 for every test/fixture;
4. appends the hashes and exact commands to this packet;
5. starts two implementation sessions concurrently, cross-assigned so neither
   implements against tests it authored;
6. gives each implementation session exclusive ownership of one staging root
   except the frozen `tests/**` bytes.

No test weakening occurs after hash freeze. A genuine test-contract defect
returns to its author and receives a new recorded hash; implementation failures
return to the implementation owner.

## Gate 1 change budget

Orchestrator in the private monorepo:

- this packet;
- append-only Gate 1 status in `internal/SLICE_PACKET.md`;
- ignored decision-memory continuation.

Test authors: only their exact staging `tests/**` roots. Dependencies: none.
Production code: none. Existing dirty worktree: untouched except the listed
orchestrator documentation. External side effects: the two empty permanent
local repository directories were created with owner approval; no remote state
exists.

## Independent RED freeze — 2026-08-11

The orchestrator read every test and fixture, confirmed disjoint ownership,
synthetic-only values, black-box authority, and failures caused by absent
implementation rather than collection or syntax defects.

### Preview frozen bytes

- `tests/conftest.py`:
  `1691885f90ac35f1b85ff762a5f915c7569d1506634ceebb1df183faa8054653`
- `tests/test_cli.py`:
  `45d940c2dcc4cf1205b90feb1c26c10a5cc064a060ad17e6cea9003e85188c75`
- `tests/test_distribution_inventory.py`:
  `cfd0869be6bcdc49fec2aa13aaa72fb2612a167794b254429d4a8c819215c97c`
- `tests/test_provider_boundary.py`:
  `e8a50d64081c551682953188762002b73c5db70ed7c573f5727787acdb093e02`
- `tests/test_security_integrity.py`:
  `5b3c4aa45992c04f0b23a99c08e6297b0ea90137c67a48d7c8e09f32ff541738`
- `tests/_absent_runtime/triana_preview/__init__.py`:
  `007e45d4a318aeed7abc2bb19a87ee34bb56884046e4f836518beb4ea6120053`

Verification from the Preview staging root:

```text
python3 -m compileall -q tests
/Users/akarshgajbhiye/triana/triana-preview/.venv/bin/python -m pytest --collect-only -q
/Users/akarshgajbhiye/triana/triana-preview/.venv/bin/python -m pytest -q --tb=short
```

Result: compilation passed, 27 collected, 27 valid RED failures. Production,
package metadata, legal/docs, and build artifacts are absent. The sentinel
prevents the test runner's unrelated editable monorepo installation from
masking that absence.

### Skills frozen bytes

- `tests/test_plugin_contract.py`:
  `421be6be7b192b4a79d308d1057a465d1680c29f09f0f337900f25e95d32f31e`
- `tests/fixtures/synthetic-previewtrace.jsonl`:
  `8cb3fb6c603db37b5b0fb9538471c3879198cc3583b4b767e6be0eff116a0d31`

Verification from the Skills staging root:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Result: 7 collected, one test-only fixture control passed, six valid RED
failures, zero errors. Failures are the absent manifests, skill, documents,
license, CI, and exact public inventory.

Status: **RED FROZEN; TWO CROSS-ASSIGNED IMPLEMENTATION AUTHORS AUTHORIZED**.
Test bytes above are immutable unless a demonstrated contract defect returns to
the original test author and a superseding hash is appended here.

### Final-verifier security RED supersession — 2026-08-11

Independent read-only verification found three privacy/custody gaps outside the
first frozen cases: trace pathname replacement between stable validation and
redaction reopen; provider-file symlink replacement and unbounded private-file
read between metadata check and read; and ambient LangSmith/LangChain tracing
that could create unauthorized secondary egress. The original Preview test
author froze four black-box regressions without editing production.

Superseding hashes:

- `tests/conftest.py`:
  `0f2f82ff7c9163b4dcf59be8711ee9b4be3113138823533184dcb4865b36cc80`
- `tests/test_provider_boundary.py`:
  `3eb25d60559562876d1c446b3d4fd5596aa0c516457280dea7991fbaf1a758f8`
- `tests/test_security_integrity.py`:
  `b28b971fe7e5bcd7d4d090b2207c2e03664de89106355d723a4e34cd3b0abf2e`

Unchanged hashes remain `test_cli.py`
`45d940c2dcc4cf1205b90feb1c26c10a5cc064a060ad17e6cea9003e85188c75`
and `test_distribution_inventory.py`
`d6df630b487c3ddd705e56db58b81cc7a8592dcc9d01c07b0eebf5023fbad143`.

Verification: 31 collected; 27 prior cases passed and exactly four new cases
failed. Current code accepted both replacement races, read a valid 16,385-byte
provider file, and constructed ambient tracing. Provider configuration is now
bounded at 16 KiB. These are valid RED privacy gates returned to the Preview
implementation author; test bytes are frozen at the superseding hashes.

The first two replacement regressions were subsequently corrected because they
interposed on `Path.read_bytes` and therefore rewarded an unsafe unbounded path
reopen. The corrected benign tests forbid any target `Path.read_bytes` reopen
after bounded stable authority and independently replace one ordinary regular
file at the stable-open boundary. Current production collected 31 with 29 pass
and exactly those two corrected tests RED. These hashes supersede only the
provider and security hashes immediately above:

- `tests/test_provider_boundary.py`:
  `c5e79dfbc4da9a0e5f3face89e84584cc1f5f530cf565031ec726ccd256c182a`
- `tests/test_security_integrity.py`:
  `4c9bbf5b3a6d32fed5c183275c4388fdb63246567a5eb898a90776d5361c2c81`

`tests/conftest.py` remains
`0f2f82ff7c9163b4dcf59be8711ee9b4be3113138823533184dcb4865b36cc80`;
the 16 KiB provider bound and ambient tracing regressions remain unchanged and
GREEN from the prior production repair.

## Final Gate 1 verdict — 2026-08-11

Status: **PASS FOR LOCAL REPOSITORY ACCEPTANCE; PUBLICATION HELD**.

Independent verification on the final staging bytes established:

- Preview: 31/31 frozen tests, Ruff format/check on `src`, and strict mypy;
- Skills: 7/7 frozen tests and both official Claude plugin validators;
- both current staging roots passed Gitleaks;
- wheel SHA-256
  `ca4d644bc70a87d0c93b832b14f32e34f59097bf0898b965518acc18ceed773a`;
- sdist SHA-256
  `12cb1b579a49e95276f9da14f6f6d5f21ccf64d1c1a71045fb71ba2473b838bd`;
- wheel/sdist inventory, package metadata, dependency allowlist, checkpoint
  claims, and canonical frozen test hashes matched this packet.

The orchestrator copied only canonical source/test/document/workflow files to
the permanent local roots. It excluded `.venv`, `.mypy_cache`, `.pytest_cache`,
`.ruff_cache`, `__pycache__`, and `dist`; no staging transient was copied.

Publication remains outside Gate 1 and is held until a separate release slice
verifies a clean dependency install and exact `uvx` candidate, TestPyPI, remote
repository/CI setup, and the selected legal-owner review. Semgrep and OSV were
unrun because the local CA path and offline vulnerability database were not
available. These are recorded as unverified, not passing. No provider call,
customer-data use, GitHub repository, PyPI project, tag, push, or release
occurred.

### Release-checkout test hash supersession — 2026-08-11

The first GitHub release checkout exposed one test-contract defect: the exact
repository inventory test treated required `.git` checkout metadata as a public
artifact. The original Preview test author added only `.git` to the transient
metadata set; the public artifact allowlist and production behavior are
unchanged. The focused test and all 31 cases passed. This hash supersedes only
the prior `tests/test_distribution_inventory.py` hash:

- `tests/test_distribution_inventory.py`:
  `0863a01928428ff89aadea7ce7f0912fb8e121ed885fdd43dc5b30a03c157534`

The correction did not change either accepted distribution hash.
