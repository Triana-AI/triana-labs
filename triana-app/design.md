---
name: Triana Labs Mission Control
description: A dense, trustworthy evidence console for inspecting agent behavior.
colors:
  acid-signal: "oklch(91% 0.19 118)"
  warm-paper: "oklch(99.4% 0.003 112)"
  warm-paper-subtle: "oklch(97.4% 0.01 112)"
  command-ink: "oklch(15% 0.008 120)"
  stage-ink: "oklch(22% 0.01 120)"
  secondary-ink: "oklch(57% 0.012 118)"
  gray-green-rule: "oklch(85% 0.014 112)"
  evidence-red: "oklch(53% 0.21 27)"
  caution-amber: "oklch(58% 0.13 75)"
typography:
  display:
    fontFamily: "Manrope, ui-sans-serif, system-ui, sans-serif"
    fontWeight: 700
    lineHeight: 1.06
    letterSpacing: "-0.035em"
  body:
    fontFamily: "Hanken Grotesk, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1rem"
    lineHeight: 1.55
  label:
    fontFamily: "JetBrains Mono, ui-monospace, SFMono-Regular, monospace"
    fontSize: "0.6875rem"
    fontWeight: 500
    letterSpacing: "0.08em"
rounded:
  xs: "2px"
  sm: "4px"
  md: "6px"
  lg: "8px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  navigation-active:
    backgroundColor: "{colors.command-ink}"
    textColor: "{colors.warm-paper}"
    rounded: "{rounded.md}"
    height: "44px"
  evidence-stage:
    backgroundColor: "{colors.warm-paper}"
    textColor: "{colors.command-ink}"
    rounded: "{rounded.lg}"
    padding: "24px"
  status-warning:
    textColor: "{colors.caution-amber}"
    rounded: "{rounded.xs}"
  status-failure:
    textColor: "{colors.evidence-red}"
    rounded: "{rounded.xs}"
---

# Design System: Triana Labs Mission Control

## Overview

**Creative North Star: "The Operator's Evidence Ledger"**

Triana Labs is a professional control surface for examining agent behavior, not a marketing dashboard. The dark shell establishes operational context while contiguous warm paper evidence surfaces carry sustained reading. Dark content stages are rare and purposeful; the composition changes between surfaces so the product feels like a connected tool rather than one repeated document template.

The interface is dense but not cramped. It makes provenance, uncertainty, and human authority visible without decorating them into generic cards. The official Triana Lazo and a very sparse acid signal provide identity; semantic amber and red remain reserved for caution and failure.

**Key Characteristics:**

- Persistent full-label navigation and compact product chrome.
- A dark operational shell framing calm, contiguous evidence surfaces.
- Unequal, content-led layouts instead of repeated card grids.
- Report-driven facts with explicit partial, unavailable, and unreviewed states.
- Acid used as a locator or action signal, never as a large fill.

## Colors

The palette is controlled and high-contrast: command ink, warm paper, gray-green rules, and one rare acid signal.

### Primary

- **Acid Signal:** Marks the active location, keyboard focus, and small action underlines. Its scarcity is the brand signature.

### Neutral

- **Command Ink:** Shell, command stages, and active navigation cells.
- **Warm Paper:** Primary reading and evidence surfaces.
- **Warm Paper Subtle:** Product header and secondary light fields.
- **Gray-Green Rule:** Dividers, borders, and table structure.
- **Secondary Ink:** Supporting labels and non-primary copy.

### Semantic

- **Evidence Red:** Failed or known-gap evidence only.
- **Caution Amber:** Backlog, not-evaluated, and warning evidence only.

**The Sparse Signal Rule.** Acid appears on one primary locator or action family in a viewport and never becomes a panel background.

**The Evidence Color Rule.** Amber and red communicate evidence state; they are never decorative brand accents.

## Typography

**Display Font:** Manrope with a system sans fallback

**Body Font:** Hanken Grotesk with a system sans fallback

