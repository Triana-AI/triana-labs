# Triana demo video — narration and animation direction

**Status:** Working V3 for modular production  
**Target duration:** 80–85 seconds  
**Format:** 16:9 product film with founder voiceover  
**Primary use:** YC application and landing-page product demo  
**Source of truth:** Existing Triana demo screens and recorded HR-AI snapshot

### Final artifact order

Keep the existing artifact names so Claude Design does not have to rename prior
work. The final edit order is:

```text
A1 GitHub Gate
→ A2 Production Behavior
→ A5 Release Control
→ A3 Release Diff
→ A4 Release Memory Maintenance
```

`A5` is intentionally inserted between `A2` and `A3`. Production Behavior
shows what users rely on. Release Control shows how that evidence will be
judged. Release Diff then shows what changed. Release Memory closes the loop by
maintaining the eval set for future merges.

Recommended artifact durations:

- A1 GitHub Gate: 12–15 seconds.
- A2 Production Behavior: 12–15 seconds.
- A5 Release Control: 10–12 seconds.
- A3 Release Diff: 15–18 seconds.
- A4 Release Memory Maintenance: 15 seconds maximum.
- Transitions and close: 8–10 seconds total.

## 1. What this video must do

In roughly eighty-five seconds, the viewer should understand:

1. A code change is ready to merge in GitHub.
2. The code diff does not show what changed for users.
3. Triana shows how customers currently use the agent and the recorded sessions behind those behaviors.
4. Release Memory owns what evidence and eval cases get rerun.
5. Release Control owns how that evidence becomes `PASS`, `REVIEW`, or `BLOCK`.
6. One named case changed from `SHORTLIST` to `REJECT`.
7. The customer’s harness executes inside GitHub Actions.
8. An observed regression can be promoted into a regression eval.
9. Newly important user behavior can be added as a representative eval.
10. A human approves changes to what future releases must catch.

This is not a full product tour. It is one merge and one regression story. The
Production Behavior screen earns its place because it explains where the
release cases come from.

## 2. The continuous demo fixture

Use one agent throughout:

> HR-AI Recruitment Screening Assistant

Use one pending merge:

> PR #181 — Preserve eval-to-decision follow-through

Use the current recorded release evidence:

- 18 checks.
- 3 regressions.
- 1 low-sample signal.
- Decision: `BLOCK`.

Use the current Production Behavior evidence:

- 185 recorded sessions.
- 11 stable user needs.
- 91% of traffic explained by those stable needs.
- The top observed need is candidate evaluation and outreach: 77 sessions,
  representing 41.6% of traffic.

Use one named case for the reveal:

> `hr_0099` — Sofia Marchetti

Recorded comparison:

- Current version: `SHORTLIST`.
- Candidate version: `REJECT`.
- Candidate response says that the evidence required for evaluation was inaccessible.
- Tool calls: `9 → 12`.
- Turns: `6 → 2`.

Do not introduce a second example during the main story.

## 3. Locked narration draft

Approximate voiceover length: 188 words.

> An engineer has changed the agent and opened a pull request. The code is ready. The existing checks are green. But a code diff cannot tell you what changed for users.
>
> Triana runs as a check inside GitHub Actions. Your code and credentials stay in CI, and the engineer can open the deeper release evidence.
>
> Before deciding, Triana starts with production. Across one hundred and eighty-five recorded sessions, it shows eleven stable user needs covering ninety-one percent of traffic—evaluation and outreach, applicant ranking, rubric questions—and the sessions behind each.
>
> Release Memory defines what evidence and eval cases get rerun. Release Control defines how those results are judged: absolute requirements, allowed deltas, and changes that need human approval.
>
> This merge was supposed to preserve decision follow-through. Triana selected eighteen relevant approved cases. Three regressed.
>
> Open `hr_0099`. The current agent shortlisted Sofia. The candidate rejected her—even while saying it could not access the evidence.
>
> After the release, Triana turns observed change into maintenance. A regression can become a regression eval. New user behavior can become a representative eval. Your team approves what future releases must catch.
>
> The result is not another score. It is PASS, REVIEW, or BLOCK—with the reason.
>
> Customers should not be your regression test.
>
> Triana shows what a release breaks before it ships.

## 4. Synchronized scene plan

