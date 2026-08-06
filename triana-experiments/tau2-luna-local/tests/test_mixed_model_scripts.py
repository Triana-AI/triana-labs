from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER = PROJECT_ROOT / "scripts" / "cloud_worker.py"
AZURE_RUN = PROJECT_ROOT / "scripts" / "azure_run.sh"
AZURE_DEPLOY = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
VM_SMOKE = PROJECT_ROOT / "scripts" / "vm_smoke.sh"
CHECKPOINT_DOMAIN = b"tau2-luna-cloud-checkpoint:v1\0"


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_worker_routes_explicit_model_limits_to_separate_budgets_and_limiters() -> None:
    source = WORKER.read_text()
    tree = ast.parse(source)
    constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, int)
    }

    assert "TerraModelCallBudget" in source
    assert "LunaModelCallBudget" in source
    assert "TerraPanelRateLimiter" in source
    assert "LunaPanelRateLimiter" in source
    assert 8_192 in constants
    assert 2_048 in constants
    assert 50_000 not in constants
    assert 'required("TAU2_LUNA_API_BASE")' in source
    assert 'required("TAU2_LUNA_API_VERSION")' in source
    assert 'required("TAU2_NL_ASSERTIONS_DEPLOYMENT")' in source
    assert "tau2-luna-smoke-20260805" in source
    assert "azure-openai-luna-key" in source


def test_azure_preflight_checks_both_exact_deployments_before_vm_start() -> None:
    run = AZURE_RUN.read_text()

    assert run.count("cognitiveservices account deployment show") == 2
    assert "kairos-openai-1" in run
    assert "gpt-5-6-terra-sentinel" in run
    assert re.search(r"gpt-5\.6-terra.*?capacity:100", run, flags=re.DOTALL)
    assert "kairos-memory" in run
    assert "tau2-luna-smoke-20260805" in run
    assert re.search(r"gpt-5\.6-luna.*?capacity:10", run, flags=re.DOTALL)
    assert "https://kairos-memory.openai.azure.com/" in run
    second_preflight = run.rfind("cognitiveservices account deployment show")
    assert second_preflight < run.index("vm start") < run.index("vm run-command invoke")
    for forbidden in ("vm auto-shutdown", "vm deallocate", "vm delete", "group delete"):
        assert forbidden not in run
    assert "vm_discovery_bootstrap.sh" in run
    assert '.state == "RUNNING"' in run
    assert ".blob_status_verified == true" in run
    assert "luna_api_base=${TAU2_LUNA_API_BASE}" in run
    assert "luna_deployment=${TAU2_NL_ASSERTIONS_DEPLOYMENT}" in run
    assert re.search(r"--parameters[^\n]*key=", run) is None


def test_deploy_custodies_luna_key_as_distinct_file_backed_vault_secret() -> None:
    deploy = AZURE_DEPLOY.read_text()

    assert "kairos-openai-1" in deploy
    assert "kairos-memory" in deploy
    assert "luna_secret_file" in deploy
    assert re.search(
        r'account keys list.*?--name (?:"\$\{AZURE_LUNA_RESOURCE\}"|kairos-memory)'
        r'.*?>"\$\{luna_secret_file\}"',
        deploy,
        flags=re.DOTALL,
    )
    assert re.search(
        r"keyvault secret set.*?--name azure-openai-luna-key"
        r'.*?--file "\$\{luna_secret_file\}".*?--output none',
        deploy,
        flags=re.DOTALL,
    )
    assert "--name azure-openai-luna-key --value" not in deploy
    assert "luna_secret_file" in next(line for line in deploy.splitlines() if line.startswith("trap "))


def test_vm_bootstrap_and_worker_require_separate_luna_configuration_and_v2_source() -> None:
    vm = VM_SMOKE.read_text()
    worker = WORKER.read_text()

    assert "TAU2_LUNA_API_BASE" in vm
    assert "TAU2_LUNA_API_VERSION" in vm
    assert "TAU2_NL_ASSERTIONS_DEPLOYMENT" in vm
    assert "luna_api_key" in worker
    assert "azure-openai-luna-key" in worker
    assert "TAU2_LUNA_API_BASE" in worker
    assert "TAU2_NL_ASSERTIONS_DEPLOYMENT" in worker
    assert "terra-10-v2" in vm
    assert "tau2-terra-10-v2.tar.gz" in vm
    assert "tau2-terra-10-v1" not in vm


def test_same_run_resume_retains_prior_partial_and_starts_new_attempt() -> None:
    from tau2_luna_local.cloud_smoke import plan_resume

    checkpoint = {
        "schema_version": "tau2-luna-cloud-checkpoint/v1",
        "task_id": "83",
        "trial": 0,
        "attempts": [
            {
                "attempt_id": "attempt-live-partial",
                "state": "PARTIAL",
                "prefix": "runs/terra10-20260805-001/tasks/83/attempts/attempt-live-partial/",
            }
        ],
    }
    checkpoint["checkpoint_hash"] = hashlib.sha256(CHECKPOINT_DOMAIN + _canonical(checkpoint)).hexdigest()
    before = _canonical(checkpoint)

    decision = plan_resume(
        checkpoint,
        task_id="83",
        trial=0,
        attempt_id_factory=lambda: "attempt-resume-2",
        verify_completed=lambda _: False,
    )

    assert decision == {
        "action": "START_NEW_ATTEMPT",
        "attempt_id": "attempt-resume-2",
        "retained_attempt_ids": ["attempt-live-partial"],
    }
    assert _canonical(checkpoint) == before
