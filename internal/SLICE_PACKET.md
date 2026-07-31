# Active implementation slice

Status: **HISTORICAL SLICE 0A — COMPLETE; REPLACE BEFORE NEW LABS WORK**

## Repository-wide workflow controls

These controls were accepted after Slice 0A was completed and moved into
`triana-core/`. They do not change Slice 0A product behavior, acceptance
criteria, frozen test ownership, or allowed production paths. Before any new
Labs slice or any other implementation slice begins, the orchestrator must
replace this historical packet and populate the fields below with
slice-specific values. No worker starts while a required field remains
unfilled.

### Change budget

```text
Expected files or bounded path patterns: [required]
Expected production areas: [required]
Expected test and fixture areas: [required]
Explicitly untouched areas: [required]
New dependencies permitted: [none, or exact allowed purpose]
Maximum scope expansion without orchestrator return: [required]
```

Every worker stops before exceeding this budget. At exit, the orchestrator
records the actual files and dependencies and explains every variance.

### Single-hypothesis debugging record

Repeat this block once per debugging iteration:

```text
Observed failure:
Smallest reproduction:
Current hypothesis:
Evidence that would falsify it:
One change attempted:
Result:
Regression test or fixture:
```

One iteration contains one causal intervention. A falsified speculative change
is removed or isolated before the next hypothesis.

### Structured uncertainty handoff

Every worker and the final orchestrator handoff uses:

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

Use `none` rather than omitting an empty field. Unrun checks are reported as
unverified, never implied to have passed.

The owner started execution on 2026-07-30. The implementation author first
created only the approved reproducible `NOT_IMPLEMENTED` scaffold. Independent
test-author audits then forced the field-level protocol, nine corrections, and
four final closures to be owner-approved before any fixture became ground
truth.

The independent test author subsequently created only
`tests/acceptance/**` and `tests/fixtures/**`. The orchestrator reviewed the
suite, returned two incomplete coverage passes to the test author, reproduced
the final exhaustive manifest and behavioral RED result, matched every file
hash, and froze the test-owned paths in commit `87476be`. During implementation,
three test-only defects were correctly returned to the test author: malformed
stable-key inputs failed inside the fixture oracle, and two optional fields had
been transcribed as required. The test author repaired and exhaustively audited
those cases in `f01b08e`; the orchestrator then reproduced the corrected RED
state from a clean export. The implementation author may edit production-owned
paths but may not edit the corrected frozen tests or fixtures.

## Identity

- Slice ID: `0A-contract-kernel`
- Working interpretation: the first implementation slice, not Phase 1
  acquisition
- Canonical RED base commit: `f08b30c`
- Normative contract commit: `710bccd`
- Frozen test commit: `f01b08e`
- Frozen test evidence: `internal/SLICE_0A_TEST_FREEZE.json`
- Orchestrator: primary Codex agent
- Test author: separate agent; completed and frozen
- Implementation author: different agent; released only after this freeze

## Product outcome

Slice 0A establishes one deterministic evidence language that later trace
adapters, comparison, CLI, API, GitHub output, and UI can share.

The machine-verifiable result is:

> A synthetic, versioned Triana contract can be strictly parsed, serialized to
> canonical bytes, assigned a stable identity/hash, written, loaded, and
> verified without semantic drift. Invalid, unsupported, ambiguous, or
> tampered inputs fail with safe machine-readable errors and structured,
> redacted logs.

This slice does not calculate comparisons, policies, recommendations, or human
decisions.

## Deliverables

### D1. Reproducible repository scaffold

- One pinned runtime and package manager.
- Locked dependencies.
- Strict compiler/type configuration.
- One local verification command used unchanged by CI.
- Separate source, test, fixture, and generated-schema paths.
- Minimal container/package proof for the CLI boundary.

### D2. Versioned contract package

Four core evidence families:

1. `NormalizedTrace`
2. `ProtectedCase`
3. `ReleaseEvidenceRecord`
4. `RecordChain`

One additional independently valid lifecycle document:

5. `DecisionAttestation`

The closed nested-type registry and exact field-level wire contract are
normative in `docs/CONTRACTS.md`.

Nested typed values include:

- `ReleaseChange`
- `ReleaseObligation`
- `EvidenceRequirement`
- `ObservationScope`
- `ExecutionContract`
- `RuntimeFingerprint`
- `TrialResult`
- `AssertionResult`
- `CustomerEvaluatorResult`
- `EvidenceGap`
- `Comparison`
- `PolicyEvaluation`
- `EvidenceReference`
- `Approval`

