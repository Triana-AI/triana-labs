# Triana Slice 0A wire contracts

Status: **owner-approved normative V1 contract**

This document is the field-level authority for Slice `0A-contract-kernel`.
`docs/PRODUCT.md` owns product meaning, `docs/ARCHITECTURE.md` owns authority
boundaries, and this document owns the exact JSON wire representation.

No Pydantic model, generated JSON Schema, fixture, CLI behavior, or UI type may
disagree with this document. A semantic change requires an append-only decision
and a schema-version decision before tests or implementation change.

## Active Labs self-serve service boundary

The Slice 0A document registry below remains unchanged. Active Labs adds a
service contract, not another Slice 0A public document kind: an authenticated
PreviewTrace upload response always includes
`analysis: {feature_state, run}`. `run` is null while `ANALYSIS` is `LOCKED` or
`REQUESTED`; only `AVAILABLE` may start a run. A completed run binds one
`agent_id`, `import_id`, `run_id`, and `report_id` and is retrievable only by
the owning workspace.

The same owner scope applies to agent analysis history, report, review state,
append-only ruling, and report-bound conversation evidence. A ruling requires
the current review `item_hash`; stale or foreign identities fail without
mutating the ledger. A report may contain zero populations, eval proposals,
outcomes, or review items, but it must expose the corresponding typed gap or
unavailable state and may not infer a pass or reward. Exact endpoint and model
representations live in `triana-backend/src/triana_backend/api/` and the frozen
black-box acceptance contract is
`triana-backend/tests/acceptance/test_trace_to_eval_self_serve.py`.

### Triana onboarding skill boundary

The distributable onboarding package has one canonical skill body and one
deterministic CLI surface. Codex metadata and the Claude Code plugin/marketplace
are wrappers over that same skill; they MUST NOT duplicate or specialize the
adapter contract. Every operation that reads a trace source requires explicit
`--confirm-authorized-traces` first.

`inspect` accepts only a local regular file and emits physical-line counts,
root JSON types, known structural field/type shapes, and an exact redacted-key
count. It MUST NOT emit paths, source values, or unknown/dynamic object keys.
`validate` implements the current closed PreviewTrace v1 and Observer corpus
boundary, preserves valid bytes exactly, rejects invalid or mixed-privacy
corpora with typed reasons, and never overwrites an output. `scaffold` creates
only a bounded `IMPLEMENTATION_REQUIRED` adapter seam and content-free
contract; it is not an inferred mapping or acceptance. `preview` validates
first and emits at most three redacted event-shape examples.

Structural validity is distinct from publication custody. Safe external
identities and explicitly recognized structured identities remain unchanged.
Before residual scanning, an unfamiliar `trace_id` or `source_trace_id` whose
positive detections are exclusively `PHONE`, `POSTAL_CODE`, or `LONG_NUMBER`
MUST be replaced through the stable redactor token registry. The projection
MUST preserve equality and distinctness, remain byte-identical for repeated
identical input, validate as PreviewTrace v1, and expose only aggregate
category counts without raw values, tokens, or mappings. Any other residual
identifier category MUST continue to refuse. Preview MUST translate that
remaining refusal to the content-free public reason
`PREVIEW_TRACE_REDACTION_RESIDUAL_IDENTIFIER`.

Provider-enabled Preview MUST require every named
`TRIANA_BEHAVIOR_MAP_*` provider field. Its `endpoint_origin` and
`audit_endpoint_origin` compatibility fields MUST contain the exact configured
base URLs after trimming only trailing `/`; the OpenAI-v1 path is authorization
evidence and MUST NOT be reduced to scheme and authority. Missing, partial, or
application-specific Azure/OpenAI variables do not authorize egress. Provider
absence remains the typed deterministic mode, and neither mode permits retry or
fallback.

A fresh provider-enabled Behavior Map run MUST complete bounded synthetic
model-contract preflights for extraction, population consolidation, and pattern
consolidation before sending corpus evidence. A successful preflight consumes
one ordinary provider attempt but contributes no episode, population,
occurrence, pattern, evidence, or audit subject. A failed preflight MUST stop
fresh corpus semantic work and emit a stage-specific typed gap. A fully
checkpointed provider-disabled replay MUST NOT call a provider merely to add
preflight artifacts.

Failed call custody MUST store only: failure code and phase, safe HTTP
category/status when present, finish reason, a closed structural schema
location, truncation state, response SHA-256, retriability, and whether provider
egress began. Exception text, response bodies, prompts, credentials, headers,
and provider-chosen field names MUST NOT persist. The only extra-field schema
location is the constant `SCHEMA_ROOT/EXTRA_FIELD`; unsupported paths become
absent. A local budget refusal has `provider_attempted=false` and contributes
zero attempted calls and zero reservation. A legacy failed artifact without
this evidence MUST produce `SEMANTIC_ATTEMPT_ACCOUNTING_UNKNOWN` and mark the
reported attempt count `LOWER_BOUND`; it MUST NOT invent an exact historical
count.

`pattern_analysis.status` distinguishes `PATTERNS_OBSERVED`,
`NO_RECURRING_PATTERN_OBSERVED`, `PATTERN_ANALYSIS_FAILED`, and
`PATTERN_ANALYSIS_UNAVAILABLE`. The substantive no-recurring-pattern state is
valid only after eligible pattern analysis completed without a blocking
semantic-stage failure.

`docker-command` accepts only a separately published release manifest whose
image is pinned as `<registry>/<image>@sha256:<64 lowercase hex>`. It returns an
argv array and MUST NOT execute Docker. The trace file mount is read-only, the
output is a local directory, credentials never enter argv or artifacts, and an
unpublished or mutable image reference is a refusal. The public onboarding
package contains no Behavior Map engine, provider adapter, image credential,
retry, fallback, upload, telemetry, or deployment authority.

### Behavior Map historical projection

`behavior_map_historical_projection_v0` is a private internal artifact, not a
new public Slice 0A document kind. It MUST bind the immediate semantic
predecessor, accepted baseline predecessor, corrected extraction hash, source
hash, DEVELOPMENT selection hash, privacy class, and provider-disabled state.
Every corrected episode has exactly one disposition. Only populations with a
current `SUPPORTED` audit own active assignment/support; changed populations
remain visible candidates with `MISSING` audit and unpublished visibility, and
their members are intentionally unassigned with `REAUDIT_REQUIRED`. Rejected or
grounding-replacement memberships and occurrences remain typed excluded
history and contribute zero active support. Edge conservation MUST classify
every predecessor edge with zero unexplained loss, or publication refuses.
Historical provider attempts and lane-cap violations remain historical facts;
projection attempts are separately zero and actual cost remains unknown unless
an authoritative cost record exists.

### Behavior Map pattern conservation

`behavior_map_report_v0` MUST expose the exact eligible behavior-occurrence
IDs, one `pattern_occurrence_dispositions` row per eligible ID, and
`pattern_accounting`. A disposition is active assignment, intentional
unassignment with a typed reason, or audit dispute; no eligible ID may disappear
or receive multiple terminal rows. Semantic membership IDs absent from the
exact first-level or hierarchy input MUST be rejected, typed, counted, and
contribute zero support. Ordinary unassigned behavior is reported independently
of vague or generic-label rejection.

