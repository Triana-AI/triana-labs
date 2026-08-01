# Triana agent architecture

Status: current LABS-04 launch design and parked post-LABS-04 direction.

This document separates the agent needed now from the agentic simulation
system Triana may earn later. The current implementation contract remains
`internal/LABS04_GROUNDING_HANDLE_CONTRACT.md`.

## Current: restricted LangChain Case Factory

```text
verified synthetic traces
          |
          v
deterministic evidence/catalog builder
  - redact and allowlist
  - create run-local evidence handles
  - preserve canonical provenance privately
          |
          v
restricted create_agent graph (pinned GLM-5.2)
  - grounding-researcher instructions
  - case-architect instructions
  - conditional deterministic repair invocation
  - four allowlisted tools only
          |
          v
deterministic guardrail
  - resolve handles and derive portable IDs/support
  - validate references, privacy, diversity, bounds, budget
          |
     valid|       |invalid
          |       v
          |  Repair Agent (same pinned model, at most once per batch)
          |       |
          +-------+
          |
          v
preserved bundle + human usefulness review
```

LangChain `create_agent`, backed by LangGraph, owns the bounded model/tool loop
and strict terminal response. It receives exactly four Triana tools and adds no
coding, shell, web, filesystem, todo, memory, or delegation tools. Triana's
deterministic controller remains outside the framework and owns batching,
repair invocation, questions, budgets, transitions, and acceptance.

The ordinary harness functions are the present tools:

- `build_evidence_catalog`: co-locate allowed event content and short handles;
- `validate_case_batch`: return all typed RFC 6901 defects in one pass;
- `inspect_budget`: calculate reservation before every provider call;
- `resolve_and_publish`: map handles to canonical citations and atomically
  preserve requests, responses, intermediates, failures, cost, and lineage.

`search_evidence`, `get_trace_packet`, `inspect_budget`, and
`submit_case_batch` are the only model-callable tools. Catalog construction,
canonical resolution, publication, and final validation remain application
functions the model cannot invoke or override.

Run memory is the immutable evidence catalog, generated draft, normalized
intermediate representation, defects, attempts, cost ledger, and final bundle.
Exact-response and intermediate-representation caching reuses identical work.
The model cannot write durable memory.

Case quantity is requested rather than hard-coded: 1--25, default 10, emitted
in deterministic batches of at most five. Each batch has one generation call
and at most one repair call. The harness stops with typed partial evidence when
budget cannot fund the next complete call; it does not silently shrink the
request, change models, or retry to green. The launch smoke requests 10 and
requires at least seven distinct grounded reviewable cases.

The current provider is Fireworks GLM-5.2 through Microsoft Foundry, selected
only after a live tool/structured-output conformance probe. The synthetic-only
provider-named egress and USD 3 experiment ceiling are explicit. There is no
runtime model router or fallback. DeepSeek-V4-Flash remains a later comparison,
not a fallback inside this run.

## Future: agentic simulation system

This direction is parked until grounded designs are useful and target-agent
execution begins.

```text
                    deterministic run controller
             budget / state / provenance / termination
                              |
      +-----------------------+-----------------------+
      |                       |                       |
      v                       v                       v
Grounding Researcher     Case Architect       Evaluation Supervisor
search/retrieve tools    personas/intents     judges and human rulings
      |                  world + policies              |
      +-----------> shared typed run memory <----------+
                              |
                              v
                  Multi-turn User Simulator
             observes target-agent response/tool event
                 chooses next turn from turn policy
                              |
                              v
                      customer target agent
                              |
                              v
                 deterministic trace and outcome log
                              |
                              v
                     promotion review gate
                              |
              approved eval failures/rulings only
                              |
                              v
                  versioned learning memory
```

Future model-callable tools are narrow and read-oriented:
`search_evidence`, `get_trace_packet`, `inspect_world_state`,
`inspect_budget`, and `submit_candidate`. A model never directly writes an
artifact, changes a ruling, mutates global memory, calculates a denominator,
or decides that its own output passed.

Future memory has three distinct scopes:

1. Evidence memory: immutable local source packets for one corpus.
2. Run memory: typed events and intermediate state for one simulation.
3. Learning memory: versioned human-approved rulings, failure fixtures,
   grader examples, and measured model/prompt performance across runs.

Promotion into learning memory requires deterministic lineage plus human or
accepted-eval authority. Raw model reflection never compounds automatically.

## Agent SDK boundary

LangChain `create_agent` plus LangGraph is the current restricted runtime.
DeepAgents 0.6.12 was evaluated and deliberately not used in LABS-04: its
filesystem, todo, execution, summarization, and `task` scaffolding must be
excluded to recover the exact-four tool surface, while enabling its dynamic
subagents necessarily adds `task` as a fifth tool. That complexity supplies no
current capability because Triana deterministically owns batching and repair.

DeepAgents remains the leading future candidate when target-agent simulation
actually requires runtime delegation, long-lived sessions, and governed
memory. Re-evaluate it on the same conformance suite rather than inheriting it
from this checkpoint.

The following remain the reasons for using an agent runtime rather than
building one:

- dynamic model tool-call loops rather than fixed application calls;
- target-agent/user-simulator turns persisted across a long-lived session;
- two or more runtime specialist handoffs with shared typed state;
- standardized tool approvals, cancellation, and resumable execution;
- provider-independent trace export that materially reduces our own code;
- concurrent simulations whose lifecycle is difficult to express in the
  deterministic controller.

Before any later framework expansion, compare it on the same conformance suite.
It must preserve multi-provider access,
deterministic authority, local evidence custody, exact replay, cost accounting,
and typed failure artifacts. Framework convenience is not sufficient evidence.

## Explicitly out of the current checkpoint

No target-agent execution, online turn generator, model judge, autonomous
memory curator, runtime routing/fallback, hosted ingestion, real-data support,
or generic skill registry is part of LABS-04.