Nested values are not services, database tables, or independently deployed
systems.

`ReleaseChange` records the customer declaration, observable composite
identity, and unresolved differences. `ReleaseObligation` carries the
human-approved semantic requirement inside the V1 `ProtectedCase`.
`EvidenceRequirement` is distinct from the received evidence result. Slice 0A
protects these meanings structurally but does not infer change impact,
obligation applicability, or evidence sufficiency.

### D3. Deterministic integrity kernel

- Strict raw JSON parser boundary.
- Schema and cross-field validation.
- Canonical byte generation.
- Stable content identity.
- Record seal and verification.
- Single-record previous-hash field validation.
- Read-only verification with no input mutation.

Record-chain traversal and comparison/policy correctness remain Slice 0B
unless Akarsh explicitly expands 0A.

### D4. Thin black-box interface

Proposed commands:

```text
triana contracts validate <file>
triana records seal <unsigned-record-file>
triana records verify <sealed-record-file>
```

Artifacts go to stdout or an explicit output file. Structured logs go to
stderr. No network, database, authentication, or customer environment is
required.

### D5. Independent fixture and evidence set

- Minimal and complete valid fixtures.
- Independently authored canonical-byte goldens and SHA-256 digests.
- Invalid-version and malformed fixtures.
- One mutation per protected field class.
- Unicode, numeric, ordering, duplicate-key, and resource-limit fixtures.
- Secret-bearing rejected fixture used only to prove log redaction.
- Machine-readable RED and GREEN test reports.

## Non-goals

- Trace-provider adapters
- Candidate surfacing or ranking
- Human case-authoring UI
- Assertion execution
- Customer evaluator execution
- Agent replay
- Baseline/candidate orchestration
- Comparison calculation
- Release Policy calculation
- Recommendation generation
- Hosted API, database, object store, authentication, tenancy, or billing
- GitHub Action or PR comment
- Release Review UI
- Digital signatures or key management
- Encryption or secret storage
- General migration framework
- Performance optimization beyond approved parser safety limits
- Real customer data
- Kairos-AI corpora as product acceptance truth
- Rollout, enforcement, or deployment behavior

## Authority

- Deterministic code owns parsing, ordering, canonicalization, identity,
  hashing, validation, and verification.
- Humans own Protected Case semantic truth and approval.
- No LLM participates in Slice 0A runtime behavior.
- No customer evaluator executes in Slice 0A.
- Fixtures may structurally represent later states but cannot claim their
  comparison or policy meaning.
- Invalid schema, identity, integrity, unsupported version, or impossible
  state aborts. It never becomes an evidence gap.

## Proposed contract invariants

- Same accepted input produces identical canonical bytes and hash across
  processes, locales, timezones, and repeated runs.
- Parse → canonicalize → parse has no semantic drift.
- Canonicalization is idempotent.
- Object insertion order and JSON whitespace do not affect identity.
- Ordered-field permutation changes identity.
- Explicit set-like-field permutation does not change identity.
- Every immutable stored field is hash-protected except the self-referential
  current hash field.
- `previous_record_hash` is protected by the current record hash.
- Unknown fields, duplicate keys, unsupported versions, and missing required
  identity fail.
- Failure emits no successful or partially verified artifact.
- Logging configuration, timestamps, and environment do not affect artifact
  bytes.
- Verification does not mutate its input.

## Owner decisions

Every decision below was accepted by Akarsh on 2026-07-30. These decisions are
frozen for Slice 0A. Changing one requires an explicit owner decision and an
append-only decision-log entry before affected tests or implementation change.

### D0A-00 — Phase interpretation and clean base — ACCEPTED

- “Phase one” here means the first implementation slice,
  `0A-contract-kernel`, rather than acquisition Phase 1.
- The current governance/product documentation may be reviewed, moved to a
  `codex/` topic branch, and committed before code begins.
- No worker edits start from the current dirty `main`.

### D0A-01 — Primary stack — ACCEPTED

- Python owns the deterministic core, CLI, backend APIs, integrations, and
  future AI-assisted subsystems.
- TypeScript owns the web UI.
- Versioned JSON Schema is the enforced language boundary.
- The deterministic core must not import or depend on an AI-assisted package.

Distribution is container-first and proprietary. Python implementation is not
published as open source, but inspectability of distributed Python is accepted
for V1. Native compilation is deferred until customer evidence requires its
cost.

### D0A-02 — Python and UI tooling — ACCEPTED

