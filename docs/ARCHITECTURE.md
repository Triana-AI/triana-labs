# Architecture and trust contracts

This document fixes the V1 authority and system boundaries without choosing a
cloud architecture prematurely. The accepted implementation split is Python
for the deterministic core, CLI, backend APIs, integrations, and future
AI-assisted packages, with TypeScript for the web UI and versioned JSON Schema
as the enforced language boundary. `docs/CONTRACTS.md` owns the exact Slice 0A
wire representation.

## Active Labs execution boundary

For active Triana Labs work, `triana-labs/CHARTER.md` and the current Labs plan
supersede the suspended V1 flow below. The shipped local synthetic pipeline is:

```text
source-specific synthetic JSONL
  -> standalone reference transform
  -> PreviewTrace JSONL
  -> Trace Observer
  -> verified Observer manifest + normalized traces
  -> structural Corpus Intelligence
  -> deterministic clusters + explicit semantic gaps
```

`triana traces observe` owns raw PreviewTrace accounting and five deterministic
corpus artifacts. `triana corpus derive` accepts only that Observer manifest,
verifies all sibling hashes/counts/traces, and publishes a separate atomic
intelligence bundle. `intelligence/input.py` owns input integrity,
`intelligence/derive.py` owns fingerprints, membership, IDs, support and gap
artifacts, `intelligence/publication.py` owns atomic filesystem publication,
and `cli.py` owns invocation, safe terminal events, and exits.

The current structural fingerprint contains counts, ordered safe tool names,
terminal presence/state, unmatched calls, and mechanical case eligibility. It
does not consume conversation text, opaque tool values, error prose, or source
trace IDs. Personas, intents, turn policies, language, and distress remain
typed `NOT_DERIVED`/`NOT_EVALUATED` states. No provider, LLM, real-data path,
redaction/egress path, Case Generator, or UI exists in this checkpoint.

The later Trace-to-Eval Review V0 and authenticated self-serve bridge add a
separate active Labs path without changing the suspended Release Review V1
contracts:

```text
magic-link owner -> workspace -> agent -> authorized PreviewTrace upload
  -> deterministic import/rejection accounting
  -> ANALYSIS entitlement gate
  -> canonical Trace-to-Eval engine (semantic provider absent by default)
  -> immutable report/review/conversation artifacts in workspace S3
  -> run/report/artifact indexes in RDS
  -> owner-scoped UI + backend CLI
  -> append-only human rulings
```

Authentication establishes subject identity; workspace ownership scopes every
agent, import, run, report, conversation, and ruling lookup; entitlements own
feature rollout. These authorities are not interchangeable. Upload is bound to
the exact owner, agent version, import, source hash, and engine version, so an
identical request is idempotent while another agent receives a distinct run.
The report is the common backend/UI/CLI evidence object. TypeScript projects
it but does not recalculate evidence.

Deterministic code owns identity, accepted/rejected accounting, split/group
integrity, report lineage, idempotency, owner scope, and ruling custody. An LLM
may propose populations and evals only after separately authorized provider
egress; the default self-serve bridge uses `semantic_model=None`. A human owns
reward mapping when no authoritative outcome exists, proposal acceptance or
editing, and review rulings. Absence of any lane is a typed gap, never a pass.

Behavior Map recovery has two distinct execution forms. A fresh semantic run
may propose demand episodes, population membership, behavior occurrences, and
patterns under explicit provider authority. A provider-disabled historical
projection may instead repair deterministic grounding and conservation defects
using a completed private predecessor, but it may retain authority only for
byte-identical semantic subjects and their exact audits. Changed episode
grounding creates explicit predecessor lineage; changed population or pattern
membership is a new unaudited candidate, remains unpublished, and cannot
contribute active assignment or support. The projection binds the failed
semantic predecessor and accepted baseline separately, preserves rejected
evidence as excluded history, reports zero projection calls, and carries any
historical lane-budget violation without converting it into an overall-budget
pass.

