# Behavior Map V0 vertical slice

Date frozen: 2026-08-07

Status: **ACTIVE GENERALIZATION — TAU, BLITZ, AND HRAI REPORTS**

Slice ID: `BEHAVIOR-MAP-V0`

Continuation ID: `BEHAVIOR-MAP-V0-READABLE-EVIDENCE`

Generalization ID: `BEHAVIOR-MAP-V0-THREE-CORPUS-REPORTS`

## Three-corpus report entry gate — 2026-08-07

After the readable TAU evidence exit, the owner requested three equivalent
Phase 1 Behavior Map reports: the completed TAU² Retail corpus, the authorized
private Blitz trace corpus with agent purpose inferred from owner-authorized
Kairos-AI/Agentagon evidence, and an authorized HRAI trace corpus with agent
purpose inferred from Kairos-AI/Agentagon/HRAI evidence. The output remains the
same canonical JSON plus Markdown/plain HTML contract. Each report must show
user demand, agent behavior, emerging/unknown observations, questions, and
conversation-shaped evidence; no corpus may borrow semantic labels, outcomes,
or evidence from another corpus.

The USD 100 approval is interpreted conservatively as a cumulative ceiling
including the existing USD 48 reservation. For the new Blitz and HRAI runs the
owner explicitly reversed the roles on cost grounds: Luna is the primary
semantic author at USD 0.072 reserved per attempted call and Terra is the
separately identified auditor at USD 0.18 reserved per attempted call. Each
run is capped at 100 Luna calls/USD 7.20 plus 69 Terra calls/USD 12.42, so both
new reports reserve at most USD 39.24 and the three-report cumulative ceiling
is USD 87.24. The completed TAU checkpoints retain their historical Terra
primary/Luna auditor lineage. There is no fallback, silent model substitution, retry to
green, locked-holdout opening, provider-response persistence, deployment,
infrastructure mutation, or new public claim. Exact source paths, hashes,
privacy class, DEVELOPMENT/holdout boundary, adapter counts, agent-context
evidence, provider identities, and per-run reservations must be frozen after
read-only preflight and before egress. One corpus failure becomes a typed
corpus-specific gap and cannot falsify or rewrite another report.

Preflight workers are read-only. They may inspect only the authorized
Agentagon, Kairos-AI, and HRAI repositories plus existing private local trace
artifacts to identify source identity, adapter compatibility, and grounded
agent context. No worker may edit production, tests, canonical documentation,
raw data, manifests, or reports during preflight. Any code correction requires
a separately reconciled change budget plus independent RED/implementation/
review ownership. The orchestrator alone freezes live manifests, performs
provider preflight, authorizes bounded calls, audits artifacts, and updates
canonical decisions. Generated private reports remain under `/private/tmp`.

Blitz preflight established a required privacy correction before provider
execution: the grouped adapter produces customer-authorized full conversations
with redaction `NOT_DECLARED`. A bounded `BEHAVIOR-MAP-V0-REDACTED-PROJECTION`
subslice is therefore authorized. It may adapt the owner-authorized Agentagon
`experiments/blitz_seed/anonymize_tasks.py` detector categories into a generic,
deterministic PreviewTrace projection that redacts every string-bearing event,
preserves event/trace identity and structure, writes a content-free audit, and
refuses malformed or residual direct-identifier evidence. It must never alter
the source file, silently drop a trace/event, claim complete PII removal, or
mark semantic provider egress authorized. The derived manifest remains an
orchestrator-owned separate step and may record only `APPLIED` plus exact audit
and source hashes. The semantic report uses the redacted projection as both its
provider evidence and displayed evidence; raw customer text remains local and
outside report artifacts.

Redaction change budget: independent test author may create only
`triana-labs/tests/behavior_map/test_redacted_projection_v0.py`; implementation
author may create only
`triana-labs/src/triana_labs/behavior_map/redaction.py` and minimally expose a
`behavior-map redact` command in `triana-labs/src/triana_labs/cli.py` plus
`triana-labs/src/triana_labs/behavior_map/__init__.py`; the orchestrator may
update this packet, `docs/PROVENANCE.md`, `internal/WORKING_MEMORY.md`, the
append-only decision log, and the current decision-memory journal. No new
dependency, UI/backend change, provider call, retry, raw fixture, copied
customer value, or unrelated cleanup is allowed. Acceptance requires an
independently authored black-box test for stable repeated-value placeholders,
all event string surfaces, structure/count preservation, content-free audit,
source immutability, residual refusal, exception-safe paired publication, byte
determinism, and a fresh-process CLI invocation. Pair publication must leave
neither destination after any handled validation or `OSError` failure. It is
not claimed to be crash-atomic across two filesystem renames and does not
defend against a hostile concurrent process racing destination creation; live
runs therefore use new explicit paths inside one operator-owned private
directory, and both artifacts must be present and hash-verified before use.
Final review is independently owned.

Acceptance requires: the existing readable TAU report still passes its frozen
contract; Blitz and HRAI each have exact accepted/rejected/eligible accounting,
corpus-specific grounded context, non-empty useful semantic output or honest
typed abstention, readable evidence on every supporting link, exact provider
and budget lineage, no cross-corpus evidence, independent artifact review, and
reproducible local URLs/commands. Total cumulative reservation must remain at
or below USD 100 and actual provider cost must remain unknown unless directly
reported rather than inferred.

The first-report semantic discovery scope is exactly 34 DEVELOPMENT
conversations per corpus, while deterministic accounting covers every accepted
conversation. Selection is content-independent and reproducible: rank only
DEVELOPMENT trace IDs by SHA-256 of
`behavior-map-discovery-sample-v0\0<normalized-source-sha256>\0<trace-id>`, take
the first 34, then publish the selected-list SHA-256 and the full DEVELOPMENT,
selected, calibration, and holdout counts. This is an initial behavior-discovery
sample, not exhaustive rare-behavior coverage. For Blitz the counts are
624 accepted, 374 DEVELOPMENT, 34 selected, 125 calibration, 125 holdout. For
HRAI they are 185 accepted plus 15 typed source rejections, 111 DEVELOPMENT,
34 selected, 37 calibration, and 37 holdout. Calibration and holdout content
remain outside every semantic request.

Independent three-corpus entry audit blocked the previously accepted TAU
artifact on two deterministic integrity defects. First, every semantic-eligible
conversation that yields no surviving demand episode must appear as an explicit
conversation-scoped emerging/unknown item; `tau2-56` may not silently disappear.
Second, a conversation excerpt spanning one user turn to its assistant response
must preserve every intervening same-turn tool call and result in canonical
source order; it may not select one call and place the aggregate response beside
it while hiding sibling calls. Excerpts remain bounded, and visible truncation
must be explicit rather than silently selective.

The repair ID is `BEHAVIOR-MAP-V0-TAU-AUDIT-INTEGRITY`. Independent test author
may edit only `triana-labs/tests/behavior_map/test_behavior_map_v0.py`.
Implementation author may edit only
`triana-labs/src/triana_labs/behavior_map/__init__.py` and, only if the frozen
test proves renderer behavior itself is defective,
`triana-labs/src/triana_labs/behavior_map/render.py`. Orchestrator documentation
scope is unchanged. No provider calls, prompt/schema changes, checkpoints,
dependencies, adapters, source traces, UI/backend, or semantic-result edits are
allowed. Acceptance requires both independent regressions, all earlier
readability/integrity tests, deterministic regeneration from existing TAU
checkpoints, exact re-audit of semantic coverage and excerpt source order, and
independent final artifact review.

## Active continuation entry gate — 2026-08-07

The owner accepted the Phase 1 result and requested that every supporting
evidence link open a readable conversation-shaped excerpt rather than an
isolated quote or raw JSON event. The deterministic evidence projection must
show, in source order where available:

```text
User message
Agent
  Tool call: <tool name>
  Tool input: <readable arguments>
  Tool result: <readable result/status>
Agent response
Next user message
```

The canonical JSON remains the sole evidence authority. It gains a bounded,
deterministically projected conversation excerpt structure so Markdown and
HTML render the same facts. Existing evidence IDs remain navigable and exact
event sequence/identity remains visible as secondary audit metadata. Trace
content is escaped; renderers do not infer or summarize semantic meaning.

