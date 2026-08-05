"""Create the LABS-08 application storage schema.

Revision ID: 0001_labs08_storage
Revises: none
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_labs08_storage"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(sa.text("CREATE SCHEMA IF NOT EXISTS app"))
    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("artifact_kind", sa.String(64), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("byte_count", sa.BigInteger(), nullable=False),
        sa.Column("media_type", sa.String(128), nullable=False),
        sa.Column("storage_backend", sa.String(16), nullable=False),
        sa.Column("storage_bucket", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("kms_key_id", sa.Text(), nullable=False),
        sa.Column("checksum_sha256_b64", sa.String(64), nullable=False),
        sa.Column("availability", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("artifact_kind", "content_sha256"),
        schema="app",
    )
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("slug", sa.String(128), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(40),
            sa.ForeignKey("app.workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("agent_key", sa.String(128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "agent_key"),
        schema="app",
    )
    op.create_table(
        "agent_versions",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "agent_id",
            sa.String(40),
            sa.ForeignKey("app.agents.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("version_key", sa.String(128), nullable=False),
        sa.Column("source_commit", sa.String(128)),
        sa.Column("config_identity", sa.String(128)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("agent_id", "version_key"),
        schema="app",
    )
    op.create_table(
        "imports",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(40),
            sa.ForeignKey("app.workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_version_id",
            sa.String(40),
            sa.ForeignKey("app.agent_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_artifact_id",
            sa.String(40),
            sa.ForeignKey("app.artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("evidence_class", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(128), nullable=False),
        sa.Column("physical_record_count", sa.Integer(), nullable=False),
        sa.Column("usable_conversation_count", sa.Integer(), nullable=False),
        sa.Column("source_status_counts", postgresql.JSONB(), nullable=False),
        sa.Column("rejected_record_count", sa.Integer(), nullable=False),
        sa.Column("rejection_summary", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("identity_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("idempotency_request_hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "idempotency_key"),
        schema="app",
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "import_id",
            sa.String(40),
            sa.ForeignKey("app.imports.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "agent_version_id",
            sa.String(40),
            sa.ForeignKey("app.agent_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("workflow_id", sa.String(255), nullable=False, unique=True),
        sa.Column("request_identity", sa.String(64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("labs_version", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("request_identity", "attempt_number"),
        schema="app",
    )
    op.create_table(
        "analysis_facts",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(40),
            sa.ForeignKey("app.runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("fact_id", sa.String(64), nullable=False),
        sa.Column("fact_kind", sa.String(128), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("value_json", postgresql.JSONB(), nullable=False),
        sa.Column("authority", sa.String(32), nullable=False),
        sa.Column("lineage_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("run_id", "fact_id"),
        schema="app",
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(40),
            sa.ForeignKey("app.runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "artifact_id",
            sa.String(40),
            sa.ForeignKey("app.artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("projection_schema_version", sa.Integer(), nullable=False),
        sa.Column("report_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("run_id", "projection_schema_version"),
        schema="app",
    )
    op.create_table(
        "run_artifacts",
        sa.Column(
            "run_id",
            sa.String(40),
            sa.ForeignKey("app.runs.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "artifact_id",
            sa.String(40),
            sa.ForeignKey("app.artifacts.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("artifact_role", sa.String(64), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )
    op.create_table(
        "provider_cache",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("request_identity", sa.String(64), nullable=False, unique=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("endpoint_fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "response_artifact_id",
            sa.String(40),
            sa.ForeignKey("app.artifacts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("parser_version", sa.String(128), nullable=False),
        sa.Column("validation_state", sa.String(32), nullable=False),
        sa.Column("usage_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )


def downgrade() -> None:
    for table in (
        "provider_cache",
        "run_artifacts",
        "reports",
        "analysis_facts",
        "runs",
        "imports",
        "agent_versions",
        "agents",
        "workspaces",
        "artifacts",
    ):
        op.drop_table(table, schema="app")
    op.execute(sa.text("DROP SCHEMA app"))
