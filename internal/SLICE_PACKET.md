# Active implementation slice

## Triana Preview local distribution entry gate — 2026-08-10

Status: **INDEPENDENTLY VERIFIED; COMMIT PENDING**

Slice ID: `TRIANA-PREVIEW-LOCAL-ALPHA-1`

Canonical base: `92609bb0db4f747501e36cf03f397cc8072e699f`

Active authority: `triana-labs/CHARTER.md`, specifically the accepted local-
first Phase 1 Behavior Map value claim. This slice packages that already
implemented engine for an invite-only on-device preview; it does not create a
second analysis implementation or broaden the semantic claim.

### Product outcome and public behavior

One private local command accepts a prescribed PreviewTrace JSONL path, a
short agent description, an empty destination, and an explicit
customer authorization acknowledgement. It deterministically redacts the
source into private run custody, constructs the existing evidence-manifest
boundary, invokes the installed `triana-labs` Behavior Map command unchanged,
and leaves the canonical JSON, Markdown, HTML, checkpoints, redaction audit,
and run manifest on the customer's device. Provider configuration remains the
existing explicit environment contract. With no provider configured, the
existing engine emits deterministic accounting and typed semantic gaps.

The package and container are named **Triana Preview**. `triana-preview/` is a
distribution facade that depends on `triana-labs`; it MUST NOT contain copied
episode extraction, taxonomy, grouping, audit, support, identity, or rendering
logic. Future engine changes flow into the Preview only by updating the single
`triana-labs` dependency at the same repository commit and passing the Preview
smoke gate.

Input contract:

- one regular, non-symlink PreviewTrace JSONL file under the existing parser
  and resource limits;
- one non-empty agent description of at most 2,000 UTF-8 bytes;
- one new or empty local-private output directory;
- explicit `--confirm-authorized-traces` acknowledgement;
- optional existing `TRIANA_BEHAVIOR_MAP_*` provider environment. A partially
  configured provider is an integrity refusal before model construction.

Output contract:

- private `0700` output custody and `0600` intermediate artifacts;
- `input.redacted.jsonl`, `redaction-audit.json`, and `manifest.json`;
- unchanged Behavior Map `behavior-map.json`, `behavior-map.md`,
  `behavior-map.html`, and checkpoints;
- the underlying Behavior Map exit semantics, including exit `10` for a
  truthful completed-with-gaps report;
- no raw source copy, credential value, provider response, network telemetry,
  or Triana-hosted upload.

### Authority, privacy, gaps, and refusal

- Deterministic `triana-labs` code owns validation, redaction, manifest facts,
  evidence identity, support, accounting, report identity, and typed gaps.
- The existing primary and audit models may propose semantic meaning only when
  the operator separately configures and authorizes their exact provider
  boundary. Verification uses no models and traps provider execution.
- A human owns trace authorization and all semantic acceptance. The package
  creates no accepted taxonomy or ruling.
- Raw traces remain on the customer's device. The container receives the
  trace mount read-only and writes only to the declared output mount. Redacted
  semantic evidence may leave the device only to the exact configured model
  endpoints.
- Invalid JSONL, missing authorization, unsafe path/symlink, non-empty output,
  incomplete provider configuration, redaction refusal, or engine integrity
  failure aborts visibly. Provider absence is not an abort; it remains the
  existing typed semantic gap.

### Provenance and dependencies

No external source code or prose is reused. No Agentagon, Kairos-AI, HRAI, or
private Blitz artifact enters the package. The facade imports only current
repository-owned `triana-labs` public seams. No new runtime dependency is
allowed. Python, `uv`, and the container base follow already pinned repository
versions.

### Frozen change budget and role ownership

Independent test author only:

- `triana-preview/tests/**`;
- `triana-preview/tests/fixtures/**`.

Independent implementation author only:

- `triana-preview/src/**`;
- `triana-preview/pyproject.toml`;
- `triana-preview/uv.lock`;
- `triana-preview/Dockerfile`;
- `triana-preview/.dockerignore`;
- `triana-preview/.env.example`;
- `triana-preview/README.md`;
- `triana-preview/scripts/**`.

Orchestrator only:

- this packet;
- the smallest architecture/charter update;
- append-only `internal/DECISION_LOG.md` entry;
- ignored local decision memory;
- optional content-free verification output under `/private/tmp`.

Explicitly untouched:

- all `triana-labs/src/**` production behavior and prompts;
- all existing tests and fixtures outside `triana-preview/`;
- `triana-core/`, `triana-backend/`, `triana-app/`, deployment and cloud
  configuration;
- accepted Blitz reports, projections, tags, raw traces, and private evidence;
- provider retry/fallback, budgets, grouping thresholds, audit authority, and
  semantic schemas;
- the pre-existing user modification to `internal/WORKING_MEMORY.md`.

No dependency is added. Maximum scope expansion is one root-level
`.dockerignore` only if the test author proves the repository build context can
include a secret or local artifact despite explicit Docker `COPY` boundaries;
otherwise workers stop before editing outside the budget.

### Independent acceptance contract

The independent test author freezes black-box RED proving:

1. missing trace authorization refuses before redaction or engine execution;
2. a valid prescribed PreviewTrace file plus agent description reaches the
   real installed Labs engine and produces JSON/Markdown/HTML locally;
3. invalid, symlinked, or mutated input refuses without becoming an empty
   successful report;
4. the source file is byte-unchanged and never copied into the image/output;
5. redacted source, audit, and manifest are private and credential-free;
6. no-provider execution remains a completed-with-typed-gaps report and makes
   zero provider calls;
7. partial provider configuration refuses before child engine execution;
8. non-empty output refuses rather than overwriting prior evidence;
9. report and manifest facts bind the exact redacted source hash/counts and
   one unique grouping disposition per trace;
10. the Preview package imports the one Labs engine and contains no copied
    Behavior Map implementation;
11. source and clean-installed command behavior match;
12. the local container build has a non-root runtime, no embedded credential,
    no customer data, and a read-only documented input mount.

Required RED:

```text
cd triana-preview
uv run --locked pytest -q
```

Independent test freeze (2026-08-10):

- `tests/conftest.py` —
  `74dec24111cef6d34f260ff29284f4d67030d7b7d1ddc6e38fe5fb7d62ffe451`;
- `tests/test_preview_cli.py` —
  `7a58219238c40db9bc9a3730fe05dfbfd0347bdba7c3e3917c931e2a623fdfef`;
- `tests/fixtures/synthetic_preview_trace.jsonl` —
  `5fbae0884520cfc21b8115a045863fb64d9c71ac54ade6abeb971c51d7e85b73`.

The frozen command collected thirteen tests and all thirteen failed because
the Preview module, installed command, source facade, and Docker surface did
not yet exist. The failures were missing product behavior rather than test
collection or fixture errors. The sandbox required an explicit private uv
cache; that environment-only substitution does not change the command's
product contract.

Debugging iteration 1 (2026-08-10):

- Observed failure: after the initial thirteen tests turned GREEN, independent
  verification changed a regular source in place, restored its original bytes
  during the custody interval, and `_source_unchanged` accepted it even though
  the file `mtime_ns` and `ctime_ns` changed.
- Smallest reproduction: hold the initial descriptor/hash, write same-length
  alternate bytes, restore the original bytes, then run the post-redaction
  custody check; it returned true.
- Falsifiable hypothesis: the post-check binds only inode, final digest, and
  size, so a transient mutation can influence the separately reopened redaction
  input and disappear before validation.
- Falsifier: a frozen black-box test must show any transient in-place mutation
  receives `INPUT_CHANGED_DURING_RUN` and publishes no report while unchanged
  inputs still pass.
- Scope: independent test author may add only the adversarial case under the
  existing test budget; implementation author may change only the Preview
  custody facade after RED is frozen.

Debugging iteration 2 (2026-08-10):

- Observed failure: Preview's documented Docker command uses the repository
  root as build context, but only `triana-preview/.dockerignore` existed; Docker
  therefore does not consult it and may send unrelated repository files or
  local trace data into BuildKit custody even though explicit `COPY` commands
  keep those files out of the final image.
- Smallest reproduction: resolve the documented context and show that the root
  has no `.dockerignore`, while the nested ignore file cannot govern it.
- Falsifiable hypothesis: a root-context allowlist containing only the exact
  Labs/Preview packaging and source inputs required by the Dockerfile prevents
  unrelated code, `.git`, environment files, tests, documents, and JSONL trace
  data from entering the build context.
- Falsifier: a frozen static black-box test must reject any root ignore policy
  that is absent, denylist-only, or admits unrelated/customer-shaped files.
- Scope expansion: activate the already budgeted single root `.dockerignore`;
  no Dockerfile, image behavior, product code, or cloud action changes.

Adversarial freeze transitions (append-only):

