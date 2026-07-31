# Active implementation slice — LABS-01 Trace Observer

Status: **ENTRY GATE FROZEN; NO WORKER BEHAVIOR EDITS BEFORE PLAN COMMIT**

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
- Arbitrary JSON floats, NaN, and Infinity are rejected.

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
