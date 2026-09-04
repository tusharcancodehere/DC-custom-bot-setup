import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(filename="logs/bot.log", level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents, application_id=int(os.getenv("APPLICATION_ID")))
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
        await self.load_extension("features.welcome.commands")
        await self.load_extension("features.levels.commands")
        await self.load_extension("features.general.commands")
        await self.load_extension("features.ai.commands")
        await self.load_extension("features.moderation.commands")
        logging.info("Features loaded")

    async def on_ready(self):
        guild = discord.Object(id=self.server_id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        logging.info(f"Logged in as {self.user}")
        logging.info(f"Synced {len(synced)} commands")
        print(f"Logged in as {self.user}")
        print(f"Synced {len(synced)} commands")