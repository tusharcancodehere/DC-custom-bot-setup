# Project Roadmap & TODO

This document tracks completed milestones, current features, and future plans for **DC Custom Bot**.

All active features are beginner-friendly, fully multi-server compatible, and globally synchronized.

---

## Foundation

* [x] Create bot core ([`src/core/bot.py`](src/core/bot.py))
* [x] Load environment variables ([`src/core/config.py`](src/core/config.py))
* [x] Implement Discord client with auto-reconnect
* [x] Dynamic Cog discovery and loading ([`src/core/loader.py`](src/core/loader.py))
* [x] Global slash command synchronization
* [x] Global error handling ([`src/core/errors.py`](src/core/errors.py))
* [x] Application logging with stdout support ([`src/core/logging.py`](src/core/logging.py))
* [x] Permission checks and decorators ([`src/core/permissions.py`](src/core/permissions.py))
* [x] Common Discord UI views and buttons ([`src/views/common.py`](src/views/common.py))

---

## Database

* [x] Configure PostgreSQL connection environment ([`src/database/database.py`](src/database/database.py))
* [x] Configure SQLAlchemy 2.0 async engine and sessionmaker
* [x] Configure asyncpg driver support
* [x] Configure Alembic database migration environment ([`alembic/`](alembic/))
* [x] Create initial database models ([`src/database/models.py`](src/database/models.py))
* [x] Create migration workflow ([`alembic/versions/001_create_user_xp_table.py`](alembic/versions/001_create_user_xp_table.py))
* [x] Add user XP model (`UserXP`)
* [x] Safe database connection testing and graceful degradation if offline
* [ ] Add guild configuration model (custom prefix, log channels)
* [ ] Add moderation log model (case history, warnings)

---

## Moderation

* [x] Ban command (`/ban`)
* [x] Unban command (`/unban`)
* [x] Kick command (`/kick`)
* [x] Timeout command (`/timeout`)
* [x] Direct message warning (`/warn`)
* [x] Bulk message purge (`/purge` - up to 1,000 messages)
* [ ] Warning history inspection
* [ ] Lock and unlock channel commands
* [ ] Slowmode management
* [ ] Server moderation logging channel
* [ ] Automated spam and invite link filtering

---

## Welcome

* [x] Welcome announcement command (`/welcome`)
* [x] Custom welcome embed template ([`src/features/welcome/embed.json`](src/features/welcome/embed.json))
* [ ] Automatic new member join listener
* [ ] Member leave announcement
* [ ] Welcome channel configuration per server
* [ ] Auto-role assignment for new members
* [ ] Dynamic welcome banner image generator

---

## Level System

* [x] Persistent PostgreSQL XP tracking ([`src/database/models.py`](src/database/models.py))
* [x] Automatic message XP rewards (15–25 XP per eligible message)
* [x] Anti-spam message cooldown (60 seconds per user per server)
* [x] Level calculation formula (`100 * (level ^ 1.5)`)
* [x] Interactive rank card command (`/level`)
* [x] Text rank command (`/rank`)
* [x] Server top 10 leaderboard (`/leaderboard`)
* [x] Detailed XP breakdown command (`/show_xp`)
* [x] Admin XP management (`/add_xp`, `/remove_xp`, `/set_xp`)
* [x] Level-up announcement messages in chat
* [x] Customizable level embed styling ([`src/features/levels/embed.json`](src/features/levels/embed.json))
* [x] Graceful degradation if database is not configured
* [ ] Custom level role rewards
* [ ] Server-specific XP multipliers

---

## Music

* [x] Voice channel connection and management
* [x] Audio streaming via yt-dlp and FFmpeg
* [x] Play command with YouTube search (`/play`)
* [x] Random music discovery playback (`/random`)
* [x] Pause playback (`/pause`)
* [x] Resume playback (`/resume`)
* [x] Skip current track (`/skip`)
* [x] Stop and clear queue (`/stop`)
* [x] Queue display (`/queue`)
* [x] Volume adjustment (`/volume`)
* [x] Interactive player view with controls (`/player`)
* [x] Disconnect from voice (`/leave`)
* [x] 24/7 continuous voice connection mode (`/247`)
* [x] Automatic queue and cache file cleanup

---

## AI Assistant

* [x] Primary OpenAI integration (`gpt-5-mini`)
* [x] Automatic Google Gemini fallback (`gemini-2.5-flash`)
* [x] Multi-turn conversational AI command (`/ask`)
* [x] Reset conversation history (`/clear`)
* [x] Context limits and response chunking for Discord limits
* [x] Friendly error handling when API keys are unconfigured
* [ ] AI moderation helper
* [ ] AI support ticket assistant

---

## Deployment & Hosting

* [x] Single entrypoint (`python src/main.py` / `uv run python src/main.py`)
* [x] Production containerization ([`Dockerfile`](Dockerfile) & [`.dockerignore`](.dockerignore))
* [x] Hosting panel support with standalone dependencies ([`requirements.txt`](requirements.txt))
* [x] Fail-fast environment validation ([`src/core/config.py`](src/core/config.py))
* [x] Clean standard output logging for hosting consoles
* [x] Graceful shutdown handling (`SIGINT`, `SIGTERM`, and `!shutdown`)
* [x] Comprehensive deployment documentation in [`README.md`](README.md)
* [ ] Docker Compose setup for local PostgreSQL + Bot

---

## Documentation

* [x] Beginner-friendly [README.md](README.md)
* [x] Contributor guidelines in [CONTRIBUTING.md](CONTRIBUTING.md)
* [x] Community standards in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
* [x] Vulnerability reporting in [SECURITY.md](SECURITY.md)
* [x] Database and migrations guide in [docs/database.md](docs/database.md)
* [x] Open source license in [LICENSE](LICENSE)

---

## Future Roadmap

* [ ] Reaction role menus
* [ ] Community poll system
* [ ] Server giveaways
* [ ] Scheduled reminders
* [ ] Support ticket panels and transcript exports
* [ ] Server statistics voice channels
* [ ] Web management dashboard
