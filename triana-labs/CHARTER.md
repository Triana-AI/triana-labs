# Triana Labs charter

Date: 2026-07-31
Status: **active build authority for Triana Labs surfaces**
Owner: Akarsh

## What this document is

The governing specification for Triana Labs work. It exists because the
suspended V1 specification (`docs/PRODUCT.md`) and Labs cannot share one
frozen boundary. Precedence for Labs work: this charter → the append-only
`internal/DECISION_LOG.md` → the current canonical execution plan
(`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`). Repository governance
(`AGENTS.md`, provenance ledger, decision-memory hooks) applies unchanged.

## Narrative (owner-frozen)

> Triana Preview takes your production traces, builds a grounded case panel
> from observed reference behavior and failure signals, mixes shared-context
> resampling with labeled expansion, runs your baseline and candidate on the
> same panel, and reports ranked divergences — including behaviors your evals
> never covered — with every claim backed by a paired transcript and every
> non-claim labeled. Confirmed findings become must-checks for the next run.

## Immediate launch cut (owner-frozen, 2026-08-01)

For the first public developer preview, the value moment is narrower and
supersedes the immediate baseline/candidate sequence above without erasing the
longer-term comparison product:

> Supply authorized conversational traces; Triana derives grounded proposed
> user personas and behaviors, synthesizes a diverse panel of new situations,
> runs genuinely adaptive multi-turn conversations against one existing
> conversational/tool agent, and returns inspectable transcripts, coverage,
> cost, fidelity, and uncertainty. Reviewed local evidence compounds into the
> next run.

This mode is labeled `GENERATED_MULTI_TURN_SIMULATION`. It is not F0 or F1,
does not compare baseline and candidate, and cannot make regression, release,
or accepted-behavior claims. The launch remains local-first and initially
synthetic-only. A model may propose personas, cases, turns, rubrics, and memory;
deterministic code owns identity, support, lineage, selection, duplicate
arithmetic, budgets, and publication; a human supplies the judgment that can
promote, reject, supersede, or revoke persistent local memory.

The launch cut explicitly defers baseline/candidate execution, divergence
reporting, global or managed memory, autonomous model/prompt training, coding
and other universal-agent support, hosted ingestion, and a SaaS control plane.
Those surfaces require later evidence and a new accepted checkpoint.

### First launch checkpoint — Grounded Case Factory

The owner froze LABS-04 on 2026-08-01 as the first checkpoint in this launch
cut. It consumes only the shipped synthetic Observer and structural
intelligence bundles. The completed closing experiment uses the explicitly
authorized Microsoft Foundry Fireworks `FW-GLM-5.2` deployment through a
restricted LangChain `create_agent` four-tool runtime. One initial
clarification is followed by five independent bounded one-case slots;
deterministic code owns evidence projection, citations, support, identities,
slot orchestration, duplicate arithmetic, budget, HTTP accounting, lineage,
and publication. Model output remains `PROPOSED`; semantic usefulness requires
a blind owner review. The 2026-08-02 close produced five valid distinct cases
with no gaps and therefore cleared machinery. Akarsh then answered yes to all
six frozen usefulness questions for all five cases and confirmed that no
accepted case depends on a hidden or fabricated fact. LABS-04 therefore passed
`LABS04_USEFULNESS_V1`. Akarsh then accepted the smallest LABS-05 checkpoint
and directed implementation; its frozen packet and wire are
`internal/SLICE_PACKET.md` and `internal/LABS05_WIRE_CONTRACT.md`.
The closure includes a supported, strict config-dispatched
`triana cases generate` path for the pinned restricted runtime plus immutable
`triana cases resume`; legacy configs remain explicit and no fallback exists.

The required smoke input is the first 50 physical lines of the existing
tracked HRAI v2 `run_200` historical-traffic corpus, exact selected SHA-256
`4bb5839771bffe13b33b30cb42cf8cfc4ab1513e9012c10da0923bf58e1e991c`,
labeled `SYNTHETIC_EXISTING_TRACE_CORPUS`. It is not production or real-user
evidence. LABS-04 does not expand the privacy boundary, execute the target
agent, create persistent memory, or expose a generic agent framework. Its
historical exact contract remains `internal/LABS04_WIRE_CONTRACT.md` and its
closed evidence remains in the LABS-05 handoff.

### Second launch checkpoint — Adaptive Multi-Turn Runner

