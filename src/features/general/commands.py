import discord
from discord import app_commands
from discord.ext import commands

PRIMARY_COLOR = 0x5865F2

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Check if the bot is online")
    async def ping(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(title="🏓 Pong!", color=PRIMARY_COLOR)
        embed.add_field(name="📡 Latency", value=f"`{latency_ms}ms`", inline=True)
        embed.add_field(name="🟢 Status", value="Operational", inline=True)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))