from __future__ import annotations

import json
from dataclasses import dataclass, replace
from typing import cast

from triana_labs.report import (
    CompiledAnalysis,
    ReportCompilationError,
    compile_hrai_normalized_trace_v2,
    compile_preview_trace_v1,
)

from triana_backend.domain.models import (
    ArtifactKind,
    ArtifactStore,
    ImportRegistry,
    ImportRequest,
    ParsedImport,
    RegisteredImport,
    SourceValidationError,
)
from triana_backend.domain.parser import HRAI_NORMALIZED_TRACE_V2

PREVIEW_TRACE_V1 = "preview-trace-v1"


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
            compiled, parser_version = compile_registered_source(
                source_bytes,
                evidence_class=command.request.evidence_class.value,
                expected_sha256=command.expected_sha256,
                parser_version=command.request.parser_version,
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
            request=replace(command.request, parser_version=parser_version),
            artifact=artifact,
            parsed=parsed,
        )


def compile_registered_source(
    source_bytes: bytes,
    *,
    evidence_class: str,
    expected_sha256: str,
    parser_version: str,
) -> tuple[CompiledAnalysis, str]:
    """Dispatch only the two registered retained-source contracts."""

    selected = parser_version
    if parser_version == HRAI_NORMALIZED_TRACE_V2:
        first_line = source_bytes.split(b"\n", 1)[0]
        try:
            first = json.loads(first_line)
        except (UnicodeDecodeError, json.JSONDecodeError):
            first = None
        if isinstance(first, dict) and first.get("contract_kind") == "preview_trace":
            selected = PREVIEW_TRACE_V1
    if selected == PREVIEW_TRACE_V1:
        return (
            compile_preview_trace_v1(
                source_bytes,
                evidence_class=evidence_class,
                expected_sha256=expected_sha256,
            ),
            PREVIEW_TRACE_V1,
        )
    if selected == HRAI_NORMALIZED_TRACE_V2:
        return (
            compile_hrai_normalized_trace_v2(
                source_bytes,
                evidence_class=evidence_class,
                expected_sha256=expected_sha256,
            ),
            HRAI_NORMALIZED_TRACE_V2,
        )
    raise ReportCompilationError("SOURCE_CONTRACT_UNSUPPORTED")
