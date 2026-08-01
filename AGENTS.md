# Triana agent instructions

This file is the shared operating contract for every coding agent, including
Codex and Claude Code. `CLAUDE.md` points here so the two tools do not develop
different rules. A task is not complete if its code is correct but its
decisions, evidence, provenance, or canonical documentation are stale.

## Authority and ground truth

Use repository evidence, not chat memory, as ground truth. Read conflicts in
the following product-specific order.

For Triana Labs work:

1. `triana-labs/CHARTER.md` — active Labs product authority.
2. `internal/DECISION_LOG.md` — append-only accepted decisions. A later entry
   supersedes an earlier entry only when it says so explicitly.
3. The current Labs plan named by the charter — accepted implementation and
   milestone detail.

For the suspended Release Review V1, `docs/PRODUCT.md` remains its frozen
product scope and claims. Across both product lines, `docs/ARCHITECTURE.md`,
`docs/CONTRACTS.md`, `docs/ENGINEERING.md`, and `docs/PROVENANCE.md` remain
authoritative wherever the active product authority has not explicitly
superseded them. `internal/WORKING_MEMORY.md` holds active hypotheses,
questions, and work queues; it is useful context, not accepted truth.

If a durable decision changes a canonical document, update both the decision
log and that document in the same change. Chat, tickets, customer requests,
and generated plans do not override the repository.

## Start-of-task reading

Before changing product direction, architecture, implementation policy,
evaluation interpretation, repository boundaries, or go-to-market claims,
read:

1. `triana-labs/CHARTER.md`
2. the current Labs plan named by the charter
3. `docs/PRODUCT.md`
4. `docs/ARCHITECTURE.md`
5. `docs/CONTRACTS.md`
6. `internal/WORKING_MEMORY.md`
7. `docs/PROVENANCE.md`
8. the full `internal/DECISION_LOG.md`

Triana Labs Preview is the active build surface. The frozen Release Review V1
is suspended, not erased, and its contracts in `triana-core/` remain
unchanged. Discussion and customer requests do not change either boundary. A
successor or merger decision requires observed evidence and an explicit
decision-log entry.

## Clean-room rule

Agentagon is restricted by default: do not copy, translate, port, or derive
implementation from it unless `docs/PROVENANCE.md` explicitly allowlists the
exact source surface. The current narrow exception is the Agentagon
`Triana demo` UI package; the rest of Agentagon remains restricted.

The Agentagon reset history does not establish file-level ownership. A commit
authored by Akarsh is therefore not sufficient proof that a file is eligible.

Kairos, Kairos-AI, and HRAI are permitted source-mining repositories because
Akarsh explicitly authorized their reuse. `docs/PROVENANCE.md` is the live
authority for exact exceptions, dataset permissions, and restrictions. Before
copying from any permitted source:

1. identify the exact source file and commit;
2. explain the capability being reused;
3. record the destination and whether the code was copied or reimplemented in
   `docs/PROVENANCE.md`;
4. preserve any applicable third-party license or attribution;
5. verify that the source does not itself contain an Agentagon-derived port.

Facts, accepted product decisions, and customer insights owned by Akarsh may
be rewritten here. Blitz data is design-partner evidence governed by the
provenance ledger, not a general implementation allowlist. Do not copy
Agentagon prose or code beyond an exact recorded exception.

## Product invariants

For active Triana Labs Preview:

- The baseline is reference behavior, not ground truth. Only explicit
  acceptance evidence or a human ruling marks it accepted.
- Human confirmation creates persistent rulings; Triana does not invent
  accepted behavior, known failure, or release truth.
- Baseline and candidate receive the same historical prefix in F0 and execute
  freshly. F1 simulated continuation is labeled separately.
- Missing, invalid, unstable, or non-comparable evidence cannot become a
  finding or pass; lower-confidence observations remain visible as typed
  partial evidence.
- Deterministic code owns case identity, trial pairing, denominators,
  comparability, stability arithmetic, fidelity labels, and report lineage.
- Customer traces remain local except for explicitly authorized,
  provider-named egress under customer or operator keys. Redaction and egress
  validation run before hashing and before provider calls.
- Labs may be open source only after provenance, privacy, and egress gates
  pass.

For the suspended Release Review V1:

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

For Labs, an LLM may derive candidate personas, intents, turn policies, user
turns, and finding explanations from authorized evidence. It may propose
signals and rulings. It cannot own identity, pairing, denominators,
comparability, stability, fidelity, or a persistent ruling; deterministic code
owns the former and a human confirms the latter.

For the suspended V1, an LLM may propose a risk name, expected behavior,
prohibited behavior, or candidate assertions. A human must approve the
protected case and policy. Deterministic code owns case identity,
qualification state, trial membership, denominators, arithmetic,
comparability, policy rendering, artifact identity, and record chaining.

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

- the active product outcome it advances (Labs charter, or frozen V1 only
  after an explicit resumption decision);
- the input and output contract;
- deterministic versus LLM versus human authority;
- privacy and execution location;
- gaps and refusal behavior;
- provenance of any reused code;
- a reproducible acceptance test.
- a change budget covering expected files and bounded paths, test and
  production ownership, explicitly untouched areas, dependency allowance, and
  maximum scope expansion.

Workers stop before editing outside the change budget. At exit, the
orchestrator reconciles the actual diff against it and rejects unexplained
files, dependencies, cleanup, or formatting.

Debugging uses one falsifiable hypothesis per iteration: record the observed
failure, smallest reproduction, hypothesis, falsifying evidence, one attempted
change, result, and resulting regression test or fixture. A falsified
speculative change is removed or isolated before the next hypothesis. Do not
bundle unrelated fixes or hide an unexplained state with a guard, retry,
default, broader exception, or weakened assertion.

Every worker and orchestrator returns a structured uncertainty handoff:
what changed; why each file was necessary; change-budget reconciliation; exact
verification and artifacts; unverified work; assumptions; unexpected
findings; dependencies; deliberately excluded problems; known risks; and any
human action required. Use `none` explicitly and never report an unrun check as
passing.

An explicit user request authorizes implementation within its stated scope.
Stop for confirmation only when a material product/architecture choice,
destructive action, external side effect, or unresolved ambiguity would expand
that scope.

## Authenticated consoles and UI automation

Do not use Playwright, browser control, computer-use tooling, or other UI
automation for a flow that requires authentication or operates inside an
authenticated cloud/provider console. If an already-authenticated CLI cannot
perform the required operation because login, authorization, role assignment,
marketplace acceptance, or console-only configuration is required, stop the UI
path and give Akarsh the exact minimal manual steps to perform. Resume only
after Akarsh confirms completion.

Prefer an existing authenticated AWS, Azure, or provider CLI for authorized
non-interactive operations. Never enter, request through an automated browser,
or interact with passwords, OTPs, security keys, consent screens, or account
selectors. Public unauthenticated documentation browsing remains allowed.

## Engineering and delivery

Read `docs/ENGINEERING.md` before implementation. In particular:

- execute each implementation slice through the independent orchestrator,
  test-author, and implementation-author protocol; do not let one agent write
  the acceptance contract, production behavior, and final verdict;
- freeze and reconcile the slice change budget, use the single-hypothesis
  debugging loop, and require the structured uncertainty handoff;
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
