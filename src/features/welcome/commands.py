import json
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="welcome", description="Show the welcome message")
    async def welcome_command(self, interaction: discord.Interaction):
        with open(Path(__file__).parent / "embed.json", encoding="utf-8") as file:
            data = json.load(file)

        data = data["embeds"][0]
        channels = {}

        for channel in interaction.guild.text_channels:
            channels[channel.name] = channel.mention

        data["description"] = data.get("description", "").format(**channels)

        embed = discord.Embed.from_dict(data)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))