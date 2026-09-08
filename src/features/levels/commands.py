from datetime import datetime, timezone
import json
from pathlib import Path
import random
import time

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import func, select

from database.database import async_session
from database.models import UserXP

EMBED_FILE = Path(__file__).parent / "embed.json"
PRIMARY_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
COOLDOWN_SECONDS = 60
MIN_MESSAGE_LENGTH = 5
XP_MIN = 15
XP_MAX = 25
PROGRESS_BAR_LENGTH = 12
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

def xp_for_level(level: int) -> int:
    if level <= 0:
        return 0
    return int(100 * (level ** 1.5))

def calculate_level(xp: int) -> int:
    if xp < 100:
        return 0
    lvl = int((xp / 100) ** (2 / 3) + 1e-9)
    while xp_for_level(lvl + 1) <= xp:
        lvl += 1
    while lvl > 0 and xp_for_level(lvl) > xp:
        lvl -= 1
    return lvl

def create_progress_bar(current: int, total: int, length: int = PROGRESS_BAR_LENGTH) -> str:
    if total <= 0:
        return "░" * length
    filled = min(length, max(0, int((current / total) * length)))
    return "█" * filled + "░" * (length - filled)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        with open(EMBED_FILE, encoding="utf-8") as file:
            self.embed_data = json.load(file)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            else:
                await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)
        else:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ An error occurred: `{error}`", ephemeral=True)
            else:
                await interaction.followup.send(f"❌ An error occurred: `{error}`", ephemeral=True)

    async def get_or_create_user(self, session, guild_id: int, user_id: int) -> UserXP:
        user_xp = await session.get(UserXP, (guild_id, user_id))
        if not user_xp:
            user_xp = UserXP(guild_id=guild_id, user_id=user_id, xp=0, level=0, last_xp=datetime.now(timezone.utc))
            session.add(user_xp)
            await session.flush()
        return user_xp

    def build_level_embed(self, user: discord.Member, guild: discord.Guild, level: int, xp: int, rank: int) -> discord.Embed:
        current_base = xp_for_level(level)
        next_base = xp_for_level(level + 1)
        progress_in_level = max(0, xp - current_base)
        needed_in_level = max(1, next_base - current_base)
        percentage = min(100, round((progress_in_level / needed_in_level) * 100))
        progress_bar = create_progress_bar(progress_in_level, needed_in_level)

        data = self.embed_data["embeds"][0].copy()
        title = data.get("title", "⚡ {username}'s Level").format(username=user.name)
        description = data.get("description", "").format(
            rank=rank,
            level=level,
            xp=xp,
            next_xp=next_base,
            next_level=level + 1,
            progress_bar=progress_bar,
            percentage=percentage,
        )

        embed = discord.Embed(title=title, description=description, color=data.get("color", PRIMARY_COLOR))
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        server_icon = guild.icon.url if guild and guild.icon else None
        if server_icon:
            embed.set_author(name=guild.name, icon_url=server_icon)
            embed.set_footer(text=f"{guild.name} • Level System", icon_url=server_icon)
        elif guild:
            embed.set_author(name=guild.name)
            embed.set_footer(text=f"{guild.name} • Level System")

        return embed

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if len(message.content.strip()) < MIN_MESSAGE_LENGTH:
            return

        if not async_session:
            return

        now = time.monotonic()
        key = (message.guild.id, message.author.id)
        if now - self.cooldowns.get(key, 0) < COOLDOWN_SECONDS:
            return
        self.cooldowns[key] = now

        xp_gain = random.randint(XP_MIN, XP_MAX)
        old_level = 0
        new_level = 0

        async with async_session() as session:
            async with session.begin():
                user_xp = await self.get_or_create_user(session, message.guild.id, message.author.id)
                old_level = user_xp.level
                user_xp.xp += xp_gain
                new_level = calculate_level(user_xp.xp)
                user_xp.level = new_level
                user_xp.last_xp = datetime.now(timezone.utc)

        if new_level > old_level:
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"Congratulations {message.author.mention}, you reached **Level {new_level}**!",
                color=SUCCESS_COLOR,
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.timestamp = discord.utils.utcnow()
            try:
                await message.channel.send(embed=embed)
            except discord.HTTPException:
                pass

    @app_commands.command(name="level", description="Show the current level and XP of a user")
    async def level_command(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        target = user or interaction.user
        async with async_session() as session:
            user_xp = await session.get(UserXP, (interaction.guild.id, target.id))
            xp = user_xp.xp if user_xp else 0
            level = user_xp.level if user_xp else 0

            rank_stmt = (
                select(func.count())
                .select_from(UserXP)
                .where(UserXP.guild_id == interaction.guild.id, UserXP.xp > xp)
            )
            rank = (await session.scalar(rank_stmt) or 0) + 1

        embed = self.build_level_embed(target, interaction.guild, level, xp, rank)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank", description="Show the rank of a user within the server")
    async def rank_command(self, interaction: discord.Interaction, user: discord.Member | None = None):
        await self.level_command(interaction, user)

    @app_commands.command(name="leaderboard", description="Show the highest-XP members in this server")
    async def leaderboard_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        async with async_session() as session:
            stmt = (
                select(UserXP)
                .where(UserXP.guild_id == interaction.guild.id)
                .order_by(UserXP.xp.desc())
                .limit(10)
            )
            rows = (await session.scalars(stmt)).all()

        server_name = interaction.guild.name
        server_icon = interaction.guild.icon.url if interaction.guild.icon else None

        if not rows:
            embed = discord.Embed(
                title="🏆 Server Leaderboard",
                description="No experience recorded in this server yet.\n\n*Chat in text channels to earn XP!*",
                color=PRIMARY_COLOR,
            )
        else:
            lines = ["Top active members ranked by experience:\n"]
            for idx, row in enumerate(rows, start=1):
                medal = MEDALS.get(idx, f"`{idx}.`")
                member = interaction.guild.get_member(row.user_id)
                name = member.mention if member else f"User `{row.user_id}`"
                lines.append(f"{medal} **{name}** — Level {row.level} • `{row.xp:,} XP`")

            lines.append("\n*Chat in text channels to climb the ranks!*")
            embed = discord.Embed(
                title="🏆 Server Leaderboard",
                description="\n".join(lines),
                color=PRIMARY_COLOR,
            )

        embed.timestamp = discord.utils.utcnow()
        if server_icon:
            embed.set_thumbnail(url=server_icon)
            embed.set_footer(text=f"{server_name} • Leaderboard", icon_url=server_icon)
        else:
            embed.set_footer(text=f"{server_name} • Leaderboard")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="show_xp", description="Show the current XP breakdown of a user")
    async def show_xp_command(self, interaction: discord.Interaction, user: discord.Member | None = None):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        target = user or interaction.user
        async with async_session() as session:
            user_xp = await session.get(UserXP, (interaction.guild.id, target.id))
            xp = user_xp.xp if user_xp else 0
            level = user_xp.level if user_xp else 0

        current_base = xp_for_level(level)
        next_base = xp_for_level(level + 1)
        progress = max(0, xp - current_base)
        needed = max(1, next_base - current_base)
        percentage = min(100, round((progress / needed) * 100))
        progress_bar = create_progress_bar(progress, needed)

        embed = discord.Embed(
            title=f"✨ {target.name}'s Experience",
            description=(
                f"👤 **Member:** {target.mention}\n"
                f"⭐ **Level:** `{level}`\n"
                f"✨ **Total XP:** `{xp:,} XP`\n"
                f"🎯 **Next Milestone:** Level {level + 1} (`{next_base:,} XP`)\n\n"
                f"`{progress_bar}` {percentage}%"
            ),
            color=PRIMARY_COLOR,
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text=f"{interaction.guild.name} • Level System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="add_xp", description="Add XP to a member (Admin)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def add_xp_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        async with async_session() as session:
            async with session.begin():
                user_xp = await self.get_or_create_user(session, interaction.guild.id, user.id)
                user_xp.xp += amount
                user_xp.level = calculate_level(user_xp.xp)
                user_xp.last_xp = datetime.now(timezone.utc)
                new_xp = user_xp.xp
                new_level = user_xp.level

        embed = discord.Embed(
            title="✨ XP Added",
            description=f"Successfully added **{amount:,} XP** to {user.mention}.\n\n⭐ **Level:** `{new_level}`\n✨ **Total XP:** `{new_xp:,} XP`",
            color=SUCCESS_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove_xp", description="Remove XP from a member (Admin)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def remove_xp_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        async with async_session() as session:
            async with session.begin():
                user_xp = await self.get_or_create_user(session, interaction.guild.id, user.id)
                user_xp.xp = max(0, user_xp.xp - amount)
                user_xp.level = calculate_level(user_xp.xp)
                user_xp.last_xp = datetime.now(timezone.utc)
                new_xp = user_xp.xp
                new_level = user_xp.level

        embed = discord.Embed(
            title="📉 XP Removed",
            description=f"Successfully removed **{amount:,} XP** from {user.mention}.\n\n⭐ **Level:** `{new_level}`\n✨ **Total XP:** `{new_xp:,} XP`",
            color=WARNING_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_xp", description="Set a member's XP directly (Admin)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def set_xp_command(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not async_session:
            await interaction.response.send_message("Database is not configured. Persistent XP is currently unavailable.", ephemeral=True)
            return

        if amount < 0:
            await interaction.response.send_message("XP amount cannot be negative.", ephemeral=True)
            return

        async with async_session() as session:
            async with session.begin():
                user_xp = await self.get_or_create_user(session, interaction.guild.id, user.id)
                user_xp.xp = amount
                user_xp.level = calculate_level(user_xp.xp)
                user_xp.last_xp = datetime.now(timezone.utc)
                new_xp = user_xp.xp
                new_level = user_xp.level

        embed = discord.Embed(
            title="⚙️ XP Set",
            description=f"Successfully set {user.mention}'s XP to **{new_xp:,} XP**.\n\n⭐ **Level:** `{new_level}`",
            color=PRIMARY_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))