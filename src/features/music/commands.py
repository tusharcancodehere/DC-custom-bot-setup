import asyncio
import os

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

CACHE_DIR = os.path.abspath("src/features/music/cache")
DEFAULT_VOLUME = 1.0
MIN_VOLUME = 0
MAX_VOLUME = 100
MUSIC_COLOR = 0x9B59B6

class MusicPlayerView(discord.ui.View):
    def __init__(self, music, guild_id):
        super().__init__(timeout=None)
        self.music = music
        self.guild_id = guild_id

    def get_voice(self):
        guild = self.music.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        if voice.is_paused():
            voice.resume()
            await interaction.response.send_message("▶️ Resumed.", ephemeral=True)
        elif voice.is_playing():
            voice.pause()
            await interaction.response.send_message("⏸️ Paused.", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.primary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice or not voice.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return

        voice.stop()
        await interaction.response.send_message("⏭️ Skipped.", ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        queue = self.music.get_queue(self.guild_id)
        queue.clear()
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await interaction.response.send_message("⏹️ Stopped and cleared the queue.", ephemeral=True)
        await self.music.update_player(self.guild_id)

    @discord.ui.button(emoji="🔁", label="24/7", style=discord.ButtonStyle.success)
    async def toggle_247(self, interaction: discord.Interaction, button: discord.ui.Button):
        enabled = not self.music.always_on.get(self.guild_id, False)
        self.music.always_on[self.guild_id] = enabled
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.send_message(f"🔁 24/7 mode **{'enabled' if enabled else 'disabled'}**.", ephemeral=True)
        await self.music.update_player(self.guild_id, self)

    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.secondary)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        voice = self.get_voice()
        if not voice:
            await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
            return

        queue = self.music.get_queue(self.guild_id)
        queue.clear()
        self.music.always_on[self.guild_id] = False
        if voice.is_playing() or voice.is_paused():
            voice.stop()

        await voice.disconnect()
        await interaction.response.send_message("👋 Left the voice channel.", ephemeral=True)
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

    @app_commands.command(name="play", description="Play a song")
    async def play_command(self, interaction: discord.Interaction, query: str):
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        if not interaction.user.voice:
            await interaction.response.send_message("You must be in a voice channel.", ephemeral=True)
            return

        await interaction.response.defer()

        channel = interaction.user.voice.channel
        voice = interaction.guild.voice_client

        try:
            if not voice:
                voice = await channel.connect()
            elif voice.channel != channel:
                await voice.move_to(channel)
        except Exception as error:
            print(f"Voice error: {error}")
            await interaction.followup.send("I couldn't join the voice channel.")
            return

        try:
            song = await self.download_song(query)
        except Exception as error:
            print(f"Download error: {error}")
            await interaction.followup.send(f"Couldn't download the song: `{error}`")
            return

        queue = self.get_queue(interaction.guild.id)
        queue.append(song)

        if voice.is_playing():
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
        voice = interaction.guild.voice_client
        if not voice or not voice.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return

        voice.stop()
        await interaction.response.send_message("⏭️ Skipped.")

    @app_commands.command(name="pause", description="Pause the current song")
    async def pause_command(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_playing():
            await interaction.response.send_message("Nothing is playing.", ephemeral=True)
            return

        voice.pause()
        await interaction.response.send_message("⏸️ Paused.")

    @app_commands.command(name="resume", description="Resume the current song")
    async def resume_command(self, interaction: discord.Interaction):
        voice = interaction.guild.voice_client
        if not voice or not voice.is_paused():
            await interaction.response.send_message("Nothing is paused.", ephemeral=True)
            return

        voice.resume()
        await interaction.response.send_message("▶️ Resumed.")

    @app_commands.command(name="stop", description="Stop music and clear the queue")
    async def stop_command(self, interaction: discord.Interaction):
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
