import asyncio
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord
from discord.ext import commands

from features.music.commands import (
    Music,
    create_added_to_queue_embed,
    create_now_playing_embed,
    create_playlist_added_embed,
    format_duration,
    is_youtube_url,
)


class TestMusicHelpers(unittest.TestCase):
    def test_youtube_url_validation(self):
        """Test URL validator for YouTube, YouTube Music, and invalid URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "http://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://music.youtube.com/playlist?list=PL12345",
            "https://www.youtube.com/playlist?list=PL12345",
            "https://youtube.com/watch?v=abc&list=xyz",
        ]
        for url in valid_urls:
            self.assertTrue(is_youtube_url(url), f"Expected '{url}' to be recognized as valid YouTube URL")

        invalid_urls = [
            "https://spotify.com/track/123",
            "https://soundcloud.com/user/track",
            "https://youtube.com.attacker.com/watch?v=123",
            "https://notyoutube.com/watch?v=123",
            "ftp://youtube.com/watch?v=123",
            "hello world",
            "",
            "https:///malformed",
        ]
        for url in invalid_urls:
            self.assertFalse(is_youtube_url(url), f"Expected '{url}' to be rejected as invalid YouTube URL")

    def test_format_duration(self):
        """Test duration formatting for various second counts."""
        self.assertEqual(format_duration(None), "Live / Unknown")
        self.assertEqual(format_duration(0), "Live / Unknown")
        self.assertEqual(format_duration(45), "0:45")
        self.assertEqual(format_duration(213), "3:33")
        self.assertEqual(format_duration(3600), "1:00:00")
        self.assertEqual(format_duration(3674), "1:01:14")

    def test_embed_creation(self):
        """Test Now Playing, Added to Queue, and Playlist embeds."""
        track = {
            "title": "Test Song",
            "url": "https://www.youtube.com/watch?v=123",
            "duration": 180,
            "uploader": "Test Artist",
            "thumbnail": "https://img.youtube.com/vi/123/hqdefault.jpg",
        }

        # Now Playing Embed
        np_embed = create_now_playing_embed(track, queue_len=2)
        self.assertEqual(np_embed.title, "🎵 Now Playing")
        self.assertIn("Test Song", np_embed.description)
        self.assertEqual(np_embed.fields[0].value, "Test Artist")
        self.assertEqual(np_embed.fields[1].value, "3:00")
        self.assertEqual(np_embed.fields[2].value, "2 tracks queued")

        # Now Playing Embed with empty queue
        np_empty = create_now_playing_embed(track, queue_len=0)
        self.assertEqual(np_empty.fields[2].value, "Queue is empty")

        # Added to Queue Embed
        add_embed = create_added_to_queue_embed(track, position=3)
        self.assertEqual(add_embed.title, "🎵 Added to Queue")
        self.assertEqual(add_embed.fields[2].value, "#3")

        # Playlist Added Embed
        pl_embed = create_playlist_added_embed("Awesome Mix", count=15, url="https://youtube.com/playlist?list=1")
        self.assertEqual(pl_embed.title, "🎶 Playlist Added to Queue")
        self.assertIn("15", pl_embed.description)

    def test_format_error_bot_detection(self):
        """Verify yt-dlp bot-detection errors are translated into clear bot-detection warnings."""
        bot_errors = [
            Exception("Sign in to confirm you're not a bot. This helps protect our community."),
            Exception("sign in to confirm you are not a bot"),
            Exception("WARNING: [youtube] mweb client https formats require a GVS PO Token which was not provided."),
            Exception("Sign in to confirm your identity or automated queries detected."),
            Exception("Botguard token challenge failed"),
        ]
        cog = Music(MagicMock())
        for err in bot_errors:
            msg = cog._format_error(err)
            self.assertIn("bot-detection", msg.lower())
            self.assertIn("skipping", msg.lower())

    def test_format_error_other_conditions(self):
        """Verify standard error translation for age-restriction, private, and copyright."""
        cog = Music(MagicMock())
        self.assertIn("age-restricted", cog._format_error(Exception("Confirm your age to view")).lower())
        self.assertIn("private", cog._format_error(Exception("This is a private video")).lower())
        self.assertIn("copyright", cog._format_error(Exception("Video blocked due to copyright")).lower())
        self.assertIn("does not exist", cog._format_error(Exception("Video does not exist")).lower())


class TestMusicCommands(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = MagicMock(spec=commands.Bot)
        self.bot.user = MagicMock()
        self.bot.user.id = 9999
        self.bot.loop = asyncio.get_event_loop()
        self.cog = Music(self.bot)

    def tearDown(self):
        self.cog.cog_unload()

    def _mock_interaction(self, in_server=True, in_voice=True, perms_ok=True):
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response = AsyncMock()
        interaction.followup = AsyncMock()
        interaction.is_expired = MagicMock(return_value=False)

        if in_server:
            guild = MagicMock(spec=discord.Guild)
            guild.id = 123456
            interaction.guild = guild
            interaction.channel = AsyncMock(spec=discord.TextChannel)

            # Bot member permissions
            bot_member = MagicMock(spec=discord.Member)
            guild.me = bot_member
            guild.get_member.return_value = bot_member

            # Voice client
            voice_client = MagicMock(spec=discord.VoiceClient)
            voice_client.is_playing.return_value = False
            voice_client.is_paused.return_value = False
            voice_client.move_to = AsyncMock()
            voice_client.disconnect = AsyncMock()
            guild.voice_client = voice_client
            self.bot.get_guild.return_value = guild

            # User voice
            if in_voice:
                user = MagicMock(spec=discord.Member)
                voice_channel = AsyncMock(spec=discord.VoiceChannel)
                perms = MagicMock()
                perms.connect = perms_ok
                perms.speak = perms_ok
                voice_channel.permissions_for.return_value = perms
                voice_channel.connect = AsyncMock(return_value=voice_client)
                user.voice = MagicMock(channel=voice_channel)
                interaction.user = user
                voice_client.channel = voice_channel
            else:
                user = MagicMock(spec=discord.Member)
                user.voice = None
                interaction.user = user
        else:
            interaction.guild = None

        return interaction

    async def test_command_registration(self):
        """Verify that exactly the 7 specified music commands are registered."""
        command_names = {cmd.name for cmd in self.cog.get_app_commands()}
        expected_commands = {"play", "queue", "skip", "pause", "resume", "stop", "leave"}
        self.assertEqual(command_names, expected_commands)

    async def test_play_rejects_invalid_url(self):
        """Verify /play rejects non-YouTube URLs with user-friendly error."""
        interaction = self._mock_interaction()
        await self.cog.play_command.callback(self.cog, interaction, "https://spotify.com/track/123")
        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        self.assertIn("valid YouTube or YouTube Music URL", args[0])

    async def test_play_requires_voice(self):
        """Verify /play rejects users not connected to a voice channel."""
        interaction = self._mock_interaction(in_voice=False)
        await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        self.assertIn("must be in a voice channel", args[0])

    async def test_play_checks_voice_permissions(self):
        """Verify /play checks bot connect and speak permissions in the target voice channel."""
        interaction = self._mock_interaction(perms_ok=False)
        await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        self.assertIn("do not have permission", args[0])

    @patch("shutil.which", return_value=None)
    async def test_play_ffmpeg_missing(self, mock_which):
        """Verify /play provides a friendly message if FFmpeg is missing."""
        interaction = self._mock_interaction()
        await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        interaction.response.send_message.assert_called_once()
        args, kwargs = interaction.response.send_message.call_args
        self.assertIn("FFmpeg was not found", args[0])

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_single_track_starts_immediately_when_idle(self, mock_which):
        """Verify single video starts playback immediately if nothing is playing."""
        interaction = self._mock_interaction()
        mock_info = {
            "title": "Never Gonna Give You Up",
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "duration": 213,
            "uploader": "Rick Astley",
            "thumbnail": "https://example.com/thumb.jpg",
        }

        with patch.object(self.cog, "_extract_info", return_value=mock_info):
            with patch.object(self.cog, "_get_stream_info", return_value=("https://stream.googlevideo.com/audio", mock_info)):
                with patch("discord.FFmpegPCMAudio") as mock_audio:
                    await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/watch?v=dQw4w9WgXcQ")

                    # Voice client should have been told to play
                    voice = interaction.guild.voice_client
                    voice.play.assert_called_once()
                    self.assertEqual(self.cog.current[interaction.guild.id]["title"], "Never Gonna Give You Up")

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_queues_when_already_playing(self, mock_which):
        """Verify track is added to queue without interrupting when already playing."""
        interaction = self._mock_interaction()
        voice = interaction.guild.voice_client
        voice.is_playing.return_value = True

        mock_info = {
            "title": "Song 2",
            "webpage_url": "https://www.youtube.com/watch?v=song2",
            "duration": 150,
            "uploader": "Artist 2",
            "thumbnail": None,
        }

        with patch.object(self.cog, "_extract_info", return_value=mock_info):
            await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/watch?v=song2")

            queue = self.cog.get_queue(interaction.guild.id)
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["title"], "Song 2")
            interaction.followup.send.assert_called_once()
            # Voice should not have called play again
            voice.play.assert_not_called()

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_playlist_adds_all_tracks(self, mock_which):
        """Verify playlist URLs add all tracks in order."""
        interaction = self._mock_interaction()
        mock_playlist = {
            "_type": "playlist",
            "title": "My Playlist",
            "entries": [
                {"title": "Track 1", "webpage_url": "https://www.youtube.com/watch?v=1", "duration": 100, "uploader": "A"},
                {"title": "[Private video]", "webpage_url": "https://www.youtube.com/watch?v=priv"},
                {"title": "Track 2", "webpage_url": "https://www.youtube.com/watch?v=2", "duration": 200, "uploader": "B"},
            ],
        }

        with patch.object(self.cog, "_extract_info", return_value=mock_playlist):
            with patch.object(self.cog, "play_next", new_callable=AsyncMock) as mock_play_next:
                await self.cog.play_command.callback(self.cog, interaction, "https://www.youtube.com/playlist?list=PL123")

                queue = self.cog.get_queue(interaction.guild.id)
                # Private video should be skipped, so 2 tracks remaining
                self.assertEqual(len(queue), 2)
                self.assertEqual(queue[0]["title"], "Track 1")
                self.assertEqual(queue[1]["title"], "Track 2")
                mock_play_next.assert_called_once_with(interaction.guild.id)

    async def test_queue_command_empty_and_populated(self):
        """Test /queue command with empty queue and with active tracks."""
        interaction = self._mock_interaction()

        # Empty queue
        await self.cog.queue_command.callback(self.cog, interaction)
        interaction.response.send_message.assert_called_once()
        embed = interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("empty", embed.description.lower())

        # Populated queue
        interaction.response.send_message.reset_mock()
        self.cog.current[interaction.guild.id] = {
            "title": "Now Playing Track",
            "url": "https://youtube.com/1",
            "duration": 180,
        }
        self.cog.get_queue(interaction.guild.id).append({
            "title": "Next Track",
            "url": "https://youtube.com/2",
            "duration": 240,
        })

        await self.cog.queue_command.callback(self.cog, interaction)
        embed = interaction.response.send_message.call_args[1]["embed"]
        self.assertIn("Now Playing Track", embed.description)
        self.assertIn("Next Track", embed.description)

    async def test_skip_command(self):
        """Test /skip command stops voice client to trigger the after callback."""
        interaction = self._mock_interaction()
        voice = interaction.guild.voice_client

        # Nothing playing
        await self.cog.skip_command.callback(self.cog, interaction)
        interaction.response.send_message.assert_called_with("❌ Nothing is currently playing.", ephemeral=True)

        # Playing
        voice.is_playing.return_value = True
        interaction.response.send_message.reset_mock()
        await self.cog.skip_command.callback(self.cog, interaction)
        voice.stop.assert_called_once()
        interaction.response.send_message.assert_called_with("⏭️ Skipped current track.")

    async def test_pause_and_resume_commands(self):
        """Test /pause and /resume commands."""
        interaction = self._mock_interaction()
        voice = interaction.guild.voice_client

        # Try to pause when nothing is playing
        await self.cog.pause_command.callback(self.cog, interaction)
        interaction.response.send_message.assert_called_with("❌ Nothing is currently playing.", ephemeral=True)

        # Pause when playing
        voice.is_playing.return_value = True
        voice.is_paused.return_value = False
        interaction.response.send_message.reset_mock()
        await self.cog.pause_command.callback(self.cog, interaction)
        voice.pause.assert_called_once()

        # Resume when paused
        voice.is_playing.return_value = False
        voice.is_paused.return_value = True
        interaction.response.send_message.reset_mock()
        await self.cog.resume_command.callback(self.cog, interaction)
        voice.resume.assert_called_once()

    async def test_stop_command(self):
        """Test /stop command clears queue and stops playback."""
        interaction = self._mock_interaction()
        voice = interaction.guild.voice_client
        voice.is_playing.return_value = True

        queue = self.cog.get_queue(interaction.guild.id)
        queue.append({"title": "Queued Track"})
        self.cog.current[interaction.guild.id] = {"title": "Current Track"}

        await self.cog.stop_command.callback(self.cog, interaction)
        self.assertEqual(len(queue), 0)
        self.assertNotIn(interaction.guild.id, self.cog.current)
        voice.stop.assert_called_once()

    async def test_leave_command(self):
        """Test /leave command disconnects bot and clears queue."""
        interaction = self._mock_interaction()
        voice = interaction.guild.voice_client

        queue = self.cog.get_queue(interaction.guild.id)
        queue.append({"title": "Queued Track"})

        await self.cog.leave_command.callback(self.cog, interaction)
        self.assertEqual(len(queue), 0)
        voice.disconnect.assert_called_once()

    async def test_per_guild_isolation(self):
        """Verify queue in Guild A does not affect Guild B."""
        queue_a = self.cog.get_queue(111)
        queue_b = self.cog.get_queue(222)

        queue_a.append({"title": "Song A"})
        self.assertEqual(len(queue_a), 1)
        self.assertEqual(len(queue_b), 0)

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_next_skips_bot_blocked_track_and_continues_queue(self, mock_which):
        """Verify that when a track triggers YouTube bot detection, play_next skips it and plays next track."""
        interaction = self._mock_interaction()
        guild_id = interaction.guild.id
        self.cog.text_channels[guild_id] = interaction.channel

        track_1 = {
            "title": "Blocked Track",
            "url": "https://www.youtube.com/watch?v=blocked",
            "duration": 180,
            "uploader": "Blocked Artist",
            "thumbnail": None,
        }
        track_2 = {
            "title": "Allowed Track",
            "url": "https://www.youtube.com/watch?v=allowed",
            "duration": 200,
            "uploader": "Allowed Artist",
            "thumbnail": None,
        }
        queue = self.cog.get_queue(guild_id)
        queue.extend([track_1, track_2])

        def fake_get_stream_info(url):
            if "blocked" in url:
                raise Exception("Sign in to confirm you're not a bot. This helps protect our community.")
            return "https://stream.googlevideo.com/audio2", track_2

        with patch.object(self.cog, "_get_stream_info", side_effect=fake_get_stream_info):
            with patch("discord.FFmpegPCMAudio"):
                await self.cog.play_next(guild_id, initial_interaction=interaction)
                await asyncio.sleep(0.05)

                interaction.followup.send.assert_called()
                call_args = interaction.followup.send.call_args[0][0]
                self.assertIn("Blocked Track", call_args)
                self.assertIn("bot-detection", call_args.lower())

                voice = interaction.guild.voice_client
                voice.play.assert_called_once()
                self.assertEqual(self.cog.current[guild_id]["title"], "Allowed Track")
                self.assertEqual(len(queue), 0)

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_next_skips_empty_stream_url_and_continues(self, mock_which):
        """Verify that when a track returns no direct audio stream, play_next skips it and plays next track."""
        interaction = self._mock_interaction()
        guild_id = interaction.guild.id
        self.cog.text_channels[guild_id] = interaction.channel

        track_1 = {"title": "No Stream Track", "url": "https://youtube.com/watch?v=nostream", "duration": 100, "uploader": "A", "thumbnail": None}
        track_2 = {"title": "Good Track", "url": "https://youtube.com/watch?v=good", "duration": 150, "uploader": "B", "thumbnail": None}
        queue = self.cog.get_queue(guild_id)
        queue.extend([track_1, track_2])

        def fake_get_stream_info(url):
            if "nostream" in url:
                return None, {}
            return "https://stream.googlevideo.com/good", track_2

        with patch.object(self.cog, "_get_stream_info", side_effect=fake_get_stream_info):
            with patch("discord.FFmpegPCMAudio"):
                await self.cog.play_next(guild_id, initial_interaction=interaction)
                await asyncio.sleep(0.05)

                interaction.followup.send.assert_called()
                call_args = interaction.followup.send.call_args[0][0]
                self.assertIn("No Stream Track", call_args)

                voice = interaction.guild.voice_client
                voice.play.assert_called_once()
                self.assertEqual(self.cog.current[guild_id]["title"], "Good Track")

    @patch("shutil.which", return_value="/usr/bin/ffmpeg")
    async def test_play_next_failed_extraction_does_not_set_current(self, mock_which):
        """Verify that when stream extraction fails, the track is not marked as currently playing."""
        interaction = self._mock_interaction()
        guild_id = interaction.guild.id
        self.cog.text_channels[guild_id] = interaction.channel

        track = {
            "title": "Failing Track",
            "url": "https://www.youtube.com/watch?v=fails",
            "duration": 180,
            "uploader": "Artist",
            "thumbnail": None,
        }
        queue = self.cog.get_queue(guild_id)
        queue.append(track)

        with patch.object(self.cog, "_get_stream_info", side_effect=Exception("Extraction error")):
            await self.cog.play_next(guild_id, initial_interaction=interaction)
            await asyncio.sleep(0.05)

            self.assertNotIn(guild_id, self.cog.current)
            self.assertEqual(len(queue), 0)
            interaction.guild.voice_client.play.assert_not_called()


if __name__ == "__main__":
    unittest.main()
