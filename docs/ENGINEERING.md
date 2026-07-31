# Triana engineering and delivery policy

Status: **repository operating contract**

This document defines how humans and coding agents turn Triana decisions into
reviewable, reproducible changes. The active product authority identified in
`AGENTS.md` owns product scope; `docs/ARCHITECTURE.md` owns shared trust
boundaries where the active authority does not supersede it. This document
owns implementation and delivery practice.

## First principles

1. **The repository is memory.** Canonical documents and committed evidence
   outlive chats and agent sessions. Work is incomplete while they disagree.
2. **Human approval creates protected meaning.** Software and LLMs may propose
   or verify; they do not silently create semantic truth.
3. **Deterministic machinery owns release facts.** Identity, membership,
   denominators, arithmetic, comparability, policy rendering, hashing, and
   record chaining must be reproducible.
4. **Unknown is not pass.** Missing, skipped, invalid, and non-comparable
   evidence are explicit typed outcomes.
5. **Proof travels with claims.** A result names the inputs, versions,
   conditions, checks, gaps, and artifacts needed to reproduce it.
6. **Customer custody is a boundary.** Customer code, credentials, fixtures,
   and raw data stay in the execution location promised by the product.
7. **One clear path beats hidden fallback.** Dependencies and sources are
   explicit. A failed primary path does not silently switch meaning.
8. **Small changes preserve understanding.** Each commit should be reviewable,
   testable, and safe to revert on its own.
9. **Visible value arrives early.** A vertical slice must end in an executable
   or inspectable product result. The active product plan defines the concrete
   milestone; infrastructure alone is not a slice exit.
10. **Optimization follows measurement.** Correctness, clarity, and the first
    complete loop come before performance or infrastructure tuning. Optimize
    only a measured bottleneck against a stated target.

## Before an implementation slice

Write down the slice before writing implementation code. A plan, issue, pull
request description, or the active section of `internal/WORKING_MEMORY.md` may
hold it, but it must identify:

- the active product outcome advanced;
- inputs and outputs;
- deterministic, LLM, and human authority;
- privacy and execution location;
- gaps, invalid states, and refusal behavior;
- provenance for reused material;
- a reproducible acceptance test;
- explicit non-goals.
- a change budget naming expected files and areas, test-owned paths, production
  paths, explicitly untouched areas, permitted dependencies, and the maximum
  scope expansion that can occur without returning to the orchestrator.

An implementation can proceed when the user has explicitly requested it and
these points do not introduce a material choice beyond that request. Material
product, architecture, privacy, or repository-boundary changes require a human
decision and a new append-only decision-log entry.

## Vertical-slice development

Build through the product, not one technical layer at a time. Each slice
contains the smallest useful path across contracts, deterministic core,
interface, tests, evidence, and documentation:

```text
declared input
    ↓
strict validation
    ↓
deterministic processing
    ↓
versioned evidence artifact
    ↓
CLI or Release Review projection
```

For the suspended Release Review V1, the first three slices were:

1. **Contract kernel:** versioned contracts, strict parsing, canonical
   serialization, stable identity, hashing, golden fixtures, and round-trip
   verification.
2. **Comparison and policy:** A/A, planted A/B, comparability, denominators,
   typed gaps, Release Policy, record chaining, and tamper rejection.
3. **Visible Release Review:** one focused page rendering the same record and
   Decision Attestation contracts used by the CLI. It is not a dashboard.

The active Triana Labs milestone sequence is owned by its charter and current
plan. Do not restart or continue the suspended sequence without an explicit
resumption decision. For either product line, do not postpone all visible
output until ingestion and orchestration are complete: start with
deterministic fixtures, then replace fixture boundaries with real adapters.

Do not begin with authentication, billing, microservices, Kubernetes, event
buses, generic plugin systems, general workflow engines, or a large design
system unless an accepted slice cannot ship without them.

## Three-role slice protocol

Every implementation slice uses exactly two worker agents and the main
orchestrator. The roles run serially in a shared worktree. Use isolated
worktrees if genuine parallelism is necessary.

