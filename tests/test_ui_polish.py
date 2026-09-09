import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

import discord
from discord.ext import commands

from features.general.commands import General
from features.music.commands import Music, MusicControlView
from views.common import (
    ERROR_COLOR,
    PRIMARY_COLOR,
    SUCCESS_COLOR,
    WARNING_COLOR,
    PaginatorView,
    error_embed,
    info_embed,
    success_embed,
    warning_embed,
)


class TestCommonViews(unittest.TestCase):
    def test_embed_builders(self):
        """Test common embed builders produce consistent structure and colors."""
        s = success_embed("Success Title", "Success Desc", footer="Footer")
        self.assertEqual(s.title, "Success Title")
        self.assertEqual(s.description, "Success Desc")
        self.assertEqual(s.color.value, SUCCESS_COLOR)
        self.assertEqual(s.footer.text, "Footer")
        self.assertIsNotNone(s.timestamp)

        e = error_embed("Error Title", "Error Desc")
        self.assertEqual(e.color.value, ERROR_COLOR)

        w = warning_embed("Warning Title", "Warning Desc")
        self.assertEqual(w.color.value, WARNING_COLOR)

        i = info_embed("Info Title", "Info Desc")
        self.assertEqual(i.color.value, PRIMARY_COLOR)

    def test_paginator_view_controls(self):
        """Test PaginatorView button states and page bounds."""
        pages = [
            discord.Embed(title="Page 1"),
            discord.Embed(title="Page 2"),
            discord.Embed(title="Page 3"),
        ]
        view = PaginatorView(pages, author_id=123)

        # On initial page 0: prev is disabled, next is enabled
        self.assertTrue(view.prev_button.disabled)
        self.assertFalse(view.next_button.disabled)
        self.assertEqual(view.page_indicator.label, "1 / 3")

        # Advance to page 1
        view.current_page = 1
        view._update_buttons()
        self.assertFalse(view.prev_button.disabled)
        self.assertFalse(view.next_button.disabled)
        self.assertEqual(view.page_indicator.label, "2 / 3")

        # Advance to last page (page 2)
        view.current_page = 2
        view._update_buttons()
        self.assertFalse(view.prev_button.disabled)
        self.assertTrue(view.next_button.disabled)
        self.assertEqual(view.page_indicator.label, "3 / 3")


class TestGeneralUIPolish(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock(spec=commands.Bot)
        self.bot.latency = 0.042
        self.cog = General(self.bot)

    async def test_ping_embed_structure(self):
        """Test /ping outputs a standardized embed with latency."""
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response = AsyncMock()

        await self.cog.ping.callback(self.cog, interaction)
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("Pong!", embed.title)
        self.assertIn("42ms", embed.fields[0].value)


class TestMusicUIPolish(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock(spec=commands.Bot)
        self.bot.user = MagicMock(id=9999)
        self.bot.loop = asyncio.get_event_loop()
        self.cog = Music(self.bot)

    def tearDown(self):
        self.cog.cog_unload()

    def test_music_control_view_initialization(self):
        """Test MusicControlView initializes with pause, skip, stop, and queue buttons."""
        guild = MagicMock(spec=discord.Guild)
        voice = MagicMock(spec=discord.VoiceClient)
        voice.is_paused.return_value = False
        guild.voice_client = voice
        self.bot.get_guild.return_value = guild

        view = MusicControlView(self.cog, guild_id=123)
        labels = [btn.label for btn in view.children if hasattr(btn, "label")]
        self.assertIn("Pause", labels)
        self.assertIn("Skip", labels)
        self.assertIn("Stop", labels)
        self.assertIn("Queue", labels)

    async def test_queue_pagination_with_many_tracks(self):
        """Test /queue generates pagination when tracks exceed 10."""
        guild_id = 987654
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.guild = MagicMock(spec=discord.Guild, id=guild_id)
        interaction.user = MagicMock(id=111)
        interaction.response = AsyncMock()

        self.cog.current[guild_id] = {
            "title": "Currently Playing Track",
            "url": "https://youtube.com/current",
            "duration": 200,
        }
        # Add 15 queued tracks
        queue = self.cog.get_queue(guild_id)
        for i in range(1, 16):
            queue.append({
                "title": f"Queued Track #{i}",
                "url": f"https://youtube.com/track_{i}",
                "duration": 180,
            })

        await self.cog.queue_command.callback(self.cog, interaction)
        interaction.response.send_message.assert_called_once()
        kwargs = interaction.response.send_message.call_args[1]
        self.assertIn("view", kwargs)
        self.assertIsInstance(kwargs["view"], PaginatorView)
        self.assertEqual(len(kwargs["view"].pages), 2)
        # Page 1 contains track 1, Page 2 contains track 15
        self.assertIn("Queued Track #1", kwargs["view"].pages[0].description)
        self.assertIn("Queued Track #15", kwargs["view"].pages[1].description)


if __name__ == "__main__":
    unittest.main()
