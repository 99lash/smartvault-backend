"""add provisioning_token to users

Revision ID: 9f3a1c8d2b7e
Revises: 0dbbbaef458c
Create Date: 2026-03-02 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f3a1c8d2b7e'
down_revision = '0dbbbaef458c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column('provisioning_token', sa.String(8), nullable=True, unique=True),
    )


def downgrade():
    op.drop_column('users', 'provisioning_token')