Input: the existing validated PreviewTrace corpus plus the already produced
Behavior Map semantic results. Output: byte-deterministic JSON, Markdown, and
HTML with conversation-shaped supporting evidence. Deterministic code owns
event selection, role/tool rendering, ordering, anchor membership, and
truncation. Models and humans have no new authority. Raw traces remain local;
the excerpt cannot contain fields outside the already authorized canonical
trace projection. Missing neighboring messages or tool results are shown as
absent rather than invented.

Change budget:

- test author: `triana-labs/tests/behavior_map/test_behavior_map_v0.py` only;
- implementation author: `triana-labs/src/triana_labs/behavior_map/{__init__.py,contracts.py,render.py}` only;
- orchestrator: this packet, `internal/WORKING_MEMORY.md`, append-only
  `internal/DECISION_LOG.md`, and the current decision-memory journal;
- no dependencies, provider calls, retries, deployment, app/backend/UI work,
  adapters, source-trace edits, or unrelated formatting;
- maximum scope expansion: one purpose-built synthetic fixture inside the
  existing Behavior Map test file after an orchestrator note.

Acceptance requires an independently authored black-box test proving mixed
user/assistant/tool-call/tool-result evidence is rendered in chronological,
human-readable form in both Markdown and HTML; exact evidence anchors and
event ordinals survive; arguments/results are readable and escaped; a missing
tool result remains explicit; repeated execution is byte-identical; and raw
JSON event blobs are not the primary human presentation. The implementation
author may read but not edit the frozen test. Final verification is the
existing Behavior Map plus Trace-to-Eval focused gate, Ruff, format, mypy,
governance, and diff check. Regenerating the real report may reuse exact
checkpoints only and must make zero provider calls.

Independent test ownership is frozen at
`triana-labs/tests/behavior_map/test_behavior_map_v0.py` SHA-256
`7d972535c9585ab27e9467622645ca3f12c370d564129c1db40442d084cecc19`.
The new focused case is valid RED because canonical `EVENT` evidence lacks the
required `conversation_excerpt`; all pre-failure determinism controls pass.

Independent post-GREEN review blocked the first implementation: a missing-result
tool call could attach an assistant response after an intervening user turn;
transcript citation evidence remained isolated; Markdown could interpret or
lose untrusted markup/backticks; HTML removed literal evidence characters; and
the excerpt had no deterministic size/truncation boundary or readable handling
for JSON-encoded result strings. These are acceptance defects inside this same
continuation, not deferred UX polish. Superseding independent regressions must
be frozen before production repair.

The superseding independent test contract is frozen at SHA-256
`e928420517deede25aeb4cc62d3483357622318e4c7e0b55bda1c5eac6971f23`.
The preserved original acceptance case passes and four causal regressions are
RED: intervening-user boundary, transcript excerpts, bounded/decoded values,
and lossless hostile-content rendering.

The second independent GREEN review retained two blockers: the serialized
bounded-preview wrapper could exceed its advertised 4096-byte maximum after
JSON escaping, and a deeply nested valid JSON-string tool result could raise
an uncaught `RecursionError`. Both are same-slice evidence-integrity failures;
the bound must cover final canonical bytes and pathological decode depth must
fall back to opaque bounded evidence rather than crash or invent structure.

The final superseding independent test contract is frozen at SHA-256
`0bb7486f38cac27ec7b3235697fbc6caee11d1bd3705e398647715f7d1db2ec6`.
Its two focused cases are valid RED on truthful final canonical byte accounting
and deep JSON recursion containment; all earlier readable-evidence controls are
preserved.

Final exit: 51/51 Behavior Map tests and 43/43 adjacent Trace-to-Eval tests
pass, the seven readable-evidence cases pass, Ruff/format/mypy/governance and
diff checks are green, and independent adversarial review is PASS. The real
TAU report was deterministically refreshed with zero provider calls: all 478
EVENT and 132 TRANSCRIPT evidence rows contain bounded conversation excerpts.
Report id is
`sha256:986251c0d2315674ae40075ff9e13053988ffefb87dd96181f323bd2408b6d9e`;
the local HTML is HTTP 200 and browser inspection confirms readable source
order with raw canonical JSON secondary and collapsed.

Canonical base: the documentation-freeze commit produced from current
`codex/selfserve-v0` after this packet is committed.

Authority: `triana-labs/CHARTER.md`, the append-only
`internal/DECISION_LOG.md`, and
`internal/BEHAVIOR_MAP_PHASES_2026-08-07.md`.

## Active product outcome

One authorized trace source produces a useful single-corpus Behavior Map:

1. Corpus overview;
2. User Demand Map over multi-goal demand episodes;
3. multi-label Agent Behavior Map;
4. Emerging and Unknown Behavior;
5. exact evidence;
6. editable Questions for You.

The canonical machine artifact is strict JSON. Human artifacts are one
readable Markdown file and one mechanically equivalent plain HTML file. This
slice stops before backend, self-serve upload, and application UI wiring so the
real result can be audited before plumbing resumes.

This slice contains no behavior differences, outcome slicing, eval proposal,
existing-eval import, Track/Edit/Defer, frozen evaluator, L4/first-broken-link,
simulation, release verdict, or accepted-truth claim.

## Public seam

```text
run_behavior_map(
    manifest_path,
    output_dir,
    *,
    primary_model=None,
    audit_model=None,
    agent_context=None,
) -> BehaviorMapReportV0
```

The function is exported from `triana_labs.behavior_map`. It reads the existing
authorized evidence-manifest/source boundary, writes these immutable artifacts,
and returns the same report object:

```text
behavior-map.json
behavior-map.md
behavior-map.html
behavior-map-checkpoints/
```

The CLI seam is:

```text
triana behavior-map run --manifest <path> --output-dir <path>
```

Provider selection remains explicit configuration. Tests call the Python seam
with fakes and make no provider call.

## Contracts

### `DemandEpisodeV0`

One independently actionable observed user demand or a materially revised
success condition. Required fields:

- deterministic `episode_id`;
- `conversation_id`;
- `ordinal` within the conversation;
- proposed `goal`, `requested_action`, `subject`;
- `constraints`, `fallbacks`, and optional `supersedes_episode_id`;
- existing `start_turn_ordinal` and `end_turn_ordinal`;
- one or more exact `EvidenceCitationV0` user citations;
- status `PROPOSED`, `UNKNOWN`, or `UNSUPPORTED`.

Episodes may share turns when one utterance contains several goals. A
clarification, preference, or fallback is not automatically a separate episode.
A material change from one requested action to another closes the prior episode
as superseded and links the new episode. Any uncovered material request remains
an explicit unknown; code never fabricates a catch-all episode.

### `UserPopulationV0`

A proposed denominator-worthy group of similar demand episodes. Required
fields include deterministic identity, label, definition, ordered episode IDs,
support, visibility, representative citations, method identity, and audit
state. Visibility is code-owned:

- support >= 3: `PROPOSED_POPULATION`;
- support 1-2: `EMERGING`;
- ambiguous, ungrounded, unsupported, or unstable: `UNKNOWN`.

Each eligible episode has exactly one primary population membership or an
explicit emerging/unknown disposition. Conversations may participate in
several populations through different episodes.

### `AgentBehaviorOccurrenceV0`

One evidence-linked observed agent behavior attached to one or more episodes.
Required fields:

- deterministic occurrence identity and conversation identity;
- source lane `DETERMINISTIC`, `SEMANTIC`, or `HYBRID`;
- structured `action`, `object`, `condition`, and optional
  `observed_effect`;
- attached episode IDs;
- exact transcript citations and/or canonical event/tool evidence IDs;
- proposal/audit status and method identity.

Several occurrences may attach to one episode or conversation. A semantic
occurrence without an exact citation abstains. An incomplete export cannot
support claims such as lying, fabrication, policy violation, or failure.

### `AgentBehaviorPatternV0`

