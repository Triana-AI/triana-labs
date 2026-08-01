# Active implementation slice — LABS-04 Grounded Case Factory

Status: **LIVE PROVIDER RED — CORRECTED BUDGET TESTS FROZEN**

Date: 2026-08-01
Branch: `codex/labs-04-semantic-eval`
Canonical base: `83454e3`
Slice ID: `LABS-04-grounded-case-factory`

Active failure and repair evidence is maintained in
`internal/LABS04_TRIAGE.md`. That ledger records classification and status but
does not supersede this packet or the exact wire contract.
Owner: Akarsh
Orchestrator: Codex

Exact wire authority: `internal/LABS04_WIRE_CONTRACT.md`. That document closes
field-level schemas, canonical bytes, identity preimages, provider envelopes,
transport behavior, partial publication, blind ordering, and the corrected
smoke identity. Its exact rules supersede examples or shorthand here without
expanding this packet's product scope.

## 1. Product outcome and falsifiable claim

Prove or falsify that Triana can convert a verified, authorized synthetic
conversation-trace corpus into useful, inspectable designs for genuinely
adaptive multi-turn simulations.

The checkpoint produces proposed behavioral personas, intents, adaptive turn
policies, and five proposed simulation cases. It does not execute an agent.
The cases remain proposals until a human reviews them. If fewer than three
distinct valid cases survive the deterministic gates, or the owner review does
not clear the frozen usefulness rubric, the checkpoint fails and LABS-05
multi-turn execution does not start.

```text
LABS-02 file adapter
  -> LABS-01 Trace Observer
  -> LABS-03 structural Corpus Intelligence
  -> LABS-04 Grounded Case Factory
       -> evidence-backed proposed personas
       -> evidence-backed proposed intents
       -> adaptive proposed turn policies
       -> five proposed simulation cases
       -> grounding, diversity, cost, lineage, and gap evidence
  -X-> no target-agent execution
  -X-> no panel run, behavioral verdict, or persistent memory
```

This slice advances the active charter's
`GENERATED_MULTI_TURN_SIMULATION` launch cut. It is the evidence gate before a
runtime harness: Triana must not build machinery that executes generic,
unsupported, repetitive, or unusable cases faster.

## 2. Invocation and exact input boundary

The user-facing command is:

```text
triana cases generate <observer-manifest> \
  --intelligence <intelligence-manifest> \
  --config <case-factory-config.json> \
  --out <new-directory>
```

The Observer manifest and intelligence manifest are both explicit inputs. The
command verifies both complete bundles through the existing owners and proves
that `intelligence_manifest.input_manifest_hash` equals the SHA-256 of the
exact Observer manifest bytes. No path is inferred from a hash, working
directory, environment, source ID, or sibling-name convention.

The slice accepts only the already-supported `SYNTHETIC` privacy class. It does
not add production, customer, public-corpus, Blitz, or `LOCAL_SENSITIVE`
support. Source IDs, system-visible messages, tool arguments, tool results,
terminal reasons, and opaque metadata do not enter provider-bound evidence.

Eligible semantic evidence is projected from validated traces as:

- user and assistant message content with trace ID and event sequence;
- ordered safe tool names and result state, without arguments or results;
- terminal state, without reason text;
- LABS-03 structural cluster membership and mechanical eligibility;
- explicit omission and gap records.

Only case-generation-eligible traces enter selection. Selection is input-order
independent: sort clusters by cluster ID, take one trace per cluster in
round-robin order, then take remaining traces by trace ID, stopping at 25
traces or the provider-bound byte ceiling. A message event above 16,384 UTF-8
bytes is omitted whole and creates `EVIDENCE_EVENT_TOO_LARGE`; it is never
silently truncated. A trace with no remaining user content is excluded with
`NO_USABLE_USER_EVIDENCE`. The complete provider request is limited to 240,000
UTF-8 bytes before transmission.

The evidence projection is treated as untrusted data. It is serialized inside
a closed JSON evidence field, receives no tools, cannot change system
instructions, and cannot name credentials, endpoints, budgets, acceptance
states, or output paths.

## 3. Frozen Azure provider experiment

LABS-04 uses one Azure OpenAI deployment through the GA v1 chat-completions
REST surface and strict structured outputs:

```text
provider_kind: AZURE_OPENAI
api_surface: /openai/v1/chat/completions
deployment: gpt-4.1-mini
model_name: gpt-4.1-mini
model_version: 2025-04-14
response_format: json_schema, strict=true
```

The existing owner Azure subscription was inspected read-only on 2026-08-01.
The selected deployment exists on the owner's Azure AI resource. `Luna` was
not an observed Azure deployment. `gpt-5.6-terra` exists but was not selected:
newer capability does not establish a lower price, and this checkpoint chooses
the smaller deployed model with documented structured-output support.

The config names, but never contains, credentials:

```json
{
  "artifact_kind": "case_factory_config",
  "schema_version": 1,
  "provider": {
    "provider_kind": "AZURE_OPENAI",
    "endpoint_env": "AZURE_OPENAI_ENDPOINT",
    "api_key_env": "AZURE_OPENAI_API_KEY",
    "secret_sentinel_envs": ["TRIANA_LABS04_SECRET_SENTINEL"],
    "allowed_endpoint_host": "<operator-approved-azure-host>",
    "api_surface": "/openai/v1/chat/completions",
    "deployment": "gpt-4.1-mini",
    "model_name": "gpt-4.1-mini",
    "model_version": "2025-04-14"
  },
  "authorization": {
    "allow_provider_egress": true,
    "privacy_classes": ["SYNTHETIC"],
    "allowed_projection": "LABS04_SYNTHETIC_SEMANTIC_EVIDENCE_V1"
  },
  "generation": {
    "candidate_count": 5,
    "evidence_trace_limit": 25,
    "seed": 2026080104
  },
  "budget": {
    "max_calls": 3,
    "normal_calls": 3,
    "max_input_bytes_per_call": 240000,
    "max_output_tokens_per_call": 12000,
    "max_wall_clock_seconds": 600,
    "request_timeout_seconds": 60,
    "max_transport_retries_per_stage": 0,
    "max_usd": "8.700000",
    "conservative_input_usd_per_million_tokens": "10.000000",
    "conservative_output_usd_per_million_tokens": "40.000000",
    "pricing_source": "OPERATOR_CONSERVATIVE_BOUND"
  }
}
```

The endpoint environment value must be exact HTTPS with no userinfo, query, or
fragment and must resolve to the configured host. The API key is read only from
the named environment variable. No ambient credential or Azure CLI fallback is
allowed. The smoke's exact existing resource host is supplied in a local,
uncommitted config and represented portably only by its hash; the raw endpoint
does not enter the repository.

