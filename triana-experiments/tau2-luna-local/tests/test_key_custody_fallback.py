from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "azure_run.sh"
RELAY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_relay.sh"
WORKER_SCRIPT = PROJECT_ROOT / "scripts" / "cloud_worker.py"
AOAI_SECRET = "synthetic-aoai-key-must-not-print"
LUNA_SECRET = "synthetic-luna-key-must-not-print"
STORAGE_SECRET = "synthetic-storage-key-must-not-print"


def _write_fake_az(fake_bin: Path) -> tuple[Path, Path]:
    command_log = fake_bin.parent / "az.log"
    audit_log = fake_bin.parent / "secret-audit.log"
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_AZ_LOG}"
case "$*" in
  *"deployment group create"*)
    printf '%s' '{"vaultName":{"value":"fake-vault"},'
    printf '%s\n' '"storageAccount":{"value":"fakestorage"},"containerName":{"value":"tau2-smoke"}}'
    ;;
  *"cognitiveservices account keys list"*)
    case "$*" in
      *"--name kairos-memory"*) printf '%s\n' "${FAKE_LUNA_SECRET}" ;;
      *) printf '%s\n' "${FAKE_AOAI_SECRET}" ;;
    esac
    ;;
  *"storage account keys list"*) printf '%s\n' "${FAKE_STORAGE_SECRET}" ;;
  *"keyvault secret set"*)
    name=''
    file=''
    while test "$#" -gt 0; do
      case "$1" in
        --name) name="$2"; shift 2 ;;
        --file) file="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    value="$(cat "${file}")"
    case "${name}:${value}" in
      "azure-openai-key:${FAKE_AOAI_SECRET}") printf '%s\n' azure-openai-key >> "${FAKE_SECRET_AUDIT}" ;;
      "azure-openai-luna-key:${FAKE_LUNA_SECRET}")
        printf '%s\n' azure-openai-luna-key >> "${FAKE_SECRET_AUDIT}"
        ;;
      "storage-account-key:${FAKE_STORAGE_SECRET}")
        printf '%s\n' storage-account-key >> "${FAKE_SECRET_AUDIT}"
        ;;
      *) exit 91 ;;
    esac
    ;;
esac
"""
    )
    fake_az.chmod(0o700)
    return command_log, audit_log


def test_deploy_stores_both_keys_from_files_without_output_or_artifact_leak(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    command_log, audit_log = _write_fake_az(fake_bin)
    seed_audit = tmp_path / "seed-audit.log"
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
test -f "${AZURE_STORAGE_KEY_FILE}"
test "$(tr -d '\n' < "${AZURE_STORAGE_KEY_FILE}")" = "${FAKE_STORAGE_SECRET}"
test -f "${TAU2_SEED_ARCHIVE}"
test -f "${TAU2_SEED_DIGEST}"
test "${TAU2_SEED_PREFIX}" = source/f8de30c298689cbe0117d76a378e7315a17e5bd8/retail-discovery-v5/
test "${TAU2_SEED_ARCHIVE_NAME}" = tau2-retail-discovery-v5.tar.gz
test "${TAU2_SEED_DIGEST_NAME}" = tau2-retail-discovery-v5.sha256
test "$*" = "run --quiet --frozen --directory ${FAKE_PROJECT_ROOT} python scripts/blob_seed.py"
printf '%s\n' "${TAU2_SEED_STORAGE}/${TAU2_SEED_CONTAINER}" > "${FAKE_SEED_AUDIT}"
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
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_AZ_LOG": str(command_log),
        "FAKE_SECRET_AUDIT": str(audit_log),
        "FAKE_AOAI_SECRET": AOAI_SECRET,
        "FAKE_LUNA_SECRET": LUNA_SECRET,
        "FAKE_STORAGE_SECRET": STORAGE_SECRET,
        "FAKE_SEED_AUDIT": str(seed_audit),
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
        "AZURE_OPERATOR_OBJECT_ID": "11111111-2222-3333-4444-555555555555",
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
    assert audit_log.read_text().splitlines() == [
        "azure-openai-key",
        "azure-openai-luna-key",
        "storage-account-key",
    ]
    observable = completed.stdout + completed.stderr + command_log.read_text() + output.read_text()
    assert AOAI_SECRET not in observable
    assert LUNA_SECRET not in observable
    assert STORAGE_SECRET not in observable
    commands = command_log.read_text()
    assert "keyvault secret set" in commands
    assert "--file" in commands
    assert "--output none" in commands
    assert "retail-discovery-v5" in DEPLOY_SCRIPT.read_text()
    assert seed_audit.read_text().strip() == "fakestorage/tau2-smoke"


def test_worker_gets_both_keys_from_vault_and_blob_uses_storage_key(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    requested: list[str] = []
    blob_credentials: list[Any] = []

    identity_module = ModuleType("azure.identity")
    identity_module.DefaultAzureCredential = lambda **_: "managed-identity"  # type: ignore[attr-defined]
    secrets_module = ModuleType("azure.keyvault.secrets")

    class SecretClient:
        def __init__(self, **_: Any) -> None:
            pass

        def get_secret(self, name: str) -> SimpleNamespace:
            requested.append(name)
            values = {"azure-openai-key": AOAI_SECRET, "storage-account-key": STORAGE_SECRET}
            return SimpleNamespace(value=values[name])

    secrets_module.SecretClient = SecretClient  # type: ignore[attr-defined]
    blob_module = ModuleType("azure.storage.blob")

    class BlobServiceClient:
        def __init__(self, *, account_url: str, credential: Any) -> None:
            assert account_url == "https://fakestorage.blob.core.windows.net"
            blob_credentials.append(credential)

        def get_container_client(self, name: str) -> SimpleNamespace:
            assert name == "tau2-smoke"
            return SimpleNamespace()

    blob_module.BlobServiceClient = BlobServiceClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "azure.identity", identity_module)
    monkeypatch.setitem(sys.modules, "azure.keyvault.secrets", secrets_module)
    monkeypatch.setitem(sys.modules, "azure.storage.blob", blob_module)

    from tau2_luna_local.cloud_smoke import managed_identity_clients

    _, api_key = managed_identity_clients(
        account_url="https://fakestorage.blob.core.windows.net",
        container="tau2-smoke",
        vault_url="https://fake-vault.vault.azure.net",
        secret_name="azure-openai-key",
        storage_secret_name="storage-account-key",
    )
    assert requested == ["azure-openai-key", "storage-account-key"]
    assert blob_credentials == [STORAGE_SECRET]
    assert api_key == AOAI_SECRET
    output = capsys.readouterr().out
    assert AOAI_SECRET not in output
    assert STORAGE_SECRET not in output
    assert 'storage_secret_name="storage-account-key"' in WORKER_SCRIPT.read_text()


def test_relay_retrieves_storage_key_to_private_file_without_output(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    key_path_log = tmp_path / "key-path.log"
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
file=''
while test "$#" -gt 0; do
  case "$1" in --file) file="$2"; shift 2 ;; *) shift ;; esac
done
test -n "${file}"
printf '%s\n' "${FAKE_STORAGE_SECRET}" > "${file}"
"""
    )
    fake_az.chmod(0o700)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
