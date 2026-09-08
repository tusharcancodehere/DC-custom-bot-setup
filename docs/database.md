# Database Architecture & Guide

This document explains the database stack, local setup, configuration, models, and migrations for **DC Custom Bot**.

All database operations are fully asynchronous, beginner-friendly, and designed with graceful degradation.

---

## 1. Technology Stack

DC Custom Bot uses an asynchronous database stack built around PostgreSQL and SQLAlchemy 2.0:

| Technology | Purpose | Documentation |
| :--- | :--- | :--- |
| **PostgreSQL** (`>= 15`) | Relational database engine for persistent data storage. | [PostgreSQL Docs](https://www.postgresql.org/docs/) |
| **SQLAlchemy** (`>= 2.0.52`) | Modern Python ORM and SQL toolkit using async engines and declarative models. | [SQLAlchemy Docs](https://docs.sqlalchemy.org/en/20/) |
| **asyncpg** (`>= 0.31.0`) | High-performance asynchronous PostgreSQL driver for Python and asyncio. | [asyncpg Docs](https://magicstack.github.io/asyncpg/) |
| **Alembic** (`>= 1.19.1`) | Database schema migration tool for tracking and applying database revisions. | [Alembic Docs](https://alembic.sqlalchemy.org/en/latest/) |

---

## 2. Architecture & Graceful Degradation

### Persistent Leveling
The database persistently tracks member experience (`xp`), current level (`level`), and timestamp cooldowns (`last_xp`) per server guild. This ensures member ranks and leaderboards survive bot restarts.

### Graceful Degradation (Database is Optional)
To make local development, quick testing, and hosting setup effortless:
* **The bot starts and runs even without a database.**
* If `DATABASE_URL` is omitted from `.env`, or if the PostgreSQL server is unreachable, [`init_db()`](../src/database/database.py) logs a friendly notice:
  `Database: unavailable (DATABASE_URL not configured)`
* All core features continue to work: moderation (`/kick`, `/ban`, `/purge`), music playback (`/play`, `/player`), welcome embeds (`/welcome`), and AI assistant (`/ask`).
* Level commands (`/level`, `/rank`, `/leaderboard`, etc.) safely report a friendly message to the user:
  `"Database is not configured. Persistent XP is currently unavailable."`

---

## 3. Database Models

Active models are declared in [`src/database/models.py`](../src/database/models.py) using SQLAlchemy 2.0 declarative syntax:

### `UserXP` (`user_xp` Table)

Stores individual member experience per server:

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `guild_id` | `BigInteger` | Primary Key | Discord server ID |
| `user_id` | `BigInteger` | Primary Key | Discord user ID |
| `xp` | `Integer` | Default: `0`, Not Null | Total earned experience points |
| `level` | `Integer` | Default: `0`, Not Null | Current calculated user level |
| `last_xp` | `DateTime(timezone=True)` | Default: `now()`, Not Null | Timestamp of last awarded XP (used for anti-spam cooldown) |

An index `ix_user_xp_guild_xp` on `(guild_id, xp)` optimizes high-traffic leaderboard queries.

---

## 4. Configuration & Environment Variables

The database engine reads its connection details from the `DATABASE_URL` variable in your `.env` file.

### Connection String Format

```env
DATABASE_URL="postgresql+asyncpg://<username>:<password>@<host>:<port>/<database_name>"
```

* Always use the `postgresql+asyncpg://` driver prefix.
* Do not use synchronous drivers like `psycopg2`.

### Example Configurations

* **Local PostgreSQL**:
  ```env
  DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dc_custom_bot"
  ```
* **Production PostgreSQL**:
  ```env
  DATABASE_URL="postgresql+asyncpg://db_user:secure_password@db.internal:5432/dc_custom_bot_prod"
  ```

---

## 5. Local Setup Options

If you wish to test persistent leveling locally, choose either Docker or native installation.

### Option A: Docker (Fastest & Easiest)

Run a local PostgreSQL 15 container with one command:

```bash
docker run --name dc-bot-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=dc_custom_bot \
  -p 5432:5432 \
  -d postgres:15-alpine
```

To pause or resume the container later:

```bash
docker stop dc-bot-postgres
docker start dc-bot-postgres
```

### Option B: Native Installation

1. **Install PostgreSQL**:
   * **Ubuntu / Debian**: `sudo apt update && sudo apt install -y postgresql postgresql-contrib`
   * **macOS**: `brew install postgresql@15 && brew services start postgresql@15`
   * **Windows**: Download from [postgresql.org](https://www.postgresql.org/download/windows/).

2. **Create the Database and User**:
   ```bash
   sudo -u postgres psql -c "CREATE USER postgres WITH PASSWORD 'postgres';"
   sudo -u postgres psql -c "CREATE DATABASE dc_custom_bot OWNER postgres;"
   ```

3. **Set `DATABASE_URL` in `.env`**:
   ```env
   DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/dc_custom_bot"
   ```

---

## 6. Schema Migrations with Alembic

[Alembic](https://alembic.sqlalchemy.org/) manages database table creation and future schema changes.

Migration revisions live in the [`alembic/versions/`](../alembic/versions/) folder.

### 1. Apply Migrations (Required Before Running Persistent Levels)

Run the upgrade command to bring your database schema to the latest version:

* Using `uv`:
  ```bash
  uv run alembic upgrade head
  ```
* Using standard Python:
  ```bash
  alembic upgrade head
  ```

### 2. Creating a New Migration (For Developers)

When adding or modifying SQLAlchemy models in [`src/database/models.py`](../src/database/models.py):

```bash
uv run alembic revision --autogenerate -m "Describe your schema changes"
```

Inspect the newly generated script inside [`alembic/versions/`](../alembic/versions/), verify the table operations, and apply it with `upgrade head`.

### 3. Rolling Back a Migration

To roll back the most recent migration step:

```bash
uv run alembic downgrade -1
```

---

## 7. Database Code Structure

All database connection management is organized inside [`src/database/database.py`](../src/database/database.py):

* [`init_db()`](../src/database/database.py): Tests the connection with `SELECT 1`, auto-creates registered tables, and returns `True` or `False`.
* [`close_db()`](../src/database/database.py): Gracefully disposes the connection engine when the bot shuts down.
* [`get_session()`](../src/database/database.py): Asynchronous generator yielding isolated database sessions with automatic context management.

### Query Example inside Cogs

```python
from database.database import get_session
from database.models import UserXP
from sqlalchemy import select

async def fetch_user_level(guild_id: int, user_id: int) -> int:
    async for session in get_session():
        stmt = select(UserXP).where(
            UserXP.guild_id == guild_id,
            UserXP.user_id == user_id,
        )
        result = await session.execute(stmt)
        record = result.scalar_one_or_none()
        return record.level if record else 0
```

---

## 8. Security Best Practices

* **Never commit credentials**: Keep database usernames, passwords, and hostnames in `.env` or your hosting environment panel.
* **Sanitize logs**: The bot ensures database passwords are never logged to the console or log files.
* **Non-blocking asynchronous queries**: Always use `await session.execute(...)` to keep the Discord gateway responsive.
* **Principle of least privilege**: In production, create a dedicated database user with permissions restricted only to the bot's database.
