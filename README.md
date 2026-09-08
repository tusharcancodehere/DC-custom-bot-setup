# DC Custom Bot

A beginner-friendly, modular open-source Discord bot built with Python 3.13 and [`discord.py`](https://github.com/Rapptz/discord.py).

DC Custom Bot provides server moderation, persistent leveling with PostgreSQL, music playback, dual-provider AI assistance, customizable welcome cards, and general utilities in a single, clean bot. It is designed to be fully multi-server compatible and hosting-ready: clone the repo, configure your token, and run!

---

## Current Status

> **Status:** Production-Ready Core & Active Development

All 28 slash commands are fully functional, globally synchronized, and tested across multiple servers simultaneously. Persistent XP storage uses PostgreSQL with SQLAlchemy 2.0 and Alembic (and safely degrades if a database is not configured). Voice playback uses `yt-dlp` and FFmpeg. Conversational AI supports OpenAI with automatic Google Gemini fallback. Track upcoming features in [`TODO.md`](TODO.md).

---

## Features

### 🛡️ Moderation
Server management commands with permission checks and role hierarchy protection:
* `/kick` — Kick a member from the server with an optional reason.
* `/ban` — Ban a member from the server with an optional reason.
* `/unban` — Unban a user by their Discord user ID.
* `/timeout` — Temporarily timeout a member for a duration in minutes.
* `/purge` — Bulk delete recent channel messages (1–1,000 messages).
* `/warn` — Send a formal direct message warning to a member.

### 🎵 Music
Voice channel audio playback and queue management powered by `yt-dlp` and FFmpeg:
* `/play` — Search YouTube or provide a direct audio URL to play in voice.
* `/random` — Play a randomly discovered music track from the internet.
* `/pause` — Pause current playback.
* `/resume` — Resume paused audio.
* `/skip` — Skip the current track to play the next song in the queue.
* `/stop` — Stop playback and clear the guild queue.
* `/queue` — View currently queued tracks with duration details.
* `/volume` — Adjust audio volume (0–100%).
* `/player` — Display an interactive music player with controls.
* `/leave` — Disconnect the bot from the voice channel.
* `/247` — Toggle 24/7 mode to keep the bot connected in voice even when idle.

### 🤖 AI Assistant
Conversational AI powered by dual providers with automated fallback:
* `/ask` — Send prompts to the AI assistant. Queries OpenAI (`gpt-5-mini`) first, automatically falling back to Google Gemini (`gemini-2.5-flash`) if OpenAI is unavailable.
* `/clear` — Reset your personal conversation history in the current server.

### 👋 Welcome System
Member greeting functionality:
* `/welcome` — Displays a formatted welcome embed loaded from [`embed.json`](src/features/welcome/embed.json) with dynamic channel mentions and server branding.

### 🆙 Level System
Activity and rank tracking components with persistent PostgreSQL storage:
* `/level` — Display a rank and level card with visual progress bars.
* `/rank` — View your server rank and experience.
* `/leaderboard` — View the top 10 most active members in the server.
* `/show_xp` — View the complete XP breakdown of a member.
* `/add_xp` — Add experience to a member (Admin).
* `/remove_xp` — Remove experience from a member without dropping below 0 (Admin).
* `/set_xp` — Set a member's experience directly (Admin).

### ⚙️ General & Utility
* `/ping` — Check bot connectivity, response latency, and operational status.
* `!shutdown` — Gracefully shut down the bot (restricted to the application owner).
* **Global Command Syncing** — Automatically registers and synchronizes slash commands globally across every Discord server where the bot is installed.

---

## Technology Stack

| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | `>= 3.11` | Core programming language |
| **discord.py** | `>= 2.7.1` | Discord API wrapper and bot framework |
| **SQLAlchemy** | `>= 2.0.52` | Modern asynchronous ORM and database toolkit |
| **asyncpg** | `>= 0.31.0` | High-performance PostgreSQL asynchronous driver |
| **Alembic** | `>= 1.19.1` | Database schema migrations |
| **yt-dlp** | `>= 2026.8.19` | Audio streaming and metadata extraction |
| **yt-dlp-ejs** | `>= 0.8.0` | JavaScript challenge solver for yt-dlp |
| **PyNaCl** | `>= 1.6.2` | Voice encryption library |
| **FFmpeg** | System binary | Audio decoding and transcode pipeline |
| **OpenAI SDK** | `>= 3.8.0` | OpenAI API client for AI assistant |
| **Google GenAI** | `>= 2.22.0` | Google Gemini API client for fallback AI assistant |
| **uv** | Latest | Fast Python package and dependency manager |

---

## Project Structure

```text
DC-custom-bot-setup/
├── src/
│   ├── main.py              # Single application entrypoint
│   ├── core/                # Core bot framework and shared services
│   │   ├── bot.py           # CustomBot class, setup_hook, on_ready sync, logging
│   │   ├── config.py        # Environment loading, startup validation, colors
│   │   ├── errors.py        # Global exception handling
│   │   ├── loader.py        # Cog discovery and loading
│   │   ├── logging.py       # Application logging utilities
│   │   └── permissions.py   # Permission checks and decorators
│   ├── features/            # Independent, modular bot features
│   │   ├── ai/              # AI assistant (/ask, /clear)
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # Persistent XP tracking and rank cards (/level, /rank, etc.)
│   │   ├── moderation/      # Moderation commands (/kick, /ban, /timeout, etc.)
│   │   ├── music/           # Audio playback, queues, and player (/play, /queue, etc.)
│   │   └── welcome/         # Welcome messages and templates (/welcome)
│   ├── views/               # Shared Discord UI components
│   │   └── common.py
│   └── database/            # Database engine, models, and session management
│       ├── database.py      # Async engine and session factory
│       └── models.py        # SQLAlchemy UserXP model
├── alembic/                 # Database schema migrations
│   ├── versions/            # Migration version scripts
│   └── env.py               # Async Alembic migration runner
├── docs/                    # Architectural and developer documentation
│   └── database.md          # Database setup and migration guide
├── requirements.txt         # Standalone pip dependencies for hosting panels
├── Dockerfile               # Production container definition
├── .dockerignore            # Container build exclusion rules
├── .env.example             # Configuration template with safe empty placeholders
├── .python-version          # Recommended Python version (3.13)
├── pyproject.toml           # Project metadata and dependencies
├── uv.lock                  # Pinned dependency lockfile
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Contributor Code of Conduct
├── SECURITY.md              # Security policy and disclosure process
├── TODO.md                  # Project roadmap and completed tasks
└── README.md                # Project documentation overview
```

---

## Discord Bot Setup & Credentials Guide

Follow these beginner-friendly steps to create your Discord bot in the developer portal, copy your credentials, enable required intents, and invite the bot to your server:

### Step 1: Open the Discord Developer Portal
1. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Log in with your Discord account if you are not already signed in.

### Step 2: Create a New Discord Application
1. Click the blue **New Application** button in the top-right corner.
2. Enter a name for your bot (e.g., `DC Custom Bot`).
3. Check the box to agree to Discord's Developer Terms of Service and Developer Policy.
4. Click **Create**.

### Step 3: Copy Your Application ID
1. In the left navigation sidebar, ensure you are on the **General Information** page.
2. Locate the field labeled **Application ID**.
3. Click the **Copy** button beneath the ID.
4. Keep this value handy — you will paste it as `APPLICATION_ID` in your `.env` file or hosting panel.

### Step 4: Create the Bot and Copy Your Bot Token
1. In the left sidebar, click on **Bot**.
2. Click the **Reset Token** button (or **Add Bot** if prompted) and confirm the prompt.
3. Click **Copy** to copy your bot token immediately.
   > [!IMPORTANT]
   > Discord only displays your bot token once! If you lose it or close the page, you will need to click **Reset Token** again. Never share this token with anyone or commit it to GitHub.
4. Keep this value handy — you will paste it as `DISCORD_TOKEN` in your `.env` file or hosting panel.

### Step 5: Enable Privileged Gateway Intents (Required)
The bot requires specific Discord Gateway Intents to listen for messages, award XP, and manage members:
1. Stay on the **Bot** page in the Developer Portal.
2. Scroll down to the section titled **Privileged Gateway Intents**.
3. Toggle the switch to **ON** for both:
   * **Server Members Intent** (required for member management, welcome cards, and permission checks)
   * **Message Content Intent** (required for awarding chat XP and reading command content)
4. Click the green **Save Changes** button at the bottom of the page.

### Step 6: Invite the Bot to Your Discord Server
1. In the left sidebar, navigate to **OAuth2** -> **URL Generator**.
2. Under the **Scopes** section, check the following boxes:
   * `bot`
   * `applications.commands` (required to register slash commands)
3. Under the **Bot Permissions** section that appears below, select either:
   * **Administrator** (recommended for testing or full server management), or:
   * Select specific permissions:
     * *General*: Manage Roles, Kick Members, Ban Members, Moderate Members, View Audit Log, Read Messages/View Channels.
     * *Text*: Send Messages, Send Messages in Threads, Manage Messages, Embed Links, Attach Files, Read Message History, Mention @everyone.
     * *Voice*: Connect, Speak, Use Voice Activity.
4. Scroll to the bottom of the page and copy the link from the **Generated URL** box.
5. Paste this URL into your web browser, select your target Discord server from the dropdown, and click **Authorize**.

---

## Setup & Deployment Options

### Configuration & Environment Variables

Copy the template to create your `.env` file (or configure these variables directly in your hosting panel):

```bash
cp .env.example .env
```

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | **Yes** | Discord Bot token generated from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `APPLICATION_ID` | **Yes** | Discord Application / Client ID from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `DATABASE_URL` | Optional | PostgreSQL connection string (`postgresql+asyncpg://...`). If omitted, database-backed features safely degrade. |
| `OPENAI_API_KEY` | Optional | OpenAI API key for `/ask` (`gpt-5-mini`). |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for `/ask` fallback (`gemini-2.5-flash`). |

> [!WARNING]
> Never commit your `.env` file or expose your bot token publicly.

---

### Option 1: Local Development (`uv`)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tusharcancodehere/DC-custom-bot-setup.git
   cd DC-custom-bot-setup
   ```
2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your DISCORD_TOKEN and APPLICATION_ID
   ```
3. **Install dependencies**:
   ```bash
   uv sync
   ```
4. **Run database migrations** (optional, if `DATABASE_URL` is set):
   ```bash
   uv run alembic upgrade head
   ```
5. **Start the bot**:
   ```bash
   uv run python src/main.py
   ```

---

### Option 2: Hosting Panels (Pterodactyl / FPS.ms / Generic VPS)

For bot hosting platforms that provide standard Python environments without `uv`:

1. **Upload or clone** the repository to your hosting server.
2. **Set environment variables** directly in the hosting panel (`DISCORD_TOKEN`, `APPLICATION_ID`, and optionally `DATABASE_URL`, etc.).
3. **Set the application entry point** to [`src/main.py`](src/main.py).
4. **Install dependencies** using the provided [`requirements.txt`](requirements.txt):
   ```bash
   pip install -r requirements.txt
   ```
5. **Ensure FFmpeg is installed** on the host for voice/music capabilities.
6. **Apply migrations** (if using PostgreSQL):
   ```bash
   alembic upgrade head
   ```
7. **Start the bot**:
   ```bash
   python src/main.py
   ```

---

### Option 3: Containerized Hosting (Docker)

A production-ready [Dockerfile](Dockerfile) is included:

1. **Build the container image**:
   ```bash
   docker build -t dc-custom-bot-setup .
   ```
2. **Run the container**:
   ```bash
   docker run --env-file .env dc-custom-bot-setup
   ```

---

## Database & Migrations

The bot uses PostgreSQL with SQLAlchemy 2.0 and `asyncpg`. Schema migrations are managed through **Alembic**. Detailed database setup instructions are available in the [Database Guide](docs/database.md).

* **Apply latest migrations**:
  ```bash
  alembic upgrade head
  ```
* **Database Optionality**: If `DATABASE_URL` is not set or the database is unavailable, the bot starts normally and features requiring persistence (such as XP tracking) report:
  `"Database is not configured. Persistent XP is currently unavailable."`

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
