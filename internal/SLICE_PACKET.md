# Active implementation slice — LABS-01 Trace Observer

Status: **LABS-01B ARCHITECTURE TESTS FROZEN; IMPLEMENTATION AUTHORIZED**

Date: 2026-07-31
Canonical base before slice plan: `6d86624`
Product authority: `triana-labs/CHARTER.md`
Execution authority:
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`
Engineering authority: `docs/ENGINEERING.md`
Provenance authority: `docs/PROVENANCE.md`
Orchestrator: primary Codex agent
Independent test author: separate worker agent, assigned after scaffold freeze
Implementation author: separate worker agent, limited first to the RED scaffold

## 1. Slice identity and product outcome

Slice ID: `LABS-01-trace-observer-synthetic`

Component advanced: **Trace Observer**

This slice creates the first readable Triana Labs product artifact:

> Given a bounded JSONL corpus explicitly labeled synthetic, validate and
> normalize every trace, account for every input line as accepted or rejected,
> identify which accepted traces can support later case generation, and emit a
> deterministic machine-readable corpus bundle plus a Markdown explanation.

The public command is:

```text
triana traces observe <input.jsonl> --out <new-output-directory>
```

This slice is intentionally restricted to `privacy_class: "SYNTHETIC"`.
`LOCAL_SENSITIVE` and real customer traces are refused until a later
redaction/authorization slice freezes and tests that boundary. The restriction
is a truthful safety boundary, not a fixture shortcut.

## 2. User-visible deliverable

For a mixed five-line fixture:

```text
5 input lines
├── 3 accepted traces
│   ├── 2 case-generation eligible
│   └── 1 structurally valid but not eligible
└── 2 rejected traces
    ├── malformed JSON
    └── orphaned tool result
```

the command creates:

```text
<output-directory>/
  manifest.json
  normalized_traces.jsonl
  rejected_traces.jsonl
  corpus_profile.json
  corpus_profile.md
