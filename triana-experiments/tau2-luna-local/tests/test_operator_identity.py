from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
BICEP_TEMPLATE = PROJECT_ROOT / "infra" / "main.bicep"


def test_deploy_uses_explicit_service_principal_without_signed_in_user_discovery(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    az_log = tmp_path / "az.log"
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_AZ_LOG}"
case "$*" in
  *"ad signed-in-user show"*) exit 97 ;;
  *"deployment group create"*)
    printf '%s' '{"vaultName":{"value":"fake-vault"},'
    printf '%s\n' '"storageAccount":{"value":"fakestorage"},"containerName":{"value":"tau2-smoke"}}'
    ;;
  *"cognitiveservices account keys list"*) printf '%s\n' 'synthetic-key' ;;
  *"storage account keys list"*) printf '%s\n' 'synthetic-storage-key' ;;
esac
"""
    )
    fake_az.chmod(0o700)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
test -f "${AZURE_STORAGE_KEY_FILE}"
test "$(tr -d '\n' < "${AZURE_STORAGE_KEY_FILE}")" = synthetic-storage-key
test "${TAU2_SEED_PREFIX}" = source/f8de30c298689cbe0117d76a378e7315a17e5bd8/retail-discovery-v5/
test "${TAU2_SEED_ARCHIVE_NAME}" = tau2-retail-discovery-v5.tar.gz
test "${TAU2_SEED_DIGEST_NAME}" = tau2-retail-discovery-v5.sha256
test "$*" = "run --quiet --frozen --directory ${FAKE_PROJECT_ROOT} python scripts/blob_seed.py"
printf '%s\n' blob-seed >> "${FAKE_AZ_LOG}"
"""
    )
    fake_uv.chmod(0o700)
    fake_tar = fake_bin / "tar"
    fake_tar.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
archive=''
while test "$#" -gt 0; do
  case "$1" in -czf) archive="$2"; shift 2 ;; *) shift ;; esac
done
test -n "${archive}"
printf '%s\n' synthetic-discovery-v5-archive > "${archive}"
"""
    )
    fake_tar.chmod(0o700)
    output = tmp_path / "deploy-output.json"
    explicit_id = "11111111-2222-3333-4444-555555555555"
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_AZ_LOG": str(az_log),
        "FAKE_PROJECT_ROOT": str(PROJECT_ROOT),
        "AZURE_SUBSCRIPTION_ID": "subscription-test",
        "AZURE_RESOURCE_GROUP": "tau2-test-rg",
        "AZURE_LOCATION": "eastus2",
        "TAU2_VM_SIZE": "Standard_D2as_v5",
        "AZURE_VM_SSH_PUBLIC_KEY": "ssh-ed25519 synthetic-test-key",
        "AZURE_OPENAI_RESOURCE_GROUP": "existing-openai-rg",
        "TAU2_LUNA_DEPLOYMENT": "gpt-5-6-terra-sentinel",
        "TAU2_EXECUTION_MODE": "discovery",
        "TAU2_DEPLOY_OUTPUT": str(output),
        "AZURE_OPERATOR_OBJECT_ID": explicit_id,
        "AZURE_OPERATOR_PRINCIPAL_TYPE": "ServicePrincipal",
    }

    completed = subprocess.run(
        ["bash", str(DEPLOY_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    commands = az_log.read_text()
    assert "ad signed-in-user show" not in commands
    deployment = next(line for line in commands.splitlines() if "deployment group create" in line)
    assert f"operatorObjectId={explicit_id}" in deployment
    assert "operatorPrincipalType=ServicePrincipal" in deployment
    assert "vmSize=Standard_D2as_v5" in deployment
    assert "blob-seed" in commands
    deploy_source = DEPLOY_SCRIPT.read_text()
    assert "retail-discovery-v5" in deploy_source
    assert "tau2-retail-discovery-v5.tar.gz" in deploy_source
    assert output.is_file()


def test_bicep_uses_key_vault_access_policies_and_no_role_assignments() -> None:
    template = BICEP_TEMPLATE.read_text()
    assert "Microsoft.Authorization/roleAssignments" not in template
    assert "allowSharedKeyAccess: true" in template
    assert "allowBlobPublicAccess: false" in template
    assert re.search(r"publicAccess:\s*'None'", template)
    assert "enableRbacAuthorization: false" in template
    assert "accessPolicies:" in template
    assert "objectId: operatorObjectId" in template
    assert "objectId: vm.identity.principalId" in template