- Custody-mutation test freeze changed
  `tests/test_preview_cli.py` from
  `7a58219238c40db9bc9a3730fe05dfbfd0347bdba7c3e3917c931e2a623fdfef`
  to
  `d84031d008bb0bdcab320abcd39f685c3e3d2de288f0c57bd9cb53497cafbbfb`;
  the suite contained fourteen tests and the new case was valid RED at exit 10
  instead of the required integrity refusal.
- Root-context allowlist test freeze changed that file from
  `d84031d008bb0bdcab320abcd39f685c3e3d2de288f0c57bd9cb53497cafbbfb`
  to
  `af87aa3191425b07b1b2a3069f7c8887fe641b74b498d6760ad5afde6f25cafd`;
  the suite contained fifteen tests and the new case was valid RED because the
  repository-root `.dockerignore` was absent.

Final independent result (2026-08-10):

- all fifteen Preview black-box tests pass;
- Ruff format/check and strict mypy pass for Preview;
- the Preview lock checks offline and wheel/sdist build succeeds;
- source and installed commands have matching refusal behavior, while two real
  provider-disabled runs emit the same report identity and byte-identical
  artifacts with `provider_calls=0`;
- private output modes are `0700`/`0600` and the accepted source is unchanged;
- the custody adversary now refuses transient mutate-and-restore writes;
- the root Docker build context is default-deny and admits only exact
  Labs/Preview package metadata, locks, and source required by the Dockerfile;
- governance and diff checks pass; the complete Labs suite passes 891 tests and
  builds both distributions. Its final clean-venv dependency installation was
  not credited as passing because the local uv cache contained a missing
  `pydantic-core` RECORD; no product test or build failed.
- a local Docker build was attempted twice but the installed Docker daemon did
  not answer its socket ping; the image/runtime smoke remains explicitly
  unverified, and no registry login, image push, provider call, or deployment
  occurred.

Debugging iteration 3 (post-commit CI, 2026-08-10):

- Observed failure: GitHub `arm64-images` could load the new root
  `.dockerignore` but the existing backend Dockerfile then failed because
  `triana-backend/pyproject.toml`, `uv.lock`, `src`, `alembic.ini`, and
  `migrations` were absent from its build context.
- Smallest reproduction: run the existing root-context backend build under the
  Preview root allowlist; its required inputs are intentionally excluded.
- Falsifiable hypothesis: Docker's file-specific
  `triana-preview/Dockerfile.dockerignore` can own the exact Preview allowlist
  when `-f triana-preview/Dockerfile` is used, while removing the restrictive
  root policy restores all pre-existing image contexts.
- Falsifier: independent tests must prove the file-specific policy is
  default-deny and exact, the root restrictive policy is absent, and existing
  root-context Docker input paths remain eligible.
- Scope: replace the one root ignore file with one Preview Dockerfile-specific
  ignore file; no application, Dockerfile, semantic, provider, or deployment
  behavior changes.

CI-regression freeze transition and result:

- `tests/test_preview_cli.py` changed from
  `af87aa3191425b07b1b2a3069f7c8887fe641b74b498d6760ad5afde6f25cafd`
  to
  `9030479d190bd9502ac5b0e3dd1d0d5ad7c3eac6c4d4026c4b866aaade14f357`;
  the corrected test was valid RED because the Dockerfile-specific ignore was
  absent and the restrictive root policy remained.
- The exact default-deny allowlist now lives at
  `triana-preview/Dockerfile.dockerignore`, which Docker applies only to the
  Preview Dockerfile. The root policy was removed, all fifteen Preview tests
  pass, and existing backend Docker inputs are again eligible for their sibling
  root-context build.
- This supersedes only the earlier root-location choice; the accepted privacy
  requirement and exact allowlist are unchanged.

Final verification:

```text
cd triana-preview
uv lock --check
uv run --locked ruff format --check src tests
uv run --locked ruff check src tests
uv run --locked mypy src
uv run --locked pytest -q
uv build
./scripts/verify.sh

cd ../triana-labs
UV_OFFLINE=1 PIP_NO_INDEX=1 ./scripts/verify.sh

cd ..
./scripts/verify-governance.sh --working-tree
git diff --check
```

When Docker is locally available, the orchestrator also builds
`triana-preview:0.1.0-alpha.1`, runs the packaged no-provider smoke twice on a
synthetic fixture, and compares the report artifacts. No registry login, image
push, Docker Cloud configuration, provider call, or external deployment is
authorized.

Acceptance is a locally installable and locally container-buildable private
Preview whose command genuinely reaches the one current Labs Behavior Map
engine. It is not an SDK stability promise, public/open-source release,
arbitrary trace-format adapter, semantic taxonomy-quality passage, cloud
service, or Docker registry publication.

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

## BEHAVIOR-MAP-V0-EXTRACTION-OUTPUT-CEILING — 2026-08-08

Status: **COMPLETE — INDEPENDENT FINAL VERDICT PASS**

Canonical base: `d8eef7d` on `codex/selfserve-v0`. Outcome: eliminate the
observed systematic Luna extraction truncation before continuing the authorized
374-conversation Blitz DEVELOPMENT run. Calibration and holdout remain sealed.

Observed failure: with the general 2,000-token output ceiling, 29 of the first
123 completed extraction attempts became content-free failed tombstones. Two
bounded diagnostics reproduced `LengthFinishReasonError`. Raising the same
conversation to 4,000 produced valid strict output at 2,517 tokens; a distinct
conversation still truncated at 4,000 and produced valid strict output at
8,000 with 7 episodes, 12 behaviors, and 4,112 output tokens. The maximum full
extraction request in the sanitized DEVELOPMENT scope is 27,607 bytes. Under
the frozen Luna ceilings of USD 1/M input and USD 6/M output, pessimistically
treating every byte as a token plus 8,000 output tokens remains below USD 0.076
per extraction call.

Single hypothesis: applying a general 2,000-token ceiling caused the dominant
full-corpus failures, and an extraction-specific 8,000-token ceiling eliminates
those truncations without weakening output, schema, citation, privacy, or
budget validation. Falsifiers: the exact extraction wire does not send 8,000;
non-extraction stages stop using their configured ceiling; invalid JSON/schema
becomes accepted; provider retry/fallback appears; or corrected live extraction
still truncates at 8,000.

Contract: `FoundryStructuredSemanticModel` owns a visible
`extraction_max_output_tokens_per_call` defaulting to 8,000. Only stages with
prefix `demand-episodes-and-agent-behaviors-` use it; every other stage uses
existing `max_output_tokens_per_call`. Lineage exposes both ceilings. Callers
remain responsible for a conservative reservation covering their input/output
ceilings. The client retains `max_retries=0`, no temperature, JSON-object mode,
strict local schema validation, and content-free provider failures.

Privacy/execution: fixtures are local and make no provider call. Later live
recovery may reuse only exact successful checkpoints in a new private
directory, preserving all failed/interrupted history in the old directory.
Owner-authorized diagnostics and prior attempts count toward the same USD 50
independent ceiling. No sealed trace, retry loop, fallback, raw provider
response persistence, deployment, or infrastructure change.

Change budget: independent test author owns only
`triana-labs/tests/trace_to_eval/test_foundry_json_object_compatibility.py`;
implementation author owns only
`triana-labs/src/triana_labs/trace_to_eval/semantic.py`; orchestrator owns this
packet, `internal/DECISION_LOG.md`, `internal/WORKING_MEMORY.md`,
`triana-labs/CHARTER.md`, and ignored decision memory. No dependency, prompt,
schema, behavior-map projection, renderer, adapter, redaction, or unrelated
change. Acceptance: independent wire regression for exact extraction and
non-extraction ceilings, all existing invalid-output/no-temperature controls,
focused suite, full verifier, bounded live canary, and independent verdict.

Live evidence update: the stage-scoped extraction fix completed all 374
DEVELOPMENT-visible conversations without an extraction failure. The same run
then completed `user-populations-0000` through `user-populations-0004` and
failed content-free at `user-populations-0005` under the general 4,000-token
ceiling. Deterministic refusal correctly emitted no partial population map and
made no Terra audit call. The slice therefore widens, without adding files, to
an explicit `consolidation_max_output_tokens_per_call` ceiling of 8,000 for
checkpoint-qualified `user-populations-*` and `agent-behavior-patterns-*`
stages. Extraction remains 8,000; unrelated stages retain the configured
general ceiling. The added falsifiers are incorrect stage routing, hidden
retry/fallback, weakened validation, or a repeated content-length failure at
8,000. Recovery must copy only the 379 validated checkpoints into a new
private attempt root, exclude the failed consolidation tombstone, reserve all
new primary and Terra calls under the same cumulative USD 50 cap, and stop on
any new content-length failure. Test ownership returns to the independent test
author before implementation changes.

