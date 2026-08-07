# Behavior Map V0 vertical slice

Date frozen: 2026-08-07

Status: **LOCAL IMPLEMENTATION GREEN — LIVE TAU PROOF PENDING**

Slice ID: `BEHAVIOR-MAP-V0`

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
`2e4167dbd84fe32a18bcb7fed2ed5bdc9a9bf10e062bf6f6b1058f8521a58af4`.
It freezes all forty-two acceptance behaviors listed above across thirty-eight
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

Valid RED command:

```text
cd triana-labs
UV_CACHE_DIR=/private/tmp/triana-uv-cache uv run --locked pytest -q tests/behavior_map
```

Observed result: collection stops only at
`ModuleNotFoundError: No module named 'triana_labs.behavior_map'`; one error in
3.39 seconds against an isolated export of pre-implementation commit `d35dac1`.
Ruff check, Ruff format check, Python compilation, file hash, and diff check are
GREEN. Against the 81-test-green implementation handoff, the final amendment
produces one aggregated intended failure and thirty-seven passing controls in
4.00 seconds. The test-owned path is frozen. The implementation author may read
it but must not edit it.
