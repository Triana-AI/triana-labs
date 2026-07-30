#!/bin/sh

set -eu

root=$(git rev-parse --show-toplevel)
memory_dir="$root/.decision-memory"
baseline="$memory_dir/.baseline"

if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  exit 0
fi

head_hash=$(git rev-parse HEAD)
short_hash=$(git rev-parse --short HEAD)

if [ -f "$baseline" ] && [ "$(cat "$baseline")" = "$head_hash" ]; then
  exit 0
fi

entry_file=
for candidate in "$memory_dir"/*.md; do
  [ -f "$candidate" ] || continue
  if grep -q "^## $short_hash — " "$candidate"; then
    entry_file=$candidate
    break
  fi
done

if [ -z "$entry_file" ]; then
  printf 'decision-memory: no entry for %s; reinstall hooks or add the required journal entry\n' "$short_hash" >&2
  exit 1
fi

if ! awk -v header="## $short_hash — " '
  index($0, header) == 1 {
    found = 1
    inside = 1
    next
  }
  inside && /^## / {
    inside = 0
  }
  inside && /TODO|<intent|<tests|<decision-log/ {
    incomplete = 1
  }
  inside && /^- Why: .+/ && $0 !~ /TODO/ {
    why = 1
  }
  inside && /^- Evidence: .+/ && $0 !~ /TODO/ {
    evidence = 1
  }
  inside && /^- Trace: .+/ && $0 !~ /TODO/ {
    trace = 1
  }
  END {
    if (!found || incomplete || !why || !evidence || !trace) {
      exit 1
    }
  }
' "$entry_file"; then
  printf 'decision-memory: complete Why, Evidence, and Trace for %s in %s\n' "$short_hash" "$entry_file" >&2
  exit 1
fi

printf 'decision-memory: ok (%s)\n' "$short_hash"