A recurring, specific consolidation of behavior occurrences. Code owns
membership and support. The model may propose a label and definition. Generic
primary language is rejected, including labels whose only meaning is tool use,
information requested/returned, action observed, response present, or handling
unknown. A valid primary label must name a concrete action plus an object,
condition, or observable consequence.

### `BehaviorMapReportV0`

Contains source/accounting, proposed or supplied agent context, episodes,
populations, behavior occurrences and patterns, emerging/unknown inventory,
evidence handles, questions, gaps, semantic audit, method/model identity,
checkpoints, budget, and canonical report identity. It contains no public
eval-proposal, comparison, difference, verdict, or human-ruling collection.

## Model boundary

Terra is the primary semantic author:

1. per-conversation demand episodes and semantic behavior occurrences;
2. population consolidation;
3. recurring behavior-pattern consolidation;
4. proposed agent context only when none is supplied.

Luna is a separately identified bounded auditor. It audits every final
population/pattern plus a deterministic calibration sample of episodes and
members as `SUPPORTED`, `MERGE`, `SPLIT`, `UNSUPPORTED`, or `UNCERTAIN`. Luna
does not rewrite Terra output and is never silent fallback. Disagreement routes
to emerging/unknown or an explicit question.

Deterministic code owns projection, redaction, exact citation validation,
identities, ordering, episode/population/pattern membership, support, visibility,
generic-language refusal, audit sampling, checkpoints, budgets, lineage,
serialization, and rendering.

The model must not receive source rewards, TAU expected action sequences,
hidden benchmark criteria, locked holdout truth, or unrelated conversations.

## Privacy and execution

- Raw traces remain local/private.
- Only the manifest-authorized redacted conversation projection may egress.
- Redaction and egress validation occur before provider-bound hashing/calls.
- Exact provider deployment identity, model version, SKU, capacity, endpoint,
  and credential boundary are verified before live egress and recorded without
  secrets.
- The cumulative semantic-analysis budget is USD 50, including the prior
  approximately USD 24.60 reservation/usage. No retry, fallback, or
  rerun-to-green is allowed.
- Terra and Luna have distinct provider identities. Failure of one cannot route
  to the other.
- Fixtures and automated tests use fakes only.
- No deployment, provisioning, AWS mutation, Supabase configuration, public
  ingress, or secret output is authorized in this slice.

## Gaps and refusal behavior

| Condition | Behavior |
|---|---|
| provider absent | deterministic accounting plus `SEMANTIC_ANALYSIS_UNAVAILABLE`; no fake map |
| some valid checkpoints exist | publish supported partial map and exact missing-stage gaps |
| invalid/non-exact citation | reject the semantic row or abstain; never clip into truth |
| material request uncovered | explicit unknown episode/question |
| population support 1-2 | `EMERGING` |
| vague behavior wording | exclude from primary patterns and retain typed rejection |
| Terra/Luna disagreement | route affected item to unknown/question; preserve both identities |
| incomplete tool export | retain observation limit; do not accuse or infer missing action |
| source outcome present | preserve only in lineage; do not join, slice, compare, or explain it |
| budget reservation unavailable | stop before egress with `SEMANTIC_BUDGET_EXCEEDED` |
| checkpoint tamper/method mismatch | refuse reuse and report integrity failure; do not silently recompute live |
| renderer failure | retain canonical JSON and typed artifact gap; no false completion |

## Provenance

Permitted source mining is Agentagon commit
`063ad3ed54f4a9646e7040cc6a203615b0de8dcd`:

- `agentagon/exploration_v1/pipeline.py` — evidence projection, facet validation,
  bounded hierarchy, population accounting, report structure;
- `agentagon/exploration_v1/prompts.py` — evidence-grounded semantic proposal
  patterns;
- `agentagon/exploration_v1/llm.py` — bounded structured-call/checkpoint ideas;
- `agentagon/measurement_discovery_v2/pipeline.py` — deterministic behavior
  evidence cells only;
- relevant independent Agentagon tests for exploration/accounting invariants.

Existing Triana supplies trace adapters, canonical evidence, privacy/egress,
structured Azure transport, byte-bounded batching, strict validation,
checkpointing, budget accounting, and CLI patterns.

Before copying or adapting production code, the implementation author records
exact source file/commit, destination, copied versus adapted status, applicable
license, and checks in `docs/PROVENANCE.md`. Agentagon is not added as a runtime
dependency. Generated reports, caches, raw corpora, and embedded third-party
data are not copied.

## Change budget

### Test-author ownership

- new `triana-labs/tests/behavior_map/**`;
- purpose-built synthetic fixtures only under that directory.

The test author must not edit production, canonical docs, provenance, existing
Trace-to-Eval tests, or unrelated fixtures.

### Implementation-author ownership

- new `triana-labs/src/triana_labs/behavior_map/**`;
- bounded additive exports in `triana-labs/src/triana_labs/__init__.py` only if
  required;
- bounded additive CLI parsing/invocation in
  `triana-labs/src/triana_labs/cli.py`;
- bounded reuse-oriented changes in
  `triana-labs/src/triana_labs/trace_to_eval/{adapters.py,semantic.py}` only
  after reporting why a new behavior-map module cannot safely call the existing
  seam;
- exact provenance additions in `docs/PROVENANCE.md`.

### Orchestrator ownership

- this packet, decision log, working memory, phase plan, decision journal;
- test freeze hashes and verification evidence;
- no direct production or acceptance-test repair.

### Explicitly untouched

- `triana-core/**` and suspended Release Review V1;
- `triana-backend/**`, `triana-app/**`, migrations, auth, entitlements, RDS,
  S3, DBOS, deployment, Terraform, ECR, GitHub, and infrastructure;
- existing Trace-to-Eval semantics and report artifacts except bounded shared
  helper reuse explicitly reconciled by the orchestrator;
- raw TAU, Blitz, HRAI, provider responses, credentials, and locked holdouts.

No new production dependency is allowed. Maximum scope expansion is one
additional behavior-map production module and one synthetic test fixture after
an orchestrator note. Any backend/UI/self-serve work is a subsequent BM7 slice.

## Independent acceptance contract

The test author must freeze black-box cases for:

1. one conversation containing two simultaneous goals produces two episodes
   that may cite the same turn;
2. preferences/fallbacks stay constraints rather than becoming padded goals;
3. a material change of requested action creates a linked superseding episode;
4. one episode/conversation carries multiple agent behaviors;
5. semantic citations must be exact and resolvable;
6. deterministic tool/event facts and semantic behaviors remain distinct;
7. support 3 becomes proposed population while support 1-2 is emerging;
8. every eligible episode is accounted for once or explicitly unknown;
9. vague primary behavior language is rejected without hiding the occurrence;
10. a missing provider produces typed gaps and no invented semantic map;
11. Terra primary and Luna audit identities/disagreement are preserved with no
    fallback or rewrite;
12. source outcome data cannot appear as a comparison, difference, causal
    explanation, or subgoal result;
13. repeated fixture execution is byte-identical and checkpoint identity is
    method-bound;
14. Markdown and HTML contain exactly the six Phase 1 sections, usable labels,
    evidence anchors, editable questions, and no eval/difference placeholders;
15. prompt-injection text is treated only as evidence and cannot change schema,
    model role, budget, or output structure;
16. budget refusal occurs before a model call and secrets/raw provider payloads
    never enter artifacts.
17. Terra primary and Luna auditor identities are independently role-authorized;
    either mismatch refuses both provider calls with a typed role-specific gap.
18. valid exact checkpoints are reused without provider calls and tamper refuses
    before egress;
19. semantic extraction is one conversation per provider request;
20. population and behavior consolidation remains bounded and lossless across
    more than one hierarchy level;
21. unknown, unsupported, or unattached proposals cannot become published
    populations or patterns;
22. live role authorization binds provider and endpoint as well as model ID;
23. the cumulative USD 50 reservation is enforced before either role calls;
24. one episode cannot cite evidence from a different conversation;
25. missing or unknown audit items remain visible typed uncertainty;
26. human artifacts expose representative demands, occurrence-level multi-label
    behavior, evidence lanes, method, limitations, quality accounting, and gaps;
27. absent optional agent context is inferred from the eligible corpus rather
    than silently from only its first batch.
