# Versioned Git hooks

Install once per clone:

```sh
./scripts/install-git-hooks.sh
```

The installer sets `core.hooksPath=scripts/git-hooks` and configures the
repository commit-message template.

- `pre-commit` validates append-only governance and the previous commit's local
  decision-memory entry.
- `commit-msg` enforces Conventional Commits.
- `post-commit` creates a local Why/Evidence/Trace journal entry.
- `pre-push` blocks direct pushes from `main` or `master` and requires complete
  governance and decision memory.

Do not bypass these hooks with `--no-verify`.
