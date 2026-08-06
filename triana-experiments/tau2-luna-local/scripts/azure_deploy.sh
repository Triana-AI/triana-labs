#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${AZURE_SUBSCRIPTION_ID:?required}"
: "${AZURE_RESOURCE_GROUP:?required}"
: "${AZURE_LOCATION:?required}"
: "${AZURE_VM_SSH_PUBLIC_KEY:?required public key}"
: "${AZURE_OPENAI_RESOURCE_GROUP:?required}"
: "${TAU2_VM_SIZE:?required exact Azure VM size}"
: "${AZURE_OPENAI_RESOURCE:=kairos-memory}"
: "${AZURE_TERRA_RESOURCE:=kairos-openai-1}"
: "${AZURE_LUNA_RESOURCE:=kairos-memory}"
: "${TAU2_NL_ASSERTIONS_DEPLOYMENT:=tau2-luna-smoke-20260805}"
: "${TAU2_LUNA_DEPLOYMENT:=gpt-5-6-luna-smoke}"
: "${TAU2_SMOKE_PREFIX:=tau2luna}"
: "${TAU2_DEPLOY_OUTPUT:?required new private JSON output path}"
: "${TAU2_EXECUTION_MODE:=discovery}"

model_name=gpt-5.6-luna
deployment_capacity=1
luna_deployment_capacity=10
TAU2_SEED_PREFIX=source/f8de30c298689cbe0117d76a378e7315a17e5bd8/
TAU2_SEED_ARCHIVE_NAME=tau2-luna-local.tar.gz
TAU2_SEED_DIGEST_NAME=tau2-luna-local.sha256
if test "${TAU2_LUNA_DEPLOYMENT}" = gpt-5-6-terra-sentinel; then
  AZURE_OPENAI_RESOURCE="${AZURE_TERRA_RESOURCE}"
  model_name=gpt-5.6-terra
  deployment_capacity=100
  TAU2_SEED_PREFIX=source/f8de30c298689cbe0117d76a378e7315a17e5bd8/terra-10-v2/
  TAU2_SEED_ARCHIVE_NAME=tau2-terra-10-v2.tar.gz
  TAU2_SEED_DIGEST_NAME=tau2-terra-10-v2.sha256
  if test "${TAU2_EXECUTION_MODE}" = discovery; then
    TAU2_SEED_PREFIX=source/f8de30c298689cbe0117d76a378e7315a17e5bd8/retail-discovery-v5/
    TAU2_SEED_ARCHIVE_NAME=tau2-retail-discovery-v5.tar.gz
    TAU2_SEED_DIGEST_NAME=tau2-retail-discovery-v5.sha256
  fi
fi

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
secret_file="$(mktemp)"
luna_secret_file="$(mktemp)"
storage_secret_file="$(mktemp)"
source_archive="$(mktemp)"
source_digest="$(mktemp)"
trap 'rm -f "${secret_file}" "${luna_secret_file}" "${storage_secret_file}" "${source_archive}" "${source_digest}"' EXIT

az account set --subscription "${AZURE_SUBSCRIPTION_ID}"
az group create --name "${AZURE_RESOURCE_GROUP}" --location "${AZURE_LOCATION}" --output none
operator_id="${AZURE_OPERATOR_OBJECT_ID:-}"
operator_type="${AZURE_OPERATOR_PRINCIPAL_TYPE:-}"
if test -z "${operator_id}" && test -z "${operator_type}"; then
  operator_id="$(az ad signed-in-user show --query id --output tsv)"
  operator_type=User
elif test -z "${operator_id}" || test -z "${operator_type}"; then
  printf '%s\n' 'AZURE_OPERATOR_OBJECT_ID and AZURE_OPERATOR_PRINCIPAL_TYPE must be set together' >&2
  exit 2
fi
case "${operator_type}" in User|ServicePrincipal) ;; *)
  printf '%s\n' 'AZURE_OPERATOR_PRINCIPAL_TYPE must be User or ServicePrincipal' >&2
  exit 2
