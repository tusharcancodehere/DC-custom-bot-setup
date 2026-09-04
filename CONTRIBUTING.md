# Contributing to DC Custom Bot

Thank you for contributing to DC Custom Bot!

DC Custom Bot is a modular, open-source Discord bot built with Python. The project is intentionally kept simple so contributors can understand the codebase quickly and add features without unnecessary architectural complexity.

This document explains the project structure, development workflow, and guidelines for contributing.

---

## Project Structure

```text
DC-custom-bot-setup/
│
├── src/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── bot.py
│   │   ├── config.py
│   │   ├── loader.py
│   │   ├── errors.py
│   │   ├── logging.py
│   │   └── permissions.py
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   └── cog.py
│   │   ├── moderation/
│   │   ├── tickets/
│   │   ├── welcome/
│   │   ├── levels/
│   │   ├── games/
│   │   ├── music/
│   │   └── ai/
│   │
│   ├── views/
│   │   ├── __init__.py
│   │   └── common.py
│   │
│   └── database/
│       ├── __init__.py
│       └── database.py
│
├── tests/
├── docs/
├── alembic/
├── scripts/
│
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
├── README.md
├── SECURITY.md
├── TODO.md
├── mise.toml
├── pyproject.toml
└── uv.lock
```

The structure is intentionally lightweight. Do not create additional layers, folders, or abstractions unless they solve a real problem.

---

# `src/`

This contains the application's Python source code.

Most bot functionality should live inside this directory.

---

## `src/main.py`

The application's entry point.

It is responsible for starting the application and should remain small.

Typical flow:

```text
main.py
   ↓
Load configuration
   ↓
Initialize required systems
   ↓
Create bot
   ↓
Load features
   ↓
Start bot
```

Avoid putting feature-specific logic inside `main.py`.

---

# `src/core/`

`core/` contains functionality that belongs to the bot itself rather than to a specific feature.

Think:

> **How does the bot work?**

rather than:

> **What does the bot do?**

### `bot.py`

Contains the main Discord bot/client configuration.

Examples:

* Discord intents
* Bot initialization
* Global bot configuration
* Startup/shutdown behavior
* Command tree setup

Do not put feature-specific commands here.

---

### `config.py`

Handles application configuration and environment variables.

Examples:

```text
DISCORD_TOKEN
DATABASE_URL
OPENAI_API_KEY
```

Secrets must never be hardcoded.

Use `.env` locally and `.env.example` to document required variables.

---

### `loader.py`

Responsible for discovering/loading bot features and their Cogs.

The goal is that adding a new feature should not require manually maintaining a huge list of imports.

---

### `errors.py`

Contains shared error handling and custom exceptions.

Examples:

```text
Command errors
Permission errors
Configuration errors
Database errors
API errors
```

Feature-specific errors can remain inside the feature when appropriate.

---

### `logging.py`

Contains shared logging configuration.

Use this for application logs, errors, and other internal diagnostics.

Do not use logging as a replacement for Discord moderation logs; those are feature behavior and should live in the appropriate feature.

---

### `permissions.py`

Contains reusable permission and authorization checks.

Examples:

```text
Administrator
Moderator
Manage Messages
Manage Channels
Bot owner
```

Feature-specific permission requirements should use these shared checks where possible.

---

# `src/features/`

This is where the actual bot functionality lives.

Think:

> **What does the bot do?**

Each major bot system gets its own feature directory.

Current features:

```text
admin/
moderation/
tickets/
welcome/
levels/
games/
music/
ai/
```

A contributor adding a completely new feature should normally create a new directory here.

For example:

```text
src/features/reminders/
```

---

# Feature Structure

A simple feature initially looks like:

```text
src/features/tickets/
├── __init__.py
└── cog.py
```

### `cog.py`

The Discord-facing part of the feature.

It contains things such as:

* Slash commands
* Discord event handlers
* Buttons
* Select menus
* Modals
* Feature-specific listeners

Example:

```text
/ticket create
/ticket close
/ticket claim
```

Keep the Cog focused on receiving Discord interactions and passing work to the appropriate logic.

---

## Growing a Feature

Do not create a large number of files just because the project structure allows it.

Start simple:

```text
tickets/
├── __init__.py
└── cog.py
```

If the feature becomes large enough to justify separation, it can grow naturally:

```text
tickets/
├── __init__.py
├── cog.py
├── service.py
└── views.py
```

For example:

* `cog.py` → Discord commands/events
* `service.py` → ticket business logic
* `views.py` → buttons, menus, and modals

Only introduce these files when they provide a meaningful separation.

---

# `src/views/`

Contains reusable Discord UI components that are shared across multiple features.

Examples:

```text
Buttons
Select menus
Modals
Reusable views
```

Feature-specific UI can remain inside the feature.

For example:

```text
tickets/views.py
```

is preferable to putting every ticket-specific component into:

```text
src/views/
```

Use `src/views/` for UI that is genuinely shared.

---

# `src/database/`

Contains database-related code.

The project uses PostgreSQL.

Initially this directory may remain small:

```text
database/
├── __init__.py
└── database.py
```

As the database grows, it can be split when necessary.

For example:

```text
database/
├── connection.py
├── models.py
└── queries.py
```

Do not create a repository/service/model hierarchy unless the project actually needs it.

---

# `tests/`

Contains automated tests.

