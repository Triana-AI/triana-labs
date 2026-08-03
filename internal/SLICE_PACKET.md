# LABS-06 intent-first continuation repair slice packet

Date frozen: 2026-08-03

Status: **LOCAL GREEN; SINGLE LIVE RUN CONSUMED WITH GAPS; HUMAN GATE UNPASSED**

Slice ID: `LABS-06-INTENT-FIRST-CONTINUATION-REPAIR-V1`

Canonical base: `b5a9faa` on branch
`codex/labs-06-regular-user-fidelity`.

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md` -> this packet.

Normative inherited contract: `internal/LABS06_SIMULATOR_FIDELITY_V1.md` except
where this packet explicitly supersedes the simulator response, intent priority,
state-transition, and live acceptance behavior.

## 1. Product outcome

Make the existing bounded LABS-06 multi-turn runner good enough to produce
grounded next-user continuations after live HRAI responses. This is a repair,
not a redesign: keep the same three-episode controller, context bundle, target
connector, budgets, privacy, custody, no-retry behavior, and readable private
review flow.

The repair has exactly three product changes:

1. reduce the provider-authored response from seven fields to three;
2. make user intent primary and persona a tone/persistence modifier;
3. evaluate three purposeful episodes spanning valid-world deepening,
   unavailable-item recovery, and a boundary or unexpected-status challenge.

No claim of multi-turn fidelity passes until Akarsh grades the live generated
turns against the frozen acceptance metric.

## 2. Accepted owner decisions

1. The provider returns exactly:

   ```json
   {
     "disposition": "EMIT",
     "user_utterance": "one next user message",
     "stop_reason_code": null
   }
   ```

2. `EMIT` requires a nonempty utterance and null stop reason. `STOP` requires
   null utterance and a declared stop reason. Unknown fields remain invalid.
3. Deterministic code binds the response to the exact outstanding simulator
   attempt and latest observation, assigns the `USER` role, owns custody, and
   applies critical semantic checks. The model does not echo hashes, declare
   its role, or select internal reaction/action identifiers.
4. Accepted `EMIT` leaves the closed episode interaction state unchanged.
   State remains episode-local and deterministic; the model cannot mutate it.
   Accepted `STOP` terminates once. No new classifier or state abstraction is
   introduced.
5. Intent is primary. Persona affects tone, patience, and persistence only.
   The simulator continues when a useful next step exists and naturally
   clarifies, corrects, selects an offered alternative, or challenges once
   when an unavailable premise blocks the original request.
6. The same three source cases remain bounded to recovery, boundary pressure,
   and existing-status/deeper lookup. No broad case-library expansion occurs.
7. One private three-episode HRAI/Foundry run is authorized after complete
   local GREEN. It uses the same named HRAI target, `client-techcorp`, Azure
   Foundry `FW-GLM-5.2`, private `/private/tmp` custody, USD 23 ceiling, 21 HTTP
   ceiling, bounded target-owned side effects, and no automatic rerun.
8. Akarsh alone supplies naturalness, intent-advancement, appropriate-stop,
   and overall acceptance rulings. Software and Codex do not approve them.

## 3. Exact provider instruction

```text
You simulate the next USER message in an ongoing conversation.

The user's goal is the primary authority. The persona affects tone,
communication style, patience, and persistence; it must not replace or weaken
the goal.

Read the full conversation, the assistant's latest response, and the verified
current facts. Produce exactly one natural user message that advances the goal
from the current state. Continue by default when a useful next step exists.

If the requested item is unavailable, naturally clarify, correct the request,
select an offered alternative, or challenge once when the persona supports it.
Stop only when the goal is satisfied, abandoned, or a final boundary has been
established.

