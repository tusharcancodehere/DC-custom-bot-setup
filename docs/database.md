# Database Architecture & Guide

This document explains the database stack, local setup, configuration, and architectural roadmap for **DC Custom Bot**.

---

## 1. Technology Stack

DC Custom Bot uses an asynchronous database stack built around PostgreSQL and SQLAlchemy 2.0:

| Technology | Purpose |
| :--- | :--- |
| **PostgreSQL** (`>= 15`) | Relational database engine for persistent data storage. |
| **SQLAlchemy** (`>= 2.0.52`) | Modern Python ORM and SQL toolkit using async engines and declarative models. |
| **asyncpg** (`>= 0.31.0`) | High-performance asynchronous PostgreSQL driver for Python and asyncio. |
| **Alembic** (`>= 1.19.1`) | Database schema migration tool for tracking and applying database revisions. |

---

## 2. Current State vs. Planned Roadmap

To keep local development lightweight and accessible, the bot is designed to boot and function even without a database:

### Current State (In-Memory & JSON)
* **Levels & XP**: Currently tracked in-memory during bot runtime; customizable embed layouts load from `src/features/levels/embed.json`.
* **Welcome**: Loads layout configurations and channel mentions from `src/features/welcome/embed.json`.
* **Moderation**: Commands execute server-side actions (kick, ban, timeout, purge, warn DMs) directly via the Discord API without persisting infraction history.
* **Music & Queues**: Managed in-memory per guild audio player.
* **AI Conversations**: Session histories are kept in-memory for active conversations.
* **Database Engine (`src/database/database.py`)**: Gracefully evaluates `DATABASE_URL = os.getenv("DATABASE_URL")`. If the variable is not set, `engine` and `async_session` remain `None`. This allows contributors to develop and run the bot without needing a running PostgreSQL instance.

### Planned State (Persistent PostgreSQL Models)
Planned persistent tables include:
* **Guild Settings**: Configurable welcome channels, auto-roles, music channel locks, and moderation log channels.
* **User Levels**: Persistent XP, levels, and leaderboard ranking across bot restarts.
* **Moderation Logs**: Case IDs, infraction types (kick, ban, timeout, warn), reason, moderator ID, target user ID, and timestamps.
* **Ticket Transcripts**: Archival of closed support tickets, transcripts, and member interactions.

---

## 3. Configuration & Environment Variables

The database engine reads its connection details from the `DATABASE_URL` environment variable defined in `.env`.

### Connection String Format

```env
DATABASE_URL="postgresql+asyncpg://<username>:<password>@<host>:<port>/<database_name>"
```

* The driver must be `postgresql+asyncpg://` to utilize SQLAlchemy's async engine.
* Do not use synchronous drivers like `psycopg2` in `DATABASE_URL`.

### Example Configurations

* **Local PostgreSQL**:
  ```env
  DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dc_custom_bot"
  ```
* **Production PostgreSQL**:
  ```env
  DATABASE_URL="postgresql+asyncpg://db_user:secure_production_password@db.internal:5432/dc_custom_bot_prod"
  ```

---

## 4. Local Development Setup

If you are developing database models or testing persistence features, set up a local PostgreSQL instance using either Docker or a native installation.

### Option A: Docker (Recommended)

Run a PostgreSQL 15 container with a single command:

```bash
docker run --name dc-bot-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=dc_custom_bot \
  -p 5432:5432 \
  -d postgres:15-alpine
```

To stop or restart the container:

```bash
docker stop dc-bot-postgres
docker start dc-bot-postgres
```

### Option B: Native Installation

1. Install PostgreSQL:
   * **Ubuntu / Debian**: `sudo apt update && sudo apt install -y postgresql postgresql-contrib`
   * **macOS**: `brew install postgresql@15 && brew services start postgresql@15`
   * **Windows**: Download and install from [postgresql.org](https://www.postgresql.org/download/windows/).

2. Create a local database and user:
   ```bash
   sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
   sudo -u postgres psql -c "CREATE DATABASE dc_custom_bot OWNER postgres;"
   ```

3. Add `DATABASE_URL` to your `.env`:
   ```env
   DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dc_custom_bot"
   ```

---

## 5. Database Code Structure (`src/database/database.py`)

The database connection and session lifecycle are managed in [`src/database/database.py`](../src/database/database.py):

```python
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=False) if DATABASE_URL else None
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

async def get_session():
    if not async_session:
        raise RuntimeError("DATABASE_URL is not configured.")
    async with async_session() as session:
        yield session
```

### Using Sessions in Feature Cogs

When persistent models are introduced, acquire sessions using `get_session()`:

```python
from database.database import get_session

async def update_user_xp(user_id: int, xp_to_add: int):
    async for session in get_session():
        # Perform async database queries
        # await session.execute(...)
        # await session.commit()
        break
```

---

## 6. Schema Migrations with Alembic

[Alembic](https://alembic.sqlalchemy.org/) handles database schema evolution.

### Status
Alembic is installed in `pyproject.toml`. The `alembic/` directory is prepared for migration revisions as ORM models are added to the codebase.

### Workflow Reference (Planned)

Once models are defined:

1. Initialize async Alembic configuration (one-time project setup):
   ```bash
   uv run alembic init -t async alembic
   ```

2. Generate a migration script after modifying models:
   ```bash
   uv run alembic revision --autogenerate -m "Create initial tables"
   ```

3. Review the generated script in `alembic/versions/`.

4. Apply pending migrations to your database:
   ```bash
   uv run alembic upgrade head
   ```

5. Roll back the latest migration if needed:
   ```bash
   uv run alembic downgrade -1
   ```

---

## 7. Security Best Practices

* **Never commit credentials**: Always keep database usernames, passwords, and hostnames in `.env`.
* **Sanitize logs**: Ensure database connection strings with passwords are never logged to console or `logs/bot.log`.
* **Use async non-blocking queries**: Always use `await session.execute(...)` to avoid blocking the Discord bot gateway event loop.
* **Principle of least privilege**: In production, create a dedicated database user with permissions scoped only to the `dc_custom_bot` database.
