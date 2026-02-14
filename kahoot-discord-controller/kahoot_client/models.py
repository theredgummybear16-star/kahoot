"""Data models shared across the Discord and Kahoot client layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class GameInfo:
    """Metadata for a Kahoot game pin."""

    pin: int
    title: str
    host: str
    question_count: int
    raw: dict = field(default_factory=dict)


@dataclass(slots=True)
class UserPreferences:
    """Per-user configuration for join behavior."""

    default_name: str = "KahootBot"
    answer_delay: float = 1.8


@dataclass(slots=True)
class ActiveBotInfo:
    """Bookkeeping state for an active user-owned Kahoot client."""

    user_id: int
    username: str
    game_pin: int
    bot_name: str
    started_at: datetime
