"""create_admin_audit_logs_table

Revision ID: a1b2c3d4e5f6
Revises: 4ec6d82838d5
Create Date: 2026-02-14 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "4ec6d82838d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_created", "admin_audit_logs", ["created_at"])
    op.create_index("idx_audit_action",  "admin_audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("idx_audit_action",  table_name="admin_audit_logs")
    op.drop_index("idx_audit_created", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")