Do not answer as the assistant, copy or paraphrase the assistant, invent facts,
tools, records, permissions, or results, reveal hidden facts, or take an action
outside the supplied user authority. Use structured STOP, never a visible stop
token.
```

The request retains the verified persona, intent, known facts, hidden fact IDs,
user-owned policy, episode-local state, transcript, latest observation, and
remaining-turn count. Hidden values remain controller-local.

## 4. Evaluation point and metric

Evaluation point: immediately after every simulator proposal and before it is
added as a `USER` turn or sent to HRAI.

Primary metric: **Accepted Continuation Rate**.

```text
Akarsh-accepted generated user turns / eligible simulator opportunities
```

A generated turn is owner-accepted only when it is a plausible regular user,
materially responds to the latest HRAI answer, advances or naturally resolves
the intent, remains grounded in the transcript/current world, and has no
critical semantic violation.

The one-run good-enough gate is:

- all three episodes reach at least opening -> HRAI A1 -> generated U2 -> HRAI A2;
- at least five of six planned simulator opportunities are structurally valid;
- at least four generated turns are accepted by Akarsh;
- zero role inversion, exact/near assistant echo, hidden-fact leak, fixed-fact
  conflict, or unauthorized literal action;
- no retry, repair, fallback, skipped denominator, or invented pass;
- an early structured stop reduces the denominator only when Akarsh accepts
  that the stop was appropriate.

Until the owner ruling exists, the live result remains `PENDING` or unpassed.

## 5. Input, output, and authority

Inputs remain the verified three-case LABS-04 projection, reviewed LABS-06
context bundle, transcript, latest target observation, current episode-local
state, and one provider response.

Outputs remain the existing eight adaptive-run artifacts plus the private
human-readable grading Markdown. No public report schema is added.

Deterministic code owns request/response identity, latest-observation binding,
role assignment, structural and critical semantic validation, termination,
budgets, accounting, custody, dedupe, privacy, publication, and typed gaps. The
simulator owns only disposition and wording. HRAI owns its target behavior and
side effects. Akarsh owns human fidelity truth.

## 6. Refusal and gap behavior

- Invalid context remains pre-egress `SIMULATOR_CONTEXT_INVALID`.
- Provider/network failure remains `SIMULATOR_PROVIDER_ERROR`.
- Malformed three-field output remains `SIMULATOR_INVALID_RESPONSE`.
- Deterministic critical defects remain `SIMULATOR_SEMANTIC_INVALID` with the
  existing applicable detail codes.
- `STOP` with an undeclared reason is `SIMULATOR_SEMANTIC_INVALID` with
  `STOP_NOT_ALLOWED`.
- No invalid response enters transcript custody as a user turn.
- No retry, response repair, provider/model/target fallback, default message,
  or hidden second attempt exists.
- Later already-funded episode slots may continue under inherited behavior.

## 7. Minimum independent acceptance set

The independent test author changes only test-owned paths and freezes no more
than eight focused black-box functions:

1. intent-first provider instruction and exact three-field schema;
2. a valid emit is deterministically bound to the latest observation, assigned
   `USER`, and advances to a second target response;
3. unavailable-item recovery accepts clarification or offered-alternative
   selection without reaction/action IDs;
4. valid-world deepening accepts a grounded follow-up and preserves state;
5. valid structured stop terminates once with no visible stop token;
6. malformed legacy seven-field and malformed three-field outputs fail once;
7. role inversion, assistant echo, hidden/fixed-fact defect, and unauthorized
   literal action remain critical failures;
8. historical no-bundle LABS-05 behavior, accounting, privacy, custody, and
   cross-episode isolation remain unchanged.

No test may require exact model wording, helper shape, combinatorial enum
coverage, new metric artifacts, or speculative abstractions.

Valid RED requires collection success, no setup/import error, unchanged
historical acceptance GREEN, and focused failures caused only by the missing
three-field/intent-first behavior.

## 8. Three-role protocol

Codex is orchestrator. One independent test-author agent edits only frozen
test-owned paths and proves RED. Codex audits and freezes those bytes. A
different implementation-author agent then edits only production-owned paths.
Workers run serially in the shared worktree. Codex alone reconciles scope,
verifies final behavior, performs the separately authorized live run, records
evidence, and declares completion.

## 9. Change budget

Orchestrator-owned:

```text
internal/SLICE_PACKET.md
internal/LABS06_SIMULATOR_FIDELITY_V1.md
internal/DECISION_LOG.md
internal/WORKING_MEMORY.md
internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md
triana-labs/CHARTER.md
triana-labs/scripts/verify.sh (frozen LABS-06 acceptance hashes only)
.decision-memory/2026-08-03-codex-labs-06-regular-user-fidelity.md
/private/tmp LABS-06 live driver, bundle, artifacts, and readable report
```

Test-author-owned:

```text
triana-labs/tests/simulator_fidelity_acceptance/**
```

Implementation-author-owned after RED freeze:

```text
triana-labs/src/triana_labs/adaptive_runner/boundaries.py
triana-labs/src/triana_labs/adaptive_runner/simulator_fidelity.py
triana-labs/src/triana_labs/adaptive_runner/runner.py
```

Maximum production files: three. Maximum changed production physical lines:
260. Maximum changed/new test physical lines: 500. No dependency, lockfile,
package metadata, context-bundle schema, CLI, config schema, connector, target,
generic SDK, UI, public report, judge, memory, baseline/candidate, external repo,
or HRAI code change is allowed.

Explicitly untouched unrelated user files:

```text
internal/RESEARCH_BRIEFING_SIMULATION_FIDELITY_2026-08-02.md
internal/SPC_APPLICATION_EVIDENCE_MAP_2026-08-02.md
internal/SPC_INTERVIEW_VERBATIM_2026-08-02.md
```

Any worker stops before crossing this budget. No cleanup or opportunistic
refactor is allowed.

Mechanical budget clarification after implementation: the complete verifier
correctly rejected the superseded LABS-06 frozen hashes after all 566 tests
passed. `triana-labs/scripts/verify.sh` is therefore added to orchestrator
ownership for exactly two expected-hash literal replacements. This changes no
test or product behavior and is not a material scope expansion. The verifier's
own ordered `shasum` stream identity is
`0e3566eaf8d58378ee6df9c9a4538f9397d47110e14077bcdda95d3b8f7ba76a`;
the packet's earlier `f493...` identity used a different explicit path/hash
encoding and remains a valid independent freeze identity.

## 10. Verification

RED and focused GREEN:

```bash
cd triana-labs
uv run pytest tests/simulator_fidelity_acceptance -q
```

Historical adaptive regression:

```bash
cd triana-labs
uv run pytest tests/adaptive_runner_acceptance -q
```

Complete repository gate:

```bash
cd triana-labs
./scripts/verify.sh
```

The live run occurs only after all three commands are GREEN and consumes the
single authorization at the first provider or HRAI request. A zero-egress
preflight refusal does not consume it; any external request does. There is no
automatic rerun.

## 11. Exit evidence and structured uncertainty handoff

Every worker and the orchestrator reports: changed files and why; budget
reconciliation; exact commands/results/artifacts; unverified work; assumptions;
unexpected findings; dependencies; deliberately excluded problems; known
risks; and required human action, using `none` explicitly.

The slice exits only with frozen RED, separate implementation GREEN, focused
and complete verifier evidence, one consumed live result or typed pre-egress
refusal, a readable private grading Markdown, canonical status updates, and an
owner-pending human ruling.

## 12. Independent RED freeze

The independent test author changed exactly the four existing test-owned Python
files with 244 additions and 255 deletions, exactly 499 changed physical lines
against the 500-line budget. The suite contains eight black-box functions and
collects 15 cases.

Frozen whole-file identities:

```text
conftest.py                 92ec4143191ca801f2b8c0b7091c104433582005c169457d24413c078a059749
test_runtime_contract.py    f43669e5c91776204a876197f59ef01286a509ea2bd2db18a5af5de11d9cd1f7
test_semantic_refusals.py   615f664519975043050856b3f5f75e2b03e8c9b6af1fb2c421eb43a32bd7c9af
test_teacher_forced_review.py 94833e8b35ba5914f3d389b88f096d0d3046d08a60d12d5c4cbef896f7cb9d09
```

Ordered concatenated content SHA-256:
`0320dbf68093f142dc39c491ad52b447f1af3ddbf81bfd614b4a031ea35c566f`.
Ordered path/hash-stream SHA-256:
`f493fa51d1bdf2ea59b010b86b6d38fda92354f099d579bdf02eaca6516402ec`.

Codex independently reproduced focused valid RED as 11 failures and four
control passes, with no collection/setup/import error, and reproduced 143/143
historical adaptive-runner passes. Ruff and diff checks are GREEN. Frozen
test-owned bytes may not change during implementation.

## 13. Implementation, verification, and live result

The separate implementation author changed exactly the three authorized
production files: 26 insertions plus 69 deletions, 95 changed physical lines
against the 260-line ceiling. Frozen test bytes remained exact. No dependency,
CLI/config, connector, context schema, target, report, memory, judge, or
external repository changed.

Final local verification:

```text
focused repair acceptance: 15/15 passed
historical adaptive acceptance: 143/143 passed
complete repository suite: 566/566 passed
Ruff, format, strict mypy, deterministic/versioned gates: passed
source/wheel build and clean CPython 3.13.14 install: passed
evidence: /private/tmp/triana-labs-verify.HqCiRi
```

The one authorized private run used the frozen three-context bundle
`sha256:ca7627ac232793421164005abc12fa563c6505c2b03412c4ddb3aac4e8194987`,
live HRAI for `client-techcorp`, and Azure Foundry `FW-GLM-5.2`. It was consumed
once and not rerun. Result:

```text
outcome: COMPLETED_WITH_GAPS
attempted episodes: 3
valid/effective trajectories: 0/0
target/simulator/all HTTP: 9/3/12
typed gaps: 13
termination: SIMULATOR_INVALID_RESPONSE for all three episodes
reserved/actual USD: 8.666664/unavailable
generated simulator transcript turns: 0
```

All three HRAI openings received one assistant response, but each first
three-field simulator continuation was rejected before transcript insertion or
A2. Thus all-three-reach-A2 fails, structural yield is 0 of 3 attempted and 0
of 6 planned opportunities, and owner Accepted Continuation Rate is unavailable
rather than zero or pass. Raw rejected provider content is not present in the
published artifacts, so the exact provider envelope/schema defect is unknown.
No retry, repair, fallback, or second run occurred.

Private readable report:
`/private/tmp/triana-labs06-hrai-intent-first-live-20260803-c/LABS06_HRAI_CONVERSATIONS_READABLE.md`.

Structured uncertainty handoff: unverified work is the exact live provider
structural subcause and all human naturalness/intent rulings. Assumptions are
none beyond the frozen inputs. Unexpected finding is the repeated structural
failure after schema reduction. Dependencies added: none. Deliberately excluded
problems are provider-response diagnostics, retry/repair, model/provider change,
new cases, memory, judges, UI/report, and HRAI changes. Known risk is that local
fake compatibility does not establish Foundry/GLM response-envelope
compatibility. Human action required: Akarsh may read the report, but there are
no generated continuations to grade; any further live or diagnostic work needs
a new decision.
