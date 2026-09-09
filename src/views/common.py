import discord

PRIMARY_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
MUSIC_COLOR = 0x9B59B6


def create_embed(
    title: str,
    description: str,
    color: int = PRIMARY_COLOR,
    footer: str | None = None,
    thumbnail: str | None = None,
) -> discord.Embed:
    """Build a standard, consistent Discord embed."""
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    if footer:
        embed.set_footer(text=footer)
    embed.timestamp = discord.utils.utcnow()
    return embed


def success_embed(title: str, description: str, footer: str | None = None) -> discord.Embed:
    """Standard green success embed."""
    return create_embed(title, description, color=SUCCESS_COLOR, footer=footer)


def error_embed(title: str, description: str, footer: str | None = None) -> discord.Embed:
    """Standard red error embed."""
    return create_embed(title, description, color=ERROR_COLOR, footer=footer)


def warning_embed(title: str, description: str, footer: str | None = None) -> discord.Embed:
    """Standard yellow warning embed."""
    return create_embed(title, description, color=WARNING_COLOR, footer=footer)


def info_embed(title: str, description: str, footer: str | None = None) -> discord.Embed:
    """Standard blurple info embed."""
    return create_embed(title, description, color=PRIMARY_COLOR, footer=footer)


class PaginatorView(discord.ui.View):
    """Reusable, interactive pagination view with Prev/Next buttons."""

    def __init__(
        self,
        pages: list[discord.Embed],
        author_id: int | None = None,
        timeout: float = 120.0,
    ):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.author_id = author_id
        self.current_page = 0
        self.message: discord.Message | None = None
        self._update_buttons()

    def _update_buttons(self):
        total = len(self.pages)
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= total - 1
        self.page_indicator.label = f"{self.current_page + 1} / {max(1, total)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the command author can use these navigation controls.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.secondary, disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self._update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass
