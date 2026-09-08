import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from core.bot import CustomBot

class TestCogsLoading(unittest.IsolatedAsyncioTestCase):
    async def test_all_extensions_load(self):
        """Verify that all 9 feature cogs load into CustomBot without runtime errors."""
        with patch.dict(os.environ, {
            "APPLICATION_ID": "123456789012345678",
            "DISCORD_TOKEN": "mock_token_for_ci_test",
        }):
            with patch("core.bot.init_db", return_value=True):
                bot = CustomBot()
                await bot.setup_hook()

                expected_cogs = {
                    "Admin",
                    "Welcome",
                    "Levels",
                    "General",
                    "AI",
                    "Moderation",
                    "Music",
                    "Tickets",
                    "Games",
                }
                loaded_cogs = set(bot.cogs.keys())
                for cog_name in expected_cogs:
                    self.assertIn(cog_name, loaded_cogs, f"Cog {cog_name} was not loaded")

                # Verify each cog has registered app commands
                total_commands = sum(len(cog.get_app_commands()) for cog in bot.cogs.values())
                self.assertGreaterEqual(total_commands, 35)

                await bot.close()

if __name__ == "__main__":
    unittest.main()