esac
az cognitiveservices account deployment create \
  --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" \
  --name "${AZURE_OPENAI_RESOURCE}" \
  --deployment-name "${TAU2_LUNA_DEPLOYMENT}" \
  --model-format OpenAI --model-name "${model_name}" --model-version 2026-07-09 \
  --sku-name GlobalStandard --sku-capacity "${deployment_capacity}" --output none
if test "${TAU2_LUNA_DEPLOYMENT}" = gpt-5-6-terra-sentinel; then
  az cognitiveservices account deployment create \
    --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" \
    --name "${AZURE_LUNA_RESOURCE}" \
    --deployment-name "${TAU2_NL_ASSERTIONS_DEPLOYMENT}" \
    --model-format OpenAI --model-name gpt-5.6-luna --model-version 2026-07-09 \
    --sku-name GlobalStandard --sku-capacity "${luna_deployment_capacity}" --output none
fi

deployment_json="$(az deployment group create \
  --resource-group "${AZURE_RESOURCE_GROUP}" --name tau2-luna-smoke \
  --template-file "${project_dir}/infra/main.bicep" \
  --parameters prefix="${TAU2_SMOKE_PREFIX}" location="${AZURE_LOCATION}" \
  vmSize="${TAU2_VM_SIZE}" \
  sshPublicKey="${AZURE_VM_SSH_PUBLIC_KEY}" operatorObjectId="${operator_id}" \
  operatorPrincipalType="${operator_type}" \
  --query properties.outputs --output json)"
test ! -e "${TAU2_DEPLOY_OUTPUT}"
install -m 600 /dev/null "${TAU2_DEPLOY_OUTPUT}"
jq -S . <<<"${deployment_json}" >"${TAU2_DEPLOY_OUTPUT}"
vault_name="$(jq -r '.vaultName.value' <<<"${deployment_json}")"
storage_name="$(jq -r '.storageAccount.value' <<<"${deployment_json}")"
container_name="$(jq -r '.containerName.value' <<<"${deployment_json}")"

az keyvault secret list --vault-name "${vault_name}" --maxresults 1 --output none

az cognitiveservices account keys list --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" \
  --name "${AZURE_OPENAI_RESOURCE}" --query key1 --output tsv >"${secret_file}"
if test "${TAU2_LUNA_DEPLOYMENT}" = gpt-5-6-terra-sentinel; then
  az cognitiveservices account keys list --resource-group "${AZURE_OPENAI_RESOURCE_GROUP}" \
    --name "${AZURE_LUNA_RESOURCE}" --query key1 --output tsv >"${luna_secret_file}"
fi
az storage account keys list --resource-group "${AZURE_RESOURCE_GROUP}" \
  --account-name "${storage_name}" --query '[0].value' --output tsv >"${storage_secret_file}"
az keyvault secret set --vault-name "${vault_name}" --name azure-openai-key \
  --file "${secret_file}" --output none
if test "${TAU2_LUNA_DEPLOYMENT}" = gpt-5-6-terra-sentinel; then
  az keyvault secret set --vault-name "${vault_name}" --name azure-openai-luna-key \
    --file "${luna_secret_file}" --output none
fi
az keyvault secret set --vault-name "${vault_name}" --name storage-account-key \
  --file "${storage_secret_file}" --output none

tar -C "${project_dir}" --exclude .venv --exclude runs --exclude __pycache__ -czf "${source_archive}" .
openssl dgst -sha256 "${source_archive}" | awk '{print $NF}' >"${source_digest}"
AZURE_STORAGE_KEY_FILE="${storage_secret_file}" \
TAU2_SEED_STORAGE="${storage_name}" \
TAU2_SEED_CONTAINER="${container_name}" \
TAU2_SEED_ARCHIVE="${source_archive}" \
TAU2_SEED_DIGEST="${source_digest}" \
TAU2_SEED_PREFIX="${TAU2_SEED_PREFIX}" \
TAU2_SEED_ARCHIVE_NAME="${TAU2_SEED_ARCHIVE_NAME}" \
TAU2_SEED_DIGEST_NAME="${TAU2_SEED_DIGEST_NAME}" \
  uv run --quiet --frozen --directory "${project_dir}" python scripts/blob_seed.py
printf '%s\n' "Azure envelope deployed; VM remains private and the paid smoke has not run."
