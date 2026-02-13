"""create_access_logs_table

Revision ID: 4ec6d82838d5
Revises: 7e1237f49be4
Create Date: 2026-02-13 14:48:58.263912

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4ec6d82838d5'
down_revision = '7e1237f49be4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'access_logs',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column(
            'vault_id', sa.String, nullable=False,
        ),
        sa.Column(
            'user_id', sa.String, nullable=True,
        ),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('method', sa.String(20), nullable=False),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['vault_id'], ['vaults.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    )

    op.create_index(
        'ix_access_logs_vault_created',
        'access_logs',
        ['vault_id', 'created_at'],
    )
    op.create_index(
        'ix_access_logs_user_created',
        'access_logs',
        ['user_id', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_access_logs_user_created', table_name='access_logs')
    op.drop_index('ix_access_logs_vault_created', table_name='access_logs')
    op.drop_table('access_logs')