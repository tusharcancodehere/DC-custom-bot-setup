import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands
from google import genai
from openai import AsyncOpenAI

from views.common import ERROR_COLOR, SUCCESS_COLOR

SYSTEM_PROMPT = (
    "Be extremely concise and direct. Answer only what is asked. "
    "Use the fewest words possible while remaining clear and correct. "
    "No filler, repetition, greetings, or unnecessary explanation."
)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_HISTORY_MESSAGES = 20
MAX_DISCORD_MESSAGE_LENGTH = 1900

class AI(commands.Cog):
    """Conversational AI assistant with primary OpenAI and fallback Gemini support."""

    def __init__(self, bot):
        self.bot = bot
        self.openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None
        self.gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) if os.getenv("GEMINI_API_KEY") else None
        self.conversations: dict[tuple[int | None, int], list[dict]] = {}

    async def send_long_message(self, interaction: discord.Interaction, text: str):
        """Send message safely to Discord, splitting into chunks if longer than character limit."""
        if len(text) <= MAX_DISCORD_MESSAGE_LENGTH:
            await interaction.followup.send(text)
            return

        while text:
            if len(text) <= MAX_DISCORD_MESSAGE_LENGTH:
                await interaction.followup.send(text)
                break

            split_at = text.rfind("\n", 0, MAX_DISCORD_MESSAGE_LENGTH)
            if split_at == -1:
                split_at = text.rfind(" ", 0, MAX_DISCORD_MESSAGE_LENGTH)
            if split_at == -1:
                split_at = MAX_DISCORD_MESSAGE_LENGTH

            chunk = text[:split_at].strip()
            if chunk:
                await interaction.followup.send(chunk)
            text = text[split_at:].strip()

    @app_commands.command(name="ask", description="Ask the AI assistant a question")
    @app_commands.describe(prompt="What would you like to ask?")
    async def ask_command(self, interaction: discord.Interaction, prompt: str):
        """Ask the conversational AI assistant with automatic provider fallback."""
        await interaction.response.defer()

        guild_id = interaction.guild.id if interaction.guild else None
        key = (guild_id, interaction.user.id)
        if key not in self.conversations:
            self.conversations[key] = []

        self.conversations[key].append({"role": "user", "content": prompt})

        # Trim conversation to prevent exceeding context bounds
        if len(self.conversations[key]) > MAX_HISTORY_MESSAGES:
            self.conversations[key] = self.conversations[key][-MAX_HISTORY_MESSAGES:]

        # 1. Try Primary Provider: OpenAI
        try:
            if not self.openai:
                raise RuntimeError("OPENAI_API_KEY is not configured")

            output = None
            try:
                # Responses API for gpt-5-mini
                response = await self.openai.responses.create(
                    model=OPENAI_MODEL,
                    instructions=SYSTEM_PROMPT,
                    input=self.conversations[key],
                )
                output = getattr(response, "output_text", None)
            except Exception:
                # Standard Chat Completions fallback
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + self.conversations[key]
                chat_resp = await self.openai.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                )
                output = chat_resp.choices[0].message.content

            if output:
                self.conversations[key].append({"role": "assistant", "content": output})
                await self.send_long_message(interaction, output)
                return
        except Exception as openai_error:
            logging.warning(f"OpenAI error: {openai_error}. Trying Gemini fallback...")

        # 2. Try Fallback Provider: Google Gemini
        try:
            if not self.gemini:
                raise RuntimeError("GEMINI_API_KEY is not configured")

            dialogue = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in self.conversations[key])
            gemini_prompt = f"{SYSTEM_PROMPT}\n\n{dialogue}\nAssistant:"

            # Run synchronous SDK call in thread pool to avoid blocking Discord event loop
            response = await asyncio.to_thread(
                self.gemini.models.generate_content,
                model=GEMINI_MODEL,
                contents=gemini_prompt,
            )
            output = getattr(response, "text", None)
            if output:
                self.conversations[key].append({"role": "assistant", "content": output})
                await self.send_long_message(interaction, output)
                return
        except Exception as gemini_error:
            logging.warning(f"Gemini error: {gemini_error}")

        # Remove failed user prompt so broken queries don't poison history
        self.conversations[key].pop()
        embed = discord.Embed(
            title="❌ AI Temporarily Unavailable",
            description="The AI assistant is temporarily unavailable. Please try again in a moment.",
            color=ERROR_COLOR,
        )
        embed.set_footer(text="DC AI Assistant")
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle AI command errors without leaking internal technical details."""
        logging.error(f"AI command error: {error}", exc_info=True)
        message = "❌ An error occurred while processing your request. Please try again in a moment."
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            try:
                await interaction.followup.send(message, ephemeral=True)
            except Exception:
                pass

    @app_commands.command(name="clear", description="Clear your personal AI conversation history")
    async def clear_command(self, interaction: discord.Interaction):
        """Reset conversation history for the current server."""
        guild_id = interaction.guild.id if interaction.guild else None
        key = (guild_id, interaction.user.id)
        if key in self.conversations:
            del self.conversations[key]
            desc = "Your conversation history in this server has been reset."
        else:
            desc = "You do not have any active conversation history to reset."

        embed = discord.Embed(title="🧹 Conversation Cleared", description=desc, color=SUCCESS_COLOR)
        embed.set_footer(text="DC AI Assistant")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AI(bot))