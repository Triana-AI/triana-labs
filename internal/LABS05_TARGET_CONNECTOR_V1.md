# LABS-05 Target Connector V1

Date frozen: 2026-08-02

Status: **owner-approved, locally implemented, and verification GREEN**

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md` ->
`internal/SLICE_PACKET.md`.

This contract supersedes only the HRAI-owned-subprocess, four-tool-world, and
target-internal-accounting portions of `internal/LABS05_WIRE_CONTRACT.md`.
The accepted three-case panel, U1/A1/U2/A2/U3/A3 episode shape, simulator,
deterministic identity, latest-observation binding, termination, custody,
trajectory dedupe, atomic publication, synthetic-only privacy, and human
adaptation review remain unchanged except where this document says so.

Closure evidence on 2026-08-03: 131 frozen connector acceptance tests and 539
repository-wide tests pass the complete versioned gate. One owner-authorized
real HRAI smoke reached `POST /sessions` but not chat because configured
Postgres timed out and configured Redis DNS failed. That attempt is typed
failed target-infrastructure evidence, not adaptation passage, and authorizes
no rerun.

## 1. Product boundary

Triana runs the adaptive outer conversation. The target is an opaque existing
conversational agent. The target owns its system prompt, model/provider,
tools, tool execution, internal orchestration, and target-side memory. Triana
does not recreate, replace, inject, or restrict those internals.

Triana owns:

- episode, turn, request, observation, and trajectory identity;
- the ordered adaptive loop and latest-observation binding;
- target-session lifecycle requested through the connector;
- outer request, deadline, turn, and conservative reservation budgets;
- exact Triana-to-target HTTP or executable-exchange accounting;
- normalization, custody, typed gaps, termination, and publication;
- no retry, redirect, connector fallback, target fallback, or silent repair;
- synthetic-only provider-bound input validation and secret-safe artifacts.

The connector is an execution boundary, not a generic agent SDK. LABS-05
ships exactly two connector kinds: restricted HTTP/JSON and strict local JSONL
executable. HRAI is the first HTTP configuration, not the protocol. A2A,
Braintrust, DeepEval, LangSmith, Promptfoo, MCP, provider-specific SDKs, and
additional connector kinds remain deferred.

## 2. Internal connector protocol

Production and tests share the following conceptual protocol; concrete frozen
dataclasses and method names may extend the existing `TargetLaunch`,
`TargetSession`, and `TargetProcessFactory` names only as required by the
independent acceptance author:

```python
open_episode(episode_identity) -> target_session
send_turn(target_session, user_turn, remaining_budget) -> target_observation
close_episode(target_session) -> close_result
```

`target_observation` contains exactly the normalized fields Triana can know:

```text
assistant_content                    required
target_status                        required closed code
termination_signal                   optional
tool_events                          optional ordered list
reported_internal_usage              optional
response_provenance                  required
```

Absence is not zero. Missing target tool telemetry creates
`TARGET_TOOL_TRACE_UNAVAILABLE`. Missing target-internal HTTP/model/token/cost
telemetry creates `TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE`. Either gap remains
visible and weakens the corresponding claim; neither can be normalized to an
empty successful observation. A non-empty assistant response may still support
an adaptive transcript when optional telemetry is unavailable.

## 3. Restricted HTTP/JSON connector

The config discriminator is `connector_kind: "HTTP_JSON_V1"`. The object is
closed and contains:

```text
connector_id                         SafeId
base_url                             exact http://localhost/127.0.0.1 or https URL
allowed_host                         exact parsed hostname
timeout_seconds                      strict integer 1..180
auth                                 NONE or one environment-backed header
session                              REMOTE_SESSION or STATELESS_TRANSCRIPT
turn                                 request and response mappings
target_identity                      declared agent/protocol/version fields
data_class                           SYNTHETIC_LOCAL_TARGET
state_isolation                      declared closed state
```

The base URL has no userinfo, query, or fragment. Plain HTTP is allowed only
for `localhost`, `127.0.0.1`, or `::1`. HTTPS host matching is exact after
lowercase IDNA normalization. Authentication values come only from one named
environment variable and never enter config identity, logs, requests retained
as artifacts, or portable output. Redirects, cookies, proxies discovered from
ambient environment, and TLS downgrade are forbidden.

### 3.1 Restricted request construction

Each operation declares an uppercase method from `GET | POST | DELETE`, a
relative path template, and a closed constant JSON object. Triana may insert
only these typed values at configured RFC 6901 pointers:

```text
episode_id
case_id
session_id
user_turn
transcript
```

The supported placeholders are pointer assignments, not executable template
code. Unknown placeholders, overlapping assignment pointers, assignment over
a non-container, absolute operation URLs, path traversal, query strings, and
fragments are `CONFIG_INVALID`. `user_turn` is a string. `transcript` is an
ordered array of `{role, content}` objects and is required only for
`STATELESS_TRANSCRIPT`.

`REMOTE_SESSION` requires:

- one create operation before U1;
- a required response pointer yielding a non-empty string session ID;
- the session ID interpolated only into a declared path segment or request
  pointer for each turn;
- one close operation after termination, including partial termination.

The controller reserves create and close capacity together before opening a
remote session. A close failure creates `TARGET_SESSION_CLOSE_FAILED` and
invalidates reset/isolation evidence. It never triggers another close.

`STATELESS_TRANSCRIPT` forbids create/close operations and requires Triana to
send the complete current transcript on every turn. It claims no remote
session state.

### 3.2 Restricted response extraction

Every operation requires a 2xx response within its configured byte and time
limits. Turn responses are strict UTF-8 JSON objects with duplicate-key
rejection. The mapping contains:

```text
assistant_content_pointer            required string
target_status_pointer                 optional string
termination_pointer                   optional boolean
error_pointer                         optional null-or-string
tool_events                           optional mapping
internal_usage                        optional mapping
```

Tool-event mapping names a list pointer plus relative name, arguments, and
optional status pointers. Missing/invalid configured telemetry is
`TARGET_RESPONSE_INVALID`; an entirely absent optional mapping produces the
typed unavailable gap. Tool events preserve order and duplicates.

Internal-usage mappings may expose target-reported model/HTTP exchanges,
input/output tokens, and USD cost. Values are validated but explicitly labeled
`TARGET_REPORTED`; Triana does not claim they are independently observed.

Non-2xx, invalid JSON, excessive bytes, timeouts, configured error fields,
secret reflection, and mapping failures stop the episode with one typed gap.
The connector performs exactly one request per operation and never retries.

### 3.3 HRAI reference configuration

The first live configuration names existing HRAI commit
`728f6c5058efe40a16e2aecc9b528b3353f4df4f` and its FastAPI surface:

```text
POST   /sessions
POST   /sessions/{session_id}/chat
DELETE /sessions/{session_id}
```

Create uses the configured synthetic `client_id`; turn inserts `user_turn` at
`/message` and the same client at `/client_id`; create extracts `/session_id`;
turn extracts `/response` and maps `/tool_calls` using `/name` and `/args`.
HRAI's endpoint owns its real prompt, complete tools, model, provider, and
internal state. Triana supplies none of them. HRAI currently does not expose
target-internal model HTTP/token/cost accounting, so a live result must carry
`TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE` unless the endpoint contract changes.

The reference config is synthetic-only and localhost-only. It must not connect
Triana to production/customer data, and it does not assert that HRAI's internal
global memory is absent merely because a new session ID was created.

## 4. Strict executable connector

The config discriminator is `connector_kind: "EXECUTABLE_JSONL_V1"`. This is
the existing shell-free JSONL subprocess boundary generalized as a customer
bridge. The executable may call a target endpoint or local agent, but it must
not be an HRAI reconstruction shipped by Triana.

The process lifecycle remains one fresh process per episode, exact hello/ready,
one request/response per user turn, and exact close/closed framing. It receives
the accepted synthetic case projection, episode identity, turn, transcript,
and remaining outer budgets. It returns the normalized observation above.
Shell execution, stderr, extra output, duplicate keys, invalid UTF-8, partial
lines, timeout, source mutation after verification, and nonzero exit fail
closed. Triana does not retry or fall back to HTTP.

Executable identity closes over exact argv, cwd, executable/adapter content
hashes, protocol version, declared target identity, and environment-variable
names. Values remain secret and non-identity-bearing.

## 5. State and memory

Triana has only immutable accepted evidence and the current episode trajectory.
The adaptive simulator may read that episode trajectory. Triana persistent or
global learning memory remains absent.

Target state is explicitly separate:

- `STATELESS_TRANSCRIPT`: Triana replays the trajectory; no target session is
  assumed.
- `EPISODE_REMOTE_SESSION`: the target session is scoped by the returned
  session ID and close is attempted exactly once.
- `TARGET_GLOBAL_STATE_UNKNOWN`: the target exposes no verified reset for
  cross-session state.
- `TARGET_GLOBAL_STATE_RESETTABLE`: a separately declared reset operation is
  required; LABS-05 does not implement this variant.

For this checkpoint, HTTP remote sessions declare
`TARGET_GLOBAL_STATE_UNKNOWN` unless independently evidenced otherwise. This
produces `TARGET_STATE_ISOLATION_UNAVAILABLE` and forbids a reproducibility or
cross-episode independence claim. It does not prevent a diagnostic adaptive
conversation. No target state is promoted into Triana memory.

## 6. Budgets and accounting

The unchanged three complete episodes contain six simulator HTTP exchanges.
Target-connector accounting replaces the old assumed target-provider count:

```text
REMOTE_SESSION HTTP calls per complete episode     5 (create + 3 turn + close)
REMOTE_SESSION HTTP calls per complete run         15
STATELESS_TRANSCRIPT HTTP calls per complete run    9
simulator HTTP calls per complete run               6
maximum Triana-observed external HTTP calls         21
```

Executable connector exchanges are counted separately as logical connector
exchanges, not HTTP calls, unless the bridge reports internal HTTP telemetry.
`all_http_exchange_count` means only HTTP exchanges directly observed by
Triana. `target_reported_internal_http_exchange_count` is a separate optional
field and is never added to the observed count without an explicit artifact
field showing both values.

Before create/turn/simulator work, the controller reserves the full configured
unit. Remote-session creation additionally reserves one close call and its
deadline. Equality is funded. No new work begins after the applicable episode
or run deadline. Cleanup uses only its already reserved allowance.

The existing USD `23.000000` ceiling remains a conservative experiment
reservation, not observed target spend. Each simulator call and target turn
has a configured reservation. Target-internal actual cost remains null unless
reported. A black-box endpoint without internal budget telemetry carries
`TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED`; Triana must not claim the
endpoint's internal model/tool loops obey the outer reservation.

## 7. Identity, custody, and gaps

Episode identity replaces HRAI source/prompt/tool-world identity with:

```text
connector kind and protocol version
connector configuration hash with secrets absent
declared target identity
session/state-isolation policy
response mapping contract
synthetic data-class declaration
outer budget contract
```

Target-internal prompt/model/tool/memory identity is recorded only when the
target declares it. Unknown components are typed unknowns, never Triana-owned
defaults.

The existing eight publication files remain. `provider_ledger.jsonl` records
simulator requests, Triana-observed target HTTP requests or executable
exchanges, and separate target-reported internal usage. `target_tool_events`
may be empty only when the typed trace-unavailable gap exists.

New closed reasons are:

```text
TARGET_CONNECTOR_CONFIG_INVALID
TARGET_ENDPOINT_REFUSED
TARGET_HTTP_ERROR
TARGET_RESPONSE_INVALID
TARGET_SESSION_CREATE_FAILED
TARGET_SESSION_CLOSE_FAILED
TARGET_TOOL_TRACE_UNAVAILABLE
TARGET_INTERNAL_ACCOUNTING_UNAVAILABLE
TARGET_INTERNAL_BUDGET_ENFORCEMENT_UNVERIFIED
TARGET_STATE_ISOLATION_UNAVAILABLE
```

Configuration, authorization, unsafe endpoint, and malformed mapping failures
refuse before target egress. Runtime endpoint failures preserve completed
custody, stop the affected episode, and allow later already funded slots to
continue. No typed gap becomes a pass.

## 8. Acceptance and change budget

The independent acceptance author must preserve applicable existing episode,
adaptation, deadline, dedupe, custody, publication, privacy, and simulator
tests while replacing HRAI/four-tool assumptions. New tests prove:

- HRAI-shaped HTTP create/chat/delete against a local fake server;
- a second non-HRAI stateless transcript endpoint using different paths and
  response pointers;
- exact session continuity and exactly-once close after success and failure;
- no redirect, retry, proxy discovery, fallback, or unsafe host;
- strict request-pointer insertion and response-pointer extraction;
- tool/usage present, unavailable, malformed, and secret-reflection behavior;
- outer versus target-reported internal accounting never conflates;
- target-owned prompt/tools are never supplied by Triana;
- global-state and internal-budget uncertainty remain typed gaps;
- the executable bridge remains strict but contains no HRAI-specific world.

Orchestrator-owned additions/edits:

```text
internal/LABS05_TARGET_CONNECTOR_V1.md
internal/SLICE_PACKET.md
internal/LABS05_WIRE_CONTRACT.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
internal/LABS05_HANDOFF_2026-08-02.md
internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md
triana-labs/CHARTER.md
docs/ARCHITECTURE.md
docs/PROVENANCE.md
```

Test ownership remains:

```text
triana-labs/tests/adaptive_runner_acceptance/**
triana-labs/tests/adaptive_runner_fixtures/**
```

Production ownership becomes:

```text
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/adaptive_runner/**
triana-labs/examples/target_connectors/**
```

The old `triana-labs/examples/hrai_recruiter_chat_v1/**` target reconstruction
may be removed only after no production/test/package reference remains. No
dependency or lock change is allowed. Maximum production scope is 12 files and
3,200 changed nonblank/noncomment lines. `triana-core`, LABS-01 through
LABS-04 code/tests/artifacts, external HRAI, UI, judges, real-data support,
baseline/candidate comparison, persistent/global Triana memory, A2A, and broad
eval expansion remain untouched.

## 9. Research provenance

The design reimplements documented boundary patterns; no framework code is
copied. Braintrust and LangSmith use customer task/target functions, DeepEval
uses a customer model callback, and Promptfoo offers declarative HTTP plus
custom providers/session extraction. A2A is a later standards-compatible
adapter candidate. These references justify the interface shape but supply no
Triana implementation:

- https://www.braintrust.dev/docs/evaluate
- https://deepeval.com/docs/conversation-simulator
- https://docs.langchain.com/langsmith/define-target-function
- https://www.promptfoo.dev/docs/providers/http/
- https://www.promptfoo.dev/docs/providers/custom-api/
- https://a2a-protocol.org/v0.3.0/specification/
