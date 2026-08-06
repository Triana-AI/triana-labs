from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLOUD_RELAY = PROJECT_ROOT / "scripts" / "cloud_relay.py"
AZURE_RELAY = PROJECT_ROOT / "scripts" / "azure_relay.sh"
TASK_PANEL = (83, 113, 5, 52, 64, 58, 21, 85, 7, 23)
CHECKPOINT_DOMAIN = b"tau2-luna-cloud-checkpoint:v1\0"


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def _checkpoint(value: dict[str, Any]) -> bytes:
    result = dict(value)
    result["checkpoint_hash"] = hashlib.sha256(CHECKPOINT_DOMAIN + _canonical(result)).hexdigest()
    return _canonical(result) + b"\n"


class FakeBlobAuthority:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects
        self.downloads: list[str] = []
        self.lists: list[str] = []

    def download(self, name: str) -> bytes:
        self.downloads.append(name)
        try:
            return self.objects[name]
        except KeyError as exc:
            raise FileNotFoundError(name) from exc

    def list(self, prefix: str) -> list[str]:
        self.lists.append(prefix)
        return sorted(name for name in self.objects if name.startswith(prefix))


def _panel_objects(run_id: str = "terra-panel-run") -> tuple[dict[str, bytes], bytes]:
    objects: dict[str, bytes] = {}
    records: list[dict[str, Any]] = []
    for task_id in TASK_PANEL:
        attempt_id = f"attempt-{task_id}"
        prefix = f"runs/{run_id}/tasks/{task_id}/attempts/{attempt_id}/"
        bundle_objects = {
            f"{prefix}bundle/manifest.json": _canonical({"task_id": task_id}) + b"\n",
            f"{prefix}events.jsonl": _canonical({"task_id": task_id, "lane": "events"}) + b"\n",
        }
        objects.update(bundle_objects)
        relay_name = f"runs/{run_id}/tasks/{task_id}/relays/{attempt_id}.json"
        relay = {
            "schema_version": "tau2-terra-relay/v1",
            "prefix": prefix,
            "inventory": [
                {
                    "remote_name": name,
                    "local_name": (
                        name.removeprefix(prefix)
                        if "/" in name.removeprefix(prefix)
                        else f"streams/{name.removeprefix(prefix)}"
                    ),
                    "size": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
                for name, data in sorted(bundle_objects.items())
            ],
        }
        objects[relay_name] = _canonical(relay) + b"\n"
        checkpoint_name = f"runs/{run_id}/tasks/{task_id}/checkpoint.json"
        objects[checkpoint_name] = _checkpoint(
            {
                "schema_version": "tau2-luna-cloud-checkpoint/v1",
                "task_id": str(task_id),
                "trial": 0,
                "attempts": [
                    {
                        "attempt_id": attempt_id,
                        "state": "COMPLETED",
                        "prefix": prefix,
                        "bundle_hash": hashlib.sha256(
                            bundle_objects[f"{prefix}bundle/manifest.json"]
                        ).hexdigest(),
                        "relay_checkpoint": relay_name,
                    }
                ],
            }
        )
        records.append(
            {
                "task_id": task_id,
                "state": "COMPLETED",
                "attempt_id": attempt_id,
                "relay_checkpoint": relay_name,
            }
        )
    panel = {
        "denominators": {
            "requested": 10,
            "completed": 10,
            "partial": 0,
            "invalid": 0,
            "skipped": 0,
        },
        "records": records,
    }
    panel_data = _canonical(panel) + b"\n"
    panel_hash = hashlib.sha256(panel_data).hexdigest()
    objects[f"runs/{run_id}/terra-panels/{panel_hash}.json"] = panel_data
    return objects, panel_data


def _relay_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("terra_cloud_relay_acceptance", CLOUD_RELAY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_panel_relay_downloads_and_verifies_all_fixed_tasks_plus_report(
    tmp_path: Path,
) -> None:
    module = _relay_module()
    objects, panel_data = _panel_objects()
    authority = FakeBlobAuthority(objects)
    verified: list[Path] = []

    def verifier(bundle: Path, **_: Any) -> dict[str, bool]:
        assert (bundle / "manifest.json").is_file()
        verified.append(bundle)
        return {"valid": True}

    report = module.relay_terra_panel(
        authority=authority,
        run_id="terra-panel-run",
        destination=tmp_path / "relay",
        secret_values=(),
        bundle_verifier=verifier,
    )

    assert report == {
        "valid": True,
        "task_ids": list(TASK_PANEL),
        "verified_bundles": 10,
        "panel_report": "terra-panel-report.json",
    }
    assert len(verified) == 10
    assert [int(path.parent.name.removeprefix("task-")) for path in verified] == list(TASK_PANEL)
    assert (tmp_path / "relay" / "terra-panel-report.json").read_bytes() == panel_data
    assert authority.lists.count("runs/terra-panel-run/terra-panels/") == 1


def test_panel_relay_refuses_when_any_fixed_task_relay_is_missing(tmp_path: Path) -> None:
    module = _relay_module()
    objects, _ = _panel_objects()
    missing = "runs/terra-panel-run/tasks/52/relays/attempt-52.json"
    del objects[missing]

    with pytest.raises(module.PanelRelayError, match=r"52|relay|incomplete"):
        module.relay_terra_panel(
            authority=FakeBlobAuthority(objects),
            run_id="terra-panel-run",
            destination=tmp_path / "relay",
            secret_values=(),
            bundle_verifier=lambda *_args, **_kwargs: {"valid": True},
        )


def test_panel_relay_refuses_if_any_local_bundle_fails_verification(tmp_path: Path) -> None:
    module = _relay_module()
    objects, _ = _panel_objects()

    def verifier(bundle: Path, **_: Any) -> dict[str, bool]:
        return {"valid": bundle.parent.name != "task-64"}

    with pytest.raises(module.PanelRelayError, match=r"64|verification|bundle"):
        module.relay_terra_panel(
            authority=FakeBlobAuthority(objects),
            run_id="terra-panel-run",
            destination=tmp_path / "relay",
            secret_values=(),
            bundle_verifier=verifier,
        )


def test_relay_control_plane_needs_only_run_identity_and_blob_custody() -> None:
    cloud = CLOUD_RELAY.read_text()
    azure = AZURE_RELAY.read_text()

    assert "TAU2_SMOKE_ATTEMPT_ID" not in cloud
    assert "TAU2_SMOKE_ATTEMPT_ID" not in azure
    assert "relay_terra_panel(" in cloud
    assert "az vm" not in cloud
    assert "az vm" not in azure
    assert azure.count("python scripts/cloud_relay.py") == 1