- `uv` for Python environment, dependency locking, and command execution.
- CPython 3.13.14, pinned in `.python-version` and project/container
  configuration.
- Committed `uv.lock` with exact dependency versions.
- Pydantic for strict readable runtime contracts.
- pytest for acceptance and unit tests, Hypothesis for deterministic
  property/mutation tests, Ruff for formatting/linting, and mypy for strict
  static checking.
- Defer the TypeScript package manager and web framework until the UI slice.
- Do not perform the former Zod-versus-TypeBox bake-off.

### D0A-03 — Public contract authority — ACCEPTED

- Pydantic schema as readable authoring source plus checked-in JSON Schema
  2020-12 projection with a CI drift check.

### D0A-04 — Wire format and strictness — ACCEPTED

- UTF-8 JSON is the only normative Slice 0A wire format.
- Reject duplicate object keys before normal object parsing.
- Reject unknown fields at every versioned boundary.
- Reject coercion, defaults that alter identity, `undefined`, `Date`, `BigInt`,
  NaN, and infinity in wire objects.
- YAML may later be an authoring format but is never hash input.

### D0A-05 — Canonicalization — ACCEPTED

- RFC 8785/JCS exactly.
- UTF-8, no BOM, no whitespace in canonical bytes.
- The hash covers canonical bytes without a terminal newline.
- Human-readable artifact files may end with one LF, excluded from the hash.
- Use published JCS conformance vectors.

RFC 8785 requires unique object keys, preserves Unicode strings without
normalization, retains array order, and constrains numbers to the I-JSON /
IEEE-754 domain.

### D0A-06 — Numeric representation — ACCEPTED

- Safe integers only for counts, indices, and millisecond durations.
- Decimal strings for scores, rates, costs, and currency amounts.
- Store integer numerators and denominators where a rate is derived.
- Reject unsafe integers, `-0`, non-finite values, and arbitrary protected
  floats.
- Derived rates and movements use exactly six fractional digits with
  round-half-even. Integer counts remain authoritative.

### D0A-07 — Unicode, timestamps, null, and optional fields — ACCEPTED

- Preserve accepted Unicode code points exactly; no implicit NFC
  normalization.
- Reject invalid Unicode/lone surrogates.
- Require canonical UTC RFC 3339 timestamps with fixed millisecond precision
  and `Z`; reject equivalent alternate offsets at this boundary.
- Required fields are present.
- Optional fields are absent, not `null`, unless null is explicitly defined as
  a domain state.

### D0A-08 — Ordered and set-like collections — ACCEPTED

Ordered sequences:

- trace events;
- conversation turns;
- tool activity;
- trials;
- assertion execution results;
- record-chain entries.

Set-like collections, sorted by stable identity and rejecting duplicates:

- allowed alternatives;
- expected/prohibited behavior statements;
- observation capabilities;
- record-level gaps;
- evidence references.
- check definitions;
- customer evaluator results.

Execution order, when relevant, is represented as separate metadata and does
not control set identity.

### D0A-09 — Identity model — ACCEPTED

- Protected Case has stable logical `case_id` plus content-derived
  `case_version`.
- Trace keeps its source identity plus a Triana content hash.
- Release record identity is its `record_hash`; no separate random ID in 0A.
- Trial identity derives from run, case version, side, trial index, code ref,
  and execution-contract identity.
- External/customer IDs are opaque strings and never silently re-derived.

Any change to source evidence, bounded replay input, fixture contract, risk
name, expected/prohibited/allowed behavior, escalation requirements, policy
context, executable checks, approval, or qualification creates a new
`case_version`. External display enrichment is excluded from identity.

### D0A-10 — Hash preimage — ACCEPTED

- SHA-256 encoded as lowercase `sha256:<64 hex characters>`.
- Use this exact preimage:

  ```text
  b"triana\x00" +
  contract_kind_utf8 +
  b"\x00v" +
  schema_version_ascii +
  b"\x00" +
  canonical_json_bytes
  ```

- Include every immutable stored field, including timestamps, safe labels,
  evidence references, policy result, recommendation, and
  `previous_record_hash`.
- Exclude only `current_record_hash` from its own preimage.
- Volatile display enrichment lives outside immutable records.

### D0A-11 — Record chain boundary — ACCEPTED

- Explicit `GENESIS` versus `APPEND` state.
- One chain per project/release stream.
- Reject forks in V1.
- Correction appends to the current head and separately names the superseded
  record.
- Define the schema in 0A; implement multi-record chain verification in 0B.

