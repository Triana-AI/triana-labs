# Provenance and clean-room ledger

## Repository origin

This repository was created from scratch on 2026-07-30 at Akarsh's request.
It does not share Git history with Agentagon and contains no Agentagon
implementation.

The initial Markdown files were newly authored to preserve decisions made by
Akarsh during Triana product work. They are not a code port.

## Source policy

| Source | Status | Allowed use |
|---|---|---|
| `/Users/akarshgajbhiye/agentagon` | Restricted | Do not copy code or artifacts. Rewrite Akarsh-owned facts and accepted decisions only. |
| `/Users/akarshgajbhiye/kairos` | Permitted with ledger | Inspect, copy, or reimplement Akarsh-owned code after recording exact provenance and licenses. |
| `/Users/akarshgajbhiye/kairos-ai` | Permitted with ledger | Inspect, copy, or reimplement Akarsh-owned code after recording exact provenance and licenses. |
| Triana Notion database | Permitted context | Rewrite Akarsh-owned product decisions, interviews, and research; link canonical pages. |
| Third-party repositories/packages | License-dependent | Record version, license, and usage before adoption. |

The Agentagon repository's current Git authorship cannot establish file-level
ownership because its history was reset. Do not infer eligibility from the
current commit author.

## Reuse procedure

Before a port:

1. Record source repository, path, and commit SHA.
2. Check source authorship and any third-party origin.
3. Check the source repository license and file headers.
4. Confirm that the source was not previously copied from Agentagon.
5. Decide whether to copy, adapt, or cleanly reimplement.
6. Record the destination and material changes below.
7. Add focused tests that describe Triana's contract rather than preserving
   accidental source behavior.

## Reuse ledger

| Date | Capability | Source repository/path@commit | Destination | Method | License/ownership check | Executor |
|---|---|---|---|---|---|---|
| 2026-07-30 | Initial context pack | Akarsh-authorized decisions; no source port | Repository Markdown files | Newly authored | No Agentagon code copied | Codex |

## Explicit exclusions at bootstrap

- Agentagon Python packages and tests;
- Agentagon trace, signal, eval, diff, and runner schemas;
- Agentagon prompts and LLM workflows;
- Agentagon fixtures, customer artifacts, and generated reports;
- Agentagon UI, demos, CSS, images, and landing-page implementation;
- Agentagon configuration and infrastructure;
- Agentagon Git history.

If Akarsh later wants a specific Akarsh-authored Agentagon file to cross, add an
explicit allowlist entry here before touching it. The entry must name the file
and why its ownership is sufficiently established.