Second live evidence update: after cooldown, the exact previously failed
`user-populations-0011` request succeeded at 8,000, then failure moved to
`user-populations-0016` after five rapid successful consolidation calls. The
successful calls used only 4,009 output tokens in aggregate. This falsifies a
bad-payload or remaining output-ceiling hypothesis and is consistent with the
capacity-10 Luna deployment throttling short calls that no longer have
extraction latency as natural pacing. The slice therefore adds a configurable,
deterministic `min_call_interval_seconds` (default zero) to the same model
adapter and lineage. It may delay a new provider attempt until the configured
interval since the prior attempt start has elapsed; it may not retry a failed
call, change call/budget accounting, hide a failure, or select a fallback.
Independent fixtures own the clock/sleeper contract before implementation.
The live recovery will use explicit pacing and copy only the 390 successful
checkpoints into a new attempt root; the new `0016` failure remains immutable
in its source root.

Third deterministic closeout update: the final provider run completed 462 Luna
author checkpoints and 150 Terra audit checkpoints under manifest cap USD
69.868, producing 80 retained populations, 61 retained patterns, and 47 typed
missing pattern audits. Independent final review withheld publication because
the rendered report double-counts copied checkpoint history in
`budget.total_reserved_usd` (USD 130.82) and `_safe_lineage` strips the new
extraction/consolidation ceilings and pacing scalar. No provider evidence is
invalid and no provider rerun is authorized or needed. The slice widens to a
deterministic artifact-only correction: report budget must use the manifest's
explicit cumulative prior/run/post reservation fields when present, must not
add checkpoint-derived provider reservations again, and must visibly preserve
all three output ceilings plus pacing in safe provider lineage. Legacy
manifests without the explicit cumulative fields retain the existing derived
behavior. Independent test author may additionally own
`triana-labs/tests/behavior_map/test_behavior_map_v0.py`; implementation author
may additionally own `triana-labs/src/triana_labs/behavior_map/__init__.py`.
No semantic prompt, decision, membership, support, audit, checkpoint, provider,
redaction, renderer layout, or dependency change is allowed. Acceptance is a
frozen RED, artifact-only replay with provider traps, exact analysis content,
correct USD 69.868 cap, visible 8k/8k/4k ceilings and 20-second pacing, full
gate, and independent re-verdict.

Final closeout: corrected artifact
`/private/tmp/triana-blitz-full-development-corrected-final-20260808/report`
passes independent re-verdict. All 374 DEVELOPMENT-visible conversations were
analyzed while 125 calibration and 125 holdout conversations remained sealed.
The report retains 378 grounded episodes across 230 conversations, 80 supported
user populations, 61 supported agent-behavior patterns, and 212 uniquely
population-assigned episodes; 47 unaudited pattern subjects remain typed
missing and unpublished. A provider-disabled replay reproduces all 613
checkpoint artifacts and byte-identical JSON, Markdown, and HTML. The report
records USD 53.74 prior reservation, USD 16.128 current-run maximum, and USD
69.868 total under the approved USD 70 cap, plus Luna pacing 20 seconds and
general/extraction/consolidation ceilings 4,000/8,000/8,000. The full gate
passes 757 tests plus formatting, Ruff, strict mypy, governance, build, and
clean-wheel installation at `/private/tmp/triana-labs-verify.sQKjH2`. Actual
provider billing remains unknown; reservation is not actual cost.

## BEHAVIOR-MAP-V0-COVERAGE-CONSERVATION-REPAIR — 2026-08-08

Status: **ACTIVE — ENTRY GATE FROZEN; TEST AUTHOR AUTHORIZED**

Canonical base: commit `68741dab5824709932335d23405b95d754107fce`,
annotated locally as `best-version-yet-blitz-20260808`. Active authority is
the Phase 1 Behavior Map boundary in `triana-labs/CHARTER.md`. The outcome is
to repair two independently reproduced, corpus-independent coverage defects
without weakening exact evidence, privacy, audit authority, or explicit
unknown states: mixed-validity demand citations currently reject a complete
episode, and first-level population batches currently omit episodes before
global consolidation can compare them.

The immutable successful predecessor is private report
`sha256:9c98854dba09a188600b5de7a6f20e71a86ea01791d61556e31f40f16fd1f021`
under
`/private/tmp/triana-blitz-full-development-corrected-final-20260808/report`.
Its JSON, Markdown, and HTML hashes are respectively
`9821a041d391843bae8885010c6180a58a38646f3bd33d56382e5f18a3a8f0f1`,
`7733ccfb3ea73f20043b00464f2dbc8a8c5df92f91a2d509d058e233b40d72b6`,
and `5e83984622aae54c49c53b6355b3865816f4fac021ccf8a7ff2b694897a26377`.
The aggregate relative-path checkpoint-tree hash is
`fd5668300d3cdf55c0011a56bb34a60c3b075ad899b79250b8c629859323ae7c`.
No worker may write under that root. A content-free repository manifest will
record the predecessor boundary; it will contain no Blitz IDs, quotes, raw
traces, checkpoint content, or customer identifiers.

### Contracts and authority

Input is one authorized `PreviewTrace` corpus plus the existing provider and
budget manifest. Output is a versioned proposed Behavior Map with individually
validated demand citations, field-scoped grounding declarations, inspectable
excluded citation history, exhaustive population-stage dispositions, bounded
leftover matching/regrouping, and deterministic support/identity/lineage/audit
projection. A separate deterministic comparison consumes the predecessor and
repaired reports and emits private Markdown and HTML; it labels mechanical
movement separately from human-validated semantic improvement.

The semantic author may propose demand fields, field-to-citation bindings,
population membership, one existing-population match, no match, ambiguity,
and new leftover groups. Deterministic code owns source-conversation binding,
event role/sequence/exact-quote validation, excluded-citation reasons,
field-binding completeness, every episode disposition, supplied-ID checks,
unique membership, support, denominators, identity, predecessor lineage,
batch/hierarchy conservation, audit projection, artifact identity, and
comparison arithmetic. Exact citation existence is not semantic entailment.
All recovered meaning remains `PROPOSED`; human labels and rulings alone can
establish semantic benchmark truth or accepted taxonomy.

Demand support may cite only `USER_MESSAGE`. Assistant and tool evidence stays
in agent behavior or typed excluded/context evidence. Mandatory goal,
requested action, and subject must each declare at least one surviving exact
customer citation. Every retained constraint and fallback must do the same;
an unsupported optional item is removed with visible typed uncertainty. No
valid customer citation or unsupported mandatory grounding rejects the
episode precisely. An invalid extra citation never supports an episode and
does not by itself reject independently grounded fields.

Every population-stage input receives exactly one deterministic disposition:
assigned, intentionally unassigned, ambiguous, audit-disputed, or a typed
model-omission state carried into the next bounded stage. An unsupplied ID is
never membership and creates an exact gap. Duplicate or conflicting membership
is refused. Leftovers first receive one bounded match/no-match opportunity
against existing candidate definitions and representative evidence, then a
stable cross-origin rebatch gives remaining leftovers an opportunity to form
new candidates. No assignment is forced and exhaustive quadratic comparison
is not claimed. Any membership change creates a new identity and explicit
predecessor lineage; no old audit silently governs new membership.

### Separate falsifiable hypotheses

Defect A observed failure: 71 Blitz DEVELOPMENT conversations contain 97 raw
episode proposals but no surviving episode. Hypothesis A: proposal-wide
boolean citation validation causes structurally valid customer grounding to
be discarded when any extra citation is invalid. Falsifiers: individual
validation cannot reproduce the rejection; retained mandatory or optional
fields lack permitted bindings; assistant-derived facts survive; or negative
fixtures become demands. One implementation intervention is allowed before
focused GREEN: versioned field-scoped episode grounding plus typed citation
projection. No population implementation begins until A is independently
GREEN.

Defect B observed failure: 348 eligible episodes enter 29 first-level batches;
28 batches omit at least one input, 114 valid IDs reach no first-level output
or hierarchy, and three unsupplied IDs are returned. Hypothesis B: conservation
starts only after candidate creation, so first-level omission permanently
removes comparison opportunity. Falsifiers: any omitted ID already reaches a
later comparison, exhaustive dispositions do not close the loss, or the
repair requires forced membership. One implementation intervention is allowed
after A: versioned dispositions plus deterministic carry-forward, bounded
existing-candidate matching, and cross-origin leftover rebatching.

### Privacy, execution, and live authorization

Automated tests use synthetic fixtures and fake semantic models only. Raw
Blitz evidence, private checkpoints, review labels, and generated reports stay
under private temporary custody. The 144-conversation and 114-episode frontier
may produce only a private hash-addressed review queue with empty human labels;
no semantic benchmark passage is claimed until a human supplies them.

After offline GREEN and predecessor verification, Akarsh authorizes exactly
one new private Blitz DEVELOPMENT campaign over the same 374 visible
conversations, with the same 125 calibration and 125 holdout conversations
sealed. Luna is primary author and Terra is independent judge. The new
campaign has a conservative reservation ceiling of USD 70, no retry, no
fallback, no locked-holdout access, no benchmark download, no deployment, and
no publication. Any additional live attempt or spend requires new owner
authorization. Reservation is reported separately from actual provider
billing. The repaired artifact must use a new root, identity, and explicit
predecessor lineage.