28. final provider lineage and reserved-cost accounting are sampled after calls;
29. preflight reserves both roles' complete configured run maxima against the
    cumulative USD 50 ceiling before either role calls;
30. schema-valid checkpoint-result tamper refuses before egress;
31. checkpoint reuse is bound to provider, endpoint, deployment version, SKU,
    capacity, and non-secret credential boundary;
32. readable TAU JSON-wrapped assistant evidence resolves exact escaped quotes
    and newlines against its canonical projection;
33. provider citations name canonical `event_sequence`, never ambiguous
    conversational `turn_ordinal`;
34. hierarchy recursively reaches one globally reconciled taxonomy while every
    request remains bounded;
35. ungrounded inferred context becomes typed unknown rather than publication;
36. human reports print actual typed gap codes and understandable limitations;
37. generic deterministic tool evidence is summarized rather than dumped as
    hundreds of low-value rows.
38. missing or unknown audit rulings remove affected items from the primary map
    and route their members to emerging/unknown or an explicit question;
39. synonymous vague behavior labels such as `uses tools` cannot publish;
40. every hierarchy level conserves episode and occurrence membership or emits
    a typed loss/no-reduction gap;
41. every rendered semantic occurrence exposes its identity and navigable exact
    evidence anchors.
42. rejecting one vague behavior routes only its attached members unknown and
    cannot contaminate an unrelated specific valid behavior.
43. one conversation-level extraction failure is attempted once, becomes a
    conversation-scoped typed unknown, and cannot stop later conversations;
44. one audit-item provider failure becomes item-scoped uncertainty, removes
    that item from primary publication, and cannot stop later audit items.

Expected RED must be caused by the absent `triana_labs.behavior_map` public
seam, not syntax, fixtures, imports, or dependency failure.

## Orchestrator adversarial matrix

After implementation GREEN, the orchestrator additionally checks:

- one utterance with two goals and one shared constraint does not duplicate the
  shared constraint as a third goal;
- one aggregate “return everything” request is not split per item without
  evidence that the items became independently actionable;
- an agent behavior citing only user text is rejected;
- a deterministic repeated-tool occurrence survives rejection of a vague
  semantic label;
- HTML escaping prevents trace content from injecting markup or script;
- reordering model rows cannot change canonical public identities;
- a Luna `SPLIT` audit never mutates the Terra item in place;
- a partial last provider stage preserves earlier valid exact checkpoints and
  reports remaining missing work;
- no banned public key or heading containing eval, difference, comparison,
  reward, verdict, or L4 appears in the human report.

## Verification commands

Valid RED and focused GREEN:

```text
cd triana-labs
UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked pytest -q tests/behavior_map
```

Final local gate:

```text
cd triana-labs
UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked pytest -q tests/behavior_map tests/trace_to_eval
uv run --locked ruff check src tests/behavior_map tests/trace_to_eval
uv run --locked ruff format --check src tests/behavior_map tests/trace_to_eval
uv run --locked mypy src
cd ..
./scripts/verify-governance.sh
git diff --check
```

The implementation author does not execute a live provider call. After local
GREEN and change-budget reconciliation, the orchestrator performs read-only
Azure identity/capacity preflight, freezes exact live configuration and
remaining reservation, and alone authorizes one bounded TAU² Retail run.

## Exit and non-completion

The local implementation slice is complete only when independent tests, the
adversarial matrix, deterministic replay, render inspection, provenance, and
governance are GREEN. It is not a product-value exit until the exact authorized
57-conversation TAU² Retail run produces a readable Behavior Map and the
orchestrator audits the displayed populations, behaviors, unknowns, citations,
cost, and questions.

Provider absence, partial semantics, or audit disagreement may yield a truthful
typed-gap artifact but cannot be called the useful Phase 1 launch result.

## Independent RED freeze — 2026-08-07

The independent test author owns exactly
`triana-labs/tests/behavior_map/test_behavior_map_v0.py`, SHA-256
`667a29b07b3c65cd1b35c544cd84c060dab5481bbb9425bcb0826075b1ca5516`.
It freezes all forty-four acceptance behaviors listed above across forty
black-box cases. The orchestrator
rejected the preliminary test bytes because its population fake keyed only by
conversation and silently assigned the simultaneous return episode to the
cancellation population. The corrected test keys by conversation and requested
action and asserts the cancellation population includes the cancellation
episode and excludes the return episode. A later fixture correction explicitly
authorizes the independently identified Luna auditor and adds atomic refusal
when either configured model identity is not authorized; this supersedes only
the prior test-file hash and incomplete role-authorization fixture. Independent
post-implementation review then reproduced checkpoint re-egress, cross-corpus
extraction, flat hierarchy loss, unsupported promotion, weak provider binding,
post-call budget accounting, cross-conversation citations, silent audit gaps,
first-batch-only context, and insufficient human explanation. Eleven focused
regressions supersede the second hash without weakening the original seventeen
controls. A final post-hardening read-only review reproduced stale post-call
lineage, next-call-only cumulative reservation, checkpoint binding/integrity
gaps, TAU wrapped-evidence coordinate loss, non-global hierarchy, ungrounded
context, and report-density failures. Ten additional focused regressions
supersede the third hash while retaining all twenty-eight controls.
Final signoff then found missing-audit items still present in the primary map,
vague synonymous labels, silent hierarchy membership loss, and semantic
occurrences without navigable evidence. The existing audit-uncertainty case was
amended to freeze those four same-slice obligations, superseding only the test
hash while preserving the collected test count. The final mixed-specificity
fixture then proved vague-language routing contaminated unrelated valid
behavior; its isolation assertion supersedes only the test hash again.
The first real TAU run then proved one deterministic extraction failure stopped
all later conversations and one audit failure stopped all later items. Two
per-unit isolation regressions supersede the test hash and expand the inventory
without retrying or hiding either failure.

The corrected continuation then reached the full corpus control path but all
eighteen Luna audit items failed. One bounded diagnostic reproduced HTTP 400:
the shared client forced `temperature=0`, while the Luna deployment accepts
only its default temperature. The independent provider-wire test in
`triana-labs/tests/trace_to_eval/test_foundry_json_object_compatibility.py` at
SHA-256 `2181deb9ff3d3a1965df3181b994ca6aa615676ebc66bc7d4286fa5c38c489eb`
freezes omission of the explicit temperature while retaining JSON-object mode,
strict schema validation, no SDK retry, token cap, timeout, and budget
accounting. Its smallest production correction and all 83 focused adjacent
checks are GREEN. Product-value exit remains open pending one explicitly
budgeted checkpoint continuation and independent human artifact audit.

That continuation repaired Luna and produced the first genuinely useful analyst
draft: 45 episodes, two user populations, three recurring agent patterns, six
human questions, and 11/11 successful independent audit calls. Independent
artifact review still withheld self-serve launch because the report showed an
episode-row `45/45` as coverage, omitted population-assignment coverage, left
accepted citations outside episode bounds, overstated sampled audit support,
repeated 47 gap bullets, and placed questions after the evidence appendix. The
launch-honesty contract is now frozen at Behavior Map test SHA-256
`c57790a09743db77d565cdb43a5c0536cc76edcc846c63438ae5eeaa5992170` and
GREEN with all 43 adjacent Trace-to-Eval checks. One final bounded checkpoint
continuation plus human artifact audit remains the product-value exit.

The launch-honest preview then exposed two final trust failures: one
water-bottle episode retained desk-lamp-only sibling evidence, and one
single-occurrence observation was presented as recurring. The trust gate is
frozen at Behavior Map test SHA-256
`f70233d41111606d7ebf0321a74668da34b288b4d534b7e9e43060276b29f7c9`.
It conservatively detaches only explicit distinct sibling-subject citations,
emits linked uncertainty, and demotes support-below-two recurrence claims while
preserving their occurrences and evidence. All 44 Behavior Map and 43 adjacent
Trace-to-Eval checks plus independent review are GREEN. Final live artifact
validation remains the only open product-value gate.

