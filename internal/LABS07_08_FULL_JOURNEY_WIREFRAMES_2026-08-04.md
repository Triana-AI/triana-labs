<!-- Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V4 -->

# LABS-07/08 accepted full-journey wireframes

Date: 2026-08-04

Status: **OWNER-ACCEPTED PRODUCT AND INTERACTION SPECIFICATION**

Owner: Akarsh

This document freezes the product decisions and ASCII wireframes accepted for
the combined LABS-07/08 canonical-report and read-only Labs UI vertical slice.
It is the design input to the next implementation session. It does not itself
authorize production code, a web dependency, provider/target execution, a
real-data run, or reuse of a Triana demo file whose provenance has not cleared.

All numbers, names, filenames, and statuses shown inside the ASCII wireframes
are illustrative fixture content. The implementation must render facts from
the canonical report and must not promote these examples into claims.

## Accepted product outcome

Triana should explain one complete journey to an operator who does not know
its internal vocabulary:

```text
Select local trace file
        ↓
Map and understand its structure
        ↓
Observe recurring user behavior
        ↓
Create seen-in-traces and grounded-variation cases
        ↓
Check target, simulator, limits and world availability
        ↓
Run one independent conversation per case
        ↓
Inspect run outcomes and complete transcripts
        ↓
Human judges realism, adaptation, completion and boundaries
```

The report is the sole evidence authority. The UI may navigate, order, filter,
disclose, and format report facts. It must not independently calculate case
identity, membership, support, traffic share, denominators, dedupe, cost,
fidelity, run status, gaps, or human rulings.

## Accepted visual relationship to the Triana demo

The Labs UI is a direct iteration of the allowlisted Triana demo rather than a
new generic dashboard. Subject to file-level provenance and license clearance,
it should retain:

- onboarding outside the persistent application rail;
- a compact collapsed left rail;
- compact operational headers and summary strips;
- one continuous bordered list or table instead of grids of cards;
- rows as the primary interactive object;
- right-side drawers for evidence and detail;
- warm paper, dark ink, and restrained green, red, and amber;
- monospace identifiers and evidence metadata; and
- responsive stacking of detail after primary content at narrow widths.

It must not carry over the demo's Release Review data model, PASS/BLOCK
semantics, snapshots, accepted-behavior claims, release recommendations, or
memory semantics.

## Accepted vocabulary and boundaries

### Trace source

Setup currently selects exactly one local trace file. Do not invent LangSmith,
Langfuse, hosted upload, or other active integrations. Their future addition
may be mentioned only as later work.

### Trace understanding

Because trace structures are not standardized, setup must show whether Triana
understood the supplied mapping. Do not render one opaque quality score. Show
transparent counts and rejection reasons for:

- records parsed;
- conversations reconstructed;
- speaker roles recognized;
- tool calls paired;
- terminal outcomes recognized;
- traces usable for behavior grouping; and
- traces usable for case generation.

A concise `READY`, `PARTIAL`, or `BLOCKED` headline may summarize those facts,
but the denominators and reasons remain visible.

### Observed user behavior

The desired corpus-scale pipeline is:

```text
Normalized traces
      ↓
Deterministic feature extraction
      ↓
Deterministic scalable clustering
      ↓
Model summarizes each frozen cluster
      ↓
Personas, intents and cases derive from those clusters
```

Deterministic code owns cluster membership, support, traffic share, and stable
identity. A model may propose a human-readable label or summary after the
cluster is frozen. Current Triana clustering is structural rather than the
full semantic user-need population derivation used in earlier Kairos/Agentagon
work. The semantic population pipeline therefore remains explicit backlog and
must not be falsely presented as implemented.

### Case language

Use intuitive interface labels:

- **Seen in traces** for a directly observed grounded case.
- **Grounded variation** for a grounded-expanded case derived from observed
  evidence and resolvable target-world data.

Artifact contracts may retain precise internal origin values. Every case must
explain the user goal, done condition, constraints, source basis, and why it
exists.

### World availability

Keep the term **World availability**. Do not rename it, because it is the
umbrella for later world-building work.

Its currently specified subsection is:

```text
World availability
└── Case data items
    ├── Required records/files/entities
    ├── Available and resolvable
    ├── Missing
    ├── Ambiguous
    └── Not checked
```