### 1. Orchestrator entry gate

The main orchestrator completes `internal/SLICE_PACKET.md` before worker edits.
It freezes:

- slice ID, canonical base commit, active product authority, and product
  outcome;
- input/output contracts and public behavior table;
- deterministic, LLM, customer-evaluator, and human authority;
- privacy and execution location;
- abort conditions versus typed evidence gaps;
- provenance and allowed source material;
- deterministic seed policy and fixture identities;
- explicit non-goals and file ownership;
- the change budget: expected files or bounded path patterns, expected
  production and test areas, explicitly untouched areas, whether any new
  dependency is allowed, and the maximum acceptable scope expansion;
- exact RED and final verification commands.

Unresolved product, architecture, privacy, or semantic choices go to
`internal/WORKING_MEMORY.md` and stop the slice. Accepted durable choices are
appended to `internal/DECISION_LOG.md`.

The change budget is a review boundary, not a target to consume. A worker must
stop and report before editing outside it. The orchestrator may narrow or
clarify the budget before the edit occurs. Expanding it after work begins
requires a written reason; any material product, architecture, privacy, or
repository-boundary expansion requires the human decision already mandated
above.

### 2. Independent test author

The test-author agent starts from the frozen base and edits only test-owned
paths and purpose-built fixtures declared in the slice packet. It:

- writes black-box acceptance tests against public behavior;
- covers success, meaningful failure, every introduced gap/refusal state,
  integrity/tamper behavior, and required logging/redaction;
- derives expected values independently rather than generating goldens from
  production code;
- runs the tests and records a valid RED result caused by missing behavior,
  not by syntax, imports, or broken setup;
- reports ambiguity instead of inventing product meaning.

The test author does not write production code.

### 3. Orchestrator test freeze

The orchestrator reviews the tests against the active product authority named
in `AGENTS.md`, applicable shared architecture and contracts, and the slice
packet. It verifies RED on the canonical base, then records the test commit or
content hashes and freezes the owned paths.

Acceptance tests may be visible to the implementation author. Independence
comes from ownership and freeze, not artificial secrecy. The orchestrator also
declares a small additional adversarial matrix so implementation cannot merely
memorize literal fixtures.

### 4. Independent implementation author

The implementation-author agent receives the slice packet, frozen tests, and
valid RED evidence. It edits only production-owned paths and:

- implements the smallest readable behavior that satisfies the contract;
- does not change tests, fixtures, seed lists, expected outputs, or goldens;
- does not add retry-to-green, silent fallback, skipped assertions, or
  implementation-specific exceptions to the contract;
- reports a suspected test defect to the orchestrator with evidence;
- adds no dependency or abstraction unless acceptance requires it and its
  purpose, version, ownership, and license are recorded.

The implementation author does not approve the slice.

When debugging, the implementation author follows the single-hypothesis loop
defined below. It must not bundle multiple speculative fixes into one
iteration.

### 5. Orchestrator integration and exit

The orchestrator integrates test work before implementation work and rejects
any implementation diff that touches frozen test-owned paths. It:

- runs governance, formatting, lint, type, unit, acceptance, build, and package
  gates;
- runs the declared seed matrix, repeatability checks, tamper cases, and
  failure injection;
- inspects generated records and the visible UI independently;
- verifies structured logs, correlation, and redaction;
- checks that no missing evidence became PASS;
- checks decisions, doubts, provenance, canonical docs, and local decision
  memory;
- reconciles the declared change budget against the actual diff and rejects
  unexplained files, dependencies, formatting, cleanup, or scope expansion;
- records exact commands and artifacts;
- records the structured uncertainty handoff defined below;
- alone declares the slice complete.

The orchestrator does not directly repair failed production or acceptance
logic. Implementation defects return to the implementation author; test
defects return to the test author.

### Frozen-test change rule

After freeze, acceptance behavior changes only through a separate test-author
change labeled as a test defect, with orchestrator rationale. The corrected
test must still demonstrate valid RED against the pre-implementation base.