`behavior_patterns` is a custody collection, not an active-only list. A
`SUPPORTED` pattern may contribute active membership/support. A pattern with
audit `MISSING` remains `UNPUBLISHED_AUDIT_MISSING`; a non-supported audit
ruling remains `UNPUBLISHED_AUDIT_DISPUTED`. Both retain deterministic identity,
label, definition, occurrence membership, and evidence lineage while
contributing zero active support. `pattern_accounting` separately reports
eligible occurrences, terminal dispositions, candidate patterns, audited
patterns, supported patterns, disputed patterns, audit-missing patterns, active
memberships, unpublished memberships, and published support. `UNCERTAIN` is an
explicit audited-disputed state, not missing evidence.

Active population publication MUST reject duplicate membership, declared
support unequal to unique membership, duplicate disposition rows, an
`ASSIGNED` row whose population edge differs from active membership, or any
inequality between active member IDs and assigned disposition IDs. A
predecessor `AUDIT_DISPUTED` disposition persists through historical projection
unless a current explicit supported ruling authorizes reassignment; population
membership alone is insufficient authority.

## Normative language

`MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`, and `MAY` are
normative.

- `R` means required.
- `O` means optional and absent when unused. It never means implicit `null`.
- `S` means set-like: input order is accepted, canonical order is defined
  below, and duplicate stable keys are rejected.
- `Q` means ordered sequence: input order is identity-bearing.
- Every object is closed. Unknown fields are rejected.
- Every stored field is identity-bearing through its containing document
  unless this document explicitly says otherwise.

## Public document registry

Exactly five document kinds are independently valid:

| `contract_kind` | Self-identity field |
|---|---|
| `normalized_trace` | `trace_hash` |
| `protected_case` | `case_version` |
| `release_evidence_record` | `current_record_hash` when sealed |
| `record_chain` | `chain_hash` |
| `decision_attestation` | `attestation_hash` |

The first four are the core evidence families. `decision_attestation` is a
separate public document because it is created after the evidence record and
has an independent lifecycle.

Every public document requires:

```json
{
  "contract_kind": "<registered literal>",
  "schema_version": 1
}
```

`schema_version` is a strict JSON integer. `1.0`, `"1"`, `true`, coercion, a
missing field, and any integer other than `1` are invalid.

Nested objects do not repeat these universal fields unless explicitly stated.
No nested type is independently accepted by `triana contracts validate`.

## Scalar domains

| Name | Exact domain |
|---|---|
| `SchemaVersion` | Strict JSON integer exactly `1` |
| `SafeId` | ASCII 1–128 bytes matching `^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$` |
| `ExternalId` | UTF-8 1–512 bytes; no C0 or C1 controls |
| `SafeCode` | ASCII 1–64 bytes matching `^[A-Z][A-Z0-9_]{0,63}$` |
| `SafeLabel` | UTF-8 1–256 bytes; no C0 or C1 controls |
| `StatementText` | UTF-8 1–4096 bytes; LF allowed; other C0/C1 controls forbidden |
| `LocalContent` | UTF-8 0–1,048,576 bytes; local-sensitive; LF allowed; other C0/C1 controls forbidden |
| `Digest` | ASCII matching `^sha256:[0-9a-f]{64}$` |
| `Timestamp` | Valid UTC calendar time in exact `YYYY-MM-DDTHH:MM:SS.mmmZ` form; leap seconds forbidden |
| `SafeInt` | Strict JSON integer `0..9007199254740991`; negative zero forbidden |
| `PositiveInt` | Strict JSON integer `1..9007199254740991` |
| `Index` | `SafeInt` used for zero-based positions |
| `DurationMs` | `SafeInt` milliseconds |
| `CanonicalDecimal` | Canonical decimal string described below, at most 128 ASCII bytes |
| `FixedRate` | Exactly six fractional digits, range `0.000000..1.000000` |
| `FixedMovement` | Exactly six fractional digits and optional minus sign, range `-1.000000..1.000000`; negative zero forbidden |
| `JsonPointer` | RFC 6901 JSON Pointer, 0–1024 UTF-8 bytes |

Object keys are UTF-8 strings of 1–256 bytes. Invalid UTF-8 and lone Unicode
surrogates are rejected. Accepted Unicode is preserved exactly; it is not
normalized.

`CanonicalDecimal` is exactly one of:

```text
0
[1-9][0-9]*
0\.[0-9]*[1-9]
[1-9][0-9]*\.[0-9]*[1-9]
```

with an optional `-` only when the value is non-zero. Exponents, leading
integer zeros, trailing fractional zeros, a trailing decimal point, `-0`, NaN,
and infinity are forbidden.

`FixedRate` and `FixedMovement` use exactly six fractional digits. Values
derived from integer counts use decimal round-half-even. Counts remain the
authoritative exact facts. Examples:

```text
0 / 3 -> "0.000000"
1 / 3 -> "0.333333"
1 / 2 -> "0.500000"
2 / 3 -> "0.666667"
3 / 3 -> "1.000000"
```

## Local-sensitive JSON values

`SensitiveJson` exists only inside `normalized_trace`. It recursively permits:

- JSON `null`;
- booleans;
- safe integers;
- `CanonicalDecimal` strings;
- ordinary strings subject to the string limit;
- arrays;
- objects.

Arbitrary JSON floats are forbidden. Object keys and the global depth, byte,
and string limits still apply. Unknown-field rejection does not apply inside a
`SensitiveJson` value because it is explicitly an opaque customer payload.

## Canonicalization and identity

### Domain-set normalization

Before RFC 8785/JCS serialization, only fields marked `S` are sorted. The
sort-key registry is closed:

| Set | Stable sort key |
|---|---|
| behavior or applicability statements | `statement_id` |
| observation capabilities | capability literal |
| evidence references | `reference_id` |
| evidence requirements | `requirement_id` |
| assertion definitions | `assertion_id` |
| evaluator results | `(evaluator_id, check_id, result_id)` |
| evidence gaps | `gap_id` |
| runtime components | `component_kind` |
| release-change components | `component_kind` |
| safe reason codes | code literal |
| regex flags | flag literal |
| gap IDs | ID literal |

Equal sort keys are duplicates even when other content differs. They fail
validation; canonicalization never silently deduplicates or tie-breaks them.

Fields marked `Q` preserve input order.

### JCS bytes

After domain-set normalization, serialize with RFC 8785/JCS:

- UTF-8;
- no BOM;
- no insignificant whitespace;
- no terminal newline in canonical bytes;
- no Unicode normalization;
- object keys sorted exactly as JCS requires.

Human-facing CLI output adds one LF after canonical bytes. That LF is not part
of any hash.

### Hash preimage

Every Triana-derived SHA-256 identity uses:

```text
b"triana\x00" +
identity_kind_utf8 +
b"\x00v" +
schema_version_ascii +
b"\x00" +
canonical_json_bytes
```

The result is lowercase `sha256:<64 hex>`.

The closed `identity_kind` registry is:

```text
normalized_trace
protected_case
runtime_fingerprint
execution_contract
trial_identity
json_value
release_evidence_record
record_chain
decision_attestation
```

Nested identities use the schema version of their containing public document.
Every Slice 0A nested hash therefore uses ASCII `1`. A nested object cannot be
copied into a document with another schema version unless a future,
explicitly versioned migration defines the conversion. `json_value` hashes in
V1 also use ASCII `1`.