The conservative preflight treats each UTF-8 input byte as one input token,
uses the configured maximum output tokens, includes exactly three stage calls,
and refuses before egress if its upper cost bound exceeds USD 8.70. Missing price
information is never zero. Provider-reported usage and any available charged
cost remain separate observed facts; the conservative estimate is never
presented as an invoice.

Before every provider call the order is:

```text
verify input and explicit authorization
  -> construct the allowlisted evidence projection
  -> reject configured secret sentinels and credential-shaped content
  -> validate exact endpoint and egress class
  -> hash the exact provider-bound payload
  -> reserve call, token, time, and USD budget
  -> call Azure
  -> validate finish reason and strict response
  -> append metering and lineage
```

No new runtime dependency is allowed. The production client uses the standard
library HTTPS surface plus existing Pydantic validation. Tests use an internal
transport boundary; there is no public test mode, environment bypass, or
recorded credential.

## 4. Bounded semantic loop

The experiment uses exactly three normal stages over the same evidence and
schema:

1. `PROPOSE`: produce five assets/cases. This output is the one-shot control.
2. `CRITIQUE`: identify citation, support, invention, adaptability, and
   duplication defects. The critique is advisory and creates no score or truth.
3. `REVISE`: produce the final five proposed assets/cases using the evidence,
   original proposal, and critique.

The corrected run permits exactly one attempt per stage. Transport failure,
HTTP 429/5xx, schema failure, content filtering, refusal, length truncation,
invalid citation, and semantic rejection are never retried; the single failed
attempt remains visible when the contract publishes a partial result.

The loop has no tools, retrieval service, agent framework, memory backend,
sub-agent API, dynamic prompt rewriting, or model-selected evidence. It is a
Triana-owned bounded orchestration over plain provider calls. The critic may
improve a proposal but cannot evaluate the checkpoint or promote an asset.

## 5. Authority and proposal states

| Concern | Deterministic Triana code | Azure model | Human owner |
|---|---|---|---|
| Input membership, evidence selection, IDs, hashes | owns | none | none |
| Support counts and citation existence | owns | supplies requested references | none |
| Persona, intent, policy, scenario, rubric content | schema/validity only | proposes | reviews/corrects |
| Semantic entailment of claim by citation | cannot prove | cannot approve | judges sample |
| Duplicate arithmetic and effective N | owns | cannot override | judges usefulness |
| Budget, endpoint, egress, attempts, lineage | owns | reports usage only | authorizes config |
| Accepted truth or persistent ruling | storage absent | forbidden | not created in this slice |

Every semantic asset and case is born `PROPOSED`. A valid citation proves that
the cited evidence exists, not that the model interpreted it correctly.
`VALID_CITATION` must never be rendered as `VALID_INTERPRETATION`.

Closed support states are:

```text
SUPPORTED           two or more independent traces cited
SINGLE_OBSERVATION  exactly one independent trace cited
CONFLICTED          cited evidence contains declared material conflict
INSUFFICIENT        no defensible semantic proposal
GENERATED_VARIATION scenario material generated for coverage, not observed
```

Every retained grounding claim uses `SUPPORTED`, `SINGLE_OBSERVATION`, or
`CONFLICTED` and has citations. `INSUFFICIENT` is a gap state, while
`GENERATED_VARIATION` is a semantic-item basis with no grounding claim. A case
must contain at least one observed citation-backed anchor. Generated variation
can add a situation but cannot be counted as observed customer behavior.

## 6. Exact portable artifact bundle

`--out` must not exist and its immediate parent must be a real directory. A
completed or completed-with-gaps run publishes atomically:

```text
manifest.json
generation_attempts.jsonl
evidence_index.json
control_personas.jsonl
control_intents.jsonl
control_turn_policies.jsonl
control_case_candidates.jsonl
personas.jsonl
intents.jsonl
turn_policies.jsonl
case_candidates.jsonl
case_factory_eval.json
human_review_template.json
```

All JSON artifacts use compact sorted-key UTF-8 with one LF; JSONL has one such
object per physical line. Artifact digests cover exact bytes. Paths,
timestamps, random UUIDs, secrets, raw HTTP headers, raw provider responses,
and Azure request IDs are excluded from portable identity. Provider response
content appears only through validated portable proposal fields.

Every semantic portable record contains `artifact_kind`, `schema_version: 1`,
`input_manifest_hash`, `intelligence_manifest_hash`, `proposal_state` where
semantic, `fidelity`, and `lineage`.

### 6.0 Closed common field registry

All objects are closed and reject unknown fields. JSON integers are strict and
bounded to `0..9007199254740991`; booleans are not integers. Digests match
`^sha256:[0-9a-f]{64}$`. Portable IDs match
`^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$`. Safe codes match
`^[A-Z][A-Z0-9_]{0,63}$`. Semantic text is UTF-8, permits LF but no other
C0/C1 control, and is 1–4,096 bytes. Opening turns are 1–16,384 bytes. Labels
are 1–256 bytes. Collections preserve order unless explicitly called sorted;
duplicate stable IDs are invalid. `null` appears only in novelty companion
fields, conditional attempt reason/response/provider-cost fields, and
uncompleted human-review fields.

`Lineage` has exactly:

```json
{
  "provider_kind": "AZURE_OPENAI",
  "endpoint_host_hash": "sha256:<digest>",
  "deployment": "gpt-4.1-mini",
  "model_name": "gpt-4.1-mini",
  "model_version": "2025-04-14",
  "prompt_pack_hash": "sha256:<digest>",
  "provider_evidence_hash": "sha256:<digest>",
  "stage": "PROPOSE",
  "seed": 2026080104,
  "attempt_ids": ["attempt-..."]
}
```

`stage` is `PROPOSE | REVISE`; the critique is not a semantic artifact.
Attempt IDs are unique and ordered. `fidelity` is exactly
`SYNTHETIC_CORPUS_GROUNDED`. `proposal_state` is exactly `PROPOSED`.

All semantic list elements use `SupportedText`:

```json
{
  "text": "bounded semantic text",
  "basis": "OBSERVED",
  "claim_ids": ["claim-..."]
}
```

`basis` is `OBSERVED | GENERATED_VARIATION`. `OBSERVED` requires one or more
unique claim IDs resolving within the same asset or case. Generated variation
requires an empty claim list and never raises observed support. Lists of
`SupportedText` are limited to 20 items; grounding claims and citations are
limited to 100; cases are exactly five per valid provider proposal; personas,
intents, and turn policies are each 1–10.

`GroundingClaim` and `EvidenceCitation` use the exact shapes in section 6.1.
Citation ID lists are unique and sorted by citation ID. A claim with
`SUPPORTED` or `CONFLICTED` requires citations from at least two distinct
trace IDs; `SINGLE_OBSERVATION` requires exactly one distinct trace ID;
`INSUFFICIENT` is retained only as a gap and cannot back `OBSERVED` text.