Semantic weakening requires a human product decision and append-only decision
entry. Never combine relaxed acceptance criteria and production changes in one
commit.

## Single-hypothesis debugging loop

Debugging is an evidence loop, not a sequence of plausible edits. Before each
debugging change, record:

```text
Observed failure:
Smallest reproduction:
Current hypothesis:
Evidence that would falsify it:
One change attempted:
Result:
Regression test or fixture:
```

Rules:

- read the complete error and relevant trace before forming the hypothesis;
- reproduce the failure before changing production behavior whenever the
  failure is locally reproducible;
- make one causal intervention per iteration; mechanical edits required to
  compile that intervention count as the same change, but unrelated fixes do
  not;
- run the smallest discriminating check first, then the required broader gate;
- if the result falsifies the hypothesis, remove or isolate the speculative
  change before starting the next hypothesis;
- never hide an unexplained state with a default, retry, null guard, broader
  exception handler, or weakened assertion;
- promote a confirmed defect to a stable regression test or fixture with a
  reproduction command;
- preserve failed attempts when they affect interpretation, cost, or
  reproducibility.

The loop may live in the slice packet, agent handoff, issue, or local decision
journal. It must be inspectable by the orchestrator. Test defects still return
to the test author and implementation defects still return to the
implementation author.

## Seeds, fixtures, and nondeterminism

Deterministic core code—schemas, canonicalization, identity, arithmetic,
hashing, comparison, policy, and chaining—must not depend on randomness.

When sampling or randomized trials are part of a slice:

- sort the input universe before sampling;
- derive or declare the seed before candidate execution;
- record seed, generator version, input identity, case version, and fixture
  hash;
- use identical paired seeds and trial indices for baseline and candidate;
- keep separate random streams for separate purposes;
- never use wall-clock time or ambient entropy as an implicit seed;
- never hand-pick a favorable seed or rerun until green;
- preserve retries as new attempts rather than overwriting the first result;
- repeat identical deterministic inputs at least twice and block the slice if
  artifacts or outcomes differ;
- promote every discovered failing seed into a fixed regression fixture with a
  reproduction command.

A seed controls declared randomness; it does not make an external LLM or
provider deterministic. Provider variability is measured through explicit
repeated trials and reported evidence.

Kairos-AI corpora involving coding agents or agent-development sessions may be
used only as labeled engineering stress tests for adapters, replayability,
hashing, or tooling. Unless an active product authority explicitly includes
them, they cannot be presented as product acceptance evidence or customer
ground truth.

## Decision memory

Triana uses two levels of memory.

### Curated durable record

`internal/DECISION_LOG.md` contains accepted or autonomously executed durable
decisions. It is committed and append-only.

Every entry uses:

```text
- What: <decision> | Why: <reason> | When: YYYY-MM-DD | Whom: <decision maker and executor>
```

Rules:

- append the entry in the same change that executes the decision;
- include the rejected or replaced direction in `Why` when it matters;
- reverse or correct by appending a new entry with `Supersedes: <prior
  decision description or identifier>`;
- update any canonical document affected by the decision in the same commit;
- keep questions, alternatives, requests, and unaccepted ideas in
  `internal/WORKING_MEMORY.md`.

### Local per-commit journal

Every commit gets a local entry in
`.decision-memory/<YYYY-MM-DD>-<branch>.md`:

```markdown
## <short hash> — <subject>

- Why: <intent and rejected alternatives>
- Evidence: <tests, commands, inspection, or generated artifacts>
- Trace: <decision-log entry, work item, issue, or "no durable decision">
```

The journal is gitignored. The post-commit hook creates the entry; the
committer fills it in before the next commit or push. It captures intent while
fresh. Durable content is promoted to the committed decision log.

## Implementation practice

- Inspect `git status`, nearby code, tests, and canonical docs first.
- Preserve unrelated changes. Never clean, reset, overwrite, or reformat work
  outside the requested slice.
