# Active implementation slice — LABS-02 external adapter proof

Status: **INDEPENDENT TESTS FROZEN — IMPLEMENTATION AUTHOR AUTHORIZED AFTER FREEZE COMMIT**

Date: 2026-07-31
Canonical base: `2e6d35d`
Product authority: `triana-labs/CHARTER.md`
Execution authority: `internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`
Engineering authority: `docs/ENGINEERING.md`
Provenance authority: `docs/PROVENANCE.md`
Orchestrator: primary Codex agent
Worker roles: exactly one independent test author followed serially by one
implementation author

## 1. Outcome and falsifiable claim

Slice ID: `LABS-02-hrai-v2-reference-adapter`

Component advanced: the external file boundary immediately before **Trace
Observer**. Corpus Intelligence is not started.

The checkpoint proves or falsifies this claim:

> A coding agent can copy a small, dependency-free reference transform for one
> concrete foreign trace shape, run it locally on explicitly synthetic data,
> produce exact LABS-01 `PreviewTrace` JSONL with complete source-line
> accounting, and pass that file to the unchanged Trace Observer.

This is the already-planned HRAI reference adapter, not a supported HRAI
integration, adapter SDK, generic import framework, or new `triana` command.
Customer/provider mappings remain outside Triana's deterministic product core.

Acceptance path:

```text
synthetic HRAI normalized-trace-v2 JSONL
  -> standalone examples/hrai_v2/adapter.py
  -> adapter bundle/preview_traces.jsonl
  -> existing `triana traces observe`
  -> unchanged five Observer artifacts and hashes for the canonical fixture
```

## 2. Invocation and install/run experience

From a repository checkout with the existing locked environment:

```text
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache \
  uv run --project triana-labs --locked python \
  triana-labs/examples/hrai_v2/adapter.py \
  <synthetic-hrai-v2.jsonl> \
  --out <new-adapter-output-directory> \
  --data-class SYNTHETIC

UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache \
  uv run --project triana-labs --locked triana traces observe \
  <new-adapter-output-directory>/preview_traces.jsonl \
  --out <new-observer-output-directory>
```

The adapter script uses only the Python standard library and imports no
`triana_labs` implementation module. It is deliberately copyable into a
customer repository. It must remain at or below 200 nonblank, non-comment
physical Python lines, with a target of 100; the measured count is reported at
exit. Rich module/function comments are excluded from the count.

No console entry point, package API, registry, dynamic plugin loading, stdin,
pipe protocol, or automatic adapter discovery is added.

## 3. Exact source format

One physical input line is one HRAI historical-traffic record whose required
mapping surface is:

```json
{
  "schema_version": "normalized-trace-v2",
  "case_id": "case-001",
  "session_id": "pf-case-001-demo0001",
  "status": "COMPLETED",
  "system_prompt": {"text": "You are the synthetic reference agent."},
  "turns": [
    {"role": "user", "content": "Find the synthetic candidate."},
    {"role": "assistant", "content": "I found the synthetic candidate."}
  ],
  "events": [
    {"turn": 1, "role": "user", "tool_calls": []},
    {"turn": 1, "role": "assistant", "tool_calls": []}
  ]
}
```

Required fields are exactly `schema_version`, `case_id`, `session_id`,
`status`, `system_prompt`, `turns`, and `events`. The exporter fields
`client_id`, `simulator_model`, `user_turn_budget`, `started_at`, `error`,
`tokens`, `usd`, `tool_sequence`, `decision_observable`, `sub_agents`, and
`finished_at` are recognized and ignored because they do not map to the frozen
LABS-01 vocabulary. Any other top-level field rejects the source line. Ignored
fields never enter output, logs, identities, or hashes.

Recognized ignored fields are parsed only to enforce raw JSON resource and
strict-syntax boundaries. They may contain any finite strict-JSON value,
including finite floats used by HRAI for fields such as `usd`; non-finite
`NaN`/`Infinity` tokens remain malformed JSON. A finite float is forbidden in
every mapped field, including message content structure, tool `arguments`, and
`result_summary`, because LABS-01 PreviewTrace cannot represent it.

