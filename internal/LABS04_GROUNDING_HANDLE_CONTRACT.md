# LABS-04 grounding-handle correction

Status: frozen for independent RED on 2026-08-01.

This is a correction to LABS-04 Grounded Case Factory, not a new product
milestone. It supersedes only the provider-facing evidence/reference wire, the
incomplete semantic-diagnostic allowance, the exactly-five case constant, and
the mandatory separate critic stage in the parent slice and recovery contract.
Portable case artifacts, canonical citation identity, privacy, caching,
budgets, and usefulness authority remain unchanged.

## Outcome and authority

The corrected factory must make valid grounding mechanically selectable by the
model. The LLM still proposes semantic personas, intents, turn policies, cases,
claim text, and whether multi-trace evidence corroborates or conflicts.
Deterministic code owns provider-handle construction, canonical citation and
portable record identity, evidence resolution, support-state derivation,
reference validation, defect paths, lane acceptance, diversity, lineage, and
all arithmetic. A human still owns usefulness acceptance.

Triana adopts LangChain `create_agent`, backed by LangGraph, as the restricted
runtime in this slice. It exposes only `search_evidence`, `get_trace_packet`,
`inspect_budget`, and `submit_case_batch`; shell, web, arbitrary filesystem
access, delegation, runtime routing, and durable model-written memory are not
installed. Strict structured output constrains handles and slots;
deterministic guardrails validate the result; all stages, tool calls, questions,
and defects are preserved for evaluation and replay.

The active flow is one restricted `create_agent` graph per batch, prompted to
perform grounding research then case architecture, followed by deterministic
validation and at most one new Repair invocation for that batch. The prior
independent LLM CRITIQUE stage is removed; it duplicated deterministic
criticism, cost, and the same identity failure channel without contributing
acceptance authority.

The agent may return `NEEDS_INPUT` with at most three bounded questions whose
answers materially change target relevance or case construction. The complete
run state is preserved and resumes only with explicit answers; missing answers
do not trigger assumptions or provider fallback.

## Provider evidence catalog

The provider no longer receives separate full `evidence` and `citations`
objects. It receives one `evidence_catalog` derived without model judgment from
the already-selected, redacted evidence and canonical citations:

```json
{
  "artifact_kind": "case_factory_evidence_catalog",
  "schema_version": 1,
  "traces": [
    {
      "trace_handle": "T001",
      "structural_cluster_id": "cluster-...",
      "events": [
        {
          "evidence_handle": "E000001",
          "sequence": 0,
          "event_kind": "USER_MESSAGE",
          "content": "..."
        }
      ]
    }
  ],
  "gaps": []
}
```

Trace handles are `T001` through `T025` in selected-trace order. Evidence
handles are `E000001` upward in selected-trace then event order. They are
run-local selectors, never portable identity. Each event appears once with its
handle and its allowlisted projected value. The private deterministic map from
each evidence handle to its canonical citation record is complete and
one-to-one. The portable `evidence_index.json` and final records continue to
contain canonical `citation-...` IDs only. The provider never receives or must
copy canonical trace or citation IDs.

The evidence hash remains over the existing canonical provider-evidence root;
catalog bytes and the runtime constrained schema are covered by the exact
provider-request hash. Request fitting measures the corrected complete request
and still removes only whole lowest-priority traces when necessary.

## Provider output

In proposal/revision drafts, each grounding claim has exactly:

```json
{
  "claim_key": "claim_1",
  "claim": "bounded semantic claim",
  "support_kind": "CORROBORATING",
  "evidence_handles": ["E000001", "E000027"]
}
```

`support_kind` is `CORROBORATING | CONFLICTING`. Deterministic normalization
maps unique evidence handles to sorted canonical citation IDs and derives:

- one distinct source trace -> `SINGLE_OBSERVATION`;
- two or more traces plus `CORROBORATING` -> `SUPPORTED`;
- two or more traces plus `CONFLICTING` -> `CONFLICTED`.

The model cannot declare its own support cardinality. Empty, duplicate, or
unknown handles are defects and never remapped. The runtime proposal schema
constrains every `evidence_handles` item to the exact handles in this run.

