# Triana agent instructions

## Start-of-task reading

Before changing product direction, architecture, implementation policy,
evaluation interpretation, repository boundaries, or go-to-market claims,
read:

1. `docs/PRODUCT.md`
2. `docs/ARCHITECTURE.md`
3. `internal/WORKING_MEMORY.md`
4. `docs/PROVENANCE.md`
5. `internal/DECISION_LOG.md`

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

## Before implementation

Every implementation slice must identify:

- the V1 product outcome it advances;
- the input and output contract;
- deterministic versus LLM versus human authority;
- privacy and execution location;
- gaps and refusal behavior;
- provenance of any reused code;
- a reproducible acceptance test.