Fresh Behavior Map pattern consolidation has a deterministic conservation
projection around the semantic proposer. Every eligible occurrence receives
one terminal disposition, and each model response is restricted to the exact
members supplied to that first-level or hierarchy batch. Supported patterns
are the only active-support subjects; missing-audit and non-supported patterns
remain stable unpublished candidates/disputes. Report accounting separates
candidate, audited, supported, disputed, and missing states plus active and
unpublished membership. Before artifact identity is finalized, a deterministic
gate refuses duplicate occurrence membership, duplicate population membership
or dispositions, support mismatch, population-edge mismatch, and any mismatch
between active population members and `ASSIGNED` dispositions.

Historical projection treats a predecessor `AUDIT_DISPUTED` disposition as
persistent authority. It removes that episode before recomputing population
identity/support, records the excluded predecessor edge, and cannot restore
assignment without a current explicit supported ruling. Any co-member whose
population identity changes becomes re-audit-required rather than inheriting
the predecessor audit.

### Triana Preview local distribution boundary

`triana-preview/` is a packaging and custody facade over the single active
engine in `triana-labs/`; it is not a second product implementation:

```text
authorized PreviewTrace JSONL (read-only)
  -> triana-preview authorization/path/provider custody checks
  -> existing triana_labs Behavior Map redaction
  -> private redacted source + audit + evidence manifest
  -> existing installed `triana behavior-map run`
  -> canonical JSON/Markdown/HTML/checkpoints + local run manifest
```

The facade may validate the operator acknowledgement, agent-description bound,
regular-file identity, empty destination, complete provider binding, and
private filesystem modes. Deterministic redaction, manifest interpretation,
semantic schemas, analysis, identity, support, typed gaps, and report rendering
remain owned by `triana-labs`. The package uses the repository-local Labs
dependency at the same commit, so there is no copied taxonomy or behavior-map
logic to synchronize. Its container has a non-root runtime, explicit production
copies only, a read-only input mount contract, and no hosted telemetry or
upload boundary. Image-registry publication and external deployment are not
part of this architecture checkpoint.

PreviewTrace structural validity does not by itself authorize a customer
identity for publication. The Labs redaction boundary preserves ordinary safe
identities and explicitly recognized structured identities, but projects an
unfamiliar `trace_id` or `source_trace_id` through the existing stable redactor
token registry when its residual detections are exclusively numeric identity
categories. Equal source identities remain equal within the projection,
distinct identities remain distinct, and the audit exposes category totals
without raw values or a reversible mapping. A remaining identifier residual
still refuses before analysis and is exposed by Preview as a content-free typed
reason.

Provider-enabled Preview is the same local command with one additional custody
input: a complete explicit Triana provider environment. Preview binds the exact
normalized OpenAI-v1 base URLs, including their paths, plus model, deployment,
SKU, capacity, and credential-boundary identities into the evidence manifest.
The Labs engine compares that manifest to live model lineage before the first
call. Omitting the provider environment is the deterministic no-egress mode;
partial configuration, inferred application variables, or a mismatched binding
cannot authorize semantic work.

`triana-skills/` is the public-sourceable onboarding layer above that private
facade, not another engine. One canonical Agent Skills-compatible
`plugins/triana/skills/onboard/SKILL.md` is consumed directly by Codex and is
also exposed by a thin Claude Code plugin/marketplace manifest. Its
standard-library tooling may inspect authorized local JSONL structurally,
scaffold a bounded customer adapter, validate the exact PreviewTrace v1
mechanical contract, show at most three redacted previews, and construct an
immutable-digest Docker argv. It never executes Docker, publishes an image,
contains credentials, uploads traces, or owns Behavior Map semantics.

Unknown or dynamic source keys are not emitted verbatim by structural
inspection; only a closed set of known schema names is visible and other keys
collapse to a non-reversible redacted token with a count. An unfamiliar schema
therefore becomes an explicit local adapter task reviewed by the operator and
coding agent. It cannot silently become valid PreviewTrace. Codex and Claude
Code share the same script, adapter template, reference, and conformance tests
so agent packaging cannot change deterministic meaning.

LABS-04 is the implemented and owner-passed case-generation boundary:

```text
verified synthetic Observer + intelligence manifests
  -> allowlisted semantic evidence projection
  -> one Foundry GLM-5.2 restricted four-tool clarification/research/submit loop
  -> five deterministic independent one-case slots
  -> deterministic citation, support, identity, duplicate, budget, HTTP-accounting, and lineage gates
  -> proposed personas, intents, adaptive turn policies, and five distinct case candidates
  -> blind human usefulness review
```

