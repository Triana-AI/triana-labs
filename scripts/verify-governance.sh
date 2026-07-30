#!/bin/sh

set -eu

mode=${1:---working-tree}
root=$(git rev-parse --show-toplevel)
decision_log="$root/internal/DECISION_LOG.md"
failed=0

fail() {
  printf 'governance: %s\n' "$1" >&2
  failed=1
}

validate_decision_log() {
  awk '
    /^```/ {
      fenced = !fenced
      next
    }
    !fenced && /^- What:/ {
      if ($0 !~ /^- What: .+ \| Why: .+ \| When: [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] \| Whom: .+$/) {
        print "malformed decision entry at line " NR > "/dev/stderr"
        bad = 1
      }
    }
    END { exit bad }
  ' "$1"
}

case "$mode" in
  --working-tree|--staged)
    ;;
  *)
    printf 'usage: %s [--working-tree|--staged]\n' "$0" >&2
    exit 2
    ;;
esac

if [ ! -f "$decision_log" ]; then
  fail "internal/DECISION_LOG.md is missing"
else
  if ! validate_decision_log "$decision_log"; then
    failed=1
  fi
fi

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  old_log=$(mktemp "${TMPDIR:-/tmp}/triana-decision-old.XXXXXX")
  new_log=$(mktemp "${TMPDIR:-/tmp}/triana-decision-new.XXXXXX")
  trap 'rm -f "$old_log" "$new_log"' EXIT HUP INT TERM

  if git show HEAD:internal/DECISION_LOG.md >"$old_log" 2>/dev/null; then
    if [ "$mode" = "--staged" ]; then
      if ! git show :internal/DECISION_LOG.md >"$new_log" 2>/dev/null; then
        fail "the staged change deletes internal/DECISION_LOG.md"
      fi
    else
      cp "$decision_log" "$new_log"
    fi

    if [ -s "$new_log" ]; then
      if ! validate_decision_log "$new_log"; then
        failed=1
      fi
      old_bytes=$(wc -c <"$old_log" | tr -d ' ')
      prefix=$(mktemp "${TMPDIR:-/tmp}/triana-decision-prefix.XXXXXX")
      head -c "$old_bytes" "$new_log" >"$prefix"
      if ! cmp -s "$old_log" "$prefix"; then
        fail "internal/DECISION_LOG.md is append-only; add a correcting or superseding entry instead of editing history"
      fi
      rm -f "$prefix"
    fi
  fi
fi

if [ "$mode" = "--staged" ]; then
  staged_files=$(git diff --cached --name-only --diff-filter=ACMR)

  for path in $staged_files; do
    case "$path" in
      .env.example)
        ;;
      .env|.env.*|*.pem|*.key|*id_rsa*|*id_ed25519*|secrets/*|*/secrets/*)
        fail "refusing staged secret-like file: $path"
        ;;
    esac
  done

  governance_changed=0
  for path in $staged_files; do
    case "$path" in
      AGENTS.md|CLAUDE.md|.claude/settings.json|docs/PRODUCT.md|docs/ARCHITECTURE.md|docs/ENGINEERING.md|scripts/git-hooks/*|scripts/verify-governance.sh|scripts/verify-decision-memory.sh)
        governance_changed=1
        ;;
    esac
  done

  if [ "$governance_changed" -eq 1 ]; then
    if ! printf '%s\n' "$staged_files" | grep -qx 'internal/DECISION_LOG.md'; then
      fail "authority or governance changed without a staged append to internal/DECISION_LOG.md"
    fi
  fi
fi

if [ "$failed" -ne 0 ]; then
  exit 1
fi

printf 'governance: ok (%s)\n' "$mode"