Tests should focus primarily on logic that can be tested without relying on a live Discord server.

Examples:

```text
Level calculations
XP calculations
Permission logic
Database operations
Ticket state changes
Game logic
Input validation
```

Keep tests organized similarly to the functionality they test when practical.

---

# `docs/`

Contains additional project documentation.

Possible documentation:

```text
Architecture
Configuration
Deployment
Database setup
Feature development
Bot permissions
Discord intents
Developer guides
```

The README should remain the quick introduction; detailed technical documentation can go here.

---

# `alembic/`

Contains PostgreSQL database migration files.

Whenever the database schema changes, create an appropriate Alembic migration.

Do not manually modify production databases without updating the migration history.

---

# `scripts/`

Contains small development or maintenance scripts.

Examples:

```text
Database setup
Development helpers
Data migration utilities
Maintenance commands
```

Scripts should not contain core bot functionality.

---

# Root Files

### `README.md`

The main project introduction.

It should explain:

* What the bot is
* Features
* Installation
* Basic configuration
* Running the bot
* Technology stack
* Basic contribution information

---

### `TODO.md`

The project's development roadmap.

Use it to track:

* Planned features
* Improvements
* Bug fixes
* Technical tasks

Keep it updated as work is completed or priorities change.

---

### `CONTRIBUTING.md`

This file explains how contributors should work on the project.

---

### `SECURITY.md`

Explains how security vulnerabilities should be reported.

Do not publicly post sensitive vulnerabilities as normal GitHub issues.

---

### `CODE_OF_CONDUCT.md`

Defines expected community behavior.

---

### `LICENSE`

Defines how the project's source code can be used, modified, and distributed.

---

### `pyproject.toml`

Contains Python project metadata and dependency configuration.

Use the project's package manager (`uv`) when adding or removing dependencies.

Do not manually edit generated dependency state unless necessary.

---

### `uv.lock`

Locks dependency versions for reproducible environments.

Normally, dependency changes should be made with:

```bash
uv add <package>
```

or:

```bash
uv remove <package>
```

and the lock file should be updated accordingly.

---

### `mise.toml`

Defines the project's development tool/version configuration.

The repository currently targets Python 3.13.

Contributors should use the project's configured versions rather than introducing arbitrary Python versions.

---

# Adding a New Feature

Suppose you want to add a reminder system.

Create:

```text
src/features/reminders/
├── __init__.py
└── cog.py
```

Then implement the feature inside the new module.

If the feature becomes more complex, expand it only as needed:

```text
src/features/reminders/
├── __init__.py
├── cog.py
├── service.py
└── views.py
```

If it requires persistent data, add the appropriate database changes and an Alembic migration.

---

# General Development Rules

### Keep Cogs focused

Cogs should primarily handle Discord interactions.

Avoid putting large amounts of unrelated business logic directly inside command methods.

---

### Avoid unnecessary abstraction

Do not create:

```text
services/
repositories/
factories/
managers/
controllers/
```

just because they are common patterns.

Introduce an abstraction when the current implementation has become difficult to maintain.

Simple code is preferred over architecture for architecture's sake.

---

### Keep features independent

A feature should avoid tightly coupling itself to unrelated features.

For example:

```text
tickets
```

should not directly depend on:

```text
games
```

Shared functionality belongs in `core/` or another clearly appropriate shared location.

---

### Reuse existing utilities

Before adding another helper, check whether the functionality already exists in:

```text
src/core/
src/views/
```

Avoid duplicated implementations.

---

### Don't hardcode secrets

Never commit:

```text
Discord bot tokens
API keys
Database passwords
Private credentials
```

Use environment variables instead.

---

# Development Setup

Clone the repository:

```bash
git clone <repository-url>
cd DC-custom-bot-setup
```

Install the configured Python version:

```bash
mise install
```

Install dependencies:

```bash
uv sync
```

Create the environment file:

```bash
cp .env.example .env
```

Configure the required values.

---

# Running the Bot

Use:

```bash
uv run python -m src.main
```

Do not commit local `.env` files.

---

# Before Opening a Pull Request

Run:

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
```

Make sure:

* The code works as intended.
* Existing functionality still works.
* No secrets are included.
* Database changes include migrations.
* Documentation is updated when necessary.
* The change is focused and understandable.

---

# Pull Requests

Pull requests should:

1. Explain what was changed.
2. Explain why the change was needed.
3. Keep unrelated changes out of the PR.
4. Include tests where practical.
5. Update documentation when necessary.

Large features should preferably be broken into logical, reviewable changes.

---

# Commit Messages

Use clear commit messages.

Examples:

```text
feat: add ticket claiming
fix: prevent duplicate tickets
docs: update setup instructions
refactor: simplify level calculation
test: add moderation tests
chore: update dependencies
```

Avoid vague messages such as:

```text
update
stuff
changes
fixed things
```

---

# Design Philosophy

DC Custom Bot intentionally follows a simple architecture:

```text
core/
    How the bot works

features/
    What the bot does

views/
    Discord UI

database/
    Persistent data
```

The project should become more structured **only when its complexity requires it**.

The goal is not to create the most sophisticated architecture possible.

The goal is to create a codebase that contributors can understand, modify, test, and extend confidently.

---

## Questions and Discussions

For questions about implementation or architecture, use the project's designated discussion or issue channels.

Before opening an issue, search existing issues and documentation to avoid duplicates.