For a self-identity, canonical bytes contain the entire object after set
normalization with only that object's self-identity field absent. Nested
self-identity fields remain present when hashing a containing object.

Derivations:

- `trace_hash`: `normalized_trace` without `trace_hash`.
- `case_version`: `protected_case` without `case_version`.
- `runtime_hash`: `runtime_fingerprint` without `runtime_hash`.
- `execution_contract_hash`: `execution_contract` without
  `execution_contract_hash`.
- `trial_id`: the canonical object containing exactly `run_id`,
  `case_version`, `side`, `trial_index`, `code_ref`, and
  `execution_contract_hash`.
- A customer may calculate `expected_hash` for an exact JSON assertion matcher
  from the canonical `SensitiveJson` value under `json_value`. Because the
  value is not stored, Slice 0A treats this as a supplied fingerprint and
  validates only its digest format. Changing it still changes the containing
  Protected Case identity.
- `current_record_hash`: the sealed release record without
  `current_record_hash`.
- `chain_hash`: `record_chain` without `chain_hash`.
- `attestation_hash`: `decision_attestation` without `attestation_hash`.

External fingerprints and policy hashes are supplied `Digest` values. Triana
validates their format but does not claim to reproduce external content.

## Shared nested objects

### `EvidenceReference`

| Field | Type | Presence |
|---|---|---|
| `reference_id` | `SafeId` | R |
| `reference_kind` | enum below | R |
| `content_hash` | `Digest` | R |
| `locator` | `EvidenceLocator` | O |

`reference_kind` is one of:

```text
TRACE
TOOL_EVENT
ASSERTION
EVALUATOR
FIXTURE
POLICY
APPROVAL
GITHUB
OTHER
```

`EvidenceLocator` is discriminated by `locator_kind`:

| Variant | Fields |
|---|---|
| `OPAQUE` | `locator_kind: "OPAQUE"`, `token: SafeId` |
| `HTTPS` | `locator_kind: "HTTPS"`, `url: ExternalId` |

An HTTPS locator must be an absolute `https` URL with a non-empty host and no
userinfo, query, or fragment. It may contain a port and path. A locator is
identity-protected but never loggable. It contains no evidence excerpt or
payload.

### `ObservationScope`

| Field | Type | Presence |
|---|---|---|
| `capabilities` | `S` of 1–9 capability literals | R |

Capability literals:

```text
CONVERSATION_TURNS
MODEL_OUTPUT
TOOL_DISPATCH
TOOL_ARGUMENTS
TOOL_RESULTS
TERMINAL_STATE
ESCALATION_HANDOFF
TIMING
COST
```

### `Approval`

| Field | Type | Presence |
|---|---|---|
| `actor_id` | `SafeId` | R |
| `actor_display_name` | `SafeLabel` | O |
| `approved_at` | `Timestamp` | R |
| `source_reference` | `EvidenceReference` | R |

### `BehaviorStatement`

| Field | Type | Presence |
|---|---|---|
| `statement_id` | `SafeId` | R |
| `text` | `StatementText` | R |

### `RuntimeComponent`

| Field | Type | Presence |
|---|---|---|
| `component_kind` | enum below | R |
| `fingerprint` | `Digest` | R |

Component kinds:

```text
AGENT_CODE
MODEL
PROMPT
TOOLING
RUNTIME
CONFIGURATION
FIXTURE
EVALUATOR
```

### `RuntimeFingerprint`

| Field | Type | Presence |
|---|---|---|
| `components` | `S[RuntimeComponent]`, 1–8 | R |
| `runtime_hash` | derived `Digest` | R |

### Execution and trial randomization

`ExecutionRandomizationPolicy` is discriminated by
`randomization_policy_kind`:

| Variant | Fields |
|---|---|
| `NONE` | `randomization_policy_kind: "NONE"` |
| `SEEDED` | `randomization_policy_kind: "SEEDED"`, `generator: SafeLabel`, `generator_version: SafeLabel` |

`TrialRandomization` is discriminated by `randomization_kind`:

| Variant | Fields |
|---|---|
| `NONE` | `randomization_kind: "NONE"` |
| `SEEDED` | `randomization_kind: "SEEDED"`, `seed: SafeId`, `generator: SafeLabel`, `generator_version: SafeLabel` |

### `ExecutionContract`

| Field | Type | Presence |
|---|---|---|
| `contract_version` | `PositiveInt` | R |
| `command_hash` | `Digest` | R |
| `fixture_fingerprint` | `Digest` | R |
| `configuration_fingerprint` | `Digest` | R |
| `reset_policy_hash` | `Digest` | R |
| `observation_scope` | `ObservationScope` | R |
| `randomization_policy` | `ExecutionRandomizationPolicy` | R |
| `declared_trial_count` | `PositiveInt`, maximum 1000 | R |
| `execution_contract_hash` | derived `Digest` | R |

### `ExecutionContractBinding`

Discriminator: `execution_binding_kind`.

| Variant | Fields |
|---|---|
| `MATCHED` | `execution_binding_kind: "MATCHED"`, `execution_contract: ExecutionContract` |
| `CANDIDATE_ONLY` | `execution_binding_kind: "CANDIDATE_ONLY"`, `candidate_execution_contract: ExecutionContract` |
| `MISMATCHED` | `execution_binding_kind: "MISMATCHED"`, `baseline_execution_contract: ExecutionContract`, `candidate_execution_contract: ExecutionContract` |

The two contract hashes in `MISMATCHED` must differ.

### `BaselineBinding`

Discriminator: `baseline_kind`.

| Variant | Fields |
|---|---|
| `APPROVED` | `baseline_kind: "APPROVED"`, `code_ref: SafeId`, `approval_reference: EvidenceReference` |
| `MISSING` | `baseline_kind: "MISSING"`, `reason_code: "MISSING_APPROVED_BASELINE"` |

### `ReleaseChangeComponent`

| Field | Type | Presence |
|---|---|---|
| `component_kind` | `RuntimeComponent.component_kind` | R |
| `candidate_fingerprint` | `Digest` | R |
| `baseline_fingerprint` | `Digest` | conditional |
| `declared_state` | `CHANGED \| UNCHANGED \| UNKNOWN` | R |
| `difference_reference_id` | `SafeId` | conditional |

If the baseline is `APPROVED`, `baseline_fingerprint` is required. If it is
`MISSING`, `baseline_fingerprint` is forbidden.

`difference_reference_id` is required exactly for `UNKNOWN` and forbidden for
other states. It must name an item in the containing Release Change's
`unresolved_difference_references`.

### `ReleaseChange`

| Field | Type | Presence |
|---|---|---|
| `change_id` | `SafeId` | R |
| `declaration_reference` | `EvidenceReference` | R |
| `candidate_code_ref` | `SafeId` | R |
| `baseline` | `BaselineBinding` | R |
| `components` | `S[ReleaseChangeComponent]`, 1–8 | R |
| `unresolved_difference_references` | `S[EvidenceReference]`, 0–100 | R |

Every `difference_reference_id` must resolve exactly once. Extra unresolved
difference references are allowed because they may describe cross-component
or unobservable differences.

## `normalized_trace`

