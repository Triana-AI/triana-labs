# LABS-05 Adaptive Multi-Turn Runner wire contract

Version: `LABS05_WIRE_V1`

Status: frozen 2026-08-02

This document is normative for the independent acceptance author and the
production author. Objects are closed: unknown fields and duplicate JSON keys
are invalid. Integers are strict `0..9007199254740991`; booleans are not
integers. Digests are `sha256:` plus 64 lowercase hexadecimal characters.
Portable IDs use `^[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}$`. Safe codes use
`^[A-Z][A-Z0-9_]{0,63}$`. Text is UTF-8, allows LF but no other C0/C1 control,
and is at most 16,384 bytes unless a smaller bound is stated.

## 1. Invocation

```text
triana episodes run CASE_FACTORY_MANIFEST \
  --review OWNER_REVIEW \
  --config CONFIG \
  --out NEW_DIRECTORY
```

Every input is a regular nonsymlink file. The manifest's immediate parent and
all declared sibling artifacts are real nonsymlink directories/files. Config
and review are one JSON object plus LF and at most 65,536 bytes. The LABS-04
manifest and declared artifacts must satisfy the existing Case Factory reader
and exact artifact hashes before target construction or simulator egress.

The selected case file must have exact file SHA-256
`06a3a2267f39041d98e08ef24466ffbc695e7833ebb16bd536f19f71c37ecbe4`.
The manifest file must have exact SHA-256
`817000637daef25bff9bd95eee46a25976f575d1b2d5aa62965a6c6d9c5b6cb9`.

### 1.1 Internal deterministic test seam

The public CLI always constructs real configured boundaries. The independent
suite uses this exact internal signature so it remains self-contained without
vendoring the external LABS-04 bundle, reading HRAI, or calling a provider:

```python
run(
    case_factory_manifest: Path,
    owner_review: Path,
    config_path: Path,
    output_path: Path,
    *,
    simulator: SimulatorTransport,
    target_factory: TargetProcessFactory,
    clock: Clock,
    environ: Mapping[str, str],
    publisher: ArtifactPublisher | None = None,
    source_verifier: TargetSourceVerifier | None = None,
    case_loader: CaseFactoryInputLoader | None = None,
) -> AdaptiveRunResult
```

`SimulatorTransport.complete(request)` returns one strict normalized provider
response with exact request/response bytes and usage/accounting fields.
`target_factory(launch)` returns one fresh session per episode exposing
`exchange(request) -> response` and `terminate() -> None`; the factory and
session retain all calls for test inspection. `TargetSourceVerifier` receives
the closed target config and either returns the verified source identity or
raises the typed source refusal. When `source_verifier` is null, production
uses the real Git/file verifier. `Clock` supplies deterministic monotonic
nanoseconds. `ArtifactPublisher`, when supplied, replaces only the final
atomic-publication operation for failure injection.

`CaseFactoryInputLoader` is the read-only external input-reader/validator
boundary. When null, production reads and validates the exact LABS-04 manifest,
every declared artifact digest, and the case file bytes. An injected loader
returns a closed `VerifiedCaseFactoryInput` with the exact manifest-file hash,
case-candidate-file hash, manifest semantic hash, and exactly three already
schema-validated case projections in the frozen selected order. The controller
still verifies those two exact file-hash literals, case IDs/membership/order,
closed projection shapes, and every downstream identity. CLI tests always use
the production loader for input/tamper/hash refusal; the injected loader exists
only so controller mechanics can be tested without requiring infeasible hash
preimages or vendoring the external LABS-04 bundle.

These dependencies may reproduce only their named external boundary. The case
loader replaces manifest/artifact schema and byte-integrity reading only; it
does not replace the controller's exact lineage/membership checks. No injected
dependency can bypass review/config validation, identity, budgets, sequencing,
adaptation binding, normalization, dedupe, custody, gaps, or publication
arithmetic. The CLI has no flag or environment variable for test mode.

### 1.2 Exact internal protocol and result shapes

The production module exposes these frozen Python shapes. Dataclasses are
frozen. `JsonObject` below means a closed `Mapping[str, JsonValue]` already
validated by its named wire schema; implementations may use a concrete dict
internally but may not add observable fields.

