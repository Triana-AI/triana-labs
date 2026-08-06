from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, BinaryIO, Protocol


class EvidenceClass(StrEnum):
    SYNTHETIC_EXISTING_TRACE_CORPUS = "SYNTHETIC_EXISTING_TRACE_CORPUS"


class ArtifactKind(StrEnum):
    SOURCE_TRACE_JSONL = "SOURCE_TRACE_JSONL"
    LABS_ANALYSIS_FACTS = "LABS_ANALYSIS_FACTS"
    LABS_REPORT = "LABS_REPORT"
    TRACE_TO_EVAL_REPORT = "TRACE_TO_EVAL_REPORT"
    TRACE_TO_EVAL_REVIEW_QUEUE = "TRACE_TO_EVAL_REVIEW_QUEUE"
    TRACE_TO_EVAL_CONVERSATIONS = "TRACE_TO_EVAL_CONVERSATIONS"
    TRACE_TO_EVAL_RULING = "TRACE_TO_EVAL_RULING"


class ArtifactAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"


class ImportState(StrEnum):
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class BoundaryError(RuntimeError):
    """A typed refusal at an external or data-integrity boundary."""

    code = "BOUNDARY_ERROR"


class ArtifactIntegrityError(BoundaryError):
    code = "ARTIFACT_INTEGRITY_FAILED"


class SourceValidationError(BoundaryError):
    code = "SOURCE_VALIDATION_FAILED"


class IdempotencyConflictError(BoundaryError):
    code = "IDEMPOTENCY_CONFLICT"


@dataclass(frozen=True)
class ArtifactRef:
    id: str
    kind: ArtifactKind
    content_sha256: str
    byte_count: int
    media_type: str
    storage_bucket: str
    storage_key: str
    kms_key_id: str
    checksum_sha256_b64: str


@dataclass(frozen=True)
class ParsedImport:
    physical_record_count: int
    usable_conversation_count: int
    source_status_counts: Mapping[str, int]
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class ImportRequest:
    workspace_slug: str
    agent_key: str
    version_key: str
    evidence_class: EvidenceClass
    parser_version: str
    idempotency_key: str


@dataclass(frozen=True)
class RegisteredImport:
    artifact_id: str
    import_id: str
    created: bool
    parsed: ParsedImport


class ArtifactStore(Protocol):
    def publish_staging(
        self,
        *,
        bucket: str,
        key: str,
        expected_sha256: str,
        kind: ArtifactKind,
        media_type: str,
    ) -> ArtifactRef: ...

    def open_verified(self, ref: ArtifactRef) -> BinaryIO: ...

    def head(self, ref: ArtifactRef) -> ArtifactAvailability: ...


class ImportRegistry(Protocol):
    def register_import(
        self,
        *,
        request: ImportRequest,
        artifact: ArtifactRef,
        parsed: ParsedImport,
    ) -> RegisteredImport: ...


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def deterministic_id(prefix: str, identity: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(identity)).hexdigest()
    return f"{prefix}_{digest[:32]}"