### Top-level fields

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | `"normalized_trace"` | R |
| `schema_version` | `1` | R |
| `privacy_class` | `"LOCAL_SENSITIVE"` | R |
| `trace_id` | `SafeId` | R |
| `source` | `TraceSource` | R |
| `conversation_id` | `SafeId` | R |
| `thread_id` | `SafeId` | O |
| `agent_ref` | `SafeId` | O |
| `release_ref` | `SafeId` | O |
| `observation_scope` | `ObservationScope` | R |
| `events` | `Q[TraceEvent]`, 1–10,000 | R |
| `trace_hash` | derived `Digest` | R |

### `TraceSource`

| Field | Type | Presence |
|---|---|---|
| `source_kind` | `LANGFUSE \| JSONL \| OTEL \| OTHER` | R |
| `source_trace_id` | `ExternalId` | R |
| `source_export_hash` | `Digest` | R |

### Trace-event union

Discriminator: `event_kind`.

Every event requires:

| Field | Type | Presence |
|---|---|---|
| `event_id` | `SafeId` | R |
| `sequence` | `Index` | R |
| `event_kind` | variant literal | R |
| `parent_event_id` | `SafeId` | O |
| `occurred_at` | `Timestamp` | O |

Variant fields:

| Variant | Additional fields |
|---|---|
| `USER_MESSAGE` | `content: LocalContent` |
| `ASSISTANT_MESSAGE` | `content: LocalContent`, `is_final: boolean` |
| `SYSTEM_VISIBLE_MESSAGE` | `content: LocalContent` |
| `MODEL_OBSERVATION` | `model_ref: SafeId`, `output: LocalContent`, `latency_ms: DurationMs` O, `cost_amount: CanonicalDecimal` conditional, `cost_currency: three uppercase ASCII letters` conditional |
| `TOOL_CALL` | `tool_name: SafeId`, `arguments: SensitiveJson` |
| `TOOL_RESULT` | `tool_call_event_id: SafeId`, `result_state: SUCCEEDED \| ERROR`, `result: SensitiveJson` conditional, `error_code: SafeCode` conditional, `error_message: LocalContent` conditional |
| `HANDOFF` | `handoff_kind: HUMAN \| AGENT \| QUEUE`, `destination_ref: SafeId`, `outcome: REQUESTED \| ACCEPTED \| REJECTED` |
| `TERMINAL` | `terminal_state: SUCCESS \| ERROR \| ABORTED`, `reason_code: SafeCode` conditional |

`cost_amount` and `cost_currency` are either both present or both absent.
`cost_amount` is non-negative.

For `TOOL_RESULT`, `SUCCEEDED` requires `result` and forbids error fields;
`ERROR` requires both error fields and forbids `result`.

Trace invariants:

- `sequence` is exactly `0..len(events)-1`.
- Event IDs are unique.
- A parent names an earlier event.
- A tool result names an earlier `TOOL_CALL`.
- At most one `TERMINAL` exists; when present, it is last.
- At most one assistant message has `is_final: true`; it precedes a terminal
  event when one exists.
- `TERMINAL.SUCCESS` forbids `reason_code`; other terminal states require it.
- `CONVERSATION_TURNS` covers message variants.
- `MODEL_OUTPUT` covers model observations.
- Tool calls require both `TOOL_DISPATCH` and `TOOL_ARGUMENTS`.
- Tool results require `TOOL_RESULTS`.
- Handoffs require `ESCALATION_HANDOFF`.
- Terminal events require `TERMINAL_STATE`.
- Present latency requires `TIMING`; present cost requires `COST`.

## `protected_case`

### Top-level fields

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | `"protected_case"` | R |
| `schema_version` | `1` | R |
| `case_id` | `SafeId` | R |
| `risk_name` | `SafeLabel` | R |
| `source_evidence` | `S[EvidenceReference]`, 1–100 | R |
| `replay_input` | `ReplayInput` | R |
| `fixture_contract` | `FixtureContract` | R |
| `release_obligation` | `ReleaseObligation` | R |
| `evidence_requirements` | `S[EvidenceRequirement]`, 1–100 | R |
| `approval` | `Approval` | R |
| `qualification` | `Qualification` | R |
| `case_version` | derived `Digest` | R |

### Replay types

`ReplayInput`:

| Field | Type | Presence |
|---|---|---|
| `messages` | `Q[ReplayMessage]`, 1–100 | R |

`ReplayMessage`:

| Field | Type | Presence |
|---|---|---|
| `message_id` | `SafeId` | R |
| `role` | `USER \| ASSISTANT \| SYSTEM_VISIBLE` | R |
| `content` | `LocalContent` | R |

Message IDs are unique.

### `FixtureContract`

| Field | Type | Presence |
|---|---|---|
| `fixture_id` | `SafeId` | R |
| `fixture_version` | `PositiveInt` | R |
| `fixture_fingerprint` | `Digest` | R |
| `reset_policy_hash` | `Digest` | R |

### `ReleaseObligation`

| Field | Type | Presence |
|---|---|---|
| `obligation_id` | `SafeId` | R |
| `obligation_statement` | `BehaviorStatement` | R |
| `source_reference` | `EvidenceReference` | R |
| `severity` | `LOW \| MEDIUM \| HIGH \| CRITICAL` | R |
| `owner_actor_id` | `SafeId` | R |
| `applicability_conditions` | `S[BehaviorStatement]`, 1–100 | R |
| `expected_behavior` | `S[BehaviorStatement]`, 1–100 | R |
| `prohibited_behavior` | `S[BehaviorStatement]`, 0–100 | R |
| `allowed_alternatives` | `S[BehaviorStatement]`, 0–100 | R |
| `handoff_requirement` | `HandoffRequirement` | R |
| `policy_context_reference` | `EvidenceReference` | O |

Statement IDs are unique across the obligation statement, applicability,
expected, prohibited, and allowed collections.

`HandoffRequirement` discriminator: `handoff_kind`.

| Variant | Fields |
|---|---|
| `NONE` | `handoff_kind: "NONE"` |
| `REQUIRED` | `handoff_kind: "REQUIRED"`, `destination_ref: SafeId` O |

### `EvidenceRequirement`

Common fields:

| Field | Type | Presence |
|---|---|---|
| `requirement_id` | `SafeId` | R |
| `requirement_kind` | discriminator | R |
| `required_observation` | `ObservationScope` | R |
| `minimum_trials` | `PositiveInt`, maximum 1000 | R |

Variants:

| Variant | Additional fields |
|---|---|
| `TRIANA_ASSERTION` | `assertion: AssertionDefinition` |
| `CUSTOMER_EVALUATOR` | `evaluator_id: SafeId`, `evaluator_version: Digest`, `check_id: SafeId` |

Requirement IDs are unique. Assertion IDs are unique across all assertion
requirements.

### `Qualification`

Discriminator: `qualification_state`.

| Variant | Fields |
|---|---|
| `READY` | `qualification_state: "READY"` |
| `NEEDS_FIXTURE` | `qualification_state: "NEEDS_FIXTURE"`, `reason_code: "FIXTURE_REQUIRED"`, `explanation_reference: EvidenceReference` |
| `NOT_YET` | `qualification_state: "NOT_YET"`, `reason_code: SafeCode` other than `FIXTURE_REQUIRED`, `explanation_reference: EvidenceReference` |

### Assertion definition union

Common fields:

| Field | Type | Presence |
|---|---|---|
| `assertion_id` | `SafeId` | R |
| `assertion_version` | `PositiveInt` | R |
| `assertion_kind` | discriminator | R |

All regex-bearing assertions use:

| Field | Type |
|---|---|
| `regex_engine` | literal `"PYTHON_RE_3_13"` |
| `pattern` | UTF-8 1–4096 bytes; no forbidden controls |
| `flags` | `S` of `ASCII \| IGNORE_CASE \| MULTILINE`, 0–3 |

Patterns must compile under Python 3.13 `re`. No other engine or flag is
accepted.

Assertion variants:

1. `tool_called`

   ```text
   assertion_kind: "tool_called"
   tool_name: SafeId
   ```

2. `tool_not_called`

   ```text
   assertion_kind: "tool_not_called"
   tool_name: SafeId
   ```

3. `tool_called_before`

   ```text
   assertion_kind: "tool_called_before"
   before_tool_name: SafeId
   after_tool_name: SafeId
   occurrence_rule: "FIRST_SUCCESSFUL_DISPATCH"
   ```

   Tool names differ. Later execution compares the first successful dispatch
   of each and requires both to exist.

4. `arg_matches`

   ```text
   assertion_kind: "arg_matches"
   tool_name: SafeId
   argument_pointer: JsonPointer
   call_selection: FIRST | LAST | EVERY
   matcher: ValueMatcher
   ```

   `ValueMatcher` discriminator: `matcher_kind`.

   | Variant | Fields |
   |---|---|
   | `EXACT_JSON` | `matcher_kind: "EXACT_JSON"`, `expected_hash: Digest`, `expected_value_reference: EvidenceReference` O |
   | `STRING_REGEX` | `matcher_kind: "STRING_REGEX"` plus the exact regex fields above |

5. `no_loop`

   ```text
   assertion_kind: "no_loop"
   signature: TOOL_NAME | TOOL_NAME_AND_ARGUMENT_HASH
   maximum_consecutive_calls: PositiveInt, maximum 1000
   ```

6. `no_unbacked_claim`

   ```text
   assertion_kind: "no_unbacked_claim"
   regex_engine: "PYTHON_RE_3_13"
   output_pattern: UTF-8 1–4096 bytes
   pattern_flags: S[ASCII | IGNORE_CASE | MULTILINE]
   claim_group_name: "claim"
   supporting_tool_name: SafeId
   support_result_pointer: JsonPointer
   normalization: EXACT_STRING | ASCII_CASEFOLD_TRIM
   support_must_precede_claim: true
   ```

   The regex must compile and contain exactly one named group called `claim`.
   Every non-overlapping claim captured from the final assistant output must
   match a scalar string extracted at the configured pointer from an earlier
   successful result of the configured tool. No claim matches means PASS.
   Missing final output, tool-result visibility, pointer, or scalar support
   makes the result UNEVALUABLE, never PASS. A tool call alone is not support.

7. `output_matches`

   ```text
   assertion_kind: "output_matches"
   target: "FINAL_ASSISTANT_MESSAGE"
   matcher: OutputMatcher
   ```

   `OutputMatcher` discriminator: `matcher_kind`.

   | Variant | Fields |
   |---|---|
   | `STRING_REGEX` | `matcher_kind: "STRING_REGEX"` plus the exact regex fields above |
   | `JSON_SCHEMA` | `matcher_kind: "JSON_SCHEMA"`, `schema_draft: "2020-12"`, `schema_hash: Digest`, `schema_reference: EvidenceReference` |

   Remote schema retrieval is forbidden.

8. `terminal_state`

   ```text
   assertion_kind: "terminal_state"
   expected_state: "NO_ERROR"
   ```

## Received evidence

### `AssertionResult`

| Field | Type | Presence |
|---|---|---|
| `result_id` | `SafeId` | R |
| `requirement_id` | `SafeId` | R |
| `assertion_id` | `SafeId` | R |
| `assertion_version` | `PositiveInt` | R |
| `execution_index` | `Index` | R |
| `status` | `PASS \| FAIL \| UNEVALUABLE` | R |
| `reason_code` | `SafeCode` | R |
| `evidence_references` | `S[EvidenceReference]`, 0–100 | R |
| `gap_ids` | `S[SafeId]`, 0–100 | R |

`PASS` forbids gaps. `UNEVALUABLE` requires at least one gap. `FAIL` may carry
gaps only when the behavioral failure remains directly evidenced.

### `CustomerEvaluatorResult`

| Field | Type | Presence |
|---|---|---|
| `result_id` | `SafeId` | R |
| `requirement_id` | `SafeId` | R |
| `check_id` | `SafeId` | R |
| `evaluator_id` | `SafeId` | R |
| `evaluator_version` | `Digest` | R |
| `status` | `PASS \| FAIL \| UNEVALUABLE` | R |
| `score` | `CanonicalDecimal` | O |
| `evidence_references` | `S[EvidenceReference]`, 0–100 | R |
| `gap_ids` | `S[SafeId]`, 0–100 | R |

The same status/gap rules apply.

### `EvidenceGap`

| Field | Type | Presence |
|---|---|---|
| `gap_id` | `SafeId` | R |
| `gap_code` | enum below | R |
| `stage` | `QUALIFICATION \| EXECUTION \| ASSERTION \| EVALUATOR \| COMPARISON` | R |
| `scope` | `GapScope` | R |
| `reason_reference` | `EvidenceReference` | R |
| `evidence_references` | `S[EvidenceReference]`, 0–100 | R |

Gap codes:

```text
MISSING_APPROVED_BASELINE
EXECUTION_CONTRACT_MISMATCH
MISSING_OBSERVATION
NEGATIVE_ASSERTION_UNEVALUABLE
EVALUATOR_TIMEOUT
EVALUATOR_ERROR
EVALUATOR_REFUSAL
EVALUATOR_SCHEMA_INVALID
INSUFFICIENT_TRIALS
FIXTURE_REQUIRED
```

`GapScope` discriminator: `scope_kind`.

| Variant | Fields |
|---|---|
| `RECORD` | `scope_kind: "RECORD"` |
| `TRIAL` | `scope_kind: "TRIAL"`, `trial_id: Digest` |
| `ASSERTION` | `scope_kind: "ASSERTION"`, `trial_id: Digest`, `assertion_id: SafeId` |
| `EVALUATOR` | `scope_kind: "EVALUATOR"`, `trial_id: Digest`, `evaluator_id: SafeId`, `check_id: SafeId` |

### `TrialResult`

| Field | Type | Presence |
|---|---|---|
| `trial_id` | derived `Digest` | R |
| `run_id` | `SafeId` | R |
| `case_version` | `Digest` | R |
| `side` | `BASELINE \| CANDIDATE` | R |
| `trial_index` | `Index` | R |
| `code_ref` | `SafeId` | R |
| `execution_contract_hash` | `Digest` | R |
| `runtime_fingerprint` | `RuntimeFingerprint` | R |
| `randomization` | `TrialRandomization` | R |
| `execution_status` | `COMPLETED \| ERROR \| TIMEOUT \| REFUSED` | R |
| `trace_reference` | `EvidenceReference` | O |
| `assertion_results` | `Q[AssertionResult]`, 0–1000 | R |
| `customer_evaluator_results` | `S[CustomerEvaluatorResult]`, 0–1000 | R |
| `gaps` | `S[EvidenceGap]`, 0–1000 | R |
| `end_to_end_status` | `PASS \| FAIL \| UNEVALUABLE` | R |