### 6.1 Evidence citation and claim

```json
{
  "citation_id": "citation-<digest-prefix>",
  "trace_id": "trace-safe-id",
  "event_sequences": [1, 2],
  "evidence_hash": "sha256:<digest>",
  "structural_cluster_id": "cluster-..."
}
```

Event sequences are unique, ascending, and resolve only to projected evidence.
The evidence hash covers the exact projected citation bytes, not the raw trace.

```json
{
  "claim_id": "claim-<digest-prefix>",
  "claim": "bounded proposed semantic text",
  "support_state": "SUPPORTED",
  "citation_ids": ["citation-..."]
}
```

Claim and citation IDs are content-derived from schema-versioned canonical
content. Equal semantic content has one identity; duplicate stable keys fail.

### 6.2 Persona

```json
{
  "artifact_kind": "persona_proposal",
  "schema_version": 1,
  "persona_id": "persona-<digest-prefix>",
  "proposal_state": "PROPOSED",
  "label": "bounded non-demographic label",
  "behavioral_traits": [],
  "communication_tendencies": [],
  "constraints": [],
  "grounding_claims": [],
  "input_manifest_hash": "sha256:...",
  "intelligence_manifest_hash": "sha256:...",
  "fidelity": "SYNTHETIC_CORPUS_GROUNDED",
  "lineage": {}
}
```

Persona fields describe observable behavior. Demographic, protected, medical,
or identity attributes are rejected unless they are explicitly present,
relevant, allowed by the evidence contract, and cited. LABS-04's allowed
projection does not authorize those fields, so the initial implementation
rejects them.

### 6.3 Intent

```json
{
  "artifact_kind": "intent_proposal",
  "schema_version": 1,
  "intent_id": "intent-<digest-prefix>",
  "proposal_state": "PROPOSED",
  "goal": "bounded proposed text",
  "known_constraints": [],
  "observed_success_signals": [],
  "observed_failure_or_abandonment_signals": [],
  "grounding_claims": [],
  "input_manifest_hash": "sha256:...",
  "intelligence_manifest_hash": "sha256:...",
  "fidelity": "SYNTHETIC_CORPUS_GROUNDED",
  "lineage": {}
}
```

An observed signal is not accepted success/failure truth. The UI/report layer
does not exist here and no PASS/FAIL label is created.

### 6.4 Adaptive turn policy

```json
{
  "artifact_kind": "turn_policy_proposal",
  "schema_version": 1,
  "turn_policy_id": "turn-policy-<digest-prefix>",
  "proposal_state": "PROPOSED",
  "information_reveal_policy": [],
  "reaction_rules": [],
  "clarification_behavior": [],
  "escalation_tendencies": [],
  "stop_conditions": [],
  "forbidden_inventions": [],
  "grounding_claims": [],
  "input_manifest_hash": "sha256:...",
  "intelligence_manifest_hash": "sha256:...",
  "fidelity": "SYNTHETIC_CORPUS_GROUNDED",
  "lineage": {}
}
```

The policy expresses how a simulated user may react to the future agent's
behavior. A prewritten dialogue, fixed list of future turns, assistant text,
tool call, or hidden target answer is schema-invalid.

### 6.5 Simulation case candidate

Each line of `case_candidates.jsonl` and
`control_case_candidates.jsonl` has the illustrative shape below; the
independent tester derives exact fixtures from
`internal/LABS04_WIRE_CONTRACT.md`, not from production models, schemas, or
serialization output:

```json
{
  "artifact_kind": "simulation_case_candidate",
  "schema_version": 1,
  "case_id": "case-<digest-prefix>",
  "proposal_state": "PROPOSED",
  "fidelity": "SYNTHETIC_CORPUS_GROUNDED",
  "input_manifest_hash": "sha256:...",
  "intelligence_manifest_hash": "sha256:...",
  "persona_id": "persona-...",
  "intent_id": "intent-...",
  "turn_policy_id": "turn-policy-...",
  "scenario": {
    "opening_user_turn": "bounded text",
    "known_facts": [],
    "private_user_facts": [],
    "unknowns": [],
    "allowed_user_actions": [],
    "tool_world_constraints": [],
    "termination_conditions": [],
    "expected_tool_names": [],
    "stressor_codes": []
  },
  "grounding_claims": [],
  "proposed_evaluation": {
    "criteria": [],
    "abstain_conditions": []
  },
  "novelty": {
    "slot_key": "sha256:...",
    "exact_duplicate_of": null,
    "duplicate_cluster_id": null
  },
  "lineage": {},
  "gaps": []
}
```

References must resolve within the same output lane. Every known/private fact,
constraint, termination condition, and proposed evaluation criterion is a
claim reference or explicitly generated variation. `private_user_facts` means
scenario facts withheld from the future agent, not private customer data.
Control cases resolve only to `control_personas.jsonl`,
`control_intents.jsonl`, and `control_turn_policies.jsonl`; revised cases
resolve only to the unprefixed final asset files.

Lineage contains provider kind, endpoint-host hash, deployment, model name and
version, prompt-pack hash, provider-bound evidence hash, stage, seed, and
attempt IDs. It contains no credential, raw endpoint, local path, or provider
request ID.

### 6.6a Attempt, manifest, evidence-index, and evaluation shapes

Each `generation_attempts.jsonl` line has exactly:

```json
{
  "artifact_kind": "case_factory_generation_attempt",
  "schema_version": 1,
  "attempt_id": "attempt-<digest-prefix>",
  "stage": "PROPOSE",
  "attempt_index": 0,
  "status": "SUCCEEDED",
  "reason_code": null,
  "request_hash": "sha256:<digest>",
  "response_hash": "sha256:<digest>",
  "input_tokens": 0,
  "output_tokens": 0,
  "provider_reported_cost_usd": null,
  "conservative_cost_usd": "0.000000",
  "deployment": "gpt-4.1-mini",
  "model_name": "gpt-4.1-mini",
  "model_version": "2025-04-14"
}
```

`stage` is `PROPOSE | CRITIQUE | REVISE`. `status` is
`SUCCEEDED | TRANSPORT_FAILED | PROVIDER_REFUSED | CONTENT_FILTERED |
TRUNCATED | INVALID_RESPONSE | BUDGET_REFUSED`. Success requires response
hash, token counts, and null reason. Failure requires one closed reason and
permits a response hash only when safe response bytes existed. Missing
provider-reported cost is null, never zero. Decimal USD strings have exactly
six fractional digits, are nonnegative, and remain estimates unless explicitly
provider-reported.

