# DC Custom Bot

A beginner-friendly, modular open-source Discord bot built with Python and [`discord.py`](https://github.com/Rapptz/discord.py).

DC Custom Bot is a coherent, feature-complete open-source Discord bot providing server moderation, administration tools, dual-provider conversational AI, audio streaming, multi-server leveling, customizable welcome embeds, and general utilities in a clean, non-overengineered architecture.

---

## Current Status

> **Status:** Feature-Complete & Production-Ready Open-Source Discord Bot

All core features, mini-games, ticket support channels, PostgreSQL persistence with Alembic migrations, and multi-container Docker Compose environments are fully implemented, tested, and ready for production deployment. Automated continuous integration runs via GitHub Actions.

Track upcoming features and active milestones in [`TODO.md`](TODO.md).

---

## Implemented Features

### 🛡️ Moderation
Member and message moderation commands equipped with permission checks, role hierarchy validation, and direct message notifications:
* `/kick` — Kick a member from the server with an optional reason.
* `/ban` — Ban a member from the server with an optional reason.
* `/unban` — Unban a user by their Discord user ID with an optional reason.
* `/timeout` — Temporarily timeout a member for a specified duration in minutes with an optional reason.
* `/purge` — Bulk delete recent channel messages (1–1,000 messages).
* `/warn` — Send a formal direct message warning to a member, recording the incident in their server history.
* `/warnings` — View full warning history and case log for a member in this server.
* `/clear_warnings` — Clear all recorded warnings for a member in this server.
* `/lock` — Lock a text channel to prevent regular members from sending messages.
* `/unlock` — Unlock a locked text channel, restoring member chat permissions.
* `/slowmode` — Configure or disable chat cooldown delay for a channel (up to 6 hours).
* **Security & Hierarchy Checks**: Prevents actions against server owners, the bot itself, or members with equal or higher roles across all moderation commands. Enforces server-side permissions (`has_permissions`).

### 👑 Administration
Server and bot administrative tools (kept strictly separate from member punishments):
* `/serverinfo` — View comprehensive administrative details about the current server (Members, Channels, Roles, Owner, Creation date).
* `/botinfo` — View bot runtime statistics, connected servers count, latency, and system status.
* `/server_settings` — View current administrative settings and bot configuration for the guild (Rules channel, System channel, Welcome channel, Mod Log channel).
* `/set_modlog_channel` — Designate or view the text channel where moderation actions and disciplinary records are automatically logged.
* `/announce` — Post a formatted, official announcement embed to a designated server channel with staff attribution.
* **Access Control**: Enforces `manage_guild` permissions with clear, friendly error feedback.

### 🆙 Level System
Server activity and XP system designed for clean multi-server operation:
* `/level` — Display your rank card with current level, XP, and visual progress bar.
* `/rank` — Alias to view your server rank and experience.
* `/leaderboard` — View the top 10 most active members in the current server.
* `/show_xp` — View detailed experience breakdown and progress toward the next level milestone.
* `/add_xp` — Add experience points to a member (Admin).
* `/remove_xp` — Remove experience points from a member without dropping below 0 (Admin).
* `/set_xp` — Set a member's experience points directly (Admin).
* **Multi-Server Isolation**: XP is strictly isolated per server and user. Member XP in Server A never affects Server B. Includes 60-second anti-spam cooldowns and level-up celebration messages.

### 🤖 AI Assistant
Conversational AI powered by dual providers with automated fallback:
* `/ask` — Send prompts and questions to the AI assistant. Queries OpenAI (`gpt-5-mini`) as the primary provider with chat completions fallback, automatically falling back to Google Gemini (`gemini-2.5-flash`) via an asynchronous worker thread if OpenAI is unavailable.
* `/clear` — Reset your personal in-memory conversation history in the current server.
* **Context & Formatting**: Maintains per-server, per-user in-memory conversation history with token bounding, instructs models to provide concise and direct responses, and safely splits long responses across Discord message length limits (>1900 chars).

### 👋 Welcome System
Server greeting and onboarding announcements:
* `/welcome` — Displays a formatted welcome embed loaded from [`embed.json`](src/features/welcome/embed.json).
* `/set_welcome_channel` — Configure or view the designated channel for automatic welcome messages (`Manage Server` permission required).
* **Automatic Join & Leave Events**: Greets incoming members automatically with their avatar, server name, and channel mentions; posts polite farewell notifications on member leave.
* **Dynamic Placeholders**: Supports clickable Discord channel placeholders such as `{rules}`, `{roles}`, `{announcements}`, `{general}`, and `{support}` that resolve to server channels dynamically.

### 🎵 Music Streaming
High-quality voice channel audio streaming powered by `yt-dlp` and FFmpeg with interactive controls:
* `/play` — Search YouTube or stream directly from a web URL into your voice channel.
* `/random` — Discover and play a random music track from popular genres (lo-fi, jazz, synthwave, acoustic, rock).
* `/player` — Display an interactive player dashboard with Discord button controls (Pause/Resume, Skip, Stop, 24/7, Leave).
* `/pause` & `/resume` — Pause and resume audio playback.
* `/skip` — Advance to the next queued track.
* `/stop` — Stop playback and clear the guild queue.
* `/queue` — View the current queue of upcoming tracks and playback progress.
* `/volume` — Adjust playback loudness between 0% and 100%.
* `/leave` — Disconnect the bot from voice and clear the queue.
* `/247` — Toggle 24/7 continuous voice connection mode.
* **Resilient Audio Pipeline**: Runs yt-dlp in a background worker thread, cleans cached audio upon completion, and translates streaming errors into helpful user messages.

### 🎫 Support Tickets
Interactive private ticket channel management for member assistance:
* `/ticket_panel` — Post the interactive ticket creation panel with the "Create Ticket" button (`Manage Server` permission required).
* `/ticket_close` — Close the current ticket channel and restrict member sending permissions.
* `/ticket_delete` — Permanently delete a closed ticket channel (`Manage Channels` permission required).
* **Automated Isolation & Overwrites**: Configures private channel permissions hiding tickets from `@everyone` while granting access only to the ticket opener and server staff. Prevents duplicate open tickets per user.

### 🎲 Mini-Games
Interactive server entertainment and casual games:
* `/coinflip` — Flip a coin with an optional guess (`heads` or `tails`) to test your prediction skills.
* `/roll` — Roll dice supporting custom sides (e.g. `20`) or standard tabletop dice notation (e.g. `2d6`, `3d20`).
* `/8ball` — Consult the classic Magic 8-Ball oracle for predictions and guidance.
* `/rps` — Play Rock, Paper, Scissors directly against the bot with win, loss, and tie detection.
* `/trivia` — Test your knowledge with interactive multiple-choice trivia questions featuring clickable buttons.

### 🗄️ Database & Persistence
PostgreSQL storage with SQLAlchemy 2.0 async sessions and Alembic schema migrations:
* **Persistent XP & Leveling**: User XP and levels are stored in PostgreSQL (`user_xp` table) and survive bot restarts.
* **Server Configurations**: Welcome channel and moderation log channel settings are persisted in PostgreSQL (`guild_config` table).
* **Moderation Audit Log**: Member warnings and disciplinary cases are tracked in PostgreSQL (`moderation_cases` table).
* **Graceful Degradation**: If `DATABASE_URL` is omitted or PostgreSQL is offline, all features continue functioning seamlessly using in-memory caches.
* See [docs/database.md](docs/database.md) for architecture, setup options, and schema migrations.

### ⚙️ General & Utility
Core maintenance and diagnostic commands:
* `/ping` — Check bot connectivity, WebSocket response latency, and operational status.
* `!shutdown` — Gracefully shut down the bot (restricted to the application owner).
* **Global Syncing**: Automatically registers and synchronizes slash commands globally across servers where the bot is installed.

---

## Planned Features

The following features are planned on our roadmap:

* **🛡️ Advanced Moderation**: Automated spam filtering, invite link blocking, and customizable auto-moderation rules.
* **👋 Advanced Welcome**: Automated role assignment on member join and dynamic banner generation.

---

## Technology Stack

| Technology | Purpose | Documentation |
| :--- | :--- | :--- |
| **Python** (`>= 3.11`) | Core programming language | [Python Docs](https://docs.python.org/3/) |
| **discord.py** (`>= 2.7.1`) | Modern Discord API wrapper | [discord.py Docs](https://discordpy.readthedocs.io/) |
| **OpenAI SDK** (`>= 3.8.0`) | Primary AI provider for `/ask` | [OpenAI Docs](https://platform.openai.com/docs) |
| **Google GenAI** (`>= 2.22.0`) | Fallback AI provider for `/ask` | [Google GenAI Docs](https://ai.google.dev/) |
| **uv** | Fast Python package and project manager | [uv Docs](https://docs.astral.sh/uv/) |
| **SQLAlchemy / asyncpg / Alembic** | Database dependencies (for planned persistence) | [SQLAlchemy Docs](https://docs.sqlalchemy.org/) |
| **yt-dlp / FFmpeg** | Audio streaming dependencies | [yt-dlp Docs](https://github.com/yt-dlp/yt-dlp) |

---

## Project Structure

```text
DC-custom-bot-setup/
├── src/
│   ├── main.py              # Application entrypoint
│   ├── core/                # Core bot framework and shared services
│   │   ├── bot.py           # CustomBot class, bot lifecycle, command sync
│   │   ├── config.py        # Environment loading & startup validation
│   │   ├── errors.py        # Global exception handling
│   │   ├── loader.py        # Dynamic Cog discovery and loading
│   │   ├── logging.py       # Centralized application logging
│   │   └── permissions.py   # Permission checks and decorators
│   ├── features/            # Modular bot features
│   │   ├── admin/           # Administrative tools (/serverinfo, /botinfo, /announce)
│   │   ├── ai/              # AI assistant (/ask, /clear)
│   │   ├── games/           # Mini-games (/coinflip, /roll, /8ball, /rps, /trivia)
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # Level system (/level, /rank, /leaderboard)
│   │   ├── moderation/      # Moderation commands (/kick, /ban, /timeout, /purge, /warn)
│   │   ├── music/           # Music streaming (/play, /player, /queue)
│   │   ├── tickets/         # Support ticket system (/ticket_panel, /ticket_close)
│   │   └── welcome/         # Welcome announcements & member events (/welcome)
│   ├── views/               # Shared Discord UI components
│   │   └── common.py
│   └── database/            # Database engine and models (for planned persistence)
│       ├── database.py      # Async engine and session factory
│       └── models.py        # SQLAlchemy models
├── alembic/                 # Database schema migrations (planned)
├── docs/                    # Architectural and database guides
│   └── database.md
├── requirements.txt         # Standalone pip requirements for standard hosting
├── Dockerfile               # Production container definition
├── .dockerignore            # Container build exclusion rules
├── .env.example             # Configuration template with placeholder values
├── pyproject.toml           # Project dependencies and tool configuration
├── uv.lock                  # Pinned dependency lockfile
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
├── CODE_OF_CONDUCT.md       # Contributor Code of Conduct
├── SECURITY.md              # Security policy and disclosure process
├── TODO.md                  # Project roadmap and completed tasks
└── README.md                # Project overview
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
4. Save this value — you will paste it as `APPLICATION_ID` in your `.env` file or hosting panel.

### Step 4: Create the Bot and Copy Your Bot Token
1. In the left sidebar, click on **Bot**.
2. Click the **Reset Token** button (or **Add Bot** if prompted) and confirm the prompt.
3. Click **Copy** to copy your bot token immediately.
   > [!IMPORTANT]
   > Discord only displays your bot token once! If you lose it or close the page, you will need to click **Reset Token** again. Never share this token with anyone or commit it to GitHub.
4. Save this value — you will paste it as `DISCORD_TOKEN` in your `.env` file or hosting panel.

### Step 5: Enable Privileged Gateway Intents (Required)
The bot requires specific Discord Gateway Intents to listen for messages, award XP, and manage members:
1. Stay on the **Bot** page in the Developer Portal.
2. Scroll down to the section titled **Privileged Gateway Intents**.
3. Toggle the switch to **ON** for both:
   * **Server Members Intent** (required for member management, welcome cards, and permission checks)
   * **Message Content Intent** (required for reading command content and chat messages)
4. Click the green **Save Changes** button at the bottom of the page.

### Step 6: Invite the Bot to Your Discord Server
1. In the left sidebar, navigate to **OAuth2** -> **URL Generator**.
2. Under the **Scopes** section, check the following boxes:
   * `bot`
   * `applications.commands`
3. Under the **Bot Permissions** section that appears below, select the necessary permissions (e.g., Administrator for full functionality).
4. Scroll to the bottom of the page and copy the link from the **Generated URL** box.
5. Paste this URL into your web browser, select your target Discord server from the dropdown, and click **Authorize**.

---

## Setup & Running

### Configuration & Environment Variables

Create your local `.env` file from the example template:

```bash
cp .env.example .env
```

| Variable | Required | Description |
| :--- | :---: | :--- |
| `DISCORD_TOKEN` | **Yes** | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `APPLICATION_ID` | **Yes** | Application / Client ID from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `OPENAI_API_KEY` | Optional | OpenAI API key for `/ask` (`gpt-5-mini`). |
| `GEMINI_API_KEY` | Optional | Google Gemini API key for `/ask` fallback (`gemini-2.5-flash`). |
| `DATABASE_URL` | Optional | PostgreSQL connection string (`postgresql+asyncpg://...`) for planned persistence. |

> [!WARNING]
> Never commit your `.env` file or expose your bot token publicly.

---

### Option 1: Local Development (`uv` - Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tusharcancodehere/DC-custom-bot-setup.git
   cd DC-custom-bot-setup
   ```
2. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your DISCORD_TOKEN and APPLICATION_ID
   ```
3. **Install dependencies**:
   ```bash
   uv sync
   ```
4. **Start the bot**:
   ```bash
   uv run python src/main.py
   ```

---

### Option 2: Standard Python (`pip`)

For environments without `uv`:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tusharcancodehere/DC-custom-bot-setup.git
   cd DC-custom-bot-setup
   ```
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your DISCORD_TOKEN and APPLICATION_ID
   ```
5. **Start the bot**:
   ```bash
   python src/main.py
   ```

---

### Option 3: Docker Container

A [Dockerfile](Dockerfile) is included for containerized environments:

1. **Build the container image**:
   ```bash
   docker build -t dc-custom-bot-setup .
   ```
2. **Run the container**:
   ```bash
   docker run --env-file .env dc-custom-bot-setup
   ```

---

### Option 4: Docker Compose (Bot + PostgreSQL)

A [`docker-compose.yml`](docker-compose.yml) is included to run the bot alongside a healthy, persistent PostgreSQL database container:

1. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your DISCORD_TOKEN and APPLICATION_ID
   ```
2. **Start the bot and database**:
   ```bash
   docker compose up -d
   ```
3. **View live logs**:
   ```bash
   docker compose logs -f bot
   ```
4. **Stop the stack**:
   ```bash
   docker compose down
   ```

---

## Verification & Code Quality

Verify that all Python source files compile cleanly and tests pass:

* **Compile check**:
  ```bash
  uv run python -m compileall -q src
  ```
* **Run test suite**:
  ```bash
  uv run python -m unittest discover -s tests -v
  ```

---

## Contributing

Contributions from the open-source community are warmly welcomed!

* Please read our [**Contributing Guide**](CONTRIBUTING.md) for local development conventions, coding standards, and how to submit focused pull requests.
* All participants must abide by our [**Code of Conduct**](CODE_OF_CONDUCT.md).

---

## Security

If you discover a security vulnerability, please do **not** report it via public GitHub issues or chat. Refer to our [**Security Policy**](SECURITY.md) for instructions on confidential reporting.

---

## License

This project is licensed under the terms of the [**MIT License**](LICENSE).

Copyright (c) 2026 Tushar Verma.
