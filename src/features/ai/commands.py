import os
import discord
from discord import app_commands
from discord.ext import commands
from openai import AsyncOpenAI
from google import genai

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
        self.conversations = {}
        self.system_prompt = "Be extremely concise and direct. Answer only what is asked. Use the fewest words possible while remaining clear and correct. No filler, repetition, greetings, or unnecessary explanation."

    @app_commands.command(name="ask", description="Ask the AI something")
    async def ask_command(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()

        user_id = interaction.user.id

        if user_id not in self.conversations:
            self.conversations[user_id] = []

        self.conversations[user_id].append({"role": "user", "content": prompt})

        try:
            if not self.openai:
                raise RuntimeError

            response = await self.openai.responses.create(model="gpt-5-mini", instructions=self.system_prompt, input=self.conversations[user_id])

            if response.output_text:
                self.conversations[user_id].append({"role": "assistant", "content": response.output_text})
                await interaction.followup.send(response.output_text)
                return
        except Exception:
            pass

        try:
            if not self.gemini:
                raise RuntimeError

            response = self.gemini.models.generate_content(model="gemini-2.5-flash", contents=self.system_prompt + "\n\n" + prompt)

            if response.text:
                self.conversations[user_id].append({"role": "assistant", "content": response.text})
                await interaction.followup.send(response.text)
                return
        except Exception:
            pass

        self.conversations[user_id].pop()
        await interaction.followup.send("Both AI providers failed to respond.")

    @app_commands.command(name="clear", description="Clear your AI conversation")
    async def clear_command(self, interaction: discord.Interaction):
        self.conversations.pop(interaction.user.id, None)
        await interaction.response.send_message("Your AI conversation has been cleared.")

async def setup(bot):
    await bot.add_cog(AI(bot))