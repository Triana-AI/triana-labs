# Triana dogfood failure memory

Updated: 2026-08-03

This is Triana's append-only operational memory for failures discovered while
using Triana on Triana, HRAI, or another explicitly authorized dogfood target.
It prevents later agents from repeating a failed path or converting an
unexplained gap into a product conclusion.

This file is evidence memory, not product authority, a backlog, or a source of
accepted truth. Durable product or architecture decisions still belong in
`internal/DECISION_LOG.md`; unresolved work belongs in
`internal/WORKING_MEMORY.md`. Never include secrets, private transcript text,
provider response bodies, or customer evidence here. Append corrections and
supersessions; do not rewrite prior incidents.

Each incident records:

- the observed failure and smallest reproduction;
- what the retained evidence proves and does not prove;
- the mistaken interpretation or failed intervention, if any;
- customer/product impact;
- a falsifiable repair hypothesis and the next permitted check;
- explicit egress, privacy, retry, and human-authority boundaries;
- status: `OPEN`, `MITIGATED`, `CLOSED`, or `SUPERSEDED`.

## DF-2026-08-03-001 — LABS-06 live continuations rejected before U2

Status: `WIRE RESOLVED; WORLD-GROUNDING/INTENT FOLLOW-UP OPEN`

### Observed failure

Two separately authorized three-case LABS-06 runs reached the same result.
Each HRAI session create, opening chat, and close succeeded. Each Azure Foundry
`FW-GLM-5.2` simulator request completed one HTTP exchange and returned a
distinct, token-accounted response, but all six first continuations were
rejected as `SIMULATOR_INVALID_RESPONSE`. No proposed user turn entered a
transcript, no episode reached A2, and both runs closed
`COMPLETED_WITH_GAPS` with zero valid or effective trajectories.

Private retained evidence remains local under:

- `/private/tmp/triana-labs06-hrai-live-20260803-b`
- `/private/tmp/triana-labs06-hrai-intent-first-live-20260803-c`

The private artifacts are not repository fixtures and must not be published,
uploaded, copied into tests, or treated as general real-data authorization.

### Smallest retained reproduction

The first failing simulator exchange in either run is sufficient to reproduce
the observed boundary:

1. HRAI returns A1.
2. Triana sends one LABS-06 simulator request.
3. Foundry returns a response with non-zero prompt and completion tokens.
4. Triana rejects the response before semantic fidelity validation and ends
   the episode without retry, repair, or fallback.

No provider or target rerun is authorized by this record.

### Proven by retained evidence

- HRAI/RDS was not the failing boundary for these six continuations.
- Foundry did not time out or return an empty response.
- In the three-field run, the transport parsed a provider envelope, parseable
  JSON content, the exact expected key set, and integer token usage. Otherwise
  its invalid-transport path would have recorded zero tokens.
- Rejection occurred during later value/relationship validation before role,
  echo, hidden-fact, fixed-fact, reaction/action, or stop-policy semantic gates.
- The seven-field-to-three-field prompt/contract change altered requests and
  outputs but did not improve live accepted-continuation yield.
- Triana correctly refused to invent a valid trajectory or human fidelity
  ruling.

### Unknown from retained evidence

The raw rejected simulator bodies were intentionally not published. The exact
violated value rule is therefore unavailable. It must not be reconstructed by
guessing or a blind replay.

For the three-field contract, remaining possibilities include an inconsistent
`EMIT`/`STOP` nullability combination, an invalid disposition value, unsafe or
oversized text, or another projection mismatch. The leading hypothesis is a
cross-field inconsistency because the provider schema permits combinations
that the deterministic validator later rejects, but this is not yet proven.

### Failed interpretation and intervention

The first one-turn result was interpreted primarily as overly restrictive
persona/intent/turn-policy behavior. The ensuing repair made intent primary,
changed the prompt, and reduced the provider proposal from seven fields to
three. That intervention was locally GREEN but did not target a proven live
failure subcause and the second live run failed at the same boundary.

Lesson: prove provider-to-validator conformance before tuning simulation
fidelity. A local fake that returns an ideal contract object proves runner
self-consistency, not live provider compatibility.

### Product impact

