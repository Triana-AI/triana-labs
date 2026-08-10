"""Black-box runtime acceptance for an already-built Triana Preview image."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from conftest import PREVIEW_ROOT

_IMAGE_ENV = "TRIANA_PREVIEW_RUNTIME_IMAGE"


def test_dockerfile_installs_runtime_packages_without_build_path_links() -> None:
    dockerfile = (PREVIEW_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "uv sync --locked --no-dev --no-editable" in dockerfile


def _docker(
    image: str,
    *,
    docker_arguments: tuple[str, ...] = (),
    command: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("TRIANA_BEHAVIOR_MAP_")
        and not key.startswith("AZURE_")
        and key not in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY"}
    }
    return subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            *docker_arguments,
            image,
            *command,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
        env=environment,
    )


@pytest.mark.skipif(
    not os.environ.get(_IMAGE_ENV),
    reason=f"set {_IMAGE_ENV} to an independently built local image",
)
def test_final_image_imports_package_and_runs_provider_disabled_product(
    tmp_path: Path,
) -> None:
    image = os.environ[_IMAGE_ENV]

    imported = _docker(
        image,
        docker_arguments=("--entrypoint", "/opt/triana-preview/bin/python"),
        command=("-c", "import triana_preview; print(triana_preview.__file__)"),
    )
    assert imported.returncode == 0, imported.stderr
    assert "triana_preview" in imported.stdout

    helped = _docker(
        image,
        docker_arguments=("--entrypoint", "triana-preview"),
        command=("--help",),
    )
    assert helped.returncode == 0, helped.stderr
    assert "analyze" in helped.stdout

    trace = PREVIEW_ROOT / "tests" / "fixtures" / "synthetic_preview_trace.jsonl"
    output_mount = tmp_path / "container-output"
    output_mount.mkdir(mode=0o777)
    output_mount.chmod(0o777)
    completed = _docker(
        image,
        docker_arguments=(
            "--mount",
            (
                f"type=bind,src={trace.resolve()},"
                "dst=/triana/input/traces.jsonl,readonly"
            ),
            "--mount",
            f"type=bind,src={output_mount.resolve()},dst=/triana/output",
        ),
        command=(
            "analyze",
            "--traces",
            "/triana/input/traces.jsonl",
            "--agent",
            "Synthetic order-support agent.",
            "--output",
            "/triana/output/report",
            "--confirm-authorized-traces",
        ),
    )
    assert completed.returncode == 10, completed.stderr
    receipt = json.loads(completed.stdout.splitlines()[-1])
    assert receipt["outcome"] == "COMPLETED_WITH_GAPS"
    assert receipt["provider_calls"] == 0
    assert (output_mount / "report" / "behavior-map.json").is_file()