- Prefer the smallest design that satisfies the acceptance test.
- Add a dependency only when its maintained behavior is materially safer or
  simpler than owning the equivalent code. Record its version, license, and
  purpose.
- Keep imports and dependency direction explicit. Do not hide architecture
  cycles with local imports or runtime lookup tricks.
- Catch only errors that can be handled at that boundary. Do not convert
  failure into empty data, `None`, or a default that downstream code can read
  as success.
- Model skips, timeouts, schema failures, missing observations, and
  non-comparability explicitly and include them in denominators.
- Do not log secrets, credentials, raw customer payloads, or unnecessary
  personally identifiable information.
- Comments explain authority, invariants, ordering, refusal, or a non-obvious
  tradeoff. They do not narrate obvious syntax.
- Keep domain names identical across contracts, core logic, tests, CLI, API,
  and UI. Prefer explicit functions and narrow modules over framework magic.
- Keep business rules in the deterministic core. CLI, API, PR comments, and UI
  may validate inputs and render results; they must not independently calculate
  recommendations, comparability, denominators, hashes, or record identity.

## Failure model

“Fail fast” and “unknown is not pass” are complementary:

### Abort immediately

Reject the operation at the boundary for:

- invalid configuration or an unsupported contract version;
- malformed input or schema violation;
- missing required identity;
- hash, signature, or record-chain mismatch;
- an impossible state transition;
- an unsafe execution contract;
- an internal invariant or arithmetic violation.

These are integrity or programming failures. Do not convert them into a gap,
empty result, default recommendation, or partial success.

### Continue with a typed evidence state

Preserve the run and weaken its claim for:

- evaluator timeout, error, refusal, or schema failure;
- missing observation required by an assertion;
- an unevaluable negative assertion;
- missing approved baseline;
- mismatched execution conditions;
- insufficient trials;
- a safely bounded fixture requirement.

These are expected evidence conditions. Represent them as typed results with
reason, scope, evidence reference, and policy consequence. They never become
implicit exclusion or PASS.

## Structured logging

Log enough to reconstruct why the system accepted, rejected, compared, or
recommended. Do not interpret “log everything” as permission to store customer
payloads or secrets.

Every structured event includes, when applicable:

- timestamp, event name, severity, service, and version;
- run, case, trial, side, code-ref, trace, policy, and record identifiers;
- contract and schema versions;
- state transition or boundary entered;
- outcome, typed reason, and duration;
- evidence keys read, never unnecessary raw evidence;
- denominator inputs and policy rule selected;
- correlation and causation identifiers.

Emit events at:

- configuration and schema validation;
- execution start, finish, refusal, and timeout;
- assertion and customer-evaluator boundaries;
- gap creation;
- comparability and denominator calculation;
- Release Policy evaluation;
- record creation, verification, chaining, and rejection;
- Decision Attestation append;
- API and UI request failure boundaries.

Never log credentials, authorization headers, raw secrets, full customer
prompts or traces by default, unredacted tool payloads, or unnecessary personal
data. Redaction happens before the logging call and is covered by tests.

## Tests and evidence

- Begin each slice with an executable acceptance test and observe it fail for
  the expected reason.
- Implement the smallest behavior that makes the test pass, then refactor only
  while the gate remains green.
- Tests land with the implementation they protect, in the same commit.
- Test the success path, the meaningful failure path, and every refusal or gap
  state introduced by the slice.
- Deterministic rules need positive and negative fixtures.
- Hashing, identity, ordering, arithmetic, and comparison logic need stable
  round-trip or golden tests where appropriate.
- Every quantitative or release-facing claim must be regenerable from a
  checked-in command and declared inputs.
- Run `./scripts/verify-governance.sh` plus the stack-specific lint, type,
  test, and build commands before commit.
- Record the exact verification in the commit body and local decision journal.
- A slice does not advance because files exist. Its declared acceptance test
  must pass and its user-visible or machine-verifiable output must be
  inspectable.