`evidence_index.json` has exactly artifact kind
`case_factory_evidence_index`, schema version, both input hashes,
`selection_algorithm: LABS04_CLUSTER_ROUND_ROBIN_V1`, selected trace count,
excluded trace count, projected byte count, an ordered `citations` list, and
an ordered `gaps` list. Each gap has exactly `reason_code`, optional safe
`trace_id`, and optional event sequence; it contains no omitted content.

`manifest.json` has exactly artifact kind `case_factory_manifest`, schema
version, both input hashes, privacy class `SYNTHETIC`, producing component and
version, provider/model/deployment/prompt/evidence hashes, seed, outcome,
attempt/valid/raw/distinct/duplicate/gap counts, conservative USD estimate,
human review state, and an `artifacts` object mapping the other twelve exact
relative paths to digests. Outcome is `COMPLETED | COMPLETED_WITH_GAPS`;
human review state is `PENDING` at generation time.

`case_factory_eval.json` has exactly artifact kind
`case_factory_evaluation`, schema version, both input hashes, raw and effective
N, duplicate algorithm/version/threshold and clusters, requested/valid/invalid
case counts for control and revised lanes, citation-valid/invalid counts,
support-state counts, attempt/call/token/conservative-cost counts, sorted gap
codes, `machine_status: PASSED | FAILED`, and
`human_review_state: PENDING`. Machine status passes only with at least three
distinct valid revised cases, zero invalid retained citations, and no privacy,
authorization, or budget violation.

`human_review_template.json` has exactly artifact kind
`case_factory_human_review`, schema version, evaluation-manifest hash,
rubric version `LABS04_USEFULNESS_V1`, deterministic blind seed, ordered review
items, and `review_state: PENDING`. Each review item contains a blind ID, the
case content needed for review, citations needed for semantic inspection, six
null integer scores, null critical-failure code, and null notes. It contains no
lane, stage, model, attempt, or original case ID. A separate
`blind_lineage` mapping in `case_factory_eval.json` resolves blind IDs after
review; it is not included in the template.

### 6.6 Diversity

`slot_key` hashes persona ID, intent ID, turn-policy ID, source structural
cluster IDs, sorted stressor codes, and ordered expected tool names. Two valid
cases with the same slot key are exact slot duplicates and only the first by
case ID counts toward effective N. Source clusters are the union reachable
through the case and its resolved persona, intent, and turn-policy claims.

Near-duplicate text uses Unicode casefolding, whitespace tokenization, and
token-set Jaccard similarity over `opening_user_turn`, intent goal, and
reaction-rule text. Similarity at or above `0.85` with the same expected tool
path creates one duplicate cluster. Similar text with a different ordered
expected tool path remains distinct. The raw cases remain in the attempt
record, but duplicates do not increase effective distinct N. Exact-slot and
near-text edges form separate per-lane graphs; mixed components are labeled
explicitly. The report names
the algorithm, version, threshold, cluster sizes, raw N, and effective N.

## 7. Evaluation-first acceptance contract

The independent acceptance suite is complete and valid RED before production
implementation begins. It has three evidence lanes.

The first 109-case freeze at `949fcaa` was paused when isolated adversarial
review found the missing resource ceilings. After the wire correction at
`02b7801`, the independent author added 33 resource cases without changing the
original 109. Codex independently reproduced the corrected suite before
reauthorizing production: 142 cases collected, 140 expected behavioral RED
failures, and two unaffected passes. That evidence was contaminated by the
implementation author's untracked partial package in the shared worktree. On
clean commit `f280f98`, Codex and the implementation author independently
reproduced the authoritative state: 142 collected, 141 expected behavioral RED
failures, and one passing normative-schema check. All 188 prior tests passed
unchanged.
Ruff and format checks passed. The sorted concatenated test/fixture content
SHA-256 is
`0d71c4146d10e54b7d5eed22c85e14d38855919766196ac0028e3b627af74c90`;
the eleven test-owned files contain 3,339 physical lines. The SHA-256 of the
NUL-sorted relative-path per-file hash-list stream is
`3ed4858ee7607915513abf8f785d8ec227dc1d0f91c6a8bf13f45e944a4c22d9`.
Any change under the two test-author-owned paths invalidates this corrected
freeze and stops production.

After candidate `2c6aeb8` passed the immutable acceptance contract, the
independent tester reproduced six additional contract-derived RED cases in an
isolated worktree: self-consistent forged intelligence accepted before egress;
wrong CRITIQUE and REVISE request-too-large reason codes; raw `Invalid` leakage
from non-Money provider cost; missing staging-directory fsync; and replacement
of a TOCTOU-created output target. The adversarial file SHA-256 is
`d9b42b3650d2c6ee9abc492e485d21369ab4de8af078a393b9c6c6da6266c276`.
All six failures were independently reproduced by Codex before production
correction. These assertions are immutable until a new explicit freeze.

The implementation author's first correction made those six assertions green,
but a second independent isolated pass found ten further contract violations.
The added 305-line file
`tests/case_factory_adversarial/test_uncovered_contract_edges.py` has SHA-256
`4e6e7502cfb0866f598beabe78e09f31208d3936b0a69fce55a1781450e2f50a`.
Codex reproduced the combined adversarial state as 17 collected, seven passed,
and ten RED: destination visibility before atomic publication; replacement of
a destination inode swapped immediately before publication; misclassification
of an exactly 100,348-byte PROPOSE request; missed exact API-key leakage in an
otherwise ignored response field; three invalid secret-configuration cases;
two malformed lowercase DNS hosts; and escaped interruption after a valid
proposal. The already-correct pre-proposal interruption behavior remains
frozen. Both adversarial files are immutable until a new explicit freeze.

The implementation-author correction against commit `f39dbc7` changes only
`evidence.py`, `generate.py`, and `provider.py`. It uses native atomic
no-replace publication on Darwin and Linux with fail-closed unsupported-platform
behavior; validates PROPOSE size, exact response secrets, secret configuration,
and DNS hosts before egress; and preserves typed post-proposal interruption
custody. The author and Codex independently reproduced 17/17 adversarial,
142/142 acceptance, 188/188 historical, Ruff, and strict mypy GREEN. The
package contains 1,779 normally formatted nonblank/noncomment production lines.
This is a corrected implementation candidate, not mechanical checkpoint exit:
the full packaging/privacy/hash gate and the one-shot Azure/HRAI smoke remain.