| Time | Founder says | Product on screen | Animated text or motion |
|---|---|---|---|
| `0:00–0:15` · A1 | “An engineer has changed the agent and opened a pull request. The code is ready. The existing checks are green. But a code diff cannot tell you what changed for users. Triana runs inside GitHub Actions.” | Use the accepted A1 GitHub Gate artifact. Ordinary checks pass; `triana / release-check` runs and returns action required. Keep the traffic-light browser chrome. | `CODE DIFF ≠ BEHAVIOR DIFF` → `RUNS IN YOUR GITHUB ACTIONS`. |
| `0:15–0:30` · A2 | “Before deciding, Triana starts with production. Across one hundred and eighty-five recorded sessions, it shows eleven stable user needs covering ninety-one percent of traffic, and the sessions behind each.” | Use A2 Production Behavior. Show the summary, then focus candidate evaluation and outreach: 77 sessions and 41.6% of traffic. | `185 RECORDED SESSIONS` → `11 USER BEHAVIORS` → `91% OF TRAFFIC EXPLAINED`. |
| `0:30–0:41` · A5 | “Release Memory defines what evidence and eval cases get rerun. Release Control defines how those results are judged: absolute requirements, allowed deltas, and changes that need human approval.” | Start on the compact boundary strip: Memory input → Control rules → PASS / REVIEW / BLOCK. Then reveal the three real control groups without opening a drawer. | `MEMORY: WHAT GETS RERUN` → `CONTROL: HOW RESULTS ARE JUDGED` → `REQUIREMENTS · THRESHOLDS · APPROVALS`. |
| `0:41–0:59` · A3 | “This merge was supposed to preserve decision follow-through. Triana selected eighteen relevant approved cases. Three regressed. Open `hr_0099`: the current agent shortlisted Sofia. The candidate rejected her while saying it could not access the evidence.” | Use A3 Release Diff. Reveal 18 checks, 3 regressions, then isolate `hr_0099` and hold `SHORTLIST → REJECT` for at least two seconds. | `18 RELEVANT CASES` → `3 REGRESSED` → `SHORTLIST → REJECT`. |
| `0:59–1:14` · A4 | “After the release, Triana turns observed change into maintenance. A regression can become a regression eval. New user behavior can become a representative eval. Your team approves what future releases must catch.” | Use the updated Release Memory screen. Show three distinct signal-to-change paths, open the `hr_0099` maintenance drawer, approve the change, then show the approved set increase from 18 to 19. | `REGRESSION OBSERVED` → `PROPOSED AS A REGRESSION EVAL` → `YOU APPROVE THE CHANGE` → `18 → 19 APPROVED CASES`. |
| `1:14–1:20` | “The result is PASS, REVIEW, or BLOCK, with the reason. Triana shows what a release breaks before it ships.” | Return briefly to PR #181 BLOCK, then recede to the Triana mark. | `PASS · REVIEW · BLOCK` → `KNOW WHAT THIS RELEASE BREAKS.` |

## 5. On-screen copy inventory

These are the only large animated phrases:

1. `PR #181 · READY TO MERGE`
2. `CODE DIFF ≠ BEHAVIOR DIFF`
3. `RUNS IN YOUR GITHUB ACTIONS`
4. `185 RECORDED SESSIONS`
5. `11 STABLE USER NEEDS`
6. `91% OF TRAFFIC EXPLAINED`
7. `MEMORY: WHAT GETS RERUN`
8. `CONTROL: HOW RESULTS ARE JUDGED`
9. `REQUIREMENTS · THRESHOLDS · APPROVALS`
10. `18 RELEVANT CASES`
11. `3 REGRESSED`
12. `SHORTLIST → REJECT`
13. `REGRESSION OBSERVED`
14. `PROPOSED AS A REGRESSION EVAL`
15. `YOU APPROVE THE CHANGE`
16. `18 → 19 APPROVED CASES`
17. `PASS · REVIEW · BLOCK`
18. `KNOW WHAT THIS RELEASE BREAKS.`

Do not add explanatory paragraphs over the product. The voiceover explains; the animation points.

## 6. Direction for Claude Design

### Preserve

- The current Triana paper-and-ink design.
- Warm dotted canvas.
- White product surfaces.
- Black ink.
- Acid green for PASS and active evidence.
- Amber for REVIEW.
- Red only for regressions and BLOCK.
- Existing typography, borders, spacing, and `T` mark.
- Real case IDs, release names, counts, messages, and tool chains.

### Animation language

- Animate real product objects, not screenshots floating inside decorative frames.
- The opening may use a faithful GitHub-style pull-request and Actions sequence,
  but it must use the real PR title, branch, counts, and Triana check boundary.
