# LABS-05 simulator-fidelity review and next north-star eval

Date: 2026-08-03

Status: **OWNER DIRECTION RECORDED; NEXT IMPLEMENTATION SLICE NOT YET FROZEN**

This document records what the one authorized HRAI run taught Triana, why one
generated turn failed, the relevant HRAI benchmark, and the smallest eval that
should guide the next simulator slice. It does not authorize another provider
run, general real-data support, or persistent/global Triana memory.

## 1. Outcome and owner ruling

The private canary attempted three episodes. Two were valid and distinct; one
was partial after a strict simulator response failure. Akarsh ruled on every
available adaptation item:

| Item | Ruling | Meaning |
|---|---:|---|
| R1 | Y | The user escalated in response to the target refusal. |
| R2 | N | The generated user turn copied the target answer and assumed the assistant role. |
| R3 | Y | The user challenged a contradiction and requested the disputed raw fields. |
| R4 | Y | The reviewer accepted termination for this checkpoint, while noting that N would also be reasonable because `:done:` is protocol-like. |

The result is 3/4 accepted available items, two unavailable items, and only two
valid distinct trajectories. LABS-05 does not pass `LABS05_ADAPTATION_V1`.

## 2. Why R2 repeated HRAI

R2 was an exact echo, not merely a similar answer. The generated turn and the
immediately preceding HRAI response were both 1,553 characters and matched
byte-for-byte.

The cause is a contract defect at the LABS-04/LABS-05 boundary:

1. LABS-04 produced a verified case, persona, intent, and turn-policy
   projection.
2. LABS-05 made all four available to the target connector as case context,
   but sent only the case, transcript, latest observation, and remaining-turn
   count to the user simulator.
3. The simulator system instruction was only: `react only to the latest
   bounded evidence`.
4. The strict response schema checked JSON fields, types, and observation-hash
   binding. It did not check that the text remained in the user role, expressed
   the persona, advanced the intent, or avoided copying the assistant.
5. With temperature zero and the full target response as the most recent large
   text, the model could satisfy the JSON contract while copying that response.

The failed context-recovery U3 is different. Its Azure request succeeded, but
the returned object failed the strict structural response contract. The raw
invalid response was deliberately not retained, so no narrower semantic cause
is supportable from the evidence.

## 3. What the existing HRAI corpus already did well

The local HRAI historical-traffic experiment is the best current benchmark:

- plan:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/EXPERIMENT_PLAN.md`
- persona archetypes:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/personas.json`
- richer recruiter identities:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/recruiter_identities.json`
- conversation-style profile:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/conversation_style_profile.json`
- 200 frozen scenarios:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/scenarios_200.jsonl`
- realized report:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/out/run_200/REPORT_200.md`
- readable conversations:
  `/Users/akarshgajbhiye/Documents/hr_ai/experiments/historical_traffic_v0/out/run_200/CONVERSATIONS_200.md`

Its persona set covers terse high-volume, careful evidence-seeking, hurried,
nontechnical, typo/informal, skeptical, recruiting-ops, and adversarial users.
Only 20 of 200 scenarios were in the security family; regular operational use
was the majority. That is the right product direction: ordinary usage is the
primary distribution, while angry, impatient, skeptical, mistaken, informal,
and adversarial behavior are controlled strata rather than the generator's
default voice.

The HRAI design also separated deterministic scenario truth from natural-
language realization. Fixed facts, known/hidden facts, authorized reaction,
correction order, stop conditions, and turn budget were controller-owned. The
LLM rendered one next user message. A split validator hard-rejected hidden-fact
leakage, fixed-fact violations, and unauthorized tool instructions while
allowing ordinary human messiness such as terseness, typos, impatience,
rudeness, and false beliefs.

## 4. North-star eval: `REGULAR_USER_SIMULATION_FIDELITY_V1`

The primary eval should answer one question:

> Given the same conversation prefix, latest agent observation, grounded user
> persona, intent, known facts, and user-owned turn policy, does Triana produce
> the next turn that a plausible user of that kind would make?

It should not primarily measure adversarial success or reward longer
conversations. Use two evidence lanes.

### Lane A — teacher-forced next-turn fidelity (primary)

Build a held-out, reviewable panel of regular-use HRAI conversation prefixes.
At each selected prefix, hide the next real or pre-frozen user reaction and ask
the simulator for exactly one turn. Evaluate:

- user-role correctness;
- material reaction to the latest agent answer;
- persona and voice consistency;
- intent progress or natural abandonment;
- consistency with known facts and no hidden-fact leakage;
- natural correction, clarification, impatience, or stopping behavior;
- no exact or near-copy of any assistant turn;
- no invented tool instructions outside the user policy.

Initial checkpoint proposal: 30 stratified items, at least 24 human-accepted,
with zero assistant-role inversions, exact/near echoes, hidden-fact leaks, or
unauthorized actions. The 24/30 threshold is a small launch criterion to
calibrate with human review, not a universal quality claim.

### Lane B — free-running episode fidelity (secondary)

Run the same simulator adaptively against an opaque target for multiple turns.
Measure complete/partial episodes, typed gaps, persona drift, stop correctness,
distinct trajectory rate, repeated-turn rate, and whether later user turns
consume the latest observation. This lane catches feedback-loop failures but
does not replace Lane A because target behavior makes attribution harder.

### Distribution report

Report results by ordinary task family and persona stratum. Never silently
upweight adversarial cases. Show the declared mix, realized mix, per-stratum
acceptance, exact/near-duplicate rate, and trajectory diversity. HRAI's 200-case
mix is a useful benchmark, not automatically the final Triana customer mix.

## 5. Smallest repair before another live run

The next slice should remain a simulator-fidelity repair, not a broad eval
platform:

1. Send the verified persona, intent, and a **user-owned** turn policy in every
   simulator request.
2. Correct any LABS-04 turn policy that describes what the assistant should do;
   it must instead describe the user's allowed reactions, disclosures,
   corrections, escalation, patience, and stopping rules.
3. Strengthen the simulator instruction: remain the user, emit exactly one
   natural user utterance, do not answer as the assistant, do not copy or
   paraphrase the assistant, and use `proposed_stop` rather than a visible
   protocol token when ending.
4. Deterministically reject exact and near assistant echoes, user/assistant role
   inversion, hidden-fact leakage, and unauthorized actions as typed
   `SIMULATOR_SEMANTIC_INVALID` evidence.
5. Do not silently repair an evaluated item. A generation workflow may permit
   one separately counted regeneration, but the original rejection remains
   evidence; an evaluation workflow fails that item without fallback.
6. Test Lane A locally before requesting any new live episode authorization.

## 6. Memory boundary

No persistent/global Triana memory is required for this eval.

- Case memory: immutable persona, intent, facts, and user turn policy.
- Episode memory: the current transcript and latest target observation.
- Target memory: whatever the external agent owns; it is target behavior and
  may itself be evaluated, but Triana must not treat it as simulator memory.
- Persistent/global Triana memory: still deferred. A future feature may propose
  lessons from reviewed failures such as R2, but only a human-confirmed ruling
  may promote them across runs.

This keeps the next checkpoint about faithful adaptive user simulation rather
than quietly turning Triana into a self-modifying global-memory system.