Only user/assistant text, safe tool names/result states, terminal state, and
structural membership may enter the provider projection. System text, source
IDs, tool arguments/results, terminal reasons, paths, secrets, and opaque
metadata remain outside it. The provider has proposal authority only. A valid
citation proves existence, not semantic entailment; all assets remain
`PROPOSED` and a human review is required before the checkpoint can pass.
LABS-04 uses LangChain `create_agent` only as the bounded tool-loop harness; it
does not delegate deterministic authority to the framework. It adds no
target-agent runner, persistent memory, model judge, real-data path, or UI.
The supported CLI dispatches by a closed config artifact kind: restricted
configs construct only the pinned Foundry GLM-5.2 transport, while legacy
configs retain the older engine. `cases resume` verifies exact config bytes,
the immutable pause bundle, complete bounded answers, and the same private
cache before transport construction. Unknown or malformed state refuses; no
engine, credential, model, or provider fallback exists.
The owner passed all five cases under `LABS04_USEFULNESS_V1`.

LABS-05 is the active test-first boundary:

```text
accepted LABS-04 case + reproducible owner ruling
  -> deterministic three-slot episode controller
  -> U1 copied from case
  -> strict HRAI Recruiter Chat ReAct subprocess -> A1 + normalized tools
  -> Foundry GLM-5.2 consumes latest observation -> U2
  -> same isolated target session -> A2
  -> Foundry GLM-5.2 consumes latest observation -> U3
  -> same isolated target session -> A3
  -> immutable transcript/tool/HTTP/budget/gap artifacts
  -> deterministic trajectory fingerprint and duplicate clusters
  -> owner adaptation review
```

The HRAI target is pinned to commit `728f6c5`, historical Qwen 235B model, and
the executable `candidate-screening-v3-decision-followthrough` prompt at that
commit, but runs through a Triana-owned target-specific JSONL adapter
against a fresh in-memory synthetic read-only world. HRAI persistent memory,
database writes, web, email, evaluation submission, and sub-agents are absent.
The target process and episode state are discarded after each episode.

The simulator may propose only U2/U3 and a stop suggestion. Deterministic code
owns every identity, sequence, observation binding, termination, reservation,
HTTP/token/tool count, custody, and duplicate denominator. Provider or target
failure is typed partial evidence; no retry or fallback exists. Persistent or
global learning memory remains deferred: only immutable evidence memory and
discarded episode memory exist in this checkpoint.

This boundary is locally implemented behind `triana episodes run`. Repository
verification proves the deterministic/fake boundary and strict process
contract; it does not prove live Foundry or HRAI/Qwen compatibility, valid live
trajectories, or the owner adaptation ruling.

The owner-approved Target Connector V1 supersedes the preceding LABS-05 target
paragraphs while retaining the episode controller and artifacts. Triana now
owns only the adaptive outer loop and connector-observed facts. An existing
agent owns its prompt, model/provider, tools, internal orchestration, and
target-side state. `HTTP_JSON_V1` provides restricted request-pointer insertion,
response-pointer extraction, explicit remote-session or transcript-replay
lifecycle, exact endpoint authorization, and no retry/redirect/fallback.
`EXECUTABLE_JSONL_V1` retains the shell-free process isolation as a customer
bridge rather than an HRAI reconstruction. HRAI maps its existing
`POST /sessions`, `POST /sessions/{id}/chat`, and `DELETE /sessions/{id}`
surface through configuration. Target-internal accounting and state isolation
are recorded only when reported or evidenced; absence is a typed gap. The
normative contract is `internal/LABS05_TARGET_CONNECTOR_V1.md`.

This superseding boundary is locally GREEN with 131 focused connector tests
and 539 repository-wide tests. The first authorized real HRAI smoke proved
endpoint reachability only: configured Postgres timed out and Redis DNS failed,
so session creation returned HTTP 500 before any chat turn. The attempt is a
typed target-infrastructure gap, not an adaptive episode or owner passage.

