"""Strict mutation request models for the versioned API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SourceLocatorModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bucket: str = Field(min_length=1)
    key: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class ImportRegistrationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workspace_slug: str = Field(min_length=1)
    agent_key: str = Field(min_length=1)
    version_key: str = Field(min_length=1)
    source: SourceLocatorModel
    evidence_class: str = Field(min_length=1)


class RunStartModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    import_id: str = Field(min_length=1)
    rerun: bool = False
