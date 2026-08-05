# Triana Labs application agent instructions

Before changing any screen, read `LABS_DESIGN_CONTRACT.md` completely. Read
`DESIGN_CONTRACT.md` for the inherited visual system and shell ancestry only;
its suspended Release Review product hierarchy and vocabulary are superseded in
this repository.

The inherited demo screens are the canonical structural reference. Preserve
their shell, density, spacing, typography, copy style, and evidence-first
interaction model. `design.md` is the locked Labs visual system and
`LABS_DESIGN_CONTRACT.md` is the current product and route authority. Do not
introduce a different dashboard genre or hero treatment.

Screen work must:

1. Use the shared `AppShell` and compact, collapsible Triana rail.
2. Reuse the existing tokens in `tokens.css` and the brand treatment in
   `design.md`.
3. Keep the primary operational object above the fold.
4. Prefer compact queues, tables, and drawers over large cards.
5. Use only validated facts from `data/labs-report.json`; do not add a second
   UI data authority or calculate report outcomes in TypeScript.
6. Label intentional demo policy/configuration as policy or configuration; do
   not present invented evidence as observed fact.
7. Keep visible copy human and domain-readable. Internal ontology identifiers
   may appear only as secondary monospace metadata.
8. Provide responsive behavior with no horizontal document overflow.
9. Never add the Agentagon name or mark to visible app chrome.
10. Run `npm run build` after integration.

Product vocabulary: use trace understanding, observed user behavior, cases,
conversation runs, results, and human review. Do not reintroduce PASS/BLOCK,
baseline/candidate, regression, release recommendation, release memory, or
accepted-behavior semantics.

Shared shell, navigation, global imports, and other agents' screen files are
owned by the primary integrator unless the task explicitly assigns them.
