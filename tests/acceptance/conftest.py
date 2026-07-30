"""Acceptance harness configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from hypothesis import Phase, settings

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "tests"))

settings.register_profile(
    "slice0a",
    max_examples=200,
    deadline=None,
    database=None,
    phases=(Phase.generate, Phase.shrink),
    derandomize=False,
    report_multiple_bugs=True,
    suppress_health_check=(),
)
settings.load_profile("slice0a")


@pytest.fixture(scope="session")
def fixture_manifest() -> dict[str, object]:
    return json.loads((FIXTURES / "manifest.json").read_text())
