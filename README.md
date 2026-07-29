# Triana

Triana turns an approved production failure into a repeatable release check,
runs that check against an approved baseline and a candidate inside the
customer's CI, and produces an advisory release recommendation with permanent
evidence.

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

## The V1 loop

```text
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
        ↓
approved baseline and PR candidate run in customer CI
        ↓
deterministic evidence + customer-owned evaluator results
        ↓
advisory PASS / REVIEW / BLOCK + Release Evidence Record
```

The first value moment is not a trace dashboard. It is:

> This approved production failure passed 10/10 on the approved baseline and
> 6/10 on this PR. Recommendation: BLOCK. Here are the failed executions and
> exact evidence.

## Repository status

No production implementation exists yet. The first build target is M0: one
public reference agent, three protected cases, an A/A control, a planted A/B
regression, reproducible records, and a static evidence page. Triana itself
remains closed-source.

No open-source license is granted.
