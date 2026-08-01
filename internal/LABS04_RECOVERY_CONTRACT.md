# LABS-04 recovery contract

Date: 2026-08-01
Status: owner-approved recovery slice
Authority: narrows and supersedes only the failed-response, intermediate
artifact, exact-replay, and invalid-PROPOSE flow in
`internal/LABS04_WIRE_CONTRACT.md`; every other LABS-04 rule remains unchanged.

## 1. Outcome and non-goals

Make the existing Grounded Case Factory capable of producing or honestly
diagnosing five grounded case designs without another opaque paid failure.
This slice adds no model, provider framework, UI, memory layer, target-agent
execution, generic SDK, prompt optimization loop, or LABS-05 behavior.

## 2. Invocation and exact response cache

`triana cases generate` adds one required argument:

```text
--cache-dir <private-existing-or-new-directory>
```

The function boundary adds `cache_path: Path`. The cache root is local,
operator-owned, mode `0700`, is never inside the output target, and cannot be a
symlink. Triana creates a missing root with `0700`; an unsafe root refuses
before egress as `CACHE_REFUSED(4)`. Cache files are mode `0600`.

For each stage, cache identity is the domain-separated hash of endpoint-host
hash, deployment, model name/version, exact request-body hash, and prompt-pack
hash. An entry contains exact request bytes, HTTP status, exact secret-safe
response bytes, and canonical metadata with those identities and byte hashes.
It contains no API key, authorization header, environment value, or filesystem
path.

On an exact verified hit, no transport call, call reservation, or provider
cost occurs. The response is replayed through current parsing and validation
with `execution_mode: CACHE_REPLAY`. A miss uses `FRESH_PROVIDER`, then writes
the response atomically before parsing. Corrupt, mismatched, oversized, unsafe,
or secret-bearing entries refuse as `CACHE_INVALID(4)` with zero transport and
no fallback. A response containing an in-memory secret sentinel is neither
cached nor emitted raw; only its response hash and
`PROVIDER_RESPONSE_SECRET_DETECTED` defect survive.

Provider-native caching remains provider-owned. Triana projects
`usage.prompt_tokens_details.cached_tokens` when present as
`provider_cached_input_tokens`; missing means `null`, not zero. Conservative
budget arithmetic does not discount cached tokens.

## 3. Preserved intermediates

After the first provider response, every run atomically publishes either a
success/partial bundle or a failure bundle. Secret-safe stage bytes use:

```text
provider/propose/request.json
provider/propose/response.json
provider/propose/parsed.json
provider/propose/defects.json
provider/critique/request.json
provider/critique/response.json
provider/critique/parsed.json
provider/critique/defects.json
provider/revise/request.json
provider/revise/response.json
provider/revise/parsed.json
provider/revise/defects.json
generation_attempts.jsonl
evidence_index.json
case_factory_eval.json
human_review_template.json
manifest.json
```

Absent stages have no files. `request.json` is the exact body sent or replayed,
without headers. `response.json` is the exact safe provider body, including
envelope extras. `parsed.json` is the exact extracted content JSON when strict
parsing and provider-schema validation succeed. `defects.json` is always
present for a parsed proposal/revision and is sorted by
`(code, path, related_ids)`.

A failure manifest has `artifact_kind: case_factory_failure_manifest`, schema
version 1, `outcome: REJECTED`, top-level reason, failing stage, evidence and
provider lineage, attempt/call/token/cache/cost counts, and hashes of every
published artifact. Pre-egress input/privacy/config/budget refusal retains the
existing no-output behavior. Post-egress failure never deletes safe evidence.

## 4. Typed semantic defects

Every deterministic proposal/revision rejection emits records shaped as:

```json
{
  "code": "SUPPORT_CARDINALITY_MISMATCH",
  "path": "/personas/0/grounding_claims/2",
  "message": "SUPPORTED requires citations from at least two traces",
  "related_ids": ["citation-..."],
  "repairable": true
}
```