- Accepted Continuation Rate was `0/3` in each run.
- Multi-turn fidelity, adaptation, role safety, and natural stopping were not
  exercised live and remain unpassed.
- The single generic reason code prevented exact diagnosis.
- Hash-only rejected-response custody preserved privacy but omitted a safe
  diagnostic projection.
- After the first shared conformance failure, two later cases repeated the
  same integration boundary and added cost without testing deeper behavior.

### Bounded repair hypothesis

The smallest repair is an observability-and-conformance slice, not another
persona or simulation redesign:

1. Split `SIMULATOR_INVALID_RESPONSE` into stage-specific typed subreasons for
   envelope, content JSON, key set, disposition, EMIT companion fields, STOP
   companion fields, and safe-text validation.
2. Retain a privacy-safe diagnostic projection only: response hash, content
   byte length, finish reason when present, sorted key names, disposition,
   null/non-null field shape, token counts, and failing validator stage. Never
   retain rejected utterance text, hidden facts, secrets, or the raw response.
3. Align the advertised provider contract with deterministic value rules. At
   minimum, describe the exact EMIT and STOP field relationships in the schema
   and system instruction and cover both with independent black-box tests. Do
   not loosen semantic, privacy, role, observation-binding, or stop authority.
4. Add an integration-conformance gate before any target episode: the exact
   production transport must convert a bounded synthetic provider envelope
   into either a valid typed proposal or an exact typed rejection. Hermetic
   tests must include inconsistent EMIT/STOP combinations rather than only an
   ideal fake proposal.
5. Treat a confirmed shared simulator-contract failure as a run-level circuit
   break. Later target slots become a typed shared-conformance gap without
   further HRAI/provider egress; this is not retry, repair, or fallback.

### Eval point and exit condition

Before another HRAI run, measure `Structural Continuation Yield`:

```text
structurally valid simulator proposals / attempted simulator proposals
```

The minimum conformance exit is `3/3` on the fixed synthetic LABS-06 cases,
with exact typed diagnostics for every injected invalid combination, preserved
token/accounting/privacy behavior, and zero retry/repair/fallback. After that,
and only with separate owner permission, the existing end-to-end metric
resumes: all three cases produce a valid EMIT or allowed STOP, at least the two
continuation-requiring cases reach A2, owner fidelity rulings remain human,
and critical semantic failures remain zero.

### Next falsifiable check

Freeze RED tests showing that the current implementation collapses distinct
cross-field failures into one generic reason and publishes no safe diagnostic
stage. Implement typed diagnostics and contract alignment locally. Then request
separate authorization for a simulator-only, synthetic, no-HRAI conformance
execution. Do not call HRAI, Foundry, another provider, or real data under this
incident entry alone.

### Local mitigation update — 2026-08-03

The bounded conformance repair is locally implemented and verified. The exact
three-field authority remains unchanged; EMIT/STOP companions are explicit;
all accepted structural stages now produce one closed detail code and a
bounded text-free diagnostic; normalized usage survives later content
rejection; privacy retains first precedence; and two distinct matching
first-continuation failures block the next slot without target or simulator
egress. No validation was weakened and no retry, repair, fallback, raw-body
retention, or persistent memory was added.

Independent evidence is 43/43 focused cases, 143/143 historical adaptive
cases, and a complete 594-test/build/install verifier pass at
`/private/tmp/triana-labs-verify.qLDTKk`. No provider, HRAI, target, or real
data ran during the repair. Status remains `OPEN`, not `MITIGATED` or `CLOSED`,
because the falsifiable live condition is still unobserved: a separately
authorized simulator-only synthetic check must produce Structural
Continuation Yield `3/3` with exact accounting, zero privacy leakage, and zero
retry/repair/fallback before another HRAI run is considered.

### Live conformance update — 2026-08-04

The owner-authorized production-transport synthetic check made exactly three
Azure exchanges and produced Structural Continuation Yield `2/3`. Two `EMIT`
responses were structurally valid. The failed response returned `STOP` with
both a nonempty stop reason and a non-null user utterance; the new diagnostic
typed it exactly `SIMULATOR_STOP_FIELDS_INVALID`. Input/output tokens were
retained for all three, USD 3 was reserved, and no retry, repair, fallback,
provider switch, HRAI, RDS, or target call occurred.

