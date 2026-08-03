# LABS-06 regular-user simulator fidelity handoff

Date: 2026-08-03

Status: **NEW-SESSION ENTRY; PLANNING AND OWNER QUESTIONS BEFORE IMPLEMENTATION**

## 1. Restart ground truth

- LABS-04 passed `LABS04_USEFULNESS_V1`: five requested, valid, distinct cases;
  no gaps, repairs, or duplicates.
- LABS-05's local adaptive runner and opaque target connectors are implemented.
  The final pre-handoff repository verification passed 551 tests plus the
  complete versioned gate at `/private/tmp/triana-labs-verify.CRYzso`.
- The single owner-authorized real HRAI canary is consumed and cannot be rerun
  under its old authorization. It attempted three episodes, produced two valid
  distinct trajectories and one partial trajectory, and closed with gaps.
- Akarsh's available adaptation rulings were R1 Y, R2 N, R3 Y, and R4 Y; two
  required items were unavailable. LABS-05 is closed and unpassed.
- R2 exactly copied the preceding 1,553-character HRAI answer and assumed the
  assistant role. The supported cause is that the simulator request omitted
  the verified persona, intent, and turn-policy projections, while its prompt
  and structural validator did not enforce user role or reject assistant echo.
- Persistent/global Triana memory remains deferred. LABS-06 may use immutable
  case context plus bounded episode-local interaction state only.
- The next public path is LABS-06 fidelity, LABS-07 report contract, LABS-08
  Labs UI, LABS-09 public synthetic demo, and LABS-10 stranger installation.
- No provider experiment, real-data use, HRAI mutation, UI implementation,
  baseline/candidate diff, judge, generic SDK, or broad eval expansion is
  authorized by this handoff.

Canonical supporting documents:

1. `AGENTS.md` and every authority it requires;
2. `triana-labs/CHARTER.md`;
3. `internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`;
4. `internal/DECISION_LOG.md` in full;
5. `internal/WORKING_MEMORY.md`;
6. `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`, `docs/ENGINEERING.md`, and
   `docs/PROVENANCE.md`;
7. `internal/LABS05_SIMULATOR_FIDELITY_REVIEW_2026-08-03.md`;
8. `internal/LABS05_REAL_DATA_CANARY_2026-08-03.md`;
9. `internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md`;
10. the current `internal/SLICE_PACKET.md`, which remains the closed LABS-05
    packet until a separately accepted LABS-06 packet replaces it.

## 2. Intended LABS-06 outcome

LABS-06 should make the adaptive-user boundary believable enough to support a
public synthetic Preview claim:

> Given a grounded persona, intent, known facts, user-owned turn policy,
> conversation prefix, and latest agent response, Triana produces exactly one
> plausible next user action or a structured stop, while deterministic code
> rejects assistant imitation, echoing, fact leakage, and unauthorized action.

The round should prefer a small, explicit design and fail-fast evidence over a
general conversation-simulation framework.

The recommended exit is:

- accepted LABS-06 LLD and wire/spec;
- a frozen small teacher-forced fidelity fixture/panel;
- minimum black-box acceptance tests for critical authority/refusal behavior;
- implementation that is locally GREEN against those tests;
- a reproducible review packet and honest gaps;
- no live/provider execution unless Akarsh separately authorizes one after the
  local gate is complete.

## 3. First-turn protocol in the new session

The new session must **not implement immediately**.

Its first turn must:

1. read all authority and handoff documents;
2. inspect the current simulator request, provider boundary, response model,
   runner turn transition, publication artifacts, and existing acceptance
   tests;
3. restate the active outcome and explicitly say what it proposes to do and
   not do;
4. produce a concrete LLD and behavioral spec proposal;
5. enumerate the smallest meaningful edge-case matrix;
6. identify every material owner choice and ask the questions in section 7;
7. recommend defaults rather than asking open-ended questions where evidence
   supports a choice;
8. stop and wait for Akarsh's answers.

Only after Akarsh answers may the session:

1. append accepted durable decisions;
2. replace `internal/SLICE_PACKET.md` with the exact LABS-06 contract and
   change budget;
3. use the independent orchestrator/test-author/implementation-author protocol;
4. freeze minimum acceptance RED;
5. implement within the accepted budget;
6. run the full repository gate before commit;
7. request separate authority before any provider, external endpoint, or real-
   data execution.

## 4. Recommended LLD to challenge and refine