### D0A-12 — Trace privacy boundary — ACCEPTED

- `NormalizedTrace` is explicitly local-sensitive and may contain the bounded
  raw content needed inside customer CI.
- `ReleaseEvidenceRecord` is upload-safe and contains only approved normalized
  excerpts, typed facts, references, and hashes.
- No automatic raw trace-to-record copying.
- Logs never contain raw prompts, complete traces, tool arguments/results,
  credentials, or query-bearing URLs.
- Release Evidence Records use hashes and references only; they contain no
  user-text excerpts in V1.

### D0A-13 — Protected Case semantics — ACCEPTED

- Expected, prohibited, and allowed behavior are arrays of identified
  human-readable statements.
- Executable checks are a separate versioned discriminated union.
- Any semantic statement/check/replay/fixture change creates a new case
  version and requires new approval.
- Approver uses an opaque actor ID; optional display name; timestamp and source
  reference required.
- Qualification enum is exactly `READY | NEEDS_FIXTURE | NOT_YET`.
- Non-READY states require typed reason and safe explanation.
- Define the complete versioned configuration contract for all eight frozen V1
  deterministic assertion types in 0A. Execution remains out of scope.

### D0A-14 — Trial, evidence, gap, and comparison vocabulary — ACCEPTED

Structural vocabulary:

- execution: `COMPLETED | ERROR | TIMEOUT | REFUSED`;
- assertion/evaluator: `PASS | FAIL | UNEVALUABLE`;
- comparison:
  `COMPARABLE | FIRST_OBSERVATION | MOVED | INSUFFICIENT_EVIDENCE`;
- recommendation: `PASS | REVIEW | BLOCK`.

Minimum proposed gap codes:

- `MISSING_APPROVED_BASELINE`
- `EXECUTION_CONTRACT_MISMATCH`
- `MISSING_OBSERVATION`
- `NEGATIVE_ASSERTION_UNEVALUABLE`
- `EVALUATOR_TIMEOUT`
- `EVALUATOR_ERROR`
- `EVALUATOR_REFUSAL`
- `EVALUATOR_SCHEMA_INVALID`
- `INSUFFICIENT_TRIALS`
- `FIXTURE_REQUIRED`

Slice 0A validates shapes, references, uniqueness, ranges, and impossible
states. Slice 0B calculates comparison, evidence strength, rates, policy, and
recommendation.

### D0A-15 — Decision Attestation — ACCEPTED

- Include a minimal versioned schema and integrity rules in 0A.
- Do not implement attestation chaining, GitHub linking, or rendering until
  later slices.

### D0A-16 — Error contract and precedence — ACCEPTED

Error fields:

- stable error code;
- safe message;
- JSON Pointer path;
- contract kind;
- received schema version when safe;
- correlation ID.

Precedence:

```text
raw parse and resource limits
→ schema and version
→ cross-field/identity invariants
→ hash verification
```

Collect a bounded set of schema errors for readability. Abort before hashing
or producing a partial artifact.

### D0A-17 — Resource limits — ACCEPTED

- Input file: 16 MiB.
- Nesting depth: 64.
- Individual string: 1 MiB encoded as UTF-8.
- Events per trace: 10,000.
- Trials per record: 1,000.
- Assertions, evaluator results, and gaps per trial: 1,000 each.
- Validation errors returned: 100.
- Limits are hard, deterministic, and fail fast in 0A. A later change requires
  measurements and a successor decision.

### D0A-18 — Logging contract — ACCEPTED

- Core accepts an injected structured sink.
- CLI emits JSON Lines on stderr.
- Artifacts use stdout/files only.
- Correlation ID is caller-supplied or generated outside the canonical
  artifact.
- Allowlist safe log fields first; pattern redaction is defense in depth.
- Redaction occurs before invoking the sink.
- Terminal events are mandatory; start events are debug-level to reduce noise.
- Logs may vary in timestamp/duration but never affect artifact identity.
- If safe redaction cannot be guaranteed, logging fails closed without
  emitting the sensitive event.

### D0A-19 — Test strategy — ACCEPTED

- Fixed independently authored fixtures plus deterministic property/mutation
  tests.
- Property-test library and version pinned.
- Seed printed and stored in machine-readable test output.
- Any discovered failure becomes a committed fixed regression fixture.
- No blanket numeric coverage target in 0A; explicitly test every branch of
  schema, identity, canonicalization, hash, and verification logic.
- Signature/authenticity testing is explicitly out of scope.

### D0A-20 — UI decision — ACCEPTED

