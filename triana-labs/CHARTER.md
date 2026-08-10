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

### Self-serve trace-viewer checkpoint (owner-frozen, 2026-08-06)

Akarsh superseded the prior immediate deferral of hosted ingestion and accounts
for one deliberately narrow beta checkpoint. Its entire value loop is:
authenticate, create one agent, upload one prescribed PreviewTrace JSONL file,
inspect deterministic accepted/rejected accounting, and browse accepted
conversations in a reusable transcript/tool viewer. It does not run analysis,
simulation, reports, models, providers, targets, or HRAI ingestion and makes no
behavioral, regression, release, or accepted-truth claim.

The backend, not the browser, owns authentication verification and workspace
authorization. One authenticated owner receives one personal workspace; teams,
invites, roles, billing, SSO, API keys, and public sharing remain deferred.
Uploaded traces use the explicit `CUSTOMER_AUTHORIZED_TRACE_DATA` privacy class,
require human authorization attestation, remain private, and have no model or
provider egress. Deterministic code owns source hashing, identity, line
accounting, validation, status, ordering, linkage, pagination, and isolation.
The exact implementation boundary and minimal acceptance gate are frozen in
`internal/SLICE_PACKET.md`.

The owner subsequently selected open email magic-link signup for this
checkpoint: authentication itself has no approval waitlist. Supabase Auth owns
email delivery and session issuance while the Triana backend continues to
verify JWTs and own authorization. Gradual feature rollout uses workspace
entitlements rather than overloading membership roles. Trace ingestion and the
conversation viewer are available by default; analysis, simulation, team
collaboration, and API access are locked and expose an idempotent request-access
action. A request is not a grant, and this checkpoint adds no analysis,
simulation, team, billing, or admin-approval implementation.

The owner then authorized one private non-auth dry run of the analysis core on
the existing LABS-08 AWS runtime. The exact verified 57-task TAU² Discovery
archive may be deterministically adapted to synthetic PreviewTrace records and
grouped only by observable event/tool structure through real S3/RDS/DBOS. This
proves neither semantic user populations nor the authenticated analysis bridge;
no model/provider call, new infrastructure, entitlement grant, or persistent
ruling is authorized by that canary.

On 2026-08-07 Akarsh superseded the immediate analysis value surface with
Phase 1 Behavior Map: one authorized conversational-trace corpus produces a
proposed User Demand Map over multi-goal episodes, a multi-label Agent Behavior
Map, emerging/unknown observations, exact readable evidence, and unresolved
human questions. Comparison/diff, eval generation, existing-eval integration,
outcome judgment, L4, simulation, and accepted taxonomy remain later phases.
Semantic output is proposed evidence, never correctness or policy truth;
deterministic code owns trace/sample identity, sealed splits, evidence
coordinates, support, lineage, budget, artifact integrity, and typed gaps.
Independent semantic audit authority is subject-scoped: an episode ruling may
detach only that episode from a population, while a population ruling governs
the population. Any surviving membership is deterministically reprojected so
support, visibility, identity, assignments, denominators, and typed uncertainty
remain consistent; an unsupported member and its audit evidence remain visible.
The same episode ruling propagates to every agent-behavior occurrence derived
from that episode. Disputed occurrences remain visible as excluded evidence,
but only independently eligible occurrences contribute to a published
pattern's membership and support. Any surviving pattern is deterministically
reidentified and linked to its pre-projection audit subject; a pattern-level
ruling continues to govern the whole pattern.

Pattern-stage custody is exhaustive. Every eligible behavior occurrence has
one deterministic terminal disposition; successful-batch omissions, failed
batches, insufficient support, audit-missing candidates, and audited disputes
remain distinct. A semantic response may contribute only occurrence IDs from
its exact batch or hierarchy input. Missing-audit and disputed patterns retain
stable identity, membership, evidence lineage, and unpublished visibility but
contribute zero active support. Candidate, audited, supported, disputed, and
missing counts are separate. Population publication likewise requires unique
membership, support equal to unique members, one disposition per episode, and
exact equality between active episode-to-population edges and `ASSIGNED`
disposition edges.

