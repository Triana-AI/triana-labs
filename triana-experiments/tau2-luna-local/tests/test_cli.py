from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("tau2_luna_local") is None,
    reason="production package absent; test_package_contract owns the RED signal",
)


def test_verify_command_reports_valid_bundle(valid_bundle: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from tau2_luna_local.cli import main

    assert main(["verify", str(valid_bundle)]) == 0
    assert '"valid": true' in capsys.readouterr().out.lower()


def test_run_command_refuses_missing_explicit_environment_before_egress(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from tau2_luna_local.cli import main

    for name in ("AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION", "TAU2_LUNA_DEPLOYMENT"):
        monkeypatch.delenv(name, raising=False)
    assert main(["run"]) != 0
    stderr = capsys.readouterr().err
    assert "AZURE_API_KEY" in stderr
    assert "traceback" not in stderr.lower()