Provider-local coordination keys are closed selectors rather than arbitrary
identity: numbered persona, intent, turn-policy, case, and claim slots bounded
by the requested batch size. Every supplied case slot must occur once. Claim
keys are scoped to their containing object. Portable asset, claim, and case IDs
remain content-derived after validation.

The exact GENERATE/REPAIR instruction says to choose only supplied evidence
handles, use two different trace handles for corroborated/conflicted claims,
use every supplied case slot once, and never copy or invent a canonical ID.

Requested case count is 1--25 with default 10. Calls are deterministic batches
of at most five cases. Each batch receives exactly its closed slot set and may
have at most one repair. Budget refusal stops before an unfunded call and
publishes typed partial evidence; it never silently reduces the requested
count. Launch acceptance requests 10 and requires at least seven distinct,
grounded, reviewable cases.

## Complete deterministic guardrail

Diagnosis runs on every schema-valid proposal and revision before conversion,
returns every applicable defect in one sorted pass, and never uses exception
order as the user-visible diagnosis. It must cover at least:

- wrong asset/case counts; missing or duplicate closed slots;
- empty, duplicate, unsorted, or unknown evidence handles;
- invalid or duplicate claim keys; broken and duplicate claim references;
- unused claims and observed text without a valid local claim;
- missing asset references and cases without a case-local observed anchor;
- empty reaction rules; invalid gaps/tools/stressors; empty evaluation fields;
- forbidden demographic/medical traits and all existing bounds.

Exact safe codes and RFC 6901 paths are stable. Unknown handles use
`UNKNOWN_EVIDENCE_HANDLE`; duplicate slots use `DUPLICATE_LOCAL_SLOT`; broken
asset or claim references use `BROKEN_LOCAL_REFERENCE`; duplicate evidence
handles use `DUPLICATE_EVIDENCE_HANDLE`. All are repairable. Any unclassified
conversion failure is `INTERNAL_INVARIANT_FAILED`, not `PROVIDER_FAILED` and
not a pass. REPAIR receives the catalog, draft, and complete defects; strict
deterministic revalidation alone clears them.

## Refusal, preservation, and evaluation

Schema-invalid output, unknown handles, duplicate handles, broken references,
or final semantic defects fail closed. There is no fuzzy lookup, nearest-ID
repair, fabricated citation, fallback prompt, alternate provider, retry, or
partial acceptance of an invalid asset lane. Safe requests, responses, parsed
drafts, normalized drafts, and defects remain preserved under the existing
private cache and diagnostic bundle rules. Normalized drafts are additional
stage artifacts and contain canonical citations but no provider secret.

The independent regression corpus must include a synthetic reconstruction of
the observed live failure: invented evidence handles, repeated intent slots,
and multi-citation claims whose resolving evidence comes from one trace. It
must prove the corrected runtime schema rejects invented handles, the complete
guardrail reports duplicate/broken slots, and valid handles from two traces
produce canonical citations and deterministically derived support. It must
also prove that provider inputs contain no canonical citation or trace IDs,
each event text occurs once in the catalog, old cached responses cannot match
the new request identity, and final portable artifacts contain no run-local
handles.

Local exit requires all prior tests and canonical hashes, new immutable RED
then GREEN tests, Ruff, strict mypy, build, clean-wheel parity, and a zero-call
fake-transport run producing at least seven of 10 distinct valid cases. A fresh paid
Azure usefulness smoke is outside the remaining USD 15 authorization and
requires a separately recorded budget authorization after local GREEN.

## Change budget

Independent test-author ownership:

```text
triana-labs/tests/case_factory_acceptance/**
triana-labs/tests/case_factory_adversarial/**
triana-labs/tests/case_factory_fixtures/**
```

Implementation-author ownership:

```text
triana-labs/src/triana_labs/case_factory/evidence.py
triana-labs/src/triana_labs/case_factory/semantic.py
triana-labs/src/triana_labs/case_factory/generate.py
triana-labs/src/triana_labs/case_factory/schemas/proposal.schema.json
triana-labs/src/triana_labs/case_factory/schemas/critique.schema.json
```