- Use object continuity: the PR row becomes the report; `hr_0099` becomes the Release Memory case; the same case enters the later CI check.
- Use slow camera crops and short state transitions rather than constant zooming.
- Keep the product readable for at least two seconds after every important state appears.
- Use masks, row expansion, drawer motion, cursor focus, count changes, and restrained text reveals.
- Treat the `SHORTLIST → REJECT` transition as the visual climax.
- Let `BLOCK` arrive after the evidence, not before it, in the detailed-report scene.
- The GitHub opening is the only authored surface outside the existing Triana
  product.

### Do not use

- Fake browser chrome.
- Floating glass cards.
- Generic mesh gradients or gradient text. A restrained warm-to-acid light
  gradient behind the product is allowed as scene lighting.
- Generic AI particles, neural networks, or glowing orbs.
- Decorative 3D objects.
- Fast montage editing.
- Repeated whoosh transitions.
- Invented dashboards, metrics, customer logos, or traces.
- Full subtitles competing with the product. Burned captions, if required, stay small and near the lower safe area.

### Sound

- Founder voice is primary.
- Low, restrained rhythmic bed.
- One subtle CI-start sound.
- One muted impact when `BLOCK` appears.
- One light confirmation sound for `Protect in future releases`.
- No sound effect on every text reveal.

## 7. What to give Claude Design

Give Claude Design the complete local demo project:

> `/Users/akarshgajbhiye/agentagon/Triana demo`

The whole folder is preferable to screenshots because it contains:

- Exact React components.
- Current routes and interactions.
- Frozen CSS and design tokens.
- Real snapshot data.
- The temporary Triana mark.
- Responsive behavior.

Do not ask Claude Design to explore the whole Agentagon repository. Scope it to
`Triana demo` plus the script.

Also provide a small reference pack:

1. This file:
   `internal/TRIANA_DEMO_VIDEO_SCRIPT.md`.
2. `Triana demo/DESIGN_CONTRACT.md`.
3. `apps/landing/TRIANA_LANDING_PAGE_CONTENT.md` for locked public language.
4. One clean screenshot of each required state:
   - Release Decisions.
   - Production Behavior.
   - `hr_0099` session drawer.
   - PR #181 deeper report.
   - Release Memory.
   - Issue/protection action.
5. A short text file listing the localhost routes and the exact state to capture.

Screenshots are references, not the animation source. Claude Design should reuse
or import the real components wherever practical and build the animated sequence
as a separate prototype so the product demo remains untouched.

Recommended working boundary:

```text
Triana demo/                  read-only product source
internal/TRIANA_DEMO_VIDEO_SCRIPT.md
video-prototype/              new Claude Design output
```

Do not let Claude Design rewrite `Triana demo` while creating the film.

## 8. Claude Design master prompt

> Create an 80–90 second 16:9 animated product demo for Triana, targeting 85 seconds, using the supplied real product code, screens, snapshot data, and design system. Do not redesign the application. Preserve its warm dotted canvas, white paper surfaces, black ink, monospace metadata, acid green PASS state, amber REVIEW state, red BLOCK state, hairline borders, compact information density, and temporary black `T` mark.
>
> Tell one continuous story about PR #181, “Preserve eval-to-decision follow-through,” for the HR-AI Recruitment Screening Assistant. Open with a faithful GitHub-style pull-request animation: the code change is ready to merge and ordinary checks are green, but the Triana GitHub Actions check opens the deeper behavioral release evidence. This GitHub scene is authored connective animation; do not fabricate a GitHub product capability or claim.
>
> From GitHub, enter the real Release Decisions queue and keep PR #181 as the continuous object. Before showing its verdict, visit the real Production Behavior screen. Show 185 recorded sessions, 11 stable user needs, and 91% of traffic explained. Focus the top need, candidate evaluation and outreach: 77 sessions and 41.6% of traffic. Open the recorded session behind it. Do not invent a historical demand change; this scene shows how customers currently use the agent and the production sessions behind that behavior.
>
> Return to PR #181. The merge has 18 relevant approved cases, 3 regressions, 1 low-sample signal, and a BLOCK decision. The reveal is recorded case `hr_0099`: the current version shortlisted Sofia Marchetti, while the candidate rejected her despite saying the evidence required for evaluation was inaccessible. Treat `SHORTLIST → REJECT` as the visual climax.
>
> Carry the same `hr_0099` object into Release Memory and define Release Memory on screen as “APPROVED CASES RERUN BEFORE EACH MERGE.” Show “Protect in future releases,” then show the same case entering a later CI scope. Make the execution boundary explicit: the customer’s existing harness runs current and candidate versions inside GitHub Actions; code and credentials stay in CI; Triana selects relevant approved cases, compares outcomes, records the release decision, and links it to the original session.
>
> Finish on the real Release Decisions screen with one recent PASS, one REVIEW, and PR #181 changing to BLOCK. Close on “KNOW WHAT THIS RELEASE BREAKS.” and “Release Intelligence for production AI agents.”
>
> Animate the existing product rather than presenting static screenshots. Use object continuity, row expansion, right-side drawers, restrained camera crops, and short text reveals. Keep every important product state readable for at least two seconds. Do not use fake browser frames around the Triana product, glass cards, generic AI imagery, decorative 3D objects, invented metrics, invented traces, or rapid montage editing. A restrained warm-to-acid light gradient may be used as scene lighting behind the product, never as gradient text or a generic mesh background.
>
> Build the animation as a new editable HTML/CSS/JavaScript prototype outside the Triana demo folder. Import or faithfully reuse the real components and tokens. Do not modify the source demo. Keep narration and animation timing aligned to the supplied timeline.

