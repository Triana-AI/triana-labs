from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from triana_labs.report import ReportCompilationError, compile_hrai_normalized_trace_v2

from triana_backend.domain.models import (
    ArtifactKind,
    ArtifactStore,
    ImportRegistry,
    ImportRequest,
    ParsedImport,
    RegisteredImport,
    SourceValidationError,
)


@dataclass(frozen=True)
class RegisterS3Import:
    bucket: str
    key: str
    expected_sha256: str
    request: ImportRequest


class ImportService:
    def __init__(self, *, artifacts: ArtifactStore, registry: ImportRegistry) -> None:
        self._artifacts = artifacts
        self._registry = registry

    def register_s3(self, command: RegisterS3Import) -> RegisteredImport:
        artifact = self._artifacts.publish_staging(
            bucket=command.bucket,
            key=command.key,
            expected_sha256=command.expected_sha256,
            kind=ArtifactKind.SOURCE_TRACE_JSONL,
            media_type="application/x-ndjson",
        )
        source = self._artifacts.open_verified(artifact)
        try:
            source_bytes = source.read()
        finally:
            source.close()
        try:
            compiled = compile_hrai_normalized_trace_v2(
                source_bytes,
                evidence_class=command.request.evidence_class.value,
                expected_sha256=command.expected_sha256,
            )
        except ReportCompilationError as error:
            raise SourceValidationError(error.reason_code) from error
        fact_values = {fact.fact_kind: fact.value for fact in compiled.facts}
        status_counts = fact_values["source_status_counts"]
        if not isinstance(status_counts, dict):
            raise SourceValidationError("SOURCE_STATUS_COUNTS_INVALID")
        parsed = ParsedImport(
            physical_record_count=cast(int, fact_values["physical_record_count"]),
            usable_conversation_count=cast(
                int, fact_values["usable_conversation_count"]
            ),
            source_status_counts=cast(dict[str, int], status_counts),
            record_ids=(),
        )
        return self._registry.register_import(
            request=command.request, artifact=artifact, parsed=parsed
        )
