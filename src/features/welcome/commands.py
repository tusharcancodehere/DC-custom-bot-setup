import asyncio
import json
from pathlib import Path

import discord
from discord.ext import commands


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load the welcome embed from embed.json.
        with open(Path(__file__).parent / "embed.json", encoding="utf-8") as file:
            self.embed_data = json.load(file)

    def channel_mention(self, guild, name):
        # Find a channel by name and turn it into a clickable mention.
        channel = discord.utils.get(guild.text_channels, name=name)
        return channel.mention if channel else f"#{name}"

    def create_embed(self, member):
        data = self.embed_data["embeds"][0]

        description = data.get("description", "").format(
            user=member.mention,
            username=member.name,
            server=member.guild.name,
            member_count=member.guild.member_count,
            rules=self.channel_mention(member.guild, "rules"),
            roles=self.channel_mention(member.guild, "roles"),
            announcements=self.channel_mention(member.guild, "announcements"),
            general=self.channel_mention(member.guild, "general"),
            support=self.channel_mention(member.guild, "support")
        )

        embed = discord.Embed(
            title=data.get("title"),
            description=description,
            color=data.get("color", 0)
        )

        author = data.get("author")
        if author:
            embed.set_author(
                name=author.get("name", ""),
                url=author.get("url"),
                icon_url=author.get("icon_url")
            )

        footer = data.get("footer")
        if footer:
            embed.set_footer(
                text=footer.get("text", ""),
                icon_url=footer.get("icon_url")
            )

        if data.get("timestamp"):
            embed.timestamp = discord.utils.parse_time(data["timestamp"])

        if data.get("thumbnail"):
            embed.set_thumbnail(url=data["thumbnail"]["url"])

        if data.get("image"):
            embed.set_image(url=data["image"]["url"])

        for field in data.get("fields", []):
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )

        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"{member} joined {member.guild.name}")

    @discord.app_commands.command(
        name="testwelcome",
        description="Test the welcome embed"
    )
    async def testwelcome(self, interaction):
        embed = self.create_embed(interaction.user)
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