Final product-value exit passed on report
`sha256:df7222f892a637ed8a9eb3ea788ae73205efe79be4fc5b365168852d8b1911f4`.
The 57-conversation TAU² artifact kept 12 calibration and 11 holdout
conversations sealed, produced 50 episodes across 27/34 eligible conversations,
assigned 25/50 episodes to four demand groups, published three behavior patterns
with distinct support at least two, exposed eight questions before exact
evidence, and closed both final trust failures in the live bytes. The final run
reserved USD 3.53; the conservative cumulative reservation is USD 48/50 and
actual provider cost is unknown. No further paid run is authorized by this
slice. Phase 1 exits only as a proposed self-serve preview, never complete or
accepted behavioral truth.

Valid RED command:

```text
cd triana-labs
UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked pytest -q tests/behavior_map
```

Observed result: collection stops only at
`ModuleNotFoundError: No module named 'triana_labs.behavior_map'`; one error in
3.39 seconds against an isolated export of pre-implementation commit `d35dac1`.
Ruff check, Ruff format check, Python compilation, file hash, and diff check are
GREEN. Against the first real-run implementation, the live correction suite
produces two intended failures and thirty-eight passing controls in 8.02
seconds. The test-owned path is frozen. The implementation author may read it
but must not edit it.

## Integrity repair freeze — 2026-08-07

The three-corpus generalization preflight exposed two release-blocking local
integrity defects before either new report completed: ordinary umask recreated
private report directories as `0755`, and failed or interrupted provider calls
left no durable attempt record, so a restarted process could retry a consumed
stage and understate cumulative reservation. Provider execution is paused.

The independent test author supersedes the Behavior Map test bytes at SHA-256
`6b4792392bfac32087014d0658fe902a2b9d3172bbe9078a3ed969f8e55a3910`.
Three focused cases are valid RED: every attempted stage must durably become a
validated success checkpoint or a content-free `FAILED`/`IN_FLIGHT` tombstone;
a restart must never reissue a consumed identity and must surface it as typed
unknown; historical attempts must remain in attempted-call and conservative
reservation lineage; and all output/checkpoint directories and files must be
`0700`/`0600` regardless of ordinary umask. Retry and fallback remain `NONE`.

The same independent author supersedes the redaction projection tests at
SHA-256
`56a8b458b029505cebf415bbb90155e4c32e19885208b757e2ae14e212d3f1cd`.
The two added publication controls are already GREEN: existing targets are
never clobbered, and a handled second publication failure removes the first
published counterpart. This supersedes the unrecorded intermediate
`ef600e020e912b9fc1f4a738f29b5edcc0cc9030b8ef708f9548e004c30f8e1e`
bytes while preserving all prior redaction controls.

The repair change budget permits production edits only in
`triana-labs/src/triana_labs/behavior_map/__init__.py`; acceptance tests remain
test-author owned. No dependencies, schemas outside Behavior Map V0, adapters,
CLI, rendering language, provider configuration, raw data, UI/backend, or
infrastructure may change. The implementation author runs no provider. The
orchestrator alone reconciles the six conservative Blitz Luna attempts and one
HRAI Luna attempt already consumed, selects fresh DEVELOPMENT conversations
for those identities, and may restart only after focused GREEN plus independent
review. Existing successful partial checkpoints remain immutable abandoned-run
evidence and are not inputs to the fresh reports.

Independent adversarial review then proved the first tombstone implementation
accepted descriptor and identity tampering and used process-visible rename
without crash-durable file and parent-directory sync. The test author therefore
supersedes only the Behavior Map test bytes at SHA-256
`e3f2323e30d2cb02bb2eb24332d195c75ce3178252e815681e5f381df81c3226`.
Four focused cases are valid RED: wrong routing IDs, unexpected/raw descriptor
keys, a recomputed filename around a malformed one-key identity, and absent
file-plus-directory `fsync` before egress and after final replacement. The
production change budget remains the single Behavior Map implementation file;
provider execution remains paused until GREEN and independent re-review.

A further independent adversarial probe recomputed the public descriptor digest
after changing a routing ID while retaining the provider-call identity and
filename. The test author supersedes only the Behavior Map test bytes again at
SHA-256
`fb4ffab87fddaf7cb7a2ae2cfa7dc168e75a37b239108d28a6f3058e819c96db`.
The one added case is valid RED and requires tombstone reuse to compare its
stored descriptor exactly with the descriptor derived from the current
hash-bound payload before returning a consumed-attempt state. Scope and paused
provider status are unchanged.

Package-configured Ruff then mechanically wrapped the final regression without
changing its assertion. The frozen Behavior Map test bytes are therefore
superseded one final time at SHA-256
`88169439dc4b7d92edb9c762f84cefc51a92a780b4a0ef318dbeca93b00dc4b7`;
all sixty-two cases in that file remain GREEN.

Final independent ordering review showed that a missing earlier extraction
checkpoint could egress before a later, internally self-consistent but rerouted
tombstone was reached. The test author supersedes the Behavior Map test bytes
at SHA-256
`d9f1168e94d2583b64954813566dcc4fd62c23d6cba712e5b915c79ff45827dc`.
The one added case is valid RED and requires every statically knowable existing
extraction artifact to be validated against its planned current payload before
the first missing extraction identity may egress. Scope remains the same one
production file and providers remain paused.

## Blitz privacy and Markdown canonical rerun — 2026-08-07

The first Luna-primary Blitz report is mechanically sound and semantically
promising but blocked from release. Independent audit found bare shipment
identifiers shaped `GS` plus at least nine digits and `NM` or `NN` plus at
least nine digits in the redacted source, checkpoints, and final evidence.
The original detector required a nearby order/tracking keyword and residual
validation reused that same blind detector. The Markdown renderer also emitted
population detail between table rows, leaving every row after the first
outside the table. The localhost Blitz server was stopped immediately.

The new independent acceptance contract must freeze both observed identifier
families as direct and structured-tool values, require deterministic stable
replacement plus residual refusal, and preserve structural trace identities
and existing placeholders. It must also require all Markdown population rows
to remain contiguous before per-population detail while HTML/JSON semantics
remain unchanged. Test-author budget is only the two existing Behavior Map test
files. Production-author budget is only
`triana-labs/src/triana_labs/behavior_map/redaction.py` and
`triana-labs/src/triana_labs/behavior_map/render.py`. No dependency, adapter,
schema, CLI, semantic engine, provider boundary, UI/backend, or infrastructure
change is allowed.

The leaking report/checkpoints remain private abandoned evidence and cannot be
mutated into a canonical report. After GREEN and independent review, the
orchestrator may re-redact the original normalized Blitz source, exclude all
thirty-nine distinct Blitz conversations previously attempted, deterministically
select thirty-four untouched DEVELOPMENT conversations, and run one fresh
Luna-primary/Terra-audited report with no retry/fallback. Prior conservative
reservation is USD 70.14; the complete new run maximum is USD 19.62, keeping
the cumulative ceiling at USD 89.76/100. HRAI remains a zero-semantic typed
failure artifact and is not rerun.

The independent test author froze the redaction acceptance contract at
SHA-256 `46d3770e703f56e870d90757d1cb433e00baf273b024c97f00a1be36c64ee2cb`
and the Behavior Map rendering contract at SHA-256
`e09af238a19ab3936256ee75833440524260c4609b85a63cf205f8f3839adea6`.
The expected RED state is two privacy failures and one Markdown failure;
format and lint checks on the test changes pass.

Implementation exposed two fixture-local contradictions: raw substring absence
could not coexist with preserving an identifier embedded in an ordinary
alphanumeric token, and the generated-token count included the explicitly
preserved pre-existing placeholder. The independent test author corrected only
those assertions without weakening standalone-identifier absence. The
redaction acceptance contract is superseded at SHA-256
`68225f1a0d4b7957281c4d2d10a2ee39853cddbcd27a4db524564a1966058304`;
the rendering contract remains
`e09af238a19ab3936256ee75833440524260c4609b85a63cf205f8f3839adea6`.
Focused privacy and Markdown checks are GREEN.

## Blitz address residual canonical rerun — 2026-08-07

