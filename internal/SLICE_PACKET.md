# Active implementation slice — LABS-04 Grounded Case Factory

Status: **FROZEN ENTRY CONTRACT — ORCHESTRATOR RED AUDIT CORRECTION**

Date: 2026-08-01
Branch: `codex/labs-04-semantic-eval`
Canonical base: `83454e3`
Slice ID: `LABS-04-grounded-case-factory`
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
`NO_USABLE_USER_EVIDENCE`. The complete provider request is limited to 100,000
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
    "max_calls": 6,
    "normal_calls": 3,
    "max_input_bytes_per_call": 100000,
    "max_output_tokens_per_call": 4096,
    "max_wall_clock_seconds": 600,
    "request_timeout_seconds": 60,
    "max_transport_retries_per_stage": 1,
    "max_usd": "10.000000",
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
uses the configured maximum output tokens, includes all six possible calls,
and refuses before egress if its upper cost bound exceeds USD 10. Missing price
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

Each stage permits at most one retry for a transport failure, HTTP 429, or HTTP
5xx response. Schema failure, content filtering, refusal, length truncation,
invalid citation, or semantic rejection is not transport-retried. Every retry
has a new attempt ID; the failed attempt remains in `generation_attempts.jsonl`.

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

### Lane A — deterministic contract and safety

- strict config, input, portable artifact, citation, and reference schemas;
- stable IDs, hashes, order independence, exact bytes, and fresh-process
  repeatability;
- Observer/intelligence integrity and lineage agreement;
- endpoint, credential-name, authorization, secret-sentinel, and egress
  refusals before a provider call;
- conservative budget preflight and per-attempt reservation;
- provider timeout, 429/5xx, content filter, refusal, length, malformed output,
  schema error, and retry ledger behavior through a fake internal transport;
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
  exceeds six calls or USD 10 conservative bound;
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
  symlinks, nonregular files, invalid UTF-8, BOM, depth/size/line limits;
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
- transport retry succeeds/fails, original attempt preserved, no semantic
  retry, retry budget exhausted, and retry never exceeds six total calls;
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
maximum new production code is 1,500 normally formatted nonblank/noncomment
lines. These are ceilings, not targets. Any new file or line beyond them stops
the implementation author.

## 13. Reproducible exit gate

The slice implementation is mechanically complete only when:

- the independent RED commit and test aggregates are frozen before production;
- all new acceptance and reserved adversarial cases pass unchanged;
- all prior 188 tests pass and the five canonical Observer hashes are
  byte-identical;
- Ruff, strict mypy, package build, clean CPython 3.13.14 wheel install, source
  and wheel CLI parity, secret scan, governance, and decision-memory pass;
- fake-provider tests prove every refusal/partial/retry/budget state without
  network access;
- the authorized Azure/HRAI-50 smoke runs without exceeding three normal/six
  total calls or the USD 10 conservative cap;
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
