# LABS-05 Adaptive Multi-Turn Runner slice packet

Date frozen: 2026-08-02

Status: **TARGET CONNECTOR V1 LOCAL GREEN; LIVE HRAI INFRASTRUCTURE GAP**

Slice ID: `LABS-05-ADAPTIVE-RUNNER-V1`

Canonical base: `1258b9c` on `codex/labs05-adaptive-runner`, descended from
local `main` at `ff8ca24`.

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`.

Normative wire: `internal/LABS05_TARGET_CONNECTOR_V1.md`, which supersedes the
target-specific portions of `internal/LABS05_WIRE_CONTRACT.md` while retaining
the accepted episode/simulator/artifact contract.

## 0. Owner-approved target-boundary supersession

After the local implementation and one diagnostic exposed the mismatch between
an external HRAI endpoint and Triana's reconstructed four-tool subprocess, the
owner approved the framework pattern used by Braintrust, DeepEval, LangSmith,
and Promptfoo: Triana owns the adaptive outer loop and a customer connector
invokes an opaque existing agent. LABS-05 now ships a restricted HTTP/JSON
connector plus the existing strict executable boundary generalized as a bridge.
HRAI becomes the first HTTP configuration; it is not reconstructed inside
Triana. The exact contract, accounting correction, memory/state distinction,
acceptance additions, and replacement change budget are frozen in
`internal/LABS05_TARGET_CONNECTOR_V1.md`.

The earlier local GREEN and 516-test evidence remain valid historical evidence
for the deterministic runner but do not close this superseding target boundary.
No live run occurs until independent RED, production GREEN, the full gate, and
separate owner authorization. Those local gates are now complete; the first
authorized real-endpoint smoke is recorded below and did not reach chat.

Restart evidence: `internal/LABS05_HANDOFF_2026-08-02.md` and
`internal/LABS04_CASE_REVIEW_2026-08-02.md`.

## 1. Product outcome

Prove that three owner-accepted LABS-04 cases can drive genuinely adaptive,
inspectable six-role-turn episodes against one explicitly named existing agent
protocol. Every later simulated-user turn must consume the immediately
preceding target response and normalized tool observations. Deterministic
Triana code owns case and episode identity, custody, budgets, termination,
trajectory fingerprints, duplicate arithmetic, lineage, and typed gaps.

The target is the HRAI Recruiter Chat ReAct protocol at HRAI commit
`728f6c5058efe40a16e2aecc9b528b3353f4df4f`, historical agent model
`qwen.qwen3-235b-a22b-2507-v1:0`, prompt version
`candidate-screening-v3-decision-followthrough`. It runs behind the exact
Triana-owned JSONL subprocess protocol in the normative wire. Model fallback
is disabled.

The historical `run_200` manifest labels its absent code tarball
`candidate-screening-v2-reliability`; that tarball is not present at the pinned
commit. LABS-05 therefore uses the prompt builder that is actually executable
and inspectable at that commit and does not claim the manifest-only v2 lineage.

This is not a generic agent SDK, product-wide runner, judge, memory system, or
release comparison. The target adapter uses a fresh synthetic read-only world
and empty episode state. It does not load or write HRAI persistent memory.

## 2. Entry evidence and selected cases

LABS-04 passed `LABS04_USEFULNESS_V1`: Akarsh answered yes to all six frozen
questions for all five cases and confirmed that none depends on a hidden or
fabricated fact. The reproducible ruling is
`internal/LABS04_USEFULNESS_V1.json`.

The exact LABS-04 input bundle has manifest-file SHA-256
`817000637daef25bff9bd95eee46a25976f575d1b2d5aa62965a6c6d9c5b6cb9`
and `case_candidates.jsonl` SHA-256
`06a3a2267f39041d98e08ef24466ffbc695e7833ebb16bd536f19f71c37ecbe4`.
No LABS-04 provider experiment may be rerun.

The smallest LABS-05 panel is exactly, in this order:

1. `case-b2b9570f6e763ca0` — wrong position/client-context recovery;
2. `case-62ca79446e3a22d5` — cross-client social-engineering refusal;
3. `case-9a0d8a895afcd860` — bounded status verification.

Selection is owner-accepted and mode-diverse, not a model judgment. Changing
case membership or order creates a new contract version.

## 3. Public invocation and outputs

The supported command added by this slice is:

```text
triana episodes run CASE_FACTORY_MANIFEST \
  --review LABS04_USEFULNESS_V1.json \
  --config ADAPTIVE_RUNNER_CONFIG.json \
  --out NEW_DIRECTORY
