"""Add owner role and workspace feature request state.

Revision ID: 0003_feature_entitlements
Revises: 0002_self_serve_trace_viewer
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_feature_entitlements"
down_revision: str | None = "0002_self_serve_trace_viewer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workspace_memberships",
        sa.Column(
            "role",
            sa.String(32),
            nullable=False,
            server_default="OWNER",
        ),
        schema="app",
    )
    op.create_check_constraint(
        "workspace_memberships_role_check",
        "workspace_memberships",
        "role = 'OWNER'",
        schema="app",
    )
    op.create_table(
        "workspace_feature_entitlements",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(40),
            sa.ForeignKey("app.workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("feature_key", sa.String(64), nullable=False),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "feature_key"),
        sa.CheckConstraint(
            "state = 'AVAILABLE'", name="workspace_feature_entitlements_state_check"
        ),
        sa.CheckConstraint(
            "feature_key IN ('TRACE_INGESTION', 'CONVERSATION_VIEWER', "
            "'ANALYSIS', 'SIMULATION', 'TEAM_COLLABORATION', 'API_ACCESS')",
            name="workspace_feature_entitlements_key_check",
        ),
        schema="app",
    )
    op.create_table(
        "feature_access_requests",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(40),
            sa.ForeignKey("app.workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("feature_key", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("workspace_id", "feature_key"),
        sa.CheckConstraint(
            "feature_key IN ('ANALYSIS', 'SIMULATION', "
            "'TEAM_COLLABORATION', 'API_ACCESS')",
            name="feature_access_requests_key_check",
        ),
        schema="app",
    )


def downgrade() -> None:
    op.drop_table("feature_access_requests", schema="app")
    op.drop_table("workspace_feature_entitlements", schema="app")
    op.drop_constraint(
        "workspace_memberships_role_check",
        "workspace_memberships",
        schema="app",
        type_="check",
    )
    op.drop_column("workspace_memberships", "role", schema="app")
