import asyncio
import discord
from discord import app_commands
from discord.ext import commands


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="level", description="Show the level of a user")
    async def level_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("This is a placeholder for the level command.")

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


if __name__ == "__main__":
    from core.bot import CustomBot

    async def main():
        bot = CustomBot()
        await bot.load_extension("features.levels.commands")
        await bot.start(bot.token)

    asyncio.run(main())