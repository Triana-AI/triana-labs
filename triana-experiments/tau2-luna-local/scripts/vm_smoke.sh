#!/usr/bin/env bash
set -euo pipefail
umask 077
export HOME=/root
test "$#" -eq 9
export TAU2_SMOKE_STORAGE="$1"
export TAU2_SMOKE_VAULT_URI="$2"
export AZURE_API_BASE="$3"
export AZURE_API_VERSION="$4"
export TAU2_LUNA_DEPLOYMENT="$5"
export TAU2_SMOKE_RUN_ID="$6"
export TAU2_LUNA_API_BASE="$7"
export TAU2_LUNA_API_VERSION="$8"
export TAU2_NL_ASSERTIONS_DEPLOYMENT="$9"

work_dir=/opt/tau2-luna-smoke
mkdir -p "${work_dir}"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ca-certificates curl git python3-venv
python3 -m venv "${work_dir}/bootstrap"
"${work_dir}/bootstrap/bin/pip" install --quiet \
  azure-identity==1.25.1 azure-keyvault-secrets==4.10.0 azure-storage-blob==12.27.1
download='import os; from azure.identity import DefaultAzureCredential; from azure.keyvault.secrets import SecretClient; from azure.storage.blob import BlobClient; identity=DefaultAzureCredential(exclude_interactive_browser_credential=True); key=SecretClient(vault_url=os.environ["TAU2_BOOTSTRAP_VAULT"], credential=identity).get_secret("storage-account-key").value; account_url="https://" + os.environ["TAU2_BOOTSTRAP_STORAGE"] + ".blob.core.windows.net"; BlobClient(account_url=account_url, container_name="tau2-smoke", blob_name=os.environ["TAU2_BOOTSTRAP_BLOB"], credential=key).download_blob().readinto(open(os.environ["TAU2_BOOTSTRAP_DEST"], "wb"))'
source_prefix=source/f8de30c298689cbe0117d76a378e7315a17e5bd8/terra-10-v2
for object in tau2-terra-10-v2.tar.gz tau2-terra-10-v2.sha256; do
  TAU2_BOOTSTRAP_STORAGE="${TAU2_SMOKE_STORAGE}" TAU2_BOOTSTRAP_BLOB="${source_prefix}/${object}" \
    TAU2_BOOTSTRAP_VAULT="${TAU2_SMOKE_VAULT_URI}" \
    TAU2_BOOTSTRAP_DEST="${work_dir}/${object}" "${work_dir}/bootstrap/bin/python" -c "${download}"
done
test "$(sha256sum "${work_dir}/tau2-terra-10-v2.tar.gz" | awk '{print $1}')" = \
  "$(tr -d '[:space:]' <"${work_dir}/tau2-terra-10-v2.sha256")"
project_dir="$(mktemp -d "${work_dir}/project.XXXXXX")"
tar -xzf "${work_dir}/tau2-terra-10-v2.tar.gz" -C "${project_dir}"
if test ! -d "${work_dir}/tau2-source/.git"; then
  git clone https://github.com/sierra-research/tau2-bench.git "${work_dir}/tau2-source"
  git -C "${work_dir}/tau2-source" checkout --detach f8de30c298689cbe0117d76a378e7315a17e5bd8
fi
test "$(git -C "${work_dir}/tau2-source" rev-parse HEAD)" = f8de30c298689cbe0117d76a378e7315a17e5bd8
git -C "${work_dir}/tau2-source" diff --quiet
git -C "${work_dir}/tau2-source" diff --cached --quiet
printf '%s\n' '{"repository":"https://github.com/sierra-research/tau2-bench","commit":"f8de30c298689cbe0117d76a378e7315a17e5bd8"}' \
  >"${work_dir}/tau2-source/.tau2-source.json"
curl -LsSf https://astral.sh/uv/0.12.0/install.sh | sh
"${HOME}/.local/bin/uv" sync --locked --directory "${project_dir}"

export TAU2_TRACE_ROOT="${work_dir}/runs"
export TAU2_SOURCE_DIR="${work_dir}/tau2-source"
export TAU2_DATA_DIR="${work_dir}/tau2-source/data"
"${HOME}/.local/bin/uv" run --directory "${project_dir}" \
  python scripts/cloud_worker.py
