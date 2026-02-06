"""create vault_authorizations table

Revision ID: 6543d5a990bc
Revises: c3f92920f181
Create Date: 2026-02-06 17:09:52.656391

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6543d5a990bc'
down_revision = 'c3f92920f181'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'vault_authorizations',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('vault_id', sa.String, nullable=False),
        sa.Column('user_id', sa.String, nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('granted_by', sa.String, nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['vault_id'], ['vaults.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('vault_id', 'user_id', name='uq_vault_user'),
    )

    op.create_index('idx_vault_auth_vault', 'vault_authorizations', ['vault_id'])
    op.create_index('idx_vault_auth_user', 'vault_authorizations', ['user_id'])


def downgrade():
    op.drop_index('idx_vault_auth_user', table_name='vault_authorizations')
    op.drop_index('idx_vault_auth_vault', table_name='vault_authorizations')
    op.drop_table('vault_authorizations')
