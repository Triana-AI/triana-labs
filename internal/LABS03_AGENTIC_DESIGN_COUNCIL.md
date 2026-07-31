# Triana agentic semantic-design council brief

Status: **discussion input only — not product authority or an accepted decision**

Date: 2026-07-31

## Instructions for Claude Code / Fable

Read this entire file and the repository files named under **Authority to
inspect**. Do not edit any other repository file. Perform a skeptical,
doubt-driven architecture council on the question below. Replace only the text
between `CLAUDE_RESPONSE_START` and `CLAUDE_RESPONSE_END` with your response.

Do not assume the founder's proposal is correct. Distinguish accepted repository
decisions, shipped evidence, hypotheses, recommendations, and open owner choices.
Do not propose implementation until the design and falsification experiment are
clear.

Suggested invocation from the repository root:

```bash
claude --model fable
```

Then send:

```text
Read internal/LABS03_AGENTIC_DESIGN_COUNCIL.md completely. Inspect every file
listed in its Authority to inspect section. Perform the requested doubt-driven
design council. Edit no other file. Replace only the content between the
CLAUDE_RESPONSE_START and CLAUDE_RESPONSE_END markers, preserving both markers.
```

## Authority to inspect

Read these files as repository ground truth:

1. `AGENTS.md`
2. `triana-labs/CHARTER.md`
3. `internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`
4. `internal/WORKING_MEMORY.md`
5. the full `internal/DECISION_LOG.md`
6. `internal/SLICE_PACKET.md`
7. `docs/ARCHITECTURE.md`
8. `docs/PROVENANCE.md`
9. `triana-labs/src/triana_labs/contracts/traces.py`
10. `triana-labs/src/triana_labs/intelligence/input.py`
11. `triana-labs/src/triana_labs/intelligence/derive.py`
12. `triana-labs/src/triana_labs/intelligence/publication.py`
13. `triana-labs/src/triana_labs/cli.py`

Authority order remains the Labs charter, append-only decision log, current
Labs plan, then other canonical documents where not superseded. This brief is
not authority.

## Current accepted product direction

- User simulation is in scope. The core future intelligence is a next-turn
  generator grounded in observed corpus behavior.
- Corpus-derived persona, intent, and turn-policy artifacts are planned inputs
  to F1 simulated continuation.
- F0 and F1 are different evidence tiers. F0 freshly executes baseline and
  candidate from the same historical prefix. F1 begins only after divergence
  and is always labeled simulation.
- Diversity is first-class. Raw run count cannot silently substitute for
  effective distinct trajectories.
- An LLM may propose semantic labels, assets, user turns, and explanations. It
  cannot own corpus membership, support counts, identity, pairing,
  comparability, denominators, stability, fidelity, or persistent rulings.
- A human may correct or approve semantic assets and judges realism samples.
- Provider calls require an explicitly named provider, authorized egress,
  redaction before hashing/calls, metering, and hard budgets.
- Initial alpha is bounded to one provider/model and one subprocess agent
  protocol. Universal agent support is not currently promised.

## L3 as currently written

Working-memory hypothesis L3 is:

> F1 generated user continuations are realistic enough to reveal relevant
> post-divergence behavior.

Its smallest useful evidence is a blind or owner-reviewed sample of 30 turns
with a declared acceptance threshold and duplicate-trajectory budget. Its
status is **untested**.

The current plan additionally requires an owner gate before M2C tests for:

- generation model or models;
- realism rubric and pass threshold;
- trajectory representation;
- similarity threshold;
- duplicate budget;
- deduplicate-versus-down-weight policy.

## What LABS-03 actually shipped

LABS-03 is deterministic structural Corpus Intelligence, not semantic
derivation and not simulation.

Command:

```text
triana corpus derive <observer-manifest> --out <new-directory>
```

It verifies the complete synthetic Observer bundle and deterministically groups
validated traces by:

