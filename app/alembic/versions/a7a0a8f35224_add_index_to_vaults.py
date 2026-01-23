"""Add index to vaults

Revision ID: a7a0a8f35224
Revises: 0001_create_vaults_table
Create Date: 2026-01-23 13:34:41.660146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a7a0a8f35224'
down_revision = '0001_create_vaults_table'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_index(
        "ix_vaults_owner_id",
        "vaults",
        ["owner_id"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_vaults_owner_id", table_name="vaults")

