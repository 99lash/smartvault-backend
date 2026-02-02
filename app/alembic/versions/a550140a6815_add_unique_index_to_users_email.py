"""add unique index to users email

Revision ID: a550140a6815
Revises: c3f92920f181
Create Date: 2026-02-02 21:46:52.459301

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a550140a6815'
down_revision = 'c3f92920f181'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )


def downgrade():
    op.drop_index("ix_users_email", table_name="users")