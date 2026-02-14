"""Kahoot client package for educational simulation of Bayeux/WebSocket flows."""

from .client import KahootClient, fetch_game_info
from .models import GameInfo, UserPreferences

__all__ = ["KahootClient", "fetch_game_info", "GameInfo", "UserPreferences"]
