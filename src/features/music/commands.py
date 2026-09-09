import asyncio
import logging
import os
from pathlib import Path
import shutil
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

from views.common import MUSIC_COLOR, PaginatorView

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"

YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def is_youtube_url(url: str) -> bool:
    """Validate whether the given string is a valid YouTube or YouTube Music URL."""
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        return hostname in YOUTUBE_DOMAINS or hostname.endswith(".youtube.com")
    except Exception:
        return False


def format_duration(seconds: int | float | None) -> str:
    """Format duration in seconds into H:MM:SS or M:SS string."""
    if not seconds:
        return "Live / Unknown"
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def create_now_playing_embed(track: dict, queue_len: int) -> discord.Embed:
    """Build a clean, polished Now Playing embed."""
    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"### [{track['title']}]({track['url']})",
        color=MUSIC_COLOR,
    )
    if track.get("thumbnail"):
        embed.set_thumbnail(url=track["thumbnail"])

    uploader = track.get("uploader") or "Unknown Artist"
    duration = format_duration(track.get("duration"))

    embed.add_field(name="Channel / Artist", value=uploader, inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)

    if queue_len > 0:
        queue_status = f"{queue_len} track{'s' if queue_len != 1 else ''} queued"
    else:
        queue_status = "Queue is empty"
    embed.add_field(name="Queue Status", value=queue_status, inline=True)

    embed.set_footer(text="DC Music Player • Use controls below to manage playback")
    embed.timestamp = discord.utils.utcnow()
    return embed


def create_added_to_queue_embed(track: dict, position: int) -> discord.Embed:
    """Build an Added to Queue embed."""
    embed = discord.Embed(
        title="🎵 Added to Queue",
        description=f"**[{track['title']}]({track['url']})**",
        color=MUSIC_COLOR,
    )
    if track.get("thumbnail"):
        embed.set_thumbnail(url=track["thumbnail"])

    uploader = track.get("uploader") or "Unknown Artist"
    duration = format_duration(track.get("duration"))

    embed.add_field(name="Channel / Artist", value=uploader, inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)
    embed.add_field(name="Position in Queue", value=f"#{position}", inline=True)
    embed.set_footer(text="DC Music Player")
    embed.timestamp = discord.utils.utcnow()
    return embed


def create_playlist_added_embed(playlist_title: str, count: int, url: str) -> discord.Embed:
    """Build a Playlist Added to Queue embed."""
    embed = discord.Embed(
        title="🎶 Playlist Added to Queue",
        description=f"Added **{count}** tracks from [{playlist_title}]({url}) to the queue.",
        color=MUSIC_COLOR,
    )
    embed.set_footer(text="DC Music Player")
    embed.timestamp = discord.utils.utcnow()
    return embed