### Frozen change budget

Independent test-author ownership:

- `triana-labs/tests/behavior_map/test_behavior_map_coverage_repair.py`;
- `triana-labs/tests/behavior_map/test_behavior_map_comparison.py`;
- synthetic fixtures only under
  `triana-labs/tests/behavior_map/fixtures/coverage_repair/` if necessary.

Implementation-author ownership after RED freeze:

- `triana-labs/src/triana_labs/behavior_map/contracts.py`;
- `triana-labs/src/triana_labs/behavior_map/__init__.py`;
- `triana-labs/src/triana_labs/behavior_map/render.py` only if required to
  expose excluded evidence/dispositions;
- new bounded modules
  `triana-labs/src/triana_labs/behavior_map/comparison.py` and
  `triana-labs/src/triana_labs/behavior_map/benchmark.py` only if the frozen
  black-box contract requires them.

Orchestrator ownership:

- this packet;
- `triana-labs/CHARTER.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACTS.md`,
  `internal/DECISION_LOG.md`, and a new content-free baseline manifest;
- ignored local decision memory and private `/private/tmp` run/comparison/
  review artifacts.

Explicitly untouched: the predecessor report/checkpoints; existing adapters,
redaction/privacy logic, provider transport, pricing, retry/fallback policy,
locked splits, auth/UI/backend/deployment/infrastructure, Agentagon/Kairos/HRAI
sources, raw corpora, and the pre-existing unrelated
`internal/WORKING_MEMORY.md` modification. No dependency is allowed. Maximum
scope expansion is one additional existing Behavior Map test file or one
renderer field needed by the frozen contract; any other expansion stops for
orchestrator review.

### Acceptance and execution order

The independent test author freezes black-box RED for all user-specified
positive/negative citation and cross-batch cases, unsupplied IDs, duplicate
membership, support equality, scoped audit rejection, disputed-support
exclusion, repeated byte identity, batch-boundary permutations, comparison
arithmetic, and provider traps. The orchestrator records exact test hashes and
RED commands. Defect A production then runs focused and adjacent GREEN before
Defect B production begins. The implementation author may not edit frozen
tests.

Final local gates are the complete Behavior Map and Trace-to-Eval suites,
format, Ruff, strict mypy, governance, build/install, repeated deterministic
projection, provider-disabled predecessor verification, and change-budget
reconciliation. The live run begins only afterward. The separate before/after
report must compare exact corpus/split identities, report recovered/rejected/
uncertain/still-unassigned counts, identity and lineage movement, gaps, audits,
cost, and all requested semantic benchmark metrics as `HUMAN_LABELS_MISSING`
where labels do not exist. Higher coverage alone is never a pass.

Independent RED freeze: the test-author-owned files are frozen at SHA-256
`00fa8de6fe1c2d74bd2645c693b9c32d0f0ab4a3c578f76ac354091abc8234dc`
for `test_behavior_map_coverage_repair.py` and
`d46a338fac824a3888f716bb6a4df176868436c36c5e7c2653cc691db06241e9`
for `test_behavior_map_comparison.py`. The orchestrator reproduced 20 cases:
18 intended behavioral RED failures and two controls passing. The RED failures
cover missing field-scoped citation salvage/refusal, actual tool-result role
rejection, excluded history, optional-field uncertainty, exhaustive population
dispositions, batch omission carry-forward, unsupplied IDs, duplicate/unique/
ambiguous behavior, audit-scoped support, the private unlabeled benchmark, and
the same-selection predecessor comparison. Ruff format/check and five adjacent
legacy citation/audit controls pass. These two files are immutable for the
implementation author.

### Bounded test-budget expansion — 2026-08-08

The orchestrator exercised the frozen allowance for one additional existing
Behavior Map test file. The independent test author may edit only
`triana-labs/tests/behavior_map/test_behavior_map_v0.py` so the existing
checkpoint-tamper test selects a successful checkpoint without assuming typed
FAILED attempt artifacts contain a `result` member. Production must continue
to preserve FAILED attempts; deleting, suppressing, or accepting their invalid
semantic output is forbidden. No other test behavior or file budget changed.

### Superseding final repair test freeze — 2026-08-08

The final independent test-author bytes supersede only the earlier hashes in
this slice:

- coverage/benchmark SHA-256
  `e82fb706544b4d9da9e0cffe4bf29c1b5a5508786819219260897af886c6bfe8`;
- comparison SHA-256
  `4622e81f6d9f60f570f14ff6738e9c85efffa4d920877e20cff14ecb491dc24a`;
- legacy Behavior Map V0 SHA-256
  `be35bfb66d61d0431b9a670d88d7fcd6d57c6f45c958806c6aad8c743846b64f`.

The orchestrator reproduced 114/114 Behavior Map tests, Ruff, and strict mypy.
A provider-disabled predecessor replay emitted exact predecessor and 374-item
selection lineage with zero attempted provider calls. The private unlabeled
benchmark replay produced exactly 144 no-surviving conversations and 114
explicit `UNASSIGNED_DEMAND` episodes; all semantic metrics remain
`HUMAN_LABELS_MISSING`.

### Coverage-repair execution and acceptance — 2026-08-08

Independent RED/GREEN iterations were kept falsifiable and provider-free except
for the single owner-authorized private campaign. Frozen regression hashes were:

- population-batch failure isolation:
  `8bc8e91093404c06084ec9cb780a75003da39f15e7f1c31df0f872a0883a0cd7`;
- pattern-batch failure isolation:
  `28b62ac70a3bdf703e13033c4ff71d890b7edc1a4e557ac388d3c83abd2b8a0d`;
- audit subject-class continuation:
  `7c07037263bc021519db27d7e7ac7b239e032d2eca3f0df720782a827195b9f0`;
- legacy comparison selection:
  `ac22b379547bd5fbd032d71bfadf2c70534a19a6c244a5fcdd8b463aa59bc499`;
- strict audit-scope projection:
  `ac18ccae61ec42e7150bf421213bf793f6a60cd7b3720ba39367598d6ae15c0e`;
- post-relevance field-grounding projection:
  `413cfe308fbd699b273a4ad697e73b02461ad43b070f43cb1857357506a62970`;
- observed lane-budget truth:
  `8ddddf9317e858f1491872674b9a402134a3e7973c4ecac556a96e72df5ba21f`;
- comparison membership-edge conservation:
  `1d13683ccec88e9fe4dd273917bfc1fe3d3bed470ab87e515ab259591d9cbf67`;
- final historical-projection authority, replacement-edge, candidate-audit,
  dual-lineage, and exact legacy-budget contract:
  `627d7eed43032f5bfb3e9c16d6de03ef2af0837f223253939159171b4c5fe1b9`.

The first live continuation path was incorrectly reused after being declared
immutable. Its original failed report remains hash-preserved in
`/private/tmp/triana-blitz-coverage-repair-failed-snapshot-20260808`; the reused
root and every subsequent rejected v2-v4 projection remain typed historical
failed evidence and are not acceptance artifacts. No accepted baseline bytes
changed.

The final independently accepted bounded artifact is
`/private/tmp/triana-blitz-coverage-repair-historical-projection-final-v5-20260808/behavior_map_historical_projection.json`,
projection ID
`sha256:4a31e882651e533254a71fb43bf2aafe87b026297dea056c0c377aa4c1729f6e`,
file SHA-256
`e4e3af9eb8d24f12e7932a9c020a9469b4ab317449cd606fc194cd3f705e3934`.
The repeated v5 projection is byte-identical and used zero providers. It
contains 405 grounded episodes, 74 supported populations/210 active
assignments, three unpublished candidates/eight re-audit-required memberships,
24 supported patterns, 765 active occurrences, and five excluded occurrences.
The accepted full Blitz baseline remains unchanged and best accepted.

Historical campaign accounting is explicit: 455 Luna attempts; 115 Terra
attempts against an 89-call Terra cap; USD 20.70 observed audit reservation
against USD 16.02 declared; USD 69.912 total reservation within USD 70; actual
cost unknown. The Terra lane is typed
`SEMANTIC_LANE_BUDGET_CONTRACT_EXCEEDED`; overall-ceiling compliance does not
erase that violation. Human semantic benchmark metrics remain blocked on the
private label panel, and a separately authorized fresh run is required before
claiming global reconsolidation or Defect-B semantic benchmark passage.

### Final-review superseding RED freeze — 2026-08-08

Independent final review invalidated the immediately preceding GREEN claim by
reproducing release-blocking contract holes before the first live campaign
could complete. That campaign was stopped after 97 Luna attempts; its partial
private checkpoints are evidence only and are not a repaired report. The test
freeze now supersedes the earlier hashes and status:

