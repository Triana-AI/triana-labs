# Triana decision log

Append only accepted or autonomously executed decisions. Never rewrite history.

Format:

```text
- What: <decision> | Why: <reason> | When: YYYY-MM-DD | Whom: <decision maker and executor>
```

- What: Start Triana in a new independent repository with no Agentagon code, artifacts, or Git history; preserve Akarsh-owned product decisions through newly authored context files and permit future Kairos/Kairos-AI reuse only through a provenance ledger | Why: Agentagon's reset history cannot reliably separate Gursharan-owned implementation from later work, and Akarsh wants a clean codebase without losing product context | When: 2026-07-30 | Whom: Akarsh decided; Codex created and verified the clean-room bootstrap

- What: Keep the repository language-neutral and implementation-empty at bootstrap | Why: Runtime, packaging, and service architecture should follow the first vertical-slice contract rather than arrive accidentally through copied code | When: 2026-07-30 | Whom: Codex executed within Akarsh's clean-slate authorization

- What: Ship the first self-serve V1 for a narrow CI-runnable ICP as one human-approved production incident converted into a protected case, replayed against an explicit approved baseline and candidate, evaluated through Triana deterministic assertions plus one generic customer-owned result lane, and returned as an advisory PASS, REVIEW, or BLOCK recommendation with a permanent Release Evidence Record | Why: This is the smallest truthful production-to-release loop that tests value without claiming representative coverage, automatic ground truth, universal replay, or enforcement | When: 2026-07-29 | Whom: Akarsh decided; Codex preserved the decision in the clean-room product specification

- What: Keep Triana V1 closed-source and distribute a versioned compiled CLI/container, a thin GitHub Action wrapper, and hosted APIs and web surfaces; disclose sample workflows, cases, records, and reproduction instructions but not Triana implementation | Why: Customer-CI execution requires local custody of code and credentials, not source disclosure, and the implementation remains proprietary until adoption creates a concrete reason to change distribution | When: 2026-07-29 | Whom: Akarsh decided; Codex preserved the decision

- What: Keep release authority deterministic and human-approved; permit LLMs only as optional case-drafting assistance or inside the customer agent/evaluator, never as hidden authority over membership, denominators, comparability, policy, or record identity | Why: The release recommendation must be reproducible, auditable, and grounded in approved semantics and explicit evidence | When: 2026-07-29 | Whom: Akarsh asked for the boundary; Codex formalized and preserved it