One pinned LangChain/LangChain-OpenAI/LangGraph dependency set is allowed after
live conformance. DeepAgents remains future design only. No target-agent
execution, judge, global memory, UI, real-data support, prompt search, or
unrelated cleanup is authorized. Workers stop before editing outside their
owned paths.

## Assertion-level restricted-runtime wire

This section closes the test-author entry gap and supersedes conflicting
five-case, three-stage, Azure OpenAI lineage, and provider-envelope details in
the parent packet. It adds no CLI surface. The existing `generate(...)` remains
unchanged; the restricted path is an internal API:

```python
def generate_restricted(
    observer_manifest: Path,
    intelligence_manifest: Path,
    config_path: Path,
    output_path: Path,
    *,
    cache_path: Path,
    transport: RestrictedAgentTransport,
    clock: Clock,
    environ: Mapping[str, str],
    publisher: ArtifactPublisher | None = None,
    requested_case_count: int = 10,
) -> GenerateResult: ...

def resume_restricted(
    pause_manifest: Path,
    answers: Mapping[str, str],
    output_path: Path,
    *,
    cache_path: Path,
    transport: RestrictedAgentTransport,
    clock: Clock,
    publisher: ArtifactPublisher | None = None,
) -> GenerateResult: ...
```

Requested count is `1..25`; globally numbered `case_1..case_N` slots form
consecutive batches of at most five. Resume always writes a distinct new output
directory and never mutates its pause bundle. `GenerateResult.outcome` is
`COMPLETED | COMPLETED_WITH_GAPS | NEEDS_INPUT | REJECTED`.

### Transport seam

The framework-neutral fake/live boundary is:

```python
class RestrictedAgentTransport(Protocol):
    def run(
        self, request: AgentBatchRequest, tools: RestrictedTools
    ) -> AgentBatchResponse: ...
```

`AgentBatchRequest` is closed and contains exactly `run_id`, `batch_id`,
`phase`, `case_slots`, `evidence_catalog`, `answers`, `prior_submission`,
`deterministic_defects`, and `remaining_budget_usd`. `run_id` is
`sha256:<64 lowercase hex>`; `batch_id` is `batch-001` upward; `phase` is
`GENERATE | REPAIR`; remaining budget is a six-place decimal string. Answers
are ordered closed objects with `question_id` and `answer`. GENERATE has empty
answers/defects and null prior submission except a resumed paused batch, which
has its explicit answers. REPAIR has a non-null prior submission and non-empty
sorted defects.

`AgentBatchResponse` is closed and contains exactly `status`, `submission`,
`questions`, `failure_reason_code`, `request_bytes`, `response_bytes`,
`input_tokens`, `output_tokens`, `actual_cost_usd`, and `latency_ms`. Status is
`SUBMITTED | NEEDS_INPUT | FAILED`. SUBMITTED alone has a submission;
NEEDS_INPUT alone has one to three questions; FAILED alone has a closed failure
reason. Raw bytes are private diagnostic inputs, are secret-scanned before
preservation, and never enter portable identity. The runtime supplies exactly
the four frozen tools; wrappers record every invocation and the transport
cannot bypass them.

### Attempts, diagnostics, and terminal bundles

Each `generation_attempts.jsonl` record is closed and contains exactly:
`artifact_kind: case_factory_agent_attempt`, `schema_version: 1`, `attempt_id`,
`batch_id`, `phase`, `case_slots`, `status`, `reason_code`, `request_hash`,
`response_hash`, `input_tokens`, `output_tokens`, `actual_cost_usd`,
`reserved_cost_usd`, and `latency_ms`. Status is `SUCCEEDED | INVALID |
NEEDS_INPUT | TOOL_FAILED | PROVIDER_FAILED | BUDGET_REFUSED`. Nullable values
are null only when the corresponding boundary was not reached.

Each private tool-call record contains exactly `artifact_kind:
case_factory_tool_call`, `schema_version: 1`, `attempt_id`, `sequence`,
`tool_name`, `arguments`, `status`, `reason_code`, and `result`. Tool names are
the four allowlisted names; tool status is `SUCCEEDED | FAILED`.

