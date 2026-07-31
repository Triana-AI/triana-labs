"""Normative schemas, CLI terminal shape, and built-wheel parity."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from conftest import PROJECT_ROOT, SCHEMA_ROOT, run_cli


def test_normative_provider_schemas_parse_at_frozen_hashes() -> None:
    expected = {
        "proposal.schema.json": "1dca47393765106083de920baf9beaf28d7afa10a05a4da9241e58c2cbacafd4",
        "critique.schema.json": "7dd625aeb57ae7b207638c87e4176ab51e940bf176ddab9976534e1d5a21bc5d",
    }
    for name, digest in expected.items():
        payload = (SCHEMA_ROOT / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == digest
        assert json.loads(payload)["additionalProperties"] is False


def test_cli_usage_terminal_is_exact_and_redacted() -> None:
    private = "PRIVATE_CASE_FACTORY_PATH"
    result = run_cli("cases", "generate", private)
    assert result.returncode == 2
    assert result.stdout == b""
    assert json.loads(result.stderr) == {
        "command": "cases.generate",
        "duration_ms": 0,
        "event_name": "triana.cases.generate.rejected",
        "outcome": "REJECTED",
        "reason_code": "CLI_USAGE_ERROR",
        "service": "triana-labs-cli",
        "service_version": "0.0.0",
        "severity": "ERROR",
    }
    assert private.encode() not in result.stderr


def test_built_wheel_contains_case_factory_and_has_help_parity(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    built = subprocess.run(
        [uv, "build", "--project", str(PROJECT_ROOT), "--out-dir", str(dist)],
        cwd=PROJECT_ROOT.parent,
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    wheel = next(dist.glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        archive.extractall(installed)
    assert any(name.startswith("triana_labs/case_factory/") for name in names)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(installed)
    packaged = subprocess.run(
        [sys.executable, "-m", "triana_labs", "cases", "generate", "--help"],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        timeout=30,
    )
    source = run_cli("cases", "generate", "--help")
    assert (source.returncode, source.stdout, source.stderr) == (
        packaged.returncode,
        packaged.stdout,
        packaged.stderr,
    )
