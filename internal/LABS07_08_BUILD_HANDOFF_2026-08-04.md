# LABS-07/08 build handoff and prompt memory

Date: 2026-08-04

Status: **ACCEPTED DESIGN HANDOFF; IMPLEMENTATION NOT YET FROZEN**

This file preserves the owner prompts, accepted decisions, unresolved gates,
and a copyable restart prompt for the combined report-and-UI vertical slice.
It exists so a fresh session does not rediscover terminology, invent product
surfaces, or start from an older LABS-07/LABS-08 split.

The exact accepted visual/product specification is
`internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md`. The dedicated
deferred fidelity/evaluation register is
`internal/LABS06_BACKLOG_2026-08-04.md`.

## Decision-driving owner prompts

The following is normalized only for punctuation and spelling. Its product
meaning must be retained.

### Full-journey correction

> Start setup by explaining what Triana does. Stop inventing trace-source
> integrations. The source right now is only a file; LangSmith, Langfuse, and
> others may come later. Because trace structures are not standardized, setup
> must show whether Triana can understand the traces. Assume the adapter
> mapping is available for now.
>
> Observe user behavior the same way as the earlier Kairos-AI or Agentagon
> work: potentially 100,000 traces are deterministically clustered, then the
> downstream objects derive from those clusters. If current Triana does not do
> this, keep it as backlog rather than pretending it exists.
>
> The case panel must explain observed-grounded and grounded-expanded cases in
> language intuitive to a person who does not know Triana's terminology. It
> must explain why every case exists.
>
> Run preflight must show cases, target, simulator identities, and world
> availability. Explain what world availability means. Run progress must show
> status one conversation at a time, and current-turn typed failure without
> pretending that the run ended successfully.
>
> The result must show exactly what Triana learned from the traces, what
> situations it created, what happened when those situations ran, and what
> needs the human's judgment. Clarify exactly which judgment Triana is asking
> for.
>
> Create ASCII wireframes for every screen. They must directly extend or
> iterate on what is already built in the Triana demo.

### World-availability correction

> Do not rename world availability because Triana will expand world building
> later. Inside World availability, add a point called Case data items.

Accepted result:

```text
World availability
└── Case data items
    ├── Required records/files/entities
    ├── Available and resolvable
    ├── Missing
    ├── Ambiguous
    └── Not checked
```

### Final acceptance and continuity request

> All these decisions and wireframes look good. Add them properly to local
> Markdown files without missing details. Store all related prompts so a new
> session does not rediscover, reinvent, or begin from something that was not
> decided. Also preserve the LABS-06 testing and evaluation backlog; it must be
> fixed later.

## Accepted decisions that must not be reopened accidentally

1. LABS-07 and LABS-08 are one vertical slice.
2. The report is the sole evidence authority; the UI is a deterministic
   projection.
3. Setup currently selects one local trace file only.
4. Trace understanding uses transparent denominators and rejection reasons,
   not an unexplained scalar quality score.
5. The desired user-behavior pipeline freezes deterministic cluster
   membership/support before model-authored summaries and downstream semantic
   assets.
6. Current structural clustering must not be mislabeled as full semantic
   user-need populations.
7. Main case labels are `Seen in traces` and `Grounded variation`; every case
   explains goal, done condition, constraints, source basis, and why it exists.
8. `World availability` remains the umbrella. `Case data items` is its first
   implemented/displayed subsection.
9. One case creates one independent conversation. The UI calls these
   `Conversation runs`, not Postgres episodes.
10. Run states and typed gaps never collapse into pass/success.
11. The results overview answers four questions: learned from traces,
    situations created, what happened, and what needs human judgment.
12. Human review has four independent Yes/No/Cannot-judge rulings: simulated
    user realism, follow-up adaptation, agent goal completion, and
    scope/privacy/boundary compliance.
13. No aggregate Triana verdict is invented.
14. A recorded ruling does not automatically change future cases, accepted
    behavior, or global memory.
15. The first public surface is read-only.
16. The UI directly iterates on the allowlisted Triana demo's visual shell,
    subject to exact per-file provenance and license clearance.
17. Release Review data models, PASS/BLOCK, snapshots, and memory semantics do
    not cross from the demo.
