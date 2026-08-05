#!/bin/sh

set -eu

root=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$root"

for required in \
  compose.production.yaml \
  triana-backend/Dockerfile \
  triana-backend/.dockerignore \
  triana-app/Dockerfile \
  triana-app/.dockerignore \
  ops/.env.example \
  ops/backend.env.example \
  ops/deploy.sh \
  ops/rollback.sh; do
  [ -f "$required" ] || { echo "missing deployment asset: $required" >&2; exit 1; }
done

if grep -Ev '^[A-Z][A-Z0-9_]*=$|^$' ops/.env.example ops/backend.env.example | grep -q .; then
  echo "ops/.env.example may contain names only" >&2
  exit 1
fi

if grep -Eq '(^|[[:space:]])ADD[[:space:]]' \
  triana-backend/Dockerfile triana-app/Dockerfile; then
  echo "Dockerfiles may not use ADD" >&2
  exit 1
fi

grep -Fq '127.0.0.1:3000:3000' compose.production.yaml
grep -Fq '127.0.0.1:8000:8000' compose.production.yaml
grep -Fq 'no-new-privileges:true' compose.production.yaml
grep -Fq '@sha256:' ops/deploy.sh
grep -Fq 'TRIANA_BACKEND_ENV_FILE' compose.production.yaml
grep -Fq 'TRIANA_LABS_REPORT_ID' compose.production.yaml

if ! awk '
  /^networks:$/ { in_networks = 1; next }
  in_networks && /^  default:$/ { in_default = 1; next }
  in_default && /^    external: true$/ { external = 1; next }
  in_default && /^    name: triana_default$/ { exact_name = 1; next }
  in_default && /^(  [^ ]|[^ ])/ { in_default = 0 }
  END { exit !(external && exact_name) }
' compose.production.yaml; then
  echo "compose default network must be external and named triana_default" >&2
  exit 1
fi

for ignore in triana-backend/.dockerignore triana-app/.dockerignore; do
  [ "$(sed -n '1p' "$ignore")" = '**' ] \
    || { echo "$ignore must start from a deny-all context" >&2; exit 1; }
  if grep -Eq '^!(\.env|\.git|internal|tests)(/|$)' "$ignore"; then
    echo "$ignore allowlists private or test-owned content" >&2
    exit 1
  fi
done

echo "deployment-assets: ok"
