# Triana instructions for Claude Code

Read and follow `AGENTS.md` in this directory in full before doing any work.
It is the single shared contributor contract for Claude Code, Codex, humans,
and other coding agents.

Do not duplicate or reinterpret its rules here. If this file and `AGENTS.md`
ever diverge, `AGENTS.md` wins and this file should be repaired to point to it.

The required repository memory is:

1. `docs/PRODUCT.md`
2. `docs/ARCHITECTURE.md`
3. `internal/DECISION_LOG.md`
4. `docs/ENGINEERING.md`
5. `internal/WORKING_MEMORY.md`
6. `docs/PROVENANCE.md`

Before implementation, read and follow the live
`internal/SLICE_PACKET.md`. Claude Code may act as test author or
implementation author, but never both for the same slice.

Use `./scripts/install-git-hooks.sh` once per clone before the first commit.
