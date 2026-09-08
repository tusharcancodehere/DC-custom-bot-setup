# Project Roadmap & TODO

This document is the source of truth for project progress, tracking implemented features, in-progress modules, and future roadmap items for **DC Custom Bot**.

---

## Foundation (Completed)

* [x] Create bot core framework ([`src/core/bot.py`](src/core/bot.py))
* [x] Environment variable configuration & validation ([`src/core/config.py`](src/core/config.py))
* [x] Discord client initialization with auto-reconnect
* [x] Dynamic Cog discovery and loading ([`src/core/loader.py`](src/core/loader.py))
* [x] Global slash command synchronization
* [x] Global application error handling ([`src/core/errors.py`](src/core/errors.py))
* [x] Centralized application logging with stdout support ([`src/core/logging.py`](src/core/logging.py))
* [x] Reusable permission checks and role hierarchy decorators ([`src/core/permissions.py`](src/core/permissions.py))
* [x] Shared Discord UI components and views ([`src/views/common.py`](src/views/common.py))
* [x] Graceful shutdown handling (`SIGINT`, `SIGTERM`, `!shutdown`)
* [x] Multi-container orchestration via Docker Compose ([`docker-compose.yml`](docker-compose.yml))

---

## Implemented Feature Groups

### General
* [x] Connectivity diagnostic command (`/ping`)
* [x] Application owner shutdown command (`!shutdown`)

### Administration
* [x] Server administrative overview command (`/serverinfo`)
* [x] Bot administrative status command (`/botinfo`)
* [x] Server configuration settings overview command (`/server_settings`)
* [x] Moderation log channel configuration command (`/set_modlog_channel`)
* [x] Official server announcement command (`/announce`)
* [x] Administrative permission checks (`manage_guild`)

### Moderation
* [x] Kick member command (`/kick`)
* [x] Ban member command (`/ban`)
* [x] Unban user command (`/unban`)
* [x] Temporary member timeout command (`/timeout`)
* [x] Bulk message purge command (`/purge` - up to 1,000 messages)
* [x] Formal direct message warning command (`/warn`)
* [x] Warning history inspection command (`/warnings`)
* [x] Clear member warnings command (`/clear_warnings`)
* [x] Channel lockdown and restore commands (`/lock`, `/unlock`)
* [x] Channel slowmode management command (`/slowmode`)
* [x] Optional moderation reasons for all actions
* [x] Server-side Discord permission checks (`has_permissions`)
* [x] Role hierarchy protection across all moderation actions (owner, bot, equal/higher roles)
* [x] Direct message delivery to warned members

### Level System
* [x] Multi-server isolated XP tracking
* [x] Random message XP rewards (15–25 XP per message)
* [x] Anti-spam message cooldown (60 seconds per user per server)
* [x] Level calculation formula and progress bars
* [x] Interactive rank card commands (`/level`, `/rank`)
* [x] Server top 10 leaderboard command (`/leaderboard`)
* [x] Detailed XP breakdown command (`/show_xp`)
* [x] Admin XP management commands (`/add_xp`, `/remove_xp`, `/set_xp`)
* [x] Level-up announcement messages in chat
* [x] Customizable rank card embed styling ([`src/features/levels/embed.json`](src/features/levels/embed.json))

### Welcome
* [x] Welcome announcement command (`/welcome`)
* [x] Server-configurable welcome channel command (`/set_welcome_channel`)
* [x] Automatic member join event listener (`on_member_join`)
* [x] Member leave announcement listener (`on_member_remove`)
* [x] JSON-based welcome embed template ([`src/features/welcome/embed.json`](src/features/welcome/embed.json))
* [x] Dynamic channel mention placeholders (`{rules}`, `{roles}`, `{announcements}`, `{general}`, `{support}`)

### AI Assistant
* [x] Conversational AI command (`/ask`)
* [x] Reset personal conversation history (`/clear`)
* [x] Primary AI provider: OpenAI (`gpt-5-mini` with chat completions fallback)
* [x] Automatic fallback provider: Google Gemini (`gemini-2.5-flash` via thread pool)
* [x] Multi-turn conversation retention with history bounding
* [x] Safe message chunking for long responses (>1900 chars)
* [x] Strict `(guild_id, user_id)` conversation isolation
* [x] Concise and direct system instructions
* [x] Safe error messaging and unfulfilled prompt rollback when providers fail

---

### Music
* [x] Voice channel connection and lifecycle management
* [x] Audio streaming via yt-dlp and FFmpeg
* [x] Play command with YouTube search (`/play`)
* [x] Random music discovery command (`/random`)
* [x] Playback controls (`/pause`, `/resume`, `/skip`, `/stop`)
* [x] Queue display command (`/queue`)
* [x] Volume adjustment command (`/volume`)
* [x] Interactive player view with button controls (`/player`)
* [x] Voice disconnect command (`/leave`)
* [x] 24/7 continuous voice connection mode (`/247`)
* [x] Automatic audio cache cleanup

### Support Tickets
* [x] Interactive ticket launch panel (`/ticket_panel`)
* [x] Persistent "Create Ticket" button view (`TicketLaunchView`)
* [x] Automated private support channel creation with permission overwrites
* [x] Duplicate ticket prevention per user per server
* [x] In-channel ticket controls (`TicketControlView` with Close & Delete)
* [x] Staff slash commands (`/ticket_close`, `/ticket_delete`)

### Mini-Games
* [x] Coin flip command with prediction option (`/coinflip`)
* [x] Dice roll command supporting multi-dice and dice notation (`/roll`)
* [x] Magic 8-Ball oracle command (`/8ball`)
* [x] Rock, Paper, Scissors game against bot (`/rps`)
* [x] Interactive multiple-choice trivia challenge with buttons (`/trivia`)

### Database & Persistence
* [x] Active PostgreSQL persistent storage integration
* [x] SQLAlchemy 2.0 async session integration in feature Cogs
* [x] Alembic schema migrations workflow for production ([`alembic/versions/`](alembic/versions/))
* [x] Guild configuration model (`GuildConfig` with custom welcome & mod-log channels)
* [x] Moderation case log model (`ModerationCase` with infraction history, actions, reasons, and timestamps)
* [x] User experience model (`UserXP` with per-server isolation and rank tracking)
* [x] Comprehensive database and graceful degradation test suite ([`tests/test_database.py`](tests/test_database.py))

---

## Planned Work

### Advanced Moderation
* [ ] Automated spam and invite link filtering

### Advanced Welcome
* [ ] Auto-role assignment for new members
* [ ] Dynamic banner image generation

---

## Documentation & Repository

* [x] Beginner-friendly [README.md](README.md)
* [x] Discord Developer Portal setup & credentials guide ([README.md](README.md#discord-bot-setup--credentials-guide))
* [x] Contributor guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)
* [x] Community standards in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
* [x] Vulnerability reporting in [SECURITY.md](SECURITY.md)
* [x] Architectural notes in [docs/database.md](docs/database.md)
* [x] Open source license in [LICENSE](LICENSE)
