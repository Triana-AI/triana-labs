from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
BICEP_TEMPLATE = PROJECT_ROOT / "infra" / "main.bicep"


def test_vm_size_is_explicit_single_value_and_recorded_in_deployment_output() -> None:
    script = DEPLOY_SCRIPT.read_text()
    template = BICEP_TEMPLATE.read_text()

    assert re.search(r':\s+"\$\{TAU2_VM_SIZE:\?[^}]+\}"', script)
    assert 'vmSize="${TAU2_VM_SIZE}"' in script
    assert re.search(r"param\s+vmSize\s+string", template)
    assert re.search(r"hardwareProfile:\s*\{\s*vmSize:\s*vmSize\s*\}", template)
    assert re.search(r"output\s+vmSize\s+string\s*=\s*vmSize", template)

    combined = script + "\n" + template
    assert "Standard_B2s" not in combined
    assert "list-sizes" not in script
    assert "list-skus" not in script
    assert not re.search(r"for\s+\w*size\w*\s+in", script, flags=re.IGNORECASE)
    assert not re.search(r"while\s+.*(?:size|sku)", script, flags=re.IGNORECASE)
