import sys

import discord
from discord import app_commands
from discord.ext import commands

ADMIN_COLOR = 0x5865F2

class Admin(commands.Cog):
    """Server and bot administration commands.
    
    This cog handles configuration and server information rather than member punishments.
    It is kept separate from Moderation so that administrative tools can grow cleanly.
    """
    def __init__(self, bot):
        self.bot = bot
        # In-memory mapping of guild_id -> channel_id for moderation logs
        self.modlog_channels: dict[int, int] = {}

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle missing permissions gracefully with a friendly message."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You need the **Manage Server** or **Administrator** permission to use this command."
        else:
            message = f"❌ An error occurred: `{error}`"

        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    def get_modlog_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Get the configured moderation log channel for a guild."""
        channel_id = self.modlog_channels.get(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel
        return None

    @app_commands.command(name="serverinfo", description="View administrative details about the server")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def serverinfo_command(self, interaction: discord.Interaction):
        """Display an administrative overview of the current server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild = interaction.guild
        owner = guild.owner.mention if guild.owner else f"ID: {guild.owner_id}"
        created_at = guild.created_at.strftime("%B %d, %Y")
        
        # Count humans vs bots for server admins
        total_members = guild.member_count or len(guild.members)
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count if total_members >= bot_count else total_members

        embed = discord.Embed(title=f"📊 Server Administration: {guild.name}", color=ADMIN_COLOR)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 Owner", value=owner, inline=True)
        embed.add_field(name="📅 Created On", value=created_at, inline=True)

        embed.add_field(
            name="👥 Members",
            value=f"Total: **{total_members:,}**\nHumans: **{human_count:,}** • Bots: **{bot_count}**",
            inline=True,
        )
        embed.add_field(
            name="💬 Channels",
            value=f"Text: **{len(guild.text_channels)}**\nVoice: **{len(guild.voice_channels)}**",
            inline=True,
        )
        embed.add_field(name="🏷️ Roles", value=f"**{len(guild.roles)}** roles", inline=True)

        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="View bot runtime statistics and system status")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def botinfo_command(self, interaction: discord.Interaction):
        """Display runtime and status information about the bot."""
        latency_ms = round(self.bot.latency * 1000)
        guild_count = len(self.bot.guilds)
        total_users = sum(g.member_count or len(g.members) for g in self.bot.guilds)

        embed = discord.Embed(title="🤖 Bot Administrative Overview", color=ADMIN_COLOR)
        if self.bot.user and self.bot.user.display_avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(name="🟢 Status", value="Operational", inline=True)
        embed.add_field(name="📡 Latency", value=f"`{latency_ms}ms`", inline=True)
        embed.add_field(name="🌐 Connected Servers", value=f"**{guild_count}**", inline=True)
        embed.add_field(name="👥 Visible Users", value=f"**{total_users:,}**", inline=True)
        embed.add_field(name="🐍 Python Version", value=f"`{sys.version.split()[0]}`", inline=True)
        embed.add_field(name="📚 discord.py Version", value=f"`{discord.__version__}`", inline=True)

        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_modlog_channel", description="Set or view the moderation log channel")
    @app_commands.describe(channel="The channel for moderation logs (leave empty to view current)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_modlog_channel(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        """Set or view the channel where moderation actions are logged."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if channel is None:
            current = self.get_modlog_channel(interaction.guild)
            if current:
                await interaction.response.send_message(f"📋 Moderation logs are currently sent to {current.mention}.")
            else:
                await interaction.response.send_message("📋 No moderation log channel is currently configured.")
            return

        self.modlog_channels[interaction.guild.id] = channel.id
        await interaction.response.send_message(f"✅ Moderation log channel set to {channel.mention}.")

    @app_commands.command(name="announce", description="Post a formatted announcement embed to a channel")
    @app_commands.describe(channel="Target channel for announcement", message="Announcement message text", title="Optional announcement title")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def announce_command(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str, title: str = "📢 Server Announcement"):
        """Post a formatted server announcement to a designated channel."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        embed = discord.Embed(title=title, description=message, color=ADMIN_COLOR)
        embed.timestamp = discord.utils.utcnow()
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"Posted by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Announcement posted in {channel.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I lack permission to send messages in {channel.mention}.", ephemeral=True)

    @app_commands.command(name="server_settings", description="View current administrative server settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def server_settings_command(self, interaction: discord.Interaction):
        """Display current server configuration settings."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild = interaction.guild
        system_channel = guild.system_channel.mention if guild.system_channel else "*None*"
        rules_channel = guild.rules_channel.mention if guild.rules_channel else "*None*"
        verification = str(guild.verification_level).capitalize()

        welcome_cog = self.bot.get_cog("Welcome")
        welcome_ch = welcome_cog.get_welcome_channel(guild) if welcome_cog else None
        welcome_channel = welcome_ch.mention if welcome_ch else "*None*"

        modlog_ch = self.get_modlog_channel(guild)
        modlog_channel = modlog_ch.mention if modlog_ch else "*None*"

        embed = discord.Embed(title=f"⚙️ Administrative Settings: {guild.name}", color=ADMIN_COLOR)
        embed.add_field(name="🛡️ Verification Level", value=f"`{verification}`", inline=True)
        embed.add_field(name="📜 Rules Channel", value=rules_channel, inline=True)
        embed.add_field(name="📢 System Channel", value=system_channel, inline=True)
        embed.add_field(name="👋 Welcome Channel", value=welcome_channel, inline=True)
        embed.add_field(name="📋 Mod Log Channel", value=modlog_channel, inline=True)
        embed.add_field(name="🤖 Bot Role", value=guild.me.top_role.mention, inline=True)
        embed.add_field(
            name="💡 Administration Note",
            value="Configure channels using `/set_welcome_channel` and `/set_modlog_channel`.",
            inline=False,
        )

        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"{guild.name} • Settings")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
