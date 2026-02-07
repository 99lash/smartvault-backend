"""add pin to vaults

Revision ID: 7e1237f49be4
Revises: 6543d5a990bc
Create Date: 2026-02-07 09:18:20.693918

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e1237f49be4'
down_revision = '6543d5a990bc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('vaults', sa.Column('pin_hash', sa.String(length=255), nullable=True))
    op.add_column('vaults', sa.Column('pin_set_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column('vaults', 'pin_set_at')
    op.drop_column('vaults', 'pin_hash')
