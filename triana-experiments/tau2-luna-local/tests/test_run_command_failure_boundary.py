from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VM_SCRIPT = PROJECT_ROOT / "scripts" / "vm_smoke.sh"
DISCOVERY_BOOTSTRAP = PROJECT_ROOT / "scripts" / "vm_discovery_bootstrap.sh"
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "azure_run.sh"


def _bootstrap_download_code() -> str:
    match = re.search(r"^download='(?P<code>.*)'$", VM_SCRIPT.read_text(), flags=re.MULTILINE)
    assert match is not None
    return match.group("code")


def test_bootstrap_download_snippet_compiles() -> None:
    python = shutil.which("python3.10")
    assert python is not None, "Ubuntu 22.04 bootstrap grammar requires a Python 3.10 compiler"
    completed = subprocess.run(
        [python, "-c", "import sys; compile(sys.stdin.read(), 'vm_smoke.bootstrap_download', 'exec')"],
        input=_bootstrap_download_code(),
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_bootstrap_download_failure_is_nonzero_and_not_a_syntax_error(tmp_path: Path) -> None:
    fake_modules = tmp_path / "modules"
    (fake_modules / "azure" / "storage").mkdir(parents=True)
    (fake_modules / "azure" / "keyvault").mkdir(parents=True)
    (fake_modules / "azure" / "__init__.py").write_text("")
    (fake_modules / "azure" / "storage" / "__init__.py").write_text("")
    (fake_modules / "azure" / "keyvault" / "__init__.py").write_text("")
    (fake_modules / "azure" / "identity.py").write_text(
        "class DefaultAzureCredential:\n    def __init__(self, **kwargs): pass\n"
    )
    (fake_modules / "azure" / "keyvault" / "secrets.py").write_text(
        "class SecretClient:\n"
        "    def __init__(self, **kwargs): pass\n"
        "    def get_secret(self, name): return type('Secret', (), {'value': 'storage-key'})()\n"
    )
    (fake_modules / "azure" / "storage" / "blob.py").write_text(
        "class BlobClient:\n"
        "    def __init__(self, **kwargs): pass\n"
        "    def download_blob(self): return self\n"
        "    def readinto(self, target): raise RuntimeError('synthetic download failure')\n"
    )
    destination = tmp_path / "source.tar.gz"
    completed = subprocess.run(
        [sys.executable, "-c", _bootstrap_download_code()],
        env={
            **os.environ,
            "PYTHONPATH": str(fake_modules),
            "TAU2_BOOTSTRAP_STORAGE": "fakestorage",
            "TAU2_BOOTSTRAP_BLOB": "source/frozen/source.tar.gz",
            "TAU2_BOOTSTRAP_VAULT": "https://fake-vault.vault.azure.net",
            "TAU2_BOOTSTRAP_DEST": str(destination),
        },
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode != 0
    assert "synthetic download failure" in completed.stderr
    assert "SyntaxError" not in completed.stderr


def test_run_command_provisioning_success_without_terminal_evidence_is_failure(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    command_log = tmp_path / "az.log"
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_AZ_LOG}"
case "$*" in
  *"deployment-name tau2-luna-smoke-20260805"*)
    printf '%s' '{"model_name":"gpt-5.6-luna","model_version":"2026-07-09",'
    printf '%s\n' '"sku":"GlobalStandard","capacity":10}'
    ;;
  *"deployment-name gpt-5-6-terra-sentinel"*)
    printf '%s' '{"model_name":"gpt-5.6-terra","model_version":"2026-07-09",'
    printf '%s\n' '"sku":"GlobalStandard","capacity":100}'
    ;;
  *"vm run-command invoke"*)
    printf '%s' '{"provisioningState":"Succeeded","value":['
    printf '%s\n' '{"code":"ProvisioningState/succeeded","message":"guest result unavailable"}]}'
    ;;