LABS-05 was frozen for test-first implementation on 2026-08-02. It executes
exactly the owner-reviewed LABS-04 cases for context recovery, cross-client
refusal, and bounded status verification as three six-role-turn episodes. The
simulated user uses Foundry Fireworks `FW-GLM-5.2`; the first named target is
the existing HRAI Recruiter Chat ReAct HTTP protocol at commit `728f6c5`.
Triana owns the adaptive outer loop and invokes the opaque target through the
restricted `HTTP_JSON_V1` connector. A strict `EXECUTABLE_JSONL_V1` customer
bridge is the bounded escape hatch for endpoints that cannot use declarative
HTTP/JSON. Triana does not reconstruct the target's prompt, model, tools,
orchestration, or memory.

Deterministic code owns episode/turn/tool identity, latest-observation binding,
termination, all budgets, outer HTTP accounting, artifact custody, trajectory
fingerprints, duplicate arithmetic, and typed gaps. The simulator proposes
only U2 and U3. Triana persistent/global memory remains deferred; target state
stays target-owned and unknown isolation is a typed gap. There is no Triana
retry, redirect, proxy, or target/model/provider fallback.

Automated implementation verification uses fakes only. A live three-episode
run requires separate owner authorization. Passage then requires three valid
nonduplicate inspectable trajectories and Akarsh's `LABS05_ADAPTATION_V1`
review. Judges, persistent/global memory, UI, real-data support,
baseline/candidate diff, generic SDKs, broad evaluation, and hosted execution
remain deferred. The exact contract is `internal/SLICE_PACKET.md` plus
`internal/LABS05_TARGET_CONNECTOR_V1.md`; restart history remains
`internal/LABS05_HANDOFF_2026-08-02.md`.

One non-general exception is frozen in
`internal/LABS05_REAL_DATA_CANARY_2026-08-03.md`: Akarsh authorized exactly one
private three-episode run against the named real HRAI/RDS target with responses
sent to the named Azure Foundry simulator. It must be labeled
`OWNER_AUTHORIZED_REAL_DATA_CANARY`, may remain only under `/private/tmp`, and
expires after the first attempted run. This does not authorize public,
portable, repeatable, or general real-data support.

That run is now consumed: three episodes were attempted, two were valid and
distinct, and one became partial at U3 with `SIMULATOR_INVALID_RESPONSE`.
LABS-05 therefore remains unpassed with `INSUFFICIENT_DISTINCT_TRAJECTORIES`;
four adaptation review items exist and no rerun is implied. Akarsh ruled those
items Y, N, Y, Y. The rejected item exactly copied the preceding target answer
and assumed the assistant role. The supported cause is a simulator-boundary
defect: verified persona, intent, and turn policy were not sent to the
simulator, and semantic validation did not reject role inversion or echoing.

The next proposed checkpoint is regular-use-first simulator fidelity, recorded
in `internal/LABS05_SIMULATOR_FIDELITY_REVIEW_2026-08-03.md`. Regular user
behavior is primary; angry, impatient, skeptical, informal, mistaken, and
adversarial behavior are declared strata. Persistent/global Triana memory
remains deferred.

On 2026-08-03 Akarsh accepted and started LABS-06 under
`internal/LABS06_SIMULATOR_FIDELITY_V1.md` and the replacement
`internal/SLICE_PACKET.md`. It is a synthetic-only, one-attempt repair that
passes a versioned user-owned persona/intent/fact/policy projection and bounded
episode state to every simulator call, adds deterministic declared-matcher
semantic gates and true structured stopping, and freezes a 30-item
`REGULAR_USER_SIMULATION_FIDELITY_V1` panel with a 24-accepted and zero-critical
human gate. The historical LABS-04 artifacts remain immutable. Additional
provider execution and human passage remain separately owner-gated; persistent/global
memory, judges, UI/report, baseline/candidate comparison, real data, generic
SDKs, and broad eval expansion remain deferred.

The synthetic-only LABS-06 implementation is locally GREEN: 18 frozen fidelity
acceptance cases, 143 historical adaptive-runner cases, and the complete
569-test repository verifier passed on 2026-08-03. This proves the bounded
component and null-ruling review contract only. A separately authorized private
three-episode HRAI/Foundry smoke was then consumed: each opening received one
HRAI response, but each first simulator continuation was rejected as
`SIMULATOR_INVALID_RESPONSE`, leaving 0 valid/effective trajectories. No retry
or rerun occurred. `REGULAR_USER_SIMULATION_FIDELITY_V1` remains unpassed and
pending Akarsh's human rulings; the smoke does not authorize general real-data
support or another provider/target run.

### Public Preview rollout direction

On 2026-08-03 Akarsh directed Triana to move from component proofs toward a
public, usable Preview and to add the allowlisted Triana demo UI to the active
roadmap. The ordered proposal is recorded in
`internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md`: repair
regular-user simulator fidelity, freeze a machine-readable report projection,
adapt the provenance-cleared demo visual system to Labs semantics, ship a
one-command synthetic public demo, and then prove real-agent usability through
the stranger-installation gate. Static read-only hosting is permitted for the
public proof; hosted ingestion, accounts, storage, or execution remain
deferred.

