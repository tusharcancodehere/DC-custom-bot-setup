"""Create guild_config and moderation_cases tables

Revision ID: 002_create_guild_config_and_cases
Revises: 001_create_user_xp_table
Create Date: 2026-09-08 19:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002_guild_config_and_cases'
down_revision: Union[str, None] = '001_create_user_xp_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'guild_config',
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('welcome_channel_id', sa.BigInteger(), nullable=True),
        sa.Column('modlog_channel_id', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('guild_id'),
    )
    op.create_table(
        'moderation_cases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('moderator_id', sa.BigInteger(), nullable=False),
        sa.Column('moderator_name', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_moderation_cases_guild_user', 'moderation_cases', ['guild_id', 'user_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_moderation_cases_guild_user', table_name='moderation_cases')
    op.drop_table('moderation_cases')
    op.drop_table('guild_config')