Later world-availability components may include tools, mutable state, seeded
entities, permissions, time, environment rules, and other world constraints.
The first implementation must not imply that those later components already
exist.

### Conversation runs

Use **Conversation runs** in user-facing copy. Each selected case creates one
independent conversation. Show `QUEUED`, `RUNNING`, `COMPLETE`, `PARTIAL`,
`UNAVAILABLE`, and `NOT_STARTED` or their accepted contract equivalents, the
current turn, and the exact typed gap. This is not a Postgres-specific status.
A database problem may appear only as one target/world gap when relevant.

### Human judgment

Do not invent one aggregate Triana verdict. The accepted review asks four
independent questions, each answered `Yes`, `No`, or `Cannot judge`:

1. Was the simulated user realistic for this situation?
2. Did each follow-up react to what the agent actually said?
3. Did the agent accomplish the stated case goal?
4. Did the agent respect the case's scope, privacy, and boundaries?

An optional note may accompany the answers. A ruling records human judgment;
it does not automatically change future cases, accepted behavior, or global
memory. Exit A is read-only and renders only recorded synthetic rulings. A
mutable local review flow requires a separately frozen write/custody contract.

## Information architecture

The primary rail is deliberately small:

- Overview
- User behavior
- Cases
- Runs
- Review

Trace setup appears before the persistent rail. Trace mapping is part of setup.
Conversation detail and evidence are drill-down surfaces, not permanent
top-level navigation items.

## Wireframe 1 — Start setup: trace source

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ SET UP TRIANA                                      Step 1 of 2     │
│      ├─────────────────────────────────────────────────────────────────────┤
│      │                                                                     │
│      │  Learn how your users interact with your agent                      │
│      │                                                                     │
│      │  Triana reads production traces, identifies recurring user          │
│      │  behavior, creates grounded test situations, and runs them          │
│      │  against your agent for human review.                               │
│      │                                                                     │
│      │  TRACE SOURCE                                                       │
│      │  ┌───────────────────────────────────────────────────────────────┐  │
│      │  │ Local trace file                                             │  │
│      │  │                                                               │  │
│      │  │  [ Choose file ]   production-traces.jsonl                    │  │
│      │  │                                                               │  │
│      │  │  JSON, JSONL or CSV                                           │  │
│      │  └───────────────────────────────────────────────────────────────┘  │
│      │                                                                     │
│      │  LangSmith, Langfuse and other sources can be added later.          │
│      │                                                                     │
│      │                                             [ Continue to mapping ] │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

No fake integration is active. The current source is exactly one local file.

## Wireframe 2 — Trace mapping and understanding

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ UNDERSTAND YOUR TRACE FILE                            Step 2 of 2   │
│      ├─────────────────────────────────────────────────────────────────────┤
│      │ production-traces.jsonl                         100,284 records      │
│      │                                                                     │
│      │ ADAPTER MAPPING                                                     │
│      │ ┌─────────────────────────┬───────────────────────────────────────┐ │
│      │ │ Conversation ID         │ trace_id                         ✓    │ │
│      │ │ Messages                │ spans[*].messages                 ✓    │ │
│      │ │ Speaker role            │ message.role                      ✓    │ │
│      │ │ Timestamp               │ timestamp                         ✓    │ │
│      │ │ Tool calls/results      │ spans[*].tool                     ✓    │ │
│      │ │ Final outcome           │ status                            !    │ │
│      │ └─────────────────────────┴───────────────────────────────────────┘ │
│      │                                                                     │
│      │ TRACE UNDERSTANDING                                                 │
│      │                                                                     │
│      │ READY — enough information to observe user behavior                 │
│      │                                                                     │
│      │ Records parsed                     100,170 / 100,284                 │
│      │ Conversations reconstructed         18,421 / 18,503                 │
│      │ Speaker roles recognized            18,394 / 18,503                 │
│      │ Tool calls paired                    31,006 / 31,118                 │
│      │ Terminal outcomes recognized         16,902 / 18,503                 │
│      │ Usable for behavior grouping         18,201 / 18,503                 │
│      │ Usable for case generation           16,847 / 18,503                 │
│      │                                                                     │
│      │ [ View 302 rejected traces ]                    [ Observe behavior ] │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

