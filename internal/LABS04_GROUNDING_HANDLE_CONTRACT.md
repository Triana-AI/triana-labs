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

Triana adopts DeepAgents/LangGraph as a restricted runtime in this slice. It
exposes only `search_evidence`, `get_trace_packet`, `inspect_budget`, and
`submit_case_batch`; shell, web, arbitrary filesystem access, runtime routing,
and durable model-written memory are disabled. Strict structured output
constrains handles and slots; deterministic guardrails validate the result;
all stages, tool calls, questions, and defects are preserved for evaluation
and replay.

The active flow is one restricted DeepAgent run per batch with a grounding
researcher and case architect, followed by deterministic validation and at
most one Repair handoff for that batch. The prior independent LLM CRITIQUE
stage is removed; it duplicated deterministic criticism, cost, and the same
identity failure channel without contributing acceptance authority.

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

One pinned DeepAgents/LangGraph dependency set is allowed after live
conformance. No target-agent execution, judge, global memory, UI, real-data
support, prompt search, or unrelated cleanup is authorized. Workers stop
before editing outside their owned paths.
