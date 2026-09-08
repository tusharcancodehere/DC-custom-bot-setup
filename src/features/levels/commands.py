import json
import logging
from pathlib import Path
import random
import time

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy import func, select

from database import database as db
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
    """Calculate the minimum total XP required to reach a specific level."""
    if level <= 0:
        return 0
    return int(100 * (level ** 1.5))

def calculate_level(xp: int) -> int:
    """Calculate the user's level based on their total XP points."""
    if xp < 100:
        return 0
    lvl = int((xp / 100) ** (2 / 3) + 1e-9)
    while xp_for_level(lvl + 1) <= xp:
        lvl += 1
    while lvl > 0 and xp_for_level(lvl) > xp:
        lvl -= 1
    return lvl

def create_progress_bar(current: int, total: int, length: int = PROGRESS_BAR_LENGTH) -> str:
    """Create a visual text progress bar for rank cards."""
    if total <= 0:
        return "░" * length
    filled = min(length, max(0, int((current / total) * length)))
    return "█" * filled + "░" * (length - filled)

class Levels(commands.Cog):
    """Level and XP system with complete per-guild data isolation."""
    def __init__(self, bot):
        self.bot = bot
        # Guild-isolated storage: guild_id -> {user_id: {"xp": int, "level": int, "last_xp": float}}
        # This guarantees that User XP in Server A never affects or leaks into Server B.
        self.guild_xp: dict[int, dict[int, dict]] = {}
        # Cooldown tracking: (guild_id, user_id) -> timestamp
        self.cooldowns: dict[tuple[int, int], float] = {}

        # Load customizable rank card embed structure
        with open(EMBED_FILE, encoding="utf-8") as file:
            self.embed_data = json.load(file)

    def get_user_data(self, guild_id: int, user_id: int) -> dict:
        """Get or initialize user XP record for a specific guild."""
        if guild_id not in self.guild_xp:
            self.guild_xp[guild_id] = {}
        if user_id not in self.guild_xp[guild_id]:
            self.guild_xp[guild_id][user_id] = {
                "xp": 0,
                "level": 0,
                "last_xp": 0.0,
            }
        return self.guild_xp[guild_id][user_id]

    async def get_or_fetch_user_data(self, guild_id: int, user_id: int) -> dict:
        """Fetch user record from memory cache, or load from database if present."""
        if guild_id in self.guild_xp and user_id in self.guild_xp[guild_id]:
            return self.guild_xp[guild_id][user_id]

        if db.async_session:
            try:
                async with db.async_session() as session:
                    stmt = select(UserXP).where(UserXP.guild_id == guild_id, UserXP.user_id == user_id)
                    result = await session.execute(stmt)
                    record = result.scalar_one_or_none()
                    if record:
                        if guild_id not in self.guild_xp:
                            self.guild_xp[guild_id] = {}
                        self.guild_xp[guild_id][user_id] = {
                            "xp": record.xp,
                            "level": record.level,
                            "last_xp": record.last_xp.timestamp() if record.last_xp else 0.0,
                        }
                        return self.guild_xp[guild_id][user_id]
            except Exception as e:
                logging.error(f"Failed to fetch XP for user {user_id} in guild {guild_id}: {e}")

        return self.get_user_data(guild_id, user_id)

    async def _persist_user_xp(self, guild_id: int, user_id: int, xp: int, level: int):
        """Persist updated XP and level to the database."""
        if not db.async_session:
            return
        try:
            async with db.async_session() as session:
                stmt = select(UserXP).where(UserXP.guild_id == guild_id, UserXP.user_id == user_id)
                result = await session.execute(stmt)
                record = result.scalar_one_or_none()
                if record:
                    record.xp = xp
                    record.level = level
                    record.last_xp = discord.utils.utcnow()
                else:
                    record = UserXP(guild_id=guild_id, user_id=user_id, xp=xp, level=level)
                    session.add(record)
                await session.commit()
        except Exception as e:
            logging.error(f"Failed to persist XP for user {user_id}: {e}")

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle missing permissions gracefully with a friendly message."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You do not have permission to use this command."
        else:
            message = f"❌ An error occurred: `{error}`"

        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    def build_level_embed(self, user: discord.Member, guild: discord.Guild, level: int, xp: int, rank: int) -> discord.Embed:
        """Construct the formatted rank card embed from embed.json."""
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
        """Award random XP on eligible chat messages with anti-spam cooldowns."""
        # Ignore bot messages and direct messages
        if message.author.bot or not message.guild:
            return

        # Ignore short messages to prevent spam abuse
        if len(message.content.strip()) < MIN_MESSAGE_LENGTH:
            return

        # Enforce 60-second cooldown per user per guild
        now = time.monotonic()
        key = (message.guild.id, message.author.id)
        if now - self.cooldowns.get(key, 0) < COOLDOWN_SECONDS:
            return
        self.cooldowns[key] = now

        # Fetch isolated record for this guild
        user_data = await self.get_or_fetch_user_data(message.guild.id, message.author.id)
        old_level = user_data["level"]
        xp_gain = random.randint(XP_MIN, XP_MAX)
        user_data["xp"] += xp_gain
        new_level = calculate_level(user_data["xp"])
        user_data["level"] = new_level
        user_data["last_xp"] = time.time()
        await self._persist_user_xp(message.guild.id, message.author.id, user_data["xp"], user_data["level"])

        # Send celebration announcement when reaching a new level
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
        """Display rank card with level progress and percentage."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        target = user or interaction.user
        user_data = await self.get_or_fetch_user_data(interaction.guild.id, target.id)
        xp = user_data["xp"]
        level = user_data["level"]

        # Calculate rank relative only to members in this server
        rank = 1
        if db.async_session:
            try:
                async with db.async_session() as session:
                    stmt = select(func.count()).select_from(UserXP).where(UserXP.guild_id == interaction.guild.id, UserXP.xp > xp)
                    res = await session.execute(stmt)
                    higher_count = res.scalar_one_or_none() or 0
                    rank = higher_count + 1
            except Exception:
                guild_users = self.guild_xp.get(interaction.guild.id, {})
                rank = sum(1 for data in guild_users.values() if data.get("xp", 0) > xp) + 1
        else:
            guild_users = self.guild_xp.get(interaction.guild.id, {})
            rank = sum(1 for data in guild_users.values() if data.get("xp", 0) > xp) + 1

        embed = self.build_level_embed(target, interaction.guild, level, xp, rank)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank", description="Show the rank of a user within the server")
    async def rank_command(self, interaction: discord.Interaction, user: discord.Member | None = None):
        """Alias for /level."""
        await self.level_command(interaction, user)

    @app_commands.command(name="leaderboard", description="Show the highest-XP members in this server")
    async def leaderboard_command(self, interaction: discord.Interaction):
        """Display the top 10 most active members in the current server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        top_10 = []
        if db.async_session:
            try:
                async with db.async_session() as session:
                    stmt = (
                        select(UserXP)
                        .where(UserXP.guild_id == interaction.guild.id, UserXP.xp > 0)
                        .order_by(UserXP.xp.desc())
                        .limit(10)
                    )
                    result = await session.execute(stmt)
                    db_records = result.scalars().all()
                    if db_records:
                        top_10 = [(r.user_id, r.xp, r.level) for r in db_records]
            except Exception as e:
                logging.error(f"Failed to query leaderboard from database: {e}")

        if not top_10:
            guild_users = self.guild_xp.get(interaction.guild.id, {})
            # Filter and sort only members belonging to this guild
            active_members = [
                (uid, data["xp"], data["level"])
                for uid, data in guild_users.items()
                if data.get("xp", 0) > 0
            ]
            active_members.sort(key=lambda x: x[1], reverse=True)
            top_10 = active_members[:10]

        server_name = interaction.guild.name
        server_icon = interaction.guild.icon.url if interaction.guild.icon else None

        if not top_10:
            embed = discord.Embed(
                title="🏆 Server Leaderboard",
                description="No experience recorded in this server yet.\n\n*Chat in text channels to earn XP!*",
                color=PRIMARY_COLOR,
            )
        else:
            lines = ["Top active members ranked by experience:\n"]
            for idx, (uid, xp, level) in enumerate(top_10, start=1):
                medal = MEDALS.get(idx, f"`{idx}.`")
                member = interaction.guild.get_member(uid)
                name = member.mention if member else f"User `{uid}`"
                lines.append(f"{medal} **{name}** — Level {level} • `{xp:,} XP`")

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
        """Display detailed XP breakdown and progress to the next milestone."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        target = user or interaction.user
        user_data = await self.get_or_fetch_user_data(interaction.guild.id, target.id)
        xp = user_data["xp"]
        level = user_data["level"]

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
        """Add experience points to a member in this server."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        user_data = await self.get_or_fetch_user_data(interaction.guild.id, user.id)
        user_data["xp"] += amount
        user_data["level"] = calculate_level(user_data["xp"])
        user_data["last_xp"] = time.time()
        new_xp = user_data["xp"]
        new_level = user_data["level"]
        await self._persist_user_xp(interaction.guild.id, user.id, new_xp, new_level)

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
        """Remove experience points from a member without dropping below 0."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("Amount must be greater than zero.", ephemeral=True)
            return

        user_data = await self.get_or_fetch_user_data(interaction.guild.id, user.id)
        user_data["xp"] = max(0, user_data["xp"] - amount)
        user_data["level"] = calculate_level(user_data["xp"])
        user_data["last_xp"] = time.time()
        new_xp = user_data["xp"]
        new_level = user_data["level"]
        await self._persist_user_xp(interaction.guild.id, user.id, new_xp, new_level)

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
        """Set a member's experience points directly."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if amount < 0:
            await interaction.response.send_message("XP amount cannot be negative.", ephemeral=True)
            return

        user_data = await self.get_or_fetch_user_data(interaction.guild.id, user.id)
        user_data["xp"] = amount
        user_data["level"] = calculate_level(user_data["xp"])
        user_data["last_xp"] = time.time()
        new_xp = user_data["xp"]
        new_level = user_data["level"]
        await self._persist_user_xp(interaction.guild.id, user.id, new_xp, new_level)

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