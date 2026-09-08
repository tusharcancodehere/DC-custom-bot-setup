from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

DEFAULT_REASON = "No reason provided"
MIN_TIMEOUT_MINUTES = 1
MIN_PURGE = 1
MAX_PURGE = 1000
MAX_SLOWMODE_SECONDS = 21600

SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

class Moderation(commands.Cog):
    """Server moderation and enforcement commands."""

    def __init__(self, bot):
        self.bot = bot
        # In-memory warning records mapped by [guild_id][user_id]
        self.warnings: dict[int, dict[int, list[dict]]] = {}

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle common moderation command errors with friendly feedback."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You do not have permission to use this moderation command."
        elif isinstance(error, app_commands.BotMissingPermissions):
            message = "❌ I do not have the required permissions to perform this action."
        else:
            message = f"❌ An error occurred: `{error}`"

        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    async def _log_action(self, guild: discord.Guild, embed: discord.Embed):
        """Send a copy of moderation action embed to the configured modlog channel if present."""
        admin_cog = self.bot.get_cog("Admin")
        if admin_cog and hasattr(admin_cog, "get_modlog_channel"):
            channel = admin_cog.get_modlog_channel(guild)
            if channel and guild.me and channel.permissions_for(guild.me).send_messages:
                try:
                    await channel.send(embed=embed)
                except Exception:
                    pass

    def _check_hierarchy(self, interaction: discord.Interaction, target: discord.Member) -> str | None:
        """Verify role hierarchy so moderators cannot target server owner, bot, or equals/superiors."""
        if target == interaction.guild.owner:
            return "You cannot moderate the server owner."
        if target == interaction.guild.me:
            return "I cannot moderate myself."
        if target.top_role >= interaction.user.top_role and interaction.user != interaction.guild.owner:
            return "You cannot moderate someone with an equal or higher role."
        if target.top_role >= interaction.guild.me.top_role:
            return "I cannot moderate this member because their role is higher than mine."
        return None

    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        hierarchy_error = self._check_hierarchy(interaction, user)
        if hierarchy_error:
            await interaction.response.send_message(f"❌ {hierarchy_error}", ephemeral=True)
            return

        await user.kick(reason=reason)

        embed = discord.Embed(title="🔨 Member Kicked", color=ERROR_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        hierarchy_error = self._check_hierarchy(interaction, user)
        if hierarchy_error:
            await interaction.response.send_message(f"❌ {hierarchy_error}", ephemeral=True)
            return

        await user.ban(reason=reason)

        embed = discord.Embed(title="🔨 Member Banned", color=ERROR_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="unban", description="Unban a user by their user ID")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_command(self, interaction: discord.Interaction, user_id: str, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)

            embed = discord.Embed(title="🔓 Member Unbanned", color=SUCCESS_COLOR)
            embed.add_field(name="👤 User", value=f"{user.mention} (`{user.name}`)", inline=True)
            embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="📄 Reason", value=reason, inline=False)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed)
            await self._log_action(interaction.guild, embed)
        except (ValueError, discord.NotFound):
            await interaction.response.send_message("❌ User not found or is not banned.", ephemeral=True)

    @app_commands.command(name="timeout", description="Temporarily mute/timeout a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_command(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if minutes < MIN_TIMEOUT_MINUTES:
            await interaction.response.send_message("Duration must be at least 1 minute.", ephemeral=True)
            return

        hierarchy_error = self._check_hierarchy(interaction, user)
        if hierarchy_error:
            await interaction.response.send_message(f"❌ {hierarchy_error}", ephemeral=True)
            return

        until = discord.utils.utcnow() + timedelta(minutes=minutes)
        await user.timeout(until, reason=reason)

        embed = discord.Embed(title="⏱️ Member Timed Out", color=WARNING_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="⏳ Duration", value=f"{minutes} minute{'s' if minutes != 1 else ''}", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="warn", description="Issue a formal warning to a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        hierarchy_error = self._check_hierarchy(interaction, user)
        if hierarchy_error:
            await interaction.response.send_message(f"❌ {hierarchy_error}", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if guild_id not in self.warnings:
            self.warnings[guild_id] = {}
        if user.id not in self.warnings[guild_id]:
            self.warnings[guild_id][user.id] = []

        warn_id = len(self.warnings[guild_id][user.id]) + 1
        record = {
            "id": warn_id,
            "moderator": interaction.user.name,
            "moderator_id": interaction.user.id,
            "reason": reason,
            "time": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        }
        self.warnings[guild_id][user.id].append(record)
        total_warnings = len(self.warnings[guild_id][user.id])

        # Attempt sending DM to warned member
        dm_embed = discord.Embed(
            title=f"⚠️ Warning in {interaction.guild.name}",
            description=f"You received a warning from staff.\n\n**Reason:** {reason}\n**Total Warnings:** {total_warnings}",
            color=WARNING_COLOR,
        )
        dm_embed.timestamp = discord.utils.utcnow()
        if interaction.guild.icon:
            dm_embed.set_thumbnail(url=interaction.guild.icon.url)

        try:
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass

        embed = discord.Embed(title="⚠️ Warning Issued", color=WARNING_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="🔢 Total Warnings", value=f"**{total_warnings}**", inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="warnings", description="View warning history for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warnings_command(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        user_warnings = self.warnings.get(guild_id, {}).get(user.id, [])

        if not user_warnings:
            await interaction.response.send_message(f"ℹ️ {user.mention} has no recorded warnings.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"⚠️ Warning History: {user.name}",
            description=f"Total warnings: **{len(user_warnings)}**",
            color=WARNING_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        for item in user_warnings[-10:]:
            embed.add_field(
                name=f"Case #{item['id']} • {item['time']}",
                value=f"**Reason:** {item['reason']}\n**Moderator:** {item['moderator']}",
                inline=False,
            )

        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clear_warnings", description="Clear all warnings for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clear_warnings_command(self, interaction: discord.Interaction, user: discord.Member):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if guild_id in self.warnings and user.id in self.warnings[guild_id]:
            count = len(self.warnings[guild_id][user.id])
            del self.warnings[guild_id][user.id]
            await interaction.response.send_message(f"✅ Cleared **{count}** warning{'s' if count != 1 else ''} for {user.mention}.")
        else:
            await interaction.response.send_message(f"ℹ️ {user.mention} has no warnings to clear.", ephemeral=True)

    @app_commands.command(name="lock", description="Lock a channel to prevent regular members from sending messages")
    @app_commands.describe(channel="The channel to lock (defaults to current channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock_command(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("❌ This command can only lock text channels.", ephemeral=True)
            return

        overwrite = target.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        await target.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=f"Locked by {interaction.user}")

        embed = discord.Embed(title="🔒 Channel Locked", description=f"{target.mention} has been locked by staff.", color=ERROR_COLOR)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="unlock", description="Unlock a channel allowing regular members to send messages")
    @app_commands.describe(channel="The channel to unlock (defaults to current channel)")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock_command(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("❌ This command can only unlock text channels.", ephemeral=True)
            return

        overwrite = target.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = None
        await target.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {interaction.user}")

        embed = discord.Embed(title="🔓 Channel Unlocked", description=f"{target.mention} has been unlocked by staff.", color=SUCCESS_COLOR)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="slowmode", description="Set or disable slowmode delay in a channel")
    @app_commands.describe(seconds="Slowmode cooldown in seconds (0 to disable)", channel="Target channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode_command(self, interaction: discord.Interaction, seconds: int, channel: discord.TextChannel | None = None):
        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("❌ This command can only set slowmode in text channels.", ephemeral=True)
            return

        if seconds < 0 or seconds > MAX_SLOWMODE_SECONDS:
            await interaction.response.send_message(f"❌ Seconds must be between 0 and {MAX_SLOWMODE_SECONDS}.", ephemeral=True)
            return

        await target.edit(slowmode_delay=seconds, reason=f"Slowmode set by {interaction.user}")

        if seconds == 0:
            desc = f"Slowmode has been **disabled** in {target.mention}."
        else:
            desc = f"Slowmode in {target.mention} set to **{seconds}** second{'s' if seconds != 1 else ''}."

        embed = discord.Embed(title="⏱️ Slowmode Updated", description=desc, color=SUCCESS_COLOR)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)
        await self._log_action(interaction.guild, embed)

    @app_commands.command(name="purge", description="Bulk delete recent messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_command(self, interaction: discord.Interaction, amount: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if amount < MIN_PURGE or amount > MAX_PURGE:
            await interaction.response.send_message(f"Amount must be between {MIN_PURGE} and {MAX_PURGE}.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)

        embed = discord.Embed(
            title="🧹 Messages Purged",
            description=f"Successfully deleted **{len(deleted)}** message{'s' if len(deleted) != 1 else ''}.",
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text=f"Purged by {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))