```python
@dataclass(frozen=True)
class VerifiedCaseProjection:
    case: JsonObject
    persona: JsonObject
    intent: JsonObject
    turn_policy: JsonObject

@dataclass(frozen=True)
class VerifiedCaseFactoryInput:
    manifest_file_hash: str
    case_candidate_file_hash: str
    input_manifest_hash: str
    intelligence_manifest_hash: str
    cases: tuple[VerifiedCaseProjection, ...]

@dataclass(frozen=True)
class TargetSourceIdentity:
    source_commit: str
    source_tree_hash: str
    adapter_file_hash: str

@dataclass(frozen=True)
class SimulatorResponse:
    status: str
    request_bytes: bytes | None
    response_bytes: bytes | None
    next_user_content: str | None
    consumed_observation_hash: str | None
    proposed_stop: bool | None
    stop_reason: str | None
    input_tokens: int
    output_tokens: int
    provider_http_exchange_count: int
    provider_reported_cost_usd: str | None
    reason_code: str | None

@dataclass(frozen=True)
class TargetLaunch:
    episode_id: str
    case_id: str
    target_config: JsonObject
    world: JsonObject
    world_hash: str
    source_identity: TargetSourceIdentity
    environment: Mapping[str, str]

@dataclass(frozen=True)
class AdaptiveRunResult:
    outcome: str
    reason_code: str | None
    exit_code: int
    manifest_path: Path
    attempted_episode_count: int
    valid_episode_count: int
    effective_trajectory_count: int
    simulator_http_exchange_count: int
    target_http_exchange_count: int
    all_http_exchange_count: int
    reserved_cost_usd: str
    actual_cost_usd: str | None
```

Each `VerifiedCaseProjection` object is the exact already-validated LABS-04
record from `case_candidates.jsonl` plus its resolved exact persona, intent,
and turn-policy records. Their shapes remain the existing LABS-04 closed
schemas; the injected loader may supply newly authored synthetic objects that
satisfy those schemas, but must state the frozen external file hashes above.
The controller revalidates top-level artifact kinds/schema/fidelity/proposal
state, case-to-asset IDs, input/intelligence hashes, selected case IDs/order,
and the scenario/turn-policy fields it projects. It does not trust loader
ordering or references merely because the dataclass was constructed.

`source_tree_hash` and `adapter_file_hash` are digest strings. Production
derives the tree identity from the pinned Git commit and the adapter digest
from exact bytes; the injected verifier supplies them deterministically.

Protocols are exactly:

```python
class CaseFactoryInputLoader(Protocol):
    def load(self, manifest: Path) -> VerifiedCaseFactoryInput: ...

class TargetSourceVerifier(Protocol):
    def verify(self, target_config: JsonObject) -> TargetSourceIdentity: ...

class SimulatorTransport(Protocol):
    def complete(self, request: JsonObject) -> SimulatorResponse: ...

class TargetSession(Protocol):
    def exchange(self, request: JsonObject) -> JsonObject: ...
    def terminate(self) -> None: ...

class TargetProcessFactory(Protocol):
    def start(self, launch: TargetLaunch) -> TargetSession: ...

class Clock(Protocol):
    def monotonic_ns(self) -> int: ...

class ArtifactPublisher(Protocol):
    def publish(self, output_path: Path, artifacts: Mapping[str, bytes]) -> None: ...
```

Production also exposes `JsonlTargetProcessFactory()` implementing
`TargetProcessFactory`. Its zero-argument constructor creates no subprocess.
`start(launch)` uses only the closed `TargetLaunch`, starts the configured argv
with `shell=False`, configured cwd and allowlisted environment, then returns a
session that owns raw UTF-8 JSONL framing, the 1,048,576-byte line ceiling,
strict duplicate-key parsing, exact one-response-per-request behavior, stderr
monitoring, timeout, exit status, and TERM/bounded-KILL cleanup from section 4.
It performs no HRAI import and no provider call itself; therefore acceptance
tests may use it with a newly authored local fake executable while injecting
the verified case loader and source verifier.

Raw target-process failures raise only:

```python
class TargetProtocolFailure(Exception):
    reason_code: str
```