This proves the bounded hypothesis: the provider-facing schema allowed two
nullable companion fields whose cross-field relationship it could not enforce.
The next check is a two-field `action` plus single `content` wire in which the
observed invalid combination is unrepresentable and deterministic code maps
content to the unchanged internal EMIT/STOP authority. HRAI remains blocked
until a fresh three-call check reaches `3/3`.

## DF-2026-08-03-002 — Shared schema drift broke legacy LABS-04

### Observation

The first full verifier for `LABS-046-GROUNDED-WORKFLOW-CLOSURE-V1` produced
538 passes and 65 LABS-04 failures. Focused closure tests were green. Every
failure crossed the legacy provider request boundary after three new optional
fields had been added to the shared proposal schema.

### Smallest reproduction and hypothesis

Representative `test_wire_exactness.py` and `test_success_artifacts.py` cases
failed because the shared schema changed the deterministic prompt/request hash,
so scripted legacy provider responses no longer matched. The falsifiable
hypothesis was that closure fields belonged only in the closure dynamic schema.

### One attempted change and result

The static proposal schema was restored exactly to `main`; `goal`,
`done_when`, and `required_world_keys` are now added only when a verified world
inventory selects closure mode. No assertion, retry, repair, or fallback was
added. Focused closure acceptance passed 9/9, representative legacy acceptance
passed 7/7, and the complete repository verifier passed 603/603 at
`/private/tmp/triana-labs-verify.eLaFCb`.

### Prevention

Versioned modes must not mutate shared provider schema bytes when historical
request identity is frozen. Additive fields are isolated behind the versioned
dynamic renderer, and the complete verifier remains mandatory before closure.

### Related open blocker

The closure implementation is honest synthetic-only. Existing trace and world
inventory validators refuse owner-authorized real data. This is not repaired
by relabeling HRAI/RDS evidence; it requires a separately frozen real-data
contract and exact custody/egress approval.

## DF-2026-08-04-003 — Real-data Case Factory transport failure blocked LABS-06

Status: `CASE_FACTORY RESOLVED; LABS-06 FOLLOW-UP RECORDED`

### Observed failure

An owner-authorized real-data canary inspected 15 eligible operational HRAI
recruiter traces and deterministically selected four distinct traces. Observer
accepted all four, and Intelligence produced four structural clusters with
three typed gaps. The first Case Factory exchange returned
`MATERIAL_INPUT_REQUIRED`; the already-approved authoritative direction was
then supplied once. That continuation ended `PROVIDER_TRANSPORT_FAILED` after
three HTTP exchanges and produced zero valid or distinct cases.

Private retained evidence remains local under
`/private/tmp/triana-labs046-live-20260804.y9Jb0l`. It must not be committed,
published, uploaded, or converted into fixtures. No private transcript text,
provider response body, credential, or customer evidence is retained here.

### Accounting and boundary

The Case Factory consumed two logical provider calls and four HTTP exchanges,
with USD 4 reserved. The first response reported 25,147 input tokens and 826
output tokens; the failed continuation did not provide trustworthy token or
actual-cost accounting, so actual cost remains unknown rather than zero.

No retry, repair, provider switch, or fallback followed the transport failure.
Because no deterministic case/persona/intent/turn-policy bundle existed,
LABS-06 made zero simulator calls and zero HRAI calls and caused zero target
side effects. Its result is `NOT_EXECUTED`, not pass or behavioral failure.

### Proven and not proven

The trace-selection, normalization, and structural-clustering path accepted
the selected input. The failure occurred at the Case Factory provider
transport boundary before valid generated artifacts existed. This run does
not evaluate grounded-observed case quality, grounded-expanded case quality,
regular-user multi-turn fidelity, or HRAI behavior under those cases.

### Next falsifiable check

Diagnose the retained text-free transport metadata locally and reproduce the
same request/response boundary without HRAI or real-data egress. Any new
provider, endpoint, real-data, or HRAI execution requires a new explicit
authorization and must remain a one-attempt, bounded canary. Do not infer or
reconstruct the missing case bank from the source traces by hand.

### Direct-normalization proof update — 2026-08-04

