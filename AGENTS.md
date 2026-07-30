# Triana agent instructions

This file is the shared operating contract for every coding agent, including
Codex and Claude Code. `CLAUDE.md` points here so the two tools do not develop
different rules. A task is not complete if its code is correct but its
decisions, evidence, provenance, or canonical documentation are stale.

## Authority and ground truth

Use repository evidence, not chat memory, as ground truth. Read conflicts in
this order:

1. `docs/PRODUCT.md` — frozen product scope and claims.
2. `docs/ARCHITECTURE.md` — authority, execution, privacy, and refusal
   boundaries.
3. `internal/DECISION_LOG.md` — append-only accepted decisions. A later entry
   supersedes an earlier entry only when it says so explicitly.
4. `docs/ENGINEERING.md` — implementation, verification, Git, and review
   policy.
5. `internal/WORKING_MEMORY.md` — active hypotheses, questions, and work queue;
   useful context, not accepted truth.

If a durable decision changes a canonical document, update both the decision
log and that document in the same change. Chat, tickets, customer requests,
and generated plans do not override the repository.

## Start-of-task reading

Before changing product direction, architecture, implementation policy,
evaluation interpretation, repository boundaries, or go-to-market claims,
read:

1. `docs/PRODUCT.md`
2. `docs/ARCHITECTURE.md`
3. `docs/CONTRACTS.md`
4. `internal/WORKING_MEMORY.md`
5. `docs/PROVENANCE.md`
6. `internal/DECISION_LOG.md`

The frozen V1 is a constraint, not a brainstorm. Discussion and customer
requests do not change it. A successor decision requires observed evidence and
an explicit decision-log entry.

## Clean-room rule

Do not copy, translate, port, or derive implementation from the Agentagon
repository. This includes source, tests, prompts, schemas, fixtures, UI, CSS,
configuration, generated artifacts, and Git history.

The Agentagon reset history does not establish file-level ownership. A commit
authored by Akarsh is therefore not sufficient proof that a file is eligible.

Kairos and Kairos-AI are permitted source-mining repositories because Akarsh
explicitly authorized their reuse. Before copying from either:

1. identify the exact source file and commit;
2. explain the capability being reused;
3. record the destination and whether the code was copied or reimplemented in
   `docs/PROVENANCE.md`;
4. preserve any applicable third-party license or attribution;
5. verify that the source does not itself contain an Agentagon-derived port.

Facts, accepted product decisions, and customer insights owned by Akarsh may be
rewritten here. Do not copy Agentagon prose wholesale unless Akarsh explicitly
allowlists the exact file.

## Product invariants

- Human approval creates protected behavior; Triana never invents ground
  truth.
- The customer's agent and credentials run inside customer CI.
- An approved baseline is explicit. A merge base is not an approved baseline.
- Regression language requires comparable baseline and candidate executions.
- Missing or non-comparable evidence cannot become a pass.
- Evaluation gaps are reported separately from behavioral failures.
- Triana-owned deterministic assertions and customer-owned evaluators are
  distinct evidence lanes.
- PASS, REVIEW, and BLOCK are advisory recommendations in V1.
- The Release Evidence Record is immutable and uses the weakest claim supported
  by the evidence.
- Triana V1 is closed-source.

## LLM boundary

An LLM may propose a risk name, expected behavior, prohibited behavior, or
candidate assertions. A human must approve the protected case and policy.
Deterministic code owns case identity, qualification state, trial membership,
denominators, arithmetic, comparability, policy rendering, artifact identity,
and record chaining.

A customer-owned evaluator may use an LLM judge. Triana records its identity
and result but does not silently claim ownership of that judgment.

## Decision log

Append only accepted or autonomously executed decisions. Never rewrite prior
entries. Use:

```text
- What: <decision> | Why: <reason> | When: YYYY-MM-DD | Whom: <decision maker and executor>
```

Questions, alternatives, feature requests, and incomplete ideas belong in
`internal/WORKING_MEMORY.md`, not the decision log.

Decision discipline is mandatory:

- Read the full decision log before product, architecture, policy, or
  repository-boundary work.
- Record an accepted or autonomously executed durable decision in the same
  change that implements it.
- Append only. Corrections and reversals are new entries that identify what
  they supersede; history is never rewritten.
- Capture raw per-commit intent in the gitignored
  `.decision-memory/<YYYY-MM-DD>-<branch>.md` journal. Promote only durable
  decisions from that journal to `internal/DECISION_LOG.md`.
- Never use the decision log as a backlog, status report, or transcript.

## Before implementation

Every implementation slice must identify:

- the V1 product outcome it advances;
- the input and output contract;
- deterministic versus LLM versus human authority;
- privacy and execution location;
- gaps and refusal behavior;
- provenance of any reused code;
- a reproducible acceptance test.

An explicit user request authorizes implementation within its stated scope.
Stop for confirmation only when a material product/architecture choice,
destructive action, external side effect, or unresolved ambiguity would expand
that scope.

## Engineering and delivery

Read `docs/ENGINEERING.md` before implementation. In particular:

- execute each implementation slice through the independent orchestrator,
  test-author, and implementation-author protocol; do not let one agent write
  the acceptance contract, production behavior, and final verdict;
- keep each change small, reviewable, and reversible;
- write tests with the behavior they protect;
- fail visibly and represent unknown, missing, skipped, or non-comparable
  evidence as typed states rather than passes;
- inspect the worktree before editing and preserve unrelated user changes;
- use Conventional Commits and explain why in the commit body;
- run the repository verification gate before commit and push;
- never push directly to `main`, force-push, bypass hooks, or commit secrets;
- update canonical docs and the decision record before declaring completion.

Install the versioned hooks once per clone with
`./scripts/install-git-hooks.sh`. They enforce append-only decisions,
Conventional Commits, local decision memory, and protected-branch push rules.

The live contract for the current slice is `internal/SLICE_PACKET.md`. No
worker agent starts until the orchestrator completes its entry gate. Because
agents share a worktree by default, test and implementation handoffs are
serial. True parallel edits require isolated worktrees.