class MusicControlView(discord.ui.View):
    """Interactive audio controls attached to the Now Playing embed."""

    def __init__(self, music_cog: "Music", guild_id: int):
        super().__init__(timeout=None)
        self.music = music_cog
        self.guild_id = guild_id
        self._sync_state()

    def _sync_state(self):
        guild = self.music.bot.get_guild(self.guild_id)
        voice = guild.voice_client if guild else None
        if voice and voice.is_paused():
            self.pause_resume_btn.label = "Resume"
            self.pause_resume_btn.emoji = "▶️"
            self.pause_resume_btn.style = discord.ButtonStyle.success
        else:
            self.pause_resume_btn.label = "Pause"
            self.pause_resume_btn.emoji = "⏸️"
            self.pause_resume_btn.style = discord.ButtonStyle.secondary

    async def _check_user_voice(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You must be in a voice channel to use music controls.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Pause", emoji="⏸️", style=discord.ButtonStyle.secondary)
    async def pause_resume_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        guild = self.music.bot.get_guild(self.guild_id)
        voice = guild.voice_client if guild else None
        if not voice:
            await interaction.response.send_message("❌ I'm not connected to a voice channel.", ephemeral=True)
            return

        if voice.is_paused():
            voice.resume()
            button.label = "Pause"
            button.emoji = "⏸️"
            button.style = discord.ButtonStyle.secondary
            await interaction.response.edit_message(view=self)
        elif voice.is_playing():
            voice.pause()
            button.label = "Resume"
            button.emoji = "▶️"
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        guild = self.music.bot.get_guild(self.guild_id)
        voice = guild.voice_client if guild else None
        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        voice.stop()
        await interaction.response.send_message("⏭️ Skipped current track.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        guild = self.music.bot.get_guild(self.guild_id)
        voice = guild.voice_client if guild else None
        queue = self.music.get_queue(self.guild_id)
        queue.clear()
        self.music.current.pop(self.guild_id, None)

        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        for item in self.children:
            item.disabled = True

        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            pass
        await interaction.followup.send("⏹️ Playback stopped and queue cleared.", ephemeral=True)

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        current = self.music.current.get(self.guild_id)
        queue = self.music.get_queue(self.guild_id)
        pages = self.music._build_queue_pages(current, queue)

        if not pages:
            embed = discord.Embed(
                title="🎶 Music Queue",
                description="The queue is currently empty. Use `/play <url>` to add music!",
                color=MUSIC_COLOR,
            )
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0], ephemeral=True)
        else:
            view = PaginatorView(pages, author_id=interaction.user.id)
            await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.queues: dict[int, list[dict]] = {}
        self.current: dict[int, dict] = {}
        self.text_channels: dict[int, discord.abc.Messageable] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._clean_legacy_cache()

    def _clean_legacy_cache(self):
        """Remove any leftover audio cache files from previous versions."""
        try:
            if CACHE_DIR.exists():
                for item in CACHE_DIR.glob("*.opus"):
                    try:
                        item.unlink(missing_ok=True)
                    except OSError:
                        pass
        except Exception as e:
            logger.debug(f"Cache cleanup notice: {e}")

    def cog_unload(self):
        """Clean up queues and active data when cog is unloaded."""
        for queue in self.queues.values():
            queue.clear()
        self.current.clear()
        self.text_channels.clear()
        self._locks.clear()

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle music command errors with friendly feedback."""
        logger.error(f"Music command error: {error}", exc_info=True)
        message = f"❌ An error occurred while processing the command: `{error}`"
        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            try:
                await interaction.followup.send(message, ephemeral=True)
            except Exception:
                pass

    def get_queue(self, guild_id: int) -> list[dict]:
        """Get or initialize the queue for a specific guild."""
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def get_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or initialize the lock for a specific guild to prevent simultaneous playback starts."""
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Clean up guild queue if the bot is disconnected from voice."""
        if self.bot.user and member.id == self.bot.user.id and before.channel and not after.channel:
            guild_id = member.guild.id
            queue = self.get_queue(guild_id)
            queue.clear()
            self.current.pop(guild_id, None)
            self.text_channels.pop(guild_id, None)

    def _format_error(self, error: Exception) -> str:
        """Translate technical yt-dlp errors into clean, user-friendly messages."""
        msg = str(error).lower()
        if (
            "confirm you're not a bot" in msg
            or "sign in to confirm" in msg
            or "bot detection" in msg
            or "po token" in msg
            or "botguard" in msg
            or "automated queries" in msg
        ):
            return "YouTube blocked playback due to bot-detection on the host server. Skipping to next track..."
        if "confirm your age" in msg or ("age" in msg and "restricted" in msg):
            return "This video is age-restricted and cannot be played without authentication."
        if "private video" in msg:
            return "This video is private and cannot be played."
        if "unavailable" in msg or "not available" in msg:
            return "This video is unavailable or region-restricted."
        if "copyright" in msg:
            return "This audio is unavailable due to copyright restrictions."
        if "does not exist" in msg:
            return "The requested video or playlist does not exist."
        return "Could not stream the requested track. Please try a different URL."

    def _get_extractor_args(self) -> dict:
        """Configure extractor arguments including player clients and optional PO Token Provider URL."""
        args: dict = {
            "youtube": {
                "player_client": ["mweb", "web_music", "web_embedded", "android", "ios"],
            }
        }
        pot_url = os.getenv("POT_PROVIDER_URL") or os.getenv("YOUTUBE_POT_PROVIDER_URL")
        if pot_url and pot_url.strip():
            args["youtubepot-bgutilhttp"] = {"base_url": [pot_url.strip()]}
        return args

    def _extract_info(self, url: str) -> dict:
        """Extract metadata for video or playlist using flat extraction."""
        opts = {
            "extract_flat": "in_playlist",
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "playlistend": 100,
            "extractor_args": self._get_extractor_args(),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _get_stream_info(self, url: str) -> tuple[str | None, dict]:
        """Extract direct audio stream URL and metadata for playback."""
        opts = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "extractor_args": self._get_extractor_args(),
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]
            stream_url = info.get("url")
            if not stream_url and "formats" in info:
                audio_formats = [f for f in info["formats"] if f.get("acodec") != "none" and f.get("url")]
                if audio_formats:
                    stream_url = audio_formats[-1]["url"]
            return stream_url, info

    def _build_queue_pages(self, current: dict | None, queue: list[dict]) -> list[discord.Embed]:
        """Build paginated embeds for the current music queue."""
        if not current and not queue:
            return []

        PAGE_SIZE = 10
        total_tracks = len(queue)
        total_pages = max(1, (total_tracks + PAGE_SIZE - 1) // PAGE_SIZE) if total_tracks else 1
        pages = []

        for page_idx in range(total_pages):
            embed = discord.Embed(title="🎶 Music Queue", color=MUSIC_COLOR)
            lines = []
            if current:
                lines.append(
                    f"**Now Playing:**\n▶️ [{current['title']}]({current['url']}) • `{format_duration(current.get('duration'))}`\n"
                )

            if queue:
                lines.append("**Up Next:**")
                start = page_idx * PAGE_SIZE
                end = start + PAGE_SIZE
                for idx, track in enumerate(queue[start:end], start=start + 1):
                    lines.append(f"`{idx}.` [{track['title']}]({track['url']}) • `{format_duration(track.get('duration'))}`")
            else:
                lines.append("*No more tracks in queue.*")

            embed.description = "\n".join(lines)
            if total_pages > 1:
                embed.set_footer(
                    text=f"Page {page_idx + 1} of {total_pages} • Total: {total_tracks} track{'s' if total_tracks != 1 else ''} queued"
                )
            else:
                embed.set_footer(text=f"Total: {total_tracks} track{'s' if total_tracks != 1 else ''} in queue")
            embed.timestamp = discord.utils.utcnow()
            pages.append(embed)

        return pages

    async def _send_now_playing_embed(
        self,
        guild_id: int,
        embed: discord.Embed,
        initial_interaction: discord.Interaction | None = None,
    ):
        """Send the Now Playing embed to the interaction followup or guild text channel with interactive controls."""
        view = MusicControlView(self, guild_id)
        if initial_interaction and not initial_interaction.is_expired():
            try:
                await initial_interaction.followup.send(embed=embed, view=view)
                return
            except (discord.NotFound, discord.HTTPException) as e:
                logger.debug(f"Interaction followup send failed: {e}")

        channel = self.text_channels.get(guild_id)
        if channel:
            try:
                await channel.send(embed=embed, view=view)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Could not send Now Playing embed to channel: {e}")

    async def play_next(self, guild_id: int, initial_interaction: discord.Interaction | None = None):
        """Play the next track from the guild queue. Uses asyncio.Lock to prevent races."""
        lock = self.get_lock(guild_id)
        async with lock:
            guild = self.bot.get_guild(guild_id)
            if not guild or not guild.voice_client:
                return

            voice = guild.voice_client
            if voice.is_playing() or voice.is_paused():
                return

            queue = self.get_queue(guild_id)
            if not queue:
                self.current.pop(guild_id, None)
                try:
                    if not any(self.current.values()):
                        await self.bot.change_presence(activity=None)
                except Exception:
                    pass
                return

            track = queue.pop(0)
            self.current[guild_id] = track

            # Extract direct stream URL just-in-time
            try:
                stream_url, detailed_info = await asyncio.to_thread(self._get_stream_info, track["url"])
                if detailed_info:
                    track["title"] = detailed_info.get("title") or track["title"]
                    track["uploader"] = detailed_info.get("uploader") or track["uploader"]
                    track["duration"] = detailed_info.get("duration") or track["duration"]
                    if detailed_info.get("thumbnail"):
                        track["thumbnail"] = detailed_info.get("thumbnail")
            except Exception as e:
                logger.warning(f"Failed to stream track '{track['title']}': {e}")
                err_msg = f"⚠️ Could not stream **{track['title']}**: {self._format_error(e)}"
                if initial_interaction and not initial_interaction.is_expired():
                    try:
                        await initial_interaction.followup.send(err_msg)
                    except Exception:
                        pass
                else:
                    channel = self.text_channels.get(guild_id)
                    if channel:
                        try:
                            await channel.send(err_msg)
                        except Exception:
                            pass
                asyncio.create_task(self.play_next(guild_id))
                return

            if not stream_url:
                logger.warning(f"No stream URL found for '{track['title']}'. Skipping...")
                no_stream_msg = f"⚠️ Could not extract audio stream for **{track['title']}**. Skipping..."
                if initial_interaction and not initial_interaction.is_expired():
                    try:
                        await initial_interaction.followup.send(no_stream_msg)
                    except Exception:
                        pass
                else:
                    channel = self.text_channels.get(guild_id)
                    if channel:
                        try:
                            await channel.send(no_stream_msg)
                        except Exception:
                            pass
                asyncio.create_task(self.play_next(guild_id))
                return

            try:
                source = discord.FFmpegPCMAudio(
                    stream_url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
                    options="-vn",
                )

                def after_playing(error):
                    if error:
                        logger.error(f"Playback error in guild {guild_id}: {error}")
                    asyncio.run_coroutine_threadsafe(self.play_next(guild_id), self.bot.loop)

                voice.play(source, after=after_playing)

                try:
                    await self.bot.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.listening,
                            name=track["title"][:120],
                        )
                    )
                except Exception:
                    pass

            except Exception as e:
                logger.error(f"Failed to start voice playback in guild {guild_id}: {e}")
                play_err_msg = f"⚠️ Failed to play audio for **{track['title']}**. Skipping..."
                if initial_interaction and not initial_interaction.is_expired():
                    try:
                        await initial_interaction.followup.send(play_err_msg)
                    except Exception:
                        pass
                else:
                    channel = self.text_channels.get(guild_id)
                    if channel:
                        try:
                            await channel.send(play_err_msg)
                        except Exception:
                            pass
                asyncio.create_task(self.play_next(guild_id))
                return

            embed = create_now_playing_embed(track, len(queue))
            await self._send_now_playing_embed(guild_id, embed, initial_interaction)

    @app_commands.command(name="play", description="Play a YouTube or YouTube Music video or playlist")
    @app_commands.describe(url="YouTube or YouTube Music video or playlist URL")
    async def play_command(self, interaction: discord.Interaction, url: str):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        clean_url = url.strip()
        if not is_youtube_url(clean_url):
            await interaction.response.send_message(
                "❌ Please provide a valid YouTube or YouTube Music URL (e.g. `https://www.youtube.com/watch?v=...` or `https://music.youtube.com/...`).",
                ephemeral=True,
            )
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return

        user_voice = interaction.user.voice.channel
        bot_member = interaction.guild.me or interaction.guild.get_member(self.bot.user.id)
        if bot_member:
            perms = user_voice.permissions_for(bot_member)
            if not perms.connect or not perms.speak:
                await interaction.response.send_message(
                    "❌ I do not have permission to connect to or speak in your voice channel.",
                    ephemeral=True,
                )
                return

        if not shutil.which("ffmpeg"):
            await interaction.response.send_message(
                "❌ FFmpeg was not found on PATH. Audio cannot be streamed.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        voice = interaction.guild.voice_client
        try:
            if not voice:
                voice = await user_voice.connect()
            elif voice.channel != user_voice:
                await voice.move_to(user_voice)
        except Exception as e:
            logger.error(f"Failed to connect to voice channel: {e}")
            await interaction.followup.send("❌ Could not connect to your voice channel. Please check channel permissions.")
            return

        self.text_channels[interaction.guild.id] = interaction.channel

        try:
            info = await asyncio.to_thread(self._extract_info, clean_url)
        except Exception as e:
            logger.warning(f"Extraction error for '{clean_url}': {e}")
            await interaction.followup.send(f"❌ {self._format_error(e)}")
            return

        guild_id = interaction.guild.id
        queue = self.get_queue(guild_id)

        # Handle playlists
        if info.get("_type") == "playlist" or ("entries" in info and info["entries"] is not None):
            raw_entries = info.get("entries", [])
            tracks_to_add = []
            for entry in raw_entries:
                if not entry:
                    continue
                title = entry.get("title")
                if not title or title in ("[Private video]", "[Deleted video]"):
                    continue
                track_url = entry.get("webpage_url") or entry.get("url")
                if not track_url or not track_url.startswith("http"):
                    vid_id = entry.get("id")
                    if vid_id:
                        track_url = f"https://www.youtube.com/watch?v={vid_id}"
                    else:
                        continue

                thumb = entry.get("thumbnail")
                if not thumb and entry.get("thumbnails"):
                    thumb = entry["thumbnails"][-1].get("url")

                tracks_to_add.append({
                    "title": title,
                    "url": track_url,
                    "duration": entry.get("duration"),
                    "uploader": entry.get("uploader") or entry.get("channel") or "Unknown Artist",
                    "thumbnail": thumb,
                })

            if tracks_to_add:
                queue.extend(tracks_to_add)
                playlist_title = info.get("title") or "YouTube Playlist"
                await interaction.followup.send(
                    embed=create_playlist_added_embed(playlist_title, len(tracks_to_add), clean_url)
                )

                if not voice.is_playing() and not voice.is_paused():
                    await self.play_next(guild_id)
                return

        # Handle individual video
        track_url = info.get("webpage_url") or info.get("url") or clean_url
        thumb = info.get("thumbnail")
        if not thumb and info.get("thumbnails"):
            thumb = info["thumbnails"][-1].get("url")

        track = {
            "title": info.get("title") or "Unknown Title",
            "url": track_url,
            "duration": info.get("duration"),
            "uploader": info.get("uploader") or info.get("channel") or "Unknown Artist",
            "thumbnail": thumb,
        }

        queue.append(track)

        if voice.is_playing() or voice.is_paused():
            await interaction.followup.send(embed=create_added_to_queue_embed(track, len(queue)))
        else:
            await self.play_next(guild_id, initial_interaction=interaction)

    @app_commands.command(name="queue", description="Show the current music queue")
    async def queue_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        current = self.current.get(guild_id)
        queue = self.get_queue(guild_id)
        pages = self._build_queue_pages(current, queue)

        if not pages:
            embed = discord.Embed(
                title="🎶 Music Queue",
                description="The queue is currently empty. Use `/play <url>` to add music!",
                color=MUSIC_COLOR,
            )
            embed.timestamp = discord.utils.utcnow()
            await interaction.response.send_message(embed=embed)
            return

        if len(pages) == 1:
            await interaction.response.send_message(embed=pages[0])
        else:
            view = PaginatorView(pages, author_id=interaction.user.id)
            await interaction.response.send_message(embed=pages[0], view=view)

    @app_commands.command(name="skip", description="Skip the current track")
    async def skip_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        voice.stop()
        await interaction.response.send_message("⏭️ Skipped current track.")

    @app_commands.command(name="pause", description="Pause the current track")
    async def pause_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        if voice.is_paused():
            await interaction.response.send_message("⚠️ Playback is already paused.", ephemeral=True)
            return

        voice.pause()
        await interaction.response.send_message("⏸️ Paused playback.")

    @app_commands.command(name="resume", description="Resume playback")
    async def resume_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or (not voice.is_playing() and not voice.is_paused()):
            await interaction.response.send_message("❌ Nothing is currently playing.", ephemeral=True)
            return

        if not voice.is_paused():
            await interaction.response.send_message("⚠️ Playback is not paused.", ephemeral=True)
            return

        voice.resume()
        await interaction.response.send_message("▶️ Resumed playback.")

    @app_commands.command(name="stop", description="Stop playback and clear the queue")
    async def stop_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        queue = self.get_queue(guild_id)
        queue.clear()
        self.current.pop(guild_id, None)

        voice = interaction.guild.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        await interaction.response.send_message("⏹️ Stopped playback and cleared the queue.")

    @app_commands.command(name="leave", description="Disconnect from voice and clear the queue")
    async def leave_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        queue = self.get_queue(guild_id)
        queue.clear()
        self.current.pop(guild_id, None)
        self.text_channels.pop(guild_id, None)

        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message("❌ I'm not in a voice channel.", ephemeral=True)
            return

        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await voice.disconnect()
        await interaction.response.send_message("👋 Disconnected from the voice channel.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
