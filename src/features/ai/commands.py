import os

import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from openai import AsyncOpenAI

SYSTEM_PROMPT = (
    "Be extremely concise and direct. Answer only what is asked. "
    "Use the fewest words possible while remaining clear and correct. "
    "No filler, repetition, greetings, or unnecessary explanation."
)
OPENAI_MODEL = "gpt-5-mini"
GEMINI_MODEL = "gemini-2.5-flash"

SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
        self.conversations = {}

    @app_commands.command(name="ask", description="Ask the AI something")
    async def ask_command(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        guild_id = interaction.guild.id if interaction.guild else None
        key = (guild_id, interaction.user.id)
        if key not in self.conversations:
            self.conversations[key] = []

        self.conversations[key].append({"role": "user", "content": prompt})

        try:
            if not self.openai:
                raise RuntimeError

            response = await self.openai.responses.create(model=OPENAI_MODEL, instructions=SYSTEM_PROMPT, input=self.conversations[key])
            if response.output_text:
                self.conversations[key].append({"role": "assistant", "content": response.output_text})
                await interaction.followup.send(response.output_text)
                return
        except Exception:
            pass

        try:
            if not self.gemini:
                raise RuntimeError

            response = self.gemini.models.generate_content(model=GEMINI_MODEL, contents=SYSTEM_PROMPT + "\n\n" + prompt)
            if response.text:
                self.conversations[key].append({"role": "assistant", "content": response.text})
                await interaction.followup.send(response.text)
                return
        except Exception:
            pass

        self.conversations[key].pop()
        embed = discord.Embed(
            title="❌ AI Temporarily Unavailable",
            description="Both AI providers failed to respond. Please verify API configuration or try again in a moment.",
            color=ERROR_COLOR,
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="clear", description="Clear your AI conversation")
    async def clear_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id if interaction.guild else None
        key = (guild_id, interaction.user.id)
        self.conversations.pop(key, None)
        embed = discord.Embed(
            title="🧹 Conversation Cleared",
            description="Your AI conversation history has been reset.",
            color=SUCCESS_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AI(bot))