import random
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

GAME_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C

MAGIC_8BALL_ANSWERS = [
    # Positive
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    # Neutral
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    # Negative
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very doubtful.",
]

TRIVIA_QUESTIONS = [
    {
        "question": "What is the capital city of Australia?",
        "options": ["Sydney", "Melbourne", "Canberra", "Brisbane"],
        "answer": 2,
    },
    {
        "question": "Which planet in our solar system is known as the Red Planet?",
        "options": ["Venus", "Mars", "Jupiter", "Mercury"],
        "answer": 1,
    },
    {
        "question": "Who created the Python programming language?",
        "options": ["Guido van Rossum", "Dennis Ritchie", "Bjarne Stroustrup", "Linus Torvalds"],
        "answer": 0,
    },
    {
        "question": "What is the largest ocean on Earth?",
        "options": ["Atlantic Ocean", "Indian Ocean", "Arctic Ocean", "Pacific Ocean"],
        "answer": 3,
    },
    {
        "question": "How many bits are in a single byte?",
        "options": ["4 bits", "8 bits", "16 bits", "32 bits"],
        "answer": 1,
    },
    {
        "question": "In Minecraft, which mineral is required along with obsidian and a book to craft an Enchanting Table?",
        "options": ["Gold", "Emerald", "Diamond", "Netherite"],
        "answer": 2,
    },
    {
        "question": "Which chemical element has the symbol 'Au'?",
        "options": ["Silver", "Gold", "Copper", "Aluminum"],
        "answer": 1,
    },
    {
        "question": "What year was the original Discord platform released?",
        "options": ["2013", "2015", "2017", "2019"],
        "answer": 1,
    },
]

class TriviaView(discord.ui.View):
    """Interactive four-option trivia button view."""
    def __init__(self, invoker: discord.Member | discord.User, question_data: dict):
        super().__init__(timeout=60)
        self.invoker = invoker
        self.question_data = question_data
        self.answered = False

        # Dynamically create buttons for each option
        labels = ["A", "B", "C", "D"]
        for idx, option in enumerate(question_data["options"]):
            button = discord.ui.Button(
                label=f"{labels[idx]}: {option}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"trivia_{idx}",
            )
            button.callback = self._make_callback(idx)
            self.add_item(button)

    def _make_callback(self, selected_idx: int):
        async def button_callback(interaction: discord.Interaction):
            if interaction.user.id != self.invoker.id:
                await interaction.response.send_message("❌ Only the player who started this trivia game can answer!", ephemeral=True)
                return

            if self.answered:
                await interaction.response.send_message("You have already answered this question.", ephemeral=True)
                return

            self.answered = True
            correct_idx = self.question_data["answer"]
            correct_text = self.question_data["options"][correct_idx]

            # Style buttons to indicate right and wrong answers
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
                    idx = int(item.custom_id.split("_")[1])
                    if idx == correct_idx:
                        item.style = discord.ButtonStyle.success
                    elif idx == selected_idx:
                        item.style = discord.ButtonStyle.danger

            if selected_idx == correct_idx:
                embed = discord.Embed(
                    title="🎉 Correct!",
                    description=f"Great job, {self.invoker.mention}! The correct answer was **{correct_text}**.",
                    color=SUCCESS_COLOR,
                )
            else:
                embed = discord.Embed(
                    title="❌ Incorrect",
                    description=f"Sorry, {self.invoker.mention}! The correct answer was **{correct_text}**.",
                    color=ERROR_COLOR,
                )
            embed.timestamp = discord.utils.utcnow()

            await interaction.response.edit_message(embed=embed, view=self)

        return button_callback

