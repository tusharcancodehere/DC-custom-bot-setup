"""Create user_xp table

Revision ID: 001_create_user_xp_table
Revises: 
Create Date: 2026-09-06 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001_create_user_xp_table'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'user_xp',
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('xp', sa.Integer(), server_default='0', nullable=False),
        sa.Column('level', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_xp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('guild_id', 'user_id'),
    )
    op.create_index('ix_user_xp_guild_xp', 'user_xp', ['guild_id', 'xp'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_user_xp_guild_xp', table_name='user_xp')
    op.drop_table('user_xp')