The frozen standalone-identifier gate passed and one fresh Luna/Terra run
completed, but the orchestrator's broader pre-publication audit found
street-address-like customer text in fourteen redacted-source traces, mostly
user messages, and confirmed that one such phrase propagated into semantic
output. The report at
`/private/tmp/triana-blitz-behavior-v1/report-clean` therefore remains private
non-canonical evidence even though its identity, rendering, and configured
identifier residual checks pass.

The next independent acceptance contract must cover address phrases whose
street markers appear without a preceding `address` keyword, including common
house, flat, plot, colony, lane, road, street, sector, nagar, apartment,
building, and society forms. It must require stable recursive replacement,
independent residual refusal when replacement is bypassed, existing-placeholder
preservation, structural identity preservation, and ordinary non-address prose
preservation. Independent audit also found generic uppercase-alphanumeric
order/tracking shapes: the contract must redact values under structured keys
that explicitly denote order, tracking, AWB, shipment, reference, ticket, or
identifier fields, and shapes in explicit order/delivery/tracking text context,
while preserving unrelated ordinary alphanumeric tokens. Test-author budget is only
`triana-labs/tests/behavior_map/test_redacted_projection_v0.py` and
production-author budget is only
`triana-labs/src/triana_labs/behavior_map/redaction.py`. No rendering, adapter,
schema, CLI, semantic, provider, UI/backend, dependency, or infrastructure
change is allowed.

After GREEN and independent review, the orchestrator may re-redact the original
normalized Blitz source, exclude all seventy-three distinct conversations from
the five aborted, first blocked, and address-blocked runs, select thirty-four
untouched DEVELOPMENT conversations, and run one fresh Luna-primary/Terra-
audited report with no retry/fallback. The prior conservative reservation is
USD 74.57; the complete new run maximum is USD 19.62, keeping the cumulative
ceiling at USD 94.19/100.

The independent test author froze the address and generic order/tracking
privacy contract at SHA-256
`edaebda5e53faa1dc91a8d410130d01412c5fd1db052724487cdd663d7553825`.
The expected RED state is four failures and one already-passing contextual
residual-refusal case; Ruff formatting and lint pass. The production budget
remains the single redaction module.

The real-corpus refusal then exposed only a structural `call_id` false positive;
the implementation author proved all 1,238 structured residual candidates came
from that top-level relationship field and narrowly exempted it while leaving
nested/plain fulfillment `id` fields covered. A broader independent scan then
found address variants fragmented by earlier numeric/person rules. The test
author supersedes the privacy contract at SHA-256
`adbd81a0328fe652868a7117ecea6b6691840639eeb6f6dea133198f227f86cb`,
requiring whole-span address replacement before postal, long-number, or person
rules. The expected focused state is one RED failure; Ruff remains GREEN.

## Blitz location residual final rerun — 2026-08-07

The address/order repair passed its frozen and actual-corpus gate, and the next
Luna/Terra report produced the strongest semantic draft so far, but expanded
post-run privacy audit found fifteen high-confidence customer-location forms in
the redacted source: five leading-number street/sector/phase/lane forms and ten
named landmarks preceded by `near`, `opposite`, or `behind`. One persisted into
a private checkpoint; none persisted into the final render. The report at
`/private/tmp/triana-blitz-behavior-v3/report-clean` remains private non-
canonical evidence.

The final test-author budget is only the redaction test file and must cover both
location families, stable whole-span ADDRESS replacement, replacement-bypass
residual refusal, and ordinary non-location uses of the same words. The final
production-author budget is only the redaction module. No other code, data,
dependency, provider boundary, or infrastructure surface may change. After
GREEN and independent actual-corpus review, the orchestrator may exclude all
107 previously attempted conversations, select thirty-four untouched
DEVELOPMENT conversations, and run one last Luna-primary/Terra-judged report
with no retry/fallback. Prior conservative reservation is USD 79.65; the
complete run maximum is USD 19.62, keeping the cumulative ceiling at USD
99.27/100.

The independent test author froze the final location contract at SHA-256
`efccbb16a0e29f298be95366b42c24fde75c550939ccdf643fb8637f349adaab`.
Focused expected RED is three failures with sixteen deselected; Ruff formatting,
lint, and diff checks are GREEN.

Final implementation and runtime reconciliation: the frozen location test hash
remained exact, 83 focused Behavior Map tests plus Ruff formatting/lint passed,
and independent actual-corpus review found zero configured or expanded
residuals across 624 traces and 5,229 events. The projection preserves exact
trace/source identities and stable injective pseudonymization across all 622
tool call/result relationships. The canonical redacted Blitz source is
`sha256:0904a38121d5af58fd1919cfa8b5a36965afa3d2eb7a5b0f3489ac2db099333d`.

The final untouched-sample Blitz report is
`sha256:738e3001837f3aba5033c2ecfbf878ceadfe5d01813515f20bf21b4a324d438a`
at `/private/tmp/triana-blitz-behavior-v4/report-clean`. Artifact SHA-256 values
are JSON `1324e53c0e287c0ac5f92454f922a0abb8d946b3ddcdc6c4308d1751521b4381`,
Markdown `1e5c95f64c8d0ee2f5190c4809d4a838d442017b90df8cbdffd95d86d8e68a32`,
and HTML `f2b838fcc1ff42c0ea1b8ef2c176b4ec91e91e2bbbc3d44e9b335efad07b7a17`.
It is served privately at `http://127.0.0.1:8910/behavior-map.html`.

Independent final audit passed report identity, byte regeneration, 44 success
checkpoints plus six durable tombstones, private modes, reference/citation/link
closure, exact source/audit hashes, 107 prior-conversation exclusions, sealed
125/125 calibration/holdout groups, and all expanded privacy scans. Luna made
41 attempts with 35 successful stages and USD 2.95 reserved; Terra judged 9/9
items with USD 1.62 reserved; no retry/fallback occurred. Cumulative
conservative reservation is USD 84.22/100 and actual billing is unknown.

The final product-value boundary is partial: 14 episodes survive across 12/34
selected conversations, one support-one user population remains EMERGING, and
three useful agent-handling patterns have support 5/4/4. Twenty-eight
emerging/unknown rows, 37 typed gaps, five questions, and 106 readable evidence
records remain visible. This passes as a private proposed Behavior Map, not an
accepted taxonomy or a wow-complete user-demand result. The canonical TAU²
report remains
`sha256:4b0e1f76a652656c6586e74118e92b16b750ec97436c08c6d33d63cfde85e6e1`;
the HRAI artifact remains the truthful zero-semantic typed provider-failure
report
`sha256:fe95e939ebb0e2dfd01c3df9a9bf35b2d702d90df05c3d5793569f4e86a5eabe`.

Repository-wide exit gate passed outside the restricted socket sandbox:
governance, locked dependency resolution, formatting, Ruff, strict mypy, all
746 tests, source distribution, wheel build, clean-environment installation,
and installed-artifact acceptance/repeatability checks are GREEN. Evidence is
under `/private/tmp/triana-labs-verify.nnM9OV`. The first sandboxed invocation
reported 716 passes and thirty pre-existing fake-HTTP failures solely because
loopback socket binding was denied; the unchanged escalated rerun passed all
746 tests.

## BEHAVIOR-MAP-V0-AUDIT-SCOPE-PROJECTION — 2026-08-07

Status: **COMPLETE — INDEPENDENT FINAL PASS**

Canonical base: `57ab5fdcee7ca252543817adcf8a53bce7b11af7` on
`codex/selfserve-v0`. Active authority is `triana-labs/CHARTER.md`; this slice
advances the Phase 1 promise that proposed populations, support, evidence, and
typed uncertainty are internally consistent.

Observed failure: the canonical private Blitz V4 checkpoints contain fourteen
surviving episodes and ten pre-audit population memberships. Three independent
population-scoped audits are `SUPPORTED`, while two separately sampled
episode-scoped audits are `UNSUPPORTED`. The current deterministic projection
turns both episode IDs into population-wide disputes and deletes every parent
population containing either member, reducing assignment from ten of fourteen
to one of fourteen. This conflates two evidence scopes.