The authorized direct-submit proof removed the question, search, trace-fetch,
repair, and agent-graph paths and made one fresh provider exchange for the
first five slots. Context preflight passed. The request used 24,962 prompt
tokens, carried a forced `submit_case_batch` tool choice, and reserved USD 2.

`FW-GLM-5.2` returned no tool call. It emitted 25,000 completion tokens as
plain explanatory/case-drafting text and stopped with finish reason `length`
after 141.75 seconds. Triana rejected it as `PROVIDER_INVALID_RESPONSE`,
persisted zero cases, and did not execute the remaining batches, repair,
retry, fallback, another provider, or HRAI.

This falsifies context duplication as the only blocker. The direct request was
well beneath the 100,000-token working ceiling; the newly observed boundary is
forced-tool compatibility plus an oversized five-case output. Before another
authorized proof, replace provider-specific forced tool submission with an
explicit structured-response boundary and reduce authoritative batch width so
one incomplete output cannot erase multiple cases.

### Strict structured-output proof update — 2026-08-04

The next authorized proof used a compact strict JSON-Schema response, one case
slot, no tools, no agent graph, and the same private evidence/inventory. The
provider returned complete parseable JSON with finish reason `stop` in one
exchange: 17,288 input tokens, 8,082 output tokens, and 53.615 seconds.

Triana nevertheless rejected the response as `PROVIDER_INVALID_RESPONSE`
before normalization because a stale post-transport guard still required the
old tool path to populate `tools.submission`. That guard was removed only for
the authoritative structured path. Inspection also showed semantically poor
field naming: the model placed claim-key tokens in human-readable text fields.
The wire now names those fields `content` and `claim_text` and explicitly
requires real human-readable content.

No second exchange, repair, retry, fallback, provider switch, or HRAI call
followed. The retained response proves strict JSON-Schema support on this
deployment but does not prove an accepted grounded case because the consumed
run never reached deterministic normalization.

### Successful structured-normalization proof — 2026-08-04

Proof V9 completed all twelve planned slots after the wire was reduced to
human-readable content with direct evidence handles, deterministic local
claims, required primary world binding, deterministic one-trace observed and
two-trace expanded source selection, structural evaluation/reaction fields,
and normalized stressor labels.

The result is 12 valid and 12 distinct cases: exactly six
`OBSERVED_PRODUCTION_CASE` and six `GROUNDED_EXPANDED_CASE`. All twelve provider
attempts succeeded in their single `GENERATE` phase, with twelve HTTP
exchanges, 207,640 input tokens, 54,738 output tokens, USD 24 reserved, no
typed gaps, and no questions, tools, agent graph, repair, SDK retry, fallback,
provider switch, or HRAI call. Actual provider cost remains unavailable rather
than zero. Private artifacts are retained under
`/private/tmp/triana-labs04-structured-proof-v9-20260804`.

Across all authorized proof attempts in this iteration, cumulative reserved
spend was USD 42, below the owner's USD 100 ceiling. The successful proof
closes the Case Factory generation boundary only; tests, repository verifier,
LABS-06 execution, and human fidelity rulings remain separate.

### Acceptance-freeze update — 2026-08-04

The strict normalization behavior is now frozen by four independently authored
black-box acceptance cases. They reproduced RED 4/4 against base `1460266`,
pass on the implementation, and the complete Case Factory suite passes 212
tests. The complete repository verifier passes 617 tests plus source/wheel
build and clean-wheel installation at
`/private/tmp/triana-labs-verify.m8oIxX`. The Case Factory blocker is resolved;
the separate LABS-06 live trajectory and human fidelity assessment remain
open and must not be inferred from this result.

## DF-2026-08-04-004 — LABS-06 multi-turn mechanics passed while world fidelity failed

Status: `OPEN`

### Observed failure

The final identical HRAI canary retained three valid/effective machine
trajectories from twelve selected grounded workflows. Two reached six role
turns, proving that the repaired action/content wire can produce real adaptive
continuations. Both multi-turn conversations nevertheless introduced world
claims absent from the authorized inventory and latest HRAI observation:
nonexistent uploaded files, a new candidate, an unavailable position, resume
paths, and a LinkedIn URL. One additional partial conversation abandoned its
verification-before-shortlisting intent and requested recommendation upgrade,
shortlisting, outreach, database mutation, and ATS ranking despite explicit
verification gaps.