The first combined full-suite run exposed three order-dependent runtime imports
inside the frozen acceptance harness: `from conftest` resolved to the already
cached LABS-03 module rather than the LABS-04 module. The independent test
author reproduced 344 passes/three import failures and moved only the same
helper names into the three files' existing module-level imports; no assertion,
fixture, or expected behavior changed. Codex reproduced the exact three-file
diff and re-froze the 142-case suite with sorted concatenated content SHA-256
`0044aab6adc61a5f1c65184e98be2ee7b84fb4f0f404288315c4043c2bee8fd5`
and sorted per-file hash-list SHA-256
`df4d1aaacd24c8049e47bda6594b09697ced68af02b820507075cf984be4ec73`.
This narrow harness correction supersedes only the two earlier LABS-04
acceptance aggregate hashes; all 142 behavioral assertions remain frozen.
The versioned verifier now enforces both corrected acceptance aggregates, both
adversarial-file hashes, and source/clean-wheel `cases generate --help` parity.
Codex ran it through a clean CPython 3.13.14 install with network access:
347/347 tests, Ruff, strict mypy, lock verification, source distribution,
wheel build/install, all prior source/wheel handoffs, five canonical Observer
hashes, governance, and the added LABS-04 hashes passed. The remaining exit
work is the authorized one-shot Azure/HRAI smoke, artifact inspection, secret
scan after that run, budget reconciliation, and owner usefulness review.

Smoke preflight preserved two zero-egress refusals. The first was Codex's local
config omission (`api_key_env`), corrected and exactly preflighted before any
provider call. The valid config then exposed a contract defect: the pinned
HRAI projection passed the 90,000-byte evidence-root bound at 73,650 bytes but
created 424 singleton citations and an exact 193,867-byte PROPOSE request, so
the required smoke refused `EVIDENCE_TOO_LARGE(3)` with zero Azure calls. The
independent test author correctly rejected a proposed 100-total-citation cap as
contrary to the exact wire. The accepted correction retains the existing
90,000-byte root bound, then removes lowest-priority selected traces from the
tail until the then-current complete request limit, recording the existing
`EVIDENCE_BYTE_LIMIT_REACHED` gap for every removal. It never replaces removed
traces or truncates evidence. Under the superseded 100,000-byte request wire,
the pinned corpus retained nine priority traces and 198 citations in a
93,166-byte request; that preflight evidence led to the first actual call below.

The independent test author encoded the corrected wire in one synthetic-only
268-line adversarial file with SHA-256
`9219b756e9f7c386cfadc4b74a0775a9716593c8e803bcd1e1144f88aba148cd`.
Codex reproduced three collected cases as one GREEN exact-100,000-byte boundary
and two RED failures under the then-current wire: exact 100,001-byte two-trace tail fitting, and repeated
priority-preserving tail removal without admitting a 26th replacement trace.
The oracle independently reconstructs every citation, gap, exclusion, order,
and input-order invariant. The then-current 100,348-byte oversized single-trace
refusal remained green. The live result below supersedes only those byte and
budget boundaries; the behavioral assertions require independent correction.

The implementation author changed only `case_factory/generate.py` to fit the
fresh provider projection after exact schema/citation construction. The author
and Codex independently reproduced 3/3 tail-fit, 20/20 total adversarial,
142/142 acceptance, 188/188 historical, Ruff, and strict mypy GREEN. Production
is 1,810 counted lines with no dependency. A fresh pinned-HRAI preflight now
retains nine traces and 198 citations, records 16 explicit byte-limit
exclusions, and constructs a 93,166-byte PROPOSE request. That correction passed
the 350-case versioned gate before the actual provider call below.

The preserved actual provider run made exactly one request. Azure telemetry for
the exact minute records HTTP 200, 28,295 input tokens, and exactly 4,096 output
tokens—the configured output ceiling. Triana returned `PROVIDER_FAILED(8)`
after 34.6 seconds and published no cases. The exact raw response is deliberately
not retained, so output truncation is an evidence-backed inference rather than
a quoted provider field; auth, transport, non-200 HTTP, and zero-generation
failures are ruled out. No unchanged rerun is allowed.

The corrected remaining experiment budget removes retries and permits exactly
three calls: 240,000 input bytes and 12,000 reserved output tokens per call,
with `max_usd=8.700000`. Its worst-case reservation is
`3 * (2.400000 + 0.480000) = 8.640000`. The preserved first call reserved
`1.095500`, so the cumulative conservative ceiling is `9.735500`, below the
owner-approved USD 10. The 193,867-byte full 25-trace HRAI proposal now fits;
no evidence reduction is expected at PROPOSE. This correction supersedes only
the request/output/call/retry/USD literals and their exact test bytes. New
independent RED must be frozen before production or another provider call.

The independent test author corrected only nine LABS-04 test files against the
new literals and no-retry semantics. Codex reproduced 163 LABS-04 cases as 131
intended RED failures and 32 passes against unchanged production, with all 188
historical tests green. The complete 14-file LABS-04 test/fixture freeze has
sorted concatenated content SHA-256
`877924718cb90cbcf05fe8179c3fefdb5f44f75e89f7e84b66d232e6fc81d1b9`
and sorted per-file hash-list SHA-256
`22c42e65e3ebb902cd8c558586a9bfddfb76cd742bdd3f2f3074aa4088ac7a65`.
It contains 4,285 physical lines. Exact 240,000 acceptance, 240,001 whole-trace
tail fitting, a 240,055 sole-trace refusal, three single attempts, no transient
retry, 12,000-token request bytes/reservation, USD 8.64 preflight, and USD 8.70
cap are now immutable before production resumes. These two aggregate hashes
supersede the earlier LABS-04 acceptance-only aggregates and all three prior
adversarial-file hashes; no behavioral assertion outside the corrected wire is
weakened.

The independent post-implementation audit found that `240,055` above was a
brittle fixture byte count rather than the refusal contract. Production and
the independent request oracle both constructed the same 240,776-byte request;
the test now asserts only the meaningful precondition that the sole-trace
request exceeds 240,000 bytes, followed by `EVIDENCE_TOO_LARGE(3)`, zero
transport, and no output. The dedicated independent oracle still freezes exact
240,000 acceptance and 240,001 whole-trace tail fitting. The corrected test is
SHA-256 `3d3afc582aafdf45e0cdcbc812987355a50b00170e1d0bf64b2a8bdaeb1d2a07`;
the complete 14-file aggregates are content SHA-256
`fd3d310166742fd67469fb68f068a5a6296ff724eb87a444a2f47ca2d4edf2be`
and per-file hash-list SHA-256
`399aa3010821083cd2e87a073fffe7381eeb11b75d0c4eee4eb90b8496dda315`.
All 163 LABS-04 and 188 historical tests passed after this correction.
For the acceptance-plus-fixture subset enforced separately by the versioned
gate, the corrected content SHA-256 is
`217083673e064de01af78970ef09a2e5d8bad6c1c36aee3746fbfca1103be18c`
and its per-file hash-list SHA-256 is
`51d67a9922c53f9b1b9da52ba0274c4494da946bd56f6a173c3cb1c74f5f6b4a`.
The corrected individual adversarial hashes enforced by the same gate are
`a4140877cb081469a047868cb96a873fcad10b21ebd256177097ec2dc802f943`
for contract regressions,
`3d3afc582aafdf45e0cdcbc812987355a50b00170e1d0bf64b2a8bdaeb1d2a07`
for uncovered edges, and
`9e0540e18ea540cb37041570758a69c002a5fc63b49d8cfae16c466f04f6866c`
for request tail fitting.

