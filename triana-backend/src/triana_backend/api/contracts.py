"""Framework-neutral API records and repository ports.

Only immutable identifiers and JSON-compatible projections cross these ports.
Infrastructure adapters retain ownership of SQL sessions and S3 streams.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

JsonObject = Mapping[str, Any]


class Availability(StrEnum):
    AVAILABLE = "AVAILABLE"
    AVAILABLE_WITH_GAPS = "AVAILABLE_WITH_GAPS"
    DEGRADED_ARTIFACT_MISSING = "DEGRADED_ARTIFACT_MISSING"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class ImportRegistration:
    workspace_slug: str
    agent_key: str
    version_key: str
    source_bucket: str
    source_key: str
    source_sha256: str
    evidence_class: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class RunStart:
    import_id: str
    idempotency_key: str
    rerun: bool = False


@dataclass(frozen=True, slots=True)
class ResourceUnavailable(Exception):
    """A resource exists, but its required artifact cannot be verified."""

    resource_kind: str
    resource_id: str
    availability: Availability
    code: str = "ARTIFACT_MISSING"


@dataclass(frozen=True, slots=True)
class ResourceNotFound(Exception):
    resource_kind: str
    resource_id: str


@dataclass(frozen=True, slots=True)
class IntegrityConflict(Exception):
    resource_kind: str
    resource_id: str
    code: str = "INTEGRITY_CONFLICT"


@dataclass(frozen=True, slots=True)
class AnalysisNotReady(Exception):
    """The canonical Labs compiler required to create a report is absent."""

    code: str = "LABS_ANALYSIS_NOT_READY"
    availability: Availability = Availability.UNAVAILABLE


class BackendReadPort(Protocol):
    """Read behavior required by `/api/v1`; implementations may use RDS/S3."""

    def get_report(self, report_id: str) -> JsonObject: ...

    def get_import(self, import_id: str) -> JsonObject: ...

    def get_import_record(self, import_id: str, record_id: str) -> JsonObject: ...

    def get_conversation(self, conversation_id: str) -> JsonObject: ...

    def get_run(self, run_id: str) -> JsonObject: ...

    def list_agents(self) -> Sequence[JsonObject]: ...

    def list_agent_versions(self, agent_id: str) -> Sequence[JsonObject]: ...


class ImportCommandPort(Protocol):
    def register_import(self, request: ImportRegistration) -> JsonObject: ...


class RunCommandPort(Protocol):
    def start_or_get_run(self, request: RunStart) -> JsonObject: ...