class Games(commands.Cog):
    """Fun server mini-games and interactive entertainment commands."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle command errors gracefully."""
        message = f"❌ An error occurred: `{error}`"
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    @app_commands.command(name="coinflip", description="Flip a coin")
    @app_commands.describe(guess="Optional guess: heads or tails")
    async def coinflip_command(self, interaction: discord.Interaction, guess: Literal["heads", "tails"] | None = None):
        """Flip a two-sided coin with optional prediction."""
        result = random.choice(["heads", "tails"])
        icon = "🪙"

        if guess:
            if guess.lower() == result:
                description = f"The coin landed on **{result.capitalize()}** {icon}!\n\n🎉 **You called it correctly!**"
                color = SUCCESS_COLOR
            else:
                description = f"The coin landed on **{result.capitalize()}** {icon}!\n\n❌ **Better luck next time!**"
                color = ERROR_COLOR
        else:
            description = f"The coin landed on **{result.capitalize()}** {icon}!"
            color = GAME_COLOR

        embed = discord.Embed(title="🪙 Coin Flip", description=description, color=color)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="roll", description="Roll dice (e.g. 6, 20, or standard 2d6 notation)")
    @app_commands.describe(dice="Number of sides (e.g. 20) or dice notation like 2d6 (defaults to 1d6)")
    async def roll_command(self, interaction: discord.Interaction, dice: str = "6"):
        """Roll one or more dice with optional dice notation."""
        dice_str = dice.strip().lower()

        try:
            if "d" in dice_str:
                parts = dice_str.split("d")
                num_dice = int(parts[0]) if parts[0] else 1
                sides = int(parts[1])
            else:
                num_dice = 1
                sides = int(dice_str)

            if num_dice < 1 or num_dice > 20:
                await interaction.response.send_message("❌ You can roll between 1 and 20 dice at a time.", ephemeral=True)
                return
            if sides < 2 or sides > 1000:
                await interaction.response.send_message("❌ Dice must have between 2 and 1,000 sides.", ephemeral=True)
                return

            rolls = [random.randint(1, sides) for _ in range(num_dice)]
            total = sum(rolls)

            if num_dice == 1:
                description = f"🎲 You rolled a **{total}** on a d{sides}!"
            else:
                rolls_text = ", ".join(str(r) for r in rolls)
                description = f"🎲 You rolled **{num_dice}d{sides}**:\n\n**Rolls:** `[{rolls_text}]`\n**Total:** **{total:,}**"

            embed = discord.Embed(title="🎲 Dice Roll", description=description, color=GAME_COLOR)
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message("❌ Invalid dice format. Use a number like `20` or notation like `2d6`.", ephemeral=True)

    @app_commands.command(name="8ball", description="Ask the Magic 8-Ball a yes/no question")
    @app_commands.describe(question="What question would you like to ask the 8-Ball?")
    async def eightball_command(self, interaction: discord.Interaction, question: str):
        """Classic Magic 8-Ball oracle for fun predictions."""
        answer = random.choice(MAGIC_8BALL_ANSWERS)

        embed = discord.Embed(title="🎱 Magic 8-Ball", color=GAME_COLOR)
        embed.add_field(name="❓ Question", value=question, inline=False)
        embed.add_field(name="🔮 Answer", value=f"*{answer}*", inline=False)
        embed.set_footer(text=f"Asked by {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="Play Rock, Paper, Scissors against the bot")
    @app_commands.describe(choice="Your move: rock, paper, or scissors")
    async def rps_command(self, interaction: discord.Interaction, choice: Literal["rock", "paper", "scissors"]):
        """Play a round of Rock, Paper, Scissors against the bot."""
        bot_choice = random.choice(["rock", "paper", "scissors"])
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        user_move = choice.lower()
        if user_move == bot_choice:
            result_text = "🤝 **It's a tie!**"
            color = WARNING_COLOR
        elif (
            (user_move == "rock" and bot_choice == "scissors")
            or (user_move == "paper" and bot_choice == "rock")
            or (user_move == "scissors" and bot_choice == "paper")
        ):
            result_text = "🎉 **You win!**"
            color = SUCCESS_COLOR
        else:
            result_text = "🤖 **Bot wins!**"
            color = ERROR_COLOR

        embed = discord.Embed(title="✂️ Rock, Paper, Scissors", description=result_text, color=color)
        embed.add_field(name="Your Choice", value=f"{emojis[user_move]} {user_move.capitalize()}", inline=True)
        embed.add_field(name="Bot's Choice", value=f"{emojis[bot_choice]} {bot_choice.capitalize()}", inline=True)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="trivia", description="Answer a random trivia question")
    async def trivia_command(self, interaction: discord.Interaction):
        """Interactive trivia game with button answers."""
        q_data = random.choice(TRIVIA_QUESTIONS)
        view = TriviaView(interaction.user, q_data)

        embed = discord.Embed(
            title="🧠 Trivia Challenge",
            description=f"### {q_data['question']}\n\nSelect your answer using the buttons below:",
            color=GAME_COLOR,
        )
        embed.set_footer(text=f"Player: {interaction.user.name} • 60s timer")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Games(bot))
