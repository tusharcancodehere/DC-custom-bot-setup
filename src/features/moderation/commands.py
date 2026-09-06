from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

DEFAULT_REASON = "No reason provided"
MIN_TIMEOUT_MINUTES = 1
MIN_PURGE = 1
MAX_PURGE = 1000

SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if user == interaction.guild.owner:
            await interaction.response.send_message("You cannot kick the server owner.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot kick someone with an equal or higher role.", ephemeral=True)
            return
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot kick this member because their role is higher than mine.", ephemeral=True)
            return

        await user.kick(reason=reason)

        embed = discord.Embed(title="🔨 Member Kicked", color=ERROR_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if user == interaction.guild.owner:
            await interaction.response.send_message("You cannot ban the server owner.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot ban someone with an equal or higher role.", ephemeral=True)
            return
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot ban this member because their role is higher than mine.", ephemeral=True)
            return

        await user.ban(reason=reason)

        embed = discord.Embed(title="🔨 Member Banned", color=ERROR_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_command(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if minutes < MIN_TIMEOUT_MINUTES:
            await interaction.response.send_message("Duration must be at least 1 minute.", ephemeral=True)
            return
        if user == interaction.guild.owner:
            await interaction.response.send_message("You cannot timeout the server owner.", ephemeral=True)
            return
        if user.top_role >= interaction.user.top_role:
            await interaction.response.send_message("You cannot timeout someone with an equal or higher role.", ephemeral=True)
            return
        if user.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("I cannot timeout this member because their role is higher than mine.", ephemeral=True)
            return

        await user.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)

        embed = discord.Embed(title="⏱️ Member Timed Out", color=WARNING_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"{user.mention} (`{user.name}`)", inline=True)
        embed.add_field(name="⏳ Duration", value=f"{minutes} minute{'s' if minutes != 1 else ''}", inline=True)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="purge", description="Delete recent messages")
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

    @app_commands.command(name="unban", description="Unban a user")
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
        except (ValueError, discord.NotFound):
            await interaction.response.send_message("User not found or is not banned.", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = DEFAULT_REASON):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        dm_embed = discord.Embed(
            title=f"⚠️ Warning in {interaction.guild.name}",
            description=f"You received a warning from staff.\n\n**Reason:** {reason}",
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
        embed.add_field(name="📄 Reason", value=reason, inline=False)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))