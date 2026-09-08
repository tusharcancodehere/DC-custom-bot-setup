import asyncio
import logging
import os
from pathlib import Path
import random
import shutil

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_VOLUME = 1.0
MIN_VOLUME = 0
MAX_VOLUME = 100
MUSIC_COLOR = 0x9B59B6
RANDOM_SEARCH_GENRES = [
    "lofi hip hop beats",
    "synthwave chill",
    "jazz classics instrumental",
    "ambient relaxing soundscape",
    "acoustic guitar chill",
    "classic rock hits",
    "piano instrumental melody",
    "electronic dance hits",
    "indie rock classics",
    "deep house chill",
]

class MusicPlayerView(discord.ui.View):
    def __init__(self, music, guild_id):
        super().__init__(timeout=None)
        self.music = music
        self.guild_id = guild_id

    def get_voice(self):
        guild = self.music.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    async def _respond(self, interaction: discord.Interaction, message: str):
        """Send button response safely, handling expired or pre-acknowledged tokens."""
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message(message, ephemeral=True)
            except discord.NotFound:
                pass
        else:
            try:
                await interaction.followup.send(message, ephemeral=True)
            except discord.NotFound:
                pass

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await self._respond(interaction, "I'm not in a voice channel.")
            return

        if voice.is_paused():
            voice.resume()
            await self._respond(interaction, "▶️ Resumed.")
        elif voice.is_playing():
            voice.pause()
            await self._respond(interaction, "⏸️ Paused.")
        else:
            await self._respond(interaction, "Nothing is playing.")

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice or not voice.is_playing():
            await self._respond(interaction, "Nothing is playing.")
            return

        voice.stop()
        await self._respond(interaction, "⏭️ Skipped.")

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await self._respond(interaction, "I'm not in a voice channel.")
            return

        queue = self.music.get_queue(self.guild_id)
        queue.clear()
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await self._respond(interaction, "⏹️ Stopped and cleared the queue.")
        await self.music.update_player(self.guild_id)

    @discord.ui.button(emoji="🔁", label="24/7", style=discord.ButtonStyle.success)
    async def toggle_247(self, interaction: discord.Interaction, button: discord.ui.Button):
        enabled = not self.music.always_on.get(self.guild_id, False)
        self.music.always_on[self.guild_id] = enabled
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await self._respond(interaction, f"🔁 24/7 mode **{'enabled' if enabled else 'disabled'}**.")
        await self.music.update_player(self.guild_id, self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.secondary)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await self._respond(interaction, "I'm not in a voice channel.")
            return

        queue = self.music.get_queue(self.guild_id)
        queue.clear()
        self.music.current.pop(self.guild_id, None)
        self.music.always_on[self.guild_id] = False
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        # Send response before awaiting disconnect to prevent 10062 Unknown interaction
        await self._respond(interaction, "👋 Left the voice channel.")
        await voice.disconnect()
        await self.music.update_player(self.guild_id)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.volumes = {}
        self.always_on = {}
        self.current = {}
        self.player_messages = {}
        self.player_views = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def is_247(self, guild_id):
        return self.always_on.get(guild_id, False)

    async def download_song(self, query):
        os.makedirs(CACHE_DIR, exist_ok=True)

        search = query if query.startswith(("http://", "https://")) else f"ytsearch1:{query}"
        options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(CACHE_DIR, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "opus",
                "preferredquality": "192"
            }]
        }

        def download():
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(search, download=True)
                if "entries" in info:
                    info = next((entry for entry in info["entries"] if entry), None)

                if not info:
                    raise RuntimeError("No video found.")

                title = info.get("title", "Unknown")
                source = ydl.prepare_filename(info)
                output = os.path.splitext(source)[0] + ".opus"

                if not os.path.isfile(output):
                    raise FileNotFoundError(f"Downloaded audio not found: {output}")

                return {
                    "title": title,
                    "file": output,
                    "duration": info.get("duration", 0),
                    "thumbnail": info.get("thumbnail"),
                    "url": info.get("webpage_url")
                }

        # Run yt-dlp in a worker thread so downloading does not block the Discord event loop.
        return await asyncio.to_thread(download)

    def format_duration(self, seconds):
        if not seconds:
            return "Unknown"

        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    def format_extraction_error(self, error: Exception) -> str:
        """Translate yt-dlp technical errors into clean, user-friendly messages."""
        msg = str(error).lower()
        if "confirm your age" in msg or "sign in to confirm" in msg or ("age" in msg and "restricted" in msg):
            return "⚠️ This video is age-restricted and cannot be played without authentication."
        if "private video" in msg:
            return "⚠️ This video is private and cannot be played."
        if "unavailable" in msg or "not available" in msg:
            return "⚠️ This video is unavailable or region-restricted."
        if "copyright" in msg:
            return "⚠️ This audio is unavailable due to copyright restrictions."
        if "no video found" in msg or "no results" in msg:
            return "❌ No matching video found for that query."
        return "❌ Could not stream the requested audio track. Please try a different song or URL."

    def build_embed(self, guild_id):
        song = self.current.get(guild_id)
        queue = self.get_queue(guild_id)
        status_247 = "✅ Enabled" if self.is_247(guild_id) else "❌ Disabled"

        embed = discord.Embed(title="🎵 Now Playing", color=MUSIC_COLOR)
        if not song:
            embed.description = "Nothing is playing right now. Use `/play` to add music."
            embed.add_field(name="🔁 24/7 Mode", value=status_247, inline=True)
            embed.add_field(name="📜 Queue", value="0 tracks", inline=True)
            embed.set_footer(text="DC Music Player")
            embed.timestamp = discord.utils.utcnow()
            return embed

        embed.description = f"### [{song['title']}]({song.get('url')})"
        if song.get("thumbnail"):
            embed.set_thumbnail(url=song["thumbnail"])

        volume_pct = int(self.volumes.get(guild_id, DEFAULT_VOLUME) * 100)
        embed.add_field(name="⏱️ Duration", value=self.format_duration(song.get("duration")), inline=True)
        embed.add_field(name="🔊 Volume", value=f"{volume_pct}%", inline=True)
        embed.add_field(name="📜 Queue", value=f"{len(queue)} track{'s' if len(queue) != 1 else ''}", inline=True)
        embed.add_field(name="🔁 24/7 Mode", value=status_247, inline=True)

        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        if voice and voice.channel:
            embed.add_field(name="📡 Voice Channel", value=voice.channel.mention, inline=True)

        server_icon = guild.icon.url if guild and guild.icon else None
        if server_icon:
            embed.set_footer(text=f"{guild.name} • Music Player", icon_url=server_icon)
        elif guild:
            embed.set_footer(text=f"{guild.name} • Music Player")
        else:
            embed.set_footer(text="DC Music Player")

        embed.timestamp = discord.utils.utcnow()
        return embed

    async def update_player(self, guild_id, view=None):
        message = self.player_messages.get(guild_id)
        if not message:
            return

        if view is None:
            view = self.player_views.get(guild_id)

        try:
            await message.edit(embed=self.build_embed(guild_id), view=view)
        except (discord.NotFound, discord.HTTPException):
            self.player_messages.pop(guild_id, None)
            self.player_views.pop(guild_id, None)

    async def send_player(self, interaction, guild_id):
        old_message = self.player_messages.get(guild_id)
        if old_message:
            try:
                await old_message.edit(embed=self.build_embed(guild_id), view=self.player_views[guild_id])
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        view = MusicPlayerView(self, guild_id)
        message = await interaction.followup.send(embed=self.build_embed(guild_id), view=view, wait=True)

        self.player_messages[guild_id] = message
        self.player_views[guild_id] = view

    async def play_next(self, guild):
        queue = self.get_queue(guild.id)
        voice = guild.voice_client
        if not voice:
            return

        if not queue:
            self.current.pop(guild.id, None)
            if not self.current:
                await self.bot.change_presence(activity=None)
            if not self.is_247(guild.id):
                await voice.disconnect()
            await self.update_player(guild.id)
            return

        song = queue.pop(0)
        self.current[guild.id] = song

        if not os.path.isfile(song["file"]):
            print(f"Music file missing: {song['file']}")
            await self.play_next(guild)
            return

        try:
            audio = discord.FFmpegPCMAudio(song["file"], before_options="-nostdin", options="-vn")
            source = discord.PCMVolumeTransformer(audio, volume=self.volumes.get(guild.id, DEFAULT_VOLUME))

            def after(error):
                if error:
                    print(f"Music error: {error}")
                asyncio.run_coroutine_threadsafe(self.song_finished(guild, song["file"]), self.bot.loop)

            voice.play(source, after=after)
            await self.bot.change_presence(activity=discord.Game(name=f"🎵 {song['title']}"))
            print(f"Playing: {song['title']}")
            print(f"File: {song['file']}")
            await self.update_player(guild.id)

        except Exception as error:
            print(f"Playback error: {error}")
            if os.path.exists(song["file"]):
                try:
                    os.remove(song["file"])
                except OSError:
                    pass
            await self.play_next(guild)

    async def song_finished(self, guild, filepath):
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

        await self.play_next(guild)

    async def ensure_voice(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return None

        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return None

        await interaction.response.defer()

        channel = interaction.user.voice.channel
        voice = interaction.guild.voice_client

        try:
            if not voice:
                voice = await channel.connect()
            elif voice.channel != channel:
                await voice.move_to(channel)
            return voice
        except Exception as error:
            print(f"Voice error: {error}")
            await interaction.followup.send("I couldn't join the voice channel.")
            return None

    @app_commands.command(name="play", description="Play a song")
    async def play_command(self, interaction: discord.Interaction, query: str):
        if not shutil.which("ffmpeg"):
            await interaction.response.send_message("❌ FFmpeg was not found on PATH. Music commands cannot play audio.", ephemeral=True)
            return

        voice = await self.ensure_voice(interaction)
        if not voice:
            return

        try:
            song = await self.download_song(query)
        except Exception as error:
            logging.warning(f"Music download error for '{query}': {error}")
            await interaction.followup.send(self.format_extraction_error(error))
            return

        queue = self.get_queue(interaction.guild.id)
        queue.append(song)

        if voice.is_playing() or voice.is_paused():
            embed = discord.Embed(
                title="🎵 Added to Queue",
                description=f"**[{song['title']}]({song.get('url')})**",
                color=MUSIC_COLOR,
            )
            embed.add_field(name="⏱️ Duration", value=self.format_duration(song.get("duration")), inline=True)
            embed.add_field(name="📍 Position", value=f"#{len(queue)}", inline=True)
            if song.get("thumbnail"):
                embed.set_thumbnail(url=song["thumbnail"])
            await interaction.followup.send(embed=embed)
            await self.update_player(interaction.guild.id)
            return

        await self.play_next(interaction.guild)
        await self.send_player(interaction, interaction.guild.id)

    @app_commands.command(name="random", description="Play a random music track from the internet")
    async def random_command(self, interaction: discord.Interaction):
        if not shutil.which("ffmpeg"):
            await interaction.response.send_message("❌ FFmpeg was not found on PATH. Music commands cannot play audio.", ephemeral=True)
            return

        voice = await self.ensure_voice(interaction)
        if not voice:
            return

        genre = random.choice(RANDOM_SEARCH_GENRES)
        query = f"{genre} {random.randint(1, 50)}"

        try:
            song = await self.download_song(query)
        except Exception as error:
            logging.warning(f"Random music download error: {error}")
            await interaction.followup.send(self.format_extraction_error(error))
            return

        queue = self.get_queue(interaction.guild.id)
        queue.append(song)

        if voice.is_playing() or voice.is_paused():
            embed = discord.Embed(
                title="🎵 Added to Queue",
                description=f"Added random track to queue: **[{song['title']}]({song.get('url')})**",
                color=MUSIC_COLOR,
            )
            embed.add_field(name="⏱️ Duration", value=self.format_duration(song.get("duration")), inline=True)
            embed.add_field(name="📍 Position", value=f"#{len(queue)}", inline=True)
            if song.get("thumbnail"):
                embed.set_thumbnail(url=song["thumbnail"])
            await interaction.followup.send(embed=embed)
            await self.update_player(interaction.guild.id)
            return

        await self.play_next(interaction.guild)
        await interaction.followup.send(f"Playing random track: **[{song['title']}]({song.get('url')})**")
        await self.send_player(interaction, interaction.guild.id)

    @app_commands.command(name="player", description="Show the music player")
    async def player_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        await interaction.response.defer()
        await self.send_player(interaction, interaction.guild.id)

    @app_commands.command(name="247", description="Toggle 24/7 voice mode")
    async def always_on_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        enabled = not self.is_247(interaction.guild.id)
        self.always_on[interaction.guild.id] = enabled

        voice = interaction.guild.voice_client
        if not enabled and voice and not voice.is_playing() and not self.get_queue(interaction.guild.id):
            await voice.disconnect()

        await interaction.response.send_message(f"🔁 24/7 mode **{'enabled' if enabled else 'disabled'}**.", ephemeral=True)
        await self.update_player(interaction.guild.id)

    @app_commands.command(name="skip", description="Skip the current song")
    async def skip_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return

        voice.stop()
        await interaction.response.send_message("⏭️ Skipped.")

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return

        voice.pause()
        await interaction.response.send_message("⏸️ Paused.")

    @app_commands.command(name="resume", description="Resume the current song")
    async def resume_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice or not voice.is_paused():
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)
            return

        voice.resume()
        await interaction.response.send_message("▶️ Resumed.")

    @app_commands.command(name="stop", description="Stop music and clear the queue")
    async def stop_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)

        queue.clear()
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        self.current.pop(interaction.guild.id, None)
        await interaction.response.send_message("⏹️ Stopped and cleared the queue.")
        await self.update_player(interaction.guild.id)

    @app_commands.command(name="queue", description="Show the music queue")
    async def queue_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)
        current = self.current.get(interaction.guild.id)

        if not voice or (not current and not queue):
            embed = discord.Embed(title="🎶 Music Queue", description="The queue is currently empty.", color=MUSIC_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title="🎶 Music Queue", color=MUSIC_COLOR)
        lines = []

        if current:
            lines.append(f"**Now Playing:**\n▶️ [{current['title']}]({current.get('url')}) • `{self.format_duration(current.get('duration'))}`\n")

        if queue:
            lines.append("**Up Next:**")
            for index, song in enumerate(queue[:10], start=1):
                lines.append(f"`{index}.` [{song['title']}]({song.get('url')}) • `{self.format_duration(song.get('duration'))}`")

            if len(queue) > 10:
                lines.append(f"\n*...and {len(queue) - 10} more track(s)*")
        else:
            lines.append("*No more tracks in queue.*")

        embed.description = "\n".join(lines)
        status_247 = "Enabled" if self.is_247(interaction.guild.id) else "Disabled"
        embed.set_footer(text=f"{len(queue)} track{'s' if len(queue) != 1 else ''} queued • 24/7: {status_247}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="volume", description="Set the music volume")
    async def volume_command(self, interaction: discord.Interaction, volume: int):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        if not voice:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        if volume < MIN_VOLUME or volume > MAX_VOLUME:
            await interaction.response.send_message("Volume must be between 0 and 100.", ephemeral=True)
            return

        self.volumes[interaction.guild.id] = volume / 100
        if isinstance(voice.source, discord.PCMVolumeTransformer):
            voice.source.volume = volume / 100

        await interaction.response.send_message(f"🔊 Volume set to **{volume}%**.")

    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave_command(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        voice = interaction.guild.voice_client
        queue = self.get_queue(interaction.guild.id)

        if not voice:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        queue.clear()
        self.current.pop(interaction.guild.id, None)
        self.always_on[interaction.guild.id] = False

        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await voice.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.")
        await self.update_player(interaction.guild.id)

async def setup(bot):
    await bot.add_cog(Music(bot))