LABS-06 is the locally implemented simulator-only correction. It preserves the
opaque target connector boundary and adds a versioned user-owned simulator context derived
without mutating LABS-04 artifacts, a closed episode-local interaction state,
one-attempt strict user-turn/structured-stop proposals, deterministic declared-
matcher semantic validation, and a synthetic teacher-forced review contract.
Deterministic code owns context identity, visibility, allowlists, state
transitions, binding, rejection, termination, accounting, and custody. The
model owns wording only; a human owns residual naturalness and fidelity. No
provider execution, persistent/global memory, model judge, report/UI,
baseline/candidate comparison, or real-data path is added by this checkpoint.

LABS-06 is now owner-closed with accepted backlog. The next planned boundary is
one combined LABS-07/08 vertical slice:

```text
verified retained run artifacts
  -> deterministic canonical report compiler
  -> versioned report JSON as sole evidence authority
  -> deterministic Markdown projection
  -> read-only full-journey Labs web projection
```

Report identity, lineage, denominators, accounting, gap classification,
fidelity labels, and human-ruling custody remain deterministic inputs to the
projection. TypeScript UI code may navigate, order, filter, disclose, and
format; it may not independently infer, calculate, upgrade, or persist those
facts. The planned journey spans trace authorization and normalization, corpus
understanding, grounded case construction, run preflight/progress, adaptive
transcripts, evidence/gaps/cost, human review, and carried backlog. Exact
Triana-demo files may enter only after per-file provenance and license review.
This is an accepted architecture direction, not yet an implemented report or
UI boundary.

The owner-accepted projection shape is now frozen in
`internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md`. It uses one local
trace file at setup; transparent adapter/trace-understanding counts;
deterministically owned behavior-group membership and support with separately
labeled model-proposed summaries; intuitive seen-in-traces and grounded-
variation cases; `World availability` with `Case data items` as the currently
specified child; one independent conversation per case; transcript-primary
evidence; and four independent human rulings. The UI cannot collapse those
rulings into one verdict or write them back into memory. Current structural
clusters remain structurally truthful until a later deterministic
corpus-scale semantic-population pipeline is implemented and evaluated.

## Authority map

```text
ACQUISITION / CASE CREATION

CUSTOMER PRODUCTION TRACES
        │
        ▼
DETERMINISTIC SURFACING
membership, signal values, ranking, deduplication
        │
        ▼
HUMAN INCIDENT SELECTION
        │
        ▼
OPTIONAL LLM DRAFTING
risk name, expected/prohibited behavior, candidate assertions
        │
        ▼
HUMAN APPROVAL + PROMOTION
semantic truth and policy authority
        │
        ▼
DETERMINISTIC QUALIFICATION
READY / NEEDS_FIXTURE / NOT_YET
        │
        ▼

RECURRING RELEASE REVIEW

CUSTOMER-DECLARED RELEASE CHANGE
baseline + candidate + declared delta + observable fingerprints
        │
        ▼
HUMAN-SELECTED RELEASE OBLIGATION
one approved Protected Case + required evidence
        │
        ▼
CUSTOMER AGENT REPLAY ───── CUSTOMER-OWNED EVALUATORS
customer code, credentials, environment, and usually an LLM
        │
        ├──────────────┐
        ▼              ▼
TRIANA ASSERTIONS   CUSTOMER CHECK COMMAND
deterministic       may include an LLM judge
        └──────┬───────┘
               ▼
DETERMINISTIC EVIDENCE NORMALIZATION + COMPARISON
identity, trial membership, denominators, rates, gaps, comparability
               │
               ▼
VERSIONED RELEASE POLICY
               │
               ▼
ADVISORY PASS / REVIEW / BLOCK
               │
               ▼
APPEND IMMUTABLE RELEASE EVIDENCE RECORD
evidence + policy version + recommendation
               │
               ▼
RELEASE REVIEW
record + gaps + recommendation + decision state
               │
               ▼
HUMAN RELEASE DECISION
approve / hold / approve with exception
               │
               ▼
APPEND IMMUTABLE DECISION ATTESTATION
```

An LLM may propose meaning. It cannot create truth, approve a case, alter trial
membership or denominators, decide comparability, or write a release outcome
unsupported by the record.

The recommendation and the Release Decision are different authorities.
Deterministic policy renders the recommendation. A human makes the decision.
V1 may link an existing GitHub review, merge, hold, or exception reference; it
does not infer approval from `PASS` or infer a hold from `BLOCK`. The link is a
separate append-only Decision Attestation, never a mutation of the Release
Evidence Record.

