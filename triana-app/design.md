# Triana Labs visual system

Status: locked for the Labs report application on 2026-08-05.

Triana Labs is a warm technical instrument panel for AI engineers. It uses the
solid cream and near-white product surfaces from the Triana site, dense rules
for sustained inspection, and acid green only as a sparse signal.
This application uses the Workbench macrostructure because the primary job is
to inspect report evidence and move between related operational views.

## Palette and depth

- The page canvas is solid warm cream and reading surfaces are near-white.
- The persistent navigation rail is compact white with an ink-dark active cell.
- Acid green marks the active location, focus, and small evidence signals; it
  must not become a large background field.
- Red and amber remain
  semantic evidence states and never become decorative accents.
- Primary evidence surfaces use a thin gray-green border, a restrained shadow, and,
  for the Overview evidence stage only, one offset backing plane.
- Do not draw fake browser, terminal, phone, or IDE chrome.
- Do not use background images, dot patterns, textures, or gradients.

## Type and spacing

- Manrope is the display face, Hanken Grotesk is the reading face, and
  JetBrains Mono is limited to identifiers, counts, and compact metadata.
- Body copy is at least 16px on reading surfaces. Display type uses a 1.25
  scale, tight tracking, and no italic emphasis.
- Use the shared 4px spacing scale. Operational lists stay continuous; avoid
  grids of identical cards and avoid card-in-card containment.
- Page headers are left-biased and compact. The primary report object remains
  above the fold.

## Shell and logo

- Use the official Triana Lazo SVG in both desktop and mobile navigation.
- The expanded lockup reads “Triana Labs”; the collapsed rail retains the
  recognizable mark and an accessible brand label.
- Desktop navigation is a compact collapsible rail. Mobile navigation is an
  off-canvas sheet that is absent from focus and visibility while closed.
- Navigation labels never wrap. Every control has a visible focus state and a
  touch target of at least 44px.

## Overview

- Lead with a compact disclosure: “Bundled demo report”. State that this public
  build ships one synthetic artifact and that the renderer is report-driven.
- Present the four result questions as one evidence stage with unequal visual
  weight, not four decorative feature cards.
- Only values already present in `data/labs-report.json` may appear as facts.

## Review

- First explain what a human is deciding and why the four dimensions stay
  independent. “Cannot judge” means evidence is missing, not that the run
  failed.
- Define realism, adaptation, goal completion, and scope/privacy/boundaries in
  plain language before showing the recorded ruling queue.
- The queue distinguishes recorded from unreviewed conversations without
  inventing a combined score or aggregate verdict.
- Recorded rulings remain read-only and link back to their exact conversation.

## Motion and responsiveness

- Motion is limited to navigation state and directional link feedback. Animate
  transform or opacity only, use the shared exponential easings, and honor
  `prefers-reduced-motion`.
- Required QA widths are 320, 375, 414, 768, 1280, and 1440 CSS pixels.
- `html` and `body` use `overflow-x: clip`; long headings and identifiers may
  wrap, but clickable labels may not.

## Prohibited patterns

No gradients, pure black/white surfaces, fake UI chrome, decorative icon-card
grids, large accent fills, hover-only affordances, invented metrics, aggregate
verdicts, upload/run/save promises, or Release Review vocabulary.