Source constraints:

- `schema_version` is exactly `normalized-trace-v2`.
- `case_id` and `session_id` are LABS-01 `SafeId`; `session_id` becomes both
  `trace_id` and `source_trace_id`.
- A `session_id` already used by an earlier accepted source line rejects the
  later line as `DUPLICATE_TRACE_ID`. Because both output identities derive
  from the same source field, LABS-02 has no separately representable
  duplicate-source-ID condition. Rejected lines do not reserve `session_id`.
- `status` must be `COMPLETED`. `HARNESS_ERROR` or any other value is rejected,
  not translated into agent terminal behavior.
- `system_prompt` is a closed object with one non-empty string field `text`.
- `turns` is a non-empty ordered array of closed objects with `role`, `content`,
  and optional recognized-but-ignored `tools_called` and `metadata`.
- Roles alternate exactly `user`, `assistant`, beginning with `user`; the final
  turn is `assistant`.
- User content is non-empty; assistant content may be empty. LABS-01 content
  byte/control limits apply.
- `events` has the same length and role order as `turns`. Each event is a
  closed object with `turn`, `role`, `tool_calls`, and optional
  recognized-but-ignored `tokens`, `ts`, and `error`.
- User events have no tool calls. Assistant events contain zero or more closed
  tool-call objects with `name`, `arguments`, `result_summary`, `status`,
  `error`, `latency_ms`, and `cached`.
- Assistant tool-call `name` is a LABS-01 `SafeId`; `arguments` and a present
  `result_summary` obey LABS-01 opaque-JSON limits and forbid floats.
- Tool status is exactly `ok` or `error`. `error` status may contain any
  source-local error value, but output uses only safe code
  `HRAI_TOOL_ERROR`; raw error content is never emitted.
- `latency_ms` and `cached` are validated only as non-negative safe integer or
  null, and boolean, respectively; they have no LABS-01 output field.

Raw file boundaries equal LABS-01: local regular non-symlink file, 16 MiB,
1,000 physical lines, 1 MiB per line, LF/CRLF, optional final LF, strict UTF-8,
no BOM, duplicate JSON keys rejected, maximum JSON depth 32, strict JSON with
non-finite numeric tokens rejected by the parser. Finite floats are accepted
only within the recognized ignored source fields described above.

## 4. Exact mapping to PreviewTrace

For every accepted source line, output one compact, sorted-key JSON object with
exactly:

```json
{
  "contract_kind": "preview_trace",
  "events": [],
  "privacy_class": "SYNTHETIC",
  "schema_version": 1,
  "source_trace_id": "<source session_id>",
  "trace_id": "<source session_id>"
}
```

The ordered `events` array is constructed as follows:

1. Event 0 is `SYSTEM_VISIBLE_MESSAGE` containing `system_prompt.text`.
2. Each user turn emits one `USER_MESSAGE` with its source content.
3. For each assistant turn, its aligned enriched source tool calls are emitted
   before the assistant message, in source order.
4. Each source tool call emits `TOOL_CALL` with deterministic
   `call_id: "hrai-t<turn>-c<one-based-call-index>"`, source `name` as
   `tool_name`, and source `arguments`.
5. `status: "ok"` plus a non-null `result_summary` emits a following
   `TOOL_RESULT` with `result_state: "SUCCEEDED"` and `result` equal to the
   source summary. A null summary emits no result, leaving the observation gap
   visible as an unmatched call.
6. `status: "error"` emits a following `TOOL_RESULT` with
   `result_state: "ERROR"` and `error_code: "HRAI_TOOL_ERROR"`; raw source
   error content is discarded.
7. The assistant turn then emits `ASSISTANT_MESSAGE`. `is_final` is true only
   for the last assistant turn.
8. `sequence` is assigned contiguously from zero after expansion.
9. No `TERMINAL` event is invented: HRAI `COMPLETED` describes harness
   completion, not agent-origin success.

The resulting object must independently pass the existing LABS-01
`PreviewTrace` validator. The adapter must not import that production validator
to construct output or its test oracle.

## 5. Adapter output bundle

