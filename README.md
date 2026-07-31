# Triana

Triana Labs Preview is the active build surface. It takes production-derived
traces, builds a grounded case panel, executes an explicit baseline and
candidate against the same historical prefixes, continues post-divergence
only through labeled simulation, and reports stable paired behavioral
differences and explicit gaps. It does not decide whether to ship.

Preview is CLI-first: a coding agent can perform the repository setup, while
the human reviews a generated local HTML report backed by machine-readable
evidence. Initial user acquisition is a bounded five-team design-partner
cohort, not a hosted account or trace-upload product.

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
11. [`internal/SLICE_PACKET.md`](internal/SLICE_PACKET.md) — historical Slice
    0A packet; it must be replaced before any Labs implementation worker starts.

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
production-derived traces
        ↓
redaction, authorization, and versioned PreviewTrace adaptation
        ↓
corpus-derived personas, intents, turn policies, and grounded case panel
        ↓
F0 shared-prefix baseline/candidate resampling with paired trials
        ↓
labeled F1 simulated continuation after divergence
        ↓
typed outcomes, pass^3 stability, comparability, and explicit gaps
        ↓
divergence-first report with paired transcripts and fidelity
        ↓
human confirms meaning; a later run may reuse that ruling after M3.5
```

The first value moment is:

> Baseline reliably did A and candidate reliably did B under the same
> historical prefix (pass^3 on both arms). Here is the first divergence, every
> paired transcript, the evidence fidelity, and every gap. A human decides
> what the difference means.

## Repository status

The shared Slice 0A deterministic kernel is implemented in `triana-core/`.
Triana Labs has an active charter and canonical execution plan but no Labs
implementation yet. The first implementation action is to replace the
historical `internal/SLICE_PACKET.md` with the exact M0A slice contract.

Labs is intended for open-source distribution only after provenance, privacy,
egress, and license gates pass. No open-source license is granted yet.
