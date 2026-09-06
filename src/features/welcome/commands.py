import json
from collections import defaultdict
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

EMBED_FILE = Path(__file__).parent / "embed.json"
PRIMARY_COLOR = 0x5865F2

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def resolve_channels(self, guild: discord.Guild) -> dict:
        channels = {channel.name.lower(): channel.mention for channel in guild.text_channels}

        def find_channel(keyword: str, fallback: str) -> str:
            for name, mention in channels.items():
                if keyword in name:
                    return mention
            return fallback

        resolved = defaultdict(lambda: "#channel")
        resolved.update(channels)
        resolved["rules"] = find_channel("rule", "#rules")
        resolved["roles"] = find_channel("role", "#roles")
        resolved["announcements"] = find_channel("announc", find_channel("news", "#announcements"))
        resolved["general"] = find_channel("general", find_channel("chat", "#general"))
        resolved["support"] = find_channel("support", find_channel("ticket", "#support"))
        return resolved

    @app_commands.command(name="welcome", description="Show the welcome message")
    async def welcome_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        with open(EMBED_FILE, encoding="utf-8") as file:
            raw_data = json.load(file)

        guild = interaction.guild
        data = raw_data["embeds"][0].copy()
        channel_map = self.resolve_channels(guild)

        title = data.get("title", "Welcome").format(server=guild.name)
        description = data.get("description", "").format_map(channel_map)
        server_icon = guild.icon.url if guild.icon else None

        embed = discord.Embed(title=title, description=description, color=data.get("color", PRIMARY_COLOR))
        embed.timestamp = discord.utils.utcnow()

        if server_icon:
            embed.set_thumbnail(url=server_icon)
            embed.set_footer(text=f"{guild.name} • Welcome", icon_url=server_icon)
        else:
            embed.set_footer(text=f"{guild.name} • Welcome")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Welcome(bot))