The Triana demo package is allowlisted only after per-file ancestry and license
checks. Its Release Review claims, PASS/BLOCK logic, snapshots, and release
memory are not Labs truth and cannot cross merely because its visual shell is
eligible.

The superseding local implementation reached GREEN on 2026-08-03: 131 frozen
connector acceptance tests and 539 repository-wide tests pass with the complete
versioned verification gate. Exact outer HTTP accounting remains deterministic;
unavailable target-internal calls, tokens, cost, tool trace, budget enforcement,
or global-state isolation are typed gaps rather than zeros.

The owner-authorized one-turn localhost smoke reached unchanged HRAI commit
`728f6c5`, but HRAI could not create a session: its configured Postgres endpoint
timed out during startup and its configured Redis hostname did not resolve, so
`POST /sessions` returned HTTP 500. No chat turn, tool call, or HRAI session
occurred. The response exposed and closed one Triana classification defect with
an independent regression; the actual smoke remains failed target-infrastructure
evidence, not a successful episode or `LABS05_ADAPTATION_V1` passage. No rerun
is authorized by this record.

## Scope decisions (Akarsh, 2026-07-31)

1. **User simulation is in scope.** The core intelligence layer is the
   **next-turn generator**: read the historical trace corpus, cluster how
   users actually behave, derive persona and intent files from those
   clusters, and generate the most realistic next user turn when a candidate
   diverges from the recording. Multi-turn comparison is a goal, not a
   deferral.
2. **Diversity control is a first-class requirement.** Independent simulated
   runs must not silently converge on duplicate trajectories. The panel and
   the generator must measure and bound trajectory duplication so N runs
   represent N distinct situations.
3. **Provider: OpenRouter (or equivalent API provider) with the operator's
   keys.** Customer deployments use customer keys. Spend is metered and
   capped per panel.
4. **Real-user grounding comes from mined corpora.** Blitz data (Akarsh's
   own, referenced in agentagon/HRAI/Kairos-AI) is the primary mining target
   for distress markers and persona realism; public corpora (ABCD, tau-bench)
   are acceptable supplements; generated corpora are acceptable when labeled
   as such. Fidelity labels on every derived asset.
5. **Open-source distribution** after the redaction, egress-validation, and
   provenance checks pass. Local-first: nothing is sent to Triana. Redaction
   and egress validation run before hashing and before trace content is sent
   to a model provider. Customer-held keys do not imply authorization;
   configuration or consent must name the provider and permitted egress.
6. **The Slice 0A kernel (`triana-core/`) is shared infrastructure.** Labs
   defines its own document kinds (e.g. PreviewTrace) using the kernel's
   canonicalization and hashing; the five frozen V1 contracts are not
   modified.

## Evidence rules (carried over from repository discipline)

- Divergence-first reporting; verdict language never replaces the human.
- Universal-invariant hits are high-priority flags, not verdicts; a human
  confirmation converts a flag class into a persistent ruling.
- Baseline is reference behavior, not automatically accepted behavior.
  Acceptance requires a human ruling or explicit acceptance evidence. A case
  carrying confirmed failure evidence marks the baseline `KNOWN_FAILURE`;
  divergence then defaults to a candidate-improvement candidate, not a
  verdict.
- Explicit denominators; paired claims only from two-sided intersections;
  gaps, non-comparable, and unstable cases reported separately, never folded
  into scores.
- No rerun-to-green: machinery acceptance is proven on constructed
  nondeterministic fixtures; real-data milestones pass by reporting honestly,
  whatever the data shows.
- Fidelity badge on every report: shared-prefix resampling, simulated
  continuation, and generated-corpus evidence are labeled and never
  conflated.

## Accepted outcome and stability boundary

The owner accepted the typed outcome, pass^3 stability, comparability,
observed-baseline-variation, and evidence-gap machinery in the active plan on
2026-07-31. Outcome fields use `NOT_APPLICABLE`, `MISSING`, or
`PRESENT(value)`; missing required evidence cannot block valid lower-field
observations from being shown, but it prevents a complete-outcome claim. The
plan is normative for the complete mechanism.

The external usability gate is M3.5: a developer who did not build Triana must
install the public repository, adapt their traces within the stated line
budget, and produce an honest report within 90 minutes before persistent label
storage or promotion work proceeds.

## Relationship to suspended V1

V1 (`docs/PRODUCT.md`) is suspended, not deleted. Its incident→ProtectedCase
loop survives inside Labs as the must-check promotion path. Resuming V1 or
merging it with Labs requires an explicit decision-log entry.