The live output therefore closed `COMPLETED_WITH_GAPS`, not passed. It retained
12 attempted episodes, 3 valid/effective trajectories, 31 target plus 8
simulator HTTP exchanges, 111 target tool calls, USD 36.333320 reserved, and
actual cost unavailable. Target internal errors/tool budgets and the frozen
run deadline made the other nine episodes partial or unavailable. Human
fidelity and completion rulings remain blank.

### Smallest reproduction

Conversation 7 is sufficient:

1. HRAI asks for missing resume, position, and candidate context.
2. The simulator invents Daniel Whitfield, `POS-2041`, a resume path, and a
   LinkedIn URL rather than selecting only bound or observed world values.
3. HRAI truthfully reports that the position/file/profile do not exist and
   lists actual positions.
4. The simulator selects a real position but invents a second resume path.

Conversation 4 independently shows the same class by claiming three security
test PDFs were uploaded after HRAI said it could only parse supplied files.

### Falsified interpretation

The earlier belief that the strict persona/intent policy merely stopped too
early is incomplete. After the structural wire was repaired, the simulator did
continue adaptively. The remaining dominant defect is the opposite: semantic
validation permits plausible but unauthorized world-state additions and does
not enforce intent preconditions strongly enough.

### Bounded next hypothesis

Before transcript admission, deterministically reject a proposed next user turn
that introduces an entity, file/path, position, URL, or claimed upload absent
from both the bound world inventory and latest HRAI observation. Also reject an
action request that contradicts an explicit case-intent precondition such as
verification before shortlisting. Preserve a typed semantic gap with no repair,
retry, fallback, invented alternative, memory, judge, or target rerun.

Private evidence remains under
`/private/tmp/triana-labs06-final-live-20260804-v5` and must not be committed or
used as a public fixture.

### Owner disposition and backlog update — 2026-08-04

Akarsh accepted Conversation 3 and Conversation 4 for the current round.
Conversation 4's unsupported uploaded-file claim remains a known backlog
defect rather than a blocker for that conversation's owner ruling. This does
not accept Conversation 7, close the broader world-grounding incident, or pass
LABS-06 overall.

The smallest candidate fix is a generic mutation-authority contract, not a
hard-coded action list: mutation claims require an allowed mutation class and
a bound or newly observed object. A missing authority or object becomes a
typed pre-admission gap with no retry, repair, or fallback. The fix is not yet
implemented. A future twelve-case execution should also raise the overall run
deadline above 600 seconds; the recommended value is 1,800 seconds with
unchanged per-call timeouts and no retry. Network instability is the owner's
attribution for the four not-started episodes, not a proven target defect.

Closure disposition: `ACCEPTED_BACKLOG`. Akarsh closed LABS-06 without
closing this operational incident or converting its negative evidence into a
pass. The world-mutation and intent-precondition guards move forward as
bounded backlog; target availability remains separately typed. This entry
must be consulted before any later simulator-fidelity or live-run slice.

## DF-2026-08-04-005 — Case Factory cache preserved evidence but did not replay it

Status: `OPEN`

### Observed failure

During V11 through V17 regeneration, the private directory named `cache`
preserved exact provider requests/responses and stage artifacts but fresh runs
still called Azure from batch one. The operator initially interpreted the
directory as an executable exact-response cache and described later attempts
as cached progress. Attempt accounting disproved that interpretation: fresh
runs reported new provider HTTP exchanges and different response hashes.

### Impact and recovery

Repeated explicit runs consumed USD 52 reserved before the mistake was
corrected. No budget ceiling was exceeded, and no hidden retry occurred, but
the labeling and operator expectation were wrong. The original V9 cache did
retain all twelve exact successful request/response pairs. A private replay
transport verified the system instruction, user request, strict schema, and
response wire for every slot, then replayed those responses through the
repaired deterministic normalizer with zero provider HTTP exchanges. V19
completed 12/12 valid and distinct.

### Bounded next hypothesis

Rename the current surface to evidence custody or implement an explicit,
hash-verified replay command with distinct accounting for logical replay versus
provider HTTP exchange. Do not silently infer replay from file presence.