- user and assistant message counts;
- tool-call and tool-result counts;
- ordered safe tool names;
- tool-error and unmatched-call counts;
- terminal state or missing terminal;
- mechanical case-generation eligibility.

It publishes structural clusters, support states, ambiguity/fidelity/lineage,
and explicit `NOT_DERIVED` persona, intent, and turn-policy indexes plus
`NOT_EVALUATED` language and distress gaps.

Evidence:

- implementation commit `7cde8b5`;
- final closure commit `0ea463d`;
- 33 independent acceptance cases;
- four orchestrator adversarial cases;
- 188 total passing tests;
- source and clean-wheel output parity;
- final evidence root `/private/tmp/triana-labs-verify.JjLqlV`;
- all five canonical Observer hashes unchanged.

LABS-03 proves that an Observer bundle can feed a deterministic next component
with exact lineage and honest gaps. It does **not** prove semantic clustering,
persona realism, intent inference, turn policies, user simulation, diversity,
customer grounding, provider safety, or usefulness.

## Founder concern and proposed direction

The founder believes deterministic-only semantic persona derivation will not be
sufficient. The proposed direction is to compare or combine two lanes:

1. a **deterministic provider**; and
2. an **agentic provider** with a real harness, bounded memory, optional
   sub-agents, adversarial review, and the ability to simulate many user and
   situation types.

The founder also expects coding agents such as Codex or Claude Code to perform
well, but asks how Triana supports other agents rather than accidentally
becoming a coding-agent-specific product.

## Ambiguities the council must resolve

### What does “deterministic provider” mean?

Challenge the phrase. Decide whether this lane should be:

- a fixture/rules/retrieval engine with no model call;
- a recorded-response provider with byte-frozen outputs;
- a seeded low-temperature model with repeatability measured rather than
  claimed;
- or something else.

Do not call an external model deterministic merely because temperature is zero
or a seed is supplied.

### What does “agentic provider” own?

Separate at least:

1. offline semantic asset derivation from a corpus;
2. scenario and panel construction;
3. runtime F1 next-user-turn simulation;
4. the runner for the agent under test;
5. evaluation and realism review.

Determine where agents, sub-agents, tools, retrieval, memory, critics, and
humans belong. Prevent the generator from selecting its own evidence,
evaluating itself, or creating accepted truth.

### What memory exists?

Distinguish:

- immutable evidence memory with citations;
- persona and intent state;
- current simulation episode state;
- frozen scenario/world state;
- agent-under-test memory;
- cross-trial memory.

Specify reset and leakage rules. Ambient memory between trials must not become
hidden evidence.

### Which agents can Triana support?

Assess at least:

- ordinary chat agents;
- tool-using API or HTTP agents;
- customer-support agents;
- coding agents such as Codex and Claude Code;
- browser agents;
- voice or multimodal agents;
- persistent-memory agents;
- delegated or multi-agent systems;
- long-running autonomous agents.

The current PreviewTrace contains user, assistant, system-visible, tool-call,
tool-result, and terminal events. It has no explicit child-agent graph, memory
read/write event, artifact mutation event, browser state, audio event, or
general span hierarchy. Decide whether to extend PreviewTrace, add an optional
execution-graph sidecar, or deliberately refuse unsupported agent classes.

## Required doubt-driven analysis

Answer all of the following:

1. State the exact current design decisions for L3 and LABS-03.
2. Give the strongest case that the founder's two-lane proposal is necessary.
3. Give the strongest case that it is premature, misframed, or likely to create
   an expensive eval-platform/swarm abstraction.
4. Identify the most important confounders, including generator/evaluator
   self-bias, same-model correlation, prompt sensitivity, provider drift,
   hidden memory, mode collapse, unsupported persona invention, and false
   determinism.
5. Recommend whether the two lanes should compete, compose, or serve different
   evidence roles.
6. Design the minimum provider-neutral harness contract: inputs, outputs,
   tools/world boundary, state/reset, budgets, retries, lineage, and typed gaps.
