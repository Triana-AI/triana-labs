# Owner-authorized real-data plumbing packet

Date frozen: 2026-08-04

Status: **FROZEN FOR PARALLEL INDEPENDENT TEST AND PRODUCTION AUTHORSHIP; NO EXTERNAL EXECUTION**

Slice ID: `LABS046-OWNER-AUTHORIZED-REAL-DATA-V1`

Canonical base: commit `26859b9` on branch
`codex/labs-06-regular-user-fidelity`.

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md` -> this packet.

## 1. Outcome

Remove the accidental synthetic-only implementation restriction from the
already approved LABS-046 workflow. The exact additional accepted class is
`OWNER_AUTHORIZED_REAL_DATA_CANARY`. It must propagate truthfully from input
traces through Observer, Corpus Intelligence, grounded case generation, world
inventory, selection, adaptive execution, custody, and tiered reports.

This is plumbing, not a live run. It does not query RDS, call a provider,
start HRAI, execute a target, or authorize paid egress.

## 2. Closed privacy contract

Accepted input privacy classes are exactly:

- `SYNTHETIC`
- `OWNER_AUTHORIZED_REAL_DATA_CANARY`

Every other value remains `UNSUPPORTED_PRIVACY_CLASS`. One corpus/bundle may
contain only one class. Mixed classes refuse before publication, hashing for a
provider request, or provider/target execution with
`PRIVACY_CLASS_MISMATCH`.

The canary class is private and nonportable:

- all Observer, Intelligence, Case Factory, and runner output/cache roots must
  resolve beneath `/private/tmp`;
- manifests and records retain the canary class; no artifact may say
  `SYNTHETIC` for canary evidence;
- world inventory `data_class` must equal the trace/run class;
- simulator and target configuration must use the existing canary privacy and
  `OWNER_AUTHORIZED_REAL_TARGET` pairing;
- a synthetic/canary mismatch refuses before egress;
- raw customer traces, provider bodies, secrets, and hidden facts never enter
  public or repository artifacts.

No class conversion, default, repair, retry, fallback, or mixed-mode merge is
allowed.

## 3. Propagation and labels

For synthetic inputs, every historical byte and behavior remains unchanged.

For owner-authorized inputs:

- Observer manifest/profile custody carries
  `OWNER_AUTHORIZED_REAL_DATA_CANARY`;
- Corpus Intelligence outputs carry the same privacy class and fidelity
  `OWNER_AUTHORIZED_REAL_DATA_OBSERVED_STRUCTURE`;
- generated personas, intents, policies, and cases carry fidelity
  `OWNER_AUTHORIZED_REAL_DATA_GROUNDED`;
- Case Factory evidence index and manifest carry the same privacy class;
- the canary evidence authorization projection is exactly
  `LABS04_OWNER_AUTHORIZED_REAL_DATA_SEMANTIC_EVIDENCE_V1`, while the existing
  synthetic projection remains byte-identical;
- world inventory accepts exactly the canary class and hash-binds it as before;
- closure selection/config/cases/inventory must agree on privacy identity;
- adaptive manifests, records, gaps, tiered Markdown, and result custody retain
  the canary class without exposing private values.

The provider may summarize or combine authorized observed evidence under the
existing grounded rules. It still cannot invent facts, identifiers, goals,
completion conditions, rulings, or lineage. Deterministic and human authority
remain unchanged.

## 4. Failure behavior

Fail before egress on:

- unsupported or mixed privacy classes;
- canary paths outside `/private/tmp`;
- trace/intelligence/inventory/config/target class disagreement;
- a synthetic target paired with canary data or vice versa;
- missing authorization labels or lineage;
- any existing privacy, secret, schema, identity, budget, or custody refusal.

Failures remain typed and cannot become valid cases, findings, completions, or
passes. Later episode continuation after an already typed per-case world gap is
unchanged.

## 5. Preserved behavior and non-goals

Preserve deterministic identity, observation binding, termination, budgets,
custody, dedupe, privacy scanning, typed gaps, one attempt, and no retry,
repair, redirect, proxy, or fallback. Preserve all legacy synthetic hashes and
the exact LABS-046 6/6 and twelve-case behavior.

Deferred: persistent/global/emotion memory, judges, UI/report expansion,
baseline/candidate diff, generic SDKs, broad eval expansion, general customer
real-data support, arbitrary privacy classes, mutable sandbox/world building,
hosted storage, and any external execution.

No external repository source is copied or derived.

## 6. Independent parallel ownership

The test author works only in isolated worktree
`/private/tmp/triana-realdata-tests` on branch
`codex/labs046-realdata-tests` and may edit only:

- new or existing black-box tests under `triana-labs/tests/acceptance/**`;
- `triana-labs/tests/intelligence_acceptance/**`;
- `triana-labs/tests/case_factory_acceptance/**`;
- `triana-labs/tests/adaptive_runner_acceptance/**`;
- purpose-built fixtures under the matching fixture directories.

Budget: at most eight new/changed black-box functions, 30 collected cases, and
650 changed/new physical test lines. No helper-shape tests, coverage padding,
combinatorial matrix, external calls, production edits, docs, or verifier
hash edits.

The implementation author works only in isolated worktree
`/private/tmp/triana-realdata-impl` on branch
`codex/labs046-realdata-impl` and may edit only:

- `triana-labs/src/triana_labs/contracts/traces.py`
- `triana-labs/src/triana_labs/observer/observe.py`
- `triana-labs/src/triana_labs/observer/publication.py`
- `triana-labs/src/triana_labs/observer/renderer.py`
- `triana-labs/src/triana_labs/intelligence/input.py`
- `triana-labs/src/triana_labs/intelligence/derive.py`
- `triana-labs/src/triana_labs/case_factory/evidence.py`
- `triana-labs/src/triana_labs/case_factory/generate.py` (public restricted
  wrapper translates only the new privacy refusal to `GenerateFailure`)
- `triana-labs/src/triana_labs/case_factory/restricted_runtime.py`
- `triana-labs/src/triana_labs/case_factory/semantic.py`
- `triana-labs/src/triana_labs/adaptive_runner/runner.py`

Budget: at most 430 changed/new physical production lines. No dependency,
schema package, connector, simulator-fidelity, CLI, test, docs, script, or
external-repository change.

Each author commits only owned files and returns the complete structured
uncertainty handoff required by `AGENTS.md`. The orchestrator alone reconciles
and cherry-picks both commits, updates canonical docs/decision memory/verifier
hashes, resolves genuine contract conflicts, and owns the final verdict.

## 7. Minimum acceptance

The independent set must prove only:

1. canary traces are accepted and the exact class propagates through Observer;
2. mixed/unknown classes and non-private canary custody refuse without output;
3. Intelligence consumes and republishes canary evidence with exact fidelity;
4. Case Factory accepts matching canary evidence/inventory, rejects mismatches
   before a transport call, and retains canary labels in cases/manifests;
5. the closure runner accepts a matching canary inventory/config/real target,
   retains exact private custody, and rejects mismatches before target or
   simulator creation;
6. synthetic controls remain byte/behavior compatible.

Approximately six to eight black-box tests are sufficient. Do not add broad
real-data or live-infrastructure coverage.

## 8. Verification

Focused commands are selected by the independent author and must include all
new tests plus one synthetic control per affected stage. Then run:

```bash
cd triana-labs
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src/triana_labs
./scripts/verify.sh
```

No command above authorizes RDS, provider, HRAI, target, or real-data egress.

## 9. Independent RED freeze

The independent test author committed `62627edf31fcd00bf0198ab1bc6abb7ec6c95886`
(integrated as `421a780`), the assertion-supersession follow-up
`20e397a19b9bcd5ad38affc03ad4395174c4ee9c` (integrated as `eb2dc25`), and
the public-derive fixture correction `38840927b7833430bc76d7a1dba1cfe393e7620b`
(integrated as `ff1b711`). The final set has exactly seven black-box functions,
ten cases, and 394 changed/new physical lines across six authorized test files.
The frozen
file SHA-256 values are:

```text
tests/acceptance/test_observe_success.py
  9785048c869867ba8085181bf04c1c034c1e154e71cd2da80476ad04b7c81680
tests/acceptance/test_observe_rejections.py
  974f55f959eb839651a237ca0d4e629574afeb11f933e67f12907b84172fd944
tests/acceptance/test_observe_safety.py
  4526030cbbc80c878b66565f517bdf35a4038da80ef2adc44cdf7f164d733ad4
tests/intelligence_acceptance/test_derivation_success.py
  9a03ffa0314690d94fa51291b840322cfc064213c628ff2d3a353d4ffd93dae7
tests/case_factory_acceptance/test_grounded_workflow_closure.py
  63b717755f14971ab4c70a9a2f7a410d7d6823c65fdf5b41a3caac2c5b8cc359
tests/adaptive_runner_acceptance/test_workflow_closure_execution.py
  9bc0fa6a8b08e89a3251e03151ac6abe640fcf8a57b9361e6dfcbb84d9447ad6
```

Codex independently reproduced nine behavioral RED failures and one existing
target-class refusal control pass: four Observer, one Intelligence, two Case
Factory, and two runner failures. Four separate synthetic stage controls pass.
Collection, imports, lint, formatting, and setup are valid; no external call
occurred. These test bytes are frozen before integration of production.

## 10. Exit and later live gate

Local exit requires independent RED provenance, candidate GREEN, all legacy
controls, complete repository GREEN, exact change-budget reconciliation, and
canonical decision/doc updates.

The implementation author committed `1851f9815c26b7778ed259d370237d6e7605615b`
(integrated as `7058053`) with 356 changed physical production lines across
the eleven authorized files, within the 430-line budget. The final test fixture
uses the public deterministic Observer-to-Intelligence boundary rather than
forging an Intelligence bundle. Focused stage acceptance is GREEN, Ruff and
strict mypy are GREEN, and the complete repository verifier passes 613 tests,
build, clean-wheel install, frozen hashes, artifact replay, and governance at
`/private/tmp/triana-labs-verify.ccgGCu`. No provider, HRAI, target, RDS, or
real-data execution occurred.

Only after local exit may the orchestrator inspect a concrete read-only RDS
export command. Before any provider or HRAI execution, Akarsh must see and
approve the exact private trace selection, world inventory, twelve cases,
endpoints, target-side-effect boundary, and maximum USD/HTTP budget.
