import unittest
from unittest.mock import AsyncMock, MagicMock
import discord
from src.features.levels.commands import Levels

class TestLevelupOptIn(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.levels_cog = Levels(self.bot)

        # Guild 1 (default / unconfigured)
        self.guild_1 = MagicMock(spec=discord.Guild)
        self.guild_1.id = 111
        self.guild_1.name = "Guild One"

        # Guild 2
        self.guild_2 = MagicMock(spec=discord.Guild)
        self.guild_2.id = 222
        self.guild_2.name = "Guild Two"

        # Admin user
        self.admin = MagicMock(spec=discord.Member)
        self.admin.id = 999
        admin_perms = MagicMock()
        admin_perms.manage_guild = True
        self.admin.guild_permissions = admin_perms

        # Regular user
        self.regular_user = MagicMock(spec=discord.Member)
        self.regular_user.id = 888
        user_perms = MagicMock()
        user_perms.manage_guild = False
        self.regular_user.guild_permissions = user_perms
        self.regular_user.bot = False
        self.regular_user.display_avatar = MagicMock(url="https://example.com/avatar.png")
        self.regular_user.mention = "<@888>"

    def _create_interaction(self, guild, user):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = guild
        interaction.guild_id = guild.id
        interaction.user = user
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = MagicMock(return_value=False)
        return interaction

    async def test_levelup_announcements_disabled_by_default(self):
        """Verify level-up announcements are disabled by default for all guilds."""
        self.assertFalse(self.levels_cog.is_levelup_enabled(self.guild_1.id))
        self.assertFalse(self.levels_cog.is_levelup_enabled(self.guild_2.id))

    async def test_silent_levelup_when_disabled(self):
        """Verify users earn XP and level up silently without sending announcement when disabled."""
        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()

        # Initialize user at 90 XP (Level 0)
        user_data = self.levels_cog.get_user_data(self.guild_1.id, self.regular_user.id)
        user_data["xp"] = 90
        user_data["level"] = 0

        # Create chat message that grants XP and pushes past level 1 threshold (100 XP)
        msg = MagicMock(spec=discord.Message)
        msg.author = self.regular_user
        msg.guild = self.guild_1
        msg.channel = channel
        msg.content = "Chatting to level up!"

        await self.levels_cog.on_message(msg)

        # Level increased
        self.assertGreater(user_data["xp"], 100)
        self.assertGreaterEqual(user_data["level"], 1)

        # Announcement NOT sent
        channel.send.assert_not_called()

    async def test_admin_enables_and_announcement_sent(self):
        """Verify admin can enable level-up announcements, and celebration is sent on level up."""
        interaction = self._create_interaction(self.guild_1, self.admin)
        await self.levels_cog.levelup_enable.callback(self.levels_cog, interaction)

        self.assertTrue(self.levels_cog.is_levelup_enabled(self.guild_1.id))
        interaction.response.send_message.assert_called_once()
        self.assertIn("enabled", interaction.response.send_message.call_args[0][0])

        # Test level up now sends announcement
        channel = MagicMock(spec=discord.TextChannel)
        channel.send = AsyncMock()

        # User at 90 XP in level 0
        user_data = self.levels_cog.get_user_data(self.guild_1.id, self.regular_user.id)
        user_data["xp"] = 90
        user_data["level"] = 0

        msg = MagicMock(spec=discord.Message)
        msg.author = self.regular_user
        msg.guild = self.guild_1
        msg.channel = channel
        msg.content = "Chatting to level up with announcement!"

        await self.levels_cog.on_message(msg)

        self.assertGreaterEqual(user_data["level"], 1)
        channel.send.assert_called_once()
        embed = channel.send.call_args[1].get("embed")
        self.assertIsNotNone(embed)
        self.assertIn("Level Up!", embed.title)

    async def test_admin_disables_levelup_announcements(self):
        """Verify admin can disable level-up announcements."""
        self.levels_cog.levelup_enabled[self.guild_1.id] = True
        interaction = self._create_interaction(self.guild_1, self.admin)

        await self.levels_cog.levelup_disable.callback(self.levels_cog, interaction)

        self.assertFalse(self.levels_cog.is_levelup_enabled(self.guild_1.id))
        interaction.response.send_message.assert_called_once()
        self.assertIn("disabled", interaction.response.send_message.call_args[0][0])

    async def test_non_admin_cannot_change_setting(self):
        """Verify users without manage_guild permission cannot toggle level-up setting."""
        interaction = self._create_interaction(self.guild_1, self.regular_user)
        await self.levels_cog.levelup_enable.callback(self.levels_cog, interaction)

        self.assertFalse(self.levels_cog.is_levelup_enabled(self.guild_1.id))
        interaction.response.send_message.assert_called_once()
        self.assertIn("You do not have permission", interaction.response.send_message.call_args[0][0])

    async def test_per_guild_isolation(self):
        """Verify setting in Guild 1 does not affect Guild 2."""
        interaction = self._create_interaction(self.guild_1, self.admin)
        await self.levels_cog.levelup_enable.callback(self.levels_cog, interaction)

        self.assertTrue(self.levels_cog.is_levelup_enabled(self.guild_1.id))
        self.assertFalse(self.levels_cog.is_levelup_enabled(self.guild_2.id))

    async def test_levelup_status_command(self):
        """Verify /levelup status reports the correct state."""
        interaction = self._create_interaction(self.guild_1, self.admin)
        await self.levels_cog.levelup_status.callback(self.levels_cog, interaction)
        interaction.response.send_message.assert_called_once()
        self.assertIn("disabled", interaction.response.send_message.call_args[0][0])

        self.levels_cog.levelup_enabled[self.guild_1.id] = True
        interaction.response.send_message.reset_mock()
        await self.levels_cog.levelup_status.callback(self.levels_cog, interaction)
        interaction.response.send_message.assert_called_once()
        self.assertIn("enabled", interaction.response.send_message.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