### Invite-only local Preview distribution (owner-frozen, 2026-08-10)

The first distributable Behavior Map surface is an invite-only local package
and container named **Triana Preview**. Its single command accepts one
authorized PreviewTrace JSONL source, a short agent description, an empty
private output directory, and an explicit trace-authorization acknowledgement.
It redacts and binds the evidence locally, then invokes the same installed
`triana-labs` Behavior Map engine that repository development uses. The facade
owns custody and invocation only: it contains no episode, taxonomy, grouping,
audit, support, identity, or report implementation. Engine improvements reach
Preview by updating that one same-commit dependency and passing the Preview
verification gate, rather than by copying code.

Raw traces remain on the operator's device, the input mount is read-only, and
the output remains private. Provider absence produces the engine's existing
typed semantic gaps; partial provider configuration refuses before execution.
This distribution is not public or open source, does not add hosted upload,
telemetry, arbitrary adapters, a UI, or a stable SDK promise, and authorizes no
registry publication or deployment. Those actions require a later owner
decision after the local pilot.

The owner subsequently authorized a public-sourceable onboarding package
without opening the private engine. `triana-skills/` contains one canonical
Codex/Claude Code skill, a deterministic PreviewTrace validator, a bounded
coding-agent adapter scaffold, and a digest-pinned Docker command constructor.
It may help a coding agent implement a customer-local mapping, but unfamiliar
schemas remain explicitly `IMPLEMENTATION_REQUIRED`; no generic adapter or
semantic inference is claimed. The package may be published only after its
privacy, contract-parity, and metadata gates pass. Image publication, registry
access, provider execution, hosted upload, telemetry, UI, deployment, and the
Behavior Map implementation remain private and separately authorized.

The TAU² proof used Terra as author and Luna as auditor. For subsequent Blitz
and HRAI generalization runs, Akarsh selected the cheaper Luna deployment as
primary author and Terra as independent auditor, with no retry or fallback and
a cumulative USD 100 conservative reservation ceiling. That role choice is a
named run configuration, not a claim that either model is globally better.
The completed Blitz run produced a useful partial map; the HRAI run produced a
truthful zero-semantic typed-gap report after every Luna extraction request
failed at the provider boundary. Neither result is accepted behavior or a
complete taxonomy.

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

The current intent-first LABS-06 implementation is locally GREEN: 15 frozen
repair acceptance cases, 143 historical adaptive-runner cases, and the complete
566-test repository verifier passed on 2026-08-03. The earlier seven-field and
the repaired three-field private HRAI/Foundry runs were each consumed once.
Both produced one HRAI response per opening, but all three first simulator
continuations in each run were rejected as `SIMULATOR_INVALID_RESPONSE`, leaving
0 valid/effective trajectories and no generated user turn. No retry or rerun
occurred. `REGULAR_USER_SIMULATION_FIDELITY_V1` and the Accepted Continuation
Rate gate remain unpassed; another provider/target run requires a new owner
decision, and general real-data support remains deferred.

The final local LABS-06 provider-conformance pass is now also GREEN. It keeps
the exact three-field authority and every semantic/privacy gate, adds one
closed structural detail plus a bounded text-free diagnostic, preserves valid
usage accounting on later content rejection, and blocks a third slot only
after two distinct first-continuation episodes prove the same structural
detail. Independent verification passed 43/43 focused cases, 143/143
historical adaptive cases, and the complete 594-test/build/install gate at
`/private/tmp/triana-labs-verify.qLDTKk`. No provider, HRAI, target, or real
data ran. The dogfood incident, live Structural Continuation Yield, Accepted
Continuation Rate, and human fidelity gate remain open; any simulator-only or
end-to-end live execution requires a separate owner decision.

The grounded-workflow closure path is now locally GREEN under
`LABS-046-GROUNDED-WORKFLOW-CLOSURE-V1`. It adds a separate twelve-case mode
with six deterministically observed production cases, six deterministically
grounded expansions, captured-world preflight, goal-first continuations, and
readable manifest-hashed LABS-04/LABS-06 evidence while preserving all legacy
paths. The complete verifier passed 603 tests at
`/private/tmp/triana-labs-verify.eLaFCb`. This is synthetic acceptance only:
the current trace and inventory contracts reject owner-authorized real data,
so no truthful RDS-backed case bank or live HRAI result exists yet. Supporting
that requires a separately frozen real-data contract and exact egress approval;
human completion and fidelity rulings remain solely Akarsh's.

On 2026-08-04 Akarsh removed the accidental synthetic-only plumbing block for
the grounded-workflow path. Exactly `OWNER_AUTHORIZED_REAL_DATA_CANARY` may now
be implemented alongside `SYNTHETIC`, with private `/private/tmp` custody and
exact class agreement from source trace through report. This does not open
general real-data support or authorize RDS, provider, HRAI, or target execution;
those remain separately exact-bundle and cost gated.

The bounded plumbing implementation is now locally complete. Independent
acceptance covers the exact class through Observer, Intelligence, Case Factory,
world inventory, adaptive execution, and report custody; unknown, mixed,
non-private, and cross-stage mismatches refuse before egress. The complete
repository verifier passes 613 tests plus build/install/artifact gates at
`/private/tmp/triana-labs-verify.ccgGCu`. No external system or real dataset
ran, so this is local contract evidence only and creates no human fidelity
ruling.

LABS-06 closed on 2026-08-04 as `CLOSED_WITH_ACCEPTED_BACKLOG`. The final
private twelve-case HRAI canary produced three valid/effective trajectories:
one valid single-turn stop and two genuine six-role-turn conversations. Akarsh
accepted Conversations 3 and 4 for this round. This closes the launch
checkpoint on deterministic simulator controls, live provider compatibility,
and demonstrated adaptive multi-turn execution; it does not establish
universal, population-level, or production-grade simulator fidelity.

The earlier 30-item/24-accepted/zero-critical panel is superseded as a required
LABS-06 milestone exit and retained as optional future calibration before any
broader fidelity claim. Known backlog remains: authorize claimed world
mutations against bound or newly observed objects; preserve explicit intent
preconditions before downstream actions; use a longer aggregate deadline for
future twelve-case runs; and keep target protocol/tool-budget availability
separate from simulator fidelity. Conversation 7 remains negative evidence,
and partial or unavailable episodes remain typed gaps rather than passes or
failures. The next checkpoint is the combined LABS-07/08 report-and-UI vertical
slice; no implementation is authorized until its full-journey wireframes,
minimum report boundary, provenance-cleared source files, and bounded slice
packet are accepted.

LABS-07 and LABS-08 are one milestone rather than sequential projects. The
canonical report remains the sole evidence authority, but it is designed and
validated with the read-only UI so the contract follows the actual user
journey instead of speculative reporting abstractions. That journey spans
authorized trace setup, observed corpus understanding, grounded persona/intent
and case derivation, execution preflight and progress, inspectable adaptive
conversations, coverage/cost/gaps/lineage, human review, and carried backlog.
The allowlisted Triana demo may supply only file-level provenance-cleared
visual tokens, layout, navigation, drawers, and responsive behavior; Release
Review data models, PASS/BLOCK semantics, snapshots, and memory do not cross.
LABS-09 remains the separate packaging, no-key demo, documentation, licensing,
and static-publication checkpoint.