```

It writes one concise receipt to stdout:

```json
{
  "accepted_count": 3,
  "case_generation_eligible_count": 2,
  "manifest_path": "<output-directory>/manifest.json",
  "outcome": "COMPLETED_WITH_REJECTIONS",
  "rejected_count": 2
}
```

Paths in stdout are presentation values and are not stored in portable
artifacts or logs. The receipt is not identity-bearing.

## 3. Inputs and exact Trace contract

### 3.1 Raw boundary

- Input is a local regular file path; stdin, URLs, directories, devices, and
  symlinks are refused in LABS-01.
- Raw file maximum: 16 MiB.
- Maximum physical lines: 1,000.
- Maximum raw line size including newline: 1 MiB.
- File is read as bytes and split on LF.
- CRLF is accepted by stripping one terminal CR before decoding.
- A final missing LF is accepted.
- Empty file has zero input lines.
- A blank or whitespace-only physical line counts as one rejected input line.
- Each nonblank line is decoded as strict UTF-8 and parsed independently.
- A UTF-8 BOM on the first line is rejected as `BOM_FORBIDDEN`.
- Duplicate JSON object keys are rejected before schema validation.
- JSON depth maximum: 32.
- Bare `NaN`, `Infinity`, and `-Infinity` tokens are not strict JSON and are
  rejected as `MALFORMED_JSON`.
- Finite fractional or exponent-form JSON numbers are syntactically valid but
  outside the LABS-01 scalar contract and are rejected as
  `SCHEMA_VALIDATION_FAILED`.

Every physical input line is counted exactly once:

```text
input_count = accepted_count + rejected_count
```

No fatal file-boundary error produces a partial output directory.

### 3.2 Top-level `PreviewTrace`

Every accepted line is one closed JSON object:

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | literal `"preview_trace"` | required |
| `schema_version` | strict integer `1` | required |
| `privacy_class` | literal `"SYNTHETIC"` | required |
| `trace_id` | `SafeId` | required |
| `source_trace_id` | `ExternalId` | required |
| `events` | ordered array of 1–1,000 `PreviewEvent` values | required |

Unknown fields are rejected. Missing fields are rejected. `null` never
substitutes for absence or a required value.

`SafeId` is ASCII 1–128 bytes matching:

```text
^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$
```

`ExternalId` is UTF-8 1–512 bytes with C0/C1 controls forbidden.

### 3.3 Shared event fields

Every event is a closed object with:

| Field | Type | Presence |
|---|---|---|
| `sequence` | strict integer `0..9007199254740991` | required |
| `event_kind` | closed discriminator | required |

Event sequence must equal exactly `0..len(events)-1`.

### 3.4 Event variants

`USER_MESSAGE`

```json
{
  "sequence": 0,
  "event_kind": "USER_MESSAGE",
  "content": "..."
}
```

`content` is UTF-8 1–65,536 bytes. LF is allowed; other C0/C1 controls are
forbidden.

`ASSISTANT_MESSAGE`

```json
{
  "sequence": 1,
  "event_kind": "ASSISTANT_MESSAGE",
  "content": "...",
  "is_final": false
}
```

`content` may be empty and is limited to 65,536 UTF-8 bytes. `is_final` is a
strict boolean.

`SYSTEM_VISIBLE_MESSAGE`

```json
{
  "sequence": 0,
  "event_kind": "SYSTEM_VISIBLE_MESSAGE",
  "content": "..."
}
```

Content rules equal `USER_MESSAGE`.

`TOOL_CALL`

```json
{
  "sequence": 2,
  "event_kind": "TOOL_CALL",
  "call_id": "call-1",
  "tool_name": "lookup_order",
  "arguments": {}
}
```

`call_id` and `tool_name` are `SafeId`. `arguments` is an opaque JSON value
limited by the line/depth/string rules. It permits null, booleans, safe
integers, strings, arrays, and objects. Floats remain forbidden.

`TOOL_RESULT`

Successful:

```json
{
  "sequence": 3,
  "event_kind": "TOOL_RESULT",
  "call_id": "call-1",
  "result_state": "SUCCEEDED",
  "result": {}
}
```

Failed:

```json
{
  "sequence": 3,
  "event_kind": "TOOL_RESULT",
  "call_id": "call-1",
  "result_state": "ERROR",
  "error_code": "ORDER_NOT_FOUND"
}
```

`SUCCEEDED` requires `result` and forbids `error_code`. `ERROR` requires
`error_code: SafeCode` and forbids `result`. `SafeCode` matches
`^[A-Z][A-Z0-9_]{0,63}$`.

`TERMINAL`

```json
{
  "sequence": 4,
  "event_kind": "TERMINAL",
  "terminal_state": "SUCCESS"
}
```

`terminal_state` is `SUCCESS | ERROR | ABORTED`. `SUCCESS` forbids
`reason_code`; other states require `reason_code: SafeCode`.

### 3.5 Cross-field trace invariants

- Event sequences are contiguous from zero.
- `call_id` values on `TOOL_CALL` are unique.
- Every `TOOL_RESULT.call_id` names exactly one earlier `TOOL_CALL`.
- At most one result exists per call.
- At most one assistant message has `is_final: true`.
- At most one terminal event exists.
- A terminal event, when present, is last.
- A final assistant message, when present with a terminal, precedes it.
- Duplicate `trace_id` across accepted input lines rejects the later line as
  `DUPLICATE_TRACE_ID`; the first accepted line remains.
- Duplicate `source_trace_id` across accepted input lines rejects the later
  line as `DUPLICATE_SOURCE_TRACE_ID`.
- Rejected lines never reserve either ID.

### 3.6 Case-generation eligibility

An accepted trace is `case_generation_eligible` exactly when:

1. it contains at least one `USER_MESSAGE`; and
2. after at least one user message, it contains an `ASSISTANT_MESSAGE` or
   `TOOL_CALL`.

Eligibility is a mechanical readiness observation. It is not a generated case,
quality score, accepted behavior, or finding.

## 4. Output contracts

All output files use UTF-8, LF, no BOM, sorted object keys, compact JSON for
JSON/JSONL, and exactly one terminal LF. Arrays retain semantic order. Object
keys are sorted. The same accepted input produces byte-identical portable
artifacts across repeated fresh processes.

No output contains timestamps, random IDs, absolute paths, usernames,
hostnames, environment values, or ambient locale/timezone data.

### 4.1 `normalized_traces.jsonl`

- Contains accepted traces only.
- Preserves accepted input-line order.
- Each line is the normalized closed `PreviewTrace`.
- Content is retained only because the slice accepts synthetic data.
- The file is empty, with zero bytes, when no trace is accepted.

### 4.2 `rejected_traces.jsonl`

One safe closed record per rejected input line:

```json
{
  "line_number": 4,
  "code": "MALFORMED_JSON",
  "json_pointer": "",
  "safe_message": "Input line is not valid JSON."
}
```

Rules:

- Physical line numbers are one-based.
- Records preserve input-line order.
- No rejected value, content excerpt, path, exception, or raw line is present.
- `safe_message` is not a byte-stable API; code and pointer are.

Closed line-rejection codes:

```text
BLANK_LINE
INVALID_UTF8
BOM_FORBIDDEN
LINE_TOO_LARGE
MALFORMED_JSON
DUPLICATE_JSON_KEY
NESTING_TOO_DEEP
SCHEMA_VALIDATION_FAILED
UNSUPPORTED_SCHEMA_VERSION
UNSUPPORTED_PRIVACY_CLASS
DUPLICATE_TRACE_ID
DUPLICATE_SOURCE_TRACE_ID
IMPOSSIBLE_TRACE_STATE
```

### 4.3 `corpus_profile.json`

Closed deterministic structure:

```json
{
  "artifact_kind": "corpus_profile",
  "schema_version": 1,
  "input_count": 5,
  "accepted_count": 3,
  "rejected_count": 2,
  "case_generation_eligible_count": 2,
  "event_kind_counts": {
    "ASSISTANT_MESSAGE": 2,
    "SYSTEM_VISIBLE_MESSAGE": 2,
    "TERMINAL": 1,
    "TOOL_CALL": 1,
    "TOOL_RESULT": 1,
    "USER_MESSAGE": 2
  },
  "tool_call_counts": {
    "lookup_order": 1
  },
  "terminal_state_counts": {
    "ABORTED": 0,
    "ERROR": 0,
    "SUCCESS": 1
  },
  "rejection_code_counts": {
    "IMPOSSIBLE_TRACE_STATE": 1,
    "MALFORMED_JSON": 1
  },
  "language_analysis": "NOT_EVALUATED",
  "distress_analysis": "NOT_EVALUATED"
}
```

The canonical mixed fixture behind these counts has:

- accepted trace 1: `SYSTEM_VISIBLE_MESSAGE`, `USER_MESSAGE`,
  non-final `ASSISTANT_MESSAGE`, `TOOL_CALL lookup_order`, successful
  `TOOL_RESULT`, and `TERMINAL SUCCESS`;
- accepted trace 2: `USER_MESSAGE` followed by final
  `ASSISTANT_MESSAGE`;
- accepted trace 3: one `SYSTEM_VISIBLE_MESSAGE`, making it structurally valid
  but mechanically ineligible;
- rejected line 4: malformed JSON;
- rejected line 5: an orphan tool result producing
  `IMPOSSIBLE_TRACE_STATE`.

The accepted universe therefore contains exactly nine events. This explicit
construction is normative for the five-line acceptance fixture.

Tool-name keys sort by UTF-8 bytes. Closed event and terminal maps include zero
counts. Rejection counts include only codes present and sort by code.

### 4.4 `corpus_profile.md`

Human projection generated only from `corpus_profile.json` and the manifest.
It contains:

- title and explicit `SYNTHETIC` fidelity;
- input, accepted, rejected, and eligible counts;
- event-kind table;
- tool-call table or explicit “none observed”;
- terminal-state table;
- rejection-code table or explicit “none rejected”;
- explicit statements that language, distress, personas, intents, cases,
  execution, and comparison were not evaluated;
- relative artifact filenames, never absolute paths.

The Markdown renderer performs no independent counting.

### 4.5 `manifest.json`

Closed deterministic structure:

```json
{
  "artifact_kind": "corpus_manifest",
  "schema_version": 1,
  "privacy_class": "SYNTHETIC",
  "input_count": 5,
  "accepted_count": 3,
  "rejected_count": 2,
  "case_generation_eligible_count": 2,
  "artifacts": {
    "normalized_traces.jsonl": "sha256:...",
    "rejected_traces.jsonl": "sha256:...",
    "corpus_profile.json": "sha256:...",
    "corpus_profile.md": "sha256:..."
  }
}
```

Each digest is lowercase SHA-256 over exact artifact bytes. LABS-01 does not
introduce a self-hash or domain-separated public document identity. The later
Labs contract-kernel slice owns that decision. Hashing is permitted here
because the input is structurally restricted to synthetic data.

## 5. CLI and failure behavior

### 5.1 Success and partial success

- Exit `0`: at least one input line and every line accepted.
- Exit `10`: command completed and artifacts exist, but at least one line was
  rejected or input was empty.
- Stdout is one compact JSON receipt plus LF.
- Stderr is exactly one safe terminal JSON log event plus LF.
- Output directory contains exactly the five declared files.

Empty input creates the five deterministic zero-count artifacts, returns
`outcome: "EMPTY_CORPUS"`, and exits `10`.

### 5.2 Fatal refusal

Fatal conditions create no target output directory:

| Code | Exit |
|---|---:|
| `CLI_USAGE_ERROR` | 2 |
| `INPUT_READ_FAILED` | 2 |
| `INPUT_NOT_REGULAR_FILE` | 2 |
| `INPUT_SYMLINK_FORBIDDEN` | 2 |
| `OUTPUT_PARENT_MISSING` | 2 |
| `OUTPUT_ALREADY_EXISTS` | 2 |
| `INPUT_TOO_LARGE` | 3 |
| `TOO_MANY_LINES` | 3 |
| `OUTPUT_WRITE_FAILED` | 7 |
| `INTERNAL_INVARIANT_FAILED` | 70 |
| `NOT_IMPLEMENTED` | 70, scaffold only |

### 5.3 Atomic output

- The target output directory must not exist.
- Its immediate parent must already exist and be a real directory.
- The implementation writes a uniquely named private temporary sibling.
- All five files are flushed and closed before one atomic rename.
- Any failure removes only the exact temporary sibling created by the command.
- The command never overwrites or merges with an existing directory.
- Cleanup failure is logged safely and returns internal failure without
  deleting or changing unrelated paths.

### 5.4 Logging

Exactly one terminal JSONL event:

```text
triana.traces.observe.succeeded
triana.traces.observe.completed_with_rejections
triana.traces.observe.rejected
```

Severity is exact: `succeeded` and `completed_with_rejections` use `INFO`;
`rejected` uses `ERROR`.

Safe fields:

```text
event_name
severity
service = "triana-labs-cli"
service_version
command = "traces.observe"
outcome
input_count
accepted_count
rejected_count
case_generation_eligible_count
reason_code
duration_ms
```

Logs never contain input/output paths, trace IDs, source IDs, content, tool
names, arguments/results, rejected values, exceptions, environment values, or
artifact hashes.

`--help` exits zero, writes human help to stdout, and emits no terminal log.

## 6. Deterministic versus LLM versus human authority

Deterministic code owns:

- byte/line/resource accounting;
- parsing and schema validation;
- trace/event identity uniqueness;
- trace invariants;
- eligibility;
- all counts;
- artifact bytes, ordering, and hashes;
- exit status and refusal behavior.

No LLM/provider participates. No corpus semantics, persona, intent, distress,
language, case, finding, or accepted behavior is inferred.

The human owns:

- authorization to supply the synthetic fixture;
- later semantic review;
- any future decision to admit local-sensitive data.

## 7. Privacy and execution location

- Execution is entirely local.
- Network access is forbidden and covered by a negative test.
- Only `privacy_class: "SYNTHETIC"` is accepted.
- Real or local-sensitive data is rejected per line and never copied to
  normalized output.
- Logs and rejection artifacts contain no raw values.
- No provider key, model, redaction rule, consent, or egress is used.
- Test fixtures are newly authored synthetic data.

## 8. Provenance

- No code or fixture is copied from Agentagon, HRAI, Kairos, or Kairos-AI.
- The public behavior is newly specified from active Triana Labs authority.
- Python packaging style may follow repository conventions but no external
  implementation is copied.
- Standard-library SHA-256 and JSON are used.
- Pydantic may be added as the one approved runtime dependency for strict
  readable boundary models; exact resolved version is locked.
- Any additional dependency is forbidden without orchestrator return and a
  written license/purpose decision.

## 9. Reproducibility and seed policy

The slice uses no randomness in product behavior.

Property tests use the repository-approved deterministic practice:

```text
seed: 2026073101
max_examples: 100
deadline: none
database: none
```

Every property entrypoint supplies the seed. A discovered counterexample
becomes a fixed synthetic fixture before exit.

## 10. Change budget

### 10.1 Planning commit

Expected files:

```text
internal/SLICE_PACKET.md
internal/DECISION_LOG.md
```

No code, test, dependency, schema, or fixture changes.

### 10.2 RED scaffold

Implementation-author owned:

```text
triana-labs/.python-version
triana-labs/pyproject.toml
triana-labs/uv.lock
triana-labs/src/triana_labs/__init__.py
triana-labs/src/triana_labs/__main__.py
triana-labs/src/triana_labs/cli.py
```

Behavior is limited to package import, `--help`, and deterministic
`NOT_IMPLEMENTED` for `triana traces observe`. No observer logic is allowed.

### 10.3 Independent test author

Test-author owned:

```text
triana-labs/tests/acceptance/**
triana-labs/tests/fixtures/**
```

The test author may not edit production, packaging, docs, decisions, or
orchestrator adversarial paths.

### 10.4 Implementation author after test freeze

Implementation-author owned:

```text
triana-labs/src/triana_labs/contracts/**
triana-labs/src/triana_labs/observer/**
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/__init__.py
triana-labs/src/triana_labs/__main__.py
triana-labs/pyproject.toml
triana-labs/uv.lock
```

Acceptance tests and fixtures are frozen and forbidden.

### 10.5 Orchestrator owned

```text
triana-labs/tests/adversarial/**
triana-labs/scripts/verify.sh
internal/SLICE_PACKET.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
docs/PROVENANCE.md
README.md
```

Only files necessary for exit evidence or canonical alignment may be edited.

### 10.6 Explicitly untouched

```text
triana-core/**
docs/PRODUCT.md
docs/CONTRACTS.md
docs/ARCHITECTURE.md
historical research/**
all external repositories and raw corpora
```

No UI, HTML application, provider, HRAI adapter, corpus-intelligence,
case-generator, panel, runner, comparison, or ruling code.

Maximum scope expansion without orchestrator return: none. Every worker stops
before editing an unlisted path, adding a dependency, changing a frozen
contract, or weakening a test.

## 11. Worker sequence and ownership

1. Orchestrator commits this packet and append-only slice decision.
2. Implementation author creates only the RED scaffold. This narrow exception
   is required so independent RED fails on behavior rather than package/import
   setup; it matches the repository's recorded Slice 0A precedent.
3. Orchestrator verifies and freezes the scaffold commit as canonical RED base.
4. Independent test author writes black-box tests/fixtures and demonstrates
   RED against `NOT_IMPLEMENTED`.
5. Orchestrator audits completeness, reproduces RED, hashes and freezes
   test-owned paths, and commits the test contract.
6. Implementation author implements production behavior without editing
   frozen tests/fixtures.
7. Orchestrator runs full and reserved adversarial verification. Test defects
   return only to the test author; implementation defects only to the
   implementation author.
8. Orchestrator alone declares exit.

The same implementation-author agent owns both scaffold and later production
work. It receives no test-author role.

## 12. Required acceptance matrix

The independent suite covers at minimum:

### Success

- one minimal valid trace;
- one complete trace using every event variant;
- all-valid multi-line corpus;
- mixed accepted/rejected corpus with exact five-line counts;
- CRLF and missing-final-LF equivalence;
- deterministic repeat in fresh processes;
- output hashes match independent calculations;
- Markdown values match JSON values.

### Per-line rejection

- blank line;
- invalid UTF-8;
- BOM;
- oversized line;
- malformed JSON;
- duplicate JSON key;
- nesting overflow;
- non-object root;
- missing/unknown fields;
- wrong types and null;
- wrong kind/version/privacy class;
- invalid identifiers/content/control characters;
- arbitrary float/NaN/infinity;
- empty events and too many events;
- non-contiguous sequence;
- duplicate/orphan/repeated tool results;
- invalid result/terminal companion fields;
- multiple/misplaced terminal/final events;
- duplicate trace/source IDs.

### Accounting and eligibility

- every physical line counted exactly once;
- rejected IDs do not reserve identity;
- eligibility positive and negative cases;
- event/tool/terminal/rejection counts;
- closed zero-count maps;
- accepted/rejected order preservation;
- empty input artifacts and exit `10`;
- all-rejected corpus artifacts and exit `10`.

### Safety and refusal

- input symlink/directory/device refusal;
- missing/oversized input;
- too many lines;
- missing output parent;
- existing output target;
- output failure and atomic cleanup;
- no network;
- no raw values/paths/IDs/tool names in logs or rejection records;
- fatal failure produces no target directory;
- help behavior;
- unexpected exception fails safely.

### Packaging

- pinned clean install;
- source and installed CLI parity;
- format, lint, and strict mypy;
- complete local verification command;
- package contains required modules and no fixtures/customer data.

## 13. Exact commands

Commands are frozen after scaffold resolution:

```text
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv lock --check --project triana-labs
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv sync --locked --all-groups --project triana-labs
./scripts/verify-governance.sh --working-tree
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --project triana-labs --locked ruff format --check src tests
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --project triana-labs --locked ruff check src tests
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --project triana-labs --locked mypy src
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --project triana-labs --locked pytest tests/acceptance -q
```

Commands run from repository root except tool paths `src` and `tests` are
resolved by the verification script or executed with working directory
`triana-labs`; the scaffold author must make the final single-command gate
unambiguous.

Initial valid RED means:

- package imports;
- `triana --help` succeeds;
- `triana traces observe ...` returns deterministic `NOT_IMPLEMENTED`;
- acceptance cases fail because expected artifacts/behavior are absent;
- no failure is caused by syntax, dependency, import, or fixture-oracle error.

## 14. Scaffold acceptance

Before the test author starts:

- exact Python pin matches repository direction: CPython 3.13.14;
- project name is `triana-labs`;
- import package is `triana_labs`;
- console command is `triana`;
- runtime dependency is only Pydantic;
- dev dependencies are pytest, Hypothesis, Ruff, and mypy;
- `--help` is functional;
- observe returns safe deterministic `NOT_IMPLEMENTED`;
- governance passes;
- scaffold diff matches its budget.

### 14.1 Independently frozen acceptance

The corrected independent black-box acceptance contract is frozen at commit
`85ee978`.
The implementation author may read but must not edit:

```text
triana-labs/tests/acceptance/**
triana-labs/tests/fixtures/**
```

The test-owned universe is 11 files and 106 collected cases. The independent
test author and orchestrator each reproduced the valid RED state:

```text
100 failed, 6 passed, 0 errors
```

All failures are missing public behavior from the deliberate
`NOT_IMPLEMENTED` scaffold. There are no syntax, dependency, import,
collection, configuration, fixture, Hypothesis health-check, setup, or oracle
failures.

The SHA-256 of sorted project-relative `shasum -a 256` lines for all acceptance
and fixture files is:

```text
78bd653ffaa2282de7fb094d18e93b4590eaa2e59737d84330160444f985e353
```

The fixture-only aggregate under the same procedure is:

```text
87d8610f7b92bb46c4322a4d03cb51e1c96a800ace80a96f4f0d75f93ad787c5
```

The orchestrator rejected two defects before the initial freeze—one Ruff
import-order failure and one Hypothesis fixture health check—and returned both
exclusively to the independent test author. After initial freeze `7237ed8`, the
implementation author found that a temporary scaffold sentinel permanently
required `NOT_IMPLEMENTED` for the same valid behavior that final acceptance
required to succeed. Production stopped with no edits. The independent test
author removed only that obsolete sentinel, preserved both help checks and all
product assertions, and reproduced corrected RED twice. Commit `85ee978`
supersedes `7237ed8` as the acceptance freeze. Any later acceptance or fixture
edit invalidates this freeze and requires a test-author correction, new
hashes, reproduced RED or GREEN evidence as appropriate, and a new explicit
freeze before its result can judge production.

## 15. Slice exit gate

LABS-01 is complete only when:

- planning decision and packet are committed before behavior work;
- scaffold, test, and implementation role ownership is preserved;
- frozen acceptance paths are unchanged by implementation;
- all acceptance and adversarial cases pass;
- same input creates byte-identical portable artifacts twice in fresh
  processes;
- every input line reconciles exactly;
- no raw rejected content or unsafe value enters rejection artifacts/logs;
- output is atomic and never overwrites;
- source and installed CLI outputs match;
- one command runs governance, formatting, lint, typing, tests, repeatability,
  package, and artifact inspection;
- generated five-line fixture artifacts are retained under an
  orchestrator-owned evidence directory or reproducibly generated by a
  checked-in command;
- code-reading order and exact artifact paths are included in the handoff;
- actual changed files and dependencies reconcile with the budget;
- no unsupported product claim is added;
- decision memory is complete.

### 15.1 Observed exit evidence

Implementation commit: `92f65a1`

Corrected independent acceptance freeze: `85ee978`

Frozen acceptance/fixture aggregate:

```text
78bd653ffaa2282de7fb094d18e93b4590eaa2e59737d84330160444f985e353
```

The versioned command `triana-labs/scripts/verify.sh` observed:

```text
governance: passed
Ruff format and lint: passed
strict mypy: passed
independent acceptance: 106 passed
orchestrator adversarial: 6 passed
total: 112 passed
fresh-process artifact repeatability: byte-identical
sdist and wheel: built
clean CPython 3.13.14 wheel install: passed
source/installed help parity: passed
source/installed canonical artifact parity: byte-identical
```

Final retained evidence root:

```text
/private/tmp/triana-labs-verify.oLgULS
```

Canonical artifact paths:

```text
/private/tmp/triana-labs-verify.oLgULS/first/output/manifest.json
/private/tmp/triana-labs-verify.oLgULS/first/output/normalized_traces.jsonl
/private/tmp/triana-labs-verify.oLgULS/first/output/rejected_traces.jsonl
/private/tmp/triana-labs-verify.oLgULS/first/output/corpus_profile.json
/private/tmp/triana-labs-verify.oLgULS/first/output/corpus_profile.md
```

Observed canonical result:

```text
5 input lines
3 accepted traces
2 rejected traces
2 case-generation eligible traces
COMPLETED_WITH_REJECTIONS
```

Recommended code-reading order:

1. `triana-labs/src/triana_labs/contracts/traces.py`
2. `triana-labs/src/triana_labs/observer/observe.py`
3. `triana-labs/src/triana_labs/observer/render.py`
4. `triana-labs/src/triana_labs/cli.py`
5. `triana-labs/tests/acceptance/test_observe_success.py`
6. `triana-labs/tests/acceptance/test_observe_rejections.py`
7. `triana-labs/tests/acceptance/test_observe_safety.py`
8. `triana-labs/tests/adversarial/test_observer_boundaries.py`

Known bounded uncertainty: portable Python does not provide a universal atomic
directory rename with no-replace semantics against a hostile process creating
an empty target in the final check-to-rename interval. The implementation
checks immediately before rename, never merges, preserves an existing
non-empty target, and safely fails concurrent ordinary publication. No broader
filesystem-locking or platform-specific syscall was added to this slice.

## 18. LABS-01A code-reading documentation follow-up

Date: 2026-07-31

Base: `154ac99`

Outcome: a human or coding agent can open `contracts/traces.py` and understand
where an external adapter stops, where Triana begins, why validation is split
into stages, which layer owns each invariant, and how accepted values flow to
the five Observer artifacts without reconstructing the architecture from
tests.

The adapter interaction is documentation-only in this follow-up:

```text
external adapter owned by the customer/integration
  -> emits one PreviewTrace JSON object per JSONL physical line
  -> `triana traces observe` owns file/CLI behavior
  -> `observer.observe` owns corpus accounting and publication
  -> `contracts.parse_and_validate_line` owns byte/JSON boundary validation
  -> `contracts.validate_trace` owns schema and trace invariants
  -> normalized/rejected/profile/manifest artifacts
  -> future Corpus Intelligence consumes eligible normalized traces
```

No external adapter package, SDK, import API, OTel mapping, real-trace support,
redaction, Corpus Intelligence, case generation, or behavior change is
authorized.

Implementation-author comment budget:

```text
triana-labs/src/triana_labs/contracts/traces.py
triana-labs/src/triana_labs/observer/observe.py
triana-labs/src/triana_labs/observer/render.py
triana-labs/src/triana_labs/cli.py
```

The author may enrich module docstrings, class/function docstrings, and
comments explaining boundaries, authority, ordering, refusal, privacy,
determinism, and non-obvious tradeoffs. It may not change executable AST after
docstring nodes are removed, tests, fixtures, public behavior, dependencies,
or any other path.

Independent reviewer: the existing test-author agent reviews prose against
the frozen LABS-01 contract and implementation after the author finishes. The
reviewer does not edit production.

Pre-change executable AST SHA-256 values are calculated after removing the
leading string-expression docstring node from every module, class, sync
function, and async function, then applying `ast.dump(...,
include_attributes=False)`. Comments are naturally absent from the AST. This
distinguishes documentation changes from executable changes while still
allowing the docstrings this follow-up exists to improve:

```text
contracts/traces.py  a5091694e08be6644e604d614cb00310c9054e048f5b7f677bea64a6271e6f8a
observer/observe.py  c0d525f5c085c8e3f44047e14a82e1009ac2d06dd9271a2e0525b53654ca6e6f
observer/render.py   34b80d1e9deb76d78347579e820b8ebefc31af689b2343b86315003c8df7e814
cli.py               da569a029882f155a6ac8d6c4e5d7cf2c94805e37856f4b02956a06ca4cd6f79
```

Exit requires:

- exact post-change docstring-stripped executable AST hash equality for all
  four files;
- no test, fixture, package, dependency, or artifact change;
- independent prose review with no misleading adapter or authority claim;
- Ruff, strict mypy, 112 tests, repeatability, build, and clean-wheel checks;
- generated canonical artifact bytes identical to the retained LABS-01
  evidence;
- a small reading guide in the final handoff.

### 18.1 Observed LABS-01A exit evidence

Comment implementation: `42043ab`

Changed production files: exactly the four authorized paths, with 207 inserted
documentation lines and 16 replaced one-line docstring lines.

Independent review: accepted after the author removed duplicated module-level
boundary prose, changed value-class docstrings from function-like wording, and
tightened failure and file-boundary statements.

Post-change docstring-stripped AST hashes equal all four frozen pre-change
values exactly. The final versioned verification gate observed:

```text
governance: passed
Ruff format and lint: passed
strict mypy: passed
tests: 112 passed
fresh-process repeatability: passed
sdist and wheel: built
clean CPython 3.13.14 wheel install: passed
installed command parity: passed
```

Final evidence root:

```text
/private/tmp/triana-labs-verify.PPhSN7
```

The newly generated five artifact files are byte-identical to retained
pre-comment evidence under `/private/tmp/triana-labs-verify.oLgULS`.

## 19. LABS-01B Observer responsibility refactor

Date: 2026-07-31

Base: `dcfc02d`

Owner-approved outcome: make the module tree express the responsibilities a
reader expects, without changing the CLI, contracts, artifacts, rejection
precedence, privacy, packaging, or runtime behavior.

Target dependency flow:

```text
cli.py
  -> observer/observe.py       file input, line accounting, orchestration
       -> contracts/traces.py  one-line parsing and trace validation
       -> observer/profile.py  aggregate accepted/rejected corpus facts
       -> observer/publication.py
            -> observer/renderer.py  canonical JSON and Markdown projection
            -> hashing and atomic five-file publication
```

Exact production ownership after the refactor:

- `contracts/traces.py`: unchanged one-trace contract and validation.
- `observer/observe.py`: `observe`, output/input boundary checks, physical-line
  splitting, cross-line identity, and outcome selection. It must not define
  corpus profiling, JSON/Markdown rendering, hashing, or atomic writing.
- `observer/profile.py`: `build_profile` and aggregate count-map construction.
- `observer/renderer.py`: `compact_json` and `render_markdown`; no counting,
  hashing, filesystem, or CLI behavior.
- `observer/publication.py`: `publish_bundle` and private atomic-write helpers;
  owns exact artifact bytes, manifest hashing, and publication.
- `observer/render.py`: removed. It is an internal module with no promised
  compatibility surface; preserving both names would make ownership ambiguous.

Public behavior remains only:

```text
triana traces observe <input.jsonl> --out <new-directory>
```

No external adapter SDK, direct Python adapter API, Corpus Intelligence,
profile semantics, new artifact, schema change, dependency, or performance
claim is authorized.

Change budget:

Independent test author:

```text
triana-labs/tests/architecture/**
```

Implementation author after test freeze:

```text
triana-labs/src/triana_labs/observer/observe.py
triana-labs/src/triana_labs/observer/profile.py
triana-labs/src/triana_labs/observer/renderer.py
triana-labs/src/triana_labs/observer/publication.py
triana-labs/src/triana_labs/observer/render.py  # deletion only
```

Explicitly forbidden: acceptance/adversarial tests, fixtures,
`contracts/traces.py`, CLI, package/lock files, dependencies, other products,
and all later components.

Independent RED must prove the target modules and ownership do not yet exist,
while all existing 112 behavioral tests remain green. Architecture assertions
must inspect imports/definitions rather than impose arbitrary source-line
limits.

Canonical pre-refactor artifact SHA-256 values:

```text
corpus_profile.json      6d6c8d38dae3b7fb4d5580153e7fe1f77f8b9104b6bb28e0f5234c9d30d52146
corpus_profile.md        4ede1203e02462d870865abcefdf277c1e24b2bfa16cc5785b42eaf7cc1419c6
manifest.json            7a14709fd10373beaa2da842c869988f1d976ddeae34b46501f6d8930fa7e808
normalized_traces.jsonl b294d8b0bc9dd5fe8e449015b1d9ef4e72cb815260d88cda394db1bc9fde0447
rejected_traces.jsonl   c36c32c1adce137a6c6765823fbf271005df64d04547ad9fe17f7ad6c264e98f
```

Exit requires:

- independently frozen architecture tests GREEN;
- all 112 existing tests GREEN and unchanged;
- the five canonical hashes above unchanged in source and clean-wheel runs;
- `render.py` absent and `profile.py`, `renderer.py`, `publication.py` present
  in both source and wheel;
- Ruff, strict mypy, governance, repeatability, sdist/wheel, and clean-install
  gates GREEN;
- exact change-budget reconciliation and updated reading order.

### 19.1 Independently frozen architecture RED

Architecture test commit: `a08a149`

Test file SHA-256:

```text
a16c7ceea4d3f8a2cdb594019efbbeb1e9c05d758c552a1dd282168167b943b2
```

The test author and orchestrator independently observed:

```text
architecture target: 6 failed, 0 errors
existing behavioral suite: 112 passed, 0 failures
```

All six RED failures are caused by the frozen current layout: the three target
modules are absent, ownership remains embedded in `observe.py`/`render.py`, and
the old module still ships. Implementation may read but must not edit
`tests/architecture/**`, existing tests, or fixtures.

## 16. Structured uncertainty handoff

Every worker and orchestrator returns:

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

Use `none` explicitly. Unrun checks are unverified, never passing.

## 17. Explicit non-goals

- real/local-sensitive customer traces;
- redaction or provider egress;
- language or distress inference;
- clustering, personas, intents, or turn policies;
- case generation or panel selection;
- baseline/candidate execution;
- F0/F1, provider/model use, or diversity;
- outcomes, comparison, findings, or report HTML;
- HRAI/Agentagon/Kairos source reuse;
- `triana-core` edits or public-license resolution;
- stdin/streaming, directories, OTel, HTTP, or generic adapters;
- authentication, hosted storage, upload, UI, billing, or telemetry.