The corrected HRAI preflight retained all 25 accepted traces, all 424
citations, zero exclusions, and built a 193,868-byte request with no secret
sentinel. The preserved corrected live attempt then made exactly one HTTP 200
request before returning `PROVIDER_FAILED(8)` after 42.7 seconds and publishing
no cases. Azure minute telemetry records 58,855 input and 4,877 output tokens,
well below the 12,000 output ceiling. The raw response is intentionally not
retained, so its exact finish reason and fields cannot be quoted.

Inspection exposed an independent production defect against wire section 8:
the parser rejected `usage` unless it had exactly the three core token keys or
those keys plus `cost`, even though this contract requires benign Azure extras
to be ignored after projecting validated fields and Azure documents optional
usage-detail objects. The independent regression at `8da6fca` freezes a valid
structured response with documented usage details and benign metadata: core
usage/cost alone is projected portably while the raw response hash remains
sensitive to extras. Its test SHA-256 is
`e4c626083bb6139604e8fd27965bc8f59ad4caa23fe44f01ed5f883ae6776632`;
the 164-case acceptance subset is frozen at content SHA-256
`5b0cdb61674dea350bcc35c05e853a69c25d4950ab141422159daa8cb98e3896`
and per-file hash-list SHA-256
`5c5e42090f577004b4f0821f16e52d6dc28fd242bfa27e78229ea36e21b8ff03`.
The production-only fix at `18748af` projects and validates only core usage and
optional cost after strict raw parsing, secret scanning, and response hashing.
All 164 LABS-04 and 188 historical tests, Ruff, and strict mypy pass locally.
This proven parser bug is a strong explanation for the preserved live failure,
not a claim about unretained raw fields. A changed-version live run still
requires explicit cumulative-budget and no-rerun reconciliation.

The owner-approved bounded recovery is frozen by contract `1957cd9`, independent
RED `1f65901`, production `dae4bf1`, and stale-expectation reconciliation
`3e716bb`. The three decisive recovery tests prove exact local response-cache
miss/write/replay with zero replay transport/cost, safe post-egress failure
bundles, and a schema-valid but semantically invalid PROPOSE draft carrying the
three frozen defects through CRITIQUE and REVISE into five valid revised cases
with an unavailable control comparison. All 167 LABS-04 tests pass. The new
acceptance-plus-fixture content SHA-256 is
`c8e327774c2bfb6cf5733ed1390ab7ece045386338baf330d0ceecace5aedfca`
and its repository-root per-file hash-list SHA-256 is
`d1031cee6692851687e50db1871797aee9133b7aeb50b0fed43fd0a1b9066dd5`.
The three verifier-enforced adversarial hashes are respectively
`5c1a65d177896ab45081e37195c4f77e50e7edd12443a452a50006213bedc1bd`,
`97a205a81010f4c116de543711a8c41e149cb4db3519f8866a0567c4b9e10c5b`,
and `d5d290fa6be8af5ec46618b1ce573bc6cf97624598c60491bab02d0eacd11636`.
The final live HRAI usefulness verdict remains pending the complete local gate.

### Lane A — deterministic contract and safety

- strict config, input, portable artifact, citation, and reference schemas;
- stable IDs, hashes, order independence, exact bytes, and fresh-process
  repeatability;
- Observer/intelligence integrity and lineage agreement;
- endpoint, credential-name, authorization, secret-sentinel, and egress
  refusals before a provider call;
- conservative budget preflight and per-attempt reservation;
- provider timeout, 429/5xx, content filter, refusal, length, malformed output,
  schema error, and no-retry ledger behavior through a fake internal transport;
- no unsafe value in terminal logs or portable lineage;
- atomic publication, no overwrite, safe cleanup, and typed partial output;
- source and clean-wheel parity, unchanged 188 tests, frozen acceptance
  aggregates, and five unchanged Observer artifact hashes.

### Lane B — grounding and diversity

- every retained claim has valid citations or an explicit generated-variation
  state;
- support states match independent trace counts;
- hallucinated IDs, wrong event ranges, circular references, and wrong cluster
  membership are rejected;
- no single observation is represented as supported population behavior;
- static scripted dialogues and unresolved asset references are rejected;
- exact and near duplicates remain visible but do not increase effective N;
- similar language with different consequential tool paths remains distinct;
- five requested cases produce at least three valid distinct cases or the run
  cannot claim a usable case set;
- this slice refuses model, deployment, prompt, or seed configuration changes;
  evidence changes create new lineage, and any future explicitly authorized
  contract variant must change the corresponding lineage field/hash;
- the critic cannot create a score, acceptance state, or persistent truth.

### Lane C — blind human usefulness review

`human_review_template.json` presents paired one-shot and revised cases under
deterministically shuffled blind IDs. Provider stage and ordering are hidden
from the review items but recoverable through a separate lineage mapping.
The owner scores 1–4 on:

1. citation-grounded interpretation;
2. realism of the user situation;
3. readiness for genuinely adaptive multi-turn execution;
4. distinctness from other cases;
5. relevance to testing the target agent;
6. absence of unjustified assumptions.

Product-checkpoint pass requires:

- no critical privacy, invalid-citation, or unsupported-invention failure;
- at least three cases score 3 or 4 on grounding, simulation readiness, and
  usefulness;
- median distinctness at least 3;
- at least 80% of inspected citations judged semantically supportive;
- the reviewer can explain what each passing case tests and how its simulated
  user should adapt.

Automated tests and the live smoke can finish unattended. Until Akarsh supplies
this review, the implementation slice may be mechanically green but the
product checkpoint is `AWAITING_HUMAN_REVIEW`, not passed.

## 8. Exact HRAI-50 smoke gate

The required non-test smoke input is the existing tracked HRAI historical
traffic corpus:

```text
source repository: /Users/akarshgajbhiye/Documents/hr_ai
source commit: 728f6c5058efe40a16e2aecc9b528b3353f4df4f
source path: experiments/historical_traffic_v0/out/run_200/normalized_traces.jsonl
source physical lines: 200
source SHA-256: 76e0c2c2c2e777845f6fcda9907d7e386f8f3510ce4834126fc39d16889bf01b
selection: first 50 physical lines, bytes preserved exactly
selected SHA-256: 4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c
classification: SYNTHETIC_EXISTING_TRACE_CORPUS
```

