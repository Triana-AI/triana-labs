#!/usr/bin/env bash
set -euo pipefail
: "${TAU2_SMOKE_STORAGE:?required}"
: "${TAU2_SMOKE_VAULT:?required}"
: "${TAU2_SMOKE_RUN_ID:?required}"
: "${TAU2_RELAY_DESTINATION:?required new private directory}"

test ! -e "${TAU2_RELAY_DESTINATION}"
umask 077
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
storage_key_dir="$(mktemp -d)"
storage_key_file="${storage_key_dir}/storage-account-key"
trap 'rm -f "${storage_key_file}"; rmdir "${storage_key_dir}"' EXIT
az keyvault secret download --vault-name "${TAU2_SMOKE_VAULT}" \
  --name storage-account-key --file "${storage_key_file}" --output none
AZURE_STORAGE_KEY_FILE="${storage_key_file}" \
  uv run --directory "${project_dir}" python scripts/cloud_relay.py
