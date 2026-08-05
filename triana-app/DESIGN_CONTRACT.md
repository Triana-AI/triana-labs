# Triana demo — frozen product and design contract

Status: accepted and frozen on 2026-07-27 by Akarsh.

This document is the source of truth for every subsequent Triana demo screen.
The canonical rendered references are:

- `/` — Release Decisions
- `/populations` — Production Behavior

## 1. Product posture

Triana is release intelligence for production AI systems. It runs as a real CI
step inside the customer's GitHub Actions environment and links to a deeper
hosted report. It does not ask for general repository access.

The narrow promise is: release without discovering regressions from customers.

Triana supports that promise through three connected objects:

1. Release memory grounded in current production behavior.
2. Release controls that encode what must remain true and what amount of change
   is acceptable.
3. Per-merge evidence that results in PASS, BLOCK, or REVIEW.

Triana does not position itself as an eval-writing service. Teams own
correctness and approve semantic standards. Triana maintains the evidence set,
detects drift, reruns the relevant evidence at release time, and makes the
decision legible.

Release Memory and Release Control have one strict boundary:

- Release Memory owns **what gets rerun**. It maintains the approved behaviors,
  confirmed failures, eval cases, expected outcomes, and supporting traces.
- Release Control owns **how results become a decision**. It applies absolute
  requirements, allowed deltas, and human approval rules to return PASS, REVIEW,
  or BLOCK.

Observed production signals do not silently change either object. A confirmed
regression may be proposed as a regression eval. A newly important user
behavior may be proposed as a representative eval. Coverage drift may trigger a
sampling refresh. The team approves semantic changes before they enter Release
Memory.

## 2. Screen architecture

The product navigation is:

1. Release Decisions — concurrent merge queue and immediate decision workload.
2. Production Behavior — what users ask, observed handling, and trace evidence.
3. Release Control — release standards, thresholds, and approval boundaries.
4. Release Memory — remembered production cases and suggested memory changes.
5. Releases — durable decision and regression history.
6. Issues — post-release problems that can be promoted into future protection.

Connect Agent is onboarding and remains outside the persistent app rail.

Do not add a duplicate “release check,” “release gate,” or “release decision”
screen. The merge queue is the decision entry point. A release report is the
deep evidence view.

## 3. Information hierarchy

Every screen answers one operational question:

- Release Decisions: What is waiting on me before it can merge?
- Production Behavior: What do users rely on this agent to do?
- Release Control: What must remain true for a merge to pass?
- Release Memory: What user situations does Triana remember and rerun before a merge?
- Releases: What changed across previous releases?
- Issues: What failed in production, and has it become regression memory?

The answer appears above the fold. A page title identifies the surface but never
becomes the surface. Do not use oversized hero copy, giant empty cards, or a
single summary object that consumes most of the viewport.

## 4. Spatial system

- Desktop rail: 68px collapsed by default; approximately 216px expanded.
- Content starts immediately after the rail and uses the available width.
- Screen maximum width: roughly 92–96rem, depending on table density.
- Screen padding: `clamp(1.1rem, 2.2vw, 2rem)`.
- Compact page header, then the primary operational surface within about 120px.
- Primary rows are generally 56–96px tall.
- Prefer one continuous bordered surface to a grid of unrelated cards.
- Use summary strips only when they compress useful counts into one short row.
- No horizontal document overflow at 320, 375, 768, 1280, or 1440px.

## 5. Visual language

Preserve the existing paper-and-ink visual system:

- Warm dotted canvas.
- White paper surfaces.
- Black/dark ink for primary information.
- Hairline borders and restrained shadows.
- Acid green for positive/active evidence.
- Red for regressions or blocks.
- Amber for review or uncertain evidence.
- Monospace for IDs, versions, branches, trace IDs, status labels, and metadata.
- Display sans for human-readable object names and decisions.

Color communicates state. It is not decoration. Do not add gradients, rainbow
charts, glass panels, decorative illustrations, oversized icons, or a second
accent system.

