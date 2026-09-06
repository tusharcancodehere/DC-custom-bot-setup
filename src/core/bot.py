import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

COMMAND_PREFIX = "!"
LOG_FILE = "logs/bot.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
EXTENSIONS = [
    "features.welcome.commands",
    "features.levels.commands",
    "features.general.commands",
    "features.ai.commands",
    "features.moderation.commands",
    "features.music.commands",
]

# Load Opus for voice support if available
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus("libopus.so.0")
    except Exception:
        pass

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format=LOG_FORMAT)

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents, application_id=int(os.getenv("APPLICATION_ID")))
        self.token = os.getenv("DISCORD_TOKEN")
        self.server_id = int(os.getenv("SERVER_ID"))

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        logging.info(f"Shutdown requested by {ctx.author}")
        await ctx.send("Shutting down...")
        await self.close()

    async def setup_hook(self):
        logging.info("Loading features...")
        for extension in EXTENSIONS:
            await self.load_extension(extension)
        logging.info("Features loaded")

    async def on_ready(self):
        guild = discord.Object(id=self.server_id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        logging.info(f"Logged in as {self.user}")
        logging.info(f"Synced {len(synced)} commands")
        print(f"Logged in as {self.user}")
        print(f"Synced {len(synced)} commands")