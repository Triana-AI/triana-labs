"""Black-box helpers for the Triana Preview distribution facade."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

PREVIEW_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = PREVIEW_ROOT.parent
FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_preview_trace.jsonl"

_PROVIDER_MARKERS = (
    "TRIANA_BEHAVIOR_MAP_",
    "OPENAI_API_KEY",
    "AZURE_OPENAI_API_KEY",
)


def provider_disabled_environment(
    additions: Mapping[str, str] | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()
    for key in tuple(environment):
        if key.startswith(_PROVIDER_MARKERS) or key in _PROVIDER_MARKERS:
            environment.pop(key)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["TRIANA_PREVIEW_TEST_PROVIDER_CALL_TRAP"] = "1"
    source_paths = [
        os.fspath(PREVIEW_ROOT / "src"),
        os.fspath(REPOSITORY_ROOT / "triana-labs" / "src"),
    ]
    existing = environment.get("PYTHONPATH")
    if existing:
        source_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(source_paths)
    if additions:
        environment.update(additions)
    return environment


def run_preview(
    *arguments: str,
    environment: Mapping[str, str] | None = None,
    module: bool = True,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "triana_preview"] if module else ["triana-preview"]
    return subprocess.run(
        [*command, *arguments],
        cwd=PREVIEW_ROOT,
        env=dict(environment or provider_disabled_environment()),
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )


def analyze_arguments(
    source: Path,
    destination: Path,
    *,
    authorized: bool = True,
    agent: str = "Synthetic order-support agent for tracking deliveries.",
) -> list[str]:
    arguments = [
        "analyze",
        "--traces",
        os.fspath(source),
        "--agent",
        agent,
        "--output",
        os.fspath(destination),
    ]
    if authorized:
        arguments.append("--confirm-authorized-traces")
    return arguments


def machine_json(completed: subprocess.CompletedProcess[str]) -> dict[str, object]:
    stream = completed.stdout if completed.stdout.strip() else completed.stderr
    lines = [line for line in stream.splitlines() if line.strip()]
    assert lines, completed
    return json.loads(lines[-1])


@pytest.fixture
def synthetic_trace(tmp_path: Path) -> Path:
    destination = tmp_path / "synthetic.jsonl"
    destination.write_bytes(FIXTURE.read_bytes())
    return destination