## 6. Brand and navigation

The temporary brand is a black rounded-square `T` mark plus the name `Triana`.
The `T` remains visible when the rail is collapsed. The name appears when it is
expanded.

Navigation uses compact letter glyphs and text labels. Disabled future surfaces
may look muted, but once a screen exists its navigation item is active.

Never show the Agentagon brand in visible UI.

## 7. Copy contract

Write for an AI engineer making or reviewing a release:

- Prefer “what users ask,” “merge,” “release,” “evidence,” “regression,”
  “production session,” and “needs approval.”
- Prefer recognizable user needs over ontology names.
- Do not repeat domain nouns mechanically at the start of every row.
- Avoid vague phrases such as “actionable insights,” “unlock,” “optimize,” or
  “AI-powered.”
- Avoid explaining the thesis in every screen.
- State the decision, evidence, and next action directly.

Good: “Preserve eval-to-decision follow-through.”

Bad: “Candidate observed demand population candidate workflow.”

## 8. Evidence and truthfulness

Use real snapshot facts for:

- Trace IDs and session contents.
- User messages and recorded agent responses.
- Tool chains, turns, outcomes, costs, and decision changes.
- Release versions and run IDs.
- Measurement counts, regression counts, and sample warnings.
- Production behavior support and traffic share.

Configuration and demo workflow state may be authored where the source artifacts
do not contain it, but the UI must frame it honestly as a configured standard,
suggestion, pending approval, or maintenance action. Never fabricate a trace,
customer incident, measured score, or historical release result.

Evidence should stay close to the claim it supports. Prefer a row action that
opens a right-side drawer with the full chain. Do not force users through a
separate summary page before they can inspect the evidence.

## 9. Interaction contract

- Rows are the primary interactive objects.
- Use right-side drawers for trace, issue, maintenance, or measurement detail.
- PASS/BLOCK/REVIEW is always visible before opening detail.
- Buttons describe the action: “Review change,” “View session,” “Promote to eval
  set,” “Approve standard.”
- Collapsed navigation remains usable through titles/tooltips.
- Escape and backdrop click close drawers.
- Focus-visible states must remain legible.
- Mobile surfaces stack without changing the underlying information model.

## 10. Screen-specific constraints

### Release Control

Show release standards, not a duplicate decision result. Separate:

- Absolute requirements that must pass.
- Allowed baseline-to-merge deltas.
- Semantic changes that require human approval.

The screen should make its input and output explicit: Release Memory supplies
approved evidence and eval cases; Release Control applies policy and returns
PASS, REVIEW, or BLOCK. Do not put maintenance suggestions or eval-set
membership changes on this screen.

### Release Memory

Release memory is the concrete set of user situations Triana remembers and
reruns before every merge. Each remembered case contains the user request, the
recorded chain, and the outcome or failure that future releases must preserve or
avoid. It is the product's regression memory, not a generic evidence archive.

Show the approved release set and a compact maintenance inbox. Each suggestion
must distinguish the observed signal from the proposed eval-set change. The
first maintenance actions are:

1. Regression observed → promote a confirmed failure as a regression eval.
2. User behavior observed → add a representative behavior as a new eval.
3. Eval coverage drift → refresh sampling and coverage.

Semantic additions, removals, or threshold changes require approval.

### Releases

Show one durable record per merge/release, including decision, comparison,
regression count, evidence scope, and date. Let the user inspect the historical
report without turning the page into a marketing dashboard.

### Issues

Show post-release problems in a Sentry/GitHub-like operational queue. Connect
each issue to a real recorded evidence case where available. Make its regression
memory state explicit: detected, confirmed, promoted, or resolved.

## 11. Change policy

This design contract is frozen for the demo. A later agent may extend components
and responsive rules, but must not reinterpret the product hierarchy or visual
language. Any intentional departure requires an explicit user decision and a
successor entry in the repository decision log.