Trial invariants:

- `trial_id` matches its normative derivation.
- A completed trial requires a trace reference.
- A non-completed trial cannot report end-to-end PASS.
- Assertion `execution_index` values are contiguous from zero.
- Result IDs are unique within a trial.
- Every result requirement/assertion/evaluator identity resolves to the
  containing record's evidence requirements.
- Every result gap ID resolves to exactly one trial gap.
- PASS results forbid gaps; UNEVALUABLE results require a gap.
- A `NONE` execution randomization policy requires every trial to use `NONE`.
- A `SEEDED` execution policy requires seeded trials whose generator and
  generator version exactly match the policy.
- Under a `MATCHED` execution binding, baseline and candidate trials with the
  same `trial_index` use identical trial randomization.
- Under `CANDIDATE_ONLY`, no pairing invariant applies.
- Under `MISMATCHED`, paired trial indices use identical randomization only
  when both side policies are structurally identical. When policies differ,
  each trial obeys its side and the difference remains explicit
  non-comparable evidence.
- Different trial indices may declare different seeds.

## Static comparison and policy snapshots

Slice 0A validates these supplied snapshots but does not generate policy or
comparison meaning.

### `SideSummary`

| Field | Type | Presence |
|---|---|---|
| `trial_count` | `SafeInt` | R |
| `evaluable_count` | `SafeInt` | R |
| `pass_count` | `SafeInt` | R |
| `pass_rate` | `FixedRate` | R |

The unit is a trial's `end_to_end_status`:

- `trial_count` is the number of trials on that side.
- `evaluable_count` is the number whose status is PASS or FAIL.
- `pass_count` is the number whose status is PASS.

Invariants:

```text
pass_count <= evaluable_count <= trial_count
pass_rate = round_half_even(pass_count / evaluable_count, 6)
```

When the denominator is zero, `pass_rate` is `"0.000000"` and remains
non-evidence.

### `Comparison`

| Field | Type | Presence |
|---|---|---|
| `comparison_status` | `COMPARABLE \| FIRST_OBSERVATION \| MOVED \| INSUFFICIENT_EVIDENCE` | R |
| `candidate` | `SideSummary` | R |
| `baseline` | `SideSummary` | conditional |
| `movement` | `FixedMovement` | conditional |
| `reason_codes` | `S[SafeCode]`, 0–100 | R |

Variant invariants:

- `COMPARABLE`: baseline and movement required; missing-baseline and
  contract-mismatch reasons forbidden. Movement equals the six-digit
  round-half-even value of the exact candidate rate minus exact baseline rate
  derived from counts.
- `FIRST_OBSERVATION`: baseline and movement absent; reason contains
  `MISSING_APPROVED_BASELINE`.
- `MOVED`: baseline required, movement absent; reason contains
  `EXECUTION_CONTRACT_MISMATCH`.
- `INSUFFICIENT_EVIDENCE`: movement absent; baseline optional; at least one
  reason required.

### `PolicyEvaluation`

| Field | Type | Presence |
|---|---|---|
| `policy_id` | `SafeId` | R |
| `policy_version` | `PositiveInt` | R |
| `policy_hash` | `Digest` | R |
| `rule_id` | `SafeId` | R |
| `input_evidence_hash` | `Digest` | R |
| `reason_codes` | `S[SafeCode]`, 1–100 | R |
| `recommendation` | `PASS \| REVIEW \| BLOCK` | R |

`EvidenceStrength` is `SUFFICIENT | LIMITED | INSUFFICIENT`.

## `release_evidence_record`

One schema represents unsigned and sealed records through `seal_state`.

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | `"release_evidence_record"` | R |
| `schema_version` | `1` | R |
| `seal_state` | `UNSIGNED \| SEALED` | R |
| `project_id` | `SafeId` | R |
| `release_stream_id` | `SafeId` | R |
| `run_id` | `SafeId` | R |
| `created_at` | `Timestamp` | R |
| `release_change` | `ReleaseChange` | R |
| `protected_case_id` | `SafeId` | R |
| `protected_case_version` | `Digest` | R |
| `release_obligation` | `ReleaseObligation` snapshot | R |
| `evidence_requirements` | `S[EvidenceRequirement]` snapshot, 1–100 | R |
| `execution_contracts` | `ExecutionContractBinding` | R |
| `trials` | `Q[TrialResult]`, 1–1000 | R |
| `comparison` | `Comparison` | R |
| `evidence_strength` | `EvidenceStrength` | R |
| `record_gaps` | `S[EvidenceGap]`, 0–1000 | R |
| `policy_evaluation` | `PolicyEvaluation` | R |
| `recommendation` | `PASS \| REVIEW \| BLOCK` | R |
| `pr_reference` | `EvidenceReference` | O |
| `chain_link` | `RecordChainLink` | R |
| `current_record_hash` | derived `Digest` | conditional |

`RecordChainLink` discriminator: `link_kind`.

| Variant | Fields |
|---|---|
| `GENESIS` | `link_kind: "GENESIS"` |
| `APPEND` | `link_kind: "APPEND"`, `previous_record_hash: Digest`, `supersedes_record_hash: Digest` O |

Record invariants:

- `UNSIGNED` forbids `current_record_hash`.
- `SEALED` requires a correct `current_record_hash`.
- All trial run, case, side, and code references agree with the record.
- Under `MATCHED`, every trial uses the one matched execution contract.
- Under `CANDIDATE_ONLY`, baseline trials are forbidden and candidate trials
  use the candidate contract.
- Under `MISMATCHED`, each trial uses the contract for its side.
- Candidate trials use `release_change.candidate_code_ref`.
- Baseline trials are forbidden when the baseline binding is `MISSING`;
  otherwise they use its approved code ref.
- Trial indices are unique and contiguous within each side.
- Trial count on each side does not exceed the
  `declared_trial_count` of that side's bound execution contract.
- Comparison side counts match the actual supplied trial
  `end_to_end_status` values under the exact SideSummary definition.
- Evidence requirement and result references resolve.
- Record gap IDs are unique and record-scoped.
- Record recommendation equals policy-evaluation recommendation.
- `CANDIDATE_ONLY` if and only if the baseline is `MISSING` and comparison is
  `FIRST_OBSERVATION`.
- `MISMATCHED` if and only if the baseline is `APPROVED` and comparison is
  `MOVED`.
- `MATCHED` requires an approved baseline and permits only `COMPARABLE` or
  `INSUFFICIENT_EVIDENCE`.
- Additional insufficiency remains visible through gaps and reason codes; it
  does not replace the stronger structural status `FIRST_OBSERVATION` or
  `MOVED`.
- `GENESIS` has no previous or superseded hash.
- `APPEND` requires previous hash. A superseded hash differs from previous
  hash and current hash.
- Human-approved obligation, applicability, and behavior statements are
  permitted normalized semantic text; they are not raw user excerpts.
- Upload safety is structural: no raw trace event, replay message, opaque JSON
  payload, tool argument/result, credential field, environment-value field, or
  unrestricted locator type exists in the record schema.
