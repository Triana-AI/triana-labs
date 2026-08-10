"""Add owner isolation and accepted trace projections.

Revision ID: 0002_self_serve_trace_viewer
Revises: 0001_labs08_storage
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_self_serve_trace_viewer"
down_revision: str | None = "0001_labs08_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("subject_hash", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )
    op.create_table(
        "workspace_memberships",
        sa.Column(
            "user_id",
            sa.String(40),
            sa.ForeignKey("app.users.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "workspace_id",
            sa.String(40),
            sa.ForeignKey("app.workspaces.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        schema="app",
    )
    op.add_column("agents", sa.Column("display_name", sa.String(128)), schema="app")
    op.add_column("artifacts", sa.Column("workspace_id", sa.String(40)), schema="app")
    op.create_foreign_key(
        "artifacts_workspace_id_fkey",
        "artifacts",
        "workspaces",
        ["workspace_id"],
        ["id"],
        source_schema="app",
        referent_schema="app",
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "artifacts_artifact_kind_content_sha256_key",
        "artifacts",
        schema="app",
        type_="unique",
    )
    op.create_unique_constraint(
        "artifacts_workspace_kind_sha256_key",
        "artifacts",
        ["workspace_id", "artifact_kind", "content_sha256"],
        schema="app",
    )
    op.create_table(
        "imported_conversations",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "import_id",
            sa.String(40),
            sa.ForeignKey("app.imports.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(128), nullable=False),
        sa.Column("source_trace_id", sa.String(512), nullable=False),
        sa.Column("events_json", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("import_id", "line_number"),
        sa.UniqueConstraint("import_id", "trace_id"),
        schema="app",
    )
    op.create_table(
        "import_rejections",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "import_id",
            sa.String(40),
            sa.ForeignKey("app.imports.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("json_pointer", sa.String(1024), nullable=False),
        sa.Column("safe_message", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("import_id", "line_number"),
        schema="app",
    )


def downgrade() -> None:
    op.drop_table("import_rejections", schema="app")
    op.drop_table("imported_conversations", schema="app")
    op.drop_constraint(
        "artifacts_workspace_kind_sha256_key",
        "artifacts",
        schema="app",
        type_="unique",
    )
    op.create_unique_constraint(
        "artifacts_artifact_kind_content_sha256_key",
        "artifacts",
        ["artifact_kind", "content_sha256"],
        schema="app",
    )
    op.drop_constraint(
        "artifacts_workspace_id_fkey",
        "artifacts",
        schema="app",
        type_="foreignkey",
    )
    op.drop_column("artifacts", "workspace_id", schema="app")
    op.drop_column("agents", "display_name", schema="app")
    op.drop_table("workspace_memberships", schema="app")
    op.drop_table("users", schema="app")
