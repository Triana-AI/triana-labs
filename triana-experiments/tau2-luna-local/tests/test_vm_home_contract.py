from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VM_SCRIPT = PROJECT_ROOT / "scripts" / "vm_smoke.sh"


def test_vm_smoke_establishes_deterministic_home_before_uv_install_or_use() -> None:
    script = VM_SCRIPT.read_text()
    first_uv_boundary = script.index("https://astral.sh/uv/")
    first_home_expansion = script.index("${HOME}")
    prefix = script[: min(first_uv_boundary, first_home_expansion)]

    assignment = re.search(r"(?m)^export\s+HOME=(?P<value>[^\n]+)$", prefix)
    assert assignment is not None, (
        "Azure Run Command does not guarantee HOME; vm_smoke.sh must export it "
        "before installing or invoking uv"
    )
    value = assignment.group("value")
    assert "HOME" not in value
    assert value.strip().strip('"\'')
