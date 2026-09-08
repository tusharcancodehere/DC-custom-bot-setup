import json
import logging
from collections import defaultdict
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import select

from database import database as db
from database.models import GuildConfig

EMBED_FILE = Path(__file__).parent / "embed.json"
PRIMARY_COLOR = 0x5865F2

class Welcome(commands.Cog):
    """Handles new member welcomes, farewells, and channel configuration."""

    def __init__(self, bot):
        self.bot = bot
        # Maps guild_id -> channel_id for custom welcome channels
        self.welcome_channels: dict[int, int] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        """Load persisted welcome configurations on bot startup."""
        await self.load_configs()

    async def load_configs(self):
        """Load welcome channel configurations from database into memory."""
        if not db.async_session:
            return
        try:
            async with db.async_session() as session:
                result = await session.execute(select(GuildConfig))
                for config in result.scalars().all():
                    if config.welcome_channel_id:
                        self.welcome_channels[config.guild_id] = config.welcome_channel_id
        except Exception as e:
            logging.error(f"Failed to load welcome configs from database: {e}")


    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle missing permissions gracefully with a friendly message."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You need the **Manage Server** permission to configure the welcome channel."
        else:
            message = f"❌ An error occurred: `{error}`"

        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    def get_welcome_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Find the welcome channel for a guild, checking custom config first then fallbacks."""
        # 1. Custom configured channel
        channel_id = self.welcome_channels.get(guild.id)
        if channel_id:
            channel = guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel

        # 2. Guild system channel (default in Discord)
        if guild.system_channel:
            return guild.system_channel

        # 3. Search for a channel with "welcome", "joins", or "general" in its name
        for channel in guild.text_channels:
            name = channel.name.lower()
            if any(keyword in name for keyword in ("welcome", "join", "general")):
                return channel

        # 4. Fallback to the first text channel where the bot can send messages
        for channel in guild.text_channels:
            if guild.me and channel.permissions_for(guild.me).send_messages:
                return channel

        return None

    def resolve_channels(self, guild: discord.Guild) -> dict:
        """Resolve common channel names to mentions for embed placeholders."""
        channels = {channel.name.lower(): channel.mention for channel in guild.text_channels}

        def find_channel(keyword: str, fallback: str) -> str:
            for name, mention in channels.items():
                if keyword in name:
                    return mention
            return fallback

        resolved = defaultdict(lambda: "#channel")
        resolved.update(channels)
        resolved["rules"] = find_channel("rule", "#rules")
        resolved["roles"] = find_channel("role", "#roles")
        resolved["announcements"] = find_channel("announc", find_channel("news", "#announcements"))
        resolved["general"] = find_channel("general", find_channel("chat", "#general"))
        resolved["support"] = find_channel("support", find_channel("ticket", "#support"))
        return resolved

    def build_welcome_embed(self, guild: discord.Guild, member: discord.Member | discord.User) -> discord.Embed:
        """Build the welcome embed with dynamic placeholders formatted for the member."""
        with open(EMBED_FILE, encoding="utf-8") as file:
            raw_data = json.load(file)

        data = raw_data["embeds"][0].copy()
        channel_map = self.resolve_channels(guild)
        server_icon = guild.icon.url if guild.icon else ""

        channel_map["server"] = guild.name
        channel_map["user"] = member.mention
        channel_map["member"] = member.mention
        channel_map["username"] = member.name
        channel_map["server_icon"] = server_icon

        title = data.get("title", "Welcome").format_map(channel_map)
        description = data.get("description", "").format_map(channel_map)

        embed = discord.Embed(title=title, description=description, color=data.get("color", PRIMARY_COLOR))
        embed.timestamp = discord.utils.utcnow()

        if server_icon:
            embed.set_thumbnail(url=server_icon)
            embed.set_footer(text=f"{guild.name} • Welcome", icon_url=server_icon)
        else:
            embed.set_footer(text=f"{guild.name} • Welcome")

        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Automatically send a welcome message when a new member joins."""
        if member.bot:
            return

        channel = self.get_welcome_channel(member.guild)
        if not channel:
            return

        # Check bot permissions in channel
        if member.guild.me and not channel.permissions_for(member.guild.me).send_messages:
            logging.warning(f"Missing send_messages permission in welcome channel {channel.name} ({member.guild.name})")
            return

        embed = self.build_welcome_embed(member.guild, member)
        try:
            await channel.send(content=f"Welcome to **{member.guild.name}**, {member.mention}!", embed=embed)
        except Exception as e:
            logging.error(f"Failed to send welcome message in {member.guild.name}: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Send a polite farewell notification when a member leaves."""
        if member.bot:
            return

        channel = self.get_welcome_channel(member.guild)
        if not channel:
            return

        if member.guild.me and not channel.permissions_for(member.guild.me).send_messages:
            return

        try:
            await channel.send(f"👋 **{member.name}** has left the server.")
        except Exception as e:
            logging.error(f"Failed to send leave message in {member.guild.name}: {e}")

    @app_commands.command(name="welcome", description="Show a preview of the welcome message")
    async def welcome_command(self, interaction: discord.Interaction):
        """Preview the welcome message for this server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        embed = self.build_welcome_embed(interaction.guild, interaction.user)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_welcome_channel", description="Configure the channel for welcome messages")
    @app_commands.describe(channel="The text channel for welcome messages (leave empty to view current)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        """Set or view the welcome channel for this server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if channel is None:
            current = self.get_welcome_channel(interaction.guild)
            if current:
                await interaction.response.send_message(f"📢 Welcome messages are currently sent to {current.mention}.")
            else:
                await interaction.response.send_message("📢 No welcome channel is currently configured.")
            return

        self.welcome_channels[interaction.guild.id] = channel.id
        if db.async_session:
            try:
                async with db.async_session() as session:
                    stmt = select(GuildConfig).where(GuildConfig.guild_id == interaction.guild.id)
                    result = await session.execute(stmt)
                    config = result.scalar_one_or_none()
                    if config:
                        config.welcome_channel_id = channel.id
                    else:
                        config = GuildConfig(guild_id=interaction.guild.id, welcome_channel_id=channel.id)
                        session.add(config)
                    await session.commit()
            except Exception as e:
                logging.error(f"Failed to persist welcome channel for guild {interaction.guild.id}: {e}")

        await interaction.response.send_message(f"✅ Welcome channel has been set to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
