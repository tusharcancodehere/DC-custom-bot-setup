import discord
from datetime import timedelta
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
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
        await interaction.response.send_message(f"{user.mention} was kicked. Reason: {reason}")

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
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
        await interaction.response.send_message(f"{user.mention} was banned. Reason: {reason}")

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout_command(self, interaction: discord.Interaction, user: discord.Member, minutes: int, reason: str = "No reason provided"):
        if minutes < 1:
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
        await interaction.response.send_message(f"{user.mention} was timed out for {minutes} minutes. Reason: {reason}")

    @app_commands.command(name="purge", description="Delete recent messages")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_command(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Amount must be between 1 and 100.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_command(self, interaction: discord.Interaction, user_id: str, reason: str = "No reason provided"):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user, reason=reason)
            await interaction.response.send_message(f"{user.mention} was unbanned. Reason: {reason}")
        except (ValueError, discord.NotFound):
            await interaction.response.send_message("User not found or is not banned.", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn_command(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        try:
            await user.send(f"You have been warned in **{interaction.guild.name}**.\nReason: {reason}")
        except discord.Forbidden:
            pass
        await interaction.response.send_message(f"{user.mention} was warned. Reason: {reason}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))