from alembic import op
import sqlalchemy as sa

revision = "0001_create_vaults_table"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vaults",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("owner_id", sa.String(), nullable=False),
        sa.Column("hardware_uuid", sa.String(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
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
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("hardware_uuid", name="uq_vaults_hardware_uuid"),
    )
    op.create_index("ix_vaults_hardware_uuid", "vaults", ["hardware_uuid"])


def downgrade() -> None:
    op.drop_index("ix_vaults_hardware_uuid", table_name="vaults")
    op.drop_table("vaults")
