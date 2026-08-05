# Triana Brand Guide

Use this file as the base instruction set when generating any Triana visual
(infographics, social images, Reddit posts). It is extracted from the frozen
Triana demo design contract and the landing-page design system.

## 1. Brand identity

- **Product**: Triana — release intelligence for production AI systems. It runs
  as a CI step in the customer's GitHub Actions and returns a PASS / BLOCK /
  REVIEW decision backed by evidence.
- **Promise**: "Release without discovering regressions from customers."
- **Personality**: engineering notebook, evidence desk. Calm, precise,
  technical. Never hype, never "AI-powered" marketing gloss.
- **Logo mark**: black rounded-square containing a white letter `T`, next to
  the wordmark `Triana` in the display font.

## 2. Theme in one sentence

Warm paper canvas, dark ink for hierarchy, hairline borders, and one tiny
acid-green signal — color communicates state, never decoration.

## 3. Color palette

### Surfaces (most of every image — roughly 95% of pixel area)

| Role | Hex | Notes |
|---|---|---|
| Canvas (background) | `#F2F4E9` | Warm cream-green paper. Page background. |
| Paper (cards) | `#FDFDFB` | Near-white surface for cards and panels. |
| Panel (secondary surface) | `#F6F7F0` | Slightly deeper than paper. |
| Dark surface | `#080A05` | Near-black. Nav, code blocks, inverted panels. |

### Ink (text)

| Role | Hex |
|---|---|
| Ink (primary text) | `#0B0C08` |
| Ink 2 (secondary text) | `#3A3B37` |
| Ink 3 (muted text) | `#686965` |
| Ink 4 (faint text) | `#92938F` |
| Dark-surface text | `#CDCEC9` |

### Accent — acid green (the signature; keep it under 2% of the image)

| Role | Hex |
|---|---|
| Accent | `#D7F144` |
| Accent strong | `#C3DE00` |
| Accent ink (green text on light) | `#354B00` |

Acid green marks the one active or positive thing. Never use it as a large
fill, background, or on two elements at once.

### Status colors (state only, never decoration)

| State | Hex | Soft background |
|---|---|---|
| PASS / positive | `#008039` | `#CBF4D5` |
| BLOCK / regression | `#C90F1A` | `#FFDFD9` |
| REVIEW / warning | `#A66D00` | `#FFECC9` |

### Hairlines (borders)

| Role | Hex |
|---|---|
| Hairline | `#E1E2DC` |
| Hairline 2 (default border) | `#CFD0C9` |
| Hairline 3 (strong border) | `#B7B8B0` |

### Texture

The canvas carries a faint dot grid: 1px dots of `#A4A793` at ~60% opacity,
26px spacing, on the `#F2F4E9` canvas. This is the "engineering paper" feel.

## 4. Typography

| Role | Font | Usage |
|---|---|---|
| Display | **Manrope** (bold/semibold) | Headlines, object names, decisions. |
| Body | **Hanken Grotesk** | Paragraphs, labels, UI copy. |
| Mono | **JetBrains Mono** | IDs, versions, branches, status labels (`PASS`, `BLOCK`, `REVIEW`), metrics, metadata. |

Rules:
- Headlines are dark ink, tight, never gradient text.
- Status words and metrics are always monospace, often uppercase.
- Section headings stay modest; the content (evidence) owns the space.

## 5. Layout language

- One continuous bordered surface beats a grid of unrelated cards.
- Thin 1px ink or hairline borders, 8–16px corner radius, restrained shadows.
- Pills (999px radius) for buttons and status chips.
- Dense tables with continuous hairline rows read as "product evidence."
- Product windows: thin ink border, 16px radius, subtle offset backing plane.

## 6. Hard don'ts

- No gradients, glass panels, rainbow charts, or neon glows.
- No decorative illustrations, mascots, or oversized icons.
- No second accent color system (blue exists only inside the logo mark:
  `#2867E4`).
- No large acid-green fills.
- No hype copy: avoid "actionable insights," "unlock," "optimize,"
  "AI-powered."
- Never show the Agentagon brand.

## 7. Copy voice for infographics

Write for an AI engineer making or reviewing a release. State the decision,
the evidence, and the next action directly.

- Good: "PR #181 — BLOCK. 2 regressions against release memory."
- Bad: "Unlock actionable release insights with AI-powered intelligence."

Preferred vocabulary: merge, release, evidence, regression, eval, production
session, release memory, release policy, PASS / BLOCK / REVIEW.