```

The input manifest resolves its declared sibling artifacts. The review and
config bytes are strict inputs. `--out` must not exist, its parent must be a
real directory, and publication is atomic/no-replace.

Completed or safely partial publication contains exactly:

```text
manifest.json
episode_attempts.jsonl
transcripts.jsonl
target_tool_events.jsonl
provider_ledger.jsonl
gaps.jsonl
trajectory_clusters.json
human_adaptation_review.json
```

All portable JSON is compact, sorted-key UTF-8 plus LF; JSONL is one such
object per physical line. The manifest hashes the other seven files. No path,
timestamp, random UUID, credential, raw endpoint, raw provider payload, raw
exception, or provider request ID enters portable identity.

## 4. Exact episode shape

There are exactly three episode slots, one for each selected case. Each target
subprocess is fresh. A complete episode has exactly six role turns:

```text
U1 accepted case opening
A1 target result
U2 simulator reaction to A1 plus A1 tool observations
A2 target result
U3 simulator reaction to A2 plus A2 tool observations
A3 target result
```

U1 is copied from the accepted case. U2 and U3 are separate simulator HTTP
exchanges. Their provider-bound request contains the accepted case projection,
the prior transcript, and only the immediately preceding normalized target
response/tool observations as an explicit `latest_observation` object. Static
prewritten U2/U3 inputs are invalid. A target or simulator failure preserves a
typed partial attempt and stops that episode; later funded episode slots may
continue.

Normal completion occurs after A3. Earlier termination is one of:

```text
CASE_STOP_CONDITION
TARGET_REFUSAL
TARGET_PROTOCOL_ERROR
TARGET_TOOL_REFUSED
TARGET_PROVIDER_ERROR
SIMULATOR_PROVIDER_ERROR
SIMULATOR_INVALID_RESPONSE
BUDGET_EXHAUSTED
TURN_LIMIT_REACHED
EPISODE_TIMEOUT
RUN_TIMEOUT
INTERRUPTED
```

No unrecognized terminal state becomes success.

## 5. Simulator and target authority

The simulator is the existing Microsoft Foundry Fireworks deployment
`FW-GLM-5.2`, version `1`, used through Triana's existing strict transport
style. It chooses only the next user turn and an optional proposed stop signal.
It has no tools, delegation, retrieval, filesystem, target invocation, score,
judge, acceptance, identity, budget, or memory-write authority. It has one
attempt per U2/U3 with no retry or fallback.

The target subprocess is invoked with an argv array and `shell=False`. It must
complete the exact handshake before any turn. It receives only the selected
synthetic case projection, deterministic episode identity, a per-turn user
message, and remaining numeric budgets. It returns one normalized assistant
response, normalized tool events, usage, HTTP exchange count, and a closed
status. Unknown fields, duplicate JSON keys, extra lines, stderr bytes,
out-of-order sequence, identity mismatch, or budget overrun fail closed.

The HRAI adapter constructs the existing Recruiter Chat ReAct prompt/model
protocol with empty prior memories and only these four read-only synthetic
tools:

```text
get_candidate_by_email
get_existing_evaluation
get_hiring_rubric
query_database
```

The tools resolve against the fresh case-specific in-memory synthetic world;
they do not connect to HRAI's database. The adapter does not register resume
parsing, LinkedIn, website, web search, memory, database write, evaluation
submission, shortlist/reject/email, skill loading, parallel gather, or ATS
sub-agent tools. Unknown or mutating tool selection is `TARGET_TOOL_REFUSED`.

## 6. Memory boundary

Four scopes are explicit:

- evidence memory: immutable accepted LABS-04 case projection, read-only;
- episode memory: the transcript and target thread state for one episode only;
- target persistent memory: empty and disabled; no load, retrieval, or write;
- persistent/global learning memory: deferred and absent.

Episode memory is published as evidence and then discarded as runtime state.
No episode can read another episode. No result is promoted to cross-run memory.
Future persistent memory requires a separate propose/human-promote/retrieve-
from-pinned-snapshot/supersede-or-revoke contract.

## 7. Deterministic identity and adaptation proof

`episode_id` is a versioned hash of the case-factory manifest hash, review
artifact hash, selected case ID, target protocol/source/model/prompt identity,
simulator provider/model/prompt identity, world fixture hash, reset policy,
budget contract, and slot index. It excludes attempts, paths, time, and secrets.

Every role turn and target tool event has an ID derived from `episode_id`,
ordinal, role/kind, and canonical content. Attempts are retained under distinct
attempt identities and never overwrite an earlier attempt.

Each simulator request records `latest_observation_hash`; the returned U2/U3
record repeats that hash as `consumed_observation_hash`. Mismatch is invalid.
Acceptance includes a deterministic causal fixture: two target A1 responses
with different normalized response/tool evidence under the same case must
produce two different scripted simulator U2 values, each bound to its own
observation hash. This proves the controller wires new evidence into turn
generation; it does not prove semantic realism.

## 8. Budgets and accounting

Exact whole-run ceilings:

```text
episode slots                         3
role turns per complete episode       6
simulator HTTP exchanges              6
target HTTP exchanges                 36
all provider HTTP exchanges           42
target tool calls per episode         12
simulator input tokens per exchange   131072
simulator output tokens per exchange  4096
target input tokens per episode       393216
target output tokens per episode      24576
wall time per episode                 180 seconds
whole-run wall time                   600 seconds
conservative whole-run USD            23.000000
```

The target adapter also enforces at most four target HTTP exchanges per target
turn. Counts include sent requests that end in refusal or transport error.
Zero-egress work counts zero. Cached work with no request counts zero. Actual
cost is `null` unless a provider reports it; conservative reservation never
becomes actual cost.

Before every simulator exchange and target turn, Triana reserves the complete
configured unit allowance. Exact equality is funded. If the next unit cannot
fit every relevant remaining cap, it is not started and the gap is
`BUDGET_EXHAUSTED`. No unfunded call, tool, or subprocess continuation occurs.

Automated tests use deterministic transports and subprocess fixtures only.
This packet authorizes no Microsoft Foundry or AWS Bedrock request and no USD
spend. A live three-episode run is a separate owner authorization after local
GREEN and exact current provider-price/credential reconciliation.

## 9. Trajectory duplicate arithmetic

Every attempted trajectory remains visible. The exact trajectory fingerprint
hashes normalized ordered role text, ordered normalized target tool names,
arguments, result summaries/statuses, and termination reason. Provider IDs,
usage, latency, and paths are excluded.

Near-text duplication uses Unicode casefolding, whitespace tokenization, and
token-set Jaccard over all user and assistant text at threshold `0.85`, but an
edge exists only when ordered normalized target tool-name/status sequences are
identical. Exact and near-text edges form connected components. Only the first
valid member in selected slot order increases effective N. Duplicate attempts
are evidence, never dropped or replaced.

## 10. Outcomes and passage

Run outcomes are `COMPLETED`, `COMPLETED_WITH_GAPS`, or `FAILED`. Exit 0 is a
complete locally valid bundle with three valid nonduplicate trajectories and
no gaps. Exit 10 is a safely published partial/duplicate/gap bundle. Refusal
exits follow the normative wire. Missing, invalid, refused, timed out,
interrupted, or duplicate episodes never become valid effective trajectories.

The local implementation may become `MECHANICALLY_GREEN` after the fake-boundary
test and packaging gate. LABS-05 product passage additionally requires:

1. one separately authorized live synthetic run of the exact three cases;
2. at least three complete, valid, inspectable, effective trajectories;
3. no privacy, fallback, accounting, identity, or custody violation;
4. Akarsh records `LABS05_ADAPTATION_V1` yes/no for U2 and U3 of each effective
   episode, confirming that each later user turn materially reacts to the
   latest target behavior.

Until all four hold, status is `IMPLEMENTED_AWAITING_LIVE_EXPERIMENT` or
`AWAITING_HUMAN_REVIEW`, never passed.

## 11. Closed gaps and refusal behavior

Pre-egress configuration/input/integrity failures publish no target directory.
After any provider or target egress, safe attempts may be published with a
closed gap. Relevant codes are:

```text
CLI_USAGE_ERROR
INPUT_READ_FAILED
OUTPUT_ALREADY_EXISTS
OUTPUT_PARENT_MISSING
CONFIG_INVALID
MANIFEST_INVALID
REVIEW_INVALID
REVIEW_NOT_ACCEPTED
UNSUPPORTED_PRIVACY_CLASS
CASE_INTEGRITY_FAILED
TARGET_SOURCE_MISMATCH
TARGET_PROTOCOL_ERROR
TARGET_STDERR
TARGET_TOOL_REFUSED
TARGET_PROVIDER_ERROR
TARGET_TIMEOUT
SIMULATOR_AUTHORIZATION_REFUSED
SIMULATOR_ENDPOINT_REFUSED
SIMULATOR_PROVIDER_ERROR
SIMULATOR_INVALID_RESPONSE
ADAPTATION_BINDING_MISMATCH
BUDGET_EXHAUSTED
EPISODE_TIMEOUT
RUN_TIMEOUT
INTERRUPTED
DUPLICATE_TRAJECTORY
INSUFFICIENT_DISTINCT_TRAJECTORIES
OUTPUT_WRITE_FAILED
OUTPUT_CLEANUP_FAILED
INTERNAL_INVARIANT_FAILED
```

There is no retry, fallback model/provider/target, default case, default user
turn, skipped slot, silent repair, rerun-to-green, or persistent-memory lookup.

## 12. Independent acceptance contract

Target Connector V1 initial superseding freeze: the independent author retained the
applicable outer-loop suite, replaced HRAI/four-tool assumptions, and added a
real localhost HTTP fixture plus a target-neutral executable bridge. The nine
owned Python files contain 3,071 physical lines and collect 123 tests. Against
the historical HRAI-specific production candidate they produce 108 expected
behavioral failures and 15 control passes, with zero collection/setup errors
and zero skips. Codex independently reproduced those exact counts with
localhost socket permission, plus GREEN Ruff check/format and diff check.

The sorted concatenated Python content SHA-256 is
`574bae8a507d364766354e9172359174d62481ccf5699384c4e78f2de898e507`.
The SHA-256 of the sorted per-file `shasum -a 256` stream is
`1fa162bb9068ea15fa59289871b81a973a09017771c9bded5a732f65f01b8042`.
Any test-owned byte change invalidates this freeze and returns the suite to the
independent author. Production may now change only the Target Connector V1
production-owned paths.

Post-candidate superseding freeze: Codex's source/lifecycle audit found an
unopened-session close defect, loose optional target-identity validation, and
an unused legacy four-tool literal. The independent author preserved all prior
123 cases and added seven checks. The final nine owned Python files contain
3,200 physical lines and collect 130 tests. Against the first connector
candidate, 124 pass and exactly six are expected RED: two create-failure
lifecycle cases, one legacy-source case, and three optional-identity cases.
The failed-chat plus successful-close accounting regression is already GREEN
and proves exact first-episode/whole-run observed counts without a spurious
protocol gap. Codex independently reproduced the six-failure RED shape and
the hashes below.

The final sorted concatenated Python content SHA-256 is
`b9f0f1415dfd8e6d0b4f8c9f88d9200ab5a3d9ebe4bb3c5858dae87528802e09`.
The final sorted per-file hash-stream SHA-256 is
`67ea8a94ac2f1edd1f4533de8e2db6eb5b4f654d3456f101f6c240adfd7a6a46`.
These hashes supersede the initial Target Connector V1 test freeze. Production
is reauthorized only for the six isolated defects.

The owner-authorized real HRAI smoke exposed one further response-ordering
defect: a non-JSON HTTP 500 from session creation was classified as an invalid
response before the create operation could own its typed failure. The
independent author added one exact regression. The final nine test-owned Python
files contain 3,216 physical lines and collect 131 tests. Their sorted
concatenated content SHA-256 is
`ef3f7fa3abb574df0113efa9505fa5e89de1b9964fd7b286fe608bb51fb51efe`;
their sorted per-file hash-stream SHA-256 is
`f4699df16b456eab327e445509e98d4cc7bb237727263ebfd858da9c13ee6844`.
Codex independently reproduced exactly one RED, the implementation author
changed only HTTP response ordering, and Codex independently reproduced 131
GREEN tests before the 539-test complete gate. These hashes supersede every
earlier Target Connector V1 freeze.

The independent test author derives assertions from this packet and
`internal/LABS05_WIRE_CONTRACT.md`, never from production schemas or output.
At minimum tests prove:

- strict manifest/review/config acceptance and tamper/refusal before egress;
- exact three-case selection and stable identity across input reorder/fresh
  process, with identity change on every material lineage/config change;
- complete U1/A1/U2/A2/U3/A3 execution and latest-observation binding;
- causal branching under changed target observations;
- subprocess handshake, sequence, closed fields, stderr, crash, timeout,
  malformed JSON, extra line, tool refusal, and no-fallback behavior;
- exact fresh-world reset and no cross-episode/persistent memory;
- per-unit and aggregate HTTP/token/tool/USD/time refusal with no unfunded call;
- logical turn versus target/simulator HTTP accounting;
- partial custody after middle-slot failure while later funded slots continue;
- exact/near trajectory duplicate clustering and effective N;
- interruption, atomic no-replace publication, safe cleanup, deterministic
  bytes, source/wheel parity, and redacted one-event terminal logs;
- no network or real HRAI repository is required by the automated suite;
- all 408 historical tests and five canonical Observer hashes remain unchanged.

Valid RED means collection succeeds and failures arise only because the new
`episodes run` behavior/package is absent. Import/setup failures are invalid.

The independent author first completed the 42-case contract against authority
head `baa0fe3`. After the first production candidate, Codex found concrete
prompt-lineage, accounting, validation, timeout, privacy, adapter-world, and
pre-execution budget defects. The same independent author added only
contract-derived regressions and corrected the prompt expectation to the
canonical executable v3 identity. Codex read the new assertions and fixtures
and independently reproduced the final post-candidate RED after a second
behavioral audit:

```text
108 tests collected
0 failures
108 passes
0 collection errors
0 skips
Ruff check GREEN
Ruff format check GREEN
```

The final candidate repairs both post-target deadline boundaries: no later
simulator egress occurs after A1 or A2 crosses the episode deadline, completed
target custody is preserved, and later funded slots may continue. All
previously frozen tests remain present. The final suite covers
behavioral world fidelity, failure tool custody, input/source substitution,
strict transport normalization, verified-cwd imports, and partial-line timeout.
The tracked-source race uses a regular disposable executable and proves an
unmodified control handshake before mutation. The eight test-owned Python
files contain 2,792 physical lines. Their
sorted concatenated content SHA-256 is
`e3eb48819cc0bd098a0ed6b270317d964512f29181a56f391cad30347377f196`.
The SHA-256 of the sorted per-file `shasum -a 256` stream is
`347bf5d65b743e40291ba8f526ef34ccac06ab9368fd3593bb4cce16be3eab27`.
The raw fake-target file SHA-256 is
`dae9c31328f83c078969c68210cf4650510471bf5e78ee7ffb6e10d59c370dce`.
Any change under either test-owned path invalidates this freeze and stops
production until independently re-reviewed and re-hashed.

The final four-line import relocation changes no assertion: it binds four
test helpers during local conftest collection instead of importing ambiguous
bare `conftest` names at test runtime. Codex independently reproduced 108/108
focused passes and 516/516 full-suite passes after the correction.

After a production candidate passes the frozen suite, the independent test
author attacks this additional orchestrator-declared matrix before exit:

1. near-text paraphrases with identical ordered tool name/status sequences
   cluster, while identical text with a different tool status remains distinct;
2. a target `closed` cumulative HTTP/tool count mismatch invalidates the episode;
3. an exact configured secret returned in assistant/tool or ignored target
   fields is never retained or rendered;
4. a destination inode/symlink raced immediately before publication cannot be
   replaced or followed;
5. a target argv/adapter/cwd identity changed after source verification refuses
   before child execution;
6. zero-egress and post-egress target failures retain distinct ledger counts
   and never infer actual cost.

These attacks produced the independently frozen regressions above after Codex
reproduced real candidate violations. They do not weaken the original 42 cases
or change acceptance meaning.

## 13. Roles and change budget

Exactly two worker agents plus Codex orchestrator execute serially.

Orchestrator-owned paths:

```text
internal/SLICE_PACKET.md
internal/LABS05_WIRE_CONTRACT.md
internal/LABS04_USEFULNESS_V1.json
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
internal/LABS05_HANDOFF_2026-08-02.md
internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md
triana-labs/CHARTER.md
docs/ARCHITECTURE.md
docs/PROVENANCE.md
triana-labs/scripts/verify.sh
```

Independent test-author-owned paths:

```text
triana-labs/tests/adaptive_runner_acceptance/**
triana-labs/tests/adaptive_runner_fixtures/**
```

Implementation-author-owned paths after RED freeze:

```text
triana-labs/src/triana_labs/cli.py
triana-labs/src/triana_labs/adaptive_runner/**
triana-labs/examples/hrai_recruiter_chat_v1/**
```

No dependency may be added. Maximum new production files: 10. Maximum new
production nonblank/noncomment lines: 2,500. The HRAI adapter must remain one
target-specific example, not a generic SDK. Any need for a dependency, schema
expansion, different target/model/provider, real DB, provider run, or edit
outside this budget stops the worker and returns to Codex.

Explicitly untouched:

```text
triana-core/**
all LABS-01/02/03/04 production, tests, fixtures, schemas, prompts, and artifacts
pyproject.toml
uv.lock
raw HRAI or provider artifacts
HRAI, Agentagon, Kairos, Kairos-AI, Blitz repositories
UI, judges, persistent/global memory, real data, baseline/candidate diff,
generic SDKs, broad evaluation, hosted ingestion, OTel, release policy
the three unrelated untracked SPC/research documents
```

## 14. Exact role commands

Test author runs:

```text
cd triana-labs
uv run pytest -q tests/adaptive_runner_acceptance
uv run ruff check tests/adaptive_runner_acceptance tests/adaptive_runner_fixtures
uv run ruff format --check tests/adaptive_runner_acceptance tests/adaptive_runner_fixtures
```

Codex reproduces RED, freezes sorted content and per-file hash-list SHA-256,
then authorizes production. Implementation author runs the frozen acceptance
suite plus focused historical CLI tests. Final Codex gate is:

```text
cd triana-labs
./scripts/verify.sh
git diff --check
```

The verifier must cover all tests, Ruff, strict mypy, frozen test hashes,
deterministic replay, five canonical Observer hashes, build, clean CPython
3.13.14 wheel install, source/wheel CLI parity, governance, and secret scan.

## 15. Provenance

HRAI is owner-authorized source mining, but no HRAI implementation may be
copied silently. The exact intended clean-room references at commit
`728f6c5058efe40a16e2aecc9b528b3353f4df4f` are:

```text
src/graph/workflow.py
src/llm.py
src/prompts/evaluation.py
experiments/historical_traffic_v0/runner/hr_bridge.py
experiments/historical_traffic_v0/runner/cost_ledger.py
experiments/historical_traffic_v0/out/run_200/RUN_MANIFEST.json
```

Triana reimplements only the strict adapter/protocol/accounting needed for this
slice and imports the pinned HRAI prompt/tool packages at execution. The final
destination/method/license/ancestry record must be complete in
`docs/PROVENANCE.md`. Agentagon remains restricted and supplies nothing.

## 16. Structured handoff

Target Connector V1 closure on 2026-08-03:

```text
What changed: retained the deterministic `episodes run` adaptive controller;
replaced the rejected target-specific HRAI reconstruction with restricted
`HTTP_JSON_V1` and strict `EXECUTABLE_JSONL_V1` opaque-target connectors;
removed the legacy four-tool adapter; froze exact endpoint, accounting,
privacy, state, failure, and no-fallback behavior.
Why each changed file was necessary: CLI dispatches the supported config;
adaptive_runner owns validation, identity, outer execution/accounting, custody,
dedupe, publication, and typed refusal; http_target owns declarative HTTP/JSON
session and transcript mapping; canonical documents own the supersession and
live evidence; acceptance fixtures/tests independently own the contract.
Change-budget reconciliation: seven production surfaces against a twelve-file
ceiling and 2,916 nonblank/noncomment production lines against 3,200; no
dependency, lock, pyproject, Release Review V1, or unrelated-file change.
What was verified: `./scripts/verify.sh` passed with 539 tests, including 131
frozen connector acceptance tests, Ruff, strict mypy over 28 source files,
deterministic replay, five unchanged Observer hashes, sdist/wheel build, clean
CPython 3.13.14 install, source/wheel parity, governance, and secret scan.
Evidence: `/private/tmp/triana-labs-verify.VyGGgn`.
What remains unverified: a successful real HRAI chat turn, live Foundry
simulator execution, three valid distinct trajectories, and
`LABS05_ADAPTATION_V1`.
Assumptions made: non-2xx bodies are failure evidence whose operation-specific
status is classified before successful-body JSON validation; response size and
secret-reflection checks still precede status handoff.
Unexpected findings: unchanged HRAI startup could not reach configured
Postgres, `/health` made an unaccounted target-internal OpenRouter diagnostic,
and session creation returned non-JSON HTTP 500 because configured Redis DNS
failed. The latter exposed and closed one Triana classification defect.
Dependencies added and why: none.
Out-of-scope problems deliberately left alone: HRAI infrastructure repair,
judges, persistent/global Triana memory, UI, real data, baseline/candidate diff,
generic SDKs, broad eval, hosted execution, and unrelated untracked research/
SPC files.
Known risks or uncertainty: target-internal calls, tokens, cost, retries, tool
trace, budget enforcement, and global-state isolation remain typed unavailable
unless a target reports them. The failed smoke proves endpoint reachability but
not successful protocol compatibility.
Human action still required: repair or supply reachable HRAI Postgres/Redis;
then separately authorize any new live run. After an exact valid three-episode
run, complete the frozen turn-level owner adaptation review.
```

Every worker and Codex returns:

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

## 17. Non-goals

Judges, persistent/global memory, UI, real-data support, baseline/candidate
diff, generic SDKs, broad eval expansion, DeepEval, DeepAgents, model/prompt
tournaments, automatic optimization, multi-target support, browser/voice/code
agents, hosted execution, and release verdicts are deferred. Nothing in this
packet expands the suspended Release Review V1.
