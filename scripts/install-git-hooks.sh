#!/bin/sh

set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"

git config core.hooksPath scripts/git-hooks
git config commit.template .gitmessage

mkdir -p .decision-memory
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  git rev-parse HEAD >.decision-memory/.baseline
fi

printf 'Installed Triana hooks from scripts/git-hooks.\n'
printf 'Configured .gitmessage as the commit template.\n'
printf 'Local decision memory lives in .decision-memory/ and is never pushed.\n'
