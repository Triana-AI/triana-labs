from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
BLOB_SEED_SCRIPT = PROJECT_ROOT / "scripts" / "blob_seed.py"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"


def test_deploy_seeds_immutable_source_only_through_pinned_python_blob_sdk() -> None:
    deploy = DEPLOY_SCRIPT.read_text()

    assert re.search(r"\baz\s+storage\s+blob\b", deploy) is None
    assert 'AZURE_STORAGE_KEY_FILE="${storage_secret_file}"' in deploy
    assert "scripts/blob_seed.py" in deploy
    assert "tau2-luna-local.tar.gz" in deploy
    assert "tau2-luna-local.sha256" in deploy
    assert re.search(
        r"keyvault\s+secret\s+set.*?--name\s+storage-account-key"
        r".*?--file\s+\"\$\{storage_secret_file\}\".*?--output\s+none",
        deploy,
        flags=re.DOTALL,
    )

    assert BLOB_SEED_SCRIPT.is_file()
    seed = BLOB_SEED_SCRIPT.read_text()
    assert "from azure.storage.blob import BlobServiceClient" in seed
    assert 'required("AZURE_STORAGE_KEY_FILE")' in seed
    assert ".read_text()" in seed
    assert "overwrite=False" in seed
    assert "list_blobs" in seed
    assert "print(" not in seed

    project = PYPROJECT.read_text()
    assert '"azure-storage-blob==12.27.1"' in project