- Defer the TypeScript package manager and UI framework selection to Slice 0C.
- In 0A, prove that checked-in JSON Schema can generate a TypeScript type
  projection and that a tiny compile-only consumer can use it without
  introducing a second domain model.

- The compile proof uses Node.js 24.18.0 LTS, its bundled npm, and TypeScript
  6.0.0. These pins do not select the later UI framework.

## Acceptance test plan

The independent test author owns tests and fixtures. Expected canonical bytes
and digests must be hand-derived or independently calculated, never generated
by production code.

### Harness and valid RED

1. The test harness self-check passes.
2. The public black-box commands load without syntax, import, or dependency
   failure.
3. Every unimplemented acceptance behavior returns a stable `NOT_IMPLEMENTED`
   result.
4. RED failures are behavioral assertions, not broken setup.
5. Governance remains green during RED.

### Contract parsing

1. Minimal valid instance of every approved top-level contract parses.
2. Complete nested instances parse without dropping fields.
3. Removing each required field is rejected at its exact path.
4. Unknown fields at every nested boundary are rejected.
5. Unsupported versions and unknown discriminators are rejected.
6. Duplicate raw JSON object keys are rejected before ordinary validation.
7. Wrong types, invalid enums, empty IDs, and impossible union mixtures fail.
8. Invalid UTF-8/Unicode and disallowed numeric forms fail.
9. Absent optional fields and explicit null follow the approved rule.
10. Rejected input never produces a partially valid artifact.

### Canonicalization

1. Object-key permutation and whitespace differences yield identical bytes.
2. Canonical output matches published RFC vectors if JCS is approved.
3. Canonicalization is idempotent.
4. Ordered trace/tool event permutation changes canonical bytes.
5. Declared set-like permutation preserves canonical bytes.
6. Duplicate set elements fail rather than silently deduplicate.
7. Unicode composed/decomposed strings follow the approved preservation rule.
8. Escaped and literal equivalent Unicode serialize identically.
9. Control characters serialize unambiguously.
10. Numeric boundaries and disallowed representations follow the approved
    domain.
11. Locale, timezone, environment, and process do not change output.
12. Canonical bytes use the approved UTF-8/BOM/newline policy.

### Identity and tampering

1. Repeated same-process and cross-process hashing is byte-identical.
2. Golden digest matches an independent SHA-256 calculation.
3. Contract kind/version domain separation changes the digest.
4. Mutating each protected top-level field invalidates verification.
5. Mutating every nested evidence category invalidates verification.
6. Removing, replacing, or algorithm-confusing the stored digest fails.
7. Copying a valid hash to another record or contract kind fails.
8. Mutating ordered sequences fails.
9. Reordering approved set-like collections preserves verification.
10. Mutating `previous_record_hash` invalidates the current record.
11. Invalid integrity aborts and never becomes an evidence gap.
12. Failure precedence is stable when schema and hash defects coexist.
13. Verification does not mutate input.

### Cross-field invariants

1. Duplicate trial/event/check identities fail.
2. Sequence values and declared ordering agree.
3. Trial case version, side, code ref, and execution contract agree with the
   containing record.
4. Execution error/timeout/refusal cannot masquerade as completed.
5. Missing baseline uses an explicit state, not an absent parser field.
6. Counts remain within denominators.
7. Stored decimal rate matches counts if rates are approved for storage.
8. `FIRST_OBSERVATION` and `MOVED` cannot appear as recommendations.
9. Semantic Protected Case edits change the case version according to the
   approved coverage list.
10. Decision Attestation cannot mutate the referenced record.

### Logging and redaction

1. Validation, seal, and verification outcomes emit approved structured
   events.
2. Every event has service/version, contract kind/version, outcome, safe
   reason, and correlation ID.
3. Correlation propagates across parse, seal, and verify.
4. Secret sentinels placed in every sensitive field never reach the captured
   sink.
5. Credentials, headers, cookies, raw prompts/traces/tool payloads, and
   query-bearing URLs are absent.
6. Malformed input and validation errors never echo rejected raw values.
7. Control characters in IDs cannot forge additional log lines.
8. Redaction failure fails closed.
9. Logs and artifacts use separate output channels.
10. Logging configuration never changes canonical bytes or hash.

### Packaging and reproducibility

1. Clean locked install succeeds.
2. One command runs governance, format, lint, strict type, tests, build, and
   package checks.
