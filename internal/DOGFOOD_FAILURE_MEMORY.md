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

Status: `OPEN`

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