### V3 modular prompts for A4 and A5

Use the paste-ready prompts from the handoff message or the following exact
artifact briefs:

#### A4 — Release Memory Maintenance

- Update the existing A4 artifact; do not restart its visual language.
- Duration: 12–15 seconds, with a hard maximum of 15 seconds.
- Source: the latest `/release-memory` screen and its maintenance drawer.
- Show the three separate observed-signal paths: regression observed → promote
  confirmed failure; user behavior observed → add representative behavior as a
  new eval; eval coverage drift → refresh eval coverage.
- Use `hr_0099` for the interaction. Open its maintenance drawer, show
  `SHORTLIST → REJECT`, select `Approve change`, then show the approved release
  set increasing from 18 to 19.
- The user owns semantic approval. Triana proposes maintenance; it does not
  silently rewrite the eval set.
- Use “Approve change,” not “Add to memory.” Avoid conversational uses of
  “remember.”
- Required large captions: `REGRESSION OBSERVED.` →
  `PROPOSED AS A REGRESSION EVAL.` → `RELEASE MEMORY UPDATED.`
- Required small captions: `hr_0099 changed SHORTLIST to REJECT.` →
  `Your team approves what future releases must catch.` →
  `18 → 19 approved eval cases.`

#### A5 — Release Control

- Create a new 10–12 second artifact named A5.
- It appears in the final edit between A2 Production Behavior and A3 Release
  Diff.
- Source: the latest `/release-control` screen.
- Start with the boundary strip: Release Memory supplies approved behaviors,
  failures, eval cases, and traces; Release Control applies requirements,
  thresholds, and approval rules; the output is PASS, REVIEW, or BLOCK.
- Show the three real control groups without turning this into a product tour:
  absolute requirements, allowed baseline-to-merge deltas, and semantic changes
  requiring human approval.
- Show one concrete rule from each group. Do not show an observed merge verdict
  here; A3 owns the release result.
- Required large captions: `MEMORY DEFINES WHAT GETS RERUN.` →
  `CONTROL DEFINES HOW RESULTS ARE JUDGED.` →
  `PASS · REVIEW · BLOCK.`
- Required small captions: `Approved behaviors, failures, eval cases, and traces.`
  → `Requirements, thresholds, and human approvals.`

## 9. First review checklist

Before refining color or motion, verify:

- Can a viewer explain Triana after the first 15 seconds?
- Does the GitHub opening make the release trigger obvious without implying that
  GitHub itself understands agent behavior?
- Is PR #181 visibly the same object from queue to report?
- Does Production Behavior clearly show current customer use and the sessions
  behind it?
- Are the 185-session, 11-need, and 91% figures legible and traceable to the
  snapshot?
- Does `hr_0099` remain visibly the same case from evidence to Release Memory?
- Is the `SHORTLIST → REJECT` change readable without pausing the video?
- Is Release Memory clearly a set of approved cases, not chat memory?
- Is it clear that the customer harness executes in GitHub Actions?
- Does the viewer see a PASS as well as REVIEW and BLOCK?
- Does the video end on the release outcome, not a product-feature list?
- Are all counts and claims traceable to the current demo snapshot?