18. Persistent/global memory, judges, baseline/candidate comparison, broad
    eval expansion, generic SDKs, hosted ingestion/execution, and general
    world building remain deferred.
19. No retry, repair, fallback, or rerun-to-green is added.

## Known implementation facts versus future work

### Already true

- LABS-06 is owner-closed as `CLOSED_WITH_ACCEPTED_BACKLOG`.
- The local case path has observed and grounded-expanded origin data.
- The adaptive runner preserves deterministic identity, observation binding,
  termination, budgets, accounting, custody, dedupe, privacy, typed gaps, and
  no retry/repair/fallback.
- Existing readable Markdown demonstrates that a deterministic report
  projection is feasible.

### Not yet true

- No canonical LABS-07/08 report schema is frozen.
- No Labs web UI exists in this repository.
- No Triana demo source file has cleared final per-file reuse review for this
  destination.
- No web stack/dependency decision has passed final audit.
- The current deterministic corpus grouping is structural; corpus-scale
  semantic user-need population derivation remains backlog.
- Exit A has no mutable setup, run, or review action.
- General world building does not exist; only Case data items are currently
  specified under World availability.

## Remaining material owner gates

The accepted wireframes close the journey/IA gate. These material choices are
still open and must not be invented by an implementation worker:

1. Whether the public Exit A sample is a newly generated synthetic run or a
   fully synthetic reconstruction of the private HRAI canary shape.
2. Whether the exact Triana demo snapshot/files clear reuse or the visual
   system is clean-room reimplemented.
3. Final web stack/package manager after dependency and license audit.
4. Public repository license and contribution policy.
5. Static hosting destination, which belongs to LABS-09 rather than the UI
   implementation if it is not needed to build locally.

## Copyable next-session prompt

```text
Continue Triana from local main after LABS-06 closure and acceptance of the
combined LABS-07/08 full-journey wireframes.

Read AGENTS.md and every authority document it requires. Then read completely:
- internal/LABS07_08_FULL_JOURNEY_WIREFRAMES_2026-08-04.md
- internal/LABS07_08_BUILD_HANDOFF_2026-08-04.md
- internal/LABS06_BACKLOG_2026-08-04.md
- internal/TRIANA_LABS_PUBLIC_PREVIEW_ROLLOUT_PLAN_2026-08-03.md
- internal/SLICE_PACKET.md
- the full internal/DECISION_LOG.md

Ground truth: LABS-06 is CLOSED_WITH_ACCEPTED_BACKLOG. LABS-07 and LABS-08
are one canonical-report plus read-only UI vertical slice. The owner accepted
the exact journey, terminology, four-question human-review contract, and ASCII
wireframes in the accepted wireframe document. Do not rename World
availability; Case data items is its currently specified subsection. Setup
currently supports one local file only. Do not invent active trace
integrations. Current deterministic clustering is structural, so do not claim
the semantic population pipeline already exists.

Before implementation:
1. inspect current report/artifact contracts, readable Markdown, CLI, fixtures,
   package boundaries, and the allowlisted Triana demo source candidates;
2. resolve the still-open owner gates rather than inventing them;
3. freeze the minimum canonical report fields required by the accepted screens;
4. perform exact per-file provenance/authorship/license checks before copying
   or adapting any demo byte;
5. replace internal/SLICE_PACKET.md with a bounded LABS-07/08 packet;
6. state exact production/test/doc paths and dependency allowance;
7. use the independent orchestrator → test author → test freeze →
   implementation author → orchestrator verdict protocol.

Preserve deterministic identity, membership, denominators, lineage, cost,
fidelity, gap classification, human-ruling custody, privacy, and no retry,
repair, or fallback. The report owns evidence; TypeScript may only project it.
The first public UI is read-only. Do not add persistent/global memory, judges,
baseline/candidate comparison, broad eval expansion, generic SDKs, hosted
ingestion/execution, mutable review, general world building, or Release Review
PASS/BLOCK semantics.

Ask separately before any provider, target, endpoint, or real-data execution.
```

## Exit handoff expected from the next slice

The implementation session must return the structured uncertainty handoff
required by `AGENTS.md`, including exact changed files, budget reconciliation,
verification commands/artifacts, provenance decisions, unverified behavior,
assumptions, unexpected findings, dependencies, excluded work, risks, and
human actions still required.
