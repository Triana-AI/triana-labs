from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any

from azure.core.exceptions import ResourceNotFoundError

from tau2_luna_local.cloud_smoke import (
    CHECKPOINT_DOMAIN,
    CHECKPOINT_SCHEMA,
    managed_identity_clients,
    plan_resume,
    validate_tau2_data_directory,
)
from tau2_luna_local.config import load_config
from tau2_luna_local.constants import UPSTREAM_COMMIT
from tau2_luna_local.discovery import (
    DISCOVERY_TASK_IDS,
    AggregateBudgetExhausted,
    SharedStudyBudget,
    build_study_manifest,
    checkpoint_object_name,
    hash_checkpoint,
    plan_discovery_resume,
    project_request_hashes,
    publish_terminal_evidence,
    study_identity,
    validate_discovery_tasks,
)
from tau2_luna_local.runner import run_experiment
from tau2_luna_local.serde import canonical_bytes
from tau2_luna_local.terra_smoke import (
    TERRA_DEPLOYMENT,
    TERRA_MODEL_IDENTITY,
    TERRA_TASK_PANEL,
    BudgetExhausted,
    LunaModelCallBudget,
    LunaPanelRateLimiter,
    PanelInfrastructureFailure,
    TerraModelCallBudget,
    TerraPanelRateLimiter,
    audit_trace_suitability,
    run_terra_panel,
    validate_terra_model_identity,
)
from tau2_luna_local.verify import verify_bundle


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def hashed_checkpoint(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["checkpoint_hash"] = hashlib.sha256(CHECKPOINT_DOMAIN + canonical_bytes(result)).hexdigest()
    return result


def verified_remote_attempt(
    authority: Any, attempt: dict[str, Any], secrets: tuple[str, ...]
) -> bool:
    relay_name = attempt.get("relay_checkpoint")
    if not isinstance(relay_name, str):
        return False
    try:
        relay = json.loads(authority.download(relay_name))
        for item in relay["inventory"]:
            data = authority.download(item["remote_name"])
            if (
                len(data) != item["size"]
                or hashlib.sha256(data).hexdigest() != item["sha256"]
                or any(secret.encode() in data for secret in secrets)
            ):
                return False
    except (KeyError, TypeError, ValueError, ResourceNotFoundError):
        return False
    return True


def _write_local(path: Path, value: Any) -> bytes:
    data = canonical_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def _request_fingerprints(events_path: Path) -> list[dict[str, Any]]:
    fingerprints: list[dict[str, Any]] = []
    if not events_path.is_file():
        return fingerprints
    for line in events_path.read_bytes().splitlines():
        event = json.loads(line)
        if event.get("event_name") != "model.request":
            continue
        payload = event.get("payload", {})
        request = canonical_bytes(payload.get("kwargs", {}))
        fingerprints.append(
            {
                "call_id": payload.get("call_id"),
                "model": payload.get("model"),
                **project_request_hashes(request),
            }
        )
    return fingerprints


def _local_artifacts(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def discovery_main() -> int:
    storage = required("TAU2_SMOKE_STORAGE")
    run_id = required("TAU2_SMOKE_RUN_ID")
    vault_url = required("TAU2_SMOKE_VAULT_URI")
    authority, terra_key = managed_identity_clients(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        vault_url=vault_url,
        secret_name="azure-openai-key",
        storage_secret_name="storage-account-key",
    )
    _, luna_key = managed_identity_clients(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        vault_url=vault_url,
        secret_name="azure-openai-luna-key",
        storage_secret_name="storage-account-key",
    )
    if terra_key == luna_key:
        raise RuntimeError("Terra and Luna credentials must be distinct")
    deployment = required("TAU2_LUNA_DEPLOYMENT")
    luna_deployment = required("TAU2_NL_ASSERTIONS_DEPLOYMENT")
    if deployment != TERRA_DEPLOYMENT or luna_deployment != "tau2-luna-smoke-20260805":
        raise RuntimeError("discovery requires exact Terra and Luna deployments")
    validate_terra_model_identity(TERRA_MODEL_IDENTITY)
    validate_discovery_tasks(DISCOVERY_TASK_IDS)
    validate_tau2_data_directory(Path(required("TAU2_SOURCE_DIR")))
    source_hash = required("TAU2_SOURCE_ARCHIVE_SHA256")
    study_root = Path(required("TAU2_TRACE_ROOT")) / run_id
    study_root.mkdir(parents=True, exist_ok=True)
    prefix = f"runs/{run_id}/"
    manifest = build_study_manifest(
        source_archive_sha256=source_hash,
        worker_revision="discovery-worker-v1",
        model_deployments={
            "agent_user": {
                **TERRA_MODEL_IDENTITY,
                "deployment": deployment,
                "capacity": 100,
            },
            "nl_assertions": {
                "model_name": "gpt-5.6-luna",
                "model_version": "2026-07-09",
                "sku": "GlobalStandard",
                "deployment": luna_deployment,
                "capacity": 10,
            },
        },
        runtime_config={
            "concurrency": 1,
            "provider_retries": 0,
            "cache": False,
            "fallback": False,
        },
        custody={"container": "tau2-smoke", "prefix": prefix},
    )
    manifest_data = _write_local(study_root / "study-manifest.json", manifest)
    authority.put(f"{prefix}study-manifest.json", manifest_data, overwrite=False)
    def persist_aggregate(projection: dict[str, Any]) -> None:
        data = _write_local(study_root / "budget-ledger.json", projection)
        authority.put(f"{prefix}budget-ledger.json", data, overwrite=True)

    shared_budget = SharedStudyBudget(on_change=persist_aggregate)
    try:
        shared_budget.restore(json.loads(authority.download(f"{prefix}budget-ledger.json")))
    except ResourceNotFoundError:
        persist_aggregate(shared_budget.projection())
    terra_limiter = TerraPanelRateLimiter()
    luna_limiter = LunaPanelRateLimiter()
    records: list[dict[str, Any]] = []
    terminal = "COMPLETED"

    for task_id in DISCOVERY_TASK_IDS:
        task_key = str(task_id)
        checkpoint_name = checkpoint_object_name(run_id, task_id)
        try:
            checkpoint = json.loads(authority.download(checkpoint_name))
        except ResourceNotFoundError:
            checkpoint = hash_checkpoint(task_id=task_key, trial=0, attempts=[])
        decision = plan_discovery_resume(
            checkpoint,
            task_id=task_key,
            trial=0,
            attempt_id_factory=lambda: f"attempt-{uuid.uuid4().hex}",
            verify_completed=lambda attempt: verified_remote_attempt(
                authority, dict(attempt), (terra_key, luna_key)
            ),
        )
        if decision["action"] == "SKIP_VERIFIED_COMPLETED":
            records.append({"task_id": task_id, "state": "SKIPPED"})
            continue
        attempt_id = str(decision["attempt_id"])
        attempt_prefix = f"{prefix}tasks/{task_id}/attempts/{attempt_id}/"
        attempts = [
            *checkpoint["attempts"],
            {"attempt_id": attempt_id, "state": "PARTIAL", "prefix": attempt_prefix},
        ]
        pending = hash_checkpoint(task_id=task_key, trial=0, attempts=attempts)
        checkpoint_data = _write_local(
            study_root / "tasks" / task_key / "checkpoint.json", pending
        )
        authority.put(checkpoint_name, checkpoint_data, overwrite=True)
        config = load_config(
            {
                "AZURE_API_KEY": terra_key,
                "AZURE_API_BASE": required("AZURE_API_BASE"),
                "AZURE_API_VERSION": required("AZURE_API_VERSION"),
                "TAU2_LUNA_DEPLOYMENT": deployment,
                "TAU2_TRACE_ROOT": str(study_root / "tasks" / task_key / "attempts"),
            },
            domain="retail",
            task_id=task_key,
            seed=1729,
        )
        terra_budget = TerraModelCallBudget(
            task_id=task_id,
            rate_limiter=terra_limiter,
            study_budget=shared_budget,
            allowed_task_ids=DISCOVERY_TASK_IDS,
        )
        luna_budget = LunaModelCallBudget(
            task_id=task_id,
            rate_limiter=luna_limiter,
            study_budget=shared_budget,
            allowed_task_ids=DISCOVERY_TASK_IDS,
        )
        luna_model = f"azure/{luna_deployment}"

        def guarded(
            provider: Any,
            *args: Any,
            _config: Any = config,
            _terra_budget: Any = terra_budget,
            _luna_model: str = luna_model,
            _luna_budget: Any = luna_budget,
            **kwargs: Any,
        ) -> Any:
            requested_model = kwargs.get("model")
            if requested_model == _config.model:
                budget, ceiling = _terra_budget, 8_192
            elif requested_model == _luna_model:
                budget, ceiling = _luna_budget, 2_048
            else:
                raise BudgetExhausted("unknown model refused before egress")
            requested = kwargs.setdefault("max_completion_tokens", ceiling)
            if not isinstance(requested, int) or isinstance(requested, bool) or requested > ceiling:
                raise BudgetExhausted("requested output exceeds model-specific ceiling")
            input_reservation = len(
                canonical_bytes(
                    {
                        "messages": kwargs.get("messages", []),
                        "tools": kwargs.get("tools", []),
                        "tool_choice": kwargs.get("tool_choice"),
                    }
                )
            )
            return budget.call(
                provider, *args, input_token_reservation=input_reservation, **kwargs
            )

        run_dir = config.trace_root / attempt_id
        state = "PARTIAL"
        caught: BaseException | None = None
        try:
            run_dir = run_experiment(
                config,
                run_id=attempt_id,
                remote_append=authority.append,
                remote_prefix=attempt_prefix,
                completion_guard=guarded,
                nl_assertions_config={
                    "model": luna_model,
                    "api_base": required("TAU2_LUNA_API_BASE"),
                    "api_version": required("TAU2_LUNA_API_VERSION"),
                    "api_key": luna_key,
                },
            )
            if not verify_bundle(run_dir, secret_values=(terra_key, luna_key))["valid"]:
                raise RuntimeError("local discovery bundle verification failed")
            state = "COMPLETED"
        except BaseException as exc:
            caught = exc
            cause: BaseException | None = exc
            while cause is not None:
                if isinstance(cause, AggregateBudgetExhausted):
                    state = terminal = "BUDGET_STOP"
                    break
                cause = cause.__cause__
            else:
                terminal = "PARTIAL"
        finally:
            if run_dir.is_dir():
                fingerprints = _request_fingerprints(run_dir / "events.jsonl")
                _write_local(run_dir / "request-fingerprints.json", fingerprints)
                _write_local(
                    run_dir / "task-budget.json",
                    {
                        "task_id": task_id,
                        "terra_charged_usd": str(terra_budget.charged_usd),
                        "luna_charged_usd": str(luna_budget.charged_usd),
                        "aggregate": shared_budget.projection(),
                    },
                )
                for path in sorted(run_dir.iterdir()):
                    if path.is_file():
                        authority.put(
                            f"{attempt_prefix}bundle/{path.name}",
                            path.read_bytes(),
                            overwrite=False,
                        )
            relay_name: str | None = None
            bundle_hash: str | None = None
            if state == "COMPLETED":
                inventory = []
                for remote_name in authority.list(attempt_prefix):
                    data = authority.download(remote_name)
                    if any(secret.encode() in data for secret in (terra_key, luna_key)):
                        raise RuntimeError("secret reflection found before discovery relay")
                    inventory.append(
                        {
                            "remote_name": remote_name,
                            "local_name": remote_name.removeprefix(attempt_prefix),
                            "size": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(),
                        }
                    )
                relay_name = f"{prefix}tasks/{task_id}/relays/{attempt_id}.json"
                relay_data = _write_local(
                    study_root / "tasks" / task_key / "relays" / f"{attempt_id}.json",
                    {
                        "schema_version": "tau2-retail-discovery-relay/v1",
                        "prefix": attempt_prefix,
                        "inventory": inventory,
                    },
                )
                authority.put(relay_name, relay_data, overwrite=False)
                bundle_hash = hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest()
            attempts[-1] = {
                "attempt_id": attempt_id,
                "state": state,
                "prefix": attempt_prefix,
                **({"bundle_hash": bundle_hash, "relay_checkpoint": relay_name} if bundle_hash else {}),
            }
            final_checkpoint = hash_checkpoint(task_id=task_key, trial=0, attempts=attempts)
            checkpoint_data = _write_local(
                study_root / "tasks" / task_key / "checkpoint.json", final_checkpoint
            )
            authority.put(checkpoint_name, checkpoint_data, overwrite=True)
        records.append({"task_id": task_id, "attempt_id": attempt_id, "state": state})
        if caught is not None:
            break

    _write_local(study_root / "task-records.json", records)
    artifacts = _local_artifacts(study_root)
    result = publish_terminal_evidence(
        study_id=study_identity()["study_id"],
        terminal_state=terminal,
        artifacts=artifacts,
        put=authority.put,
    )
    authority.put(
        f"{prefix}status.json",
        canonical_bytes({"state": terminal, "run_id": run_id, **result}) + b"\n",
        overwrite=True,
    )
    print(json.dumps({"state": terminal, "run_id": run_id}))
    return 0 if terminal == "COMPLETED" else 1


def main() -> int:
    if os.environ.get("TAU2_EXECUTION_MODE") == "discovery":
        return discovery_main()
    storage = required("TAU2_SMOKE_STORAGE")
    run_id = required("TAU2_SMOKE_RUN_ID")
    authority, api_key = managed_identity_clients(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        vault_url=required("TAU2_SMOKE_VAULT_URI"),
        secret_name="azure-openai-key",
        storage_secret_name="storage-account-key",
    )
    _, luna_api_key = managed_identity_clients(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        vault_url=required("TAU2_SMOKE_VAULT_URI"),
        secret_name="azure-openai-luna-key",
        storage_secret_name="storage-account-key",
    )
    if luna_api_key == api_key:
        raise RuntimeError("Terra and Luna credentials must be distinct")
    validate_terra_model_identity(TERRA_MODEL_IDENTITY)
    deployment = required("TAU2_LUNA_DEPLOYMENT")
    if deployment != TERRA_DEPLOYMENT:
        raise RuntimeError("Terra panel requires exact deployment gpt-5-6-terra-sentinel")
    luna_api_base = required("TAU2_LUNA_API_BASE")
    luna_api_version = required("TAU2_LUNA_API_VERSION")
    luna_deployment = required("TAU2_NL_ASSERTIONS_DEPLOYMENT")
    if luna_deployment != "tau2-luna-smoke-20260805":
        raise RuntimeError("NL assertions require exact Luna deployment")
    luna_model = f"azure/{luna_deployment}"
    validate_tau2_data_directory(Path(required("TAU2_SOURCE_DIR")))
    terra_panel_rate_limiter = TerraPanelRateLimiter()
    luna_panel_rate_limiter = LunaPanelRateLimiter()
    contexts: dict[int, tuple[str, str, list[dict[str, Any]]]] = {}

    def resume_task(task_id: int, trial: int) -> dict[str, str]:
        task_key = str(task_id)
        checkpoint_name = f"runs/{run_id}/tasks/{task_id}/checkpoint.json"
        try:
            checkpoint = json.loads(authority.download(checkpoint_name))
        except ResourceNotFoundError:
            checkpoint = hashed_checkpoint(
                {
                    "schema_version": CHECKPOINT_SCHEMA,
                    "task_id": task_key,
                    "trial": trial,
                    "attempts": [],
                }
            )
        decision = plan_resume(
            checkpoint,
            task_id=task_key,
            trial=trial,
            attempt_id_factory=lambda: f"attempt-{uuid.uuid4().hex}",
            verify_completed=lambda attempt: verified_remote_attempt(
                authority, dict(attempt), (api_key, luna_api_key)
            ),
        )
        if decision["action"] == "START_NEW_ATTEMPT":
            attempt_id = str(decision["attempt_id"])
            prefix = f"runs/{run_id}/tasks/{task_id}/attempts/{attempt_id}/"
            attempts = [
                *checkpoint["attempts"],
                {"attempt_id": attempt_id, "state": "PARTIAL", "prefix": prefix},
            ]
            pending = hashed_checkpoint(
                {
                    "schema_version": CHECKPOINT_SCHEMA,
                    "task_id": task_key,
                    "trial": trial,
                    "attempts": attempts,
                }
            )
            authority.put(checkpoint_name, canonical_bytes(pending) + b"\n", overwrite=True)
            contexts[task_id] = (checkpoint_name, prefix, attempts)
        return {"action": str(decision["action"]), "attempt_id": str(decision["attempt_id"])}

    def execute_task(*, task_id: int, trial: int, seed: int, attempt_id: str) -> dict[str, Any]:
        del trial, seed
        checkpoint_name, prefix, attempts = contexts[task_id]
        config = load_config(
            {
                "AZURE_API_KEY": api_key,
                "AZURE_API_BASE": required("AZURE_API_BASE"),
                "AZURE_API_VERSION": required("AZURE_API_VERSION"),
                "TAU2_LUNA_DEPLOYMENT": deployment,
                "TAU2_TRACE_ROOT": required("TAU2_TRACE_ROOT"),
            },
            domain="retail",
            task_id=str(task_id),
            seed=1729,
        )
        terra_budget = TerraModelCallBudget(
            task_id=task_id, rate_limiter=terra_panel_rate_limiter
        )
        luna_budget = LunaModelCallBudget(
            task_id=task_id, rate_limiter=luna_panel_rate_limiter
        )

        def guarded(provider: Any, *args: Any, **kwargs: Any) -> Any:
            requested_model = kwargs.get("model")
            if requested_model == config.model:
                budget = terra_budget
                output_ceiling = 8_192
                requested_output = kwargs.setdefault("max_completion_tokens", 8_192)
            elif requested_model == luna_model:
                budget = luna_budget
                output_ceiling = 2_048
                if "max_completion_tokens" not in kwargs:
                    kwargs["max_completion_tokens"] = 2_048
                requested_output = kwargs["max_completion_tokens"]
            else:
                raise BudgetExhausted("unknown model refused before egress")
            if (
                not isinstance(requested_output, int)
                or isinstance(requested_output, bool)
                or requested_output > output_ceiling
            ):
                raise BudgetExhausted("requested output exceeds model-specific ceiling")
            input_reservation = len(
                canonical_bytes(
                    {
                        "messages": kwargs.get("messages", []),
                        "tools": kwargs.get("tools", []),
                        "tool_choice": kwargs.get("tool_choice"),
                    }
                )
            )
            return budget.call(
                provider, *args, input_token_reservation=input_reservation, **kwargs
            )

        state = "PARTIAL"
        relay_name = None
        bundle_hash = None
        run_dir = config.trace_root / attempt_id
        caught: BaseException | None = None
        try:
            run_dir = run_experiment(
                config,
                run_id=attempt_id,
                remote_append=authority.append,
                remote_prefix=prefix,
                completion_guard=guarded,
                nl_assertions_config={
                    "model": luna_model,
                    "api_base": luna_api_base,
                    "api_version": luna_api_version,
                    "api_key": luna_api_key,
                },
            )
            if not verify_bundle(run_dir, secret_values=(api_key, luna_api_key))["valid"]:
                raise RuntimeError("local bundle verification failed")
            state = "COMPLETED"
        except BaseException as exc:
            caught = exc
        finally:
            if run_dir.is_dir():
                for path in sorted(run_dir.iterdir()):
                    if path.is_file():
                        authority.put(f"{prefix}bundle/{path.name}", path.read_bytes(), overwrite=False)
            def budget_projection(budget: Any) -> dict[str, Any]:
                return {
                    "task_cap_usd": str(budget.task_cap_usd),
                    "charged_usd": str(budget.charged_usd),
                    "ledger": [
                        {
                            key: str(value) if hasattr(value, "as_tuple") else value
                            for key, value in item.items()
                        }
                        for item in budget.ledger
                    ],
                }

            budget_evidence = {
                "task_id": task_id,
                "combined_task_cap_usd": "0.96",
                "terra": budget_projection(terra_budget),
                "luna": budget_projection(luna_budget),
            }
            authority.put(
                f"{prefix}terra-budget.json",
                canonical_bytes(budget_evidence) + b"\n",
                overwrite=False,
            )
            if state == "COMPLETED":
                bundle_hash = hashlib.sha256((run_dir / "manifest.json").read_bytes()).hexdigest()
                inventory = []
                for remote_name in authority.list(prefix):
                    data = authority.download(remote_name)
                    if any(secret.encode() in data for secret in (api_key, luna_api_key)):
                        raise RuntimeError("secret reflection found before relay publication")
                    relative = remote_name.removeprefix(prefix)
                    inventory.append(
                        {
                            "remote_name": remote_name,
                            "local_name": relative if "/" in relative else f"streams/{relative}",
                            "size": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(),
                        }
                    )
                relay_name = f"runs/{run_id}/tasks/{task_id}/relays/{attempt_id}.json"
                authority.put(
                    relay_name,
                    canonical_bytes(
                        {
                            "schema_version": "tau2-terra-relay/v1",
                            "prefix": prefix,
                            "inventory": inventory,
                        }
                    )
                    + b"\n",
                    overwrite=False,
                )
            attempts[-1] = {
                "attempt_id": attempt_id,
                "state": state,
                "prefix": prefix,
                **({"bundle_hash": bundle_hash, "relay_checkpoint": relay_name} if bundle_hash else {}),
            }
            authority.put(
                checkpoint_name,
                canonical_bytes(
                    hashed_checkpoint(
                        {
                            "schema_version": CHECKPOINT_SCHEMA,
                            "task_id": str(task_id),
                            "trial": 0,
                            "attempts": attempts,
                        }
                    )
                )
                + b"\n",
                overwrite=True,
            )
        if caught is not None:
            cause: BaseException | None = caught
            while cause is not None:
                if isinstance(cause, BudgetExhausted):
                    raise cause
                cause = cause.__cause__
            raise PanelInfrastructureFailure("task execution failed with partial evidence") from caught
        return {
            "state": state,
            "bundle_valid": True,
            "bundle_hash": bundle_hash,
            "relay_checkpoint": relay_name,
            "charged_usd": str(terra_budget.charged_usd + luna_budget.charged_usd),
        }

    report = run_terra_panel(
        resume=resume_task,
        execute=execute_task,
        task_ids=TERRA_TASK_PANEL,
    )
    report["model_identity"] = TERRA_MODEL_IDENTITY
    report["deployment"] = deployment
    report["trial"] = 0
    report["seed"] = 1729
    report["upstream_commit"] = UPSTREAM_COMMIT
    report["run_configuration"] = {
        "domain": "retail", "trial": 0, "seed": 1729, "concurrency": 1,
        "provider_retries": 0, "cache": False, "fallback": False,
    }
    report["trace_audit"] = audit_trace_suitability(
        records=report["records"],
        normalized_trace_required_fields=("trace_id", "messages", "tool_calls"),
        normalized_trace_observed_fields=("messages", "tool_calls"),
    )
    report_data = canonical_bytes(report) + b"\n"
    report_hash = hashlib.sha256(report_data).hexdigest()
    denominators = report["denominators"]
    terminal = (
        "COMPLETED"
        if "stop" not in report
        and denominators["completed"] + denominators["skipped"] == len(TERRA_TASK_PANEL)
        else "PARTIAL"
    )
    if terminal == "COMPLETED":
        authority.put(
            f"runs/{run_id}/terra-panels/{report_hash}.json", report_data, overwrite=False
        )
    print(json.dumps({"state": terminal, "run_id": run_id}))
    if terminal != "COMPLETED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
