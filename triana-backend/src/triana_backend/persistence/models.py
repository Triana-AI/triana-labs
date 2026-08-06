from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"
    __table_args__ = (UniqueConstraint("slug"), {"schema": "app"})
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), nullable=False)


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("subject_hash"), {"schema": "app"})
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    subject_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class WorkspaceMembership(TimestampMixin, Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = ({"schema": "app"},)
    user_id: Mapped[str] = mapped_column(
        ForeignKey("app.users.id", ondelete="RESTRICT"), primary_key=True
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("app.workspaces.id", ondelete="RESTRICT"), primary_key=True
    )


class Agent(TimestampMixin, Base):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "agent_key"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("app.workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    agent_key: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(128))


class AgentVersion(TimestampMixin, Base):
    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint("agent_id", "version_key"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("app.agents.id", ondelete="RESTRICT"), nullable=False
    )
    version_key: Mapped[str] = mapped_column(String(128), nullable=False)
    source_commit: Mapped[str | None] = mapped_column(String(128))
    config_identity: Mapped[str | None] = mapped_column(String(128))


class Artifact(TimestampMixin, Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        UniqueConstraint("workspace_id", "artifact_kind", "content_sha256"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("app.workspaces.id", ondelete="RESTRICT")
    )
    artifact_kind: Mapped[str] = mapped_column(String(64), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_count: Mapped[int] = mapped_column(BigInteger, nullable=False)
    media_type: Mapped[str] = mapped_column(String(128), nullable=False)
    storage_backend: Mapped[str] = mapped_column(String(16), nullable=False)
    storage_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    kms_key_id: Mapped[str] = mapped_column(Text, nullable=False)
    checksum_sha256_b64: Mapped[str] = mapped_column(String(64), nullable=False)
    availability: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Import(TimestampMixin, Base):
    __tablename__ = "imports"
    __table_args__ = (
        UniqueConstraint("identity_hash"),
        UniqueConstraint("workspace_id", "idempotency_key"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("app.workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    agent_version_id: Mapped[str] = mapped_column(
        ForeignKey("app.agent_versions.id", ondelete="RESTRICT"), nullable=False
    )
    source_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("app.artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_class: Mapped[str] = mapped_column(String(64), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(128), nullable=False)
    physical_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    usable_conversation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    source_status_counts: Mapped[dict[str, int]] = mapped_column(JSONB, nullable=False)
    rejected_record_count: Mapped[int] = mapped_column(Integer, nullable=False)
    rejection_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    identity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    idempotency_request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Run(TimestampMixin, Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("workflow_id"),
        UniqueConstraint("request_identity", "attempt_number"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("app.imports.id", ondelete="RESTRICT"), nullable=False
    )
    agent_version_id: Mapped[str] = mapped_column(
        ForeignKey("app.agent_versions.id", ondelete="RESTRICT"), nullable=False
    )
    workflow_id: Mapped[str] = mapped_column(String(255), nullable=False)
    request_identity: Mapped[str] = mapped_column(String(64), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    labs_version: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class AnalysisFact(TimestampMixin, Base):
    __tablename__ = "analysis_facts"
    __table_args__ = (
        UniqueConstraint("run_id", "fact_id"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("app.runs.id", ondelete="RESTRICT"), nullable=False
    )
    fact_id: Mapped[str] = mapped_column(String(64), nullable=False)
    fact_kind: Mapped[str] = mapped_column(String(128), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    value_json: Mapped[Any] = mapped_column(JSONB, nullable=False)
    authority: Mapped[str] = mapped_column(String(32), nullable=False)
    lineage_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


class RunArtifact(TimestampMixin, Base):
    __tablename__ = "run_artifacts"
    __table_args__ = (
        UniqueConstraint("run_id", "artifact_id", "artifact_role"),
        {"schema": "app"},
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("app.runs.id", ondelete="RESTRICT"), primary_key=True
    )
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("app.artifacts.id", ondelete="RESTRICT"), primary_key=True
    )
    artifact_role: Mapped[str] = mapped_column(String(64), primary_key=True)


class Report(TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("run_id", "projection_schema_version"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("app.runs.id", ondelete="RESTRICT"), nullable=False
    )
    artifact_id: Mapped[str] = mapped_column(
        ForeignKey("app.artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    projection_schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    report_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ProviderCache(TimestampMixin, Base):
    __tablename__ = "provider_cache"
    __table_args__ = (
        UniqueConstraint("request_identity"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    request_identity: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    endpoint_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response_artifact_id: Mapped[str] = mapped_column(
        ForeignKey("app.artifacts.id", ondelete="RESTRICT"), nullable=False
    )
    parser_version: Mapped[str] = mapped_column(String(128), nullable=False)
    validation_state: Mapped[str] = mapped_column(String(32), nullable=False)
    usage_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ImportedConversation(TimestampMixin, Base):
    __tablename__ = "imported_conversations"
    __table_args__ = (
        UniqueConstraint("import_id", "line_number"),
        UniqueConstraint("import_id", "trace_id"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("app.imports.id", ondelete="RESTRICT"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trace_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_trace_id: Mapped[str] = mapped_column(String(512), nullable=False)
    events_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)


class ImportRejection(TimestampMixin, Base):
    __tablename__ = "import_rejections"
    __table_args__ = (
        UniqueConstraint("import_id", "line_number"),
        {"schema": "app"},
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    import_id: Mapped[str] = mapped_column(
        ForeignKey("app.imports.id", ondelete="RESTRICT"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    json_pointer: Mapped[str] = mapped_column(String(1024), nullable=False)
    safe_message: Mapped[str] = mapped_column(String(255), nullable=False)
