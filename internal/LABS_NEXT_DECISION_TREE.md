# Triana Labs next-decision tree

Date: 2026-08-01  
Status: superseded discussion state; preserved for design history  
Authority remains: `triana-labs/CHARTER.md` → `internal/DECISION_LOG.md` →
`internal/TRIANA_LABS_PREVIEW_V1_PLAN_2026-07-31.md`.

This file prevents the current design discussion from becoming an accidental
backlog. It separates shipped evidence, the next decision, later gated work,
parked ideas, and explicit non-goals. An item moves from this tree into an
implementation slice only after the owner accepts it and the durable decision
is recorded through the repository protocol.

The 2026-08-01 decision-log entry accepting single-agent
`GENERATED_MULTI_TURN_SIMULATION` supersedes this tree's proposed next sequence.
The tree remains useful as a record of parked alternatives, but it is not the
current launch plan. After the LABS-04 close, the authoritative fresh-session
handoff and LABS-05 decision boundary are
`internal/LABS05_HANDOFF_2026-08-02.md`; do not promote a branch from this tree
without the new owner-approved slice packet.

## Decision legend

- **SHIPPED:** implemented and evidenced; do not reopen without contradictory
  evidence.
- **REQUIRED INVARIANT:** already accepted; every later mechanism must preserve
  it.
- **NEXT:** the only proposed implementation checkpoint.
- **GATED NEXT:** considered only after the named predecessor passes.
- **PARKED:** preserved for later reconsideration; no production work now.
- **REJECTED:** outside the current product or contrary to its authority map.

## Product tree

```text
Triana Labs Preview
│
├── 1. Evidence intake [SHIPPED]
│   ├── LABS-02 external file adapter
│   ├── PreviewTrace JSONL
│   ├── Trace Observer validation and profiling
│   └── synthetic-only boundary
│
├── 2. Corpus Intelligence
│   ├── structural clustering and lineage [SHIPPED: LABS-03]
│   └── semantic assets [NEXT]
│       ├── minimal provider privacy/egress/budget boundary
│       ├── persona, intent, and turn-policy proposal schemas
│       ├── supported/unsupported/duplicate/adversarial eval fixtures
│       ├── evidence citation and support validation
│       ├── one-call proposer versus bounded propose→critic→revise experiment
│       ├── blinded human review with a frozen rubric
│       └── output remains PROPOSED; no model-created truth
│
├── 3. Case Generator and Panel Builder [GATED NEXT: semantic assets pass]
│   ├── select coverage deterministically
│   ├── reserve unique batch slots atomically
│   ├── exact and near-duplicate rejection
│   ├── bounded distinct replacement generation
│   ├── effective-distinct-N and coverage arithmetic
│   └── typed partial panel when novelty or budget is exhausted
│
├── 4. F0 paired runner [GATED NEXT: panel is usable]
│   ├── one subprocess conversational/tool-agent protocol
│   ├── same historical prefix for baseline and candidate
│   ├── fresh execution and declared memory reset
│   ├── comparability and stability owned by deterministic code
│   └── reference behavior is not ground truth
│
├── 5. F1 next-turn simulation [GATED NEXT: F0 and panel pass]
│   ├── one-turn generator contract
│   ├── DeepEval conformance candidate
│   │   ├── compare against a minimal direct provider-call reference
│   │   ├── test policy compliance, grounding, diversity, isolation, cost
│   │   ├── test on scripted assistant probes and mutated SUTs
│   │   └── adopt, partially wrap, or reject from evidence
│   ├── episode-only memory
│   ├── hard call/token/USD/time/turn budget
│   ├── F1 fidelity label
│   └── typed refusal and partial trajectory
│
├── 6. Evidence and judges [GATED NEXT: observable runs exist]
│   ├── deterministic contract/lineage/comparability judge
│   ├── deterministic diversity judge
│   ├── context-specific rubric proposal
│   ├── one calibrated model judge with ABSTAIN
│   ├── positive/negative/ambiguous/missing-evidence calibration anchors
│   ├── human confirmation creates rulings
│   └── no generator or judge evaluates itself into truth
│
├── 7. Local report and onboarding [GATED NEXT: evidence engine passes]
│   ├── zero-key synthetic walkthrough with recorded-output labels
│   ├── bring-your-own-provider, named egress, and hard spend cap
│   ├── connect one subprocess conversational/tool agent
│   ├── divergence-first local report
│   └── M3.5 stranger: report within 90 minutes and adapter line budget
│
└── 8. Evaluated memory and continual learning
    ├── minimal primitive [DEFINE NOW; IMPLEMENT ONLY WHEN CONSUMED]
    │   ├── propose
    │   ├── promote through deterministic evidence or human ruling
    │   ├── retrieve from a pinned snapshot
    │   ├── supersede/revoke/delete
    │   └── attribution: record which memory affected which run
    ├── local confirmed-ruling recurrence [GATED: M3.5, canonical M4]
    └── global/managed memory [PARKED]
```