## Execution boundary

```text
GitHub pull request
        │
        ▼
customer-hosted GitHub Actions runner
  ├─ checkout approved baseline ref
  ├─ checkout candidate SHA
  ├─ start isolated runtime for each
  ├─ run the same pinned protected case N times
  ├─ collect exact trace IDs
  ├─ run deterministic assertions
  ├─ invoke optional customer evaluator command
  └─ emit normalized evidence
        │
        ▼
Triana hosted control plane
  ├─ validate submitted identities and evidence
  ├─ append immutable record to chain
  ├─ render the versioned Release Policy
  ├─ append the immutable Release Evidence Record
  ├─ post the Release Review summary
  ├─ serve the permanent Release Review page
  └─ append a Decision Attestation when a human decision is available
```

The hosted control plane receives neither repository access nor customer
credentials. It must not claim that uploaded summaries prove observations
outside their declared scope.

## Conceptual objects

These are contracts to implement, not copied schemas.

### Release Change

The Release Change is a nested, versioned object within the Release Evidence
Record, not a separately deployed service. It preserves:

- approved baseline reference;
- candidate reference;
- customer-declared component delta;
- observable composite baseline and candidate fingerprints across code,
  prompt, model, provider, tools, retrieval/configuration, evaluator, fixture,
  and execution contract when available;
- unresolved or unobservable differences;
- the scope of any causal claim.

V1 accepts a customer declaration and verifies available identity evidence. It
does not infer a complete dependency graph or automatically decide which
obligations apply.

### Release Obligation

A Release Obligation is the human-approved semantic requirement carried by a
Protected Case in V1. It includes:

- the behavior that must be preserved;
- its source, such as a confirmed incident or customer policy;
- severity, owner, and approver;
- customer-declared applicability conditions;
- required evidence;
- the bounded Protected Case used to execute the requirement.

The obligation is not created by an LLM or inferred from a score. In V1, it is
not a standalone organization-wide obligation graph.

### Trace contract

Minimum information:

- trace ID and source;
- conversation, thread, and turn identity;
- ordered user, assistant, tool, and system-visible events needed to reconstruct
  the bounded conversational episode;
- agent/release identity when available;
- ordered model and tool observations;
- tool name, arguments, result, status, and error;
- final response, escalation/handoff outcome, and terminal state;
- timestamps, cost, and latency when available;
- parent/child relationships;
- metadata binding a replay to case, trial, side, and code ref.

An adapter converts a provider export to this normalized contract. Parsing
remains provider-specific; product logic consumes only the normalized form.
V1 does not define a generic contract for offline document-processing or
long-running autonomous jobs.

### Protected case

Stable identity over:

- Release Obligation statement, source, severity, owner, applicability, and
  required evidence;
- source evidence;
- conversation prefix or bounded replay request and fixture contract;
- expected, prohibited, and allowed behavior;
- required escalation or handoff where applicable;
- executable checks and versions;
- approval;
- qualification state.

Changing semantic content creates a new case version.

### Trial result

One execution includes:

- case version;
- side (`baseline` or `candidate`);
- code ref and composite runtime fingerprint;
- trial index and randomization controls;
- trace identity;
- assertion results;
- customer evaluator results;
- execution and evaluation gaps.

### Comparison

Comparison is valid only when case version, fixture/configuration, reset policy,
and execution contract match. It preserves:

- pass count and evaluable count;
- end-to-end success count;
- typed gaps;
- absolute rates and baseline-to-candidate movement;
- evidence strength;
- approved threshold.

### Release Evidence Record

The record binds the declared Release Change, observable composite identities,
unresolved identity differences, Release Obligation, required evidence,
Protected Case and evaluator versions, policy version, per-trial evidence,
comparison, gaps, recommendation, PR reference, and chain hashes. It is
immutable. Corrections append a superseding record. Human decisions are linked
through a separate Decision Attestation.

### Release Policy

A versioned, customer-approved mapping from evidence states to an advisory
Release Recommendation. It consumes comparison and gap states; it does not
produce evaluation evidence or execute a deployment.

### Release Recommendation

The deterministic output of the Release Policy: `PASS`, `REVIEW`, or `BLOCK`.
It is advisory in V1 and cannot be represented as the human Release Decision.

### Release Review

