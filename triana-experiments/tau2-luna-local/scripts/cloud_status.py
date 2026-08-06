from __future__ import annotations

import json
import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from tau2_luna_local.cloud_smoke import AzureBlobAuthority
from tau2_luna_local.serde import canonical_bytes


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
    storage = required("TAU2_SMOKE_STORAGE")
    run_id = required("TAU2_SMOKE_RUN_ID")
    state = required("TAU2_STATUS_STATE")
    if state != "RUNNING":
        raise RuntimeError("bootstrap status publisher only accepts RUNNING")
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)
    storage_key = SecretClient(
        vault_url=required("TAU2_SMOKE_VAULT_URI"), credential=credential
    ).get_secret("storage-account-key").value
    if not storage_key:
        raise RuntimeError("managed identity did not resolve storage custody")
    authority = AzureBlobAuthority(
        account_url=f"https://{storage}.blob.core.windows.net",
        container="tau2-smoke",
        credential=storage_key,
    )
    payload = {"state": state, "run_id": run_id, "service": "tau2-retail-discovery.service"}
    name = f"runs/{run_id}/status.json"
    data = canonical_bytes(payload) + b"\n"
    authority.put(name, data, overwrite=True)
    if authority.download(name) != data:
        raise RuntimeError("RUNNING Blob handoff verification failed")
    print(json.dumps({**payload, "blob_status_verified": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
