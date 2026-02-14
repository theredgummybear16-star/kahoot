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
    command_cooldown_seconds: int = 5
    max_bots_per_user: int = 1

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables.

        Raises:
            ValueError: If required settings are missing.
        """
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise ValueError("Missing DISCORD_TOKEN in environment or .env file.")

        cooldown = int(os.getenv("COMMAND_COOLDOWN_SECONDS", "5"))
        max_bots = int(os.getenv("MAX_BOTS_PER_USER", "1"))
        return cls(
            discord_token=token,
            command_cooldown_seconds=cooldown,
            max_bots_per_user=max_bots,
        )