The decision-facing projection over one Release Evidence Record and zero or
more Decision Attestations. The PR comment and permanent page must show release
change and unresolved identity differences, applicable obligation, required
and received evidence, named risks, comparability, gaps, the policy rule that
fired, the recommendation, and the linked human decision or its absence.

### Decision Attestation

An immutable, append-only object binding a Release Evidence Record hash to the
customer-controlled approval, hold, merge, or exception reference and optional
rationale. V1 reuses the customer's existing GitHub/release workflow rather
than creating a separate approval engine. `DECISION PENDING` means no
attestation exists.

## Lifecycle boundary

V1 ends after a human decision is linked to a Release Review:

```text
declared Release Change + approved Release Obligation
        ↓
required and received eval evidence + production replay
        ↓
normalized evidence + comparison + typed gaps
        ↓
Release Policy recommendation
        ↓
Release Evidence Record
        ↓
Release Review
        ↓
human Release Decision
        ↓
Decision Attestation
        ╳
deployment / canary / rollout / rollback / post-release validation
```

The lower lifecycle is future Release Control territory. Triana may later
consume rollout and post-release outcomes as evidence, but V1 neither owns
traffic mechanics nor claims that evaluation-set maintenance is the primary
product.

The future extension preserves authority separation:

```text
immutable pre-release record
        ↓
human decision attestation
        ↓
append-only rollout/outcome observation
        ↓
human-reviewed proposal to revise future obligation or evidence requirements
```

A production outcome never rewrites the evidence known at release time, and an
automated observation never silently changes a human-approved obligation.

## Failure and refusal behavior

- Missing baseline → `FIRST_OBSERVATION`.
- Undeclared or unresolved identity difference → explicit limitation; never a
  clean model-only or prompt-only causal claim.
- No human-selected obligation → no Release Review recommendation.
- Required evidence absent → typed evidence gap and `REVIEW` unless a stricter
  customer policy applies.
- Mismatched execution contracts → `MOVED`, not regression.
- Missing tool-dispatch visibility → negative tool assertions unevaluable.
- Agent cannot run safely → `NOT_YET`.
- Required state can be created with a bounded fixture → `NEEDS_FIXTURE`.
- Evaluator errors or timeouts → evidence gap, not behavioral failure and not
  pass.
- Insufficient trials → REVIEW with the limitation shown.
- Hash or identity mismatch → reject the record append.

## Initial interfaces

The first implementation should make these seams explicit:

1. trace adapter;
2. candidate signal engine;
3. protected-case store and versioning;
4. qualification runner;
5. customer agent command contract;
6. deterministic assertion engine;
7. customer evaluator JSONL adapter;
8. paired baseline/candidate orchestrator;
9. comparison engine and Release Policy renderer;
10. immutable record, Decision Attestation, and verifier;
11. GitHub Action wrapper;
12. Release Review renderer and Decision Attestation linker.

Do not build all twelve before testing the vertical slice. Phase 0 defines
schemas and a hand-built round trip. The next slice runs one case on one
reference agent and produces one verifiable record.

## Projection boundary

The deterministic core is the only owner of identity, hashing, comparison,
denominators, gaps, policy evaluation, recommendation, and record chaining.
Every product surface consumes its versioned output:

```text
versioned contracts
        ↓
deterministic core
        ↓
Release Evidence Record + Decision Attestation
        ├─ CLI output and verifier
        ├─ hosted API
        ├─ GitHub Release Review comment
        └─ permanent Release Review page
```

The UI and PR renderer must not reproduce core calculations. A projection may
format, filter, link, and progressively disclose evidence, but the values and
reasons it displays come from the same verified record.

## First vertical slices

1. **Contract kernel:** strict schemas, canonical serialization, stable
   identity, hashing, golden fixtures, and record round-trip verification.
2. **Comparison and Release Policy:** honest A/A, planted A/B, typed gaps,
   comparability, deterministic recommendations, record chaining, and tamper
   rejection.
3. **Release Review projection:** one usable permanent page over the same
   fixture records, showing identity, named risks, evidence, gaps, policy
   reasoning, recommendation, verification state, and `DECISION PENDING` or a
   linked Decision Attestation.

Real trace adapters and paired customer execution replace fixture boundaries
after this kernel is visible. They do not require a second evidence model.