```text
VerifiedCaseProjection
  ├── persona
  ├── intent
  ├── known/hidden facts
  └── user turn policy
             │
             ▼
Deterministic SimulatorContextProjection
  + transcript prefix
  + latest observation/hash
  + bounded InteractionState
             │
             ▼
Pinned SimulatorTransport
  -> one structured next-turn proposal
             │
             ▼
Deterministic SimulatorSemanticValidator
  ├── role check
  ├── exact/near echo check
  ├── known/hidden fact check
  ├── authorized-reaction/action check
  └── structured-stop check
             │
       ┌─────┴───────────────┐
       ▼                     ▼
EMIT_USER_TURN         REJECT / STOP
       │                     │
       ▼                     ▼
target connector       typed evidence; no target call
```

Proposed internal objects:

- `SimulatorContextProjection`: immutable closed projection sent to the model;
- `InteractionState`: episode-local patience/trust/urgency/confusion/goal state;
- `SimulatorTurnProposal`: text, consumed observation hash, stop proposal, and
  optionally declared reaction identifier;
- `SemanticValidationResult`: accepted/rejected plus closed defect codes;
- `TurnDisposition`: `EMIT`, `STOP`, or `REJECT`;
- `TeacherForcedItem`: frozen prefix, context projection, latest observation,
  expected allowed-reaction set, and review identity;
- `FidelityRuling`: human-owned item judgment; never model-owned acceptance.

Authority:

- deterministic code owns identity, projection, state transitions, binding,
  validation, budgets, termination, denominators, and publication;
- the simulator owns wording and may propose a reaction/stop only;
- a human owns naturalness/material-adaptation acceptance and thresholds;
- no judge or persistent memory owns truth.

## 5. Recommended interaction-state boundary

Do not create an emotion engine. Keep only fields that affect the next user
reaction and can be inspected:

- `patience_level`;
- `trust_level`;
- `urgency_level`;
- `confusion_level`;
- `goal_state` (`OPEN`, `SATISFIED`, `ABANDONED`);
- `remaining_disclosures` or the equivalent turn-policy cursor.

Transitions should be deterministic from a closed target-observation category
plus the persona/turn policy. The LLM may realize the state as natural wording;
it may not alter the state or invent a new fact.

If the source evidence cannot support a field or transition, leave it unknown
or omit it rather than inventing customer truth.

## 6. Minimum edge cases and must-have tests

The first session should challenge this list and reduce duplication. The
recommended acceptance set is approximately 8–12 black-box behavioral tests,
not a combinatorial matrix.

Must cover:

1. simulator request carries the exact verified persona, intent, user-owned
   policy, fact visibility, interaction state, and latest-observation hash;
2. the preserved R2 exact assistant echo is rejected before any next target
   call and remains typed evidence;
3. assistant-role inversion with non-identical wording is rejected;
4. hidden-fact leakage or fixed-fact contradiction is rejected;
5. a reaction/action outside the frozen user policy is rejected;
6. a valid regular-user reaction is emitted and bound to the exact latest
   observation;
7. structured stop ends once without emitting `:done:` or calling the target;
8. malformed/unknown semantic output fails fast with no retry or fallback;
9. one episode's interaction state cannot affect another episode;
10. existing identity, budget, HTTP custody, privacy, and target-connector
    behavior remain unchanged.

Possible collapse: cases 3–5 may share one parameterized semantic-rejection
test if the public defect codes and custody assertions remain explicit.

Do not add tests merely for line coverage, every enum member, trivial dataclass
construction, private helper shape, or framework behavior already guaranteed
elsewhere.

## 7. Questions the new session must ask Akarsh

Ask these after showing the proposed LLD/spec and recommendations:

1. **Round exit:** Should LABS-06 end at locally GREEN implementation plus a
   generated human-review packet, or should it also include one separately
   authorized provider evaluation after local GREEN? Recommended: local GREEN
   first; decide provider execution only from the resulting dry-run cost and
   exact panel.
2. **Fidelity gate:** Accept 30 stratified teacher-forced items, at least 24
   human-accepted, and zero critical role-inversion, exact/near-echo, hidden-
   fact, or unauthorized-action failures? Recommended: yes for the first
   calibration checkpoint.
3. **Fixture source:** Use newly authored synthetic HRAI-shaped prefixes derived
   from the owner-authorized historical persona/scenario design, with no private
   canary text in Git? Recommended: yes.
4. **Interaction state:** Accept the six-field bounded episode state in section
   5, or remove any field before tests freeze? Recommended: keep it small and
   allow `UNKNOWN`; do not add free-form emotion memory.
5. **Retry policy:** Should LABS-06 be strictly one attempt in both evaluation
   and generation, or may later generation use one counted regeneration after
   a typed semantic rejection? Recommended for this round: one attempt and
   fail fast everywhere; revisit regeneration only after rejection evidence.
