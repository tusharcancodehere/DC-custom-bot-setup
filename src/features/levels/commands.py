import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open(Path(__file__).parent / "embed.json", encoding="utf-8") as file:
            self.embed_data = json.load(file)

    @app_commands.command(name="level", description="Show the level of a user")
    async def level_command(self, interaction: discord.Interaction):
        data = json.loads(json.dumps(self.embed_data["embeds"][0]))
        data["title"] = data["title"].format(username=interaction.user.name)
        data["description"] = data["description"].format(
            username=interaction.user.name,
            level=0,
            xp=0,
            next_xp=100,
            rank=1,
            progress_bar="░░░░░░░░░░",
            next_level=1
        )
        if "author" in data:
            data["author"]["name"] = data["author"]["name"].format(server=interaction.guild.name)
            data["author"]["icon_url"] = interaction.guild.icon.url if interaction.guild.icon else None
        if "thumbnail" in data:
            data["thumbnail"]["url"] = interaction.user.display_avatar.url
        if "footer" in data:
            data["footer"]["text"] = data["footer"]["text"].format(next_level=1)
        embed = discord.Embed.from_dict(data)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Show the leaderboard")
    async def leaderboard_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a placeholder for the leaderboard command.")

    @app_commands.command(name="rank", description="Show the rank of a user")
    async def rank_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a placeholder for the rank command.")

    @app_commands.command(name="show_xp", description="Show the XP of a user")
    async def show_xp_command(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.send_message(f"{user.mention} has 0 XP.")

async def setup(bot):
    await bot.add_cog(Levels(bot))