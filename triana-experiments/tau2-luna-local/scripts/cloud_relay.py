from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

from tau2_luna_local.cloud_smoke import (
    CHECKPOINT_DOMAIN,
    CHECKPOINT_SCHEMA,
    AzureBlobAuthority,
    relay_verified_inventory,
)
from tau2_luna_local.serde import canonical_bytes
from tau2_luna_local.terra_smoke import TERRA_TASK_PANEL
from tau2_luna_local.verify import verify_bundle


class PanelRelayError(RuntimeError):
    pass


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _object(value: bytes, *, label: str) -> dict[str, Any]:
    try:
        result = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PanelRelayError(f"{label} is not valid JSON") from exc
    if not isinstance(result, dict):
        raise PanelRelayError(f"{label} is not an object")
    return result


def _completed_attempt(checkpoint: Mapping[str, Any], *, task_id: int, attempt_id: str) -> dict[str, Any]:
    supplied = checkpoint.get("checkpoint_hash")
    unhashed = dict(checkpoint)
    unhashed.pop("checkpoint_hash", None)
    expected = hashlib.sha256(CHECKPOINT_DOMAIN + canonical_bytes(unhashed)).hexdigest()
    if (
        supplied != expected
        or checkpoint.get("schema_version") != CHECKPOINT_SCHEMA
        or checkpoint.get("task_id") != str(task_id)
        or checkpoint.get("trial") != 0
        or not isinstance(checkpoint.get("attempts"), list)
    ):
        raise PanelRelayError(f"task {task_id} checkpoint is invalid")
    matches = [
        item
        for item in checkpoint["attempts"]
        if isinstance(item, dict)
        and item.get("attempt_id") == attempt_id
        and item.get("state") == "COMPLETED"
    ]
    if len(matches) != 1:
        raise PanelRelayError(f"task {task_id} has no unique completed attempt")
    return matches[0]


def relay_terra_panel(
    *,
    authority: Any,
    run_id: str,
    destination: Path,
    secret_values: Iterable[str],
    bundle_verifier: Callable[..., Mapping[str, Any]] = verify_bundle,
) -> dict[str, Any]:
    if destination.exists():
        raise PanelRelayError("panel relay destination already exists")
    panel_prefix = f"runs/{run_id}/terra-panels/"
    panel_names = authority.list(panel_prefix)
    if len(panel_names) != 1:
        raise PanelRelayError("panel relay requires exactly one content-addressed report")
    panel_name = panel_names[0]
    panel_data = authority.download(panel_name)
    if panel_name != f"{panel_prefix}{hashlib.sha256(panel_data).hexdigest()}.json":
        raise PanelRelayError("panel report content address is invalid")
    panel = _object(panel_data, label="panel report")
    records = panel.get("records")
    denominators = panel.get("denominators")
    if not isinstance(records, list) or [item.get("task_id") for item in records] != list(
        TERRA_TASK_PANEL
    ):
        raise PanelRelayError("panel report does not contain the exact ordered task panel")
    if not isinstance(denominators, dict) or (
        denominators.get("requested") != 10
        or denominators.get("completed", 0) + denominators.get("skipped", 0) != 10
        or denominators.get("partial") != 0
        or denominators.get("invalid") != 0
    ):
        raise PanelRelayError("panel report is not complete")

    secrets = tuple(secret_values)
    verified = 0
    for task_id, record in zip(TERRA_TASK_PANEL, records, strict=True):
        try:
            attempt_id = record.get("attempt_id")
            if record.get("state") not in {"COMPLETED", "SKIPPED"} or not isinstance(
                attempt_id, str
            ):
                raise PanelRelayError(f"task {task_id} record is incomplete")
            checkpoint = _object(
                authority.download(f"runs/{run_id}/tasks/{task_id}/checkpoint.json"),
                label=f"task {task_id} checkpoint",
            )
            attempt = _completed_attempt(checkpoint, task_id=task_id, attempt_id=attempt_id)
            relay_name = attempt.get("relay_checkpoint")
            if not isinstance(relay_name, str) or record.get("relay_checkpoint", relay_name) != relay_name:
                raise PanelRelayError(f"task {task_id} relay identity is invalid")
            relay = _object(authority.download(relay_name), label=f"task {task_id} relay")
            if relay.get("schema_version") != "tau2-terra-relay/v1":
                raise PanelRelayError(f"task {task_id} relay schema is invalid")
            task_destination = destination / f"task-{task_id}"
            relay_verified_inventory(
                remote_list=authority.list,
                remote_download=authority.download,
                checkpoint=relay,
                destination=task_destination,
                secret_values=secrets,
            )
            manifest = task_destination / "bundle" / "manifest.json"
            if hashlib.sha256(manifest.read_bytes()).hexdigest() != attempt.get("bundle_hash"):
                raise PanelRelayError(f"task {task_id} bundle manifest hash is invalid")
            if not bundle_verifier(task_destination / "bundle", secret_values=secrets).get("valid"):
                raise PanelRelayError(f"task {task_id} bundle verification failed")
            verified += 1
        except PanelRelayError:
            raise
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise PanelRelayError(f"task {task_id} relay is incomplete") from exc

    destination.mkdir(parents=True, exist_ok=True)
    with (destination / "terra-panel-report.json").open("xb") as stream:
        stream.write(panel_data)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "valid": True,
        "task_ids": list(TERRA_TASK_PANEL),
        "verified_bundles": verified,
        "panel_report": "terra-panel-report.json",
    }


def main() -> int:
    storage = required("TAU2_SMOKE_STORAGE")
    run_id = required("TAU2_SMOKE_RUN_ID")
    credential = Path(required("AZURE_STORAGE_KEY_FILE")).read_text().strip()
    if not credential:
        raise RuntimeError("storage key file is empty")
    authority = AzureBlobAuthority(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        credential=credential,
    )
    secret = os.environ.get("AZURE_API_KEY", "")
    report = relay_terra_panel(
        authority=authority,
        run_id=run_id,
        destination=Path(required("TAU2_RELAY_DESTINATION")),
        secret_values=tuple(value for value in (secret, credential) if value),
    )
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
