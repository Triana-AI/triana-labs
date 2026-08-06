#!/usr/bin/env bash
set -euo pipefail
umask 077
: "${AZURE_RESOURCE_GROUP:?required}"
: "${TAU2_SMOKE_VM:?required}"
: "${TAU2_SMOKE_STORAGE:?required}"
: "${TAU2_SMOKE_VAULT_URI:?required}"
: "${AZURE_API_BASE:?required}"
: "${AZURE_API_VERSION:?required}"
: "${TAU2_LUNA_DEPLOYMENT:?required}"
: "${TAU2_LUNA_API_BASE:?required}"
: "${TAU2_LUNA_API_VERSION:?required}"
: "${TAU2_NL_ASSERTIONS_DEPLOYMENT:?required}"
: "${TAU2_SMOKE_RUN_ID:?required}"
: "${AZURE_OPENAI_RESOURCE_GROUP:?required}"
: "${AZURE_OPENAI_RESOURCE:=kairos-openai-1}"
: "${AZURE_LUNA_RESOURCE:=kairos-memory}"
[[ "${TAU2_SMOKE_RUN_ID}" =~ ^[A-Za-z0-9._-]+$ ]] || { printf '%s\n' 'run ID is invalid' >&2; exit 2; }

if test "${TAU2_LUNA_DEPLOYMENT}" != gpt-5-6-terra-sentinel || \
   test "${TAU2_NL_ASSERTIONS_DEPLOYMENT}" != tau2-luna-smoke-20260805 || \
   test "${TAU2_LUNA_API_BASE}" != https://kairos-memory.openai.azure.com/; then
  printf '%s\n' 'exact Terra/Luna discovery deployments are required' >&2
  exit 2
fi

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
result_file="$(mktemp)"
trap 'rm -f "${result_file}"' EXIT
terra_identity="$(az cognitiveservices account deployment show \
  --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" --name "${AZURE_OPENAI_RESOURCE}" \
  --deployment-name gpt-5-6-terra-sentinel \
  --query '{model_name:properties.model.name,model_version:properties.model.version,sku:sku.name,capacity:sku.capacity}' \
  --output json)"
jq -e --arg model gpt-5.6-terra '. == {model_name:$model,model_version:"2026-07-09",sku:"GlobalStandard",capacity:100}' \
  <<<"${terra_identity}" >/dev/null
luna_identity="$(az cognitiveservices account deployment show \
  --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" --name "${AZURE_LUNA_RESOURCE}" \
  --deployment-name tau2-luna-smoke-20260805 \
  --query '{model_name:properties.model.name,model_version:properties.model.version,sku:sku.name,capacity:sku.capacity}' \
  --output json)"
jq -e '. == {model_name:"gpt-5.6-luna",model_version:"2026-07-09",sku:"GlobalStandard",capacity:10}' \
  <<<"${luna_identity}" >/dev/null

az vm start --resource-group "${AZURE_RESOURCE_GROUP}" --name "${TAU2_SMOKE_VM}" --output none
az vm run-command invoke --resource-group "${AZURE_RESOURCE_GROUP}" --name "${TAU2_SMOKE_VM}" \
  --command-id RunShellScript --scripts @"${project_dir}/scripts/vm_discovery_bootstrap.sh" \
  --parameters "storage=${TAU2_SMOKE_STORAGE}" "vault=${TAU2_SMOKE_VAULT_URI}" \
  "api_base=${AZURE_API_BASE}" "api_version=${AZURE_API_VERSION}" \
  "deployment=${TAU2_LUNA_DEPLOYMENT}" "run_id=${TAU2_SMOKE_RUN_ID}" \
  "luna_api_base=${TAU2_LUNA_API_BASE}" "luna_api_version=${TAU2_LUNA_API_VERSION}" \
  "luna_deployment=${TAU2_NL_ASSERTIONS_DEPLOYMENT}" \
  --output json >"${result_file}"

jq -e --arg run_id "${TAU2_SMOKE_RUN_ID}" '
  any(
    .value[]?.message? | strings | split("\n")[] | try fromjson catch empty;
    type == "object" and .state == "RUNNING" and .run_id == $run_id and .blob_status_verified == true
  )
' "${result_file}" >/dev/null
printf '%s\n' "Discovery service RUNNING with verified Blob handoff for ${TAU2_SMOKE_RUN_ID}"