`--out` names a new directory containing exactly:

```text
adapter_manifest.json
preview_traces.jsonl
rejected_source_traces.jsonl
```

`preview_traces.jsonl` contains accepted mappings in source-line order. It is
zero bytes when no source line maps.

`rejected_source_traces.jsonl` contains one safe record per rejected physical
line:

```json
{"code":"SOURCE_TURN_EVENT_MISMATCH","json_pointer":"/events","line_number":2,"safe_message":"Source turns and events do not align."}
```

It contains no path, raw value, excerpt, exception, trace/session/case ID,
prompt, message, tool name, arguments, result, or error content.

Closed per-line codes:

```text
BLANK_LINE
INVALID_UTF8
BOM_FORBIDDEN
LINE_TOO_LARGE
MALFORMED_JSON
DUPLICATE_JSON_KEY
NESTING_TOO_DEEP
SOURCE_SCHEMA_VALIDATION_FAILED
UNSUPPORTED_SOURCE_SCHEMA_VERSION
SOURCE_EXECUTION_INCOMPLETE
SOURCE_TURN_EVENT_MISMATCH
DUPLICATE_TRACE_ID
MAPPED_TRACE_INVALID
```

`adapter_manifest.json` is:

```json
{
  "accepted_count": 1,
  "adapter_kind": "hrai_normalized_trace_v2_reference",
  "artifacts": {
    "preview_traces.jsonl": "sha256:<exact bytes>",
    "rejected_source_traces.jsonl": "sha256:<exact bytes>"
  },
  "input_count": 1,
  "privacy_class": "SYNTHETIC",
  "rejected_count": 0,
  "schema_version": 1,
  "source_schema_version": "normalized-trace-v2"
}
```

All files are UTF-8/LF/no-BOM, compact sorted-key JSON, one terminal LF except
an empty JSONL file, with byte-identical output across fresh processes. The
manifest hashes exact artifact bytes and has no self-hash.

## 6. Exit, refusal, publication, and logs

- Exit 0: at least one input line and every line maps.
- Exit 10: bundle exists but input is empty or at least one line is rejected.
- Stdout: one compact receipt with only counts, outcome, and presentation
  manifest path.
- Stderr: exactly one compact safe terminal event with counts and outcome; no
  paths or source values.
- `--help`: exit 0, help on stdout, no terminal event.
- `--data-class SYNTHETIC` is mandatory. Missing or any other value is fatal
  `UNSUPPORTED_DATA_CLASS`, exit 2, before reading input.
- Input/path/resource failures are fatal exits 2 or 3; publication failure is
  7; internal invariant is 70. Fatal failure creates no target directory.
- An already-existing output target is an output-path precondition refusal and
  exits 2 before publication begins. Exit 7 is reserved for a failure while
  creating, flushing, or atomically publishing a previously absent target.
- Output is a private temporary sibling atomically renamed to a target that
  must not exist. It never overwrites or merges.
- Every physical source line is counted exactly once:
  `input_count = accepted_count + rejected_count`.

The synthetic flag is an explicit caller attestation, not automatic data
classification. Documentation must state that real, production-derived,
customer, Blitz, or otherwise local-sensitive exports are unsupported and
must not be used in LABS-02.

## 7. Authority, privacy, and provenance

Deterministic code owns raw accounting, source-shape validation, mapping,
ordering, IDs, rejection classification, output bytes/hashes, and exit state.
No LLM, provider, network, human semantic ruling, redaction, or egress occurs.
The human owns the truthful synthetic-data attestation.

The source format was inspected at HRAI repository commit
`728f6c5058efe40a16e2aecc9b528b3353f4df4f`, specifically:

```text
experiments/historical_traffic_v0/runner/run_preflight.py
experiments/historical_traffic_v0/runner/hr_bridge.py
```

The implementation is a clean reimplementation of the mapping specified in
this packet. No HRAI code, raw trace, generated corpus, prompt, or fixture is
copied. All committed fixtures are newly authored synthetic examples. The
provenance ledger records the exact inspection and destination before worker
implementation.

## 8. Change budget and serial ownership

Orchestrator entry/exit only:

```text
internal/SLICE_PACKET.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
docs/PROVENANCE.md
README.md
triana-labs/scripts/verify.sh
triana-labs/tests/adapter_adversarial/**
```

Independent test author only:

```text
triana-labs/tests/adapter_acceptance/**
triana-labs/tests/adapter_fixtures/**
```

Implementation author only after test freeze:

```text
triana-labs/examples/hrai_v2/adapter.py
triana-labs/examples/hrai_v2/README.md
```

No dependency, package metadata, lockfile, core source, existing test, or
existing fixture change is allowed. Maximum scope expansion without
orchestrator return: none.

Explicitly untouched:

```text
triana-labs/src/triana_labs/**
triana-labs/pyproject.toml
triana-labs/uv.lock
triana-labs/tests/acceptance/**
triana-labs/tests/adversarial/**
triana-labs/tests/architecture/**
triana-labs/tests/fixtures/**
triana-core/**
docs/PRODUCT.md
docs/ARCHITECTURE.md
docs/CONTRACTS.md
all raw/external corpora and external repositories
```

## 9. Independent acceptance and RED

The test author independently creates source fixtures and expected
`PreviewTrace` bytes without importing production adapter code. Minimum matrix:

- minimal and tool-rich successful mappings with exact bytes;
- system/user/tool/result/assistant ordering and contiguous sequences;
- deterministic call IDs and final-assistant marking;
- missing tool summary retained as an unmatched call;
- source harness error refused rather than mapped to terminal behavior;
- role/turn/event mismatch;
- malformed/duplicate-key/invalid UTF-8/BOM/blank/depth/size cases, including
  accepted finite floats in ignored fields and rejected floats in mapped fields;
- duplicate accepted `session_id` as `DUPLICATE_TRACE_ID`, with rejected lines
  not reserving the identity;
- mixed partial success and exact accounting;
- empty/all-rejected deterministic bundles;
- mandatory synthetic attestation and no raw values in rejection/log output;
- atomic no-overwrite/fatal no-output behavior;
- repeatability and independent artifact hashes;
- adapter output accepted by unchanged `triana traces observe`;
- standalone standard-library/import-boundary and 200-line ceiling;
- all prior 118 tests and five canonical hashes unchanged.

Valid RED on canonical base means existing 118 tests pass and new adapter tests
fail only because the two implementation-owned example files do not exist.
No import, fixture-oracle, syntax, environment, or existing-behavior failure is
valid RED.

The orchestrator freezes the test commit and aggregate hashes before the
implementation author starts. Test defects return only to the same test author;
implementation defects only to the implementation author.

### 9.1 Independently frozen acceptance

The corrected independent acceptance contract is frozen at commit `16f7b6b`,
which supersedes provisional test commit `1a59239` after the orchestrator
returned one exit-code defect and two missing source-boundary cases exclusively
to the test author.

Frozen test-owned paths:

```text
triana-labs/tests/adapter_acceptance/**
triana-labs/tests/adapter_fixtures/**
```

The four test-owned files contain 27 collected black-box cases. The independent
test author and orchestrator each reproduced valid RED:

```text
27 errors, all at the session-scoped precondition identifying only absent
examples/hrai_v2/adapter.py and examples/hrai_v2/README.md
```

The aggregate SHA-256 over sorted repository-relative `shasum -a 256` lines is:

```text
ebd2274d8d09b51ec56e8d825bf16f69a9caebd4a799a287a9a3060fc02279a0
```

The orchestrator separately reproduced the unchanged prior suite as 118 passing
tests, the prior acceptance/fixture aggregate
`78bd653ffaa2282de7fb094d18e93b4590eaa2e59737d84330160444f985e353`,
and the architecture-test hash
`a16c7ceea4d3f8a2cdb594019efbbeb1e9c05d758c552a1dd282168167b943b2`.

Frozen acceptance files may not change during implementation. A suspected test
defect returns only to the same independent test author and requires a new
correction commit, valid RED evidence, hash, and orchestrator freeze.

Reserved orchestrator adversarial checks, not disclosed as literal fixtures to
the implementation author, cover:

- a successful run under a socket-blocking `sitecustomize` to detect network
  access;
- a rejected deeply nested private marker absent from stdout, stderr, and safe
  artifacts;
- symlink/directory and exact whole-file resource refusal with no bundle;
- copying only `adapter.py` to a temporary directory and running it outside the
  repository to prove the standard-library/copyable boundary;
- regeneration of the five canonical Observer hashes and source/clean-wheel
  acceptance of the adapter's canonical PreviewTrace output.

## 10. Verification and immutable prior evidence

Prior acceptance/fixture aggregate remains:

```text
78bd653ffaa2282de7fb094d18e93b4590eaa2e59737d84330160444f985e353
```

Prior architecture test hash remains:

```text
a16c7ceea4d3f8a2cdb594019efbbeb1e9c05d758c552a1dd282168167b943b2
```

The canonical Observer artifact hashes must remain:

```text
corpus_profile.json      6d6c8d38dae3b7fb4d5580153e7fe1f77f8b9104b6bb28e0f5234c9d30d52146
corpus_profile.md        4ede1203e02462d870865abcefdf277c1e24b2bfa16cc5785b42eaf7cc1419c6
manifest.json            7a14709fd10373beaa2da842c869988f1d976ddeae34b46501f6d8930fa7e808
normalized_traces.jsonl b294d8b0bc9dd5fe8e449015b1d9ef4e72cb815260d88cda394db1bc9fde0447
rejected_traces.jsonl   c36c32c1adce137a6c6765823fbf271005df64d04547ad9fe17f7ad6c264e98f
```

Frozen commands before worker start (the `uv run` commands execute with
`triana-labs/` as their working directory):

```text
./scripts/verify-governance.sh --working-tree
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --locked ruff format --check src tests examples
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --locked ruff check src tests examples
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --locked mypy src examples
UV_CACHE_DIR=/private/tmp/triana-labs-uv-cache uv run --locked pytest tests -q
triana-labs/scripts/verify.sh
```

The versioned verification script is extended only by the orchestrator after
GREEN to execute the canonical adapter fixture, feed its PreviewTrace file into
source and clean-wheel Observer commands, compare exact outputs, enforce prior
hashes, and inspect package contents. The example need not ship in the wheel;
the test must make that packaging fact explicit.

## 11. Abort conditions and debugging

Workers stop before changing a frozen contract, existing behavior, package
surface, dependency, or unowned file. Any ambiguity about HRAI source meaning,
especially harness completion versus agent outcome, returns to the
orchestrator. No permissive fallback, unknown-field dropping, role repair,
content guessing, or retry-to-green is permitted.

Every debugging iteration records the repository's one-hypothesis template.
Falsified changes are removed before the next hypothesis.

## 12. Exit gate and structured handoff

LABS-02 exits only when:

- test-author RED is independently reproduced and frozen before implementation;
- implementation touches only its two owned example files;
- new tests pass without changing test-owned paths;
- all previous 118 tests and exact test hashes remain unchanged;
- all five canonical Observer hashes remain unchanged;
- adapter output is independently byte-checked and accepted by the unchanged
  source and installed-wheel Observer;
- mixed input accounting, safe rejections, synthetic refusal, atomic output,
  repeatability, no-network behavior, and line ceiling are verified;
- source provenance and clean reimplementation are recorded;
- actual diff and dependencies reconcile exactly with this budget;
- Corpus Intelligence, real data, SDK, OTel, hosted ingestion, and UI remain
  unimplemented.

Every worker and the orchestrator reports:

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

## 13. Explicit non-goals

- real/local-sensitive trace support, redaction, authorization, or egress;
- an HRAI product integration or stable `triana` adapter command;
- generic adapters, SDKs, plugins, OTel, Langfuse, HTTP, or hosted ingestion;
- stdin/streaming or direct in-process Observer invocation;
- source format repair, inference, enrichment, or semantic interpretation;
- Corpus Intelligence, cases, panels, execution, comparison, reports, or UI;
- any change to LABS-01, `triana-core`, frozen V1 contracts, dependencies, or
  canonical artifact bytes.