The stack-specific gate will be added with the first implementation slice.
Until then, the governance verifier is the repository gate.

## Local and CI gates

The chosen stack must expose one versioned local verification command that CI
invokes unchanged. Do not maintain separate local and hosted definitions of
quality.

The complete gate includes:

1. governance, decision-memory, provenance, and secret checks;
2. locked and reproducible dependency installation;
3. format and lint checks;
4. strict static typing;
5. unit and contract tests;
6. black-box acceptance and golden-fixture tests;
7. deterministic repeatability, seed matrix, and tamper tests;
8. redaction and negative architecture guards;
9. build, package, and UI-render/browser smoke checks;
10. artifact-to-document claim consistency once published fixture values
    exist.

Use fail-fast tests during the RED/GREEN loop for quick feedback. CI must still
produce complete test evidence; the first failure must not hide the remaining
suite. Any skipped integration lane reports its count and reason and cannot be
the sole evidence for a required acceptance behavior.

Coverage is diagnostic, not proof. Every branch of identity, hashing,
denominator, comparability, gap, policy, and record-chain logic must have
explicit behavioral tests. Set a numeric repository threshold only after the
first stack and test layout exist; once set, enforce it mechanically.

Pin dependency resolution. Pin CI actions and build tools to immutable
versions where supported. Set timeouts, cancel superseded CI runs, and retain
machine-readable test and coverage artifacts when those systems are added.

## Git workflow

### Branches

- Work on a topic branch, never directly on `main`.
- Codex branches use `codex/<short-purpose>` by default.
- Claude Code branches use `claude/<short-purpose>` by default.
- Humans may use `feat/`, `fix/`, `docs/`, or another clear topic prefix.
- Rebase or merge only with awareness of uncommitted user work. Never use a
  destructive reset to make history convenient.

### Commits

Use Conventional Commits:

```text
<type>(optional-scope): <imperative summary>

Why:
- <reason>

Evidence:
- <command or inspection and result>

Decision:
- <decision-log reference or "no durable decision">
```

Allowed common types are `feat`, `fix`, `docs`, `test`, `refactor`, `perf`,
`build`, `ci`, `chore`, and `revert`.

A commit:

- represents one coherent behavior or policy change;
- includes its tests and required documentation;
- contains no unrelated formatting or cleanup;
- leaves the repository gate green;
- has a completed local decision-memory entry before another commit or push.

Do not use `--no-verify`. Do not amend or rewrite a commit that another person
may already rely on without explicit coordination.

### Push and pull requests

- Review `git status`, the branch name, staged diff, and commits being pushed.
- Push only the current topic branch. Never push directly to `main`.
- Never force-push unless the user explicitly authorizes the exact branch and
  collaborators have been checked.
- A pull request explains the outcome, why it matters, decisions changed,
  tests run, evidence or screenshots, known gaps, privacy impact, and rollback.
- CI evidence supplements local evidence; it does not erase a known local
  failure.

## Review checklist

- Does the change stay inside the active product authority and approved
  implementation slice?
- Does every changed file and dependency fit the declared change budget?
- Were debugging fixes supported by one reproduced, falsifiable hypothesis at
  a time?
- Is human, deterministic, LLM, and customer-evaluator authority explicit?
- Can missing evidence accidentally become a pass?
- Are baseline and candidate actually comparable before regression language?
- Are privacy and execution-location promises preserved?
- Are IDs, denominators, arithmetic, hashes, and ordering deterministic?
- Are failure and refusal paths visible and tested?
- Is every reused artifact provenance-safe and recorded?
- Are canonical docs and the append-only decision log current?
- Can another engineer reproduce the claimed evidence?

## Completion

A slice is complete only when implementation, tests, verification, provenance,
canonical docs, and decision memory agree.

Every worker and orchestrator handoff must state:

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

Use `none` where a field is empty. Do not replace evidence with “should work,”
and do not imply that an unrun check passed. The orchestrator's final handoff
must distinguish observed facts, reasoned inferences, and unresolved
uncertainty.
