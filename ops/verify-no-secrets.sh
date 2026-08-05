#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

if [ "$#" -gt 0 ]; then
  files="$*"
else
  cd "$root"
  files=$(git ls-files -- \
    '.github/workflows/*' \
    'compose.production.yaml' \
    'ops/*' \
    'triana-app/Dockerfile' \
    'triana-app/.dockerignore' \
    'triana-app/app/*' \
    'triana-app/components/*' \
    'triana-app/lib/*' \
    'triana-backend/Dockerfile' \
    'triana-backend/.dockerignore' \
    'triana-backend/migrations/*' \
    'triana-backend/src/*')
fi

for file in $files; do
  [ -f "$file" ] || continue
  if grep -E -q \
    '(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|((AZURE_OPENAI|OPENAI|AWS)_[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD))[[:space:]]*=[[:space:]]*[^[:space:]#]+)' \
    "$file"; then
    echo "secret-like content detected in $file" >&2
    exit 1
  fi
done

echo "content-secret-scan: ok"
