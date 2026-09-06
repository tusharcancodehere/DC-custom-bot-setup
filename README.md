# DC Custom Bot

A modular, open-source Discord bot built with Python 3.13 and [`discord.py`](https://github.com/Rapptz/discord.py).

DC Custom Bot provides server moderation, community engagement, leveling, music playback, general utilities, and dual-provider AI assistance in a single configurable bot. The project is designed with a clean, modular architecture so developers can easily understand the codebase, add new features, and contribute.

---

## Current Status

> **Status:** Active Early Development

Core bot infrastructure, moderation tools, welcome embeds, level displays, music streaming, and AI conversation commands are fully functional. Current active features operate with in-memory state. Persistent PostgreSQL models, database migrations, support tickets, and entertainment mini-games are on the active roadmap. Track ongoing progress and upcoming milestones in [`TODO.md`](TODO.md).

---

## Features

### 🛡️ Moderation
Essential moderation commands with server-side permission checks and role hierarchy protection:
* `/kick` — Kick a member from the server with an optional reason.
* `/ban` — Ban a member from the server with an optional reason.
* `/unban` — Unban a user by their Discord user ID.
* `/timeout` — Temporarily timeout/mute a member for a specified duration in minutes.
* `/purge` — Bulk delete recent channel messages (1–1,000 messages).
* `/warn` — Send a formal direct message warning to a member.

### 🎵 Music
Local voice channel audio playback and queue management powered by `yt-dlp` and FFmpeg:
* `/play` — Search YouTube or provide a direct audio URL to play in voice.
* `/pause` — Pause current playback.
* `/resume` — Resume paused audio.
* `/skip` — Skip the current track to play the next song in the queue.
* `/stop` — Stop playback and clear the guild queue.
* `/queue` — View currently queued tracks with duration and requester details.
* `/volume` — Adjust audio volume (1–100%).
* `/player` — Display an interactive music player embed with live status.
* `/leave` — Disconnect the bot from the voice channel.
* `/247` — Toggle 24/7 mode to keep the bot connected in voice even when idle.

### 🤖 AI Assistant
Integrated conversational AI powered by dual providers with automated fallback:
* `/ask` — Send prompts to the AI assistant. Queries OpenAI (`gpt-5-mini`) first, automatically falling back to Google Gemini (`gemini-2.5-flash`) if unavailable.
* `/clear` — Reset your personal conversation history with the bot.

### 👋 Welcome System
Customizable member greeting functionality:
* `/welcome` — Displays a formatted welcome embed loaded from a configurable JSON template (`embed.json`) with dynamic channel mention formatting.

### 🆙 Level System
Activity and rank tracking components:
* `/level` — Display an interactive rank and level card with visual progress indicators.
* `/show_xp` — View the total XP of a specified member.
* `/leaderboard` & `/rank` — Placeholders for upcoming server-wide ranking tables.

### ⚙️ General & Utility
* `/ping` — Check bot connectivity and response status.
* `!shutdown` — Gracefully shut down the bot (restricted to the bot application owner).
* **Global Command Syncing** — Automatically registers and synchronizes slash commands globally across every Discord server where the bot is installed.

### 🗺️ Planned Features
Features currently on the roadmap include:
* Support ticket panels, claiming, and transcript generation.
* Interactive games (Coinflip, Dice, RPS, 8Ball, Trivia, Tic-Tac-Toe, Connect Four, Blackjack).
* Persistent database models and migrations with PostgreSQL, SQLAlchemy, and Alembic.

---

## Technology Stack

| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `>= 3.13` | Core programming language |
| **discord.py** | `>= 2.7.1` | Discord API wrapper and bot framework |
| **yt-dlp** | `>= 2026.8.19` | Audio streaming and metadata extraction |
| **PyNaCl** | `>= 1.6.2` | Voice support encryption library |
| **FFmpeg** | System binary | Audio decoding and transcode pipeline |
| **uv** | Latest | Fast Python package and dependency manager |
| **PostgreSQL** | `>= 15` | Relational database for persistent storage (planned models) |
| **SQLAlchemy** | `>= 2.0.52` | Asynchronous ORM and SQL toolkit |
| **asyncpg** | `>= 0.31.0` | High-performance PostgreSQL asynchronous driver |
| **Alembic** | `>= 1.19.1` | Database schema migrations |
| **OpenAI SDK** | `>= 3.8.0` | OpenAI API client for AI features |
| **Google GenAI** | `>= 2.22.0` | Google Gemini API client for fallback AI features |
| **Pillow** | `>= 12.3.0` | Image processing (rank cards and welcome graphics) |
| **Jinja2** | `>= 3.1.6` | Template rendering (transcripts and HTML exports) |

---

## Project Structure

```text
DC-custom-bot-setup/
├── src/
│   ├── main.py              # Application entrypoint
│   ├── core/                # Bot initialization and shared subsystems
│   │   ├── bot.py           # CustomBot class, setup_hook, on_ready sync
│   │   ├── config.py        # Configuration loading
│   │   ├── errors.py        # Global exception handling
│   │   ├── loader.py        # Cog discovery and loading
│   │   ├── logging.py       # Central application logging
│   │   └── permissions.py   # Permission checks and decorators
│   ├── features/            # Independent, modular bot features
│   │   ├── admin/           # Server administration commands (planned)
│   │   ├── ai/              # AI commands (/ask, /clear)
│   │   ├── games/           # Mini-games and entertainment (planned)
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # XP tracking and rank cards (/level, /show_xp)
│   │   ├── moderation/      # Moderation commands (/kick, /ban, /timeout, etc.)
│   │   ├── music/           # Audio playback and queue management
│   │   ├── tickets/         # Support ticket system (planned)
│   │   └── welcome/         # Welcome messages and templates (/welcome)
│   ├── views/               # Shared Discord UI components (buttons, modals)
│   │   └── common.py
│   └── database/            # Database engine and session management
│       └── database.py
├── alembic/                 # Database schema migration scripts (planned)
├── docs/                    # Architectural and developer documentation
│   └── database.md          # Database setup and configuration guide
├── scripts/                 # Maintenance and utility scripts
├── tests/                   # Test suite
├── .env.example             # Template for required environment variables
├── pyproject.toml           # Project metadata, dependencies, and script definitions
├── uv.lock                  # Pinned dependency lockfile
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Contributor Code of Conduct
├── SECURITY.md              # Security policy and disclosure process
├── TODO.md                  # Project roadmap and completed tasks
└── README.md                # Project documentation overview
```

---

## Setup & Installation

### Prerequisites

* **Python 3.13+**
* [**uv**](https://docs.astral.sh/uv/)
* [**FFmpeg**](https://ffmpeg.org/) (required for voice and music playback)
* **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/tusharcancodehere/DC-custom-bot-setup.git
cd DC-custom-bot-setup
```

### 2. Install Dependencies

Install all project dependencies into a virtual environment using `uv`:

```bash
uv sync
```

### 3. Configure Environment Variables

Create your local `.env` configuration file from the template:

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | Yes | Discord Bot token generated from the Discord Developer Portal. |
| `APPLICATION_ID` | Yes | Discord Application / Client ID. |
| `DATABASE_URL` | Optional | PostgreSQL asyncpg connection string. If omitted, the bot runs with in-memory state. |
| `OPENAI_API_KEY` | Optional | API key for OpenAI (`gpt-5-mini`) used by `/ask`. |
| `GEMINI_API_KEY` | Optional | API key for Google Gemini (`gemini-2.5-flash`) used as a fallback for `/ask`. |

> [!WARNING]
> Never commit your `.env` file or share your bot tokens and API keys publicly.

---

## Running the Bot

Run the application using `uv`:

```bash
uv run python src/main.py
```

Upon startup, the bot loads active features, registers event listeners, and synchronizes slash commands globally across all installed servers.

---

## Database & Persistence

The bot includes an asynchronous database engine configured in [`src/database/database.py`](src/database/database.py) using SQLAlchemy 2.0 and `asyncpg`.

* **In-Memory Default**: Current active features run in-memory and do not require a running database instance to start.
* **Persistent Storage**: For running PostgreSQL locally or connecting to an external database, refer to the [**Database Guide**](docs/database.md).

---

## Verification & Code Quality

Verify that all Python source files compile cleanly without syntax errors:

```bash
uv run python -m compileall -q src
```

---

## Contributing

Contributions from the open-source community are warmly welcomed!

* Please read our [**Contributing Guide**](CONTRIBUTING.md) for full instructions on local setup, code conventions, branch naming, and opening pull requests.
* All participants must abide by our [**Code of Conduct**](CODE_OF_CONDUCT.md).

---

## Security

If you discover a security vulnerability, please do **not** report it via public GitHub issues or public chat. Refer to our [**Security Policy**](SECURITY.md) for instructions on confidential reporting.

---

## License

This project is licensed under the terms of the [**MIT License**](LICENSE).

Copyright (c) 2026 Tushar Verma.
