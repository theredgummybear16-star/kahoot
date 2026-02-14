"""Configuration loading for the Discord-controlled Kahoot educational simulator."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    """Runtime settings sourced from environment variables."""

    discord_token: str
    discord_server: int
    command_cooldown_seconds: int = 5
    max_bots_per_user: int = 1

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables.

        Raises:
            ValueError: If required settings are missing or invalid.
        """
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise ValueError("Missing DISCORD_TOKEN in environment or .env file.")

        server_value = os.getenv("DISCORD_SERVER", "").strip()
        if not server_value:
            raise ValueError("Missing DISCORD_SERVER in environment or .env file.")
        if not server_value.isdigit():
            raise ValueError("DISCORD_SERVER must be a numeric guild/server ID.")

        cooldown = int(os.getenv("COMMAND_COOLDOWN_SECONDS", "5"))
        max_bots = int(os.getenv("MAX_BOTS_PER_USER", "1"))
        return cls(
            discord_token=token,
            discord_server=int(server_value),
            command_cooldown_seconds=cooldown,
            max_bots_per_user=max_bots,
        )
