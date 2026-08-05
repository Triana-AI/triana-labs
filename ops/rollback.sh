#!/bin/sh

set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: rollback.sh <40-character-git-sha>" >&2
  exit 64
fi

git_sha=$1
deploy_root=${TRIANA_DEPLOY_ROOT:-/opt/triana}
release_file="$deploy_root/releases/$git_sha.env"
lock_file="$deploy_root/deploy.lock"

if [ "${#git_sha}" -ne 40 ]; then
  echo "git SHA must be exactly 40 lowercase hexadecimal characters" >&2
  exit 65
fi
case "$git_sha" in
  *[!0-9a-f]*) echo "git SHA must be lowercase hexadecimal" >&2; exit 65 ;;
esac
[ -f "$release_file" ] || { echo "unknown release $git_sha" >&2; exit 66; }
compose_file=$(sed -n 's/^TRIANA_COMPOSE_FILE=//p' "$release_file" | tail -1)
[ -f "$compose_file" ] || { echo "release compose metadata is unavailable" >&2; exit 66; }

exec 9>"$lock_file"
flock -n 9 || { echo "another deployment is active" >&2; exit 75; }
docker compose \
  --project-name triana \
  --env-file "$release_file" \
  --file "$compose_file" \
  up --detach --remove-orphans --wait --wait-timeout 180
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/health/ready >/dev/null
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:3000/setup >/dev/null
ln -sfn "releases/$git_sha.env" "$deploy_root/current.env"
ln -sfn "releases/$git_sha.compose.yaml" "$deploy_root/compose.yaml"
echo "rolled back to $git_sha"
