"""Minimal educational Kahoot client using Bayeux over WebSocket.

This module intentionally avoids disruptive behavior and demonstrates protocol handling
for learning purposes only. Kahoot endpoints and payload contracts can change over time.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
import uuid
from typing import Any

import requests
import websockets
from websockets import WebSocketClientProtocol

from .models import GameInfo

LOGGER = logging.getLogger(__name__)
KAHOOT_COMETD_URL = "wss://kahoot.it/cometd"
KAHOOT_PIN_LOOKUP_URL = "https://kahoot.it/rest/challenges/pin/{pin}"


class KahootClientError(Exception):
    """Raised when Kahoot protocol setup or I/O fails."""


def fetch_game_info(pin: int, timeout: float = 8.0) -> GameInfo:
    """Fetch metadata for a Kahoot game pin via Kahoot's REST lookup endpoint."""
    response = requests.get(KAHOOT_PIN_LOOKUP_URL.format(pin=pin), timeout=timeout)
    if response.status_code != 200:
        raise KahootClientError(f"Could not resolve game pin {pin} (status={response.status_code}).")

    payload: dict[str, Any] = response.json()
    kahoot_data = payload.get("kahoot", {})
    organizer = payload.get("organizer", {})
    title = kahoot_data.get("title", "Unknown Kahoot")
    questions = kahoot_data.get("numberOfQuestions", 0)
    host = organizer.get("username", "Unknown host")

    return GameInfo(
        pin=pin,
        title=title,
        host=host,
        question_count=int(questions),
        raw=payload,
    )


class KahootClient:
    """Educational Bayeux/WebSocket client for a single Kahoot game participant."""

    def __init__(self, game_pin: int, username: str, answer_delay: float = 1.8) -> None:
        self.game_pin = game_pin
        self.username = username
        self.answer_delay = max(0.3, answer_delay)
        self.client_id: str | None = None
        self.ws: WebSocketClientProtocol | None = None
        self.connected = False
        self._disconnect_requested = False
        self._ack_id = 0

    async def run(self) -> None:
        """Connect and keep handling messages until disconnected."""
        while not self._disconnect_requested:
            try:
                await self._connect_and_loop()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.warning("Kahoot client for pin=%s crashed: %s", self.game_pin, exc)
                if self._disconnect_requested:
                    break
                await asyncio.sleep(2.0)

    async def disconnect(self) -> None:
        """Disconnect the active websocket session."""
        self._disconnect_requested = True
        self.connected = False
        if self.ws is not None:
            await self.ws.close(code=1000)

    async def _connect_and_loop(self) -> None:
        async with websockets.connect(KAHOOT_COMETD_URL, ping_interval=20, ping_timeout=20) as ws:
            self.ws = ws
            await self._handshake()
            await self._join_game()
            self.connected = True

            while not self._disconnect_requested:
                raw_message = await ws.recv()
                data = json.loads(raw_message)
                if isinstance(data, dict):
                    data = [data]
                await self._handle_messages(data)

    async def _handshake(self) -> None:
        response = await self._send_bayeux(
            {
                "channel": "/meta/handshake",
                "version": "1.0",
                "minimumVersion": "1.0",
                "supportedConnectionTypes": ["websocket", "long-polling"],
                "id": self._next_id(),
                "advice": {"timeout": 60000, "interval": 0},
            }
        )
        if not response or not response[0].get("successful"):
            raise KahootClientError("Handshake failed.")
        self.client_id = response[0].get("clientId")
        if not self.client_id:
            raise KahootClientError("Handshake did not return clientId.")

        await self._send_bayeux(
            {
                "channel": "/meta/connect",
                "clientId": self.client_id,
                "connectionType": "websocket",
                "id": self._next_id(),
            }
        )

    async def _join_game(self) -> None:
        if self.client_id is None:
            raise KahootClientError("clientId missing before join.")

        join_payload = {
            "channel": "/service/controller",
            "clientId": self.client_id,
            "id": self._next_id(),
            "data": {
                "gameid": str(self.game_pin),
                "host": "kahoot.it",
                "type": "login",
                "name": self.username,
                "content": json.dumps({"device": {"userAgent": "Mozilla/5.0"}}),
            },
            "ext": {"ack": True},
        }
        response = await self._send_bayeux(join_payload)
        success = any(msg.get("successful") is True for msg in response)
        if not success:
            raise KahootClientError("Join failed (pin may be invalid, locked, or expired).")

    async def _handle_messages(self, messages: list[dict[str, Any]]) -> None:
        for message in messages:
            channel = message.get("channel", "")
            data = message.get("data", {})

            if channel == "/meta/connect":
                await self._send_bayeux(
                    {
                        "channel": "/meta/connect",
                        "clientId": self.client_id,
                        "connectionType": "websocket",
                        "id": self._next_id(),
                    }
                )
                continue

            if channel == "/service/player":
                content_raw = data.get("content")
                content = self._safe_json(content_raw)
                if isinstance(content, dict):
                    await self._try_answer_question(content)

    async def _try_answer_question(self, content: dict[str, Any]) -> None:
        """Send one random answer when question payload appears.

        Assumption: Kahoot may send an object with question index and number of choices.
        The exact schema can vary and this logic is intentionally conservative.
        """
        if "questionIndex" not in content:
            return

        num_choices = int(content.get("numberOfChoices", 4) or 4)
        num_choices = min(max(num_choices, 2), 8)
        random_choice = random.randrange(num_choices)
        question_index = content["questionIndex"]
        lag = self.answer_delay + random.uniform(0.0, 1.2)
        await asyncio.sleep(lag)

        answer_payload = {
            "channel": "/service/controller",
            "clientId": self.client_id,
            "id": self._next_id(),
            "data": {
                "gameid": str(self.game_pin),
                "host": "kahoot.it",
                "id": str(uuid.uuid4()),
                "type": "message",
                "content": json.dumps(
                    {
                        "type": "answer",
                        "choice": random_choice,
                        "questionIndex": question_index,
                    }
                ),
            },
            "ext": {"ack": True},
        }
        await self._send_bayeux(answer_payload)

    async def _send_bayeux(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        if self.ws is None:
            raise KahootClientError("WebSocket not initialized.")
        await self.ws.send(json.dumps([payload]))
        response_raw = await self.ws.recv()
        data = json.loads(response_raw)
        if isinstance(data, dict):
            return [data]
        return data

    def _next_id(self) -> str:
        self._ack_id += 1
        return str(self._ack_id)

    @staticmethod
    def _safe_json(value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                return None
        return None
