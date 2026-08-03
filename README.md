# Triana

Triana Labs Preview is the active build surface. Its immediate launch cut takes
authorized conversational traces, derives grounded proposed user behaviors,
builds distinct adaptive multi-turn simulation cases, runs them against one
existing conversational/tool agent, and returns inspectable transcripts,
coverage, cost, fidelity, and gaps. It does not yet compare baseline and
candidate or decide whether to ship.

Preview is CLI-first: a coding agent can perform the repository setup, while
the human reviews a generated local HTML report backed by machine-readable
evidence. Initial user acquisition is a bounded five-team design-partner
cohort, not a hosted account or trace-upload product.

The active product and package namespace are Triana Labs and `triana_labs`;
the user-facing command is `triana`. Triana Release Review is the suspended
proprietary product line, while `triana-core` remains its frozen shared
integrity kernel pending an explicit public-distribution boundary decision.

The prior Release Review V1 is suspended, not deleted. Its implemented
deterministic contract kernel remains shared infrastructure in `triana-core/`.

This is a clean-room repository. It has no Agentagon source code, Git history,
tests, fixtures, prompts, schemas, or generated artifacts. Product context was
rewritten from decisions authorized by Akarsh. Future implementation may reuse
code from Akarsh's Kairos repositories only through the provenance process in
[`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Read this first

1. [`triana-labs/CHARTER.md`](triana-labs/CHARTER.md) — active Labs product
   authority.
2. [`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`](internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md)
   — canonical execution plan, deliverables, edge cases, gates, and exits.
3. [`internal/DECISION_LOG.md`](internal/DECISION_LOG.md) — append-only
   accepted decisions.
4. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — shared execution and trust
   boundaries.
5. [`docs/ENGINEERING.md`](docs/ENGINEERING.md) — shared implementation,
   verification, decision-memory, Git, and review policy.
6. [`internal/WORKING_MEMORY.md`](internal/WORKING_MEMORY.md) — active
   hypotheses, proof plan, and immediate work.
7. [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — what may and may not enter this
   repository.
8. [`docs/PRODUCT.md`](docs/PRODUCT.md) — the suspended self-serve V1.
9. [`docs/FOUNDER_CONTEXT.md`](docs/FOUNDER_CONTEXT.md) — historical wedge,
   competitive objection, and unresolved risks.
10. [`CONTRIBUTING.md`](CONTRIBUTING.md) — contributor setup and workflow.
11. [`internal/SLICE_PACKET.md`](internal/SLICE_PACKET.md) — closed LABS-04
    implementation packet and exact evidence history.
12. [`internal/LABS04_CASE_REVIEW_2026-08-02.md`](internal/LABS04_CASE_REVIEW_2026-08-02.md)
    — readable denominator, distinctness, case, and human-review companion.
13. [`internal/LABS05_HANDOFF_2026-08-02.md`](internal/LABS05_HANDOFF_2026-08-02.md)
    — current restart context, LABS-05 decisions, backlog, and copyable prompt.
14. [`internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md`](internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md)
    — post-LABS-05 public rollout, Labs demo UI sequence, blockers, and deferred
    register.

Working product instruments:

- [`internal/DISCOVERY_ASK_GUIDE.md`](internal/DISCOVERY_ASK_GUIDE.md) —
  artifact-first customer interview and quantitative capture guide.
- [`internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md`](internal/examples/HIRING_AGENT_MODEL_UPGRADE_RELEASE_REVIEW.md)
  — synthetic end-to-end Release Review example.
- [`internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md`](internal/FUTURE_RELEASE_CONTROL_CONSIDERATIONS.md)
  — gated post-V1 direction and entry criteria.

Both Codex and Claude Code use the same operating contract:
[`AGENTS.md`](AGENTS.md). Claude Code enters through [`CLAUDE.md`](CLAUDE.md),
which points to that shared source instead of duplicating rules.

## The active Labs loop

```text
authorized conversational traces
        ↓
versioned PreviewTrace adaptation, observation, and structural intelligence
        ↓
grounded proposed personas, intents, adaptive turn policies, and distinct cases
        ↓
one existing conversational/tool agent through a bounded runner
        ↓
genuinely adaptive multi-turn simulated-user conversations
        ↓
inspectable transcripts, evaluation evidence, cost, fidelity, and gaps
        ↓
human-reviewed local evidence may inform a later run
```

The immediate first value moment is:

> Here are several trace-grounded, genuinely adaptive situations your agent
> was tested on, the complete conversations, what the evidence covers, what it
> cost, and what Triana could not support. A human decides what is useful.

## Repository status

The shared Slice 0A deterministic kernel is implemented in `triana-core/`.
Triana Labs has a synthetic-only local path through reference transformation,
Trace Observer, structural Corpus Intelligence, Grounded Case Factory, and the
Adaptive Multi-Turn Runner. LABS-04 produced five valid distinct grounded cases
and passed owner usefulness review. LABS-05's one private real-target canary
produced two valid distinct trajectories and one partial trajectory; owner
adaptation rulings were Y/N/Y/Y, so the checkpoint closed honestly as unpassed.
The local implementation and target connectors remain supported, while the
next blocker is regular-user simulator fidelity. Labs still does not generally
accept real/local-sensitive traces, compare releases, create persistent
memory, or render a public HTML report.

`triana cases generate` now dispatches explicitly from the config artifact
kind: the secret-free restricted example selects the pinned GLM-5.2 path while
existing legacy configs retain the older path. `triana cases resume` continues
an immutable restricted pause from exact config bytes and owner answers. This
remains synthetic-only CLI productization, not general real-data support. The
post-LABS-05 public path is fidelity repair, report contract, Labs demo UI,
one-command public demo, and then stranger installation.

Labs is intended for open-source distribution only after provenance, privacy,
egress, and license gates pass. No open-source license is granted yet.

## Run the local synthetic pipeline

The current command accepts only traces explicitly labeled `SYNTHETIC`:

```bash
cd triana-labs
uv sync --locked --all-groups
uv run --locked triana traces observe \
  tests/fixtures/valid_all_events.jsonl \
  --out /private/tmp/triana-observed
```

The new output directory contains:

```text
manifest.json
normalized_traces.jsonl
rejected_traces.jsonl
corpus_profile.json
corpus_profile.md
```

An external adapter currently interacts through files, not a Python SDK:

```text
provider- or application-specific trace
  -> customer/integration adapter
  -> one PreviewTrace JSON object per physical JSONL line
  -> triana traces observe
  -> deterministic Observer artifacts
```

The adapter does not call `contracts/traces.py`; that module is Triana's
internal per-line validation boundary. A general adapter package, OTel mapping,
and real/local-sensitive trace path do not exist yet.

LABS-02 includes one deliberately narrow reference transform for newly authored
synthetic HRAI `normalized-trace-v2` JSONL:

```bash
python examples/hrai_v2/adapter.py synthetic-hrai-v2.jsonl \
  --out /private/tmp/triana-adapted \
  --data-class SYNTHETIC
uv run --locked triana traces observe \
  /private/tmp/triana-adapted/preview_traces.jsonl \
  --out /private/tmp/triana-observed
```

The script is a copyable example, not an HRAI integration or supported adapter
API. It refuses real/local-sensitive data by contract, performs no redaction or
network access, and emits safe per-line rejections separately from accepted
PreviewTrace JSONL.

Derive the first inspectable structural intelligence bundle from the Observer
manifest:

```bash
uv run --locked triana corpus derive \
  /private/tmp/triana-observed/manifest.json \
  --out /private/tmp/triana-intelligence
```

Exit 10 is expected: structural clusters are complete, while persona, intent,
turn-policy, language, and distress semantics are explicitly not derived. The
output contains `manifest.json`, `clusters.json`, `derivation_report.json`, and
the three typed asset indexes under `personas/`, `intents/`, and
`turn_policies/`.

Generate five grounded proposals through the pinned restricted runtime after
setting the two operator-owned environment variables named by the example:

```bash
uv run --locked triana cases generate \
  /private/tmp/triana-observed/manifest.json \
  --intelligence /private/tmp/triana-intelligence/manifest.json \
  --config examples/restricted-case-factory-config.json \
  --cache-dir /private/tmp/triana-case-cache \
  --out /private/tmp/triana-cases
```

If the command exits 11 with `NEEDS_INPUT`, answer every emitted question in
one strict JSON object and resume into a new directory with the same config and
private cache:

```bash
uv run --locked triana cases resume \
  /private/tmp/triana-cases/manifest.json \
  --answers /path/to/answers.json \
  --config examples/restricted-case-factory-config.json \
  --cache-dir /private/tmp/triana-case-cache \
  --out /private/tmp/triana-cases-resumed
```

Use `./scripts/verify.sh` from `triana-labs/` to run governance, frozen-test
integrity, formatting, lint, strict typing, all tests, deterministic
repeatability, package builds, a clean CPython 3.13.14 wheel install, and
installed-command parity.
