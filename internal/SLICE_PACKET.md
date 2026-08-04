# LABS-04 through LABS-06 grounded-workflow closure packet

Date frozen: 2026-08-03

Status: **LOCAL GREEN; LIVE REAL-DATA EXECUTION BLOCKED PENDING A NEW CONTRACT SLICE AND EXACT EGRESS APPROVAL**

Slice ID: `LABS-046-GROUNDED-WORKFLOW-CLOSURE-V1`

Canonical base: commit `909f6cb` on branch
`codex/labs-06-regular-user-fidelity`, plus the already verified uncommitted
LABS-06 final-conformance slice and orchestrator documentation. Those frozen
LABS-06 test bytes remain unchanged.

Authority: `triana-labs/CHARTER.md` -> `internal/DECISION_LOG.md` ->
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md` -> this packet.

## 1. Product outcome

Close the supported LABS-04/05/06 loop with production-trace-derived,
world-valid, outcome-bearing workflows rather than optimizing isolated
conversation turns. LABS-04 must visibly separate observed production cases
from grounded expansions. LABS-05 must execute a nontrivial ordered panel.
LABS-06 must advance the verified workflow goal until its declared completion
condition or an allowed structured stop.

Local implementation and fake acceptance come first. Read-only HRAI RDS
discovery is owner-authorized, but no provider, HRAI target, or real-data
episode execution occurs until local GREEN and a separate exact pre-egress
bundle, endpoint, and cost approval.

## 2. Case contract

The restricted LABS-04 closure mode requests exactly twelve cases. Each draft
adds only:

```json
{
  "goal": {"text": "...", "basis": "OBSERVED", "claim_keys": ["..."]},
  "done_when": {"text": "...", "basis": "OBSERVED", "claim_keys": ["..."]},
  "required_world_keys": {
    "candidate_id": ["cand-example"],
    "position_id": ["pos-example"]
  }
}
```

`goal` and `done_when` must be nonempty `OBSERVED` supported text. Closure-mode
cases reject `GENERATED_VARIATION` in the opening, goal, done condition, case
scenario, linked intent, linked persona, or linked turn policy. An LLM may
extract or summarize cited evidence; it cannot invent behavior, facts,
identifiers, goals, completion conditions, or task requirements.

`required_world_keys` is a closed mapping whose field names and values are
portable safe identifiers, sorted and unique, with at most eight namespaces
and sixteen values per namespace. It is provider-authored only by selection
from the exact verified world inventory supplied to generation. Unknown or
unavailable values invalidate the case. It is not repaired, substituted, or
defaulted.

Deterministic code derives and writes:

- `case_origin = OBSERVED_PRODUCTION_CASE` when the opening, goal, done
  condition, and their supporting case claims resolve to exactly one common
  source trace;
- `case_origin = GROUNDED_EXPANDED_CASE` when those same wholly observed
  anchors resolve across two or more source traces;
- `source_trace_ids`, the sorted unique union of trace IDs supporting the
  opening, goal, and done condition.

The model cannot author or override `case_origin` or `source_trace_ids`.
Zero-source, unknown-source, mixed generated/observed, or unsupported anchors
are invalid and cannot publish as a case or pass.

## 3. Larger trace evidence

The closure path removes the arbitrary 25-trace evidence-count cutoff. It
walks the entire eligible, deterministically round-robin corpus and includes
traces until the existing bounded provider-evidence byte ceiling is reached.
The ceiling, not a chosen trace count, stops projection. Exact total eligible,
selected, excluded, and byte-limit counts remain in the evidence index. No
trace is silently counted as used when it was excluded.

The production RDS export may contain any number of authorized traces. Local
Observer and Corpus Intelligence process the full exported corpus; the case
provider sees only the privacy-validated bounded evidence projection.

## 4. World inventory and preflight

Closure generation and execution receive the same versioned
`LABS046_WORLD_INVENTORY_V1` JSON artifact. It contains only allowlisted
namespaces and sorted unique identifiers plus its declared data class and
source lineage. Its exact bytes are hashed into case generation, case
identity, owner selection, run identity, and both Markdown reports.

For every selected episode, deterministic code verifies that every
`required_world_keys` value exists in the inventory before target creation or
simulator reservation. A missing value produces one partial shell episode and
typed gap `WORLD_DATA_UNAVAILABLE`, with safe namespace/count details, zero
target starts, zero target/simulator exchanges, and zero reservation. Later
world-valid slots continue. No target query, retry, repair, substitution, or
fallback occurs during preflight.

This check proves consistency with the separately captured target-world
inventory. It does not claim that arbitrary remote target state cannot change
after capture; inventory identity and capture time stay visible.

## 5. Goal-first LABS-06 continuation

The LABS-06 simulator request carries exact top-level `goal`, `done_when`,
`case_origin`, and `source_trace_ids` ahead of the existing verified context,
episode state, transcript, and latest observation.

The provider instruction says: advance the declared goal using the latest
assistant response; do not stop merely because the assistant asks a question,
offers alternatives, returns partial information, or needs a valid selection;
return structured STOP only when `done_when` is satisfied, the supported goal
is genuinely impossible, or an existing allowed final boundary applies.
Persona controls language, patience, and reaction only.

The provider still returns exactly `disposition`, `user_utterance`, and
`stop_reason_code`. Deterministic code does not invent a next turn or infer
semantic goal completion. Existing role, echo, hidden-fact, fixed-fact,
action, stop, privacy, identity, observation-binding, termination, accounting,
custody, dedupe, diagnostics, and no-retry rules remain exact. Human review
owns usefulness and workflow completion.

## 6. Versioned 12-case execution mode

Legacy LABS-05 and LABS-06 pinned inputs and behavior remain supported without
change. The new `LABS046_WORKFLOW_CLOSURE_V1` mode is separately closed:

- exactly twelve ordered case IDs;
- exactly six `OBSERVED_PRODUCTION_CASE` and six
  `GROUNDED_EXPANDED_CASE` cases;
- at least nine ordinary workflows and at most three declared recovery,
  mistaken-user, boundary, or adversarial workflows;
- a new owner execution-selection artifact names the exact manifest hash,
  case file hash, ordered IDs, inventory hash, and context hash;
- config, selection artifact, manifest, inventory, and context must agree;
- any mismatch refuses before egress;
- the legacy exact-three descriptor remains unchanged.

The closure run retains U1/A1/U2/A2/U3/A3, one simulator attempt per
continuation, per-episode continuation after typed partial failures, and the
shared conformance circuit. The config declares exact arithmetic for twelve
episodes, at most 24 simulator exchanges, target connector exchanges, time,
tokens, and a maximum USD ceiling no greater than 100. The exact live ceiling
requires separate owner approval.

## 7. Tiered results

LABS-04 publishes manifest-hashed `LABS04_TIERED_CASES.md`, explicitly
non-authoritative:

1. `Observed production cases`
2. `Grounded expanded cases`
3. `Invalid or unavailable evidence`

For each valid case it shows origin, goal, done condition, source trace IDs,
opening, required world keys, declared workflow stratum, gaps, and pending
human state. Untrusted content is escaped or placed in fenced/indented blocks;
it cannot create headings or raw HTML. It never includes secrets, provider
bytes, private hidden facts, or uncited evidence.

LABS-06 publishes manifest-hashed `LABS06_TIERED_RESULTS.md`, also
non-authoritative:

1. `Workflow completed` — owner ruling may later confirm completion;
2. `Multi-turn progress, incomplete` — reached A2 or A3 without confirmed
   completion;
3. `Blocked, invalid, or unavailable` — typed gaps or no continuation.

Each episode shows case tier, goal/done condition, transcript, tools by safe
name/status, accounting, termination, typed gaps, world-preflight status, and
blank owner grading fields. Deterministic code may place episodes in tiers 2
or 3 from evidence. Tier 1 remains empty until Akarsh supplies a completion
ruling; software cannot approve it.

Machine JSON/JSONL remains authoritative. Markdown is a deterministic view of
the same custody and never adds a finding or ruling.

## 8. Evaluation and exit

Local acceptance proves:

1. both exact origins and unspoofable trace provenance;
2. rejection of generated, unsupported, unknown, duplicate, or unsafe case
   fields;
3. evidence selection is byte-bounded rather than count-25-bounded;
4. inventory agreement and no-egress `WORLD_DATA_UNAVAILABLE`;
5. exact goal/done projection and goal-first instruction;
6. legacy three-case compatibility;
7. exact twelve-case accounting, continuation, circuit, and denominator;
8. both deterministic privacy-safe Markdown artifacts and manifest hashes.

The later live close metric is:

- 12/12 production-trace-lined and inventory-valid before execution;
- structural simulator yield at least 95%;
- at least 11/12 reach A2;
- at least 9/12 reach A3 or receive an owner-accepted earlier STOP;
- at least 9/12 owner-confirmed workflow completions;
- zero fabricated identifiers/behavior, role inversion, assistant echo,
  hidden-fact leakage, privacy violation, retry, repair, or fallback;
- observed and expanded denominators reported separately.

Missing owner rulings keep completion and LABS-06 passage unpassed.

## 9. Non-goals

No general world builder, mutable sandbox framework, persistent/global or
emotion memory, judge, model/prompt tournament, baseline/candidate diff,
generic SDK, UI, hosted execution, automatic fixture synthesis, database
mutation, target repair, broad eval import, retry, repair, or fallback.

No source is copied from Agentagon or another repository. Existing permitted
HRAI data access is evidence input, not an implementation source.

## 10. Change budget and ownership

Independent test author may edit only:

- `triana-labs/tests/case_factory_acceptance/**`
- `triana-labs/tests/adaptive_runner_acceptance/**`
- new purpose-built synthetic fixtures under those directories

Budget: at most eight new/changed black-box functions, 48 collected cases,
and 700 changed/new physical test lines. Mechanical existing artifact-name or
fixture-shape updates count toward lines but not functions. The frozen
`tests/simulator_fidelity_acceptance/**` bytes are untouched.

Implementation author may edit only:

- `triana-labs/src/triana_labs/case_factory/evidence.py`
- `triana-labs/src/triana_labs/case_factory/generate.py` (public restricted
  wrapper forwarding the frozen inventory path only)
- `triana-labs/src/triana_labs/case_factory/schemas/proposal.schema.json`
- `triana-labs/src/triana_labs/case_factory/semantic.py`
- `triana-labs/src/triana_labs/case_factory/restricted_runtime.py`
- `triana-labs/src/triana_labs/cli.py`
- `triana-labs/src/triana_labs/adaptive_runner/boundaries.py`
- `triana-labs/src/triana_labs/adaptive_runner/runner.py`

Budget: at most 850 changed/new physical production lines. No dependency is
allowed. `contracts.py`, `simulator_fidelity.py`, connectors, core, UI, report
system, and external repositories are explicitly untouched. Workers stop
before expanding this budget.

Orchestrator owns this packet, canonical docs, decision memory, verifier hash
literals, private run configuration/evidence outside the repository, and
final verification. Pre-existing untracked user files remain untouched.

## 11. Verification

Focused RED/GREEN:

```bash
cd triana-labs
uv run pytest tests/case_factory_acceptance tests/adaptive_runner_acceptance -q
```

Preserved frozen LABS-06:

```bash
cd triana-labs
uv run pytest tests/simulator_fidelity_acceptance -q
```

Static and complete:

```bash
cd triana-labs
uv run ruff check src tests/case_factory_acceptance tests/adaptive_runner_acceptance
uv run ruff format --check src tests/case_factory_acceptance tests/adaptive_runner_acceptance
uv run mypy src/triana_labs
./scripts/verify.sh
```

No command above authorizes RDS, provider, HRAI, target, or real-data episode
execution.

## 12. Uncertainty handoff

Every worker reports changed files and necessity, budget reconciliation,
exact commands/results/artifacts, unverified work, assumptions, unexpected
findings, dependencies, deliberately excluded problems, known risks, and
human action required, using `none` explicitly.

The incident remains open after local GREEN. The orchestrator may perform the
owner-authorized read-only RDS inventory/export only after validating the
exact command cannot mutate data. Simulator-only and end-to-end calls remain
separate explicit egress approvals.

## 13. Independent RED freeze

The independent test author added exactly two test-owned files:

```text
tests/case_factory_acceptance/test_grounded_workflow_closure.py
  sha256 2af87a94cb41803130cbeb31ca4e67857ca438b1cf0578587801e9514f84761c
tests/adaptive_runner_acceptance/test_workflow_closure_execution.py
  sha256 8428d3971a4690bbac73a77bf42b3e5c2f6099cb866652b56d85cd3aecb8da8e
```

The frozen set is six black-box functions, nine collected cases, and 549 new
physical lines, within the 8/48/700 budget. Codex independently reproduced
nine clean RED failures, all at the absent public
`generate_restricted(..., world_inventory=...)` or
`run(..., world_inventory=...)` behavior after one pre-freeze temporary-path
setup defect was corrected. There are no syntax, import, collection, or setup
failures.

Independent controls passed: four LABS-04 success/legacy restricted cases,
four adaptive success cases, and all 43 frozen LABS-06 fidelity cases. Ruff and
format checks are GREEN. Frozen `simulator_fidelity_acceptance` hashes remain
unchanged. These two files are now frozen; the implementation author may read
but must not edit them.

Post-freeze audit correction: Codex found that one assertion assumed provider
submission order even though canonical publication sorts by hashed `case_id`.
The test author changed only that assertion to require six one-trace and six
two-trace cases independent of order, reproduced the same nine-failure RED,
and superseded only the case-test hash above. Meaning and every budget remain
unchanged.

A second audit found the fixture used each five-wide batch's local enumeration
to choose one versus two trace handles, making every slot appear single-trace.
The test author corrected only fixture construction to use the global
`case_N` ordinal, retained the established 5/5/2 production batching, and
proved exact 6/6 origins. Candidate state after that correction is six
case-factory passes plus three expected missing runner-inventory failures.
The final case-test hash above supersedes both earlier hashes.

## 14. Local completion and live boundary

The independent implementation author changed only the eight authorized
production paths. Relative to the packet's post-LABS-06 baseline, the closure
delta is 806 added production lines, within the 850-line ceiling. The two
frozen acceptance files retain the hashes recorded above.

Local verification is GREEN: 9/9 closure acceptance cases, 43/43 preserved
LABS-06 cases, Ruff, formatting, strict mypy, and the complete 603-test,
build, clean-wheel, frozen-hash, and artifact verifier at
`/private/tmp/triana-labs-verify.eLaFCb`. The full gate initially exposed a
shared proposal-schema compatibility regression; the static legacy schema was
restored byte-for-byte and the three closure fields now exist only in the
dynamic closure schema. The final full gate is clean.

The local artifacts are synthetic acceptance evidence, not production
results. No RDS, provider, HRAI, target, or real-data execution occurred. Both
closure world-inventory validators currently admit only `SYNTHETIC`, while
the existing Observer/Corpus Intelligence trace contracts also reject real
privacy classes. Therefore an honest owner-authorized production-trace run
cannot be assembled by relabeling RDS data under this packet. It requires a
new bounded real-data contract slice, exact read-only export path and custody,
then a separate pre-egress bundle/endpoint/cost approval before any provider
or target call.
