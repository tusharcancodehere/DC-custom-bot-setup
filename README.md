# DC Custom Bot

A modular, open-source Discord bot built with Python.

DC Custom Bot provides server management, moderation, community, entertainment, and AI features in one configurable bot while keeping the codebase simple enough for contributors to understand and extend.

> **Status:** Early development

---

## Features

### 🛠️ Administration

Tools for managing and configuring your Discord server.

* Server management
* Channel management
* Role management
* Server configuration
* Announcements
* Feature configuration

### 🛡️ Moderation

Essential moderation tools for keeping servers safe and manageable.

* Ban
* Unban
* Kick
* Timeout
* Warnings
* Message purge
* Channel locking
* Slowmode
* Moderation logging
* Auto moderation
* Spam protection
* Invite and link filtering

### 🎫 Tickets

A configurable support ticket system.

* Ticket panels
* Ticket creation
* Ticket categories
* Claiming tickets
* Adding and removing users
* Closing tickets
* Staff permissions
* Ticket logging
* Ticket transcripts

### 👋 Welcome

Customizable member join and leave functionality.

* Welcome messages
* Leave messages
* Custom channels
* Auto roles
* Welcome images
* Test messages
* Configurable templates

### 🆙 Level System

Reward server activity with an XP and leveling system.

* XP tracking
* Levels
* Rank cards
* Leaderboards
* Level-up announcements
* Level rewards
* Role rewards
* Server-specific configuration

### 🎮 Games

Interactive games and entertainment.

* Coin flip
* Dice
* Rock Paper Scissors
* 8 Ball
* Trivia
* Tic Tac Toe
* Connect Four
* Blackjack
* Game statistics

### 🎵 Music

Voice and audio functionality.

* Music playback
* Queue
* Pause and resume
* Skip
* Stop
* Loop
* Volume
* Now playing

### 🤖 AI

AI-powered functionality integrated into Discord.

* AI commands
* Conversations
* Context-aware responses
* AI assistance
* Future AI-powered server tools

---

## Planned Features

The bot is designed to grow beyond its initial feature set.

Planned and possible future features include:

* Economy
* Giveaways
* Polls
* Reminders
* Reaction roles
* Suggestions
* Starboard
* Verification
* Custom commands
* Temporary voice channels
* Server statistics
* Advanced AutoMod
* AI moderation
* Web dashboard
* Public API

See [`TODO.md`](TODO.md) for the current development roadmap.

---

## Technology Stack

| Technology  | Purpose                             |
| ----------- | ----------------------------------- |
| Python 3.13 | Main programming language           |
| discord.py  | Discord API and bot framework       |
| PostgreSQL  | Persistent database                 |
| SQLAlchemy  | Database toolkit and ORM            |
| asyncpg     | PostgreSQL driver                   |
| Alembic     | Database migrations                 |
| aiohttp     | Asynchronous HTTP requests          |
| OpenAI SDK  | AI functionality                    |
| Pillow      | Image processing                    |
| Jinja2      | HTML templates and transcripts      |
| PyNaCl      | Discord voice support               |
| FFmpeg      | Audio processing                    |
| uv          | Python dependency management        |
| mise        | Development tool/version management |

---

## Architecture

The project intentionally uses a simple modular architecture.

```text
src/
├── main.py
│
├── core/
│   ├── bot.py
│   ├── config.py
│   ├── loader.py
│   ├── errors.py
│   ├── logging.py
│   └── permissions.py
│
├── features/
│   ├── admin/
│   ├── moderation/
│   ├── tickets/
│   ├── welcome/
│   ├── levels/
│   ├── games/
│   ├── music/
│   └── ai/
│
├── views/
│   └── common.py
│
└── database/
    └── database.py
```

### `core/`

Contains functionality required by the bot itself.

### `features/`

Contains the actual bot features. Each major feature is kept separate so it can be developed and maintained independently.

### `views/`

Contains reusable Discord UI components such as buttons, select menus, and modals.

### `database/`

Contains PostgreSQL database functionality.

The architecture is intentionally not over-engineered. Additional layers or files should be introduced when the project's complexity genuinely requires them.

---

## Requirements

You need:

* Python 3.13
* `mise`
* `uv`
* PostgreSQL
* FFmpeg
* Git

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd DC-custom-bot-setup
```

Install the project's configured tools:

```bash
mise install
```

Install Python dependencies:

```bash
uv sync
```

Create your local environment file:

```bash
cp .env.example .env
```

Configure the required credentials.

---

## Environment Variables

The project uses environment variables for secrets and configuration.

Example:

```env
DISCORD_TOKEN=
DATABASE_URL=
OPENAI_API_KEY=
```

Never commit `.env` or other credentials to Git.

---

## Discord Bot Setup

Create a Discord application through the Discord Developer Portal and create a bot user.

Configure the required Gateway Intents for the features you enable.

The exact permissions and intents required may change as features are added.

Never share your Discord bot token.

---

## PostgreSQL

DC Custom Bot uses PostgreSQL for persistent data.

The application communicates with PostgreSQL through:

```text
Python
   ↓
SQLAlchemy
   ↓
asyncpg
   ↓
PostgreSQL
```

Database schema changes are managed using Alembic migrations.

---

## Running the Bot

Run the bot with:

```bash
uv run python -m src.main
```

---

## Development

Install development dependencies:

```bash
uv sync --dev
```

Run tests:

```bash
uv run pytest
```

Check the code:

```bash
uv run ruff check .
```

Format the code:

```bash
uv run ruff format .
```

---

## Contributing

Contributions are welcome.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

The contribution guide explains:

* Project structure
* Development setup
* Adding features
* Testing
* Code style
* Pull requests
* Commit conventions

Please also read [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## Security

If you discover a security vulnerability, please follow the instructions in [`SECURITY.md`](SECURITY.md) rather than publicly reporting sensitive details.

---

## License

This project is licensed under the terms specified in [`LICENSE`](LICENSE).

---

## Project Status

DC Custom Bot is currently under active development.

Features and internal APIs may change as the project evolves toward its first stable release.
