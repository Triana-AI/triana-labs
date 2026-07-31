"""Source and built-wheel command parity for Corpus Intelligence."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

from conftest import PROJECT_ROOT, build_observer_bundle


def test_source_and_built_wheel_have_derivation_parity(
    run_cli: Any, tmp_path: Path
) -> None:
    uv = shutil.which("uv")
    assert uv is not None
    dist = tmp_path / "dist"
    build = subprocess.run(
        [uv, "build", "--project", str(PROJECT_ROOT), "--out-dir", str(dist)],
        cwd=PROJECT_ROOT.parent,
        check=False,
        capture_output=True,
        timeout=60,
    )
    assert build.returncode == 0, build.stderr.decode(errors="replace")
    wheel = next(dist.glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(installed)
        names = archive.namelist()
    assert any(name.startswith("triana_labs/intelligence/") for name in names)

    manifest = build_observer_bundle(tmp_path / "observed")
    source_output = tmp_path / "source-output"
    installed_output = tmp_path / "installed-output"
    source = run_cli("corpus", "derive", manifest, "--out", source_output)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(installed)
    packaged = subprocess.run(
        [
            sys.executable,
            "-m",
            "triana_labs",
            "corpus",
            "derive",
            str(manifest),
            "--out",
            str(installed_output),
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        capture_output=True,
        timeout=30,
    )
    assert source.returncode == packaged.returncode == 10
    assert source.stdout.replace(str(source_output).encode(), b"<OUTPUT>") == (
        packaged.stdout.replace(str(installed_output).encode(), b"<OUTPUT>")
    )
    assert {
        path.relative_to(source_output): path.read_bytes()
        for path in source_output.rglob("*")
        if path.is_file()
    } == {
        path.relative_to(installed_output): path.read_bytes()
        for path in installed_output.rglob("*")
        if path.is_file()
    }