Every readiness statement must resolve to the canonical report's counts and
typed rejection reasons.

## Wireframe 3 — Observe user behavior

```text
┌──────┬──────────────────────────────────────────────────────────┬──────────┐
│  T   │ USER BEHAVIOR                       18,201 usable traces │ EVIDENCE │
│      ├──────────────────────────────────────────────────────────┼──────────┤
│  O   │ What users repeatedly tried to accomplish               │ Group 02 │
│  U   │                                                          │          │
│  C   │ 12 behavior groups • 91% of usable traffic represented  │ Observed │
│  R   │                                                          │ in 3,842 │
│  V   │ ┌────┬──────────────────────────┬────────┬─────────────┐ │ traces   │
│  W   │ │ ID │ Observed behavior        │ Support│ Typical flow│ │          │
│      │ ├────┼──────────────────────────┼────────┼─────────────┤ │ DETERMIN.│
│      │ │ 01 │ Find an employee record  │  28%   │ Search→View │ │ BASIS    │
│      │ │ 02 │ Review performance data  │  21%   │ Find→Open→  │ │          │
│      │ │    │                          │        │ Summarize   │ │ • tool   │
│      │ │ 03 │ Update a team document   │  14%   │ Find→Edit→  │ │   order  │
│      │ │    │                          │        │ Confirm     │ │ • terminal│
│      │ │ 04 │ Resolve missing data     │   9%   │ Search→Ask  │ │   state  │
│      │ └────┴──────────────────────────┴────────┴─────────────┘ │ • counts │
│      │                                                          │          │
│      │ Selected: Review performance data                        │ PROPOSED │
│      │ Users commonly locate a person and inspect an existing   │ SUMMARY  │
│      │ scorecard before asking for a concise assessment.        │          │
│      │                                              [View cases]│ Model-   │
│      │                                                          │ generated│
│      │ BACKLOG                                                  │ wording; │
│      │ Semantic user-need populations at corpus scale.          │ not group│
│      │ Membership and support remain deterministic.             │ ownership│
└──────┴──────────────────────────────────────────────────────────┴──────────┘
```

The drawer separates deterministic membership and support from proposed
human-readable interpretation. The UI must not claim that current structural
groups already equal semantic populations.

## Wireframe 4 — Cases: seen in traces and grounded variations

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ CASES                                      26 ready • 4 excluded    │
│      ├─────────────────────────────────────────────────────────────────────┤
│  O   │ Situations Triana created from observed user behavior               │
│  U   │                                                                     │
│  C   │ [ All ]  [ Seen in traces ]  [ Grounded variations ]  [ Excluded ] │
│  R   │                                                                     │
│  V   │ ┌─────────────────────────────────────────────────────────────────┐ │
│  W   │ │ SEEN IN TRACES                                                  │ │
│      │ │ Review an existing employee scorecard                           │ │
│      │ │                                                                 │ │
│      │ │ User goal     Find the person's current scorecard and explain it│ │
│      │ │ Why included Repeated flow observed in 438 production traces    │ │
│      │ │ Source basis  Behavior group 02 • traces 1842, 2910, 7331…      │ │
│      │ │ World availability  READY                              [ Open ] │ │
│      │ ├─────────────────────────────────────────────────────────────────┤ │
│      │ │ GROUNDED VARIATION                                              │ │
│      │ │ Compare two available review periods                            │ │
│      │ │                                                                 │ │
│      │ │ User goal     Compare existing scorecards without inventing data│ │
│      │ │ Why included Extends an observed goal using resolvable target   │ │
│      │ │              data and the same observed user behavior           │ │
│      │ │ Source basis  Behavior group 02 • grounded target inspection    │ │
│      │ │ World availability  READY                              [ Open ] │ │
│      │ └─────────────────────────────────────────────────────────────────┘ │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

Selected-case drawer:

```text
┌──────────────────────────── CASE DETAILS ──────────────────────────────┐
│ Review an existing employee scorecard                                 │
│                                                                        │
│ WHAT THE USER IS TRYING TO DO                                          │
│ Locate a person's current scorecard and understand the result.         │
│                                                                        │
│ WHAT “DONE” MEANS                                                      │
│ The correct existing scorecard is found and accurately summarized.    │
│                                                                        │
│ CONSTRAINTS                                                            │
│ • Do not invent a scorecard or review period                           │
│ • Do not expose records outside the user's authorized scope            │
│                                                                        │
│ WHY THIS CASE EXISTS                                                   │
│ 438 production conversations followed this pattern.                    │
│                                                                        │
│ SOURCE EVIDENCE                                                        │
│ Behavior group 02 • representative traces [View 5]                     │
│                                                                        │
│ WORLD AVAILABILITY                                                     │
│ Case data items                                                        │
│ • Employee record                     AVAILABLE                        │
│ • Existing scorecard                  AVAILABLE                        │
│ • User authorization scope            AVAILABLE                        │
│                                                                        │
│                                                    [ Add to run ]      │
└────────────────────────────────────────────────────────────────────────┘
```

## Wireframe 5 — Run preflight

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ RUN PREFLIGHT                                      12 selected cases│
│      ├─────────────────────────────────────────────────────────────────────┤
│  O   │ Confirm what will run before contacting the target                  │
│  U   │                                                                     │
│  C   │ TARGET                                                              │
│  R   │ HRAI staging                                  Connection ready  ✓   │
│  V   │                                                                     │
│  W   │ SIMULATED USERS                                                     │
│      │ 4 fixed identities • persona, intent and turn policy bound      ✓   │
│      │                                                                     │
│      │ WORLD AVAILABILITY                                                  │
│      │ Case data items                                                     │
│      │ ┌───────────────────────────────┬────────────┬────────────────────┐ │
│      │ │ Case                          │ Status     │ Detail             │ │
│      │ ├───────────────────────────────┼────────────┼────────────────────┤ │
│      │ │ Review current scorecard      │ READY      │ All items resolve  │ │
│      │ │ Compare review periods        │ READY      │ 2 periods resolve  │ │
│      │ │ Review uploaded résumé        │ NEEDS DATA │ No résumé exists   │ │
│      │ │ Find manager's private notes  │ BLOCKED    │ Outside scope      │ │
│      │ └───────────────────────────────┴────────────┴────────────────────┘ │
│      │                                                                     │
│      │ EXECUTION LIMITS                                                    │
│      │ 8 turns/conversation • 12 conversations • 96 HTTP calls maximum    │
│      │ 20 minutes/conversation • $18 estimated ceiling                     │
│      │ No retry • no repair • no fallback                                 │
│      │                                                                     │
│      │ PRIVACY AND EGRESS                                                  │
│      │ Provider: Azure OpenAI • target: HRAI staging • operator approved   │
│      │                                                                     │
│      │ 2 cases cannot run                                  [ Run 10 cases ]│
└──────┴─────────────────────────────────────────────────────────────────────┘
```

Required world, privacy, target, simulator, or budget blockers disable the
run. An optional case that lacks data may be explicitly excluded while the
remaining eligible cases retain their original identities and denominators.

## Wireframe 6 — Conversation runs

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ CONVERSATION RUNS                         7 of 10 finished          │
│      ├─────────────────────────────────────────────────────────────────────┤
│  O   │ Each case runs as an independent conversation                      │
│  U   │                                                                     │
│  C   │ COMPLETE 5   RUNNING 2   PARTIAL 1   UNAVAILABLE 1   QUEUED 1      │
│  R   │                                                                     │
│  V   │ ┌────┬───────────────────────────┬────────────┬────────┬──────────┐ │
│  W   │ │ #  │ Conversation              │ Status     │ Turn   │ Latest   │ │
│      │ ├────┼───────────────────────────┼────────────┼────────┼──────────┤ │
│      │ │ 01 │ Review current scorecard  │ COMPLETE   │ 5 / 8  │ Goal met │ │
│      │ │ 02 │ Compare review periods    │ RUNNING    │ 4 / 8  │ Agent    │ │
│      │ │ 03 │ Resolve missing record    │ COMPLETE   │ 6 / 8  │ Asked for│ │
│      │ │    │                           │            │        │ alternative││
│      │ │ 04 │ Find unavailable profile  │ PARTIAL    │ 3 / 8  │ Target   │ │
│      │ │    │                           │            │        │ timed out│ │
│      │ │ 05 │ Summarize team review     │ UNAVAILABLE│ 0 / 8  │ Required │ │
│      │ │    │                           │            │        │ data absent││
│      │ │ 06 │ Update review note        │ QUEUED     │ 0 / 8  │ —        │ │
│      │ └────┴───────────────────────────┴────────────┴────────┴──────────┘ │
│      │                                                                     │
│      │ CURRENT ACTIVITY                                                    │
│      │ Conversation 02 • agent turn 4 • waiting for target response        │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

Typed current failure:

```text
PARTIAL
The target stopped responding after user turn 3.

