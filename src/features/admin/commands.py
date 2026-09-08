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

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle missing permissions gracefully with a friendly message."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You need the **Manage Server** or **Administrator** permission to use this command."
            if not interaction.response.is_done():
                await interaction.response.send_message(message, ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
        else:
            message = f"❌ An error occurred: `{error}`"
            if not interaction.response.is_done():
                await interaction.response.send_message(message, ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)

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

    @app_commands.command(name="server_settings", description="View current administrative server settings")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def server_settings_command(self, interaction: discord.Interaction):
        """Display current server configuration settings.
        
        This command acts as the central hub for server configuration and can be
        expanded in the future for configurable welcome channels, logs, and roles.
        """
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild = interaction.guild
        system_channel = guild.system_channel.mention if guild.system_channel else "*None*"
        rules_channel = guild.rules_channel.mention if guild.rules_channel else "*None*"
        verification = str(guild.verification_level).capitalize()

        embed = discord.Embed(title=f"⚙️ Administrative Settings: {guild.name}", color=ADMIN_COLOR)
        embed.add_field(name="🛡️ Verification Level", value=f"`{verification}`", inline=True)
        embed.add_field(name="📜 Rules Channel", value=rules_channel, inline=True)
        embed.add_field(name="📢 System Channel", value=system_channel, inline=True)
        embed.add_field(name="🤖 Bot Role", value=guild.me.top_role.mention, inline=True)
        embed.add_field(
            name="💡 Administration Note",
            value="This server uses default settings. Future updates will allow configuring custom channels and roles.",
            inline=False,
        )

        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"{guild.name} • Settings")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