- coverage/benchmark SHA-256
  `a9e1b42df8a94a501f2f4dc386863b8867219a81b0b1284c8f77ea5b898f552e`;
- comparison SHA-256
  `9d7081cfee0a8c492bfa9b55539ff3140c8d2b098dfd9a2a196d92d86247de56`;
- legacy Behavior Map V0 SHA-256 remains
  `be35bfb66d61d0431b9a670d88d7fcd6d57c6f45c958806c6aad8c743846b64f`.

The orchestrator accepts RED as five focused coverage failures plus three
focused comparison failures. They cover mandatory versioned field grounding
and visible proposal authority, contradictory population dispositions,
representative match evidence, unlabeled benchmark-control semantics, private
runtime predecessor validation and exact lineage, ID-level predecessor claim
conservation, and `NO_CHANGE` classification. The true cross-batch permutation
fixture already passes and must remain GREEN. Production implementation is
reauthorized only against these frozen bytes. No live continuation is allowed
until the superseding gate and independent audit are GREEN.

### Final-review GREEN and checkpoint-migration expansion — 2026-08-08

The superseding final-review contract is GREEN at:

- coverage/benchmark SHA-256
  `a9e1b42df8a94a501f2f4dc386863b8867219a81b0b1284c8f77ea5b898f552e`;
- comparison SHA-256
  `9d7081cfee0a8c492bfa9b55539ff3140c8d2b098dfd9a2a196d92d86247de56`;
- legacy Behavior Map V0 SHA-256
  `0b08864dbab5bc3b21284d08829ff296e03d9ebba7caf5769cb6c96e7c0656f7`.

The orchestrator and independent auditor reproduced 28/28 focused and 119/119
full Behavior Map tests, Ruff, strict mypy, and unchanged predecessor hashes.
Fresh extraction now requires the versioned field-grounding schema; therefore
pre-repair checkpoint identity cannot be silently reused. The interrupted
owner-authorized campaign consumed 97 Luna attempts before review stopped it.
To continue without retrying those attempts or exceeding the same USD 70
campaign ceiling, the change budget expands once to a bounded versioned
checkpoint migration module and one synthetic test file:

- test author may add only
  `triana-labs/tests/behavior_map/test_behavior_map_checkpoint_migration.py`;
- implementation author may add only
  `triana-labs/src/triana_labs/behavior_map/migration.py` and the smallest
  call seam in the already-authorized Behavior Map files.

The independent test freeze names the bounded module
`triana-labs/src/triana_labs/behavior_map/checkpoint_migration.py`; that exact
path supersedes `migration.py` above without expanding file count or behavior.
The test file SHA-256 is
`f743a3f410ecf22689ae06bc53ccfc32a8f831a16479d22262566bac7658e656`,
with five expected missing-module RED cases and Ruff GREEN.

Independent integration audit supersedes that preliminary migration freeze
with SHA-256
`89c63635d56a50ca452a299d6b707e6f1e34ad2361d2165380cc83f2b1b72f4f`.
Against the isolated draft it produces four substantive RED and four control
passes: the migrated path/identity must equal the real current `_call_plan`, a
mixed four-conversation `run_behavior_map` continuation must make zero calls
for grounded/refused/FAILED/IN_FLIGHT predecessor units, 97 prior attempts and
their reservation remain charged, and empty/out-of-range grounding bindings
must refuse migration. This hash is the implementation authority.

The final migration safety freeze supersedes that hash with SHA-256
`affd714d221cd1fcaecb782eb3ea6aea910ba33c4b1f9a791b684207096c9085`.
It adds only whole-unit refusal for non-empty constraints or fallbacks whose
aligned binding is missing or out of range. Against the paused draft it yields
eight expected RED and four controls passing; Ruff is GREEN. This is the final
implementation authority.

The integration fixture was corrected to derive stages from the runtime's
sorted conversation order. SHA-256
`8aafc186d14168f40f9f4f7188412691ec1b9143dda73dabca08bf7b30ace302`
supersedes the preceding migration hash. It yields eleven controls GREEN and
one substantive RED: the runtime must consume the validated migration refusal
sidecar and skip the exact refused unit inside the existing enumerated loop,
without compacting stage indexes or changing denominators.

Independent code audit found that a stale valid destination sidecar could be
trusted without manifest authority. Migration test SHA-256
`01bd050edaaedc30d7b27cde4db24e4f141dcdbc517393efd5669ebf8f4f225a`
supersedes the preceding hash, with nine expected RED and eleven controls
passing. A sidecar now requires exact manifest binding for migration identity,
predecessor report, source and selected-list hashes, primary model and provider
binding, predecessor attempt count, and prior reservation. Missing or mismatched
binding fails closed before egress as `MIGRATION_BINDING_INVALID`; paths remain
private and absent from report/provider payloads.

Migration may project only immutable extraction checkpoints whose every episode
already contains explicit field bindings. It adds the contract-version marker,
validates the complete new schema, writes a new identity plus predecessor hash
sidecar, and never edits the source. Missing grounding, FAILED, or IN_FLIGHT
legacy attempts become new typed non-callable refusals and cannot be retried.
Migration is enabled only by an explicit private manifest path and predecessor
identity, remains outside provider payloads/reports, is byte-repeatable, and
must prove zero provider calls. No population/audit checkpoint migration,
semantic reinterpretation, dependency, or additional live campaign is allowed.

### Interrupted-campaign authority correction — 2026-08-08

The real stopped campaign contains an immutable manifest plus 97 extraction
checkpoint/attempt artifacts but no completed `behavior_map_report_v0`.
Manufacturing a completed predecessor report would falsely elevate partial
execution evidence. The migration source contract therefore expands only to a
typed, content-free `behavior_map_partial_campaign_v0` ledger that binds the
exact manifest hash, source and selected-list hashes, primary provider
identity, complete checkpoint-ID set, attempted-call count, prior reservation,
and cumulative ceiling. The existing migration production file remains the
sole implementation surface; no provider behavior or dependency changes.

Independent test author owns only
`triana-labs/tests/behavior_map/test_behavior_map_partial_campaign_migration.py`.
Its frozen SHA-256 is
`fb4e3f130d3aacf1641828e04f1949b5427c13658eea8eb1066d2a050bf23e1d`.
The frozen RED is 11 failures at the absent partial-campaign API with Ruff
GREEN. Acceptance requires exact checkpoint conservation, immutable inputs,
no forged report, no path leakage, and refusal of every missing, extra, or
tampered authority field before any provider execution.

Independent audit supersedes that preliminary partial-campaign freeze with
SHA-256
`3738c34ebaca02f216dcc19542a8d7013c8636ec210f6e226d41d08333389c12`.
The orchestrator reproduces 30 expected RED with the existing 20 checkpoint-
migration controls GREEN and Ruff GREEN. The complete contract additionally
binds an exact 97-entry artifact inventory and tree hash; validates file,
identity, payload/descriptor, result, provider, scope, sealed-count, budget,
retry/fallback, and contiguous-stage integrity; keeps baseline predecessor and
resume lineage distinct; projects 87 migratable and 10 nonretryable units;
requires zero calls for stages 0–96 and next stage 97; carries USD 69.912 once
with prior external reservation zero and actual cost unknown; and requires
path-free, byte-stable ledger, migration, and successor-lineage output. The
implementation author may edit only the existing
`triana-labs/src/triana_labs/behavior_map/checkpoint_migration.py` and the
smallest already-budgeted runtime seam in `behavior_map/__init__.py`.

Metadata-only replay against the real stopped campaign falsified one fixture-
specific assumption: the 97 attempted extraction stages are a prefix of 374
DEVELOPMENT conversations, not the full corpus denominator. The smallest
reproduction failed at an equality check between inventory count and
development count. The speculative inequality edit was reverted before the
independent test freeze. SHA-256
`609d30c407cafbe1b732e8a8017489114bee6f9528f7e11f3a1eeed874d9266b`
supersedes the partial-campaign test hash. The orchestrator reproduces 30
controls GREEN and two focused RED: 97 contiguous attempts within 374 selected
DEVELOPMENT conversations must preserve both numbers, while 97 attempts within
only 96 DEVELOPMENT conversations must refuse as
`PARTIAL_CAMPAIGN_INVENTORY_INVALID`. No other contract or file budget changes.

The first denominator-frontier test freeze assigned contradictory error codes
to the same 97-attempt/96-DEVELOPMENT mutation. The test author removed that
mutation from the generic binding table so the dedicated conservation test
alone owns `PARTIAL_CAMPAIGN_INVENTORY_INVALID`. SHA-256
`745539585457fe7c90a51867f4e324439c23c9dc766c0fb7bce8765d065d9ef5`
supersedes the preceding hash; the orchestrator reproduces 29 controls GREEN
and the same two substantive RED without contradictory caller-dependent
behavior.