Single falsifiable hypothesis: if post-audit projection distinguishes an audit
whose subject is a population from one whose subject is an episode, an
unsupported episode can be detached and the remainder reprojected without
invalidating a separately supported population. This is falsified if the
reprojected membership, support, visibility, identity/lineage, assignments,
denominators, or preserved audit evidence disagree with a fresh deterministic
projection of the same surviving members.

Input is the already validated in-memory episodes, populations, semantic audit
items, gaps, and evidence produced by Behavior Map V0. Output is the same
canonical report contract with audit scope applied correctly. Deterministic
code owns subject typing, membership detachment, support arithmetic,
visibility, population identity/lineage, episode assignment, denominators,
sorting, and typed gaps. The audit model owns only its immutable proposal for
the exact audited subject. A human creates no new ruling in this slice.

Public behavior is frozen as follows:

| Audit subject and decision | Deterministic result |
| --- | --- |
| episode `UNSUPPORTED`, `MERGE`, `SPLIT`, or `UNCERTAIN` | preserve the audit item and episode as disputed/partial evidence; detach only that episode from each population membership |
| parent population independently `SUPPORTED` | keep the population after member detachment if the remaining membership is valid; recompute support, visibility, identity and lineage |
| parent population `UNSUPPORTED`, `MERGE`, `SPLIT`, or `UNCERTAIN` | remove the whole population under the existing audit contract and preserve its audit evidence/typed uncertainty |
| remaining population support at least three | publish as `PROPOSED_POPULATION` with recomputed support and identity |
| remaining population support below three but nonzero | retain only through the existing `EMERGING` typed visibility; do not publish it as denominator-worthy |
| no remaining members | remove the population and retain the affected episodes/audit evidence through existing typed uncertainty |

Missing audits retain their existing typed behavior. Pattern audits, citation
validation, redaction/privacy, provider binding, budget, retry/fallback, and
minimum-support semantics are unchanged. Report summaries and questions must
be derived after the corrected projection, never patched independently.

Privacy and execution: local deterministic fixtures and, only after GREEN,
the existing sanitized Blitz V4 checkpoints under `/private/tmp` may be read.
No provider call, credential use, raw-corpus mutation, network egress, or
report overwrite is permitted. A no-call trap is required for any checkpoint
reprojection.

Change budget:

- test author owns only
  `triana-labs/tests/behavior_map/test_behavior_map_v0.py`;
- implementation author owns only
  `triana-labs/src/triana_labs/behavior_map/__init__.py`;
- orchestrator owns only `internal/SLICE_PACKET.md`,
  `internal/WORKING_MEMORY.md`, `internal/DECISION_LOG.md`,
  `triana-labs/CHARTER.md`, and the gitignored current decision-memory journal;
- no dependency, schema/prompt/citation/redaction/renderer/CLI/UI/backend,
  provider, adapter, source-trace, infrastructure, or unrelated formatting
  change is allowed;
- maximum scope expansion without returning to the orchestrator is one small
  test-local semantic-model fixture inside the existing Behavior Map test file.

Acceptance requires independently authored black-box coverage for two supported
multi-member populations each losing one independently unsupported sampled
episode; surviving parent populations and members; recomputed support,
visibility, identity/lineage, episode assignments, denominators, gaps,
questions, and immutable audit evidence; a population-scoped unsupported audit
that still removes the whole population; the support-three to support-two
visibility boundary; and byte-identical repeated runs. RED command:
`cd triana-labs && uv run pytest -q tests/behavior_map/test_behavior_map_v0.py -k 'audit_scope or episode_audit or population_audit'`.
Final focused gate is the complete Behavior Map test file plus the adjacent
Trace-to-Eval test directory, Ruff format/check, strict mypy, governance, and
diff reconciliation. The repository verifier runs before commit. No worker may
change ownership or broaden scope; ambiguity returns to the orchestrator.

Independent test ownership is frozen at SHA-256
`25c37e8ad28b0f33fd38504170fc8ead008b240eb87c8cce5890e6b1d960f3d1`.
The focused pre-implementation result is two causal failures, two passing
controls, and sixty-three deselected tests: both independently supported parent
populations are deleted, and the support-three parent disappears instead of
becoming `EMERGING`. The population-scoped `UNSUPPORTED` rejection control and
the existing scope control pass. Ruff, formatting, and diff checks pass. The
test-owned path is now immutable; the implementation author may read it but
must not edit it.

Independent final review withheld the preliminary GREEN because recomputed
population IDs inherited `SUPPORTED` while the preserved audit item still
named only the pre-projection ID. Without an explicit edge, the audit evidence
was orphaned from the surviving population. This is falsifying evidence for
the preliminary identity/lineage implementation, not a change to the user's
accepted behavior.

The smallest scope expansion is frozen: a population whose identity changes
after episode detachment must carry optional `audit_subject_id` equal to the
exact pre-projection population ID. That ID must exist in immutable
`semantic_audit.items`; unchanged populations need no redundant edge because
their `population_id` remains the audited subject. The test author may amend
only the existing scoped regression in the already owned test file and must
reproduce RED on the preliminary implementation. The implementation author may
add the optional field to
`triana-labs/src/triana_labs/behavior_map/contracts.py` and populate it only in
the existing owned engine file. No other budget changes. This contract/type
file expansion is necessary to keep the public report type synchronized with
the lineage required by the original request; it permits no schema, provider,
prompt, renderer, or unrelated contract change.

The corrected lineage acceptance bytes are frozen at SHA-256
`230b71e7a5ffe54e557dff1a973a7e5c84074407e6f8bc6497e7bf04458243e1`.
Focused replay is valid RED with two `KeyError: audit_subject_id` failures, two
passing controls, and sixty-three deselected tests; Ruff, formatting, and diff
checks pass. `audit_subject_id` is lineage metadata added after the current
population identity digest and therefore does not participate in that digest.
The existing `population_assigned_episode_count` continues to count every
episode assigned to a retained population row, including an `EMERGING` row;
`EMERGING` means not denominator-worthy as a published population claim, not
unassigned for accounting.

Final exit: the corrected test SHA-256 is
`230b71e7a5ffe54e557dff1a973a7e5c84074407e6f8bc6497e7bf04458243e1`;
engine SHA-256 is
`ef5b6f226c9bd53bf06049b04eb15da4d958dbf49860048243fc774f227c0e81`;
contract SHA-256 is
`3013672a1ab69ab3a45a6a84a7000a136d61c4cf8fe69d5a812fb3958c206f5f`.
Four scoped regressions, 110 Behavior Map/Trace-to-Eval tests, Ruff, strict
mypy, governance, and the complete 749-test/build/install verifier pass;
repository evidence is `/private/tmp/triana-labs-verify.goUqmZ`.

The no-provider Blitz checkpoint projection is report
`sha256:37f4067073c3ccab11269454c46ada85faa16e55ce74bcfedac32f620d0bc418`
under `/private/tmp/triana-blitz-audit-scope.tmfc0b`. Its JSON, Markdown, and
HTML SHA-256 values are respectively
`0c530b6b12e9889303ee5354c72a22426fc4ffea46eda1ece3589a43f7b3d91d`,
`74c9b914b19ca90e70582f66276f7c3ae06351b901e95bc22d0349aa5bcfcf5b`,
and `a191408e3f9685f4b80f5401ea1f3655fcd716042ed50c520997fb1ee4282389`;
two repeated projections are byte-identical. It derives 8/14 assignment from
support 4, 3, and 1, preserves both episode disputes, links both changed
population identities to their exact supported audit subjects, and leaves all
fifty copied checkpoints byte-identical. The model trap would raise on any
provider invocation; none occurred and spend was USD 0.

Independent preliminary review withheld on the orphaned audit-subject edge.
After the separately frozen lineage RED/GREEN correction, independent final
re-review passed with no remaining blocker. Actual diff matches the expanded
budget: one test file, two production contract/engine files, the charter,
slice packet, working memory, decision log, and ignored decision journal. No
dependency, prompt, citation, redaction, renderer, CLI, UI/backend, provider,
adapter, trace, report overwrite, infrastructure, or unrelated cleanup changed.

## BEHAVIOR-MAP-V0-DISPUTED-OCCURRENCE-PROJECTION — 2026-08-08

