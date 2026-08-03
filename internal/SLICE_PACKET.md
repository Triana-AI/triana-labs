# LABS-06 regular-user simulator fidelity slice packet

Date frozen: 2026-08-03

Status: **LOCALLY IMPLEMENTED AND VERIFIED; HUMAN FIDELITY GATE PENDING**

Slice ID: `LABS-06-REGULAR-USER-SIMULATOR-FIDELITY-V1`

Canonical base: `2e7a367325ceeffc7adb8e0e45fe3748faf0cda9` on local `main`;
implementation branch `codex/labs-06-regular-user-fidelity`.

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`.

Normative wire: `internal/LABS06_SIMULATOR_FIDELITY_V1.md`. LABS-05 Target
Connector V1 and the retained LABS-05 episode/artifact wire remain normative
where the LABS-06 wire does not supersede simulator behavior.

## 1. Product outcome

Repair the observed R2 simulator-boundary defect without expanding the target,
provider, memory, report, UI, or real-data surface. Every simulator call carries
the verified persona, intent, known-fact projection, versioned user-owned turn
policy, bounded episode state, transcript, and latest observation. Deterministic
code accepts one authorized user utterance or structured stop and rejects typed
critical semantic defects before another target call.

The round exits with locally GREEN implementation, a frozen 30-item synthetic
teacher-forced panel, and a generated human-review contract/template. It does
not claim `REGULAR_USER_SIMULATION_FIDELITY_V1` passage or produce a public
sample without Akarsh's later rulings and separate provider authorization.

## 2. Accepted owner decisions

1. Local GREEN precedes any provider evaluation; this packet authorizes none.
2. Fidelity gate is 30 items, at least 24 accepted, zero critical failures.
3. Fixtures are newly authored synthetic HRAI-shaped evidence; no private
   canary text enters Git.
4. Episode state is the six closed fields in the normative wire, with
   `UNKNOWN` and no free-form emotion memory.
5. Simulator behavior is one attempt in evaluation and generation; no
   regeneration, retry, repair, or fallback.
6. Semantic failures use `SIMULATOR_SEMANTIC_INVALID` plus closed detail codes.
7. Echo detection uses normalized containment and token-trigram Jaccard
   threshold `0.80` under `LABS06_ASSISTANT_ECHO_V1`.
8. LABS-04 policy artifacts remain immutable; LABS-06 uses a versioned
   user-owned migration.
9. LABS-06 finishes the component/review contract; public sample waits for
   LABS-07's report schema.
10. Deterministic semantics are limited to declared matchers; residual
    paraphrased-role/naturalness judgment remains human-owned.

## 3. Input, output, and authority

Inputs:

- existing verified `VerifiedCaseProjection` and frozen selected-case order;
- explicit file-backed versioned `SimulatorCaseContext` bundle, or an injected
  loader limited to read/schema/identity verification;
- current episode transcript and exact latest target observation;
- closed episode-local `InteractionState`;
- one simulator response or deterministic fake response;
- 30-item synthetic teacher-forced panel for the fidelity review contract.

Outputs:

- unchanged eight-file adaptive-run bundle with LABS-06 simulator protocol,
  semantic gap details, structured stop, and interaction-state lineage added
  only where frozen by the wire;
- deterministic teacher-forced review projection with exact item identities,
  strata, denominator, generated proposal evidence, and null human rulings.
- exactly `fidelity_attempts.jsonl`, `human_fidelity_review.json`, and
  `fidelity_manifest.json` from the separate internal teacher-forced API;
- historical LABS-05 behavior when no bundle is supplied; an invalid supplied
  bundle refuses and never falls back.

Deterministic code owns identities, migration validation, visibility,
allowlists, state transitions, binding, hard semantic checks, termination,
accounting, custody, dedupe, and publication. The simulator owns wording and
one proposed reaction/stop. Akarsh owns fidelity and naturalness rulings.

## 4. Privacy and execution

Automated work is local and synthetic-only. No provider, target, HRAI, real
data, private canary artifact, external endpoint, or credential is used. The
existing redaction/secret-reflection and provider authorization boundaries stay
closed. A later provider evaluation requires a separate explicit owner grant.

## 5. Refusal and gap behavior

Pre-egress invalid/ambiguous migration, missing required matchers, invalid
state, unknown transition, hidden value in provider projection, or unsupported
protocol refuses as `SIMULATOR_CONTEXT_INVALID` and creates no new call.

Post-response structural defects remain `SIMULATOR_INVALID_RESPONSE`; binding
mismatch remains `ADAPTATION_BINDING_MISMATCH`; semantic defects use
`SIMULATOR_SEMANTIC_INVALID` with sorted closed detail codes. Completed request
and accounting custody remain. No rejected response becomes a turn or is
silently repaired. Later already funded episode slots may continue under the
unchanged LABS-05 rule.

## 6. Essential independent acceptance set

Approximately eleven black-box behavioral tests, without helper-shape or
coverage-padding cases:

1. default and injected bundle loading, exact verified projection, historical
   no-bundle compatibility, and hidden-value non-egress;
2. valid regular-user emit, binding, state transition, and accounting;
3. preserved R2-shaped exact echo rejection before target continuation;
4. near echo positive and ordinary-overlap negative fixtures;
5. bounded nonidentical assistant-role inversion rejection;
6. hidden-fact leakage and fixed-fact conflict rejection;
7. unauthorized reaction/action rejection;
8. structured stop exactly once, no visible token, no target continuation;
9. malformed/binding/unknown semantic output fails once without fallback;
10. cross-episode state isolation;
11. exact 30-item review denominator/strata/null-ruling projection while prior
    identity, budget, connector, custody, privacy, and dedupe behavior remains
    GREEN.

Parameterized semantic rejection may combine related variants while retaining
exact detail-code and custody assertions. Tests must not assert private helper
shape, every enum member, framework behavior, or speculative abstractions.

Valid RED requires collection success, no skip/setup/import error, all existing
tests GREEN, and failures caused only by missing LABS-06 behavior. The test
author independently derives expected requests, echo calculations, identities,
and review bytes rather than importing production oracles.

## 7. Role protocol

Exactly two worker agents plus Codex orchestrator execute serially in the
shared worktree. The test author edits only test-owned paths and proves RED.
Codex audits, hashes, and freezes those bytes. Only then may a distinct
implementation author edit production-owned paths. Test defects return to the
test author; implementation defects return to the implementation author.
Codex alone runs adversarial/full gates and declares completion.

## 8. Change budget

Orchestrator-owned:

```text
internal/SLICE_PACKET.md
internal/LABS06_SIMULATOR_FIDELITY_V1.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md
triana-labs/CHARTER.md
docs/ARCHITECTURE.md
triana-labs/scripts/verify.sh
```

Test-author-owned:

```text
triana-labs/tests/simulator_fidelity_acceptance/**
triana-labs/tests/simulator_fidelity_fixtures/**
```

Implementation-author-owned after RED freeze:

```text
triana-labs/src/triana_labs/adaptive_runner/contracts.py
triana-labs/src/triana_labs/adaptive_runner/boundaries.py
triana-labs/src/triana_labs/adaptive_runner/runner.py
triana-labs/src/triana_labs/adaptive_runner/simulator_fidelity.py
triana-labs/src/triana_labs/adaptive_runner/__init__.py
```

Maximum production files: five. Maximum changed production nonblank/
noncomment lines: 1,200. Maximum new test-owned Python/JSON files: six.
Maximum test-owned physical lines: 1,600. No dependency, lock, package,
connector, CLI, config schema, report, UI, or external-repository edit is
allowed. The bundle schema and separate internal teacher-forced API are the
only new input/evaluation surfaces.
There is no scope expansion without orchestrator review; material expansion
returns to Akarsh.

Explicitly untouched:

```text
triana-core/**
triana-labs/src/triana_labs/adaptive_runner/http_target.py
triana-labs/src/triana_labs/adaptive_runner/process.py
triana-labs/src/triana_labs/cli.py
triana-labs/examples/**
all LABS-01--05 tests, fixtures, production artifacts, and external evidence
pyproject.toml and uv.lock
raw HRAI, provider, canary, Blitz, Agentagon, Kairos, and Kairos-AI material
UI/report, baseline/candidate diff, judges, persistent/global memory,
real-data support, generic SDKs, hosted execution, and broad eval expansion
the three unrelated untracked research/SPC files
```

## 9. Commands and freeze

Test author:

```text
cd triana-labs
uv run pytest -q tests/simulator_fidelity_acceptance
uv run ruff check tests/simulator_fidelity_acceptance
uv run ruff format --check tests/simulator_fidelity_acceptance
```

Codex reproduces focused RED and all historical tests, records sorted
concatenated content SHA-256 and sorted per-file hash-stream SHA-256, and
freezes every test/fixture byte before implementation.

Frozen independent RED (2026-08-03): four Python files, 748 physical lines,
12 essential black-box functions / 18 collected cases; 18 expected behavioral
failures solely at the absent LABS-06 run/evaluation surface, 143 historical
adaptive-runner cases GREEN, Ruff check/format GREEN. Sorted concatenated
content SHA-256 is
`9cb872ce1015d12eedf3f47464c88363cfb38d1c204f3418bc4bfac12271074d`;
sorted per-file hash-stream SHA-256 is
`de3767401404d32fe9786cb93cb7f4d29718deec71285cb3d5040c1190d09842`.
These test bytes are immutable during implementation.

Implementation author runs the frozen LABS-06 suite and the existing adaptive
runner suite. Final Codex gate:

```text
cd triana-labs
./scripts/verify.sh
git diff --check
```

The complete verifier must retain all existing lanes and add the frozen LABS-06
hashes, full test collection, Ruff, strict mypy, deterministic replay, five
canonical Observer hashes, build, clean CPython 3.13 wheel install,
source/wheel parity, governance, provenance, and secret scan. An unrun lane is
not passing.

Final local evidence (2026-08-03): LABS-06 acceptance 18/18 GREEN, historical
adaptive-runner acceptance 143/143 GREEN, and complete repository verification
569/569 GREEN with Ruff, strict mypy over 29 source files, deterministic replay,
five unchanged Observer hashes, frozen test hashes, sdist/wheel build, clean
CPython 3.13.14 wheel install, source/wheel parity, governance, and secret scan.
Evidence: `/private/tmp/triana-labs-verify.JGgnp9`. This proves local mechanics,
not `REGULAR_USER_SIMULATION_FIDELITY_V1` passage or provider compatibility.

## 10. Orchestrator adversarial matrix

After candidate GREEN, Codex independently checks:

1. Unicode/punctuation/case perturbation cannot evade exact/near echo while a
   short common phrase does not false-positive;
2. a forged `speaker_role: USER` with an assistant-only action matcher still
   rejects;
3. hidden/fixed matcher absence refuses before egress rather than weakening;
4. semantic rejection preserves one simulator ledger attempt and performs no
   later target exchange;
5. structured stop preserves prior transcript/accounting, closes the target
   once, and emits no synthetic user row;
6. state and remaining disclosures cannot cross episode identity or mutate the
   frozen case context.

Any actual defect returns to the responsible worker under a single falsifiable
hypothesis. Codex does not repair production or frozen acceptance logic.

## 11. Provenance and non-goals

All production and tests are newly authored from repository-local authority.
HRAI supplies only the already-recorded interface/evidence history; no HRAI or
private content is copied. Newly authored fixtures are synthetic and must not
reproduce private canary text. No provenance-ledger change is expected unless
the implemented diff uses an external source, in which case work stops first.

Deferred: persistent/global or free-form emotion memory, model judges,
provider evaluation, public sample, UI/report, baseline/candidate comparison,
real/local-sensitive support, generic SDKs, broad evals, target changes, HRAI
rerun, and hosted execution.

## 12. Required handoff

Every worker and Codex reports:

```text
What changed:
Why each changed file was necessary:
Change-budget reconciliation:
What was verified (exact commands and artifacts):
What remains unverified:
Assumptions made:
Unexpected findings:
Dependencies added and why:
Out-of-scope problems deliberately left alone:
Known risks or uncertainty:
Human action still required:
```

Use `none` explicitly. Codex does not approve a human fidelity ruling.

Final orchestrator handoff:

```text
What changed: added an explicit verified LABS-06 context-bundle boundary,
strict user-role response wire, deterministic semantic refusal and episode
state/stop control, and a separate 30-item teacher-forced review projection;
preserved no-bundle LABS-05 behavior and inherited target/accounting/privacy.
Why each changed file was necessary: contracts define bounded types;
simulator_fidelity owns loading, semantics, transitions, and review artifacts;
runner integrates activation and custody; boundaries selects the provider wire;
exports expose the API; acceptance owns behavior; verifier freezes it;
canonical documents record authority and status.
Change-budget reconciliation: five authorized production paths, four test files
and 748 lines, no dependency/lock/CLI/connector/external-repository change, and
the three unrelated untracked research/SPC files untouched.
What was verified: 18 focused, 143 historical adaptive, and 569 complete tests;
Ruff, strict mypy, frozen hashes, replay, Observer hashes, build, clean wheel,
source/wheel parity, governance, provenance, secret scan, diff check, and the
six-item adversarial matrix.
What remains unverified: live provider compatibility and all 30 human fidelity
rulings; no provider, target, external endpoint, or real data was executed.
Assumptions made: explicit bundle presence is the only LABS-06 activation;
injected loaders own read/schema/identity verification but not semantic
completeness; no bundle preserves LABS-05.
Unexpected findings: the initial freeze lacked a migration input route and
exact review API, so RED paused until corrected; adversarial audit then closed
raw non-object acceptance, hidden projection, and unsafe-response hashing.
Dependencies added and why: none.
Out-of-scope problems deliberately left alone: every deferred area in section
11 and the unrelated untracked files.
Known risks or uncertainty: declared literal matchers are intentionally bounded
and do not establish general semantic understanding; human naturalness and
fidelity remain pending.
Human action still required: separate authorization for any provider, target,
external, or real-data run, followed by Akarsh's own 30-item fidelity rulings.
```
