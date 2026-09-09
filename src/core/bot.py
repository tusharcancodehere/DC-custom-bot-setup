import logging
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands

from core.config import load_environment
from database.database import close_db, init_db

load_environment()

COMMAND_PREFIX = "!"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
EXTENSIONS = [
    "features.admin.commands",
    "features.welcome.commands",
    "features.levels.commands",
    "features.general.commands",
    "features.ai.commands",
    "features.moderation.commands",
    "features.music.commands",
    "features.tickets.commands",
    "features.games.commands",
]

# Load Opus for voice support if available
if not discord.opus.is_loaded():
    try:
        discord.opus.load_opus("libopus.so.0")
    except Exception:
        pass

# Hosting-friendly logging: stdout by default, optional file logging
handlers = [logging.StreamHandler(sys.stdout)]
try:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    handlers.append(logging.FileHandler(log_dir / "bot.log"))
except Exception as log_error:
    print(f"File logging unavailable: {log_error}")

logging.basicConfig(level=logging.INFO, format=LOG_FORMAT, handlers=handlers)

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix=COMMAND_PREFIX, intents=intents, application_id=int(os.getenv("APPLICATION_ID")))
        self.token = os.getenv("DISCORD_TOKEN")
        self._synced = False
        self.health_server = None
        self._register_prefix_commands()

    def _register_prefix_commands(self):
        @self.command(name="shutdown")
        @commands.is_owner()
        async def shutdown(ctx: commands.Context):
            logging.info(f"Shutdown requested by {ctx.author}")
            await ctx.send("Shutting down...")
            await self.close()

        @shutdown.error
        async def shutdown_error(ctx: commands.Context, error: commands.CommandError):
            if isinstance(error, commands.NotOwner):
                await ctx.send("❌ Only the bot owner can use this command.")
            else:
                logging.error(f"Error in shutdown command: {error}", exc_info=error)

    async def setup_hook(self):
        await init_db()
        print("Loading features...")
        logging.info("Loading features...")
        for extension in EXTENSIONS:
            await self.load_extension(extension)
        logging.info("Features loaded")

    async def on_ready(self):
        if not self._synced:
            commands = self.tree.get_commands()
            cmd_names = ", ".join(cmd.name for cmd in commands)
            logging.info(f"Loaded commands: {cmd_names}")
            print(f"Loaded commands: {cmd_names}")
            synced = await self.tree.sync()
            self._synced = True
            logging.info(f"Globally synced {len(synced)} commands")
            print(f"Globally synced {len(synced)} commands")

        logging.info(f"Logged in as {self.user}")
        print(f"Logged in as {self.user}")
        logging.info("Bot is ready.")
        print("Bot is ready.")

    async def close(self):
        logging.info("Shutting down bot...")
        if hasattr(self, "health_server") and self.health_server is not None:
            try:
                await self.health_server.stop()
            except Exception as e:
                logging.error(f"Error stopping health server: {e}", exc_info=e)
        for voice_client in self.voice_clients:
            try:
                await voice_client.disconnect(force=True)
            except Exception:
                pass
        await close_db()
        await super().close()