## Required invariants carried through every branch

- Deterministic code owns identity, support, lineage, pairing, denominators,
  comparability, stability, fidelity labels, diversity arithmetic, and budgets.
- An LLM may propose semantics, turns, rubrics, explanations, and memories; it
  does not create accepted behavior, a verdict, or a persistent ruling.
- Missing, invalid, unstable, duplicate, non-comparable, refused, or
  budget-exhausted evidence is visible as a typed state and never becomes a
  pass.
- Provider egress is named and authorized; redaction and egress validation run
  before hashing and provider calls.
- Customer traces remain local except for explicitly authorized provider-bound
  content under operator/customer keys.
- Every provider job has preflight estimation plus hard call, token, USD,
  wall-clock, retry, and output limits.
- Baseline and candidate receive the same F0 historical prefix and execute
  freshly; generated continuation is labeled F1.
- Independent runs do not silently count duplicate trajectories as distinct N.

## Immediate decision: DeepEval versus a Triana turn generator

### Current recommendation

**Do neither now.** Do not adopt DeepEval yet, and do not implement a custom
runtime turn generator yet.

The next product uncertainty is whether grounded semantic assets can be
derived at all. A runtime simulator cannot be judged usefully until personas,
intents, turn policies, and their evidence relationship exist. Choosing an
engine first would optimize plumbing before its inputs have passed.

When the F1 gate opens, DeepEval is the leading reusable-engine candidate, not
an accepted dependency. It receives a bounded conformance experiment against
a minimal direct provider-call reference. Triana owns the surrounding evidence
contract regardless of which engine wins.

### DeepEval adoption conditions

- It materially reduces conversation-loop and state-management code.
- It accepts Triana's frozen persona, intent, policy, prefix, and budget inputs.
- It permits memory isolation and baseline/candidate session separation.
- It preserves required tool and terminal evidence through normalization.
- It supports hard external budget enforcement and typed partial failure.
- Its generated turns meet predeclared policy-compliance, realism, grounding,
  diversity, stopping, latency, and cost thresholds.
- It exposes seeded SUT mutations at least as well as the minimal reference.
- A pinned version satisfies dependency, license, provenance, and maintenance
  review.

Failing the quality gates while passing orchestration may justify using only
its loop with Triana-owned templates. If extensive overrides eliminate the
maintenance saving, use the minimal direct-call implementation instead.

## Parked decision branches

The following ideas remain discoverable but are not next-slice scope:

```text
Memory
├── Mem0 or another managed backend
├── organization-wide semantic retrieval
├── globally promoted non-customer heuristics
├── cross-batch novelty memory
├── autonomous prompt optimization
└── model fine-tuning / weight updates

Agent classes
├── Codex / Claude Code adapters
├── filesystem and artifact mutation events
├── child-agent execution graphs
├── browser agents
├── voice/audio agents
├── persistent long-running agents
└── multi-agent systems

Judging
├── model ensembles or debate panels
├── fully automatic rubric promotion
├── global judge-learning memory
└── automated release verdicts

Infrastructure and product surface
├── real-customer trace path
├── hosted ingestion and storage
├── generic SDK or OTel surface
├── UI/dashboard
├── managed execution
└── universal provider/agent abstraction
```

Each parked branch needs a new observed failure or passed predecessor gate
before reconsideration. Being architecturally plausible is not sufficient.

## Explicitly rejected for the Preview

- Model output labeled deterministic or accepted truth.
- A generator defining its own coverage distribution or judging its own value.
- Silent memory carry-over across controlled trials.
- Automatic cross-customer memory sharing.
- Dynamic rubric changes during an evaluation run.
- Unbounded retries, spend, context, turns, or sub-agent calls.
- Duplicate cases counted toward the requested denominator.
- Brand-specific product logic presented as universal agent support.
- Building a generic eval platform, swarm framework, hosted control plane, or
  memory platform before the Labs evidence gates pass.

## Single next implementation candidate

Provisional name: **Semantic Asset Evaluation checkpoint**.

Success means the same verified synthetic evidence bundle produces proposed
persona, intent, and turn-policy assets that:

1. pass schema, citation, support, privacy, lineage, and budget gates;
2. clear a frozen blinded usefulness rubric;
3. stay within declared duplicate and invention budgets;
4. report provider refusals and insufficient support honestly; and
5. provide enough grounded structure to authorize the Case Generator/Panel
   Builder checkpoint.

Failure stops progression to panel generation and F1. It does not trigger a
larger agent harness, global memory system, or turn-generator rewrite.
