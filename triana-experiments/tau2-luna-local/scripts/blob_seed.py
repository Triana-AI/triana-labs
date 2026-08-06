from __future__ import annotations

import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
    storage = required("TAU2_SEED_STORAGE")
    container = required("TAU2_SEED_CONTAINER")
    key_path = Path(required("AZURE_STORAGE_KEY_FILE"))
    archive = Path(required("TAU2_SEED_ARCHIVE"))
    digest = Path(required("TAU2_SEED_DIGEST"))
    source_prefix = required("TAU2_SEED_PREFIX")
    archive_name = required("TAU2_SEED_ARCHIVE_NAME")
    digest_name = required("TAU2_SEED_DIGEST_NAME")
    credential = key_path.read_text().strip()
    if not credential:
        raise RuntimeError("storage key file is empty")

    sources = {
        f"{source_prefix}{archive_name}": archive,
        f"{source_prefix}{digest_name}": digest,
    }
    expected_sizes = {name: path.stat().st_size for name, path in sources.items()}
    with BlobServiceClient(
        account_url=f"https://{storage}.blob.core.windows.net",
        credential=credential,
    ) as service:
        blobs = service.get_container_client(container)
        for name, path in sources.items():
            with path.open("rb") as payload:
                blobs.upload_blob(name=name, data=payload, overwrite=False)
        observed_sizes = {
            blob.name: blob.size for blob in blobs.list_blobs(name_starts_with=source_prefix)
        }

    if observed_sizes != expected_sizes:
        raise RuntimeError("immutable source seed inventory verification failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