7. Design the memory and optional sub-agent model without requiring a provider
   that supports native sub-agents.
8. Define how scenario coverage is chosen deterministically while individual
   user turns may be generated agentically.
9. Define how coding agents and other agent types enter through capability
   declarations and runner adapters rather than brand-specific product logic.
10. List every material claim still unproven after LABS-03.
11. Propose the smallest falsification experiment comparing the lanes on the
    same corpus and situations. Include sample sizes, blind review, diversity,
    repeatability, cost, latency, and leakage measurements.
12. Give explicit stop, narrow, and go gates.
13. End with no more than seven owner decisions that must be frozen before an
    implementation slice begins.

## Response format

Use these sections:

1. Executive verdict
2. Current decisions versus shipped evidence
3. Strongest case for and against the proposal
4. Recommended architecture and ownership
5. Provider lanes
6. Harness, memory, and sub-agents
7. Support for different agent classes
8. Unproven claims and failure modes
9. Falsification experiment
10. Stop / narrow / go gates
11. Owner decisions required
12. Confidence and dissent

Be concrete. Prefer typed contracts, decision tables, and falsifiable claims to
generic agent-framework language. Do not write implementation code.

## Claude / Fable response

<!-- CLAUDE_RESPONSE_START -->

Council conducted 2026-07-31 by Claude Code (Fable) with Akarsh live in the
loop. Owner selections recorded below were made interactively during this
council. This file remains discussion input; each selection still requires an
append-only `internal/DECISION_LOG.md` entry before any implementation slice
freezes tests against it.

## 1. Executive verdict

The founder's instinct is correct and the framing is wrong in one specific
way. Deterministic-only semantic persona derivation is indeed insufficient —
a no-model lane can only ever restate observable structure, which is exactly
what LABS-03 shipped and honestly labeled `NOT_DERIVED`. But the proposal's
implied shape — two peer providers competing to produce semantic truth — would
re-litigate the already-accepted authority map and risk building an
eval-platform/swarm abstraction before a single semantic asset has been judged
useful.

The resolved design, accepted by the owner in this council, is **compose, not
compete**: the deterministic lane is the evidence substrate and gate (corpus
membership, structural clusters, support counts, citation validation,
identity, budgets); the agentic lane is the only semantic proposer, built as a
**Triana-owned bounded agent loop over plain provider API calls** — never a
brand-specific coding-agent dependency. The one legitimate open empirical
question is whether an agentic multi-step loop (propose → critic → revise)
produces better-grounded assets than a single LLM call. That question gets a
small falsification experiment (≤ USD 50, owner-blind 30-item review) before
any harness abstraction is built out.

Agent-under-test scope stays unchanged: conversational, tool-using agents
only. The harness and trace contracts are designed capability-neutral so
coding, browser, and other agent classes can be admitted later by decision,
not by accident.

## 2. Current decisions versus shipped evidence

Accepted decisions (charter, decision log, plan) relevant here:

- User simulation in scope; next-turn generator is the core intelligence
  (decision log 2026-07-31, charter scope 1).
- Diversity is first-class; raw N never substitutes for effective distinct N.
- Authority map (plan §5): deterministic code owns membership, support,
  identity, pairing, denominators, comparability, stability, fidelity;
  LLM may propose semantic labels, assets, turns, explanations; human
  corrects/approves and judges realism samples.
- F0 = shared-prefix resampling; F1 = labeled simulated continuation.
- Provider calls require named provider, authorized egress, redaction before
  hashing/calls, metering, hard USD 50/panel cap.
- Alpha bounded to one provider/model, one subprocess protocol; universal
  agent support explicitly not promised; coding/batch/research agents refused
  as inputs (plan §3.2, decision log 2026-07-30 narrowing).
