"""Distribution and verification-surface acceptance checks."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from conftest import PROJECT_ROOT, REPOSITORY_ROOT


def test_project_metadata_and_dependencies_are_bounded() -> None:
    project = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert project["project"]["name"] == "triana-labs"
    assert project["project"]["requires-python"] == "==3.13.14"
    assert project["project"]["scripts"] == {"triana": "triana_labs.cli:main"}
    assert project["project"]["dependencies"] == ["pydantic>=2,<3"]
    assert set(project["dependency-groups"]["dev"]) == {
        "hypothesis>=6,<7",
        "mypy>=1,<2",
        "pytest>=9,<10",
        "ruff>=0.12,<1",
    }
    assert project["build-system"]["requires"] == ["uv_build==0.12.0"]


def test_lock_is_present_and_contains_no_editable_external_source() -> None:
    lock = (PROJECT_ROOT / "uv.lock").read_text()

    assert lock
    assert 'name = "triana-labs"' in lock
    assert "git+" not in lock
    assert "http://" not in lock


def test_source_module_and_console_entrypoint_have_help_parity(run_cli: Any) -> None:
    source = run_cli("--help")
    executable = shutil.which("triana")
    assert executable is not None
    installed = subprocess.run(
        [executable, "--help"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        timeout=30,
    )

    assert (source.returncode, source.stdout, source.stderr) == (
        installed.returncode,
        installed.stdout,
        installed.stderr,
    )


def test_package_build_contains_modules_but_not_tests_or_fixtures(
    tmp_path: Path,
) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    output = tmp_path / "dist"
    completed = subprocess.run(
        [
            uv,
            "build",
            "--project",
            str(PROJECT_ROOT),
            "--out-dir",
            str(output),
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")

    wheel = next(output.glob("*.whl"))
    listing = subprocess.run(
        [
            sys.executable,
            "-m",
            "zipfile",
            "-l",
            str(wheel),
        ],
        check=False,
        capture_output=True,
        timeout=30,
    )
    names = listing.stdout.decode()
    assert listing.returncode == 0
    assert "triana_labs/__init__.py" in names
    assert "triana_labs/__main__.py" in names
    assert "triana_labs/cli.py" in names
    assert "tests/" not in names
    assert "fixtures/" not in names