The source is existing end-to-end trace data generated independently of the
LABS-04 tests. It is synthetic, not production or real-user evidence. The
smoke deterministically copies only the first 50 physical lines to a private
local temporary file, then reads it through the shipped LABS-02 adapter; no
HRAI trace, prompt, output, or raw corpus is copied into Triana.

Preflight exposed that the previously named `run_50b` file was legacy and
incompatible with the shipped adapter (0/50 accepted). It is not used. The
corrected selected v2 records produced 25 accepted and 25 explicit LABS-02
source rejections; Observer accepted all 25 mapped traces as eligible; LABS-03
produced 22 clusters and three expected semantic gaps. Those observations are
honest denominators, not favorable acceptance constants. The final smoke may
not select a different subset or rerun to improve them.

The reproducible smoke sequence is:

```text
HRAI-50 normalized-trace-v2
  -> shipped LABS-02 adapter with explicit SYNTHETIC attestation
  -> shipped Trace Observer
  -> shipped structural Corpus Intelligence
  -> LABS-04 Grounded Case Factory through Azure gpt-4.1-mini
```

Smoke acceptance requires:

- all 50 source lines are accounted for by the adapter;
- every downstream accepted/rejected denominator is explicit;
- the exact input and output hashes are retained in local evidence;
- normal generation uses no more than three calls and total execution never
  exceeds three calls or the corrected-run USD 8.70 conservative bound;
- five final cases are requested and at least three valid distinct cases are
  emitted;
- every retained claim passes deterministic citation validation;
- a blind human-review template is produced;
- no raw HRAI data is committed or described as real-user/customer evidence;
- an unfavorable, partial, repetitive, or weak result is preserved without
  rerun-to-green.

## 9. Closed failure, refusal, and partial behavior

Preflight failure produces no provider call and no output target. Fatal failure
after egress produces no success claim; completed provider attempts remain
represented only when a safe partial bundle can be finalized.

Closed reasons and exits:

```text
2  CLI_USAGE_ERROR, INPUT_READ_FAILED, OUTPUT_ALREADY_EXISTS,
   OUTPUT_PARENT_MISSING, CONFIG_INVALID
3  INPUT_TOO_LARGE, EVIDENCE_TOO_LARGE
4  MANIFEST_INVALID, UNSUPPORTED_PRIVACY_CLASS,
   PROVIDER_AUTHORIZATION_REFUSED, ENDPOINT_REFUSED,
   SECRET_SENTINEL_DETECTED
5  CORPUS_INTEGRITY_FAILED, INTELLIGENCE_MISMATCH,
   NO_USABLE_SEMANTIC_EVIDENCE, NO_VALID_CASES
7  OUTPUT_WRITE_FAILED, OUTPUT_CLEANUP_FAILED
8  PROVIDER_FAILED
9  BUDGET_REFUSED, BUDGET_EXHAUSTED
70 INTERNAL_INVARIANT_FAILED
```

Success with five valid revised cases and no gaps exits 0. A safe bundle with
at least one valid case plus source/provider/schema/duplicate/budget gaps exits
10 as `COMPLETED_WITH_GAPS`. Fewer than three distinct valid cases always
carries `INSUFFICIENT_DISTINCT_CASES`; it may publish partial evidence but
cannot pass the checkpoint. No invalid proposal is silently repaired, dropped
from attempted denominators, or replaced under the same identity.

One terminal JSON event is written to stderr with only service/version,
command, outcome, duration, closed reason, attempted/valid/distinct counts,
call count, and conservative USD estimate when those facts are complete. It
contains no path, endpoint, trace/case ID, content, citation, tool name, prompt,
provider response, exception, or credential.

## 10. Mandatory edge-case register

The independent tester must encode every relevant row before valid RED.

### Input and integrity

- empty, tiny, homogeneous, duplicate, and source-rejection corpora;
- zero usable user turns and system/bot text misclassified as user evidence;
- multilingual and code-switched text preserved without invented language
  normalization;
- malformed/tampered/stale manifests and artifacts, duplicate identities,
  symlinks, nonregular files, invalid UTF-8, BOM, depth limits, and the exact
  config/intelligence byte and single-line ceilings in the wire contract;
- same trace ID with changed content and duplicate content under different IDs;
- input reorder, fresh process repeat, seed change, and model/prompt change.

### Grounding and semantics

- hallucinated trace, event, cluster, asset, case, claim, and citation IDs;
- citation to unprojected system text, tool arguments/results, or omitted text;
- unsupported persona traits, demographic invention, and one trace presented
  as representative population behavior;
- persona/intent conflation, contradictory constraints, circular claims,
  impossible scenario facts, and ambiguous/conflicting intent;
- fixed future dialogue disguised as a turn policy;
- case without an observed anchor or generated material mislabeled observed;
- proposed rubric without abstain conditions or presented as accepted truth.

### Injection, privacy, and egress

- trace text instructing the model to ignore policy, reveal secrets, call
  tools, change budgets, self-approve, or write files;
- configured sentinels and credential-shaped content in every projected field;
- missing egress consent, wrong privacy class, endpoint alias/redirect,
  userinfo/query/fragment, HTTP, wrong host, missing/malformed key;
- unsafe path, endpoint, prompt, evidence, header, exception, or response in
  logs and artifacts;
- hashing or call reservation before the provider-bound projection is safe.

### Provider and budget

- connection failure, timeout, TLS failure, 401/403, 429, 5xx, content filter,
  provider refusal, truncated/length output, empty output, invalid JSON,
  schema-invalid JSON, unknown fields, duplicate keys, and repeated response;
- transport/429/5xx failures remain single-attempt evidence with no retry;
  semantic failures likewise do not retry, and execution never exceeds three
  total calls;
- missing price, conservative bound above cap, exact boundary, usage above
  reservation, budget exhaustion between stages, and wall-clock exhaustion;
- critic or reviser failure preserves the one-shot evidence without claiming
  revised success.

### Diversity, publication, and evaluation

- exact semantic duplicate, exact slot duplicate, paraphrased duplicate,
  renamed-persona duplicate, and lexical similarity with different tool path;
- all five cases collapse to one cluster and partial effective N;
- output exists, parent missing/symlinked, mid-write failure, cleanup failure,
  user interrupt, and no portable timestamp/path entropy;
- critic attempts to score or approve, blind mapping is reversible but hidden
  from review items, missing human review remains pending, and no automated
  result becomes human usefulness.

## 11. Roles, immutable tests, and controlled parallel attack

There are exactly two worker agents plus the Codex orchestrator.

