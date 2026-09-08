"""Add levelup_enabled to guild_config table

Revision ID: 003_levelup_enabled
Revises: 002_guild_config_and_cases
Create Date: 2026-09-08 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '003_levelup_enabled'
down_revision: Union[str, None] = '002_guild_config_and_cases'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('guild_config', sa.Column('levelup_enabled', sa.Boolean(), server_default='false', nullable=False))

def downgrade() -> None:
    op.drop_column('guild_config', 'levelup_enabled')
