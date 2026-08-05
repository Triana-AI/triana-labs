#!/bin/sh

set -eu

if [ "$#" -ne 4 ]; then
  echo "usage: deploy.sh <backend-image@digest> <app-image@digest> <git-sha> <compose-source>" >&2
  exit 64
fi

backend_image=$1
app_image=$2
git_sha=$3
compose_source=$4
deploy_root=${TRIANA_DEPLOY_ROOT:-/opt/triana}
runtime_env="$deploy_root/.env"
releases_dir="$deploy_root/releases"
release_file="$releases_dir/$git_sha.env"
release_compose="$releases_dir/$git_sha.compose.yaml"
current_link="$deploy_root/current.env"
compose_link="$deploy_root/compose.yaml"
lock_file="$deploy_root/deploy.lock"

validate_image() {
  digest=${1##*@sha256:}
  case "$1" in
    *@sha256:*) ;;
    *) echo "image must use a sha256 digest" >&2; exit 65 ;;
  esac
  if [ "${#digest}" -ne 64 ]; then
    echo "image digest must contain 64 hexadecimal characters" >&2
    exit 65
  fi
  case "$digest" in
    *[!0-9a-f]*) echo "image digest must be lowercase hexadecimal" >&2; exit 65 ;;
  esac
}

validate_image "$backend_image"
validate_image "$app_image"
if [ "${#git_sha}" -ne 40 ]; then
  echo "git SHA must be exactly 40 lowercase hexadecimal characters" >&2
  exit 65
fi
case "$git_sha" in
  *[!0-9a-f]*) echo "git SHA must be lowercase hexadecimal" >&2; exit 65 ;;
esac

[ -f "$runtime_env" ] || { echo "missing $runtime_env" >&2; exit 66; }
[ -f "$compose_source" ] || { echo "missing compose source" >&2; exit 66; }
command -v aws >/dev/null
command -v docker >/dev/null
command -v flock >/dev/null
command -v curl >/dev/null

mkdir -p "$releases_dir"
chmod 700 "$deploy_root" "$releases_dir"
chmod 600 "$runtime_env"
exec 9>"$lock_file"
flock -n 9 || { echo "another deployment is active" >&2; exit 75; }

registry=${backend_image%%/*}
app_registry=${app_image%%/*}
[ "$registry" = "$app_registry" ] || { echo "images must use one ECR registry" >&2; exit 65; }
region=$(sed -n 's/^AWS_REGION=//p' "$runtime_env" | tail -1)
[ -n "$region" ] || { echo "AWS_REGION is missing from runtime env" >&2; exit 66; }
aws ecr get-login-password --region "$region" \
  | docker login --username AWS --password-stdin "$registry" >/dev/null

docker pull "$backend_image"
docker pull "$app_image"

previous_release=
if [ -L "$current_link" ]; then
  previous_release=$(readlink "$current_link")
fi

candidate=$(mktemp "$releases_dir/.candidate.XXXXXX")
trap 'rm -f "$candidate"' EXIT HUP INT TERM
{
  printf 'TRIANA_BACKEND_IMAGE=%s\n' "$backend_image"
  printf 'TRIANA_APP_IMAGE=%s\n' "$app_image"
  printf 'TRIANA_GIT_SHA=%s\n' "$git_sha"
  printf 'TRIANA_RUNTIME_ENV_FILE=%s\n' "$runtime_env"
  printf 'TRIANA_COMPOSE_FILE=%s\n' "$release_compose"
  printf 'TRIANA_PREVIOUS_RELEASE=%s\n' "$previous_release"
} >"$candidate"
chmod 600 "$candidate"

docker network inspect triana_default >/dev/null 2>&1 \
  || docker network create triana_default >/dev/null

# Migrations happen once, before either long-running service is replaced.
docker run --rm \
  --network triana_default \
  --env-file "$runtime_env" \
  "$backend_image" \
  alembic -c /app/alembic.ini upgrade head

install -m 0644 "$compose_source" "$release_compose"
cp "$candidate" "$release_file"
chmod 600 "$release_file"

deployment_ok=true
docker compose \
  --project-name triana \
  --env-file "$release_file" \
  --file "$release_compose" \
  up --detach --remove-orphans --wait --wait-timeout 180 \
  || deployment_ok=false
if [ "$deployment_ok" = true ]; then
  curl --fail --silent --show-error --max-time 10 \
    http://127.0.0.1:8000/healthz >/dev/null \
    || deployment_ok=false
fi
if [ "$deployment_ok" = true ]; then
  curl --fail --silent --show-error --max-time 10 \
    http://127.0.0.1:3000/setup >/dev/null \
    || deployment_ok=false
fi

if [ "$deployment_ok" != true ]; then
  mv "$release_file" "$release_file.failed"
  mv "$release_compose" "$release_compose.failed"
  if [ -n "$previous_release" ] && [ -f "$deploy_root/$previous_release" ]; then
    previous_compose=$(sed -n 's/^TRIANA_COMPOSE_FILE=//p' "$deploy_root/$previous_release" | tail -1)
    [ -f "$previous_compose" ] \
      || { echo "previous release compose metadata is unavailable" >&2; exit 1; }
    docker compose \
      --project-name triana \
      --env-file "$deploy_root/$previous_release" \
      --file "$previous_compose" \
      up --detach --remove-orphans --wait --wait-timeout 180
  fi
  exit 1
fi

ln -sfn "releases/$git_sha.env" "$current_link"
ln -sfn "releases/$git_sha.compose.yaml" "$compose_link"
trap - EXIT HUP INT TERM
rm -f "$candidate"
echo "deployed $git_sha"
