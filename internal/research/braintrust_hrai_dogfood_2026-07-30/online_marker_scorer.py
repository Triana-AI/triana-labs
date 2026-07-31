"""Braintrust-deployed scorer for a synthetic production marker."""

from typing import Any

import braintrust
from pydantic import BaseModel


project = braintrust.projects.create(name="My Project")


class MarkerParams(BaseModel):
    output: Any


def marker_present(output: Any) -> float:
    return float("ONLINE_SCORE_OK" in str(output))


project.scorers.create(
    name="HRAI synthetic online marker",
    slug="hrai-synthetic-online-marker",
    description="Scores only a non-sensitive synthetic production marker.",
    parameters=MarkerParams,
    handler=marker_present,
    metadata={"__pass_threshold": 0.5},
)