**Label/Mono Font:** JetBrains Mono with a system monospace fallback

**Character:** Manrope supplies compact authority, Hanken Grotesk keeps report prose readable, and JetBrains Mono makes identifiers and metadata feel inspectable. Narrative body copy stays at least 16px.

### Hierarchy

- **Display:** Bold and tightly tracked; reserved for page and primary result statements.
- **Headline:** Compact section conclusions with a short measure.
- **Body:** Regular 16px reading copy with generous line height and controlled line length.
- **Label:** Uppercase mono metadata, identifiers, counts, and evidence states; never used for paragraphs.

**The Three-Voice Rule.** Display, reading, and metadata each have one typographic job; do not add novelty faces or arbitrary size jumps.

## Layout

Desktop uses a fixed 12.75rem full-label navigation rail and a compact 3.25rem product header. The rail never collapses into initials or glyph-only navigation. Overview is dark-dominant: a light orientation header gives way to dark disclosure, results, and accounting stages, then a light limitations reading break. Continuous rows and spacing bands are preferred over decorative borders or identical card grids.

At widths below 60rem, navigation becomes an off-canvas sheet and a minimum 44px menu control replaces the desktop rail. Closed navigation is invisible, non-interactive, and does not create horizontal overflow. Long identifiers and headings wrap; interactive labels do not.

## Elevation & Depth

The system is flat by default. Depth comes from tonal transitions, borders, and occasional restrained lift on raised evidence stages or the open mobile navigation. Decorative glass, gradients, textures, and stacked card shadows are excluded.

**The Evidence Plane Rule.** A shadow denotes a genuinely raised evidence plane or overlay, not every container.

## Shapes

Corners are restrained: 2–8px for tags, controls, stages, and evidence surfaces. Gray-green hairlines establish structure. Avoid pills except for intrinsically compact status tokens, and avoid ornamental clipping or novelty silhouettes.

## Components

### Navigation

The desktop rail shows complete route labels and may collapse fully off-canvas through an authored 44px control; it never degrades into initials or a glyph-only route strip. A matching expand control remains in the product header. The active route is an ink-dark cell with a two-pixel acid underline. The Lazo appears once per viewport—in the rail on desktop and the menu control on mobile. The report block says “Report artifact” and describes the bundled artifact truthfully; it never implies a live connection.

### Evidence stages

Evidence stages share one spacing and type system but use distinct compositions based on content. Overview groups its operational disclosure, results, and accounting into a dark sequence; subtle dark tonal steps separate result rows without hairline boxes. Lists remain fluid; tables are used only for genuinely tabular comparisons.

### Status tokens

Statuses use compact mono labels and semantic borders/text. Repeated status lists reserve a fixed-width status column so every explanation starts on one vertical line; badges never stretch to the row height. Amber represents backlog or unevaluated evidence, red represents failure, and neutral states remain neutral.

### Links and controls

Controls meet a 44px minimum target. Action links use a restrained acid underline and directional feedback. Keyboard focus uses a two-tone acid-and-ink ring that remains visible on both paper and command surfaces.

## Do's and Don'ts

### Do:

- **Do** preserve full navigation labels and distinct page compositions.
- **Do** render facts from the canonical report and expose missing or partial evidence honestly.
- **Do** use warm paper for sustained reading and command ink for operational framing.
- **Do** keep narrative copy at 16px or larger and controls at least 44px.
- **Do** reserve amber and red for semantic evidence states.

### Don't:

- **Don't** use duplicate brand marks, single-letter navigation, or a glyph-only desktop route strip.
- **Don't** imply live execution, connectivity, or a combined verdict in this read-only report.
- **Don't** repeat one rigid card or table layout across every section.
- **Don't** alternate surface colors without a real information boundary, or use hairline borders as a substitute for hierarchy.
- **Don't** use gradients, dot patterns, fake terminal chrome, decorative icon grids, or large acid fills.
- **Don't** invent metrics, upload/run/save promises, or Release Review vocabulary.