Secret-safe diagnostics live only below
`<cache_path>/runs/<run-id-hex>/` at:

```text
agent/tool_calls.jsonl
provider/batch-NNN/generate/{request,response,parsed,normalized,defects}.json
provider/batch-NNN/repair/{request,response,parsed,normalized,defects}.json
```

Absent phases have no directory. Response, parsed, and normalized files exist
only if that boundary was reached; defects exist for every parsed submission.
Every terminal result other than NEEDS_INPUT publishes the existing portable
bundle. Control JSONL files are empty, `comparison_available` is false in eval
and review, and valid earlier batches remain visible after a later stop. No
portable file contains run-local handles, local slots, questions, raw provider
bytes, or tool transcripts. Attempt stages and semantic lineage stages are
`GENERATE | REPAIR`; provider lineage names Fireworks GLM-5.2 through Foundry.

Closed top-level reasons are `INVALID_CASE_BATCH | BUDGET_REFUSED |
TOOL_EXECUTION_FAILED | PROVIDER_TRANSPORT_FAILED | PROVIDER_REFUSED |
PROVIDER_INVALID_RESPONSE | MATERIAL_INPUT_REQUIRED | QUESTION_LIMIT_EXCEEDED |
RESUME_INPUT_INVALID | INTERNAL_INVARIANT_FAILED`. Deterministic defects remain
separate. Unknown handles are `UNKNOWN_EVIDENCE_HANDLE`; after at most one
failed repair, the terminal reason is `INVALID_CASE_BATCH`, never a provider
failure. Tool and provider failures retain the narrow safe reason in their
private record while the top-level reason uses the closed code.

### Pause and immutable resume

A NEEDS_INPUT output contains exactly `manifest.json`,
`generation_attempts.jsonl`, `evidence_index.json`, `questions.json`, and
`resume_state.json`. Questions have `artifact_kind:
case_factory_questions`, `schema_version: 1`, `run_id`, and one to three closed
objects containing `question_id` (`Q001..Q003`), `question`, and
`material_scope: TARGET_RELEVANCE | CASE_CONSTRUCTION`.

Resume state has exactly `artifact_kind: case_factory_resume_state`,
`schema_version: 1`, `run_id`, `input_manifest_hash`,
`intelligence_manifest_hash`, `config_hash`, `requested_case_count`,
`completed_case_slots`, `pending_case_slots`, `attempt_ids`, `question_ids`,
`reserved_cost_usd`, and `actual_cost_usd`. A logical run may pause once.
Resume answers must contain every and only listed question ID with non-empty
bounded text; otherwise it publishes no new output and refuses before transport
with `RESUME_INPUT_INVALID`. Resume reuses completed batches/attempts
byte-for-byte and starts at the paused batch. It never repeats a completed
provider or tool call. A second question request or a fourth total question is
`QUESTION_LIMIT_EXCEEDED` with no assumption, retry, or fallback.

### Budget and batched projection

Restricted config adds only:

```json
{"budget":{"max_usd":"3.000000","reservation_usd_per_agent_call":"0.500000"}}
```

Both are six-place nonnegative decimals and `max_usd` cannot exceed
`3.000000`. Before every GENERATE or REPAIR call, deterministic code refuses if
`reserved_so_far + reservation_per_call > max_usd`; exact equality is funded.
Refusal appends a BUDGET_REFUSED attempt, publishes typed partial evidence,
does not call transport, and never reduces requested count. Actual provider
cost is separately recorded and never rewrites the reservation ledger.

The old PROPOSE/CRITIQUE/REVISE attempt projection becomes per-batch
GENERATE/REPAIR. Portable semantic schemas remain unchanged after handle
normalization. Manifest requested count is N. A later budget/provider/tool stop
with earlier valid batches is `COMPLETED_WITH_GAPS`; without any valid batch it
is `REJECTED`. Invalid batches are never partially accepted. The ten-case live
exit still requires at least seven distinct grounded reviewable cases.