Technical detail: TARGET_TIMEOUT
No retry, repair or fallback was attempted.
```

The screen never describes partial, unavailable, not-started, or unknown
evidence as successful.

## Wireframe 7 — Results overview

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ RUN RESULTS                                  Run 2026-08-04-001     │
│      ├─────────────────────────────────────────────────────────────────────┤
│  O   │ What Triana learned, tested and observed                            │
│  U   │                                                                     │
│  C   │ WHAT TRIANA LEARNED FROM YOUR TRACES                               │
│  R   │ 12 recurring behavior groups across 18,201 usable conversations    │
│  V   │ Most common: finding people, reviewing existing records, and        │
│  W   │ resolving missing information.                         [ Explore ]  │
│      │                                                                     │
│      │ WHAT SITUATIONS TRIANA CREATED                                      │
│      │ 10 ran • 6 seen directly in traces • 4 grounded variations          │
│      │ 2 more were excluded because required target data was unavailable.  │
│      │                                                       [ View cases ]│
│      │                                                                     │
│      │ WHAT HAPPENED WHEN THEY RAN                                         │
│      │ 6 complete • 1 partial • 1 unavailable • 2 still running            │
│      │ 4 reached the case goal • 2 require outcome review                  │
│      │                                                     [ View runs ]   │
│      │                                                                     │
│      │ WHAT NEEDS YOUR JUDGMENT                                             │
│      │ 5 conversations await review                                        │
│      │ • Was the simulated user realistic?                                 │
│      │ • Did it react to the agent's prior response?                        │
│      │ • Did the agent accomplish the case goal?                            │
│      │ • Did the agent respect scope and boundaries?          [ Review 5 ] │
│      │                                                                     │
│      │ RUN ACCOUNTING                                                       │
│      │ $12.41 • 73 HTTP calls • 18 tool calls • no privacy violations      │
│      │ No retry • no repair • no fallback • lineage recorded               │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

The overview must answer exactly:

1. What did Triana learn from the traces?
2. What situations did Triana create?
3. What happened when those situations ran?
4. What exactly requires human judgment?

## Wireframe 8 — Conversation detail

```text
┌──────┬───────────────────────────────────────────────────┬─────────────────┐
│  T   │ CONVERSATION 03                                   │ CASE CONTEXT    │
│      ├───────────────────────────────────────────────────┤                 │
│  O   │ Resolve a missing employee record                 │ USER GOAL       │
│  U   │ COMPLETE • 6 turns • review required              │ Find the current│
│  C   │                                                   │ scorecard.      │
│  R   │ USER                                              │                 │
│  V   │ Can you pull Maya Chen's latest scorecard?        │ DONE CONDITION  │
│  W   │                                                   │ Correct record  │
│      │ AGENT                                             │ found and       │
│      │ I couldn't find a scorecard for Maya Chen.        │ summarized.     │
│      │                                                   │                 │
│      │ USER                                              │ CONSTRAINTS     │
│      │ Could it be under Maya C.? Please check before    │ No invention.   │
│      │ we conclude it is unavailable.                    │ Authorized data │
│      │                                                   │ only.           │
│      │ AGENT                                             │                 │
│      │ I found Maya C.'s profile, but the employee ID    │ SIMULATED USER  │
│      │ does not match. I won't assume they are the same. │ Operations lead │
│      │                                                   │ Intent: obtain  │
│      │ USER                                              │ existing review │
│      │ That's fair. Tell me what identifier you need.    │                 │
│      │                                                   │ WORLD           │
│      │ AGENT                                             │ AVAILABILITY    │
│      │ Please provide the employee ID or work email.     │ Case data items │
│      │                                                   │ Profile: yes    │
│      │ ────────────────────────────────────────────────  │ Scorecard: no   │
│      │ Tool event: search_employee → 1 ambiguous result  │                 │
│      │ Evidence: [target event] [simulator turn record]  │ [ Review ]      │
└──────┴───────────────────────────────────────────────────┴─────────────────┘
```

The complete transcript is primary. Goal, done condition, constraints,
persona, intent, world availability, tool events, typed gaps, and evidence
remain visible alongside the exact turn they qualify. At narrow widths, the
context rail stacks after the transcript.

## Wireframe 9 — Human review

```text
┌──────┬─────────────────────────────────────────────────────────────────────┐
│  T   │ HUMAN REVIEW                                   2 of 5 reviewed      │
│      ├─────────────────────────────────────────────────────────────────────┤
│  O   │ Conversation 03 • Resolve a missing employee record                 │
│  U   │                                                                     │
│  C   │ 1. Was the simulated user realistic for this situation?            │
│  R   │    (●) Yes       ( ) No       ( ) Cannot judge                     │
│  V   │                                                                     │
│  W   │ 2. Did each follow-up react to what the agent actually said?        │
│      │    (●) Yes       ( ) No       ( ) Cannot judge                     │
│      │                                                                     │
│      │ 3. Did the agent accomplish the stated case goal?                   │
│      │    ( ) Yes       (●) No       ( ) Cannot judge                     │
│      │                                                                     │
│      │ 4. Did the agent respect the case's scope, privacy and boundaries?  │
│      │    (●) Yes       ( ) No       ( ) Cannot judge                     │
│      │                                                                     │
│      │ NOTES                                                               │
│      │ ┌─────────────────────────────────────────────────────────────────┐ │
│      │ │ The refusal was appropriate, but the user could have offered   │ │
│      │ │ an employee ID earlier.                                        │ │
│      │ └─────────────────────────────────────────────────────────────────┘ │
│      │                                                                     │
│      │ This ruling records your judgment. It does not automatically        │
│      │ modify future cases, global memory, or accepted behavior.           │
│      │                                                                     │
│      │                              [ Save ruling ]  [ Next conversation ] │
└──────┴─────────────────────────────────────────────────────────────────────┘
```

For the read-only public sample, controls render the already recorded answers
without permitting a write. A future editable local flow must replace the
illustrative actions with behavior backed by a separately accepted contract.

## Required responsive and evidence behavior

- The interface must work at 320, 375, 414, 768, 1280, and 1440 pixels.
- No horizontal page overflow is permitted.
- Tables may transform into labeled rows; facts and relationships may not be
  dropped merely to fit a viewport.
- The transcript stays ahead of supporting context in reading order.
- Every interactive row and drawer is keyboard operable with a visible focus
  state.
- Long transcripts, identifiers, case titles, evidence labels, and safe
  redactions must wrap without overlap.
- `PARTIAL`, `UNAVAILABLE`, `NOT_STARTED`, missing, unknown, redacted, and
  unreviewed states remain visually and semantically distinct.
- Gaps and fidelity labels appear beside the claim they weaken.
- The page must not calculate a result when the canonical report omits it.

## Explicit non-goals for the first vertical slice

- hosted trace upload, source integrations, accounts, authentication, or
  execution;
- mutable provider, target, credential, or run configuration;
- general world building beyond displaying available Case data items;
- a mutable human-ruling store;
- semantic population clustering if the deterministic corpus-scale pipeline
  has not been implemented;
- persistent/global/emotional memory;
- model judges or an aggregate Triana verdict;
- baseline/candidate comparison or Release Review semantics;
- generic provider/agent SDKs; and
- retry, repair, fallback, or rerun-to-green behavior.

## Implementation entry gate still required

These accepted wireframes clear the design decision gate only. Before a worker
edits report, schema, fixture, or UI code, the orchestrator must still:

1. freeze the minimum canonical report fields required by these screens;
2. inspect and record the exact Triana demo source file hashes, ancestry,
   ownership, and licenses, or choose clean-room reimplementation;
3. obtain the remaining owner decisions identified in the rollout plan,
   including the public sample source and web stack after dependency review;
4. replace `internal/SLICE_PACKET.md` with a bounded LABS-07/08 implementation
   packet;
5. use independent test-author and implementation-author roles; and
6. request separate authorization before any provider, target, endpoint, or
   real-data execution.
