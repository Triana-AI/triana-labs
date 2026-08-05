# Triana Labs application contract

Status: accepted successor contract for LABS-07/08 Exit A on 2026-08-05.

This file governs product and UI maintenance in `triana-app`. The inherited
`DESIGN_CONTRACT.md` remains frozen visual ancestry for the Workbench shell; its
Release Review product semantics are suspended and do not govern this app.

## Product posture

Triana Labs helps an AI engineer inspect what Triana read from traces, how it
grouped structurally observed behavior, which grounded situations it created,
what happened in recorded conversation runs, what evidence is incomplete, and
which four questions require human judgment.

The application is a read-only projection of one publication-safe synthetic
canonical report. It is not a hosted ingestion or execution product. It has no
upload, auth, database, storage, queue, worker, provider call, target call,
review mutation, or persistent backend.

## Data and authority

- `data/labs-report.json` is the only UI data input.
- `scripts/build-snapshot.mjs --validate` enforces the closed report contract.
- Deterministic report bytes own IDs, lineage, membership, denominators,
  counts, statuses, gaps, accounting, fidelity labels, and recorded rulings.
- TypeScript owns navigation, ordering, disclosure, and formatting only.
- Model-proposed summaries stay labeled separately from deterministic group
  membership and support.
- A human owns realism, adaptation, goal-completion, and
  scope/privacy/boundary rulings. The UI never combines them.
- Missing or weaker evidence remains `PARTIAL`, `UNAVAILABLE`, `NOT_STARTED`,
  `UNKNOWN`, `NOT_CHECKED`, or `UNREVIEWED`; it never becomes success or zero.

## Routes and questions

- `/setup`: What trace artifact did Triana read and understand?
- `/behavior`: What structural user-behavior groups were observed, and who owns
  each claim?
- `/cases`: Which seen-in-traces and grounded-variation situations exist, and
  is their case data available?
- `/run`: What were the recorded limits and state of each conversation run?
- `/results`: What did Triana learn, create, observe, and leave for judgment?
- `/conversations/[conversation_id]`: What exact transcript, tool events,
  nearby evidence, gaps, case context, and accounting were recorded?
- `/review`: What are the four independent recorded human rulings?

`/` redirects to `/setup`. The persistent rail labels are Overview, User
behavior, Cases, Runs, and Review; setup remains available as Report source.

## Visual system

`design.md` is the locked visual system. Preserve the inherited Workbench
structure while aligning its brand layer with the Triana landing site:

- compact collapsible desktop rail and off-canvas mobile rail;
- Manrope display, Hanken Grotesk body, and JetBrains Mono metadata;
- the official Triana Lazo mark in app navigation;
- solid warm cream canvas, near-white product surfaces, a compact white rail, dark ink,
  hairlines, restrained shadows, and one acid-green signal accent;
- green for complete/available evidence, amber for uncertain or review states,
  red for unavailable or negative evidence;
- continuous operational lists and transcript surfaces rather than decorative
  card grids;
- compact page headers, report facts above the fold, exact evidence adjacent to
  the claim it qualifies;
- an ink-dark selected navigation cell and sparse acid evidence signals;
- visible `:focus-visible` treatment, 44px touch targets, reduced motion, and
  no horizontal document overflow.

The UI must distinguish “this public build ships a bundled synthetic report”
from “Triana only supports synthetic data.”

Required browser widths are 320, 375, 414, 768, 1280, and 1440 CSS pixels.
Clickable labels stay on one line. At mobile widths the closed rail must be
hidden from focus and visibility, tables/grids must stack, and transcript/tool
metadata must not squeeze identifiers into unreadable fragments.

## Copy and prohibited semantics

Write for AI engineers and agent builders. Prefer concrete report language:
trace source, accepted/rejected record, structural group, support, source
basis, case data item, recorded conversation, evidence, gap, limitation, and
human judgment.

Do not show PASS/BLOCK, baseline/candidate, regression, release recommendation,
release memory, snapshot, accepted behavior, or any aggregate verdict. Do not
advertise upload, run now, rerun, save, approval, sign-in, account, provider,
target, or backend actions. Do not invent metrics, customer evidence, costs,
readiness, population coverage, or production claims.

## Change and verification policy

Keep the report contract closed and dependency-free. A new field, backend,
auth flow, data source, mutation, provider/target call, dependency version, or
hosting claim requires a separately accepted change budget and the canonical
decision/provenance update in the sibling Triana engine repository.

Before handoff run:

1. `node scripts/build-snapshot.mjs --validate data/labs-report.json`
2. `npm run typecheck`
3. `npm test`
4. `npm run build`
5. rendered responsive and keyboard QA when a screen or shared style changes

The frozen LABS-07/08 acceptance test is
`tests/labs-report-ui.test.mjs`, SHA-256
`785b9e924e5f978a6a52282b7c6cf0184bfa41daacb79245d47a9cf97cba34c6`.
Do not edit it as part of production implementation.

The frozen brand and Review-clarity acceptance test is
`tests/labs-review-brand.test.mjs`, SHA-256
`1e07ecd8e3ae5600396815c16fcc888eae3dea18e0789210d9427e95c85d4cb5`.
Do not edit it as part of production implementation.
