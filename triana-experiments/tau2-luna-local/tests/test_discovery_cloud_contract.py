# ruff: noqa: SIM905 -- compact frozen task identities keep this packet below 360 lines.
from __future__ import annotations

import hashlib
import importlib
import io
import json
import tarfile
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "azure_run.sh"
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
WORKER_SCRIPT = PROJECT_ROOT / "scripts" / "cloud_worker.py"
BOOTSTRAP_SCRIPT = PROJECT_ROOT / "scripts" / "vm_discovery_bootstrap.sh"

DISCOVERY = tuple(
    map(
        int,
        (
            "1,2,5,6,7,10,11,15,16,19,21,22,23,24,25,26,27,30,32,34,37,38,39,40,"
            "46,52,53,54,56,58,61,64,65,68,71,75,80,81,83,85,86,88,90,91,94,95,96,"
            "97,99,101,103,104,107,108,109,112,113"
        ).split(","),
    )
)
HOLDOUT = tuple(
    map(
        int,
        (
            "0,3,4,8,9,12,13,14,17,18,20,28,29,31,33,35,36,41,42,43,44,45,47,48,"
            "49,50,51,55,57,59,60,62,63,66,67,69,70,72,73,74,76,77,78,79,82,84,87,"
            "89,92,93,98,100,102,105,106,110,111"
        ).split(","),
    )
)
IDENTITY = {
    "study_id": "tau2-retail-discovery-v1",
    "panel_id": "tau2-retail-discovery-v1-seed-1729",
    "split_version": "sha256-balanced-retail-v1",
    "arm": "BASELINE_DISCOVERY",
    "domain": "retail",
    "trial": 0,
    "seed": 1729,
    "upstream_commit": "f8de30c298689cbe0117d76a378e7315a17e5bd8",
}


def _discovery() -> Any:
    return importlib.import_module("tau2_luna_local.discovery")


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def test_exact_discovery_holdout_split_identity_and_holdout_refusal() -> None:
    discovery = _discovery()

    assert discovery.DISCOVERY_TASK_IDS == DISCOVERY
    assert discovery.HOLDOUT_TASK_IDS == HOLDOUT
    assert len(DISCOVERY) == len(HOLDOUT) == 57
    assert set(DISCOVERY).isdisjoint(HOLDOUT)
    assert sorted((*DISCOVERY, *HOLDOUT)) == list(range(114))
    assert discovery.study_identity() == IDENTITY
    assert discovery.validate_discovery_tasks(DISCOVERY) == DISCOVERY

    for forbidden in (HOLDOUT[0], HOLDOUT[-1]):
        with pytest.raises(discovery.HoldoutTaskRefused, match=r"holdout|forbidden"):
            discovery.validate_discovery_tasks((*DISCOVERY[:-1], forbidden))
    with pytest.raises(discovery.DiscoveryIdentityError, match=r"57|order|panel"):
        discovery.validate_discovery_tasks(tuple(reversed(DISCOVERY)))


