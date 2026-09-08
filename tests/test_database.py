import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure src is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from sqlalchemy import delete, select

import database.database as db
from database.models import GuildConfig, ModerationCase, UserXP
from features.admin.commands import Admin
from features.levels.commands import Levels
from features.moderation.commands import Moderation
from features.welcome.commands import Welcome

TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dc_bot_test"

class TestDatabasePersistence(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Configure database for testing
        db.set_database_url(TEST_DB_URL, use_null_pool=True)

    @classmethod
    def tearDownClass(cls):
        db.set_database_url(None)

    async def asyncSetUp(self):
        # Ensure tables exist
        if db.engine:
            try:
                async with db.engine.begin() as conn:
                    await conn.run_sync(db.Base.metadata.create_all)
            except Exception:
                pass

    async def asyncTearDown(self):
        # Clean test tables
        if db.async_session:
            try:
                async with db.async_session() as session:
                    await session.execute(delete(ModerationCase))
                    await session.execute(delete(GuildConfig))
                    await session.execute(delete(UserXP))
                    await session.commit()
            except Exception:
                pass

    def test_database_helpers(self):
        """Test is_db_connected and set_database_url helpers."""
        self.assertTrue(db.is_db_connected())
        db.set_database_url(None)
        self.assertFalse(db.is_db_connected())
        db.set_database_url(TEST_DB_URL, use_null_pool=True)
        self.assertTrue(db.is_db_connected())

    async def test_guild_config_persistence(self):
        """Test persisting and querying GuildConfig records."""
        async with db.async_session() as session:
            config = GuildConfig(guild_id=123456789, welcome_channel_id=987654321, modlog_channel_id=555666777)
            session.add(config)
            await session.commit()

        async with db.async_session() as session:
            stmt = select(GuildConfig).where(GuildConfig.guild_id == 123456789)
            result = await session.execute(stmt)
            fetched = result.scalar_one_or_none()
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.welcome_channel_id, 987654321)
            self.assertEqual(fetched.modlog_channel_id, 555666777)
            self.assertFalse(fetched.levelup_enabled)

    async def test_admin_cog_persistence(self):
        """Test that Admin cog updates GuildConfig and loads persisted settings."""
        mock_bot = MagicMock()
        admin_cog = Admin(mock_bot)

        mock_guild = MagicMock()
        mock_guild.id = 111222333
        mock_channel = MagicMock()
        mock_channel.id = 444555666
        mock_channel.mention = "#mod-logs"

        mock_interaction = MagicMock()
        mock_interaction.guild = mock_guild
        mock_interaction.response = AsyncMock()

        # Execute set_modlog_channel
        await admin_cog.set_modlog_channel.callback(admin_cog, mock_interaction, channel=mock_channel)
        mock_interaction.response.send_message.assert_called_once()
        self.assertIn("#mod-logs", mock_interaction.response.send_message.call_args[0][0])
        self.assertEqual(admin_cog.modlog_channels[111222333], 444555666)

        # Verify persisted in database
        async with db.async_session() as session:
            stmt = select(GuildConfig).where(GuildConfig.guild_id == 111222333)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            self.assertIsNotNone(config)
            self.assertEqual(config.modlog_channel_id, 444555666)

        # Create a fresh Admin cog and verify load_configs restores it
        fresh_admin = Admin(mock_bot)
        self.assertEqual(fresh_admin.modlog_channels, {})
        await fresh_admin.load_configs()
        self.assertEqual(fresh_admin.modlog_channels.get(111222333), 444555666)

    async def test_welcome_cog_persistence(self):
        """Test that Welcome cog updates GuildConfig and loads persisted settings."""
        mock_bot = MagicMock()
        welcome_cog = Welcome(mock_bot)

        mock_guild = MagicMock()
        mock_guild.id = 222333444
        mock_channel = MagicMock()
        mock_channel.id = 777888999
        mock_channel.mention = "#welcome"

        mock_interaction = MagicMock()
        mock_interaction.guild = mock_guild
        mock_interaction.response = AsyncMock()

        # Execute set_welcome_channel
        await welcome_cog.set_welcome_channel.callback(welcome_cog, mock_interaction, channel=mock_channel)
        mock_interaction.response.send_message.assert_called_once()
        self.assertIn("#welcome", mock_interaction.response.send_message.call_args[0][0])
        self.assertEqual(welcome_cog.welcome_channels[222333444], 777888999)

        # Verify persisted in database
        async with db.async_session() as session:
            stmt = select(GuildConfig).where(GuildConfig.guild_id == 222333444)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            self.assertIsNotNone(config)
            self.assertEqual(config.welcome_channel_id, 777888999)

        # Create fresh Welcome cog and verify load_configs restores it
        fresh_welcome = Welcome(mock_bot)
        self.assertEqual(fresh_welcome.welcome_channels, {})
        await fresh_welcome.load_configs()
        self.assertEqual(fresh_welcome.welcome_channels.get(222333444), 777888999)

    async def test_moderation_cases_persistence(self):
        """Test that Moderation cog records, lists, and clears warning cases in the database."""
        mock_bot = MagicMock()
        mod_cog = Moderation(mock_bot)

        mock_guild = MagicMock()
        mock_guild.id = 333444555
        mock_guild.name = "Test Server"
        mock_guild.icon = None
        mock_guild.owner = MagicMock()
        mock_guild.me = MagicMock()
        mock_guild.me.top_role = 20

        mock_mod = MagicMock()
        mock_mod.id = 1001
        mock_mod.name = "ModUser"
        mock_mod.mention = "@ModUser"
        mock_mod.top_role = 10

        mock_target = MagicMock()
        mock_target.id = 2002
        mock_target.name = "Spammer"
        mock_target.mention = "@Spammer"
        mock_target.top_role = 5
        mock_target.display_avatar.url = "https://example.com/avatar.png"
        mock_target.send = AsyncMock()

        mock_interaction = MagicMock()
        mock_interaction.guild = mock_guild
        mock_interaction.user = mock_mod
        mock_interaction.response = AsyncMock()

        # Issue first warning
        await mod_cog.warn_command.callback(mod_cog, mock_interaction, user=mock_target, reason="Spamming chat")

        # Verify case in database
        async with db.async_session() as session:
            stmt = select(ModerationCase).where(ModerationCase.guild_id == 333444555, ModerationCase.user_id == 2002)
            result = await session.execute(stmt)
            cases = result.scalars().all()
            self.assertEqual(len(cases), 1)
            self.assertEqual(cases[0].action, "warn")
            self.assertEqual(cases[0].reason, "Spamming chat")
            self.assertEqual(cases[0].moderator_name, "ModUser")

        # Query warnings command with fresh cog (fetching from DB)
        fresh_mod = Moderation(mock_bot)
        mock_interaction.response.reset_mock()
        await fresh_mod.warnings_command.callback(fresh_mod, mock_interaction, user=mock_target)
        mock_interaction.response.send_message.assert_called_once()
        embed = mock_interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("Warning History", embed.title)
        self.assertEqual(len(embed.fields), 1)

        # Clear warnings
        mock_interaction.response.reset_mock()
        await fresh_mod.clear_warnings_command.callback(fresh_mod, mock_interaction, user=mock_target)
        mock_interaction.response.send_message.assert_called_once()
        self.assertIn("Cleared", mock_interaction.response.send_message.call_args[0][0])

        # Verify deleted in database
        async with db.async_session() as session:
            stmt = select(ModerationCase).where(ModerationCase.guild_id == 333444555, ModerationCase.user_id == 2002)
            result = await session.execute(stmt)
            self.assertEqual(len(result.scalars().all()), 0)

    async def test_levels_persistence(self):
        """Test that Levels cog records XP, queries leaderboard, and persists changes to database."""
        mock_bot = MagicMock()
        levels_cog = Levels(mock_bot)

        mock_guild = MagicMock()
        mock_guild.id = 444555666
        mock_guild.name = "Level Server"
        mock_guild.icon = None

        mock_user = MagicMock()
        mock_user.id = 5005
        mock_user.name = "Leveler"
        mock_user.mention = "@Leveler"
        mock_user.display_avatar.url = "https://example.com/avatar.png"

        mock_interaction = MagicMock()
        mock_interaction.guild = mock_guild
        mock_interaction.user = mock_user
        mock_interaction.response = AsyncMock()

        # Add XP via admin command
        await levels_cog.add_xp_command.callback(levels_cog, mock_interaction, user=mock_user, amount=500)
        self.assertEqual(levels_cog.guild_xp[444555666][5005]["xp"], 500)

        # Verify persisted in database
        async with db.async_session() as session:
            stmt = select(UserXP).where(UserXP.guild_id == 444555666, UserXP.user_id == 5005)
            result = await session.execute(stmt)
            xp_record = result.scalar_one_or_none()
            self.assertIsNotNone(xp_record)
            self.assertEqual(xp_record.xp, 500)

        # Query leaderboard with fresh cog
        fresh_levels = Levels(mock_bot)
        mock_interaction.response.reset_mock()
        mock_guild.get_member.return_value = mock_user
        await fresh_levels.leaderboard_command.callback(fresh_levels, mock_interaction)
        mock_interaction.response.send_message.assert_called_once()
        embed = mock_interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("Server Leaderboard", embed.title)
        self.assertIn("500 XP", embed.description)

        # Query rank with fresh cog
        mock_interaction.response.reset_mock()
        await fresh_levels.level_command.callback(fresh_levels, mock_interaction, user=mock_user)
        mock_interaction.response.send_message.assert_called_once()
        embed = mock_interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("500", embed.description)

    async def test_levelup_setting_persistence(self):
        """Test that Levels cog updates GuildConfig and loads persisted levelup_enabled setting."""
        mock_bot = MagicMock()
        levels_cog = Levels(mock_bot)

        mock_guild = MagicMock()
        mock_guild.id = 666777888

        mock_interaction = MagicMock()
        mock_interaction.guild = mock_guild
        mock_interaction.user = MagicMock()
        mock_interaction.user.guild_permissions = MagicMock(manage_guild=True)
        mock_interaction.response = AsyncMock()

        # Enable level-up announcements
        await levels_cog.levelup_enable.callback(levels_cog, mock_interaction)
        self.assertTrue(levels_cog.is_levelup_enabled(666777888))

        # Verify persisted in database
        async with db.async_session() as session:
            stmt = select(GuildConfig).where(GuildConfig.guild_id == 666777888)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            self.assertIsNotNone(config)
            self.assertTrue(config.levelup_enabled)

        # Fresh cog loads from database
        fresh_levels = Levels(mock_bot)
        self.assertFalse(fresh_levels.is_levelup_enabled(666777888))
        await fresh_levels.load_configs()
        self.assertTrue(fresh_levels.is_levelup_enabled(666777888))

        # Disable setting
        await fresh_levels.levelup_disable.callback(fresh_levels, mock_interaction)
        self.assertFalse(fresh_levels.is_levelup_enabled(666777888))

        # Verify persisted in database
        async with db.async_session() as session:
            stmt = select(GuildConfig).where(GuildConfig.guild_id == 666777888)
            result = await session.execute(stmt)
            config = result.scalar_one_or_none()
            self.assertFalse(config.levelup_enabled)

    async def test_graceful_degradation_without_database(self):
        """Test that all cogs operate fully in-memory when async_session is None."""
        mock_bot = MagicMock()

        with patch("database.database.async_session", None):
            # Admin in-memory
            admin = Admin(mock_bot)
            mock_guild = MagicMock(id=999)
            mock_channel = MagicMock(id=888, mention="#mod")
            interaction = MagicMock(guild=mock_guild, response=AsyncMock())
            await admin.set_modlog_channel.callback(admin, interaction, channel=mock_channel)
            self.assertEqual(admin.modlog_channels[999], 888)

            # Welcome in-memory
            welcome = Welcome(mock_bot)
            mock_wel_channel = MagicMock(id=777, mention="#welcome")
            interaction = MagicMock(guild=mock_guild, response=AsyncMock())
            await welcome.set_welcome_channel.callback(welcome, interaction, channel=mock_wel_channel)
            self.assertEqual(welcome.welcome_channels[999], 777)

            # Moderation in-memory
            mod = Moderation(mock_bot)
            mock_mod = MagicMock(id=1, name="Admin", mention="@Admin", top_role=10)
            mock_target = MagicMock(id=2, name="Target", mention="@Target", top_role=5, send=AsyncMock(), display_avatar=MagicMock(url="http://x"))
            mock_guild.owner = MagicMock()
            mock_guild.me = MagicMock()
            mock_guild.me.top_role = 20
            interaction = MagicMock(guild=mock_guild, user=mock_mod, response=AsyncMock())
            await mod.warn_command.callback(mod, interaction, user=mock_target, reason="Test reason")
            self.assertEqual(len(mod.warnings[999][2]), 1)

            # Levels in-memory
            levels = Levels(mock_bot)
            interaction = MagicMock(guild=mock_guild, user=mock_target, response=AsyncMock())
            await levels.add_xp_command.callback(levels, interaction, user=mock_target, amount=250)
            self.assertEqual(levels.guild_xp[999][2]["xp"], 250)

if __name__ == "__main__":
    unittest.main()