- L3 hypothesis: "F1 generated user continuations are realistic enough to
  reveal relevant post-divergence behavior." Status untested; smallest
  evidence = blind/owner-reviewed sample of 30 with declared threshold and
  duplicate budget. M2C owner gate covers model, rubric, thresholds,
  trajectory representation, dedup policy.

Shipped evidence (LABS-03, commits `7cde8b5`/`db91380`/`0ea463d`): a
deterministic structural clusterer over validated Observer bundles. It proves
byte-exact lineage, integrity verification, atomic publication, honest typed
gaps, and that the Observer bundle feeds a next component. It proves nothing
semantic: no persona, intent, turn policy, language, distress, realism,
diversity, customer grounding, provider safety, or usefulness. The gap
between "accepted direction" and "shipped evidence" is therefore the entire
semantic layer, and every design below must be judged against that gap, not
against the ambition.

## 3. Strongest case for and against the proposal

**Strongest case for the two-lane direction.** Structural fingerprints
(message counts, tool-name sequences, terminal state) cannot distinguish "user
politely asks for a refund" from "user threatens legal action" when both
produce the same event shape. Personas, intents, and turn policies are
irreducibly semantic; no rules engine derives them without a model. A single
one-shot LLM call over a cluster has known failure modes the repo already
anticipates: unsupported persona invention (edge-case register 9.2), mode
collapse in generated variety (9.6), and no self-check before output. An
agentic loop with a separate critic pass, explicit evidence reading, and
citation discipline is the natural mitigation, and the repository's role
protocol (independent test author vs implementation author vs orchestrator)
already demonstrates that adversarial separation catches real defects — five
times in the decision log. A bounded memory and sub-agent design also
future-proofs F1, where multi-turn simulation genuinely needs episode state.

**Strongest case against.** Three arguments. First, prematurity: not one
semantic asset has ever been produced or judged; building a two-lane
comparison platform before knowing what a *good* persona artifact looks like
optimizes machinery over evidence, the exact failure the Braintrust dogfood
punished. Second, misframing: "deterministic provider" for semantics is a
category error — a seeded temp-0 model is not deterministic (provider drift,
serving nondeterminism), and calling it so would violate the repo's own
honesty rules; a genuinely deterministic lane can only produce what LABS-03
already produces. The lanes as originally framed are therefore not peers and
cannot "compete" on the same output type. Third, cost gravity: harnesses,
sub-agents, adversarial review panels, and cross-trial memory are the
standard opening moves of every generic eval/agent platform; the plan's
non-goals (§16) exist precisely to keep Triana from becoming one. If the
agentic loop cannot beat one LLM call under blind review, every dollar spent
on the harness is negative.

The council resolves this tension by keeping the *architecture* decision
(compose) and shrinking the *investment* decision to one cheap experiment.

## 4. Recommended architecture and ownership

Owner-accepted in this council: **compose**. The two lanes are layers, not
competitors.

| Function | Deterministic code owns | Agentic provider (Triana loop + LLM) | Human owns |
|---|---|---|---|
| Corpus membership, structural clusters, support counts | all (shipped) | nothing | nothing |
| Evidence bundle addressing and citation validation | all | nothing | nothing |
| Semantic asset proposal (persona, intent, turn policy) | schema, identity, lineage, budget, gap typing | drafts content with mandatory trace citations | corrects, approves, may reject |
| Scenario/panel coverage | selects which situations (seeded, stratified, from clusters) | writes turn text and variants inside selected slots | approves panel contract |
| F1 next-turn generation (later, M2C) | boundary, budget, lineage, diversity arithmetic | generates the turn | judges realism sample |
| Evaluation of lane quality | blinding, sampling, arithmetic | nothing — never judges itself | owner-blind review verdict |
| Persistent truth | storage/identity only | nothing | creates rulings |

Three structural rules prevent the generator from selecting its own evidence
or creating truth:

