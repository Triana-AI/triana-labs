from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "azure_deploy.sh"
RUN_SCRIPT = PROJECT_ROOT / "scripts" / "azure_run.sh"


def test_deploy_preserves_terra_100k_capacity_while_luna_remains_capacity_one() -> None:
    deploy = DEPLOY_SCRIPT.read_text()

    assert re.search(r"^deployment_capacity=1$", deploy, flags=re.MULTILINE)
    terra_branch = re.search(
        r'if test "\$\{TAU2_LUNA_DEPLOYMENT\}" = gpt-5-6-terra-sentinel; then'
        r"(?P<body>.*?)^fi$",
        deploy,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert terra_branch is not None
    assert re.search(r"^\s*deployment_capacity=100$", terra_branch.group("body"), re.MULTILINE)
    assert '--sku-capacity "${deployment_capacity}"' in deploy
    assert "--sku-capacity 1" not in deploy


def test_run_preflight_queries_and_requires_exact_terra_capacity_100() -> None:
    run = RUN_SCRIPT.read_text()

    assert "capacity:sku.capacity" in run
    assert re.search(
        r'model_name:\$model,model_version:"2026-07-09",'
        r'sku:"GlobalStandard",capacity:100',
        run,
    )