### Pre-live partial-resume accounting and authority correction — 2026-08-08

The actual provider-free artifact audit passed inventory and migration
integrity but reproduced two live-blocking artifact-contract defects before
egress. First, runtime treated the full USD 69.912 campaign reservation as
prior spend and added the same configured primary/audit plan again. Second, a
completed successor would inherit the interrupted ledger's top-level
`NOT_EVALUATED` state. The ledger and migration remain NOT_EVALUATED; the
successor remains private, proposed, and partial under existing object-level
statuses, audits, and gaps, with predecessor campaign state expressed only as
lineage.

Independent test SHA-256
`76b5beaf1c54ffe86fc115e4cfa7044ea677fa30995922f3a9eebce13043c248`
supersedes the partial-campaign hash. The orchestrator reproduces 31 controls
GREEN and two focused RED: the resumed campaign must authorize and report USD
69.912 exactly once under the USD 70 ceiling with prior external reservation
zero and actual cost unknown; and a successor with one fresh semantic call
must not inherit the ledger-only `semantic_evaluation_state=NOT_EVALUATED`.
Baseline predecessor and resume-campaign lineage remain explicit. No provider
call is authorized until both are independently GREEN.

### Exact legacy predecessor compatibility — 2026-08-08

The first successor command exited before egress with zero Luna and zero Terra
attempts. The observed `PREDECESSOR_REPORT_MISMATCH` is isolated to the accepted
baseline report predating source-level `selected_list_sha256` and
`development_count`; its report ID recomputes exactly and its source hash,
semantic denominator, sealed counts, and manifest selection agree. Independent
comparison-test SHA-256
`e541c8cd535d450b0b93db10d183e31ba436ebc99097a49b57ba164803eea415`
freezes 14 controls GREEN and one RED for that exact legacy shape. Report-ID,
content-identity, source, semantic-count, sealed-count, and manifest-selection
tampering remain rejected before egress, and the newer strict predecessor path
remains unchanged. Implementation author may edit only the existing predecessor
loader in `behavior_map/__init__.py`; no provider, migration, comparison,
dependency, or private-artifact change.

The first exact-legacy fixture stored its selection hash at the newer test
fixture's top-level semantic scope, while the real accepted manifest stores it
under `semantic_scope.selection`. The second successor command again exited
with zero provider attempts. SHA-256
`c4e09298d70f99e5ae2fdc3238007b064696a86a69f9a2d0c89c3d34f746bec2`
supersedes the comparison freeze with 15 controls GREEN and one nested-shape
RED. Tampered nested selection hash or nested development count still rejects
pre-egress; the strict newer path and top-level compatibility controls remain
unchanged. Implementation remains a loader-only normalization in
`behavior_map/__init__.py`.

Independent review found two stale assertions in that freeze: zero calls apply
only to reused/refused extraction stages 0–96, not later successor
consolidation/audit, and `prior_reserved_usd` means external prior reservation,
not the resumed campaign reservation. SHA-256
`bb9b40be5502651b0c7f8b1193b6c5f5162c16a14143f4c17de28f6e1c2ff54d`
supersedes the preceding partial test hash. Schema-valid fake continuations now
prove 32 controls GREEN; the sole RED is migration handoff reporting USD
69.912 as prior instead of external prior USD 0. The campaign reservation
remains separately USD 69.912 and total reservation remains USD 69.912 once.
The implementation scope expands back to the already-authorized single line in
`checkpoint_migration.py` plus the current `__init__.py` fix; no other surface
changes.

### Live population-batch failure isolation — 2026-08-08

The single owner-authorized successor campaign completed extraction and then
reproduced a third deterministic orchestration defect. The immutable failed
successor artifact is
`/private/tmp/triana-blitz-coverage-repair-continuation-final-20260808`
(`sha256:0daea358863c5bd0cffe4654250f3575f7363ae29e2184da04f7ac0478ea54ca`).
It contains 406 surviving episodes across 263 conversations, but one Luna
provider failure at first-level population batch 15 escaped the batch boundary;
the outer pipeline catch consequently discarded 15 preceding valid population
batch results and emitted zero populations or patterns. This artifact is typed
failed evidence, not an accepted successor and not a replacement for baseline
`sha256:9c98854dba09a188600b5de7a6f20e71a86ea01791d61556e31f40f16fd1f021`.

Observed failure: one content-free `behavior_map_attempt_v0` with stage
`user-populations-0015` and state `FAILED`; stages 0000–0014 are schema-valid
checkpoints. Smallest reproduction: a fake model with valid population output
before and after one deterministic batch failure. Falsifiable hypothesis: if
first-level population batching isolates `_call` failures using the same typed
carry-forward discipline already used by leftover matching, the failed batch's
input episodes remain explicitly unassigned/unknown, earlier candidates
survive, later batches execute, and replay refuses the recorded failed attempt
without a provider retry. Falsifying evidence would be loss of any supplied
episode, loss of an earlier candidate, a skipped later batch, acceptance of an
unsupplied ID, or any second call for the failed batch.

The frozen change budget expands only within existing authorized files:

- independent test author: the existing bounded Behavior Map coverage test
  surface under `triana-labs/tests/behavior_map/`;
- implementation author: only
  `triana-labs/src/triana_labs/behavior_map/__init__.py`;
- orchestrator: this append-only slice entry and later accepted canonical
  documentation/decision records already budgeted by the parent slice.

No prompt, schema, citation, audit, retry, fallback, dependency, deployment,
baseline, or private-artifact mutation is allowed. Provider continuation may
use only the unconsumed calls inside the existing USD 69.912 campaign ceiling;
the failed batch itself is nonretryable. No new reservation is authorized.

Independent test SHA-256
`8bc8e91093404c06084ec9cb780a75003da39f15e7f1c31df0f872a0883a0cd7`
froze two RED cases. The independent implementation author and orchestrator
then reproduced 22/22 coverage-repair and 182/182 Behavior Map tests GREEN,
plus Ruff, format, strict mypy, and diff checks. The live continuation proved
the repair: batch 15 remained a single immutable FAILED attempt, batches 16–31
executed, and the next private report retained 406 episodes, 299 unique
assignments, and 114 population proposals.

### Live agent-pattern batch failure isolation — 2026-08-08

The population-valid continuation report
`sha256:4a19880a08ba42e2e164e3a6d8f22167775288414694b60f26fcc4f6119e766a`
is preserved read-only at
`/private/tmp/triana-blitz-coverage-repair-populations-only-snapshot-20260808`.
It is not an accepted successor because one Luna provider failure at
`agent-behavior-patterns-0011` escaped the first-level pattern batch boundary;
the outer catch discarded 11 earlier valid pattern-batch results and emitted
zero patterns and zero audits.

Observed failure: one content-free FAILED attempt at pattern batch 11 after 11
schema-valid pattern checkpoints. Smallest reproduction: a fake pattern model
with valid output before and after one deterministic batch failure. Falsifiable
hypothesis: applying the already-accepted batch-failure isolation contract to
first-level pattern grouping preserves earlier and later candidate patterns,
types the failed occurrences as excluded/unknown evidence, and makes replay
byte-stable without retrying the failed batch. Falsifying evidence is any lost
supplied occurrence, accepted failed occurrence support, skipped later batch,
mutated/retried attempt, or changed replay identity.

Change budget remains the same existing coverage test file for the independent
test author and only `behavior_map/__init__.py` for the implementation author.
No prompt, schema, support threshold, citation/audit rule, dependency, retry,
fallback, or artifact mutation is allowed. Exactly 428/499 Luna campaign
attempts now exist; a continuation may use no more than the remaining 71 Luna
calls plus the original unused 89 Terra audits under the same USD 69.912 cap.

### Provider-disabled post-grounding semantic projection — 2026-08-08

The independent artifact audit proved that three otherwise completed live
episodes retained out-of-range field-grounding indexes after subject-relevance
citation detachment. Frozen test SHA-256
`413cfe308fbd699b273a4ad697e73b02461ad43b070f43cb1857357506a62970`
is GREEN: one mandatory-ungrounded episode is now rejected, while two episodes
with unsupported optional fields are projected to new grounded identities with
visible uncertainty. A provider-disabled extraction replay therefore contains
405 episodes: 403 exact live identities, two explicit replacements, and one
rejection. Because that identity correction changes size-bounded grouping
payloads, later semantic checkpoints cannot be replayed as if their inputs were
unchanged. No further provider reservation remains under the owner USD 70
ceiling.

Falsifiable hypothesis: the already completed semantic result can be projected
onto the corrected episode frontier without inventing semantic authority if and
only if exact unchanged subjects retain their own evidence/audit; changed
population membership or pattern occurrence-membership is recomputed with new
identity and predecessor lineage but remains unpublished with current audit
MISSING; optional-grounding replacements receive episode predecessor lineage
but no automatic population assignment; the mandatory-invalid episode and all
derived occurrences are detached from support and preserved as excluded
history. Every denominator, disposition, support value, and before/after edge
must conserve exactly. The output is a new private proposed partial historical
projection, never a fresh full reanalysis, Defect-B benchmark pass, or baseline
replacement.

