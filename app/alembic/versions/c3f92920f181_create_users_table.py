"""create users table

Revision ID: c3f92920f181
Revises: 0dbbbaef458c
Create Date: 2026-02-02 20:24:38.720913

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f92920f181'
down_revision = '0dbbbaef458c'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index(
        'ix_users_email',
        'users',
        ['email'],
        unique=True,
    )


def downgrade():
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

