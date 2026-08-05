from __future__ import annotations

from dataclasses import dataclass

from triana_backend.domain.models import (
    ArtifactKind,
    ArtifactStore,
    ImportRegistry,
    ImportRequest,
    RegisteredImport,
)
from triana_backend.domain.parser import parse_hrai_normalized_traces


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
            parsed = parse_hrai_normalized_traces(source)
        finally:
            source.close()
        return self._registry.register_import(
            request=command.request, artifact=artifact, parsed=parsed
        )
