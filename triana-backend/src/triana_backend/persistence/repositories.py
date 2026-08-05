from __future__ import annotations

import hashlib
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from triana_backend.domain.models import (
    ArtifactRef,
    IdempotencyConflictError,
    ImportRequest,
    ParsedImport,
    RegisteredImport,
    canonical_json,
    deterministic_id,
)

from .models import Agent, AgentVersion, Artifact, Import, Workspace


class SqlAlchemyImportRepository:
    """PostgreSQL registry; schema lifecycle remains an explicit Alembic step."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def register_import(
        self,
        *,
        request: ImportRequest,
        artifact: ArtifactRef,
        parsed: ParsedImport,
    ) -> RegisteredImport:
        identity: dict[str, Any] = {
            "source_sha256": artifact.content_sha256,
            "parser_version": request.parser_version,
            "evidence_class": request.evidence_class.value,
            "workspace_slug": request.workspace_slug,
            "agent_key": request.agent_key,
            "version_key": request.version_key,
        }
        identity_hash = hashlib.sha256(canonical_json(identity)).hexdigest()
        request_hash = hashlib.sha256(
            canonical_json({**identity, "idempotency_key": request.idempotency_key})
        ).hexdigest()
        workspace_id = deterministic_id("wsp", {"slug": request.workspace_slug})
        agent_id = deterministic_id(
            "agt", {"workspace_id": workspace_id, "agent_key": request.agent_key}
        )
        version_id = deterministic_id(
            "av", {"agent_id": agent_id, "version_key": request.version_key}
        )
        import_id = deterministic_id("imp", identity)

        with self._session.begin():
            keyed = self._session.scalar(
                select(Import).where(
                    Import.workspace_id == workspace_id,
                    Import.idempotency_key == request.idempotency_key,
                )
            )
            if keyed is not None:
                if keyed.idempotency_request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "idempotency key was already used for a different import"
                    )
                return RegisteredImport(
                    artifact_id=keyed.source_artifact_id,
                    import_id=keyed.id,
                    created=False,
                    parsed=_parsed_from_row(keyed, parsed.record_ids),
                )

            self._insert_if_absent(
                Workspace.__table__,
                {"id": workspace_id, "slug": request.workspace_slug},
            )
            self._insert_if_absent(
                Agent.__table__,
                {
                    "id": agent_id,
                    "workspace_id": workspace_id,
                    "agent_key": request.agent_key,
                },
            )
            self._insert_if_absent(
                AgentVersion.__table__,
                {
                    "id": version_id,
                    "agent_id": agent_id,
                    "version_key": request.version_key,
                },
            )
            self._insert_if_absent(
                Artifact.__table__,
                {
                    "id": artifact.id,
                    "artifact_kind": artifact.kind.value,
                    "content_sha256": artifact.content_sha256,
                    "byte_count": artifact.byte_count,
                    "media_type": artifact.media_type,
                    "storage_backend": "S3",
                    "storage_bucket": artifact.storage_bucket,
                    "storage_key": artifact.storage_key,
                    "kms_key_id": artifact.kms_key_id,
                    "checksum_sha256_b64": artifact.checksum_sha256_b64,
                    "availability": "AVAILABLE",
                },
            )
            created = self._session.execute(
                insert(cast(Any, Import.__table__))
                .values(
                    id=import_id,
                    workspace_id=workspace_id,
                    agent_version_id=version_id,
                    source_artifact_id=artifact.id,
                    source_sha256=artifact.content_sha256,
                    evidence_class=request.evidence_class.value,
                    parser_version=request.parser_version,
                    physical_record_count=parsed.physical_record_count,
                    usable_conversation_count=parsed.usable_conversation_count,
                    source_status_counts=dict(parsed.source_status_counts),
                    rejected_record_count=0,
                    rejection_summary={},
                    status="COMPLETED",
                    identity_hash=identity_hash,
                    idempotency_key=request.idempotency_key,
                    idempotency_request_hash=request_hash,
                )
                .on_conflict_do_nothing()
                .returning(Import.id)
            ).scalar_one_or_none()
            row = self._session.scalar(
                select(Import).where(Import.identity_hash == identity_hash)
            )
            if row is None:
                keyed = self._session.scalar(
                    select(Import).where(
                        Import.workspace_id == workspace_id,
                        Import.idempotency_key == request.idempotency_key,
                    )
                )
                if keyed is None:
                    raise RuntimeError("import uniqueness conflict did not resolve")
                if keyed.idempotency_request_hash != request_hash:
                    raise IdempotencyConflictError(
                        "idempotency key was concurrently used for a different import"
                    )
                row = keyed

            return RegisteredImport(
                artifact_id=row.source_artifact_id,
                import_id=row.id,
                created=created is not None,
                parsed=_parsed_from_row(row, parsed.record_ids),
            )

    def _insert_if_absent(self, table: Any, values: dict[str, Any]) -> None:
        statement = insert(cast(Any, table)).values(**values).on_conflict_do_nothing()
        self._session.execute(statement)


def _parsed_from_row(row: Import, record_ids: tuple[str, ...]) -> ParsedImport:
    return ParsedImport(
        physical_record_count=row.physical_record_count,
        usable_conversation_count=row.usable_conversation_count,
        source_status_counts=row.source_status_counts,
        record_ids=record_ids,
    )