1. **Citation gate.** Every semantic claim in a proposed asset must cite
   trace IDs and event ranges from the immutable evidence bundle.
   Deterministic code verifies each citation exists, belongs to the named
   structural cluster, and meets a minimum support count. A proposal with an
   invalid citation is rejected with a typed gap, never silently trimmed.
2. **Proposal state.** Every agentic output is born `PROPOSED` with fidelity
   and provenance labels. Nothing the loop emits can reach `ACCEPTED` without
   a human action; `PROPOSED` assets may drive labeled F1 simulation but are
   displayed as hypotheses, never as customer truth.
3. **No self-evaluation.** The critic inside the loop improves drafts; it
   produces no score that survives into evidence. Lane quality is judged only
   by the owner-blind review defined in §9.

## 5. Provider lanes

**Deterministic lane (owner-selected meaning: no-model rules/retrieval
engine).** No provider call, ever. It owns everything LABS-03 owns today,
extended with: citation indexing over normalized traces, deterministic
coverage/strata selection for scenarios, near-duplicate arithmetic, and
validation of agentic outputs. Its outputs remain fully repeatable and are
the only artifacts allowed to carry the word "deterministic." Explicit
council ruling: a seeded or temperature-0 model call is **never** labeled
deterministic; recorded/frozen model outputs are labeled
`RECORDED_MODEL_OUTPUT` with the recording's provider identity and date, not
deterministic either.

**Agentic lane (owner-selected form: Triana-built agent loop).** A bounded,
Triana-owned orchestration over plain provider API calls through the already
planned OpenRouter-compatible boundary. No dependency on any coding-agent
product; "sub-agents" are additional bounded calls with distinct role prompts
that Triana's deterministic loop code sequences. Provider-neutral by
construction: swapping providers changes one adapter and the comparability
fingerprint, nothing else. All calls pass the plan §6.2 order of operations
(authorize → redact → validate egress → hash → budget → call → meter).

Evidence roles: deterministic-lane outputs are citable structural evidence.
Agentic-lane outputs are labeled proposals/hypotheses. The report may never
collapse the two, matching the existing fidelity-label rule.

## 6. Harness, memory, and sub-agents

Minimum provider-neutral harness contract (typed, to be frozen field-exact in
the slice packet):

- **Inputs:** task kind (`DERIVE_PERSONA | DERIVE_INTENT | DERIVE_TURN_POLICY
  | GENERATE_SCENARIO_TURN | GENERATE_F1_TURN`); evidence bundle reference
  (intelligence `manifest.json` hash — the loop may read only artifacts that
  hash-chain to it); frozen prompt-pack version; provider identity (name,
  endpoint, model, key reference); budgets (max provider calls, max
  input/output tokens, max USD, max wall-clock); seed where the provider
  accepts one (recorded, not trusted for determinism).
- **Outputs:** proposed assets with citations; a complete append-only call
  ledger (per call: role, prompt hash, model, token counts, provider-reported
  cost, refusal state); metering totals; typed gaps
  (`INSUFFICIENT_SUPPORT | CITATION_INVALID | BUDGET_EXHAUSTED |
  PROVIDER_REFUSED | PROVIDER_UNAVAILABLE | EMPTY_PROPOSAL`).
- **Tools/world boundary:** the loop's only capabilities are (a) read
  citation-addressed evidence, (b) call the named provider, (c) emit
  proposals. No filesystem writes outside its working directory, no network
  beyond the named endpoint (negative tests, as in LABS-03's socket-blocked
  adversarial cases), no ambient config discovery.
- **State/reset:** episode state (drafts, critic notes, working memory) is
  explicit, bounded, and destroyed at run end. Retries append new call
  entries; nothing is replaced in place.
- **Lineage:** every published proposal binds input manifest hash, prompt
  pack hash, provider identity, call-ledger hash, and harness version.

Memory model, per the brief's six categories:

| Memory | Backing | Write authority | Reset rule |
|---|---|---|---|
| Immutable evidence | Observer + intelligence bundles, hash-addressed | none (read-only) | never; superseded by new derivation runs |
| Persona/intent state | versioned published asset files | deterministic publication only, from validated proposals | new version = new identity; append, never mutate |
| Simulation episode state | in-run harness scratch | the loop, within budget | destroyed at episode end; never cited as evidence |
| Frozen scenario/world state | versioned fixture artifacts | human/orchestrator via slice contract | identity-bearing; change = new fingerprint |
| Agent-under-test memory | customer runner's own state | customer | declared in the comparability fingerprint; reset per the declared reset policy |
| Cross-trial memory | forbidden except published versioned artifacts | n/a | any other carry-over between trials is leakage |

**Leakage rule:** the only lawful information paths into a proposal are the
evidence bundle, the frozen prompt pack, and declared configuration. Any
other path (a previous trial's episode state, an unhashed local file, a
provider-side cache surfacing prior content) invalidates the artifact with a
typed integrity failure. This is testable: rerun with a fresh process and an
empty working directory; outputs may differ only by declared provider
nondeterminism.

**Sub-agents without native support:** a sub-agent is one more harness
invocation with a role prompt (`PROPOSER | CRITIC | REVISER`) and a budget
slice, sequenced by deterministic loop code. This works on any provider that
can complete a chat request. The critic emits typed objections
(`UNSUPPORTED_CLAIM | MISSING_CITATION | DUPLICATE_OF | INCOHERENT`); the
deterministic loop decides routing (revise or emit with gaps). No provider
feature beyond plain completion is ever required.

**Scenario coverage (deterministic) versus turn generation (agentic):**
coverage is chosen by seeded, stratified selection over structural clusters
and declared strata — which situations, how many per stratum, which
prefixes — exactly the Panel Builder contract already planned (M1C).
The agentic lane fills the selected slots with turn text and persona
variants. Deduplication and effective-N arithmetic over the filled panel
remain deterministic. The generator therefore never chooses its own
distribution.

## 7. Support for different agent classes

Owner ruling in this council: **scope unchanged** — conversational,
tool-using agents only for the alpha; no decision-log change to admit coding
agents as inputs. The design obligation is neutrality, met by two contracts:

1. **Capability declaration** (per agent under test, validated
   deterministically): event kinds producible (maps to the closed
   PreviewTrace vocabulary), tool observability (names/args/results
   observable or not), terminal observability, reset capability, memory
   persistence across episodes (must be declared; enters the comparability
   fingerprint), child-agent delegation (yes/no), modality (text-only for
   alpha). An agent whose declaration needs event kinds PreviewTrace lacks
   (artifact mutation, browser state, audio, span graphs) is refused with a
   typed `UNSUPPORTED_CAPABILITY` reason — an honest gap, not a silent
   partial ingest.
2. **Runner adapter contract**: the subprocess protocol (M2A, already gated)
   keyed by capability declaration, never by product brand. "Codex support"
   or "Claude Code support" as product logic must not exist; only
   capabilities and adapters exist.

PreviewTrace extension versus execution-graph sidecar: **defer**. Do not
extend PreviewTrace speculatively. When a concrete second agent class is
admitted by decision-log entry, choose then between a `schema_version: 2`
trace or an optional sidecar; the refusal path above keeps the boundary
honest meanwhile. Coding agents are noted as a *plausible future class*
(their transcripts are conversational and tool-ordered; their gap is
artifact-mutation and child-agent visibility), which is exactly why the
capability declaration includes those two axes now.

## 8. Unproven claims and failure modes

Material claims still unproven after LABS-03:

1. Semantic clustering validity — structural clusters correspond to
   semantically coherent behavior groups (untested).
2. Persona/intent/turn-policy derivability — any lane can produce assets a
   human accepts (untested; no asset has ever existed).
3. L3 — F1 continuations realistic enough to reveal relevant behavior
   (untested).