On 2026-08-04 Akarsh accepted the complete LABS-07/08 information architecture,
terminology, human-review contract, and ASCII wireframes in
`internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md`. Setup currently
selects one local trace file and exposes transparent trace-understanding
denominators rather than an opaque quality score. The intended corpus-scale
behavior pipeline freezes deterministic clustering before model-authored
summaries; current structural grouping may not be mislabeled as that future
semantic population capability. `World availability` remains the durable
umbrella and `Case data items` is its currently specified subsection. Human
review records four independent rulings—simulated-user realism, follow-up
adaptation, agent goal completion, and scope/privacy/boundary compliance—with
no aggregate Triana verdict or automatic memory mutation. The exact build
restart context is `internal/LABS07_08_BUILD_HANDOFF_2026-08-04.md`; LABS-06
evaluation debt is retained in `internal/LABS06_BACKLOG_2026-08-04.md`.

The accepted wireframes clear the design gate, not the implementation entry
gate. Report/UI work still waits for the remaining owner choices, exact
Triana-demo per-file provenance and license review or clean-room
reimplementation, and a replacement bounded `internal/SLICE_PACKET.md`.

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

## Full-corpus Behavior Map evidence (2026-08-08)

The bounded Blitz DEVELOPMENT proof supports the Phase 1 claim at full
visible-corpus scale: 374 authorized conversations can be extracted into
grounded demand episodes, consolidated into proposed user populations and
agent-behavior patterns, independently audited, and rendered from immutable
checkpoints without opening the 125 calibration or 125 holdout conversations.
The corrected private report retains 80 supported populations and 61 supported
patterns; 47 unaudited pattern subjects remain typed missing and unpublished.
This is a proposed, evidence-linked behavior map—not accepted truth, complete
taxonomy, correctness, outcome attribution, comparison, or eval generation.
Provider adapters may expose stage-specific output ceilings and deterministic
request pacing, but still use no automatic retry or fallback. Complete explicit
campaign reservation fields are authoritative for cumulative report budgeting
and must not be double-counted from copied checkpoint history.

The coverage-conservation repair keeps that successful report immutable and
does not replace it. A provider-disabled projection may reuse only exact
unchanged semantic subjects from a completed private predecessor. Citation
repair is field-scoped: invalid extra evidence is excluded individually, a
demand survives only while its goal, requested action, and subject retain exact
customer-message grounding, and unsupported optional fields are removed with
visible uncertainty. Every population-stage input receives an explicit
disposition; omitted, ambiguous, failed-batch, or unsupplied IDs cannot silently
become membership or disappear across batches.

Historical projection never creates fresh semantic authority. A changed
population membership or pattern occurrence set receives a new identity and
predecessor lineage, remains unpublished with audit `MISSING`, and contributes
no active assignment or support until re-audited. Rejected and grounding-
replacement evidence remains inspectable excluded history. The accepted
private projection `sha256:4a31e882651e533254a71fb43bf2aafe87b026297dea056c0c377aa4c1729f6e`
contains 405 grounded episodes, 74 currently supported populations with 210
active assignments, three unpublished candidate populations with eight
`REAUDIT_REQUIRED` memberships, and 24 supported patterns. It is only a
private, proposed, partial historical semantic projection—not a fresh full
analysis, accepted taxonomy, benchmark pass, or replacement for the immutable
baseline.

The 2026-08-09 conservation repair leaves that accepted baseline and projection
inspectable. It rejects pattern IDs absent from the exact batch or hierarchy
input, retains audit-missing and disputed patterns as unpublished custody, and
refuses duplicate or inconsistent pattern/population accounting. Historical
projection now also preserves every predecessor `AUDIT_DISPUTED` disposition;
population support cannot restore it. Provider-disabled projection
`sha256:9ee02d4d5160b55d47e96e141dbb90f2b735007b98162ca28f94e8da8b0ade33`
therefore has 73 supported populations with 208 assignments, four unpublished
candidate populations with nine re-audit-required memberships, 25 preserved
disputed dispositions, one explicitly excluded active disputed edge, and zero
unexplained loss. The original eight re-audit memberships, two grounding
replacements, and one grounding rejection remain; one additional co-member
requires re-audit because removing the disputed member changes its population
identity. Its 24 historical supported patterns and support 75 are unchanged
because this projection does not invent a fresh semantic pattern run. It is
private repair evidence, not baseline promotion or a semantic-quality claim.
