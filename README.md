# DC Custom Bot

A modular, open-source Discord bot built with Python 3.13 and [`discord.py`](https://github.com/Rapptz/discord.py).

DC Custom Bot provides server moderation, community engagement, leveling, general utilities, and dual-provider AI assistance in a single configurable bot. The project is designed with a lightweight, modular architecture so developers can easily understand the codebase, add new features, and contribute.

---

## Current Status

> **Status:** Active Early Development

Core bot infrastructure, moderation tools, welcome embeds, level displays, and AI conversation commands are functional. Additional systems—including support tickets, entertainment mini-games, voice/music playback, and PostgreSQL database models—are currently under development. Track ongoing progress and upcoming milestones in [`TODO.md`](TODO.md).

---

## Features

### 🛡️ Moderation
Essential moderation commands with server-side permission checks and role hierarchy protection:
* `/kick` — Kick a member from the server with an optional reason.
* `/ban` — Ban a member from the server with an optional reason.
* `/unban` — Unban a user by their Discord user ID.
* `/timeout` — Temporarily timeout/mute a member for a specified duration in minutes.
* `/purge` — Bulk delete recent channel messages (1–100 messages).
* `/warn` — Send a formal direct message warning to a member.

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
* **Guild Command Syncing** — Automatically copies and synchronizes slash commands to your target guild upon startup for instantaneous testing.

### 🗺️ Planned Features
Features currently on the roadmap include:
* Support ticket panels, claiming, and transcript generation.
* Interactive games (Coinflip, Dice, RPS, 8Ball, Trivia, Tic-Tac-Toe, Connect Four, Blackjack).
* Voice channel audio and music streaming.
* Persistent database models and migrations with PostgreSQL, SQLAlchemy, and Alembic.

---

## Technology Stack

| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `>= 3.13` | Core programming language |
| **discord.py** | `>= 2.7.1` | Discord API wrapper and bot framework |
| **uv** | Latest | Fast Python package and dependency manager |
| **mise** | Latest | Tool and runtime version management |
| **PostgreSQL** | `>= 15` | Relational database for persistent storage |
| **SQLAlchemy** | `>= 2.0.52` | Asynchronous ORM and SQL toolkit |
| **asyncpg** | `>= 0.31.0` | High-performance PostgreSQL asynchronous driver |
| **Alembic** | `>= 1.19.1` | Database schema migrations |
| **OpenAI SDK** | `>= 3.8.0` | OpenAI API client for AI features |
| **Google GenAI** | `>= 2.22.0` | Google Gemini API client for fallback AI features |
| **Pillow** | `>= 12.3.0` | Image processing (rank cards and welcome graphics) |
| **Jinja2** | `>= 3.1.6` | Template rendering (transcripts and HTML exports) |
| **PyNaCl** | `>= 1.6.2` | Voice support encryption library |
| **Ruff** | Latest | Code formatting and linting |
| **pytest** | Latest | Automated testing framework |

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
│   │   ├── admin/           # Server administration commands
│   │   ├── ai/              # AI commands (/ask, /clear)
│   │   ├── games/           # Mini-games and entertainment
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # XP tracking and rank cards (/level, /show_xp)
│   │   ├── moderation/      # Moderation commands (/kick, /ban, /timeout, etc.)
│   │   ├── music/           # Audio playback and queue management
│   │   ├── tickets/         # Support ticket system
│   │   └── welcome/         # Welcome messages and templates (/welcome)
│   ├── views/               # Shared Discord UI components (buttons, modals)
│   │   └── common.py
│   └── database/            # Database engine and session management
│       └── database.py
├── alembic/                 # Database schema migration scripts
├── docs/                    # In-depth architectural and developer documentation
├── scripts/                 # Maintenance and utility scripts
├── tests/                   # Test suite
├── .env.example             # Template for required environment variables
├── pyproject.toml           # Project metadata, dependencies, and script definitions
├── uv.lock                  # Pinned dependency lockfile
├── mise.toml                # Runtime tool versions
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Contributor Code of Conduct
├── SECURITY.md              # Security policy and disclosure process
└── README.md                # Project documentation overview
```

---

## Setup & Installation

### Prerequisites

* **Python 3.13+**
* [**uv**](https://docs.astral.sh/uv/)
* [**mise**](https://mise.jdx.dev/) (optional, recommended for managing Python versions)
* **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/tusharcancodehere/DC-custom-bot-setup.git
cd DC-custom-bot-setup
```

### 2. Install Development Tools

If using `mise`:

```bash
mise install
```

### 3. Install Dependencies

Install all project dependencies into a virtual environment using `uv`:

```bash
uv sync
```

### 4. Configure Environment Variables

Create your local `.env` configuration file from the template:

```bash
cp .env.example .env
```

Open `.env` and fill in your values.

---

## Environment Variables

The bot reads configuration settings from environment variables. Define these in your `.env` file:

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | Yes | Discord Bot token generated from the Discord Developer Portal. |
| `APPLICATION_ID` | Yes | Discord Application / Client ID. |
| `SERVER_ID` | Yes | Discord Guild/Server ID where slash commands will be synced immediately. |
| `OPENAI_API_KEY` | Optional | API key for OpenAI (`gpt-5-mini`) used by `/ask`. |
| `GEMINI_API_KEY` | Optional | API key for Google Gemini (`gemini-2.5-flash`) used as a fallback for `/ask`. |

> [!WARNING]
> Never commit your `.env` file or share your bot tokens and API keys publicly.

---

## Running the Bot

Run the application using `uv`:

```bash
uv run python -m src.main
```

Upon startup, the bot loads active features, registers event listeners, and synchronizes slash commands to the designated guild.

---

## Development

Install development dependencies:

```bash
uv sync --dev
```

### Linting and Code Formatting

We use [Ruff](https://docs.astral.sh/ruff/) to maintain code quality:

```bash
# Check code for linting issues
uv run ruff check .

# Automatically format code
uv run ruff format .
```

### Running Tests

Run the automated test suite using `pytest`:

```bash
uv run pytest
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
