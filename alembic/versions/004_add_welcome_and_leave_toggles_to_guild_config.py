"""Add welcome_enabled and leave_enabled to guild_config table

Revision ID: 004_welcome_leave_toggles
Revises: 003_levelup_enabled
Create Date: 2026-09-08 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004_welcome_leave_toggles'
down_revision: Union[str, None] = '003_levelup_enabled'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('guild_config', sa.Column('welcome_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('guild_config', sa.Column('leave_enabled', sa.Boolean(), server_default='true', nullable=False))

def downgrade() -> None:
    op.drop_column('guild_config', 'leave_enabled')
    op.drop_column('guild_config', 'welcome_enabled')