def test_shared_budget_serializes_outstanding_reservations_under_concurrency() -> None:
    discovery = _discovery()
    budget = discovery.SharedStudyBudget(cap_usd=Decimal("25.00"))
    barrier = threading.Barrier(26)
    admitted: list[Any] = []
    refused: list[BaseException] = []
    lock = threading.Lock()

    def reserve() -> None:
        barrier.wait()
        try:
            reservation = budget.reserve(model="terra", reserved_usd=Decimal("1.00"))
        except discovery.AggregateBudgetExhausted as exc:
            with lock:
                refused.append(exc)
        else:
            with lock:
                admitted.append(reservation)

    threads = [threading.Thread(target=reserve) for _ in range(26)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert all(not thread.is_alive() for thread in threads)
    assert len(admitted) == 25
    assert len(refused) == 1
    assert budget.accrued_usd == Decimal("0.00")
    assert budget.outstanding_usd == Decimal("25.00")


def test_shared_budget_actual_and_conservative_terminal_debits() -> None:
    discovery = _discovery()
    budget = discovery.SharedStudyBudget(cap_usd=Decimal("25.00"))

    response = budget.call(
        model="terra",
        reserved_usd=Decimal("4.00"),
        provider=lambda: {"usage": {"prompt_tokens": 200_000, "completion_tokens": 50_000}},
    )
    assert response["usage"]["completion_tokens"] == 50_000
    budget.call(model="luna", reserved_usd=Decimal("2.00"), provider=lambda: {})
    with pytest.raises(RuntimeError, match="provider failed"):
        budget.call(
            model="terra",
            reserved_usd=Decimal("3.00"),
            provider=lambda: (_ for _ in ()).throw(RuntimeError("provider failed")),
        )

    assert budget.accrued_usd == Decimal("6.25")
    assert budget.outstanding_usd == Decimal("0.00")
    assert [entry["outcome"] for entry in budget.ledger] == [
        "ACTUAL_USAGE_DEBIT",
        "CONSERVATIVE_MISSING_USAGE",
        "CONSERVATIVE_FAILED_CALL",
    ]
    assert [entry["charged_usd"] for entry in budget.ledger] == [
        Decimal("1.25"),
        Decimal("2.00"),
        Decimal("3.00"),
    ]
    with pytest.raises(discovery.AggregateBudgetExhausted):
        budget.reserve(model="luna", reserved_usd=Decimal("19.00"))


def test_manifest_is_deterministic_and_closes_over_every_study_input() -> None:
    discovery = _discovery()
    arguments = {
        "source_archive_sha256": "a" * 64,
        "worker_revision": "discovery-worker-v1",
        "model_deployments": {
            "agent_user": {
                "model_name": "gpt-5.6-terra",
                "model_version": "2026-07-09",
                "sku": "GlobalStandard",
                "deployment": "gpt-5-6-terra-sentinel",
            },
            "nl_assertions": {
                "model_name": "gpt-5.6-luna",
                "model_version": "2026-07-09",
                "sku": "GlobalStandard",
                "deployment": "tau2-luna-smoke-20260805",
            },
        },
        "runtime_config": {"concurrency": 2, "provider_retries": 0, "cache": False, "fallback": False},
        "custody": {"container": "tau2-smoke", "prefix": "runs/discovery-001/"},
    }

    first = discovery.build_study_manifest(**arguments)
    second = discovery.build_study_manifest(**arguments)
    assert first == second
    assert {key: first[key] for key in IDENTITY} == IDENTITY
    assert first["discovery_task_ids"] == list(DISCOVERY)
    assert first["holdout_task_ids"] == list(HOLDOUT)
    assert first["source_archive_sha256"] == "a" * 64
    assert first["aggregate_model_cap_usd"] == "25.00"
    assert first["model_deployments"] == arguments["model_deployments"]
    assert first["runtime_config"] == arguments["runtime_config"]
    assert first["custody"] == arguments["custody"]
    assert first["prompt_tool_schema_evidence_policy"]
    unsigned = dict(first)
    supplied_hash = unsigned.pop("manifest_sha256")
    assert supplied_hash == hashlib.sha256(_canonical(unsigned)).hexdigest()
    changed = discovery.build_study_manifest(**{**arguments, "source_archive_sha256": "b" * 64})
    assert changed["manifest_sha256"] != supplied_hash


def test_prompt_and_tool_hashes_are_projected_only_from_captured_request_bytes() -> None:
    discovery = _discovery()
    messages = [{"role": "system", "content": "policy"}, {"role": "user", "content": "buy"}]
    tools = [{"type": "function", "function": {"name": "order", "parameters": {"type": "object"}}}]
    request = _canonical({"model": "azure/deployment", "messages": messages, "tools": tools})

    projection = discovery.project_request_hashes(request)
    assert projection == {
        "observed_prompt_sha256": hashlib.sha256(_canonical(messages)).hexdigest(),
        "observed_tool_schema_sha256": hashlib.sha256(_canonical(tools)).hexdigest(),
        "captured_request_sha256": hashlib.sha256(request).hexdigest(),
    }
    no_tools = _canonical({"model": "azure/deployment", "messages": messages})
    assert discovery.project_request_hashes(no_tools)["observed_tool_schema_sha256"] is None
    with pytest.raises(discovery.RequestEvidenceInvalid):
        discovery.project_request_hashes(b"not-json")


@pytest.mark.parametrize("terminal_state", ["PARTIAL", "BUDGET_STOP"])
def test_terminal_publication_always_contains_addressed_archive_and_manifest(
    terminal_state: str,
) -> None:
    discovery = _discovery()
    objects: dict[str, bytes] = {}
    artifacts = {
        "study-manifest.json": b'{"study":"identity"}\n',
        "tasks/1/events.jsonl": b'{"event":"partial"}\n',
        "budget-ledger.json": b'{"charged_usd":"1.25"}\n',
    }

    result = discovery.publish_terminal_evidence(
        study_id=IDENTITY["study_id"],
        terminal_state=terminal_state,
        artifacts=artifacts,
        put=lambda name, data, overwrite=False: objects.setdefault(name, data),
    )

    archive_name = result["archive_object"]
    manifest_name = result["archive_manifest_object"]
    assert archive_name.endswith(f"/{result['archive_sha256']}.tar.gz")
    assert hashlib.sha256(objects[archive_name]).hexdigest() == result["archive_sha256"]
    manifest = json.loads(objects[manifest_name])
    assert manifest["terminal_state"] == terminal_state
    assert manifest["archive_sha256"] == result["archive_sha256"]
    assert manifest["inventory"] == [
        {"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(artifacts.items())
    ]
    with tarfile.open(fileobj=io.BytesIO(objects[archive_name]), mode="r:gz") as archive:
        assert archive.getnames() == sorted(artifacts)
        assert {name: archive.extractfile(name).read() for name in archive.getnames()} == artifacts
    assert json.loads(objects[result["status_object"]])["state"] == terminal_state


def test_detached_bootstrap_and_launch_retain_all_azure_resources() -> None:
    bootstrap = BOOTSTRAP_SCRIPT.read_text()
    launch = RUN_SCRIPT.read_text()
    all_lifecycle_source = "\n".join(
        path.read_text() for path in (DEPLOY_SCRIPT, RUN_SCRIPT, WORKER_SCRIPT, BOOTSTRAP_SCRIPT)
    )

    assert "systemctl enable --now" in bootstrap
    assert "systemctl is-active" in bootstrap
    assert "RUNNING" in bootstrap
    assert "cloud_status.py" in bootstrap
    assert "vm_discovery_bootstrap.sh" in launch
    assert launch.count("az vm run-command invoke") == 1
    assert "RUNNING" in launch
    for forbidden in (
        "az vm deallocate",
        "az vm delete",
        "az group delete",
        "az disk delete",
        "az storage account delete",
        "az keyvault delete",
        "nohup",
        "tmux",
        "screen",
    ):
        assert forbidden not in all_lifecycle_source


def test_remote_resume_skips_only_verified_complete_and_preserves_partial_attempt() -> None:
    discovery = _discovery()
    partial = {"attempt_id": "attempt-old", "state": "PARTIAL", "prefix": "old/"}
    checkpoint = discovery.hash_checkpoint(task_id="1", trial=0, attempts=[partial])
    decision = discovery.plan_discovery_resume(
        checkpoint,
        task_id="1",
        trial=0,
        attempt_id_factory=lambda: "attempt-new",
        verify_completed=lambda _: False,
    )
    assert decision == {
        "action": "START_NEW_ATTEMPT",
        "attempt_id": "attempt-new",
        "retained_attempt_ids": ["attempt-old"],
    }
    assert checkpoint["attempts"] == [partial]
    completed = discovery.hash_checkpoint(
        task_id="1",
        trial=0,
        attempts=[{"attempt_id": "attempt-done", "state": "COMPLETED", "prefix": "done/"}],
    )
    assert (
        discovery.plan_discovery_resume(
            completed,
            task_id="1",
            trial=0,
            attempt_id_factory=lambda: "must-not-run",
            verify_completed=lambda _: True,
        )["action"]
        == "SKIP_VERIFIED_COMPLETED"
    )
    with pytest.raises(discovery.DiscoveryCheckpointInvalid):
        discovery.plan_discovery_resume(
            completed,
            task_id="1",
            trial=0,
            attempt_id_factory=lambda: "attempt-new",
            verify_completed=lambda _: False,
        )
    assert discovery.checkpoint_object_name("discovery-001", 1) == (
        "runs/discovery-001/tasks/1/checkpoint.json"
    )