Status: **COMPLETE — INDEPENDENT FINAL PASS**

Canonical base: `9d8c0d9c9ffd4de72c4afcdea496f5fc2960f1c2` on
`codex/selfserve-v0`. Active authority is `triana-labs/CHARTER.md`. This P0
integrity slice extends the accepted subject-scoped audit rule from user
population membership to agent-behavior pattern support.

Observed failure: the corrected no-provider Blitz projection has two sampled
episodes ruled `UNSUPPORTED`. Two semantic occurrences derived exclusively
from those episodes remain members of the supported “Request an AWB or order
number to identify the referenced delivery” pattern, leaving displayed support
at four. Excluding the disputed episode evidence yields two eligible
occurrences/support units. Population projection is already correct.

Single falsifiable hypothesis: applying episode audit eligibility to every
occurrence before final pattern projection will reduce only the affected
pattern membership/support while preserving occurrence history and separately
supported patterns. It is falsified if a disputed episode still contributes,
an unaffected occurrence/pattern disappears, a below-threshold pattern is
silently published or deleted without its existing typed state, identities or
audit lineage do not match recomputed membership, or replay differs.

Input is the validated in-memory episodes, behavior occurrences, preliminary
patterns, and immutable semantic-audit items. Output is the same report with a
post-audit occurrence/pattern projection. The original occurrence remains the
historical semantic extraction record and retains its original `episode_ids`.
An affected occurrence gains sorted `audit_disputed_episode_ids` and
`audit_state`: `DISPUTED` when every derived episode is rejected, otherwise
`PARTIAL`. These fields make excluded evidence explicit; pattern support uses
only episode IDs outside that disputed set.

For every retained, non-population-disputed pattern, deterministic code removes
fully disputed occurrence IDs, recomputes `occurrence_count`, distinct episode
support, the existing support-based publishability decision, and the existing
`behavior-map-pattern-v0` identity. If identity changes, optional
`audit_subject_id` links the new pattern to its exact pre-projection pattern ID
and immutable audit item; this lineage field is added after and excluded from
the new content digest. A pattern-level non-`SUPPORTED` audit continues to
reject the whole pattern. A pattern below the existing recurrence threshold
uses `BEHAVIOR_PATTERN_SUPPORT_INSUFFICIENT` and the existing emerging/unknown
projection; it cannot remain published or become a pass. Unaffected patterns
retain direct identity and omit redundant lineage.

The episode and both affected occurrences remain visible. No audit, citation,
privacy, minimum-support, provider, or validation rule is weakened. Questions,
gaps, pattern summaries, and report identity are derived only after the final
projection. Semantic extraction output and audit decisions are not rewritten.

Privacy and execution: local deterministic fixtures plus the already sanitized
Blitz V4 checkpoints may be read after GREEN. No provider/model call, network
egress, credential use, source/checkpoint mutation, report overwrite, retry,
fallback, deployment, or infrastructure action is permitted. Any checkpoint
reprojection uses a model trap that raises if called and writes a new private
temporary artifact before the localhost projection is changed.

Change budget:

- test author owns only
  `triana-labs/tests/behavior_map/test_behavior_map_v0.py` and may extend the
  existing configurable audit-scope fixture;
- implementation author owns only
  `triana-labs/src/triana_labs/behavior_map/__init__.py` and
  `triana-labs/src/triana_labs/behavior_map/contracts.py`;
- orchestrator owns only `internal/SLICE_PACKET.md`,
  `internal/WORKING_MEMORY.md`, `internal/DECISION_LOG.md`,
  `triana-labs/CHARTER.md`, and the gitignored decision journal;
- no renderer, prompt, citation, redaction, provider, adapter, CLI, UI/backend,
  dependency, raw trace, infrastructure, or unrelated formatting change;
- maximum scope expansion without returning to the orchestrator is one
  existing renderer assertion only if the canonical HTML already exposes
  affected occurrence audit state without renderer code changes.

Acceptance requires an independently authored fixture where two supported and
two episode-rejected occurrences initially support one independently supported
pattern. Final support and membership must be exactly two; the two rejected
occurrences remain in `behavior_occurrences` with `DISPUTED` state and exact
episode linkage; the retained pattern receives a new deterministic identity
and predecessor audit edge; its immutable pattern-level audit remains
`SUPPORTED`; unrelated supported patterns survive unchanged; a separately
tested post-detachment support-one pattern takes the existing insufficient-
support typed path; a pattern-scoped `UNSUPPORTED` audit still rejects the
whole pattern; assignment/population results remain unchanged; and repeated
checkpoint projection is byte-identical. RED command:
`cd triana-labs && uv run pytest -q tests/behavior_map/test_behavior_map_v0.py -k 'disputed_occurrence or pattern_audit_projection'`.
Final gate is the complete Behavior Map and Trace-to-Eval suites, Ruff, strict
mypy, governance, the repository verifier, a no-provider Blitz replay, exact
artifact audit, and independent final verdict.

Implementation handoff: production changes are limited to the two frozen
engine/contract files. Focused acceptance is 3 passed/67 deselected, the full
Behavior Map suite is 70 passed, and Behavior Map plus Trace-to-Eval is 113
passed. Strict mypy passes 37 source files. On the real sanitized Blitz V4
checkpoints, the AWB/order-number pattern is reprojected from support 4 to 2;
both excluded occurrences remain present with exact `DISPUTED` episode links;
the surviving pattern has a new membership-derived identity and an
`audit_subject_id` edge to the preserved supported predecessor audit. The two
unaffected patterns remain support 5 and 4 and population assignment remains
8/14. A second model-trapped projection produces byte-identical JSON,
Markdown, HTML, and checkpoint directories. No provider or network call was
made. Repository-wide gates and independent final verdict remain pending.

The first independent final verdict was `WITHHOLD`: the post-audit helper
dropped an unaffected occurrence with empty `episode_ids`, although canonical
pre-audit pattern construction preserves such members and uses their distinct
`conversation_id` values only when the whole eligible episode union is empty.
The independent test author added the exact edge at amended test SHA-256
`9cf23dd278d3d4cd810c9589d82dc213ff2f6c9e4af9e01548673c91aae55545`;
pre-fix result was 1 causal failure, 3 passing controls, and 67 deselected.
The amended engine retains no-episode members unless independently disputed
and reproduces the established conversation fallback. Focused acceptance is
now 4 passed/67 deselected and the full Behavior Map suite is 71 passed.
The amended real Blitz output is byte-identical to the prior corrected
projection, including report identity and all checkpoint bytes. The fresh full
repository gate and final independent re-verdict are recorded below.

Final closeout: the amended repository verifier passes all 753 tests, Ruff,
formatting, strict mypy over 38 source files, governance, sdist/wheel builds,
and clean-environment wheel install. Evidence is
`/private/tmp/triana-labs-verify.umaYXk`. Fresh independent re-review returns
`PASS`: the withheld no-episode edge is closed; real Blitz remains pattern
support 5/4/2 with two disputed occurrence rows and 8/14 population assignment;
the corrected JSON, Markdown, HTML, and all 50 checkpoints are byte-identical
across replays. Actual diff is exactly the frozen four orchestrator paths, one
test path, and two implementation paths; no dependency, provider, prompt,
renderer, adapter, privacy, infrastructure, or unrelated source changed. No
provider/network call was made and incremental cost is USD 0.

The original independent test ownership was frozen at SHA-256
`38d8fffd404f8e5df846d888cae0d9c8e5dabd182867c4549a621441425ad82c`;
the final-review edge regression supersedes it with amended frozen SHA-256
`9cf23dd278d3d4cd810c9589d82dc213ff2f6c9e4af9e01548673c91aae55545`.
The focused pre-implementation result is two causal failures, one passing
whole-pattern audit control, and sixty-seven deselected tests. The target
fixture proves four original occurrences/four distinct episode support, two
occurrences derived exclusively from the two rejected sampled episodes, and
two eligible occurrences. Current production incorrectly retains all four and
publishes the support-three-to-one boundary instead of the existing typed
insufficient-support path. Ruff, formatting, and diff checks pass. The
test-owned file is now immutable; implementation may read but not edit it.