esac
"""
    )
    fake_az.chmod(0o700)
    environment = {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_AZ_LOG": str(command_log),
        "AZURE_RESOURCE_GROUP": "tau2-test-rg",
        "TAU2_SMOKE_VM": "tau2-test-vm",
        "TAU2_SMOKE_STORAGE": "fakestorage",
        "TAU2_SMOKE_VAULT_URI": "https://fake-vault.vault.azure.net",
        "AZURE_API_BASE": "https://unit.openai.azure.com",
        "AZURE_API_VERSION": "2026-01-01-preview",
        "TAU2_LUNA_DEPLOYMENT": "gpt-5-6-terra-sentinel",
        "TAU2_LUNA_API_BASE": "https://kairos-memory.openai.azure.com/",
        "TAU2_LUNA_API_VERSION": "2026-01-01-preview",
        "TAU2_NL_ASSERTIONS_DEPLOYMENT": "tau2-luna-smoke-20260805",
        "TAU2_SMOKE_RUN_ID": "run-1",
        "TAU2_SMOKE_TASK_ID": "18",
        "AZURE_OPENAI_RESOURCE_GROUP": "existing-openai-rg",
    }
    completed = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert completed.returncode != 0
    commands = command_log.read_text()
    assert "vm run-command invoke" in commands
    for forbidden in ("vm auto-shutdown", "vm deallocate", "vm delete", "group delete"):
        assert forbidden not in commands


def _panel_environment(fake_bin: Path, command_log: Path) -> dict[str, str]:
    return {
        **os.environ,
        "PATH": f"{fake_bin}:{os.environ['PATH']}",
        "FAKE_AZ_LOG": str(command_log),
        "AZURE_RESOURCE_GROUP": "tau2-test-rg",
        "TAU2_SMOKE_VM": "tau2-test-vm",
        "TAU2_SMOKE_STORAGE": "fakestorage",
        "TAU2_SMOKE_VAULT_URI": "https://fake-vault.vault.azure.net",
        "AZURE_API_BASE": "https://unit.openai.azure.com",
        "AZURE_API_VERSION": "2026-01-01-preview",
        "TAU2_LUNA_DEPLOYMENT": "gpt-5-6-terra-sentinel",
        "TAU2_LUNA_API_BASE": "https://kairos-memory.openai.azure.com/",
        "TAU2_LUNA_API_VERSION": "2026-01-01-preview",
        "TAU2_NL_ASSERTIONS_DEPLOYMENT": "tau2-luna-smoke-20260805",
        "TAU2_SMOKE_RUN_ID": "panel-run",
        "TAU2_SMOKE_TASK_ID": "83",
        "AZURE_OPENAI_RESOURCE_GROUP": "existing-openai-rg",
    }


def _write_panel_fake_az(fake_bin: Path) -> None:
    fake_az = fake_bin / "az"
    fake_az.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_AZ_LOG}"
case "$*" in
  *"deployment-name tau2-luna-smoke-20260805"*)
    printf '%s' '{"model_name":"gpt-5.6-luna","model_version":"2026-07-09",'
    printf '%s\n' '"sku":"GlobalStandard","capacity":10}'
    ;;
  *"deployment-name gpt-5-6-terra-sentinel"*)
    printf '%s' '{"model_name":"gpt-5.6-terra","model_version":"2026-07-09",'
    printf '%s\n' '"sku":"GlobalStandard","capacity":100}'
    ;;
  *"vm run-command invoke"*)
    printf '%s' '{"value":[{"message":"{\\"state\\":\\"'
    printf '%s' "${FAKE_TERMINAL_STATE}"
    printf '%s' '\\",\\"run_id\\":\\"panel-run\\",\\"blob_status_verified\\":'
    printf '%s' "${FAKE_BLOB_STATUS_VERIFIED}"
    printf '%s' '}\\n"}]}'
    ;;
esac
"""
    )
    fake_az.chmod(0o700)


def test_malformed_run_id_refuses_before_any_azure_call(tmp_path: Path) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    command_log = tmp_path / "az.log"
    _write_panel_fake_az(fake_bin)
    environment = _panel_environment(fake_bin, command_log)
    environment.update(
        {
            "TAU2_SMOKE_RUN_ID": "../invalid-run",
            "FAKE_TERMINAL_STATE": "RUNNING",
            "FAKE_BLOB_STATUS_VERIFIED": "true",
        }
    )

    completed = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode != 0
    assert "run ID is invalid" in completed.stderr
    assert not command_log.exists(), "malformed run identity must refuse before Azure operations"


@pytest.mark.parametrize(
    ("variable", "invalid"),
    [
        ("TAU2_LUNA_DEPLOYMENT", "wrong-terra"),
        ("TAU2_NL_ASSERTIONS_DEPLOYMENT", "wrong-luna"),
        ("TAU2_LUNA_API_BASE", "https://wrong.openai.azure.com/"),
    ],
)
def test_nonexact_discovery_model_configuration_refuses_before_azure_calls(
    tmp_path: Path,
    variable: str,
    invalid: str,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    command_log = tmp_path / "az.log"
    _write_panel_fake_az(fake_bin)
    environment = _panel_environment(fake_bin, command_log)
    environment.update(
        {
            "FAKE_TERMINAL_STATE": "RUNNING",
            "FAKE_BLOB_STATUS_VERIFIED": "true",
            variable: invalid,
        }
    )

    completed = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode != 0
    assert "exact Terra/Luna discovery deployments are required" in completed.stderr
    assert not command_log.exists(), "nonexact model config must refuse before Azure operations"


@pytest.mark.parametrize(
    ("terminal_state", "expected_returncode"),
    [("RUNNING", 0), ("PARTIAL", 1)],
)
def test_one_detached_bootstrap_requires_running_blob_handoff_and_retains_resources(
    tmp_path: Path,
    terminal_state: str,
    expected_returncode: int,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    command_log = tmp_path / "az.log"
    _write_panel_fake_az(fake_bin)
    environment = _panel_environment(fake_bin, command_log)
    environment.update(
        {
            "FAKE_TERMINAL_STATE": terminal_state,
            "FAKE_BLOB_STATUS_VERIFIED": "true",
        }
    )

    completed = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert completed.returncode == expected_returncode
    commands = command_log.read_text().splitlines()
    start = next(index for index, command in enumerate(commands) if "vm start" in command)
    run_commands = [
        (index, command) for index, command in enumerate(commands) if "vm run-command invoke" in command
    ]
    assert len(run_commands) == 1
    run_index, run_command = run_commands[0]
    assert start < run_index
    assert "vm_discovery_bootstrap.sh" in run_command
    assert "task_id=" not in run_command
    for forbidden in ("vm auto-shutdown", "vm deallocate", "vm delete", "group delete"):
        assert all(forbidden not in command for command in commands)

    run_source = RUN_SCRIPT.read_text()
    assert re.search(r"\bdate\b", run_source) is None
    assert run_source.count("vm run-command invoke") == 1
    for forbidden in ("vm auto-shutdown", "vm deallocate", "vm delete", "group delete"):
        assert forbidden not in run_source
    bootstrap_source = DISCOVERY_BOOTSTRAP.read_text()
    assert "systemctl enable --now" in bootstrap_source
    assert "RUNNING" in bootstrap_source
