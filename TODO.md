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

---

## Implemented Feature Groups

### General
* [x] Connectivity diagnostic command (`/ping`)
* [x] Application owner shutdown command (`!shutdown`)

### Administration
* [x] Server administrative overview command (`/serverinfo`)
* [x] Bot administrative status command (`/botinfo`)
* [x] Server configuration settings command (`/server_settings`)
* [x] Administrative permission checks (`manage_guild`)

### Moderation
* [x] Kick member command (`/kick`)
* [x] Ban member command (`/ban`)
* [x] Unban user command (`/unban`)
* [x] Temporary member timeout command (`/timeout`)
* [x] Bulk message purge command (`/purge` - up to 1,000 messages)
* [x] Formal direct message warning command (`/warn`)
* [x] Optional moderation reasons for all actions
* [x] Server-side Discord permission checks (`has_permissions`)
* [x] Role hierarchy protection (blocks targeting owner, bot, or equal/higher roles)
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
* [x] JSON-based welcome embed template ([`src/features/welcome/embed.json`](src/features/welcome/embed.json))
* [x] Dynamic channel mention placeholders (`{rules}`, `{roles}`, `{general}`, `{support}`)

### AI Assistant
* [x] Conversational AI command (`/ask`)
* [x] Reset personal conversation history (`/clear`)
* [x] Primary AI provider: OpenAI (`gpt-5-mini`)
* [x] Automatic fallback provider: Google Gemini (`gemini-2.5-flash`)
* [x] Per-user in-memory conversation history
* [x] Concise and direct system instructions
* [x] Safe error messaging when API keys are unconfigured

---

## In Progress

### Music
* [ ] Voice channel connection and lifecycle management
* [ ] Audio streaming via yt-dlp and FFmpeg
* [ ] Play command with YouTube search (`/play`)
* [ ] Random music discovery command (`/random`)
* [ ] Playback controls (`/pause`, `/resume`, `/skip`, `/stop`)
* [ ] Queue display command (`/queue`)
* [ ] Volume adjustment command (`/volume`)
* [ ] Interactive player view with button controls (`/player`)
* [ ] Voice disconnect command (`/leave`)
* [ ] 24/7 continuous voice connection mode (`/247`)
* [ ] Automatic audio cache cleanup

---

## Planned Work

### Database & Persistence
* [ ] Active PostgreSQL persistent storage integration
* [ ] SQLAlchemy 2.0 async session integration in feature Cogs
* [ ] Alembic schema migrations workflow for production
* [ ] Guild configuration model (custom prefix, custom log channels)
* [ ] Moderation case log model (case IDs, infraction history, timestamps)

### Advanced Moderation
* [ ] Warning history inspection command
* [ ] Channel lockdown commands (`/lock`, `/unlock`)
* [ ] Slowmode management command
* [ ] Dedicated moderation log channel
* [ ] Automated spam and invite link filtering

### Advanced Welcome
* [ ] Automatic member join event listener
* [ ] Member leave announcement listener
* [ ] Server-configurable welcome channel
* [ ] Auto-role assignment for new members
* [ ] Dynamic banner image generation

### Support Tickets
* [ ] Ticket creation panel and buttons
* [ ] Private ticket channel management
* [ ] Ticket claim and close workflows
* [ ] Transcript generation and logging

### Mini-Games
* [ ] Coin flip command
* [ ] Dice roll command
* [ ] Rock Paper Scissors command
* [ ] 8-Ball command
* [ ] Trivia command

---

## Documentation & Repository

* [x] Beginner-friendly [README.md](README.md)
* [x] Discord Developer Portal setup & credentials guide ([README.md](README.md#discord-bot-setup--credentials-guide))
* [x] Contributor guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)
* [x] Community standards in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
* [x] Vulnerability reporting in [SECURITY.md](SECURITY.md)
* [x] Architectural notes in [docs/database.md](docs/database.md)
* [x] Open source license in [LICENSE](LICENSE)
