# Triana

Triana produces a Release Review for an AI agent change. It binds the exact
baseline-to-candidate change to one human-approved Release Obligation, combines
its production-derived Protected Case with available customer-owned eval
results, applies a customer-approved Release Policy, and presents an advisory
recommendation with permanent evidence.

Production issue discovery is the acquisition path. Production replay is one
check mechanism. The human-facing product is the Release Review. The human,
not Triana, makes the Release Decision.

This is a clean-room repository. It has no Agentagon source code, Git history,
tests, fixtures, prompts, schemas, or generated artifacts. Product context was
rewritten from decisions authorized by Akarsh. Future implementation may reuse
code from Akarsh's Kairos repositories only through the provenance process in
[`docs/PROVENANCE.md`](docs/PROVENANCE.md).

## Read this first

1. [`docs/PRODUCT.md`](docs/PRODUCT.md) — the frozen self-serve V1.
2. [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — execution and trust
   boundaries.
3. [`docs/FOUNDER_CONTEXT.md`](docs/FOUNDER_CONTEXT.md) — why this wedge,
   competitive objection, and unresolved risks.
4. [`internal/WORKING_MEMORY.md`](internal/WORKING_MEMORY.md) — current
   hypotheses, proof plan, and immediate work.
5. [`docs/PROVENANCE.md`](docs/PROVENANCE.md) — what may and may not enter this
   repository.
6. [`internal/DECISION_LOG.md`](internal/DECISION_LOG.md) — append-only accepted
   decisions.
7. [`docs/ENGINEERING.md`](docs/ENGINEERING.md) — shared implementation,
   verification, decision-memory, Git, and review policy.
8. [`CONTRIBUTING.md`](CONTRIBUTING.md) — contributor setup and daily workflow.
9. [`internal/SLICE_PACKET.md`](internal/SLICE_PACKET.md) — the live,
   role-separated contract for the current implementation slice.

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

## The V1 loop

```text
FREE ACQUISITION

read-only traces or local trace export
        ↓
mechanically suspicious trace candidates
        ↓
human selects one known production incident
        ↓
Triana proposes an exact protected case
        ↓
human edits, approves, and promotes it
        ↓
qualification proves it is replayable and measurable

RECURRING RELEASE REVIEW

declared Release Change + human-approved Release Obligation
        ↓
approved Protected Case + optional customer eval command
        ↓
approved baseline and PR candidate run in customer CI
        ↓
required and received deterministic + customer-owned evidence
        ↓
immutable Release Evidence Record
        ↓
Release Policy → advisory PASS / REVIEW / BLOCK
        ↓
Release Review in the PR and on a permanent page
        ↓
human approves, holds, or records an exception
        ↓
append-only Decision Attestation links the human outcome
```

The first recurring value moment is not a trace dashboard or another eval
score. It is:

> This approved production failure passed 10/10 on the approved baseline and
> 6/10 on this PR. Recommendation: BLOCK. Here are the failed executions and
> exact evidence. The release owner can now approve, hold, or document an
> exception.

## Repository status

No production implementation exists yet. The first build target is a
record-first vertical kernel: versioned contracts and verification, honest A/A
and planted A/B comparison with policy, then one usable Release Review page by
the third slice. Real trace ingestion and paired customer execution replace
the fixture boundaries after the record and UI are inspectable. This grows
into M0: one public reference agent, three protected cases, reproducible
records, and a static evidence page. Triana itself remains closed-source.

No open-source license is granted.
