import asyncio
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

        embed = discord.Embed.from_dict(data["embeds"][0])

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))


if __name__ == "__main__":
    from core.bot import CustomBot

    async def main():
        bot = CustomBot()
        await bot.load_extension("features.welcome.commands")
        await bot.start(bot.token)

    asyncio.run(main())