```text
Codex freezes and commits this packet
  -> independent test author writes the complete acceptance suite
  -> Codex reproduces valid RED and freezes test commit + aggregate hashes
  -> implementation author writes production without editing frozen tests
       || independent tester uses an isolated worktree for read-only/fuzz/
          mutation/adversarial attacks against the already-frozen contract
  -> Codex integrates only contract-derived regressions and owns exit verdict
```

The acceptance-authoring and production-authoring roles remain serial. The
parallel tester phase begins only after the RED freeze, uses an isolated
worktree, and cannot change expected behavior or acceptance meaning. A newly
found production violation receives a tester-authored regression before the
implementation author fixes it. A genuine contract hole stops the slice and
returns to the owner/orchestrator; it is not silently interpreted around. A
test defect returns only to the tester, receives a new explicit freeze, and
production pauses. The implementation author never edits a test or fixture.

## 12. Change budget

Orchestrator only:

```text
internal/SLICE_PACKET.md
internal/LABS04_WIRE_CONTRACT.md
internal/labs04_provider_schemas/**
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md
triana-labs/CHARTER.md
docs/ARCHITECTURE.md
docs/PROVENANCE.md
README.md
triana-labs/scripts/verify.sh
triana-labs/tests/case_factory_adversarial/**
```

Independent test author only:

```text
triana-labs/tests/case_factory_acceptance/**
triana-labs/tests/case_factory_fixtures/**
```

Implementation author only after RED freeze:

```text
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/case_factory/**
triana-labs/schemas/case_factory/**
```

The implementation author may add no dependency. Existing Observer,
intelligence, and adapter modules are read-only dependencies. Any discovered
need to edit them stops the worker and returns to Codex.

Explicitly untouched:

- `triana-core/**` and all five frozen contracts;
- all LABS-01/02/03 production, test, fixture, and canonical artifact bytes;
- package metadata, lockfile, CI stack, and unrelated formatting;
- HRAI, Kairos, Kairos-AI, Agentagon, Blitz, public corpora, and raw data;
- hosted ingestion, OTel, SDK, UI, runtime runner, memory, and comparison code.

Maximum production scope is the CLI addition, one bounded `case_factory`
package, and checked-in schemas. Maximum new production-file count is 14;
maximum new production code is 3,000 normally formatted nonblank/noncomment
lines. These are ceilings, not targets. Any new file, line, or edit outside the
authorized paths stops the implementation author.

## 13. Reproducible exit gate

The slice implementation is mechanically complete only when:

- the independent RED commit and test aggregates are frozen before production;
- all new acceptance and reserved adversarial cases pass unchanged;
- all prior 188 tests pass and the five canonical Observer hashes are
  byte-identical;
- Ruff, strict mypy, package build, clean CPython 3.13.14 wheel install, source
  and wheel CLI parity, secret scan, governance, and decision-memory pass;
- fake-provider tests prove every refusal/partial/no-retry/budget state without
  network access;
- the authorized Azure/HRAI-50 corrected smoke runs without exceeding three
  total calls or its USD 8.70 conservative cap, while all preserved smoke calls
  remain below the original cumulative USD 10 conservative cap;
- smoke artifacts retain every weak, duplicate, rejected, refused, and partial
  state without rerun-to-green;
- no raw HRAI data, secret, endpoint, absolute path, or provider payload enters
  the repository;
- actual changed files, dependencies, and line counts reconcile exactly with
  this budget;
- canonical docs, provenance, decision log, and local decision memory agree.

At that point the implementation may be `MECHANICALLY_GREEN`. The Grounded
Case Factory product checkpoint becomes `PASSED` only after the owner completes
the frozen blind review in section 7. Until then it is
`AWAITING_HUMAN_REVIEW`, and LABS-05 does not start.

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

Use `none` explicitly. No unrun check is reported as passing.

## 14. Explicit non-goals

- target-agent invocation or genuinely multi-turn execution;
- panel selection or execution, baseline/candidate comparison, F0/F1 labels,
  regression, release, PASS/BLOCK, or accepted-behavior claims;
- real-customer, production, Blitz, public, or local-sensitive trace support;
- redaction as a general product surface;
- DeepEval, Deep Agents, Hermes, OpenAI Agents SDK, generic provider SDK,
  coding-agent integration, browser/voice/multi-agent support;
- model judges, evaluator ensembles, automatic rubric approval, prompt/model
  training, or autonomous optimization;
- persistent, global, Mem0, managed, or cross-run memory;
- HTML/UI/report dashboard, hosted ingestion, accounts, SaaS, SDK, or OTel;
- changes to the frozen V1 contracts or suspended Release Review meaning.

Nothing in this packet authorizes LABS-05. The next checkpoint is proposed only
after human-reviewed LABS-04 evidence demonstrates usable case designs.

## 15. One-time repair-validation exception

Akarsh approved exactly one changed-version live run after parser fix
`18748af`, with an experiment-level cumulative conservative ceiling of USD 15.
The run uses the identical pinned HRAI subset, Observer/intelligence bundles,
Azure deployment/model/version, prompts, schemas, and seed. The existing
per-run three-call/USD 8.70 limits and zero-retry behavior remain unchanged.
Both earlier failed calls remain preserved; no alternate selection,
rerun-to-improve, or subsequent provider call is authorized. Prior reservations
total USD 3.514180 and the new worst case is USD 8.640000, for USD 12.154180
maximum cumulative reservation. Success still requires published cases and the
unchanged owner usefulness review; another failure stops the smoke.

The authorized repair-validation run stopped the smoke with another preserved
`PROVIDER_FAILED(8)`: exactly one Azure HTTP 200 request, 58,855 processed
prompt tokens, 4,444 generated tokens, 57.2 seconds, no second-stage call, and
no artifacts. It did not hit the output ceiling. Raw response bytes are not
retained, so the exact rejected field is unknown. No subsequent provider call
is authorized.

This result exposes a contract-design gap independent of the unknown raw
failure: strict provider output covers only `proposal.schema.json`, while
post-parse conversion additionally requires exact asset/case counts, local-key
formats and uniqueness, sorted references/gaps, support cardinality, valid
cross-asset references, complete claim use, reaction rules, and observed
anchors. A schema-conforming draft can therefore be discarded before CRITIQUE
under the generic `PROVIDER_FAILED(8)` result. No useful simulation designs
were produced, so LABS-04 fails its live smoke and remains unpassed. Recovery
requires a newly frozen eval-first slice; it cannot be represented as a prompt
retry, semantic weakening, or another provider call under this packet.

The owner-approved bounded recovery is frozen in
`internal/LABS04_RECOVERY_CONTRACT.md`. It supersedes only post-egress artifact
custody, exact response replay, cached-token accounting, typed semantic defects,
and invalid-PROPOSE repair flow. It authorizes no other LABS-04 expansion.
