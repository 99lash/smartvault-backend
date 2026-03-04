"""drop provisioning_token column from users

Revision ID: d4e5f6a7b8c9
Revises: 9f3a1c8d2b7e
Create Date: 2026-03-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = '9f3a1c8d2b7e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('users', 'provisioning_token')


def downgrade():
    op.add_column(
        'users',
        sa.Column('provisioning_token', sa.String(8), nullable=True, unique=True),
    )