Exact codes cover asset/case counts; invalid/duplicate local keys; claim
count/key/text; missing, duplicate, unsorted, or unknown citations; support
cardinality; invalid text-to-claim references; unused claims; forbidden traits;
empty reaction rules; missing asset references; invalid tools/stressors/gaps;
empty evaluation fields; missing observed anchors; and bounded text/array
violations. Paths are RFC 6901 JSON pointers. Messages are closed safe
templates, never provider text. Related IDs contain only sorted validated safe
identifiers. Multiple defects survive; no first-error-only collapse.

Transport/envelope/JSON/schema/secret/finish failures retain existing reason
codes and gain a stage defect. `PROVIDER_FAILED(8)` may remain the CLI exit but
never without a published post-egress defect bundle.

## 5. Repair flow

```text
PROPOSE response
  -> preserve raw + parsed
  -> deterministic semantic diagnosis
     -> valid: build control lane
     -> invalid but parsed: preserve defects and continue
  -> CRITIQUE receives evidence + proposal + deterministic_defects
  -> REVISE receives evidence + proposal + critique + deterministic_defects
  -> preserve raw + parsed + final defects
  -> strict final conversion
```

The critic cannot clear or override deterministic defects. The reviser may
change the draft; deterministic revalidation alone determines usability. Final
semantic rules and at least three distinct valid cases remain unchanged.

When the original proposal is invalid, the control lane is unavailable with
`CONTROL_SEMANTICALLY_INVALID`; the review template contains only valid revised
cases and `comparison_available: false`. This slice judges absolute usefulness,
not improvement over an invalid control. An invalid revision publishes its
diagnostic bundle and no invalid case as usable.

## 6. Prompt change

Only CRITIQUE and REVISE prompts change: supplied deterministic defects are
untrusted-but-authoritative validator observations to address, and only
deterministic revalidation can clear them. PROPOSE content, provider, model,
evidence, schema, and seed remain unchanged. No examples, model switch,
temperature search, or optimization loop is added.

## 7. Acceptance and final live gate

The independent test author freezes RED before production for:

- post-egress raw request/response/parsed/defect preservation on success,
  invalid envelope, invalid proposal semantics, invalid revision, and partial;
- secret-bearing response non-retention with hash/reason preservation;
- exact cache miss/write/hit/replay, corrupt-entry refusal with zero transport,
  no fallback, permissions, and request/provider identity separation;
- provider `cached_tokens` projection and conservative non-discount;
- multiple stable path-specific semantic defects without first-error collapse;
- invalid PROPOSE reaching CRITIQUE and REVISE with exact defect bytes;
- valid revision producing at least three usable cases while invalid control is
  unavailable and never represented as usable;
- invalid revision publishing its full diagnostic bundle;
- unchanged prior privacy, budget, duplicate, citation, and package behavior.

After all local gates and a replay-only dry run pass, exactly one further live
HRAI run is authorized within the existing USD 15 cumulative ceiling. Prior
conservative reservations total USD 5.932860; a maximum USD 8.640000 run yields
USD 14.572860. It uses the same corpus/provider/model/version/evidence/seed,
zero retries, and no alternate selection. No later provider call is authorized.

## 8. Change budget

Test-author ownership:

```text
triana-labs/tests/case_factory_acceptance/**
triana-labs/tests/case_factory_adversarial/**
triana-labs/tests/case_factory_fixtures/**
```

Implementation-author ownership:

```text
triana-labs/src/triana_labs/case_factory/generate.py
triana-labs/src/triana_labs/case_factory/semantic.py
triana-labs/src/triana_labs/case_factory/provider.py
triana-labs/src/triana_labs/case_factory/primitives.py
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/case_factory/schemas/**
```

Maximum six production files plus schema files, 3,000 normally formatted
nonblank/noncomment production lines as a review alarm, no new dependency, and
no edits outside these paths without an explicit stop. The existing 188
historical tests, Observer hashes, LABS-02/03 behavior, and every unrelated
LABS-04 assertion remain unchanged.