6. **Semantic taxonomy:** One top-level `SIMULATOR_SEMANTIC_INVALID` gap with a
   closed list of defect codes, or separate top-level gaps per defect?
   Recommended: one top-level gap plus explicit defect codes to keep aggregate
   arithmetic stable.
7. **Near-echo rule:** Accept normalized exact containment plus a deterministic
   token-sequence similarity threshold frozen on positive/negative fixtures?
   Recommended: yes; do not use an LLM judge or embedding call for the hard
   gate.
8. **Turn policy ownership:** Confirm that LABS-06 may correct LABS-04 turn-
   policy projections that describe assistant behavior, but only through an
   explicit versioned migration that preserves the old artifacts. Recommended:
   yes.
9. **What do you want from this round:** Is the desired demo outcome a high-
   confidence simulator component ready for LABS-07 report/UI work, or do you
   also expect a new public sample run to be produced in LABS-06? Recommended:
   finish the component and review contract in LABS-06; generate the public
   sample only after LABS-07 freezes its report schema.

## 8. Fail-fast and non-goals

Refuse before editing or egress when:

- owner answers materially change the LLD but are not recorded;
- the fixture would include private canary/HRAI response content;
- turn-policy direction or fact visibility is ambiguous;
- a semantic rule requires an LLM judge to enforce a deterministic invariant;
- near-echo threshold lacks positive and negative fixtures;
- a proposed change touches provider, target connector, report/UI, memory,
  baseline/candidate, real-data, or dependency boundaries outside the frozen
  change budget;
- the independent test and implementation roles are not separated;
- the new implementation would silently retry, repair, or fall back.

Deferred:

- persistent/global memory and learned emotional state;
- model judges and prompt/model tournaments;
- public UI/report work;
- public sample generation;
- real/local-sensitive traces;
- baseline/candidate diff;
- broad provider or agent SDKs;
- live HRAI rerun;
- hosted execution.

## 9. Copyable new-session prompt

```text
Continue Triana from local main after the LABS-05 close and public-rollout
planning merge.

Read AGENTS.md and every authority document it requires, then read:
- internal/LABS06_HANDOFF_2026-08-03.md
- internal/LABS05_SIMULATOR_FIDELITY_REVIEW_2026-08-03.md
- internal/LABS05_REAL_DATA_CANARY_2026-08-03.md
- internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md
- the full internal/DECISION_LOG.md

Ground truth: LABS-04 passed. LABS-05's local adaptive runner and opaque target
connectors are implemented, but its consumed real canary closed unpassed: two
valid distinct trajectories, one partial trajectory, owner rulings Y/N/Y/Y,
and two unavailable review items. R2 exactly copied the preceding HRAI answer
and assumed the assistant role because the simulator request omitted verified
persona/intent/turn-policy context and semantic validation did not reject role
inversion or echoing. Do not rerun the canary or call any provider/target.

This session is for LABS-06 regular-user simulator fidelity. Do not implement
on your first turn. First:
1. inspect the current simulator/runner/contracts/tests;
2. state the goal, exact proposed outcome, scope, and non-goals in plain words;
3. propose a concrete LLD and behavioral/wire spec;
4. enumerate the smallest must-cover edge cases and approximately 8–12
   essential black-box tests—no coverage padding or combinatorial test sprawl;
5. preserve deterministic identity, observation binding, termination, budgets,
   custody, dedupe, privacy, typed gaps, and no retry/fallback;
6. keep persistent/global memory, emotion memory, judges, UI/report,
   baseline/candidate diff, real-data support, generic SDKs, and broad eval
   expansion deferred;
7. ask me every material question listed in the LABS-06 handoff, recommend a
   default for each, and explicitly confirm what I want out of this round;
8. stop and wait for my answers.

After I answer, record accepted durable decisions, replace
internal/SLICE_PACKET.md with a bounded LABS-06 packet, use the independent
orchestrator/test-author/implementation-author protocol, freeze minimal valid
RED, then implement and run the full repository gate. Fail fast on ambiguity,
scope expansion, unapproved egress, private evidence, semantic-validator
uncertainty, retry, repair, or fallback. Do not approve a human fidelity ruling
for me.
```

## 10. Expected first response shape

```text
Goal and intended outcome
What LABS-06 will and will not change
Observed current boundary and supported R2 cause
Proposed LLD
Proposed wire/behavior contract
Authority and privacy table
Fail-fast/refusal behavior
Minimum edge cases and essential tests
Change-budget proposal
Material questions with recommended answers
Explicit statement: no implementation starts until Akarsh responds
```
