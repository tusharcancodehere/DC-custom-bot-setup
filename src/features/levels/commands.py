import json
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

EMBED_FILE = Path(__file__).parent / "embed.json"
PRIMARY_COLOR = 0x5865F2
PROGRESS_BAR_LENGTH = 12

def create_progress_bar(current: int, total: int, length: int = PROGRESS_BAR_LENGTH) -> str:
    if total <= 0:
        return "░" * length
    filled = min(length, int((current / total) * length))
    return "█" * filled + "░" * (length - filled)

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open(EMBED_FILE, encoding="utf-8") as file:
            self.embed_data = json.load(file)

    def build_level_embed(self, user: discord.Member, guild: discord.Guild, level: int = 0, xp: int = 0, next_xp: int = 100, rank: int = 1) -> discord.Embed:
        percentage = round((xp / next_xp) * 100) if next_xp > 0 else 0
        progress_bar = create_progress_bar(xp, next_xp)

        data = self.embed_data["embeds"][0].copy()
        title = data.get("title", "⚡ {username}'s Level").format(username=user.name)
        description = data.get("description", "").format(
            rank=rank,
            level=level,
            xp=xp,
            next_xp=next_xp,
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

    @app_commands.command(name="level", description="Show the level of a user")
    async def level_command(self, interaction: discord.Interaction):
        embed = self.build_level_embed(interaction.user, interaction.guild)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rank", description="Show the rank of a user")
    async def rank_command(self, interaction: discord.Interaction):
        embed = self.build_level_embed(interaction.user, interaction.guild)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the leaderboard")
    async def leaderboard_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        server_name = guild.name if guild else "Server"
        server_icon = guild.icon.url if guild and guild.icon else None

        embed = discord.Embed(
            title="🏆 Server Leaderboard",
            description=(
                "Top active members ranked by experience:\n\n"
                "🥇 **Member** — Level 10 • `4,850 XP`\n"
                "🥈 **Member** — Level 8 • `3,200 XP`\n"
                "🥉 **Member** — Level 6 • `2,150 XP`\n"
                "`4.` **Member** — Level 5 • `1,600 XP`\n"
                "`5.` **Member** — Level 3 • `950 XP`\n\n"
                "*Chat in text channels to earn XP and level up!*"
            ),
            color=PRIMARY_COLOR,
        )
        embed.timestamp = discord.utils.utcnow()

        if server_icon:
            embed.set_thumbnail(url=server_icon)
            embed.set_footer(text=f"{server_name} • Leaderboard", icon_url=server_icon)
        else:
            embed.set_footer(text=f"{server_name} • Leaderboard")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="show_xp", description="Show the XP of a user")
    async def show_xp_command(self, interaction: discord.Interaction, user: discord.Member):
        guild = interaction.guild
        server_name = guild.name if guild else "Server"

        embed = discord.Embed(
            title=f"✨ {user.name}'s Experience",
            description=(
                f"👤 **Member:** {user.mention}\n"
                f"⭐ **Level:** `0`\n"
                f"✨ **XP:** `0 / 100 XP`\n"
                f"🎯 **Next Milestone:** Level 1\n\n"
                f"`{create_progress_bar(0, 100)}` 0%"
            ),
            color=PRIMARY_COLOR,
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"{server_name} • Level System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Levels(bot))