3. Source and packaged CLI produce identical bytes and hashes.
4. Local and clean-container output hashes match.
5. Tests pass twice with identical deterministic artifacts.
6. Dependency versions, licenses, and purposes are recorded.
7. Compile-only consumer proves the contract type is reusable by later UI.

## Seed and fixture plan

The deterministic core uses no randomness.

Fixed fixture classes:

- minimal valid trace;
- complete conversational/tool trace;
- minimal and complete Protected Case;
- valid unsigned and sealed Release Evidence Record;
- record with explicit missing-baseline state;
- record with mismatch-shaped comparison state;
- record with evaluator-timeout gap shape;
- Unicode/numeric edge record;
- object-key-permuted equivalent;
- ordered-event mutation;
- one mutation per protected field class;
- malformed and unsupported-version inputs;
- duplicate-key input;
- secret-bearing rejected input;
- exact resource-limit boundaries.

Property/mutation seeds are fixed only after D0A-19 approval. For every run,
store:

- generator/library version;
- declared seed;
- fixture/input-universe hash;
- reproduction command;
- failing minimal case.

## File ownership

Proposed Python-core layout under the accepted D0A-01:

```text
src/triana/contracts/         implementation-author
src/triana/core/              implementation-author
src/triana/cli/               implementation-author
schemas/                      generated projection; orchestrator drift-checks
examples/typescript-consumer/ generated-type compile proof
tests/acceptance/             test-author
tests/fixtures/               test-author
tests/adversarial/            orchestrator
internal/SLICE_PACKET.md      orchestrator
docs/ and decision/provenance orchestrator
```

The implementation author may not edit acceptance tests, fixtures, expected
bytes, expected digests, seeds, or adversarial cases.

## Commands

Exact commands:

- lock: `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv lock --check`
- sync:
  `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv sync --locked --all-groups`
- governance: `./scripts/verify-governance.sh --working-tree`
- format: `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked ruff format --check src tests`
- lint: `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked ruff check src tests`
- type: `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked mypy src`
- RED/acceptance:
  `UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked pytest tests/acceptance -q`
- full verification will combine governance, format, lint, type, complete tests,
  deterministic repeatability, tamper, redaction, build, package, and
  container parity after the test author freezes their artifact set.
- reproduce will invoke the installed `triana` CLI over the frozen golden
  fixture selected by the test author.

## Test freeze requirements

Before the implementation author starts, the orchestrator must record:

- accepted owner decisions;
- canonical base commit;
- valid RED transcript and machine-readable report;
- frozen acceptance/fixture paths and hashes;
- independent golden-byte and digest derivation;
- proof no production-owned path was edited;
- adversarial cases reserved for integration;
- all reported ambiguities resolved by Akarsh.

Freeze result:

- 620 acceptance cases collected.
- 607 cases fail only at the approved behavioral RED boundary.
- 13 scaffold, oracle, manifest, property, and help cases pass.
- The independent harness/property subset passes twice in fresh processes.
- The manifest covers 85 closed object or union-arm boundaries, 395 required
  or active-conditional paths, all five public kinds, and every
  Release Evidence Record hash-preimage field.
- Fixture universe:
  `sha256:5c89669b9c8024870291524994fd8ac9f7a477fef93c0e8210db370519c3e6b3`.
- `OUTPUT_WRITE_FAILED` and `LOG_REDACTION_FAILED` remain explicit
  orchestrator-owned adversarial/unit cases because the public CLI exposes no
  deterministic portable black-box injection hook.
- The machine-readable counts, commands, hashes, and reservations are frozen
  in `internal/SLICE_0A_TEST_FREEZE.json`.

## Slice exit gate

Slice 0A completes only when:

- all owner decisions are recorded;
- frozen tests remain unchanged by implementation;
- every approved acceptance case is green;
- repeated and cross-process results are byte-identical;
- source, packaged CLI, and container produce identical fixture hashes;
- the tamper and adversarial matrices pass;
- no invalid integrity becomes an evidence gap or partial artifact;
- structured logs are correlated and redacted before reaching the sink;
- schemas/types do not drift;
- exact commands and machine-readable evidence are retained;
- dependencies and standards provenance are recorded;
- code, tests, canonical docs, decision log, and local decision memory agree;
- Akarsh can read the contract and hashing implementation and understand the
  protected preimage without framework indirection.

## Standards evidence considered

- [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785.html)
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12)
- [Node.js Crypto](https://nodejs.org/api/crypto.html)
- [Pydantic JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/)

These sources inform the recommendations only. No dependency or standard is
accepted until Akarsh approves the corresponding decision.