Frozen expansion budget:

- independent test author: only a new bounded provider-disabled projection
  test under `triana-labs/tests/behavior_map/`;
- implementation author: only a new projection module under
  `triana-labs/src/triana_labs/behavior_map/` plus the smallest export seam if
  needed;
- orchestrator: a fresh `/private/tmp` output root, comparison artifact, and
  already-budgeted canonical documentation/decision append;
- dependencies, prompts, provider adapters, retry/fallback, thresholds,
  baseline artifacts, existing live/snapshot roots, and customer publication
  remain untouched.

Acceptance requires zero provider calls; exact source/selection/predecessor
binding; 100% valid final grounding; one disposition per corrected episode;
unique membership/support; no rejected episode or occurrence in support;
unmodified successful baseline hashes; byte-identical repeated projection; and
an independent artifact verdict. Human semantic benchmark metrics remain typed
`HUMAN_LABELS_MISSING`.

## BEHAVIOR-MAP-V0-PATTERN-AND-DISPOSITION-CONSERVATION — 2026-08-09

### Entry gate and active outcome

This slice advances the active Labs Phase 1 outcome only by making the existing
private, proposed Behavior Map mechanically conservative and attributable. It
does not change semantic prompts, grouping thresholds, accepted taxonomy,
provider behavior, or launch claims. Canonical base is
`992422f36292e4b40b56ede690182819fdb6749d`; the pre-existing user edit to
`internal/WORKING_MEMORY.md` is outside this slice and must remain untouched.

The accepted Blitz report at
`/private/tmp/triana-blitz-full-development-corrected-final-20260808/report`,
baseline record `internal/BEHAVIOR_MAP_BLITZ_BASELINE_2026-08-08.md`, and tag
`best-version-yet-blitz-20260808` (peeled commit
`68741dab5824709932335d23405b95d754107fce`) are immutable inputs. Their JSON,
Markdown, and HTML hashes remain respectively
`9821a041d391843bae8885010c6180a58a38646f3bd33d56382e5f18a3a8f0f1`,
`7733ccfb3ea73f20043b00464f2dbc8a8c5df92f91a2d509d058e233b40d72b6`,
and `5e83984622aae54c49c53b6355b3865816f4fac021ccf8a7ff2b694897a26377`.
The historical projection and continuation named by the owner are read-only
evidence. Any replay output must use a fresh private path and explicit
predecessor lineage.

### Frozen contract and authority

Input is synthetic fixtures or existing provider-disabled report/checkpoint
artifacts. Output is a new `behavior_map_report_v0`, historical projection, or
comparison whose pattern-occurrence and population membership accounting is
complete and whose missing authority remains typed. Deterministic code owns
occurrence dispositions, supplied-ID validation, candidate identity and
membership, support, audit visibility, population membership/disposition
equality, denominators, comparison comparability, and predecessor lineage. An
LLM may only propose semantic membership or no match; it makes no calls in this
slice. A human remains the sole authority for accepted taxonomy or baseline
promotion.

Every eligible pattern occurrence must have exactly one terminal disposition.
Successful-batch omissions and foreign IDs remain visible typed evidence;
foreign IDs never become support. Audit-missing pattern candidates retain
stable candidate identity, membership, label, definition, evidence lineage,
and missing/unpublished state while contributing zero published support.
Reports distinguish eligible occurrences, terminal dispositions, candidate,
audited, supported, disputed and audit-missing patterns, and active versus
unpublished memberships. Population active membership must equal exactly the
episodes disposed `ASSIGNED`; disputed or rejected subjects contribute zero
support. Historical projection cannot restore a predecessor
`AUDIT_DISPUTED` episode without a current explicit supported ruling.
Zero-lineage pattern counts are raw non-comparable counts, never direct loss,
reduction, or regression.

Privacy and execution remain `LOCAL_PRIVATE`. Provider calls, network egress,
new spend, retry/fallback, customer-data publication, accepted-artifact
mutation, and private checkpoint content in committed fixtures are forbidden.
Unknown, ambiguous, failed, omitted, insufficient, and missing-audit states
fail visibly and cannot become support.

### Single-hypothesis debugging ledger

1. Observed B1/B2/B3/B10: successful pattern responses omit supplied IDs,
   return foreign IDs, and leave ordinary unassigned reporting coupled to the
   generic-label branch. Hypothesis: first-level output is merged without an
   exact supplied-input disposition projection. Falsified if per-batch
   reconciliation already conserves all supplied IDs and types all foreign
   edges. One attempted production change may add only that reconciliation and
   ordinary unassigned projection after independent RED.
2. Observed B4/B5: audit scheduling stops before all candidates and final code
   filters missing IDs from `patterns`. Hypothesis: supported publication and
   candidate retention share one collection. Falsified if missing candidates
   already survive with zero active support. One attempted change may separate
   candidate retention/audit state from published support and accounting.
3. Observed B6: 61 baseline and 24 successor patterns have zero preserved or
   superseded pattern lineage yet comparison classifies aggregate movement.
   Hypothesis: object-count delta is allowed to drive regression without
   subject-level lineage comparability. Falsified if pattern semantic movement
   is already explicitly non-comparable. One attempted change may add only the
   lineage-scoped refusal and rendering.
4. Observed B7/B8: continuation has 221 active population members but 220
   `ASSIGNED` dispositions, including one supported member disposed
   `AUDIT_DISPUTED`. Hypothesis: population support and dispositions are
   finalized from different active sets. Falsified if the publication gate
   already enforces exact set equality and disputed exclusion. One attempted
   change may centralize projection/validation without changing thresholds.
5. Observed B9: historical projection derives `ASSIGNED` from supported
   population membership before consulting predecessor disposition.
   Hypothesis: predecessor dispute authority is ignored on exact membership.
   Falsified if a current explicit supported ruling is required. One attempted
   change may preserve dispute absent that ruling.

Suspected S1–S6 are investigation-only. Each receives the smallest synthetic
or artifact-metadata reproduction and a falsifiable result. No production
change is allowed unless independent RED promotes it to a separately confirmed
mechanical defect within this exact change budget; semantic count or quality
movement alone cannot do so.

### Frozen change budget and role ownership

- Independent test author only:
  `triana-labs/tests/behavior_map/test_behavior_map_pattern_conservation.py`,
  `triana-labs/tests/behavior_map/test_behavior_map_comparison.py`, and
  `triana-labs/tests/behavior_map/test_behavior_map_historical_projection.py`.
  It may not edit production, canonical docs, or artifacts.
- Independent implementation author only:
  `triana-labs/src/triana_labs/behavior_map/contracts.py`,
  `triana-labs/src/triana_labs/behavior_map/__init__.py`,
  `triana-labs/src/triana_labs/behavior_map/comparison.py`,
  `triana-labs/src/triana_labs/behavior_map/historical_projection.py`, and the
  smallest necessary report projection in
  `triana-labs/src/triana_labs/behavior_map/render.py`. It may not edit tests.
- Orchestrator only: this slice packet; the smallest accepted updates to
  `docs/CONTRACTS.md`, `docs/ARCHITECTURE.md`, `triana-labs/CHARTER.md`, and an
  append-only `internal/DECISION_LOG.md` entry; ignored decision memory; a new
  content-free comparison handoff under `internal/`; and fresh private outputs
  under `/private/tmp/triana-blitz-pattern-conservation-repair-20260809-*`.
- Final verifier is read-only and may not repair tests or production.

No dependency, prompt, schema-provider, adapter, retry/fallback, grouping
threshold, UI/backend, deployment, provenance, accepted baseline record,
accepted private artifact, or `internal/WORKING_MEMORY.md` edit is allowed.
Workers stop before any unbudgeted file or policy change. Maximum scope
expansion is zero without a new owner-approved packet amendment.

### Independent acceptance contract

The test author must freeze black-box RED for owner cases A–K: omitted supplied
occurrence; rejected/typed foreign occurrence; ordinary unassigned reporting;
audit-budget candidate retention; candidate identity stability across resume;
zero-lineage comparison refusal; disputed-member exclusion; membership versus
disposition integrity failure; historical dispute preservation; the historical
221/220 inconsistency; and unchanged 8 re-audit-required, 2 grounding
replacement, 1 grounding rejection, 0 unexplained projection edges. Tests use
only synthetic fixtures and content-free immutable metadata. Provider methods
must fail if invoked.

The orchestrator freezes exact test hashes and reproduces RED before production
handoff. GREEN requires all owner acceptance gates, byte-identical repeated
deterministic projection, unchanged accepted hashes/tag, focused tests, full
Behavior Map tests, full repository verification, Ruff check, Ruff format
check, strict mypy, governance checks, and diff/change-budget reconciliation.
No unrun command may be reported as passing. Final artifact verdict remains
private proposed partial and baseline promotion remains human-blocked.

