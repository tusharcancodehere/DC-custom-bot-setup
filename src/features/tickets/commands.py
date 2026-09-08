import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

TICKET_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245

class TicketLaunchView(discord.ui.View):
    """Persistent launch button panel for users to open support tickets."""
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Create Ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="create_ticket_btn")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.create_ticket_for_user(interaction)

class TicketControlView(discord.ui.View):
    """Control view placed inside an active ticket channel for closing and deleting."""
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.close_ticket_channel(interaction)

    @discord.ui.button(label="Delete Ticket", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="delete_ticket_btn")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.delete_ticket_channel(interaction)

class Tickets(commands.Cog):
    """Interactive support ticket system with private channels and staff controls."""

    def __init__(self, bot):
        self.bot = bot
        # Mapping: guild_id -> {channel_id: {"user_id": int, "closed": bool, "ticket_num": int}}
        self.active_tickets: dict[int, dict[int, dict]] = {}
        self.ticket_counters: dict[int, int] = {}

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle missing permissions gracefully with friendly feedback."""
        if isinstance(error, app_commands.MissingPermissions):
            message = "❌ You do not have permission to use this ticket command."
        else:
            message = f"❌ An error occurred: `{error}`"

        if not interaction.response.is_done():
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.followup.send(message, ephemeral=True)

    async def create_ticket_for_user(self, interaction: discord.Interaction):
        """Create a private ticket channel for the requesting user."""
        if not interaction.guild:
            await interaction.response.send_message("Tickets can only be created in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if guild_id not in self.active_tickets:
            self.active_tickets[guild_id] = {}

        # Prevent duplicate open tickets for the same user in this server
        for ch_id, t_info in self.active_tickets[guild_id].items():
            if t_info["user_id"] == interaction.user.id and not t_info["closed"]:
                existing_ch = interaction.guild.get_channel(ch_id)
                if existing_ch:
                    await interaction.response.send_message(f"❌ You already have an open ticket in {existing_ch.mention}.", ephemeral=True)
                    return

        await interaction.response.defer(ephemeral=True)

        num = self.ticket_counters.get(guild_id, 0) + 1
        self.ticket_counters[guild_id] = num

        # Channel permissions: hide from everyone, visible to ticket opener & bot
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True,
            ),
        }

        # Optional category detection
        category = discord.utils.find(
            lambda c: "ticket" in c.name.lower() or "support" in c.name.lower(),
            interaction.guild.categories,
        )

        clean_user_name = "".join(c for c in interaction.user.name if c.isalnum() or c in "-_").lower()
        channel_name = f"ticket-{num:04d}-{clean_user_name}"[:32]

        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category,
                reason=f"Ticket #{num} created by {interaction.user}",
            )
        except discord.Forbidden:
            await interaction.followup.send("❌ I lack permission to create ticket channels.", ephemeral=True)
            return

        self.active_tickets[guild_id][channel.id] = {
            "user_id": interaction.user.id,
            "closed": False,
            "ticket_num": num,
        }

        # Post initial greeting in the new ticket channel
        embed = discord.Embed(
            title=f"🎫 Support Ticket #{num:04d}",
            description=(
                f"Welcome {interaction.user.mention}!\n\n"
                "Please describe your question or issue in detail. A staff member will assist you shortly.\n\n"
                "Use the controls below when this ticket is ready to close."
            ),
            color=TICKET_COLOR,
        )
        embed.timestamp = discord.utils.utcnow()
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"{interaction.guild.name} • Ticket System")

        await channel.send(
            content=f"{interaction.user.mention} Your ticket has been opened.",
            embed=embed,
            view=TicketControlView(self),
        )

        await interaction.followup.send(f"✅ Your ticket has been created: {channel.mention}.", ephemeral=True)

    async def close_ticket_channel(self, interaction: discord.Interaction):
        """Close an active ticket channel, locking user chat permissions."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        ticket_info = self.active_tickets.get(guild_id, {}).get(interaction.channel.id)

        if not ticket_info:
            await interaction.response.send_message("❌ This channel is not an active ticket channel.", ephemeral=True)
            return

        if ticket_info["closed"]:
            await interaction.response.send_message("ℹ️ This ticket is already closed.", ephemeral=True)
            return

        ticket_info["closed"] = True

        # Restrict user from sending further messages
        member = interaction.guild.get_member(ticket_info["user_id"])
        if member:
            try:
                await interaction.channel.set_permissions(member, send_messages=False, view_channel=True)
            except discord.Forbidden:
                pass

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"This ticket was closed by {interaction.user.mention}.\nClick **Delete Ticket** to permanently remove this channel.",
            color=WARNING_COLOR,
        )
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    async def delete_ticket_channel(self, interaction: discord.Interaction):
        """Delete a ticket channel."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        guild_id = interaction.guild.id
        if guild_id in self.active_tickets:
            self.active_tickets[guild_id].pop(interaction.channel.id, None)

        await interaction.response.send_message("🗑️ Deleting ticket in 3 seconds...")
        await asyncio.sleep(3)
        try:
            await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")
        except (discord.NotFound, discord.Forbidden) as e:
            logging.warning(f"Could not delete ticket channel {interaction.channel.id}: {e}")

    @app_commands.command(name="ticket_panel", description="Post the interactive ticket creation panel")
    @app_commands.describe(channel="Target channel for ticket panel (defaults to current channel)")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ticket_panel_command(self, interaction: discord.Interaction, channel: discord.TextChannel | None = None):
        """Post the interactive ticket launch panel to a channel."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return

        target = channel or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("❌ Ticket panel can only be sent to text channels.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎫 Support Tickets",
            description=(
                "Need help, have an inquiry, or want to report an issue?\n\n"
                "Click the **Create Ticket** button below to open a private channel with our staff team."
            ),
            color=TICKET_COLOR,
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"{interaction.guild.name} • Support")

        try:
            await target.send(embed=embed, view=TicketLaunchView(self))
            await interaction.response.send_message(f"✅ Ticket panel sent to {target.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I lack permission to send messages in {target.mention}.", ephemeral=True)

    @app_commands.command(name="ticket_close", description="Close the current ticket channel")
    async def ticket_close_command(self, interaction: discord.Interaction):
        """Close the current ticket."""
        await self.close_ticket_channel(interaction)

    @app_commands.command(name="ticket_delete", description="Delete the current ticket channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_delete_command(self, interaction: discord.Interaction):
        """Delete the current ticket."""
        await self.delete_ticket_channel(interaction)

async def setup(bot):
    cog = Tickets(bot)
    bot.add_view(TicketLaunchView(cog))
    bot.add_view(TicketControlView(cog))
    await bot.add_cog(cog)
