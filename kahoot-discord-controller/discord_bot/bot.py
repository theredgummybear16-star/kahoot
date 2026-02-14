"""Discord slash-command bot for educational Kahoot client orchestration."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from kahoot_client.client import KahootClient, KahootClientError, fetch_game_info
from kahoot_client.models import ActiveBotInfo, UserPreferences

LOGGER = logging.getLogger(__name__)
CONTROL_CATEGORY_NAME = "kahoot-controller"
COMMAND_CHANNEL_NAME = "kahoot-commands"
STATUS_CHANNEL_NAME = "kahoot-status"


@dataclass(slots=True)
class ManagedClient:
    """Container for live client task and metadata."""

    client: KahootClient
    task: asyncio.Task[None]
    info: ActiveBotInfo


class KahootDiscordBot(commands.Bot):
    """Discord bot using slash commands to control one Kahoot client per user."""

    def __init__(
        self,
        *,
        cooldown_seconds: int = 5,
        max_bots_per_user: int = 1,
        guild_id: int,
    ) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.cooldown_seconds = cooldown_seconds
        self.max_bots_per_user = max_bots_per_user
        self.guild_id = guild_id
        self.preferences: dict[int, UserPreferences] = defaultdict(UserPreferences)
        self.active_clients: dict[int, list[ManagedClient]] = defaultdict(list)
        self._guild_synced = False
        self.tree.error(self.on_app_command_error)

    def _is_allowed_guild(self, interaction: discord.Interaction) -> bool:
        """Return true when a command is invoked in the configured guild."""
        return interaction.guild_id == self.guild_id

    async def setup_hook(self) -> None:
        """Register slash commands and synchronize command tree."""
        guild = discord.Object(id=self.guild_id)

        @self.tree.command(name="get_pin", description="Fetch metadata for a Kahoot game PIN.", guild=guild)
        @app_commands.guild_only()
        @app_commands.checks.cooldown(1, self.cooldown_seconds)
        async def get_pin(interaction: discord.Interaction, game_pin: int) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return

            await interaction.response.defer(thinking=True, ephemeral=True)
            try:
                game = await asyncio.to_thread(fetch_game_info, game_pin)
            except (KahootClientError, TimeoutError, OSError) as exc:
                await interaction.followup.send(f"Could not fetch game metadata: {exc}", ephemeral=True)
                return

            embed = discord.Embed(title="Kahoot Game Metadata", color=discord.Color.blurple())
            embed.add_field(name="PIN", value=str(game.pin), inline=True)
            embed.add_field(name="Title", value=game.title, inline=False)
            embed.add_field(name="Host", value=game.host, inline=True)
            embed.add_field(name="Questions", value=str(game.question_count), inline=True)
            embed.set_footer(text="Educational use only. Respect Kahoot Terms of Service.")
            await interaction.followup.send(embed=embed, ephemeral=True)

        @self.tree.command(name="ping", description="Check whether the bot is responding.", guild=guild)
        @app_commands.guild_only()
        async def ping(interaction: discord.Interaction) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return
            await interaction.response.send_message("Pong ✅ Bot is online and slash commands are working.", ephemeral=True)

        @self.tree.command(name="join", description="Join a Kahoot game with one educational bot.", guild=guild)
        @app_commands.guild_only()
        @app_commands.checks.cooldown(1, self.cooldown_seconds)
        async def join(
            interaction: discord.Interaction,
            game_pin: int,
            bot_name: str | None = None,
        ) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return

            await interaction.response.defer(thinking=True, ephemeral=True)
            user_id = interaction.user.id
            user_bots = self.active_clients[user_id]
            if len(user_bots) >= self.max_bots_per_user:
                await interaction.followup.send(
                    f"You already have {len(user_bots)} active bot(s). Leave first before spawning another.",
                    ephemeral=True,
                )
                return

            pref = self.preferences[user_id]
            name_to_use = (bot_name or pref.default_name).strip()[:16] or "KahootBot"

            try:
                await asyncio.to_thread(fetch_game_info, game_pin)
            except (KahootClientError, TimeoutError, OSError) as exc:
                await interaction.followup.send(f"Invalid or unreachable game PIN: {exc}", ephemeral=True)
                return

            client = KahootClient(game_pin=game_pin, username=name_to_use, answer_delay=pref.answer_delay)
            info = ActiveBotInfo(
                user_id=user_id,
                username=str(interaction.user),
                game_pin=game_pin,
                bot_name=name_to_use,
                started_at=datetime.now(timezone.utc),
            )
            task = asyncio.create_task(client.run(), name=f"kahoot-client-{user_id}-{game_pin}")
            self.active_clients[user_id].append(ManagedClient(client=client, task=task, info=info))
            await interaction.followup.send(
                f"Joined PIN **{game_pin}** as **{name_to_use}**."
                " This project is for educational protocol research only.",
                ephemeral=True,
            )

        @self.tree.command(name="leave", description="Leave your current Kahoot game.", guild=guild)
        @app_commands.guild_only()
        @app_commands.checks.cooldown(1, self.cooldown_seconds)
        async def leave(interaction: discord.Interaction, all: bool = False) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return

            await interaction.response.defer(thinking=True, ephemeral=True)
            user_id = interaction.user.id
            clients = self.active_clients.get(user_id, [])
            if not clients:
                await interaction.followup.send("You have no active bots.", ephemeral=True)
                return

            targets = clients if all else [clients[-1]]
            for managed in targets:
                await managed.client.disconnect()
                managed.task.cancel()

            if all:
                self.active_clients[user_id] = []
                await interaction.followup.send("Stopped all your active bots.", ephemeral=True)
            else:
                self.active_clients[user_id].pop()
                await interaction.followup.send("Stopped your most recent bot.", ephemeral=True)

        @self.tree.command(name="status", description="Show your active educational Kahoot clients.", guild=guild)
        @app_commands.guild_only()
        @app_commands.checks.cooldown(1, self.cooldown_seconds)
        async def status(interaction: discord.Interaction) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return

            user_id = interaction.user.id
            entries = self.active_clients.get(user_id, [])
            if not entries:
                await interaction.response.send_message("No active bots.", ephemeral=True)
                return

            embed = discord.Embed(title="Your Active Bots", color=discord.Color.green())
            for idx, managed in enumerate(entries, start=1):
                uptime = datetime.now(timezone.utc) - managed.info.started_at
                embed.add_field(
                    name=f"Bot {idx}: {managed.info.bot_name}",
                    value=f"PIN: {managed.info.game_pin}\n"
                    f"Connected: {managed.client.connected}\n"
                    f"Uptime: {str(uptime).split('.', maxsplit=1)[0]}",
                    inline=False,
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.tree.command(name="config", description="Set default join preferences.", guild=guild)
        @app_commands.guild_only()
        @app_commands.checks.cooldown(1, self.cooldown_seconds)
        async def config(
            interaction: discord.Interaction,
            default_name: str | None = None,
            answer_delay: app_commands.Range[float, 0.3, 10.0] | None = None,
        ) -> None:
            if not self._is_allowed_guild(interaction):
                await interaction.response.send_message("This bot is restricted to its configured server.", ephemeral=True)
                return

            user_id = interaction.user.id
            prefs = self.preferences[user_id]

            if default_name is not None:
                prefs.default_name = default_name.strip()[:16] or prefs.default_name
            if answer_delay is not None:
                prefs.answer_delay = float(answer_delay)

            await interaction.response.send_message(
                f"Saved preferences: default_name=`{prefs.default_name}`, answer_delay={prefs.answer_delay:.1f}s",
                ephemeral=True,
            )

        synced = await self.tree.sync(guild=guild)
        self._guild_synced = True
        LOGGER.info("Synced %s command(s) for guild %s.", len(synced), self.guild_id)

    async def on_ready(self) -> None:
        """Initialize required channels when the bot is online."""
        if not self._guild_synced:
            try:
                synced = await self.tree.sync(guild=discord.Object(id=self.guild_id))
                self._guild_synced = True
                LOGGER.info("Synced %s command(s) for guild %s during on_ready.", len(synced), self.guild_id)
            except discord.HTTPException as exc:
                LOGGER.error("Command sync failed for guild %s: %s", self.guild_id, exc)

        try:
            await self.ensure_guild_resources()
        except discord.Forbidden:
            LOGGER.error(
                "Missing permissions to create category/channels in guild %s. "
                "Grant Manage Channels permission to the bot.",
                self.guild_id,
            )
        except discord.HTTPException as exc:
            LOGGER.error("Failed to ensure guild resources: %s", exc)

        guild = self.get_guild(self.guild_id)
        if guild is None:
            known_guilds = ", ".join(f"{g.name}({g.id})" for g in self.guilds) or "none"
            LOGGER.error("Configured DISCORD_SERVER=%s not found in connected guilds: %s", self.guild_id, known_guilds)
        LOGGER.info("Logged in as %s", self.user)

    async def ensure_guild_resources(self) -> None:
        """Create category/channels used by the bot if they do not exist."""
        guild = self.get_guild(self.guild_id)
        if guild is None:
            LOGGER.warning("Configured guild %s is not visible to the bot.", self.guild_id)
            return

        category = discord.utils.get(guild.categories, name=CONTROL_CATEGORY_NAME)
        if category is None:
            category = await guild.create_category(CONTROL_CATEGORY_NAME, reason="Initialize Kahoot controller resources")

        existing_text_channels = {channel.name for channel in category.text_channels}
        if COMMAND_CHANNEL_NAME not in existing_text_channels:
            await guild.create_text_channel(COMMAND_CHANNEL_NAME, category=category)
        if STATUS_CHANNEL_NAME not in existing_text_channels:
            await guild.create_text_channel(STATUS_CHANNEL_NAME, category=category)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Shared error handler for slash-command failures."""
        if isinstance(error, app_commands.CommandOnCooldown):
            message = f"Cooldown active. Retry in {error.retry_after:.1f}s."
        elif isinstance(error, app_commands.NoPrivateMessage):
            message = "This command is only available in servers (guilds)."
        else:
            message = "An unexpected error occurred while executing the command."
            LOGGER.exception("App command error: %s", error)

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)
