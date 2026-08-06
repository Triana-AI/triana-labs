"""PostgreSQL persistence for owner-scoped self-serve resources."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from triana_backend.api.contracts import IntegrityConflict, ResourceNotFound
from triana_backend.application.self_serve import ParsedConversation, SafeRejection
from triana_backend.domain.models import canonical_json, deterministic_id

from .models import (
    Agent,
    AgentVersion,
    Artifact,
    FeatureAccessRequest,
    Import,
    ImportedConversation,
    ImportRejection,
    User,
    Workspace,
    WorkspaceFeatureEntitlement,
    WorkspaceMembership,
)


class SqlAlchemySelfServeRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get_or_create_me(self, owner_subject: str) -> Mapping[str, Any]:
        subject_hash = _subject_hash(owner_subject)
        user_id = deterministic_id("usr", {"subject_hash": subject_hash})
        workspace_id = deterministic_id("wsp", {"owner_user_id": user_id})
        with self._sessions() as session, session.begin():
            session.execute(
                insert(cast(Any, User.__table__))
                .values(id=user_id, subject_hash=subject_hash)
                .on_conflict_do_nothing(index_elements=["subject_hash"])
            )
            session.execute(
                insert(cast(Any, Workspace.__table__))
                .values(id=workspace_id, slug=f"personal-{subject_hash[:20]}")
                .on_conflict_do_nothing(index_elements=["slug"])
            )
            session.execute(
                insert(cast(Any, WorkspaceMembership.__table__))
                .values(user_id=user_id, workspace_id=workspace_id, role="OWNER")
                .on_conflict_do_nothing()
            )
        return {
            "owner_subject": owner_subject,
            "workspace": {"workspace_id": workspace_id},
        }

    def create_agent(self, owner_subject: str, display_name: str) -> Mapping[str, Any]:
        workspace_id = _workspace_id(owner_subject)
        self.get_or_create_me(owner_subject)
        agent_key = _agent_key(display_name)
        agent_id = deterministic_id(
            "agt", {"workspace_id": workspace_id, "agent_key": agent_key}
        )
        version_id = deterministic_id(
            "av", {"agent_id": agent_id, "version_key": "default"}
        )
        try:
            with self._sessions() as session, session.begin():
                if (
                    session.scalar(
                        select(Agent.id).where(
                            Agent.workspace_id == workspace_id,
                            Agent.agent_key == agent_key,
                        )
                    )
                    is not None
                ):
                    raise IntegrityConflict("agent", agent_id, "DUPLICATE_AGENT")
                session.add(
                    Agent(
                        id=agent_id,
                        workspace_id=workspace_id,
                        agent_key=agent_key,
                        display_name=display_name,
                    )
                )
                session.add(
                    AgentVersion(
                        id=version_id, agent_id=agent_id, version_key="default"
                    )
                )
        except IntegrityError as error:
            raise IntegrityConflict("agent", agent_id, "DUPLICATE_AGENT") from error
        return self.get_agent(owner_subject, agent_id)

    def list_agents(self, owner_subject: str) -> Sequence[Mapping[str, Any]]:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            rows = session.scalars(
                select(Agent)
                .where(Agent.workspace_id == workspace_id)
                .order_by(Agent.created_at, Agent.id)
            ).all()
            return [_agent_projection(row) for row in rows]

    def get_agent(self, owner_subject: str, agent_id: str) -> Mapping[str, Any]:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.scalar(
                select(Agent).where(
                    Agent.id == agent_id, Agent.workspace_id == workspace_id
                )
            )
            if row is None:
                raise ResourceNotFound("agent", agent_id)
            return _agent_projection(row)

    def persist_import(
        self,
        owner_subject: str,
        agent_id: str,
        *,
        filename: str,
        source: Mapping[str, Any],
        source_sha256: str,
        idempotency_key: str,
        conversations: Sequence[ParsedConversation],
        rejections: Sequence[SafeRejection],
    ) -> Mapping[str, Any]:
        del filename  # Filename is deliberately not retained in V0 metadata.
        workspace_id = _workspace_id(owner_subject)
        self.get_agent(owner_subject, agent_id)
        version_id = deterministic_id(
            "av", {"agent_id": agent_id, "version_key": "default"}
        )
        request_hash = hashlib.sha256(
            canonical_json({"agent_id": agent_id, "source_sha256": source_sha256})
        ).hexdigest()
        scoped_idempotency_key = hashlib.sha256(
            canonical_json(
                {"agent_id": agent_id, "client_idempotency_key": idempotency_key}
            )
        ).hexdigest()
        import_id = deterministic_id(
            "imp",
            {
                "workspace_id": workspace_id,
                "agent_id": agent_id,
                "source_sha256": source_sha256,
            },
        )
        status = (
            "FAILED"
            if not conversations
            else "COMPLETED"
            if not rejections
            else "COMPLETED_WITH_REJECTIONS"
        )
        with self._sessions() as session, session.begin():
            keyed = session.scalar(
                select(Import).where(
                    Import.workspace_id == workspace_id,
                    Import.idempotency_key == scoped_idempotency_key,
                )
            )
            if keyed is not None:
                if keyed.idempotency_request_hash != request_hash:
                    raise IntegrityConflict("import", keyed.id, "IDEMPOTENCY_CONFLICT")
                return _import_projection(keyed, agent_id=agent_id)
            existing = session.get(Import, import_id)
            if existing is not None:
                return _import_projection(existing, agent_id=agent_id)
            artifact_id = str(source["artifact_id"])
            session.add(
                Artifact(
                    id=artifact_id,
                    workspace_id=workspace_id,
                    artifact_kind="SOURCE_TRACE_JSONL",
                    content_sha256=source_sha256,
                    byte_count=int(source["byte_count"]),
                    media_type=str(source["media_type"]),
                    storage_backend="S3",
                    storage_bucket=str(source["storage_bucket"]),
                    storage_key=str(source["storage_key"]),
                    kms_key_id=str(source["kms_key_id"]),
                    checksum_sha256_b64=str(source["checksum_sha256_b64"]),
                    availability="AVAILABLE",
                )
            )
            row = Import(
                id=import_id,
                workspace_id=workspace_id,
                agent_version_id=version_id,
                source_artifact_id=artifact_id,
                source_sha256=source_sha256,
                evidence_class="CUSTOMER_AUTHORIZED_TRACE_DATA",
                parser_version="preview-trace-v1",
                physical_record_count=len(conversations) + len(rejections),
                usable_conversation_count=len(conversations),
                source_status_counts={
                    "ACCEPTED": len(conversations),
                    "REJECTED": len(rejections),
                },
                rejected_record_count=len(rejections),
                rejection_summary=_rejection_counts(rejections),
                status=status,
                identity_hash=hashlib.sha256(
                    canonical_json({"import_id": import_id})
                ).hexdigest(),
                idempotency_key=scoped_idempotency_key,
                idempotency_request_hash=request_hash,
            )
            session.add(row)
            for conversation in conversations:
                session.add(
                    ImportedConversation(
                        id=deterministic_id(
                            "cnv",
                            {
                                "import_id": import_id,
                                "line_number": conversation.line_number,
                            },
                        ),
                        import_id=import_id,
                        line_number=conversation.line_number,
                        trace_id=conversation.trace_id,
                        source_trace_id=conversation.source_trace_id,
                        events_json=conversation.events,
                    )
                )
            for rejection in rejections:
                session.add(
                    ImportRejection(
                        id=deterministic_id(
                            "rej",
                            {
                                "import_id": import_id,
                                "line_number": rejection.line_number,
                            },
                        ),
                        import_id=import_id,
                        line_number=rejection.line_number,
                        code=rejection.code,
                        json_pointer=rejection.json_pointer,
                        safe_message=rejection.safe_message,
                    )
                )
            session.flush()
            return _import_projection(row, agent_id=agent_id)

    def list_agent_imports(
        self, owner_subject: str, agent_id: str
    ) -> Sequence[Mapping[str, Any]]:
        self.get_agent(owner_subject, agent_id)
        version_id = deterministic_id(
            "av", {"agent_id": agent_id, "version_key": "default"}
        )
        with self._sessions() as session:
            rows = session.scalars(
                select(Import)
                .where(Import.agent_version_id == version_id)
                .order_by(Import.created_at.desc(), Import.id)
            ).all()
            return [_import_projection(row, agent_id=agent_id) for row in rows]

    def get_import(self, owner_subject: str, import_id: str) -> Mapping[str, Any]:
        row = self._owned_import(owner_subject, import_id)
        with self._sessions() as session:
            version = session.get(AgentVersion, row.agent_version_id)
            if version is None:
                raise ResourceNotFound("import", import_id)
            return _import_projection(row, agent_id=version.agent_id)

    def list_import_conversations(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]:
        self._owned_import(owner_subject, import_id)
        with self._sessions() as session:
            rows = session.scalars(
                select(ImportedConversation)
                .where(ImportedConversation.import_id == import_id)
                .order_by(ImportedConversation.line_number)
            ).all()
            return [_conversation_projection(row, include_events=False) for row in rows]

    def list_import_rejections(
        self, owner_subject: str, import_id: str
    ) -> Sequence[Mapping[str, Any]]:
        self._owned_import(owner_subject, import_id)
        with self._sessions() as session:
            rows = session.scalars(
                select(ImportRejection)
                .where(ImportRejection.import_id == import_id)
                .order_by(ImportRejection.line_number)
            ).all()
            return [
                {
                    "line_number": row.line_number,
                    "code": row.code,
                    "json_pointer": row.json_pointer,
                    "safe_message": row.safe_message,
                }
                for row in rows
            ]

    def get_conversation(
        self, owner_subject: str, conversation_id: str
    ) -> Mapping[str, Any]:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.scalar(
                select(ImportedConversation)
                .join(Import, Import.id == ImportedConversation.import_id)
                .where(
                    ImportedConversation.id == conversation_id,
                    Import.workspace_id == workspace_id,
                )
            )
            if row is None:
                raise ResourceNotFound("conversation", conversation_id)
            return _conversation_projection(row, include_events=True)

    def _owned_import(self, owner_subject: str, import_id: str) -> Import:
        workspace_id = _workspace_id(owner_subject)
        with self._sessions() as session:
            row = session.scalar(
                select(Import).where(
                    Import.id == import_id, Import.workspace_id == workspace_id
                )
            )
            if row is None:
                raise ResourceNotFound("import", import_id)
            session.expunge(row)
            return row

    def list_feature_state(self, owner_subject: str) -> tuple[set[str], set[str]]:
        workspace_id = _workspace_id(owner_subject)
        self.get_or_create_me(owner_subject)
        with self._sessions() as session:
            entitled = set(
                session.scalars(
                    select(WorkspaceFeatureEntitlement.feature_key).where(
                        WorkspaceFeatureEntitlement.workspace_id == workspace_id,
                        WorkspaceFeatureEntitlement.state == "AVAILABLE",
                    )
                ).all()
            )
            requested = set(
                session.scalars(
                    select(FeatureAccessRequest.feature_key).where(
                        FeatureAccessRequest.workspace_id == workspace_id
                    )
                ).all()
            )
            return entitled, requested

    def create_feature_access_request(
        self, owner_subject: str, feature_key: str
    ) -> None:
        workspace_id = _workspace_id(owner_subject)
        self.get_or_create_me(owner_subject)
        request_id = deterministic_id(
            "far", {"workspace_id": workspace_id, "feature_key": feature_key}
        )
        with self._sessions() as session, session.begin():
            session.execute(
                insert(cast(Any, FeatureAccessRequest.__table__))
                .values(
                    id=request_id,
                    workspace_id=workspace_id,
                    feature_key=feature_key,
                )
                .on_conflict_do_nothing(index_elements=["workspace_id", "feature_key"])
            )


def _subject_hash(subject: str) -> str:
    return hashlib.sha256(subject.encode("utf-8")).hexdigest()


def _workspace_id(subject: str) -> str:
    return deterministic_id(
        "wsp",
        {
            "owner_user_id": deterministic_id(
                "usr", {"subject_hash": _subject_hash(subject)}
            )
        },
    )


def _agent_key(display_name: str) -> str:
    normalized = re.sub(r"\s+", "-", display_name.strip().lower())
    return normalized[:96]


def _agent_projection(row: Agent) -> dict[str, Any]:
    return {
        "agent_id": row.id,
        "workspace_id": row.workspace_id,
        "display_name": row.display_name or row.agent_key,
        "default_version": {"version_key": "default"},
    }


def _import_projection(row: Import, *, agent_id: str) -> dict[str, Any]:
    return {
        "import_id": row.id,
        "agent_id": agent_id,
        "status": row.status,
        "physical_record_count": row.physical_record_count,
        "accepted_conversation_count": row.usable_conversation_count,
        "rejected_record_count": row.rejected_record_count,
        "source_sha256": row.source_sha256,
        "privacy_class": row.evidence_class,
    }


def _conversation_projection(
    row: ImportedConversation, *, include_events: bool
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "conversation_id": row.id,
        "import_id": row.import_id,
        "line_number": row.line_number,
        "trace_id": row.trace_id,
        "source_trace_id": row.source_trace_id,
    }
    if include_events:
        result["events"] = list(row.events_json)
    return result


def _rejection_counts(rows: Sequence[SafeRejection]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.code] = counts.get(row.code, 0) + 1
    return counts
