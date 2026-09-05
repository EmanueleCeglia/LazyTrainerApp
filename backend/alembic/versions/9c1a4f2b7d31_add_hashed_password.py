"""Add hashed_password (was declared on the model but never migrated)

Revision ID: 9c1a4f2b7d31
Revises: 1de4d0a8e01b
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1a4f2b7d31'
down_revision: Union[str, Sequence[str], None] = '1de4d0a8e01b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    """Databases created via reset_db.py already have this column."""
    bind = op.get_bind()
    cols = [c["name"] for c in sa.inspect(bind).get_columns(table)]
    return column in cols


def _has_index(table: str, index: str) -> bool:
    bind = op.get_bind()
    idx = [i["name"] for i in sa.inspect(bind).get_indexes(table)]
    return index in idx


def upgrade() -> None:
    """Upgrade schema."""
    if not _has_column("users", "hashed_password"):
        op.add_column('users', sa.Column('hashed_password', sa.String(), nullable=True))

    # Login now strips whitespace before looking a user up, so a username stored
    # with a stray leading/trailing space could never be matched again. Trim them,
    # but only where the trimmed name is not already taken by someone else.
    op.execute(
        """
        UPDATE users u
           SET username = btrim(u.username)
         WHERE u.username <> btrim(u.username)
           AND NOT EXISTS (
               SELECT 1 FROM users other
                WHERE other.id <> u.id
                  AND other.username = btrim(u.username)
           )
        """
    )

    # Every login does a lookup by username, so index it.
    if not _has_index("users", "ix_users_username"):
        op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)


def downgrade() -> None:
    """Downgrade schema.

    Deliberately NOT symmetric: dropping `hashed_password` would destroy every
    stored credential, and a downgrade is usually run to undo a bad deploy rather
    than to discard user accounts. We only drop the index; the column stays.

    If you genuinely want the column gone, drop it by hand after taking a dump:
        docker exec lazytrainer_db pg_dump -U postgres -d postgres -t users --data-only > users.sql
        ALTER TABLE users DROP COLUMN hashed_password;

    The username trim is not reversed either - the original spacing is not recorded.
    """
    if _has_index("users", "ix_users_username"):
        op.drop_index(op.f('ix_users_username'), table_name='users')