The constructor is `TargetProtocolFailure(reason_code: str)`. Allowed reasons
are `TARGET_PROTOCOL_ERROR | TARGET_STDERR | TARGET_TIMEOUT`; process bytes,
stderr, argv, cwd, exit status, and exception text are not exposed. The runner
maps this safe category into the existing typed episode/partial behavior.

`TargetSession.exchange` requests and returns only the exact hello/turn/close
JSON objects in section 4. `terminate` is called exactly once in a `finally`
path for every successfully started session, including failure/interruption.
`ArtifactPublisher.publish` receives exactly the eight final relative artifact
names and their complete bytes; the default owns staging/fsync/no-replace.

Prepublication refusal raises only:

```python
class AdaptiveRunFailure(Exception):
    reason_code: str
    exit_code: int
```

The constructor is `AdaptiveRunFailure(reason_code: str, exit_code: int)`.
It exposes no unsafe exception detail. After any simulator/target egress, the
runner returns an `AdaptiveRunResult` pointing to safely published partial
custody whenever publication succeeds. Publication failure raises the closed
output failure. Test doubles may raise `OSError`, `TimeoutError`,
`KeyboardInterrupt`, or return a closed failure response; production maps only
those observable categories to the frozen reasons and never serializes the
exception text.

## 2. Owner review artifact

The exact closed shape is:

```json
{
  "artifact_kind": "labs04_usefulness_ruling",
  "schema_version": 1,
  "rubric_version": "LABS04_USEFULNESS_V1",
  "case_factory_manifest_file_hash": "sha256:<digest>",
  "case_candidate_file_hash": "sha256:<digest>",
  "reviewer": "Akarsh",
  "review_date": "2026-08-02",
  "review_state": "PASSED",
  "cases": []
}
```

There are exactly five case records sorted by `case_id`. Each has exactly
`case_id`, `would_run`, `opening_understandable`, `adaptive_multi_turn`,
`judgeable_expected_behavior`, `materially_distinct`, `support_sufficient`,
and `depends_on_hidden_or_fabricated_fact`. All first six booleans must be true
and the last false for every selected case. `review_state` must be `PASSED`.

## 3. Runner config

The exact closed shape is:

```json
{
  "artifact_kind": "adaptive_runner_config",
  "schema_version": 1,
  "protocol_version": "LABS05_WIRE_V1",
  "privacy_class": "SYNTHETIC",
  "selected_case_ids": [
    "case-b2b9570f6e763ca0",
    "case-62ca79446e3a22d5",
    "case-9a0d8a895afcd860"
  ],
  "simulator": {
    "provider_kind": "MICROSOFT_FOUNDRY_FIREWORKS",
    "endpoint": "https://<host>/openai/v1",
    "allowed_host": "<same lowercase DNS host>",
    "api_key_env": "<safe env name>",
    "deployment": "FW-GLM-5.2",
    "model_name": "FW-GLM-5.2",
    "model_version": "1",
    "seed": 2026080205,
    "prompt_version": "LABS05_ADAPTIVE_USER_V1",
    "timeout_seconds": 180
  },
  "target": {
    "protocol": "HRAI_RECRUITER_CHAT_REACT_JSONL_V1",
    "source_commit": "728f6c5058efe40a16e2aecc9b528b3353f4df4f",
    "agent_model": "qwen.qwen3-235b-a22b-2507-v1:0",
    "prompt_version": "candidate-screening-v3-decision-followthrough",
    "fallback_model": null,
    "argv": ["<absolute executable>", "<absolute adapter script>"],
    "cwd": "<absolute pinned HRAI checkout>",
    "env_names": ["AWS_PROFILE", "AWS_REGION"],
    "timeout_seconds": 180
  },
  "world": {
    "kind": "HRAI_SYNTHETIC_READ_ONLY_V1",
    "reset_policy": "FRESH_PER_EPISODE",
    "persistent_memory": "DISABLED",
    "allowed_tools": [
      "get_candidate_by_email",
      "get_existing_evaluation",
      "get_hiring_rubric",
      "query_database"
    ]
  },
  "budget": {
    "episode_count": 3,
    "role_turns_per_episode": 6,
    "simulator_http_exchanges": 6,
    "target_http_exchanges": 36,
    "all_http_exchanges": 42,
    "target_http_exchanges_per_turn": 4,
    "target_tool_calls_per_episode": 12,
    "simulator_input_tokens_per_exchange": 131072,
    "simulator_output_tokens_per_exchange": 4096,
    "target_input_tokens_per_episode": 393216,
    "target_output_tokens_per_episode": 24576,
    "episode_timeout_seconds": 180,
    "run_timeout_seconds": 600,
    "max_usd": "23.000000",
    "simulator_reservation_usd_per_exchange": "1.000000",
    "target_reservation_usd_per_turn": "1.888888"
  }
}
```