test -f "${AZURE_STORAGE_KEY_FILE}"
test "$(tr -d '\n' < "${AZURE_STORAGE_KEY_FILE}")" = "${FAKE_STORAGE_SECRET}"
printf '%s\n' "${AZURE_STORAGE_KEY_FILE}" > "${FAKE_KEY_PATH_LOG}"
"""
    )
    fake_uv.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_STORAGE_SECRET": STORAGE_SECRET,
        "FAKE_KEY_PATH_LOG": str(key_path_log),
        "TAU2_SMOKE_STORAGE": "fakestorage",
        "TAU2_SMOKE_VAULT": "fake-vault",
        "TAU2_SMOKE_RUN_ID": "run-1",
        "TAU2_SMOKE_ATTEMPT_ID": "attempt-1",
        "TAU2_RELAY_DESTINATION": str(tmp_path / "relay"),
    }
    completed = subprocess.run(
        ["bash", str(RELAY_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert STORAGE_SECRET not in completed.stdout + completed.stderr
    key_file = Path(key_path_log.read_text().strip())
    assert not key_file.exists()


def test_relay_key_download_target_is_writable_and_cleaned_without_control_plane_scope(
    tmp_path: Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    key_path_log = tmp_path / "key-path.log"
    relay_call_log = tmp_path / "relay-call.log"
    az_call_log = tmp_path / "az-call.log"
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_AZ_CALL_LOG}"
file=''
overwrite=false
while test "$#" -gt 0; do
  case "$1" in
    --file) file="$2"; shift 2 ;;
    --overwrite) overwrite=true; shift ;;
    *) shift ;;
  esac
done
test -n "${file}"
if test -e "${file}" && test "${overwrite}" != true; then
  printf '%s\n' 'Refusing to overwrite existing file' >&2
  exit 73
fi
printf '%s\n' "${FAKE_STORAGE_SECRET}" > "${file}"
"""
    )
    fake_az.chmod(0o700)
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
test -f "${AZURE_STORAGE_KEY_FILE}"
test "$(tr -d '\n' < "${AZURE_STORAGE_KEY_FILE}")" = "${FAKE_STORAGE_SECRET}"
printf '%s\n' "${AZURE_STORAGE_KEY_FILE}" > "${FAKE_KEY_PATH_LOG}"
printf '%s\n' "$*" >> "${FAKE_RELAY_CALL_LOG}"
"""
    )
    fake_uv.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_STORAGE_SECRET": STORAGE_SECRET,
        "FAKE_KEY_PATH_LOG": str(key_path_log),
        "FAKE_RELAY_CALL_LOG": str(relay_call_log),
        "FAKE_AZ_CALL_LOG": str(az_call_log),
        "TAU2_SMOKE_STORAGE": "fakestorage",
        "TAU2_SMOKE_VAULT": "fake-vault",
        "TAU2_SMOKE_RUN_ID": "completed-panel-run",
        "TAU2_RELAY_DESTINATION": str(tmp_path / "relay"),
    }

    completed = subprocess.run(
        ["bash", str(RELAY_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    key_file = Path(key_path_log.read_text().strip())
    assert not key_file.exists()
    assert relay_call_log.read_text().splitlines() == [
        f"run --directory {PROJECT_ROOT} python scripts/cloud_relay.py"
    ]
    assert len(az_call_log.read_text().splitlines()) == 1
    relay_source = RELAY_SCRIPT.read_text()
    assert "TAU2_SMOKE_ATTEMPT_ID" not in relay_source
    assert "az vm" not in relay_source
    assert relay_source.count("python scripts/cloud_relay.py") == 1


def test_run_command_and_artifact_paths_never_carry_storage_or_openai_keys() -> None:
    run_script = RUN_SCRIPT.read_text()
    invocation = run_script[run_script.index("az vm run-command invoke") :]
    assert "AZURE_API_KEY" not in invocation
    assert "AZURE_STORAGE_KEY" not in invocation
    assert "storage-account-key" not in invocation
    assert "azure-openai-key" not in invocation
    assert "--parameters" in invocation
    assert json.dumps({"api_key": AOAI_SECRET, "storage_key": STORAGE_SECRET}) not in invocation
