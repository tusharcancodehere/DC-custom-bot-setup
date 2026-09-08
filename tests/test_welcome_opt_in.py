import unittest
from unittest.mock import AsyncMock, MagicMock
import discord
from src.features.welcome.commands import Welcome

class TestWelcomeOptIn(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MagicMock()
        self.welcome_cog = Welcome(self.bot)

        # Mock guild 1 (unconfigured)
        self.guild_unconfigured = MagicMock(spec=discord.Guild)
        self.guild_unconfigured.id = 111222333
        self.guild_unconfigured.name = "Unconfigured Guild"
        self.guild_unconfigured.system_channel = MagicMock(spec=discord.TextChannel, name="general")
        self.guild_unconfigured.system_channel.send = AsyncMock()
        self.guild_unconfigured.text_channels = [self.guild_unconfigured.system_channel]
        self.guild_unconfigured.icon = None

        # Mock guild 2 (configured)
        self.guild_configured = MagicMock(spec=discord.Guild)
        self.guild_configured.id = 444555666
        self.guild_configured.name = "Configured Guild"
        self.configured_channel = MagicMock(spec=discord.TextChannel)
        self.configured_channel.id = 999888777
        self.configured_channel.mention = "<#999888777>"
        self.configured_channel.send = AsyncMock()
        self.configured_channel.permissions_for = MagicMock(return_value=MagicMock(send_messages=True))
        self.guild_configured.get_channel = MagicMock(return_value=self.configured_channel)
        self.guild_configured.text_channels = [self.configured_channel]
        self.guild_configured.icon = None

        # Configure guild 2 in cog
        self.welcome_cog.welcome_channels[self.guild_configured.id] = self.configured_channel.id

    async def test_welcome_disabled_by_default(self):
        """Verify that get_welcome_channel returns None by default without fallbacks."""
        channel = self.welcome_cog.get_welcome_channel(self.guild_unconfigured)
        self.assertIsNone(channel, "Unconfigured guild should return None and not fall back to system_channel")

    async def test_join_does_nothing_when_unconfigured(self):
        """Verify on_member_join sends nothing when welcome channel is unconfigured."""
        member = MagicMock(spec=discord.Member)
        member.bot = False
        member.guild = self.guild_unconfigured
        await self.welcome_cog.on_member_join(member)
        self.guild_unconfigured.system_channel.send.assert_not_called()

    async def test_leave_does_nothing_when_unconfigured(self):
        """Verify on_member_remove sends nothing when welcome channel is unconfigured."""
        member = MagicMock(spec=discord.Member)
        member.bot = False
        member.guild = self.guild_unconfigured
        await self.welcome_cog.on_member_remove(member)
        self.guild_unconfigured.system_channel.send.assert_not_called()

    async def test_join_and_leave_work_when_configured(self):
        """Verify on_member_join and on_member_remove send messages when configured."""
        member = MagicMock(spec=discord.Member)
        member.bot = False
        member.name = "ActiveMember"
        member.mention = "<@123>"
        member.guild = self.guild_configured

        await self.welcome_cog.on_member_join(member)
        self.configured_channel.send.assert_called_once()
        self.assertIn("Welcome to **Configured Guild**", self.configured_channel.send.call_args[1]["content"])

        self.configured_channel.send.reset_mock()
        await self.welcome_cog.on_member_remove(member)
        self.configured_channel.send.assert_called_once_with("👋 **ActiveMember** has left the server.")

    async def test_deleted_or_missing_channel_handled_safely(self):
        """Verify that missing/deleted channels return None safely and do not raise exceptions."""
        guild_deleted_channel = MagicMock(spec=discord.Guild)
        guild_deleted_channel.id = 777888999
        guild_deleted_channel.get_channel = MagicMock(return_value=None)
        self.welcome_cog.welcome_channels[guild_deleted_channel.id] = 12345

        channel = self.welcome_cog.get_welcome_channel(guild_deleted_channel)
        self.assertIsNone(channel)

        member = MagicMock(spec=discord.Member)
        member.bot = False
        member.guild = guild_deleted_channel
        # Should not raise any exceptions
        await self.welcome_cog.on_member_join(member)
        await self.welcome_cog.on_member_remove(member)

    async def test_preview_command_works_unconfigured(self):
        """Verify /welcome manual preview command functions even when unconfigured."""
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.guild_unconfigured
        interaction.user = MagicMock(mention="<@User>", name="User")
        interaction.response.send_message = AsyncMock()

        await self.welcome_cog.welcome_command.callback(self.welcome_cog, interaction)
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        self.assertIsNotNone(embed)

    async def test_per_guild_isolation(self):
        """Verify welcome configuration for one guild does not affect another."""
        self.assertIn(self.guild_configured.id, self.welcome_cog.welcome_channels)
        self.assertNotIn(self.guild_unconfigured.id, self.welcome_cog.welcome_channels)
        self.assertIsNotNone(self.welcome_cog.get_welcome_channel(self.guild_configured))
        self.assertIsNone(self.welcome_cog.get_welcome_channel(self.guild_unconfigured))

if __name__ == "__main__":
    unittest.main()