- Secret-pattern detection is defense in depth and cannot establish upload
  safety. Acceptance tests prove forbidden field shapes, userinfo/query/
  fragment-bearing HTTPS locators, and trace-only types are rejected. Logs
  never emit locators or free-text statements.

Seal algorithm:

1. Strictly validate an unsigned record.
2. Change only `seal_state` to `SEALED`.
3. Normalize declared sets.
4. Canonicalize with `current_record_hash` absent.
5. Compute the `release_evidence_record` domain hash.
6. Add `current_record_hash`.
7. Emit canonical JSON plus one presentation LF.

An already sealed record is rejected by `records seal`; its hash is never
silently replaced.

## `record_chain`

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | `"record_chain"` | R |
| `schema_version` | `1` | R |
| `chain_id` | `SafeId` | R |
| `project_id` | `SafeId` | R |
| `release_stream_id` | `SafeId` | R |
| `entries` | `Q[RecordChainEntry]`, 1–1000 | R |
| `head_record_hash` | `Digest` | R |
| `chain_hash` | derived `Digest` | R |

`RecordChainEntry`:

| Field | Type | Presence |
|---|---|---|
| `position` | `Index` | R |
| `record_hash` | `Digest` | R |
| `link_kind` | `GENESIS \| APPEND` | R |
| `previous_record_hash` | `Digest` | conditional |
| `supersedes_record_hash` | `Digest` | O for APPEND only |

Slice 0A invariants:

- Positions are exactly `0..len(entries)-1`.
- Position zero is GENESIS and forbids previous/superseded hashes.
- Later positions are APPEND and require previous hash.
- Duplicate record hashes fail.
- Head equals the last record hash.
- Chain self-hash verifies.

Slice 0A does not load record files, prove links against record contents, or
detect external forks. Those behaviors remain Slice 0B.

## `decision_attestation`

| Field | Type | Presence |
|---|---|---|
| `contract_kind` | `"decision_attestation"` | R |
| `schema_version` | `1` | R |
| `attestation_id` | `SafeId` | R |
| `release_record_hash` | `Digest` | R |
| `decision_type` | `APPROVE \| HOLD \| APPROVE_WITH_EXCEPTION` | R |
| `actor_id` | `SafeId` | R |
| `actor_display_name` | `SafeLabel` | O |
| `decided_at` | `Timestamp` | R |
| `source_reference` | `EvidenceReference` | R |
| `exception_rationale_reference` | `EvidenceReference` | conditional |
| `attestation_hash` | derived `Digest` | R |

`APPROVE_WITH_EXCEPTION` requires an exception rationale reference. Other
decision types forbid it. Slice 0A verifies only the document self-hash and
field invariants; attestation chaining and external GitHub meaning are absent.

## Closed Slice 0A impossible-state registry

After successful structural schema validation, every condition below returns
`IMPOSSIBLE_STATE`; none becomes an evidence gap:

- Duplicate stable ID or set sort key.
- Non-contiguous trace sequence, assertion execution index, trial index within
  a side, or chain position.
- Forward or missing trace parent.
- Tool result not bound to an earlier tool call.
- Multiple or incorrectly positioned terminal/final-response events.
- Observation scope inconsistent with supplied trace events.
- Cross-list duplicate behavior statement ID.
- Evidence requirement and assertion/evaluator identity disagreement.
- Trial case, run, side, ref, or execution-contract mismatch with its record.
- Completed trial without trace reference.
- Non-completed trial reporting end-to-end PASS.
- PASS result carrying gap IDs.
- UNEVALUABLE result lacking a gap.
- Result gap ID absent from the trial gap set.
- Counts outside denominators, supplied counts disagreeing with record trials,
  or stored fixed rate/movement mismatch.
- Invalid comparison-state companion fields.
- Policy recommendation differing from record recommendation.
- Missing baseline represented by absence rather than its explicit union.
- A non-hash cross-field contradiction not assigned a more specific code.

Broken unions, forbidden variant companion fields, qualification companion
fields, unsigned/sealed hash presence, and GENESIS/APPEND field presence are
structural `SCHEMA_VALIDATION_FAILED` errors. A wrong `trial_id` follows the
exact digest mapping and returns `IDENTITY_MISMATCH`.

0A does not determine evidence sufficiency, infer comparison status, run
policy, or decide whether a supplied recommendation is substantively correct.
Those calculated semantics remain Slice 0B.

## Raw parser and resource rules

- Input size is raw bytes before decoding, maximum 16,777,216.
- BOM bytes count toward input size and then fail `BOM_FORBIDDEN`.
- UTF-8 is strict.
- Duplicate object keys fail before ordinary schema validation.
- Root object depth is 1. Entering an object or array increments depth;
  scalars do not. Maximum depth is 64.
- String size is measured after JSON escape decoding by re-encoding to UTF-8;
  maximum 1,048,576 bytes unless a smaller scalar limit applies.
- Each named collection receives its own documented limit.
- Resource checks precede schema checks where the raw boundary permits.
- At most 100 schema errors are returned. If more than 99 real errors exist,
  return 99 deterministically ordered real errors followed by
  `VALIDATION_ERROR_LIMIT_REACHED`.
- Exact large boundaries are generated during tests from a small committed
  manifest rather than stored as redundant multi-megabyte fixtures.

## Error contract

Precedence:

```text
input/resource/raw parse
→ contract kind and schema version
→ structural schema
→ digest-format validation
→ non-hash cross-field invariants and derived identities
→ stored seal-hash verification
```

Closed codes and exit statuses:

| Code | Exit |
|---|---:|
| `CLI_USAGE_ERROR` | 2 |
| `INPUT_READ_FAILED` | 2 |
| `INPUT_TOO_LARGE` | 3 |
| `NESTING_TOO_DEEP` | 3 |
| `STRING_TOO_LARGE` | 3 |
| `COLLECTION_TOO_LARGE` | 3 |
| `INVALID_UTF8` | 3 |
| `BOM_FORBIDDEN` | 3 |
| `MALFORMED_JSON` | 3 |
| `DUPLICATE_JSON_KEY` | 3 |
| `UNKNOWN_CONTRACT_KIND` | 4 |
| `UNSUPPORTED_SCHEMA_VERSION` | 4 |
| `SCHEMA_VALIDATION_FAILED` | 4 |
| `VALIDATION_ERROR_LIMIT_REACHED` | 4 |
| `IMPOSSIBLE_STATE` | 5 |
| `IDENTITY_MISMATCH` | 5 |
| `HASH_FORMAT_INVALID` | 6 |
| `HASH_MISMATCH` | 6 |
| `OUTPUT_WRITE_FAILED` | 7 |
| `LOG_REDACTION_FAILED` | 70 |
| `INTERNAL_INVARIANT_FAILED` | 70 |
| `NOT_IMPLEMENTED` | 70, RED scaffold only |

Exact digest-error mapping:

- Malformed syntax in any identity or hash field is `HASH_FORMAT_INVALID`.
- An incorrect `trace_hash`, `case_version`, `runtime_hash`,
  `execution_contract_hash`, or `trial_id` is `IDENTITY_MISMATCH`.
- An incorrect `current_record_hash`, `chain_hash`, or `attestation_hash` is
  `HASH_MISMATCH`.
- `IMPOSSIBLE_STATE` is reserved for non-hash cross-field contradictions.