4. Diversity control works — effective-N measurement plus dedup policy
   prevents silent trajectory convergence (untested).
5. Customer grounding — everything so far is synthetic; no real-data,
   redaction, or egress path exists (unbuilt).
6. Provider safety machinery — the §6.2 fail-closed pipeline exists on paper
   only (unbuilt).
7. Agentic benefit — the multi-step loop beats one LLM call on grounded
   usefulness (untested; this council's experiment).
8. L1/M3.5 — a stranger reaches a report in 90 minutes / ≤200 adapter lines
   (untested).
9. L2/L4/L6 — usefulness versus existing process, versus a DIY frontier
   agent, and market pull (untested).

Most important confounders for the experiment and the lanes:

- **Generator/evaluator self-bias:** eliminated for lane judging by
  owner-blind review; inside the loop the critic's opinions never become
  evidence.
- **Same-model correlation:** running both lanes on the same provider/model
  is deliberate — it isolates the harness effect. The cost: results say
  nothing about model choice; that is a separate, later question.
- **Prompt sensitivity:** prompt packs are hashed and frozen before the
  experiment; a prompt edit is a new experiment identity. One frozen pack per
  lane; no mid-run tuning.
- **Provider drift:** record model identity, endpoint, and dates; run both
  lanes and both repeats inside the smallest practical window; repeatability
  is *measured* and reported, never assumed.
- **Hidden memory:** fresh process and empty working directory per run;
  cross-run convergence beyond declared nondeterminism is investigated as
  leakage, not accepted as stability.
- **Mode collapse / unsupported invention:** measured by the duplicate
  metric and blocked by the citation gate respectively.
- **False determinism:** terminology rule in §5 is binding; tests must assert
  no artifact labels a model output deterministic.

## 9. Falsification experiment

Name: **LABS-EXP-SEM-01 — single-call versus agentic semantic derivation.**
Runs inside the M1B semantic checkpoint's entry work; requires its own slice
packet and the standard role protocol before any code.

- **Corpus:** one synthetic corpus at alpha scale (25–100 traces) through the
  existing adapter → Observer → structural-intelligence path, so both lanes
  consume the same hash-verified evidence bundle. Same corpus, same clusters,
  same prompts-freeze date for both lanes.
- **Lanes:** A = one LLM call per structural cluster per asset kind
  (persona, intent). B = Triana loop, ≤ 6 calls per cluster per asset kind
  (propose → critic → revise, budget-enforced). Same provider and model for
  both; provider named per §6.3 before any call.
- **Deterministic pre-filter:** schema validation and citation-gate checks
  run on every output; `CITATION_INVALID` and `EMPTY_PROPOSAL` rates are
  recorded per lane before human review (a lane can lose here outright).
- **Blind review (owner-selected):** Akarsh rates 30 blinded assets —
  stratified evenly across lanes and clusters, order shuffled by recorded
  seed, lane identity stripped — against a rubric frozen *before* generation.
  Rubric axes (freeze exact wording in the packet): grounded (claims
  supported by cited traces), coherent (a usable behavioral description),
  distinct (not a duplicate of another asset), simulation-ready (could drive
  a next-turn generator). Pass threshold declared before unblinding.
- **Diversity:** near-duplicate rate and effective distinct-asset count per
  lane, computed deterministically with a declared similarity method and
  threshold.
- **Repeatability:** each lane runs twice; report asset-level agreement
  between repeats per lane (measured stability, not claimed determinism).
- **Cost/latency:** full call ledger and metering per lane; hard cap
  **USD 50 total** for the whole experiment (owner-selected); the harness
  stops calls at the cap and reports partial evidence with typed gaps.
- **Leakage checks:** network guard permitting only the named endpoint;
  fresh-process/empty-workdir reruns; no evidence file outside the bundle
  readable by the loop.

Primary falsifiable claim: *lane B's blinded pass rate exceeds lane A's by a
margin the owner pre-declares as worth the cost multiple, without losing on
diversity or citation validity.* If not, the agentic harness is not built
beyond the minimal loop used in the experiment.

## 10. Stop / narrow / go gates

- **STOP (do not build the agentic harness abstraction):** lane B fails to
  beat lane A on the pre-declared blinded margin, or exceeds budget, or shows
  higher `CITATION_INVALID`/duplicate rates. Consequence: semantic derivation
  proceeds with the single-call proposer under the same citation gate;
  harness ambitions are shelved with this evidence recorded.
- **STOP (both lanes fail):** neither lane clears the rubric threshold.
  Consequence: semantic derivation is not evidence-ready on synthetic data;
  the next work is the real-data/redaction/egress boundary (the working
  memory's named next decision), not more generation machinery.
- **NARROW:** lane B wins on quality but breaches cost/latency bounds, or
  wins on personas but not intents. Consequence: adopt lane B only where it
  won; cap loop depth; re-run the losing asset kind under lane A.
- **GO:** lane B clears margin, diversity, citation, and budget gates.
  Consequence: freeze the harness contract (§6) field-exact in the next
  slice packet; carry the same contract forward as the basis for M2C F1
  generation and its separate owner gate.
- **Cross-cutting stops (any time):** leakage detected → invalidate artifacts
  and halt; any artifact labels a model output deterministic → slice-blocking
  defect; unstable deterministic-lane clustering on identical input → already
  slice-blocking per edge-case register 9.2.

## 11. Owner decisions required

Decided in this council (2026-07-31, Akarsh; require decision-log entries
before the implementing slice freezes tests):

1. Lane relation is **compose**; scope of the two-lane question is offline
   asset derivation, scenario/panel construction, and runtime F1 — not
   evaluation, which stays with the human.
2. "Deterministic provider" means a **no-model rules/retrieval lane**; model
   outputs are never labeled deterministic.
3. The agentic provider is a **Triana-built bounded loop over plain provider
   API calls**; sub-agents are orchestrated bounded calls, no coding-agent
   product dependency.
4. Lane quality is judged by **owner-blind review of 30 items** against a
   pre-frozen rubric.
5. Experiment budget is **≤ USD 50 total**, hard-capped.
6. Agent-under-test scope is **unchanged** (conversational, tool-using);
   neutrality is delivered through capability declarations and runner
   adapters; PreviewTrace extension is deferred until a second class is
   admitted by decision.

Remaining, must be frozen before the experiment slice's tests:

7. The composite experiment freeze: exact rubric wording and pass threshold,
   pre-declared lane-B victory margin, named provider + model + endpoint,
   the specific synthetic corpus, prompt-pack contents, similarity method +
   duplicate threshold, and minimum citation support count.

## 12. Confidence and dissent

High confidence: the category error in "deterministic semantics" (this is
definitional, not empirical); compose over compete given the accepted
authority map; the citation gate as the single most important control against
persona invention; deferring trace-contract extension.

Moderate confidence: that ≤ 6 calls/cluster is the right loop bound (chosen
for the USD 50 cap, not from evidence); that owner-blind review of 30 items
has enough statistical power to detect a modest lane difference — it matches
the L3 evidence bar, but a small margin may be indistinguishable from rater
noise, in which case the tie correctly goes to the cheaper lane.

Dissent worth preserving: a reasonable council member would argue the
experiment itself is premature — that the single-call proposer should simply
ship first behind the citation gate, and the agentic question should wait for
evidence that its outputs fail in practice. The counterargument that carried:
the experiment costs at most USD 50 and one owner review session, uses
machinery M1B needs anyway (prompt pack, provider boundary, citation gate),
and settles by falsification a question that would otherwise be re-litigated
by intuition on every future slice. If even USD 50 of provider spend is
premature before the redaction/egress layer exists, the honest fallback is
the dissent position: ship lane A first, keep this design on file.

<!-- CLAUDE_RESPONSE_END -->
