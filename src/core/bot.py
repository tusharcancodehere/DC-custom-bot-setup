import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents
        )

        self.token = os.getenv("DISCORD_TOKEN")

        if not self.token:
            raise RuntimeError("DISCORD_TOKEN is missing from .env")

    async def on_ready(self):
        print(f"Logged in as {self.user}")