Exact discriminator and operation-boundary mapping:

| Condition | Code | JSON Pointer |
|---|---|---|
| Missing or non-string `contract_kind` | `SCHEMA_VALIDATION_FAILED` | `/contract_kind` |
| Unknown string `contract_kind` | `UNKNOWN_CONTRACT_KIND` | `/contract_kind` |
| Missing or non-integer `schema_version` | `SCHEMA_VALIDATION_FAILED` | `/schema_version` |
| Integer schema version other than `1` | `UNSUPPORTED_SCHEMA_VERSION` | `/schema_version` |
| `records seal` or `records verify` receives another document kind | `SCHEMA_VALIDATION_FAILED` | `/contract_kind` |
| `records seal` receives a sealed record | `IMPOSSIBLE_STATE` | `/seal_state` |
| `records verify` receives an unsigned record | `IMPOSSIBLE_STATE` | `/seal_state` |

Within the discriminator stage, `contract_kind` is validated before
`schema_version`.

A public error contains:

| Field | Type | Presence |
|---|---|---|
| `code` | closed code | R |
| `safe_message` | safe non-normative text | R |
| `json_pointer` | `JsonPointer` | R when a field is known |
| `contract_kind` | registered literal | O |
| `received_schema_version` | strict integer | O |
| `correlation_id` | `SafeId` | R |
| `errors` | `Q[SchemaError]`, maximum 100 | only for aggregated schema failure |

`SchemaError` contains:

| Field | Type | Presence |
|---|---|---|
| `code` | `SCHEMA_VALIDATION_FAILED \| VALIDATION_ERROR_LIMIT_REACHED` | R |
| `json_pointer` | `JsonPointer` | R |
| `safe_message` | safe non-normative text | R |

An aggregated schema rejection has outer code
`SCHEMA_VALIDATION_FAILED`, uses the first real error's pointer as its outer
`json_pointer`, and includes `errors`. Real errors sort by the UTF-8 bytes of
their JSON Pointer and then by code. If more than 99 real errors exist, return
the first 99 followed by a forced-last sentinel:

```json
{
  "code": "VALIDATION_ERROR_LIMIT_REACHED",
  "json_pointer": "",
  "safe_message": "Additional validation errors were omitted."
}
```

Contract-kind and schema-version failures occur at an earlier precedence stage
and are single errors without `errors`.

Tests assert code, path, precedence, ordering, and safety. Human messages are
not a byte-stable API.

## Terminal logging contract

Exactly one terminal JSONL event is emitted per command:

```text
triana.contracts.validate.succeeded
triana.contracts.validate.rejected
triana.records.seal.succeeded
triana.records.seal.rejected
triana.records.verify.succeeded
triana.records.verify.rejected
triana.cli.rejected
triana.logging.rejected
```

Required fields:

| Field | Type |
|---|---|
| `timestamp` | `Timestamp` |
| `event_name` | closed event-name literal |
| `severity` | `INFO \| WARN \| ERROR` |
| `service` | literal `"triana-cli"` |
| `service_version` | `SafeLabel` |
| `command` | `contracts.validate \| records.seal \| records.verify \| cli \| logging` |
| `outcome` | `SUCCEEDED \| REJECTED` |
| `correlation_id` | `SafeId` |
| `duration_ms` | `DurationMs` |

Conditional safe fields:

```text
contract_kind
schema_version
safe_object_id
reason_code
json_pointer
errors
record_hash
```

Rules:

- `service` is `triana-cli`.
- Success is `INFO` with outcome `SUCCEEDED`.
- Expected rejection is `WARN` with outcome `REJECTED`.
- Internal invariant failure is `ERROR`.
- A caller may supply `--correlation-id SafeId`; otherwise the CLI creates a
  UUID outside the artifact.
- A missing/unknown command or invalid option uses `triana.cli.rejected` with
  `command: "cli"`.
- An invalid caller correlation ID is never echoed. The CLI generates a safe
  replacement UUID and rejects with `CLI_USAGE_ERROR`.
- Logs may vary in timestamp, duration, and generated correlation ID; artifacts
  never vary.
- No raw path, rejected value, payload, evidence locator, URL, prompt, trace
  content, tool argument/result, header, cookie, environment value, canonical
  preimage, or exception representation is loggable.
- Redaction occurs before the sink.
- Redaction failure suppresses the unsafe event and emits exactly one
  `triana.logging.rejected` event with `command: "logging"`, severity `ERROR`,
  the required common terminal fields, and
  `reason_code: "LOG_REDACTION_FAILED"`. It contains no public error array,
  object identity, path, rejected value, exception, or original unsafe event
  field, and exits 70.

On command failure, the one terminal rejection event also carries the public
error fields. There is no second error line.

## CLI contract

```text
triana contracts validate <file-or-"-">
triana records seal <unsigned-record-file-or-"-">
triana records verify <sealed-record-file-or-"-">
```

- `-` means stdin.
- Exactly one input is accepted.
- No network operation is allowed.
- `--help` is informational: it exits 0, writes human help to stdout, and emits
  no JSON terminal event.
- `contracts validate` accepts all five document kinds plus unsigned records.
- A valid self-hashed document must already carry a correct hash.
- `contracts validate` writes the canonical validated document plus LF to
  stdout. A local-sensitive trace is emitted only because the caller explicitly
  invoked this local command; it is never copied to logs or upload-safe records.
- `records seal` accepts only an unsigned Release Evidence Record and writes
  the canonical sealed record plus LF.
- `records verify` accepts only a sealed Release Evidence Record and writes:

  ```json
  {"record_hash":"sha256:...","verified":true}
  ```

  in canonical form plus LF.
- Success exit is 0 and stderr contains one terminal success event.
- Failure stdout is empty before artifact emission, stderr contains one safe
  terminal rejection event, and the exit status follows the error table.
- `OUTPUT_WRITE_FAILED` caused by a broken pipe cannot guarantee recovery of
  bytes the operating system already accepted; the CLI stops writing and
  returns exit 7 without claiming atomic stdout.
- Explicit output-file support and overwrite behavior are outside 0A; shell
  redirection is the only file-output mechanism.

## Deterministic property-test contract

Pinned Hypothesis version comes from `uv.lock`; the initial lock resolves
`6.163.1`.

```text
profile: slice0a
seed: 2026073001
max_examples: 200
deadline: none
database: none
phases: generate, shrink
derandomize: false
report_multiple_bugs: true
suppress_health_check: none
```

Every property entrypoint supplies the fixed seed explicitly. Machine-readable
evidence records:

```text
hypothesis_version
profile
seed
fixture_universe_hash
test_node_id
reproduction_blob on failure
```

The property suite runs twice in fresh processes. Every minimized failure
becomes a fixed committed fixture before the slice may pass.

## Example policy

The independent test author owns valid fixtures, canonical bytes, and expected
digests. This specification intentionally does not publish a precomputed valid
fixture that the test author could copy without independent derivation.

The test author must create:

- one minimal and one complete valid document for every public kind;
- one unsigned and one sealed Release Evidence Record;
- independently calculated canonical bytes and identities;
- a behavior-to-field traceability table.

Those fixtures are valid only if every required field above is present, every
conditional field follows its variant, every derived identity independently
matches this specification, and no field outside this closed registry exists.