### Independent RED freeze

The independent test author froze these exact test bytes:

- `test_behavior_map_pattern_conservation.py`:
  `c6dc52ba7318b11af83b7e7b0bf7e38aa5ad318829f7d8f652b29928bac9503c`;
- `test_behavior_map_comparison.py`:
  `1a5218e6e065a1ef990dbd5d92ca0fba7f68b44c88b7b47879d800e5e52eefc7`;
- `test_behavior_map_historical_projection.py`:
  `14d0067299ad518992c9c8e3cfea753922197e64f0cf773510e2579fd1c590c6`.

The test author observed four focused pattern RED (missing occurrence
dispositions, deleted missing-audit candidates, and absent exact
population/disposition conservation validation), one comparison RED (zero
pattern lineage still lacks subject-level non-comparability), and one
historical-projection RED (an exact predecessor `AUDIT_DISPUTED` episode is
restored to `ASSIGNED`). Eighteen comparison and seventeen projection controls
remain GREEN. The exact projection control preserves 8 re-audit-required
memberships, 2 grounding replacements, 1 grounding rejection, and zero
unexplained edges. Existing hierarchy-abort preservation and subject-scoped
audit controls are GREEN; S3 is not promoted. S1/S2 reproduce only the already
confirmed missing disposition and missing-candidate custody defects. S4–S6
remain human-label-blocked semantic hypotheses.

The orchestrator then reproduced 41/41 frozen checks GREEN and 215/217 full
Behavior Map checks GREEN. The two failures are direct contradictions in
`test_behavior_map_v0.py`: one conflates exclusive user-population disposition
with non-exclusive agent-behavior uncertainty; the other requires missing-
audit pattern candidates to be absent rather than retained unpublished. The
test-author budget expands only to those two assertions in
`triana-labs/tests/behavior_map/test_behavior_map_v0.py`. The independent test
author must preserve the original population exclusivity guarantee using
`population_dispositions`, assert behavior uncertainty independently, and
replace absence with explicit `MISSING` plus `UNPUBLISHED_AUDIT_MISSING` and
zero active support. No other assertion, fixture, production file, or scope is
authorized by this reconciliation amendment.

Independent code review then exposed four additional owner-gate holes in the
first GREEN implementation: audited-disputed patterns were still deleted,
duplicate pattern membership could be overwritten by the one-row disposition
map, duplicate active population membership was reduced to a set, and declared
population support was not checked against unique membership. The corrected
superseding test freeze is:

- `test_behavior_map_v0.py`:
  `eda0ef70d67fcca1f3a6458432783b798f9255055cea6df4d4881d5df4915fc8`;
- `test_behavior_map_pattern_conservation.py`:
  `4e692daeb9547a08bffeea8722e7c61f2ed6cc78264d54aaf6159a3b84f5c3f7`;
- comparison and historical-projection hashes remain
  `1a5218e6e065a1ef990dbd5d92ca0fba7f68b44c88b7b47879d800e5e52eefc7`
  and
  `14d0067299ad518992c9c8e3cfea753922197e64f0cf773510e2579fd1c590c6`.

The independently reconciled full Behavior Map result is 217 GREEN and four
expected RED, exactly for disputed-pattern retention, duplicate pattern
membership, duplicate active population membership, and population support
mismatch. Missing-population policy is explicitly unchanged; B4 remains
pattern-only.

After disputed retention became GREEN, one stale whole-pattern audit assertion
was reconciled from record deletion to unpublished disputed custody. The final
frozen `test_behavior_map_v0.py` SHA-256 is
`243cf7f57292ca5a208651d91c1ad6e1d0622bbae590e108a131154dbedbd735`.
Its remaining RED is a production precedence defect: one occurrence retained
in an audited `UNSUPPORTED` pattern still carries the earlier
`MODEL_OMITTED_OCCURRENCE` terminal state while the other retained members are
`AUDIT_DISPUTED`. Retained audited subject authority must win terminal
disposition; omission history may remain visible separately.

Making disputed-pattern custody GREEN exposes one final stale assertion in
`test_behavior_map_coverage_repair.py`: it equates subject-scoped pattern audit
rejection with record absence. The test-author budget expands only to that
assertion. It must preserve the original proof that pattern audit rejection
does not alter episode population assignment, while asserting the rejected
pattern remains `UNSUPPORTED` and `UNPUBLISHED_AUDIT_DISPUTED` with zero active
pattern support. No other coverage-repair assertion or fixture may change.

The independent reconciliation changes only that assertion and freezes
`test_behavior_map_coverage_repair.py` at SHA-256
`422a6a5ad7bd86e357f6952d63e00a5fcadcefa1cf458afb351a62b2524a1b69`.
Focused coverage is GREEN and the independent full Behavior Map suite is
221/221 GREEN; all population assignment/support and byte-identical replay
controls remain intact.

Orchestrator review then proved the exact-input B2 contract was still incomplete
inside pattern hierarchy: an occurrence omitted from first-level candidates
could be reintroduced later because hierarchy output was checked against the
global eligible set rather than the exact candidate members supplied to that
hierarchy batch. The independent hierarchy-boundary RED freezes
`test_behavior_map_pattern_conservation.py` at
`3a60e916c25defe6a6af145096a03aaaf2db038fff95a94af68d7b69e4f04bc1`
and the reconciled V0 assertion at
`d886ec868cf4f2958ae77d06d2c5ccd48c4c492c2bd684bc2b7200714a715690`.
The exact omitted member must remain `MODEL_OMITTED_OCCURRENCE`; hierarchy must
type and reject its reintroduction before support or later audit projection.

Read-only final verification then reproduced two additional exact-accounting
defects: explicit `UNCERTAIN` is disputed but omitted from audited-pattern
count, and set-only population validation accepts duplicate disposition rows or
an `ASSIGNED` row naming the wrong population. The superseding pattern-test
SHA-256 is
`c9907bd564c26e32e63f24b4ef0c100720b94ac289b82aabff70fbcfab8ac026`.
Three independent RED require one explicit uncertain ruling to count as both
audited and disputed (never missing), duplicate disposition rows to refuse as
`POPULATION_DISPOSITION_DUPLICATE`, and wrong episode-to-population assignment
edges to refuse as `POPULATION_ASSIGNMENT_EDGE_MISMATCH`.

Final read-only review confirmed hierarchy foreign membership was rejected and
typed but required its summary count to cover the same boundary. The
superseding pattern-test SHA-256 is
`ed245c687f4674f8afbef08b4ff0f7de1cb80c2c2778a0ffc57ac9be8b20ec79`;
the hierarchy fixture is GREEN with one rejected hierarchy-only ID and
`pattern_accounting.foreign_occurrence_id_count == 1`.

### Final verification and change-budget reconciliation

The final provider-disabled repository gate ran with `UV_OFFLINE=1` and
`PIP_NO_INDEX=1` so its clean-wheel installation could not use network egress.
It completed 891 tests plus governance, Ruff, formatting, strict mypy, build,
clean-wheel installation, deterministic replay, and source/installed-command
parity. The evidence root is `/private/tmp/triana-labs-verify.ci4fqv`; the
captured log is
`/private/tmp/triana-pattern-conservation-final-verify-offline.log`.

The final test hashes are:

- pattern conservation:
  `ed245c687f4674f8afbef08b4ff0f7de1cb80c2c2778a0ffc57ac9be8b20ec79`;
- V0:
  `d886ec868cf4f2958ae77d06d2c5ccd48c4c492c2bd684bc2b7200714a715690`;
- comparison:
  `1a5218e6e065a1ef990dbd5d92ca0fba7f68b44c88b7b47879d800e5e52eefc7`;
- historical projection:
  `14d0067299ad518992c9c8e3cfea753922197e64f0cf773510e2579fd1c590c6`;
- coverage repair:
  `422a6a5ad7bd86e357f6952d63e00a5fcadcefa1cf458afb351a62b2524a1b69`.

Two provider-disabled projection runs are byte-identical at SHA-256
`5918a71382294c466ea8b096f3b8071b0240d688336dc3967a5201d521cb7b63`
under
`/private/tmp/triana-blitz-pattern-conservation-repair-20260809-projection-v1`
and the corresponding `-v2` directory. They made zero provider calls. The
accepted report hashes and `best-version-yet-blitz-20260808` tag remain
unchanged.

Actual production changes stayed within the four authorized Behavior Map
files; `render.py` was untouched. Test changes stayed within the independently
amended five-file test budget. Canonical and handoff changes stayed within the
orchestrator budget. No dependency, prompt, provider adapter, retry/fallback,
threshold, UI, deployment, provenance, accepted baseline, or accepted private
artifact changed. The existing `internal/WORKING_MEMORY.md` modification is a
preserved pre-slice user change and is excluded from this slice.
