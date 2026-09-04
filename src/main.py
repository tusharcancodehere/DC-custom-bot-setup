import json
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = os.getenv("SERVER_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing from .env")

if not SERVER_ID:
    raise RuntimeError("SERVER_ID is missing from .env")

# Load the welcome embed JSON.
with open("src/features/welcome/embed.json", "r", encoding="utf-8") as file:
    welcome_data = json.load(file)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

server = discord.Object(id=int(SERVER_ID))


# Build a Discord embed from embed.json.
def create_welcome_embed(member):
    data = welcome_data["embeds"][0]

    embed = discord.Embed(
        title=data.get("title"),
        description=data.get("description", "").format(
            user=member.mention,
            username=member.name,
            server=member.guild.name,
            member_count=member.guild.member_count
        ),
        color=data.get("color", 0)
    )

    if "url" in data:
        embed.url = data["url"]

    if "footer" in data:
        embed.set_footer(
            text=data["footer"].get("text", "").format(
                user=member.name,
                server=member.guild.name,
                member_count=member.guild.member_count
            )
        )

    if "thumbnail" in data:
        embed.set_thumbnail(url=data["thumbnail"]["url"])

    if "image" in data:
        embed.set_image(url=data["image"]["url"])

    if "author" in data:
        embed.set_author(
            name=data["author"].get("name", ""),
            url=data["author"].get("url"),
            icon_url=data["author"].get("icon_url")
        )

    for field in data.get("fields", []):
        embed.add_field(
            name=field.get("name", ""),
            value=field.get("value", ""),
            inline=field.get("inline", False)
        )

    return embed


# /ping
@tree.command(
    name="ping",
    description="Check if the bot is online",
    guild=server
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")


# /testwelcome
@tree.command(
    name="testwelcome",
    description="Test the welcome embed",
    guild=server
)
async def testwelcome(interaction: discord.Interaction):
    embed = create_welcome_embed(interaction.user)

    await interaction.response.send_message(embed=embed)


# Runs automatically when a member joins.
@bot.event
async def on_member_join(member: discord.Member):
    print(f"{member} joined {member.guild.name}")


# Runs when the bot successfully connects to Discord.
@bot.event
async def on_ready():
    await tree.sync(guild=server)

    print(f"Logged in as {bot.user}")
    print(f"Synced commands to server {SERVER_ID}")


bot.run(TOKEN)