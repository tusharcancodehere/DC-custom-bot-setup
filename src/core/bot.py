import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database.database import init_db

load_dotenv(".env.local")
load_dotenv(".env")

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
        self._synced = False

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
        logging.info(f"Shutdown requested by {ctx.author}")
        await ctx.send("Shutting down...")
        await self.close()

    async def setup_hook(self):
        try:
            await init_db()
        except Exception as error:
            logging.error(f"Database initialization error: {error}")

        logging.info("Loading features...")
        for extension in EXTENSIONS:
            await self.load_extension(extension)
        logging.info("Features loaded")

    async def on_ready(self):
        if not self._synced:
            local_commands = [cmd.name for cmd in self.tree.get_commands()]
            logging.info(f"Local commands before sync ({len(local_commands)}): {', '.join(local_commands)}")
            print(f"Local commands before sync ({len(local_commands)}): {', '.join(local_commands)}")
            synced = await self.tree.sync()
            self._synced = True
            synced_names = [cmd.name for cmd in synced]
            logging.info(f"Global sync result names: {', '.join(synced_names)}")
            print(f"Global sync result names: {', '.join(synced_names)}")
            logging.info(f"Globally synced {len(synced)} commands")
            print(f"Globally synced {len(synced)} commands")

        logging.info(f"Logged in as {self.user}")
        print(f"Logged in as {self.user}")