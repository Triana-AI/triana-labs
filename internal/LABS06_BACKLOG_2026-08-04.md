# LABS-06 accepted backlog and evaluation debt

Date: 2026-08-04

Status: **REQUIRED DEFERRED WORK; NOT A LABS-06 REOPENING**

LABS-06 is closed as `CLOSED_WITH_ACCEPTED_BACKLOG`. This register preserves
the deferred defects, tests, and evaluation work that closure did not erase.
Items here do not retroactively invalidate owner acceptance of Conversations
3 and 4, and they do not authorize a provider, target, real-data, or paid run.
They must be resolved before the broader claim named for each section.

## A. Behavior defects observed in the final live evidence

### A1. Claimed world mutation without authority

Observed evidence: Conversation 4 claimed an uploaded file that was not a
bound Case data item or newly observed target fact. Conversation 7 invented a
person, position, paths, and URL.

Required future behavior: a simulated user may claim a world mutation only
when the mutation is bound in the accepted world projection or has become an
authorized observation during the current conversation. Do not hard-code a
list of file actions; enforce generic world-mutation authority.

Minimum future evaluation:

- bound mutation is accepted;
- newly observed authorized mutation is accepted;
- unbound upload/person/position/path/URL claim is rejected as a typed
  simulator gap; and
- rejection causes no target call, retry, repair, fallback, or hidden state
  change.

### A2. Intent precondition preservation

Observed evidence: one partial trajectory advanced into a downstream action
while contradicting its verification-before-action intent.

Required future behavior: explicit intent preconditions remain active until
the transcript contains the required evidence. Persona style cannot override
the intent's action order.

Minimum future evaluation:

- required verification absent blocks downstream action;
- verification present permits the declared action;
- ambiguous verification remains a typed gap; and
- a target suggestion does not silently rewrite the user's intent.

### A3. Aggregate deadline and target readiness

Observed evidence: four conversations did not start before the 600-second
aggregate deadline; separate target protocol/tool-budget failures affected
other episodes.

Required future behavior: use a recommended 1,800-second aggregate deadline
for a future twelve-case run while preserving existing per-call deadlines and
zero retry. Report target protocol/tool-budget readiness separately from
simulator fidelity. Do not attribute a timeout to network quality without
technical evidence; owner context may be displayed as context only.

## B. Simulator population-fidelity evaluation debt

The former 30-item/24-accepted/zero-critical panel is optional calibration,
not a LABS-06 exit gate. It or a superseding frozen benchmark is required
before a population-level fidelity claim.

The benchmark must keep three lanes separate:

1. simulator validity — role, facts, policy, world, and stopping contract;
2. simulator behavioral fidelity — similarity to held-out human or authorized
   real-user behavior; and
3. target-agent outcome — goal completion and applicable policy compliance.

Required measured dimensions:

- fact front-loading;
- information released per turn;
- clarification behavior;
- repetition;
- pushback and response to agent error;
- recovery versus abandonment;
- turn length and conversation length;
- realism across ordinary, angry, impatient, skeptical, informal, mistaken,
  and adversarial strata; and
- cross-dimension regressions after any prompt/model change.

Calibration must use the same tasks and same target agent for simulated and
held-out human or authorized real-user interactions. It must measure a
human-human ceiling and report communication style, information pattern,
clarification, error reaction, and outcome calibration separately. A model
judge is optional, identity-recorded, dimension-specific, human-calibrated,
and never authoritative.

## C. Trace-to-population and case-quality evaluation debt

- Build deterministic corpus-scale feature extraction and clustering suitable
  for large corpora; model summaries occur only after membership freezes.
- Evaluate semantic user-need population quality without giving the model
  membership, support, traffic-share, or identity authority.
- Calibrate persona, intent, turn-policy support and ambiguity.
- Build a representative retrieval-quality set.
- Evaluate material relevance of model-authored clarification questions.
- Calibrate human case usefulness.
- Measure exact and near duplication for cases, user turns, and trajectories,
  with explicit effective N and threshold/version lineage.
- Cover small, homogeneous, multilingual, code-switched, and missing-user-turn
  corpora without inventing populations.

## D. Accounting, custody, and failure-path evaluation debt

- Verify HTTP-level model-call, token, cached-token, and cost accounting across
  agent loops.
- Keep logical invocation count distinct from actual HTTP exchanges.
- Preserve normalized trustworthy usage even when semantic content is later
  rejected.
- Test target-internal telemetry only when the target reports it; otherwise
  preserve typed unavailable evidence.
- Test target state isolation and retain uncertainty when it cannot be proven.
- Preserve all partial, unavailable, not-started, circuit-blocked, and
  budget-exhausted episodes in denominators.
- Retain original failed attempts; never replace them with successful reruns.

## E. Minimum edge families for the eventual hardening slice

This is a backlog inventory, not a frozen test matrix. A future slice should
select the smallest black-box set that covers its accepted behavior from:

- role inversion and exact/near assistant echo;
- hidden-fact leakage and fixed-fact conflict;
- unbound versus bound world mutation;
- intent precondition absent, present, and ambiguous;
- authorized versus unauthorized reaction/action;
- malformed structured output and invalid stopping companions;
- structured natural stop after goal satisfaction;
- cross-episode state leakage;
- duplicate trajectory convergence;
- timeout before start versus timeout after observed turns;
- target protocol failure versus simulator invalidity;
- target tool-budget exhaustion;
- trustworthy usage attached to rejected content;
- privacy-first refusal before persistence or egress; and
- preservation of no retry, repair, fallback, redirect, proxy, or provider
  switching.

Do not turn this list into coverage padding or a combinatorial matrix. Each
future slice freezes only the cases necessary for the specific accepted
behavior it implements.

## F. Claim gates

| Desired future claim | Backlog that must clear first |
|---|---|
| One turn obeys declared simulator contract | Deterministic validity gates and focused regressions |
| Multi-turn simulation works mechanically | Already demonstrated for the bounded LABS-06 claim |
| Simulator is realistic for a population | Frozen held-out calibration, human ceiling, and dimension results |
| Cases represent observed user needs at corpus scale | Deterministic semantic population pipeline and calibrated summaries |
| Agent succeeds under simulated users | Separate outcome evaluation and human authority |
| Twelve-case run is operationally reliable | Longer aggregate deadline plus target protocol/tool-budget readiness |

## G. Ownership and scheduling

- These items are carried into the LABS-07/08 report as visible limitations,
  not silently fixed by UI copy.
- They do not block the bounded public proof when its claims remain narrow.
- A later simulator-hardening slice must replace `internal/SLICE_PACKET.md`,
  use independent acceptance and implementation authors, and freeze an exact
  change budget.
- Any live validation requires a separately named provider/target/data bundle,
  custody path, egress statement, and cost ceiling.
