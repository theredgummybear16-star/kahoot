# Discord-Controlled Kahoot Bot System (Educational Simulation)

> **Educational and research only**: This project demonstrates Discord slash commands + real-time WebSocket/Bayeux messaging patterns.
> It is **not** intended for abuse, disruption, or unauthorized use in live games.

## Purpose

This repository shows how to build a modular multi-client system where:

- A Discord bot receives user slash commands.
- Each user can control a lightweight Kahoot client session.
- The Kahoot client uses a direct Bayeux-style flow over WebSocket without `kahoot.py`.

## Responsible Use & Legal Notice

- You must only test against games where you have **explicit permission**.
- Using automation against live Kahoot sessions can violate Kahoot's Terms of Service.
- You assume all responsibility for any usage of this code.
- The client intentionally avoids disruptive features (no mass joins, no flooding, no griefing logic).

## Project Layout

```text
kahoot-discord-controller/
├── discord_bot/
│   ├── __init__.py
│   ├── bot.py
│   ├── cogs/
│   └── config.py
├── kahoot_client/
│   ├── __init__.py
│   ├── client.py
│   └── models.py
├── main.py
├── .env.example
├── requirements.txt
├── README.md
└── docker-compose.yml
```

## Features

- Discord slash commands only:
  - `/get_pin <game_pin:int>`
  - `/join <game_pin:int> [bot_name:str]`
  - `/leave [all:bool]`
  - `/status`
  - `/config [default_name:str] [answer_delay:float]`
- In-memory user session management.
- Max bots per user (default: 1).
- Global command cooldown.
- Graceful disconnect handling and simple reconnect loop.
- Random delayed answer behavior to simulate a participant.

## Prerequisites

- Python 3.9+
- A Discord application token with bot permissions.
- Network access to Discord and Kahoot endpoints.

## Setup

1. Clone repository and enter the directory:
   ```bash
   git clone <your-repo-url>
   cd kahoot-discord-controller
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create your environment file:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and set your real token:
   ```env
   DISCORD_TOKEN=your_real_discord_bot_token
   COMMAND_COOLDOWN_SECONDS=5
   MAX_BOTS_PER_USER=1
   ```

## Run

```bash
python main.py
```

## Command Examples

- `/get_pin 123456`
  - Returns title, host, and question count when available.
- `/config default_name:StudyBot answer_delay:2.2`
  - Sets defaults for future `/join` calls.
- `/join 123456 bot_name:NotebookBot`
  - Joins one game for your user.
- `/status`
  - Shows active sessions and uptime.
- `/leave`
  - Stops your most recent bot.
- `/leave all:true`
  - Stops all of your active bots.

## Bayeux/WebSocket Notes

The Kahoot client contains a **best-effort educational implementation** of Bayeux message flow:

1. `/meta/handshake`
2. `/meta/connect`
3. Join/login message to `/service/controller`
4. Listen for player/game messages and respond to question-like payloads.

Because Kahoot's protocol is private and can change, these assumptions may break.
The code includes comments explaining these assumptions and keeps behavior conservative.

## Continuous Integration (GitHub Actions)

This repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that runs on every push and pull request.

It validates the project by:

- Installing dependencies from `requirements.txt`
- Compiling all Python modules (`python -m compileall`)
- Running a lightweight import smoke test

## Docker (Optional)

Create `.env` first, then run:

```bash
docker compose up --build
```

## Extending the Project

- Add persistent storage for preferences and sessions.
- Move commands into cogs.
- Add structured metrics/logging.
- Add safer simulation toggles (e.g., join-only mode, no answering).
