"""Entry point for the Discord-controlled Kahoot educational simulator."""

from __future__ import annotations

import logging

from discord_bot.bot import KahootDiscordBot
from discord_bot.config import Settings


def configure_logging() -> None:
    """Configure console logging for development and educational debugging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )


def main() -> None:
    """Load settings and start the Discord bot process."""
    configure_logging()
    settings = Settings.from_env()
    bot = KahootDiscordBot(
        cooldown_seconds=settings.command_cooldown_seconds,
        max_bots_per_user=settings.max_bots_per_user,
    )
    bot.run(settings.discord_token)


if __name__ == "__main__":
    main()