The literal identities, case order, seed, prompt versions, privacy, world,
tools, and numeric ceilings above are required. `target.argv` has 2..8 strings,
each 1..4,096 bytes, total at most 16,384 bytes; element 0 and the adapter path
are absolute regular nonsymlink executable/readable files. `shell=False` is
mandatory. `cwd` must be a real nonsymlink directory whose Git HEAD equals the
source commit; dirty tracked source changes refuse. Untracked HRAI files are
not read except runtime-owned temporary state explicitly under a fresh private
directory supplied by the adapter.

Only named environment variables are forwarded from the parent, plus a minimal
fixed locale/PATH required to start the executable. Secret values are never
hashed, logged, or written. Missing env values refuse before subprocess start.
`fallback_model` is JSON null; any non-null value is invalid. Endpoint permits
HTTPS, no userinfo/query/fragment, exact allowed host, and path `/openai/v1`.

The sum of six simulator reservations and nine target-turn reservations is
USD `22.999992`, within `23.000000`. Reservations are not actual cost.

## 4. Subprocess JSONL protocol

The process uses UTF-8 JSONL over stdin/stdout. Stderr must remain empty. Each
request is fully written and flushed before reading exactly one response line.
Maximum line size is 1,048,576 bytes. EOF, blank line, timeout, invalid UTF-8,
duplicate key, unknown field, extra response line, or nonzero exit is
`TARGET_PROTOCOL_ERROR` unless a more specific closed status was already
returned. Triana terminates the process at episode end; timeout escalation is
TERM then bounded KILL, both preserved as safe status only.

### 4.1 Hello

Request:

```json
{
  "kind": "hello",
  "protocol": "HRAI_RECRUITER_CHAT_REACT_JSONL_V1",
  "episode_id": "episode-<digest-prefix>",
  "case_id": "case-...",
  "source_commit": "728f6c5058efe40a16e2aecc9b528b3353f4df4f",
  "agent_model": "qwen.qwen3-235b-a22b-2507-v1:0",
  "prompt_version": "candidate-screening-v3-decision-followthrough",
  "world_kind": "HRAI_SYNTHETIC_READ_ONLY_V1",
  "world_hash": "sha256:<digest>",
  "allowed_tools": ["get_candidate_by_email", "get_existing_evaluation", "get_hiring_rubric", "query_database"]
}
```

Response:

```json
{
  "kind": "ready",
  "protocol": "HRAI_RECRUITER_CHAT_REACT_JSONL_V1",
  "episode_id": "episode-...",
  "case_id": "case-...",
  "source_commit": "728f6c5058efe40a16e2aecc9b528b3353f4df4f",
  "agent_model": "qwen.qwen3-235b-a22b-2507-v1:0",
  "prompt_version": "candidate-screening-v3-decision-followthrough",
  "world_hash": "sha256:<digest>",
  "memory_state": "EMPTY",
  "fallback_enabled": false
}
```

Every identity must match exactly. Handshake accounts for no provider HTTP
exchange or tool call.

### 4.2 Turn

There are exactly three normal turn requests with `turn_index` 1, 2, 3.

```json
{
  "kind": "turn",
  "episode_id": "episode-...",
  "turn_index": 1,
  "user_turn_id": "turn-...",
  "content": "bounded user text",
  "remaining_budget": {
    "http_exchanges": 4,
    "input_tokens": 393216,
    "output_tokens": 24576,
    "tool_calls": 12,
    "timeout_ms": 180000
  }
}
```

Response:

```json
{
  "kind": "turn_result",
  "episode_id": "episode-...",
  "turn_index": 1,
  "status": "SUCCEEDED",
  "assistant_content": "bounded assistant text",
  "tool_events": [],
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0,
    "provider_http_exchange_count": 0,
    "provider_reported_cost_usd": null
  },
  "reason_code": null
}
```

`status` is `SUCCEEDED | REFUSED | TOOL_REFUSED | PROVIDER_FAILED |
BUDGET_EXHAUSTED | TIMED_OUT | INTERNAL_FAILED`. Success requires nonempty
assistant content and null reason. Failure requires one matching closed reason
and permits empty content. A provider-reported cost is null or a six-place
nonnegative decimal string. The adapter may not report usage beyond the
request's remaining budget. Triana recomputes cumulative arithmetic.

A tool event has exactly:

```json
{
  "tool_event_id": "tool-event-...",
  "ordinal": 1,
  "name": "get_candidate_by_email",
  "arguments": {},
  "result": {},
  "status": "SUCCEEDED",
  "reason_code": null,
  "cached": false
}
```

Arguments/result are bounded canonical JSON values with maximum depth 8,
maximum 100 object keys or list elements per container, and maximum canonical
bytes 65,536 per event. Tool names are exactly the four allowlisted names.
Status is `SUCCEEDED | REFUSED | FAILED`; reason is null only on success.
Ordinals are unique ascending from one within the episode. `cached` means an
episode-local exact repeat and never a cross-episode cache.

### 4.3 Close

After turn 3 or earlier typed termination, Triana writes:

```json
{"kind":"close","episode_id":"episode-...","last_turn_index":3}
```

The response is:

```json
{
  "kind": "closed",
  "episode_id": "episode-...",
  "last_turn_index": 3,
  "memory_state": "DISCARDED",
  "provider_http_exchange_count": 0,
  "tool_call_count": 0
}
```

The counts are cumulative and must equal the sum of turn results. A mismatch is
protocol failure and cannot validate the episode.

## 5. Simulator request/response

The provider-bound request is a strict OpenAI-compatible chat completion with
one system instruction version `LABS05_ADAPTIVE_USER_V1` and one canonical
JSON user payload. It uses the pinned model/deployment, seed, temperature 0,
one choice, no tools, and strict JSON Schema response. Redirects and retries
are disabled. Benign provider envelope extras are ignored only after secret
scan, hashing, and validation of required fields.

The canonical payload has exactly:

```json
{
  "protocol_version": "LABS05_WIRE_V1",
  "episode_id": "episode-...",
  "case": {},
  "turn_index": 2,
  "transcript": [],
  "latest_observation": {
    "assistant_turn_id": "turn-...",
    "assistant_content": "...",
    "tool_events": [],
    "observation_hash": "sha256:<digest>"
  },
  "remaining_turns": 1
}
```

The response content has exactly:

```json
{
  "next_user_content": "bounded nonempty text",
  "consumed_observation_hash": "sha256:<digest>",
  "proposed_stop": false,
  "stop_reason": null
}
```

`consumed_observation_hash` must equal the request observation hash. If
`proposed_stop` is true, `stop_reason` is a nonempty text reason and the
controller accepts it only when it matches a case termination condition under
the deterministic closed projection; otherwise it records
`SIMULATOR_INVALID_RESPONSE`. The simulator cannot set final run status.

## 6. Portable records

Every record contains `artifact_kind`, `schema_version: 1`,
`protocol_version: LABS05_WIRE_V1`, `case_factory_manifest_hash`,
`owner_review_hash`, `config_hash`, and lineage sufficient to reproduce its
identity. Content-derived record IDs use the first 16 hexadecimal digest
characters with the appropriate prefix.

`episode_attempts.jsonl` has one record per selected slot with episode/attempt
ID, slot, case ID, status, termination reason, completed role-turn count,
simulator/target HTTP and token totals, target tool count, reserved cost,
actual cost nullable, trajectory fingerprint nullable, effective flag, and
sorted gap codes. All attempted slots remain.

`transcripts.jsonl` has one record per observed role turn with episode ID,
ordinal 1..6, role `USER | ASSISTANT`, content, source `CASE_OPENING |
SIMULATOR | TARGET`, source attempt ID, observation/consumed-observation hash
where conditional, and lineage. Missing future turns are absent, never empty
synthetic placeholders.

