"""Rename.nickname to vault_name

Revision ID: 0dbbbaef458c
Revises: a7a0a8f35224
Create Date: 2026-01-23 18:57:30.272705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0dbbbaef458c'
down_revision = 'a7a0a8f35224'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "vaults",
        "nickname",
        new_column_name="vault_name",
        existing_type=sa.String(),
        existing_nullable=True,
    )

def downgrade() -> None:
    op.alter_column(
        "vaults",
        "vault_name",
        new_column_name="nickname",
        existing_type=sa.String(),
        existing_nullable=True,
    )