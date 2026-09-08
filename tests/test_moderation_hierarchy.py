import unittest
from unittest.mock import AsyncMock, MagicMock
import discord
from src.features.moderation.commands import Moderation

class FakeRole:
    def __init__(self, position: int, name: str = "Role"):
        self.position = position
        self.name = name

    def __ge__(self, other):
        return self.position >= getattr(other, "position", 0)

    def __gt__(self, other):
        return self.position > getattr(other, "position", 0)

    def __le__(self, other):
        return self.position <= getattr(other, "position", 0)

    def __lt__(self, other):
        return self.position < getattr(other, "position", 0)

    def __eq__(self, other):
        return self.position == getattr(other, "position", 0)


class TestModerationHierarchyAndPermissions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock()
        self.mod_cog = Moderation(self.bot)

        # Mock guild
        self.guild = MagicMock(spec=discord.Guild)
        self.guild.id = 123456789
        self.guild.name = "Test Guild"

        # Server owner (Role pos 100)
        self.owner = MagicMock(spec=discord.Member)
        self.owner.id = 1000
        self.owner.name = "ServerOwner"
        self.owner.mention = "<@1000>"
        self.owner.top_role = FakeRole(100, "Owner")
        self.owner.guild_permissions = discord.Permissions.all()
        self.guild.owner = self.owner

        # Bot member (Role pos 50)
        self.bot_member = MagicMock(spec=discord.Member)
        self.bot_member.id = 2000
        self.bot_member.name = "CustomBot"
        self.bot_member.mention = "<@2000>"
        self.bot_member.top_role = FakeRole(50, "BotRole")
        bot_perms = MagicMock()
        bot_perms.ban_members = True
        bot_perms.kick_members = True
        bot_perms.moderate_members = True
        self.bot_member.guild_permissions = bot_perms
        self.guild.me = self.bot_member

        # Moderator with Ban Members permission (Role pos 40)
        self.moderator = MagicMock(spec=discord.Member)
        self.moderator.id = 3000
        self.moderator.name = "Moderator"
        self.moderator.mention = "<@3000>"
        self.moderator.top_role = FakeRole(40, "ModRole")
        mod_perms = MagicMock()
        mod_perms.ban_members = True
        mod_perms.kick_members = True
        mod_perms.moderate_members = True
        self.moderator.guild_permissions = mod_perms

        # Lower-role regular member (Role pos 10)
        self.lower_member = MagicMock(spec=discord.Member)
        self.lower_member.id = 4000
        self.lower_member.name = "RegularMember"
        self.lower_member.mention = "<@4000>"
        self.lower_member.top_role = FakeRole(10, "MemberRole")
        self.lower_member.display_avatar = MagicMock(url="https://example.com/avatar.png")
        self.lower_member.ban = AsyncMock()
        self.lower_member.kick = AsyncMock()

        # Equal or higher role member (Role pos 45 - higher than mod, lower than bot)
        self.high_member = MagicMock(spec=discord.Member)
        self.high_member.id = 5000
        self.high_member.name = "AdminMember"
        self.high_member.mention = "<@5000>"
        self.high_member.top_role = FakeRole(45, "AdminRole")
        self.high_member.ban = AsyncMock()

        # Superior member (Role pos 60 - higher than bot)
        self.superior_member = MagicMock(spec=discord.Member)
        self.superior_member.id = 6000
        self.superior_member.name = "SuperiorMember"
        self.superior_member.mention = "<@6000>"
        self.superior_member.top_role = FakeRole(60, "SuperiorRole")
        self.superior_member.ban = AsyncMock()

        # Regular user without Ban Members permission (Role pos 10)
        self.unprivileged_user = MagicMock(spec=discord.Member)
        self.unprivileged_user.id = 7000
        self.unprivileged_user.name = "UnprivilegedUser"
        self.unprivileged_user.top_role = FakeRole(10, "MemberRole")
        unpriv_perms = MagicMock()
        unpriv_perms.ban_members = False
        self.unprivileged_user.guild_permissions = unpriv_perms

    def _create_interaction(self, user):
        interaction = MagicMock(spec=discord.Interaction)
        interaction.guild = self.guild
        interaction.guild_id = self.guild.id
        interaction.user = user
        interaction.response.send_message = AsyncMock()
        interaction.response.is_done = MagicMock(return_value=False)
        return interaction

    async def test_moderator_with_ban_permission_bans_lower_role(self):
        """Test moderator with Ban Members permission successfully bans a lower-role member."""
        interaction = self._create_interaction(self.moderator)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.lower_member, reason="Rule violation")

        self.lower_member.ban.assert_called_once_with(reason="Rule violation")
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1].get("embed")
        self.assertIsNotNone(embed)
        self.assertIn("Member Banned", embed.title)

    async def test_moderator_trying_to_ban_equal_or_higher_role_fails(self):
        """Test moderator cannot ban someone with an equal or higher role."""
        interaction = self._create_interaction(self.moderator)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.high_member, reason="Attempted ban")

        self.high_member.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("equal or higher role", msg)

    async def test_moderator_trying_to_ban_server_owner_fails(self):
        """Test moderator cannot ban the server owner."""
        interaction = self._create_interaction(self.moderator)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.owner, reason="Attempted owner ban")

        self.owner.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("server owner", msg)

    async def test_bot_hierarchy_failure(self):
        """Test bot cannot ban a member whose highest role is equal to or higher than the bot's highest role."""
        interaction = self._create_interaction(self.owner)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.superior_member, reason="Superior ban")

        self.superior_member.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("role is higher than mine", msg)

    async def test_user_without_ban_members_permission_fails(self):
        """Test user without Ban Members permission is denied."""
        interaction = self._create_interaction(self.unprivileged_user)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.lower_member, reason="Unauthorized ban")

        self.lower_member.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("You do not have permission", msg)

    async def test_server_owner_bypasses_role_hierarchy(self):
        """Test server owner can ban a member with higher role than other mods."""
        interaction = self._create_interaction(self.owner)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.high_member, reason="Owner executive ban")

        self.high_member.ban.assert_called_once_with(reason="Owner executive ban")
        interaction.response.send_message.assert_called_once()

    async def test_server_owner_cannot_ban_themselves(self):
        """Test server owner cannot ban themselves."""
        interaction = self._create_interaction(self.owner)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.owner, reason="Self ban")

        self.owner.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("moderate yourself", msg)

    async def test_bot_without_ban_permission_fails(self):
        """Test friendly error when bot lacks Ban Members permission."""
        self.bot_member.guild_permissions.ban_members = False
        interaction = self._create_interaction(self.moderator)
        await self.mod_cog.ban_command.callback(self.mod_cog, interaction, self.lower_member, reason="Bot lacks perm")

        self.lower_member.ban.assert_not_called()
        interaction.response.send_message.assert_called_once()
        msg = interaction.response.send_message.call_args[0][0]
        self.assertIn("I do not have the required permissions", msg)

if __name__ == "__main__":
    unittest.main()