`target_tool_events.jsonl` projects the subprocess tool event plus episode ID,
assistant turn ordinal, target protocol/source/model/prompt/world hashes, and
event identity. `provider_ledger.jsonl` has one row per attempted simulator
exchange or target turn, including zero-egress refusals, with lane, episode,
turn, attempt, status, request/response hash conditional, HTTP count, tokens,
reservation, actual cost nullable, and reason.

`gaps.jsonl` contains episode ID nullable, turn ordinal nullable, one closed
reason code, safe detail code nullable, and originating attempt ID nullable. It
contains no free-form exception or rejected payload.

`trajectory_clusters.json` records exact algorithm
`LABS05_TRAJECTORY_EXACT_V1`, near algorithm
`LABS05_TRAJECTORY_JACCARD_TOOLS_V1`, threshold `0.85`, raw/valid/effective N,
exact and near edges, components, and selected effective episode IDs.

`human_adaptation_review.json` is generated `PENDING`; it contains rubric
`LABS05_ADAPTATION_V1`, manifest hash, and one item for U2/U3 of every effective
episode with episode/case/turn IDs, prior target observation, generated user
turn, null `materially_reacts`, and null notes. No software fills the ruling.

`manifest.json` contains outcome, privacy, producing component/version,
protocol and all input/lineage hashes, selected/attempted/valid/effective/
duplicate/gap counts, all HTTP/token/tool/reservation/actual-cost totals,
human-review state, and exact hashes for the seven other artifacts.

## 7. Exit codes and terminal event

```text
0   COMPLETED
2   CLI_USAGE_ERROR, INPUT_READ_FAILED, OUTPUT_ALREADY_EXISTS,
    OUTPUT_PARENT_MISSING, CONFIG_INVALID
4   MANIFEST_INVALID, REVIEW_INVALID, REVIEW_NOT_ACCEPTED,
    UNSUPPORTED_PRIVACY_CLASS, CASE_INTEGRITY_FAILED,
    TARGET_SOURCE_MISMATCH, SIMULATOR_AUTHORIZATION_REFUSED,
    SIMULATOR_ENDPOINT_REFUSED
7   OUTPUT_WRITE_FAILED, OUTPUT_CLEANUP_FAILED
8   TARGET_PROTOCOL_ERROR, TARGET_STDERR, TARGET_TOOL_REFUSED,
    TARGET_PROVIDER_ERROR, TARGET_TIMEOUT, SIMULATOR_PROVIDER_ERROR,
    SIMULATOR_INVALID_RESPONSE, ADAPTATION_BINDING_MISMATCH
9   BUDGET_EXHAUSTED, EPISODE_TIMEOUT, RUN_TIMEOUT
10  COMPLETED_WITH_GAPS
70  INTERNAL_INVARIANT_FAILED
130 INTERRUPTED
```

After egress, safe partial evidence takes custody and exits 10 when publication
succeeds. Fewer than three effective trajectories always adds
`INSUFFICIENT_DISTINCT_TRAJECTORIES`. The CLI emits exactly one compact JSON
terminal event to stderr with service/version, command, outcome, reason,
duration, attempted/valid/effective counts, simulator/target/all HTTP counts,
and reserved/actual cost when complete. It exposes no path, case/episode/turn
ID, tool name, endpoint, prompt, response, exception, or credential. Success
also emits one safe stdout receipt naming only outcome, counts, and the
user-supplied output-relative manifest path.

## 8. Publication and interruption

Artifacts are constructed in a private sibling staging directory, fsynced,
and atomically published with native no-replace behavior. Existing or raced
destinations refuse; symlink substitution refuses. Unsupported no-replace
platforms fail closed. A pre-egress interruption removes staging and creates
no output. A post-egress interruption publishes safe partial custody when
possible, records `INTERRUPTED`, never invents missing turns, and exits 130.

## 9. Deferred memory and evaluation

No config field or artifact exists for persistent/global memory, a judge,
baseline/candidate comparison, real data, UI, SDK/plugin registration, prompt
optimization, or broad evaluation. Unknown fields attempting to enable any of
them are `CONFIG_INVALID`.
