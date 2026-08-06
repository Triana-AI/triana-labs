from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
BLOB_SEED_SCRIPT = PROJECT_ROOT / "scripts" / "blob_seed.py"
VM_SCRIPT = PROJECT_ROOT / "scripts" / "vm_smoke.sh"

UPSTREAM_COMMIT = "f8de30c298689cbe0117d76a378e7315a17e5bd8"
TERRA_SOURCE_PREFIX = f"source/{UPSTREAM_COMMIT}/terra-10-v2/"
TERRA_ARCHIVE = "tau2-terra-10-v2.tar.gz"
TERRA_DIGEST = "tau2-terra-10-v2.sha256"


def test_terra_source_uses_new_immutable_identity_without_mutating_luna_seed() -> None:
    deploy = DEPLOY_SCRIPT.read_text()
    seed = BLOB_SEED_SCRIPT.read_text()

    assert f"TAU2_SEED_PREFIX={TERRA_SOURCE_PREFIX}" in deploy
    assert f"TAU2_SEED_ARCHIVE_NAME={TERRA_ARCHIVE}" in deploy
    assert f"TAU2_SEED_DIGEST_NAME={TERRA_DIGEST}" in deploy
    assert 'required("TAU2_SEED_PREFIX")' in seed
    assert "overwrite=False" in seed
    assert re.search(r"\bdelete_blob\b|\bdelete_blobs\b", seed) is None
    assert TERRA_ARCHIVE != "tau2-luna-local.tar.gz"
    assert TERRA_DIGEST != "tau2-luna-local.sha256"


def test_vm_bootstrap_downloads_the_exact_new_terra_source_identity() -> None:
    vm = VM_SCRIPT.read_text()

    assert f"source_prefix={TERRA_SOURCE_PREFIX.removesuffix('/')}" in vm
    assert f"for object in {TERRA_ARCHIVE} {TERRA_DIGEST}" in vm
    assert f'"${{work_dir}}/{TERRA_ARCHIVE}"' in vm
    assert f'"${{work_dir}}/{TERRA_DIGEST}"' in vm
    assert "tau2-luna-local.tar.gz" not in vm
    assert "tau2-luna-local.sha256" not in vm
