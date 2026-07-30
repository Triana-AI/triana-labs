# Contributing to Triana

Triana is currently a private, closed-source project. Contribution access does
not grant a license to redistribute its implementation.

## Start here

1. Read `AGENTS.md`.
2. Read `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, and `docs/CONTRACTS.md`.
3. Read `internal/DECISION_LOG.md`, `docs/ENGINEERING.md`, and
   `internal/WORKING_MEMORY.md`.
4. Read `docs/PROVENANCE.md` before bringing in any external material.
5. Read the live `internal/SLICE_PACKET.md` before implementation.
6. Install the repository hooks:

   ```sh
   ./scripts/install-git-hooks.sh
   ```

## Work

- Use a topic branch; never work directly on `main`.
- Define the implementation slice and acceptance test before coding.
- Keep test author, implementation author, and final orchestrator approval
  independent for every slice.
- Keep changes small and include tests with implementation.
- Update canonical documentation and append durable decisions in the same
  change.
- Use Conventional Commits with `Why`, `Evidence`, and `Decision` in the body.
- Run `./scripts/verify-governance.sh` and all stack-specific gates.
- Complete the local `.decision-memory/` entry before the next commit or push.

See `docs/ENGINEERING.md` for the full policy.
