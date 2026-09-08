# Contributing to DC Custom Bot

Thank you for your interest in contributing to **DC Custom Bot**! We welcome bug reports, documentation updates, feature requests, and code contributions from the community.

This guide outlines our project structure, local development setup, coding standards, and pull request process to help you get started smoothly.

---

## Code of Conduct

All contributors and participants are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating in project spaces.

---

## Project Structure

The project follows a clean, modular architecture designed to keep features easy to understand, test, and maintain:

```text
DC-custom-bot-setup/
├── src/
│   ├── main.py              # Application entrypoint
│   ├── core/                # Core bot framework and shared services
│   │   ├── bot.py           # CustomBot class, bot lifecycle, command sync
│   │   ├── config.py        # Configuration management & validation
│   │   ├── errors.py        # Custom exceptions and error handlers
│   │   ├── loader.py        # Dynamic feature/cog loader
│   │   ├── logging.py       # Centralized application logging
│   │   └── permissions.py   # Reusable permission and authorization checks
│   ├── features/            # Independent, modular bot features
│   │   ├── admin/           # Server administration commands (planned)
│   │   ├── ai/              # AI conversation commands (/ask, /clear)
│   │   ├── games/           # Mini-games and entertainment (planned)
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # XP tracking and rank cards (/level, /rank, /show_xp, etc.)
│   │   ├── moderation/      # Moderation tools (/kick, /ban, /timeout, /purge, /warn)
│   │   ├── music/           # Voice and music playback (yt-dlp + FFmpeg)
│   │   ├── tickets/         # Support ticket system (planned)
│   │   └── welcome/         # Join/leave messages and embeds (/welcome)
│   ├── views/               # Shared Discord UI components (buttons, modals)
│   │   └── common.py
│   └── database/            # Database engine and models
│       ├── database.py      # Async engine and session factory
│       └── models.py        # SQLAlchemy UserXP model
├── alembic/                 # Database schema migrations
│   ├── versions/            # Migration version scripts
│   └── env.py               # Async migration runner
├── docs/                    # Extended documentation guides
│   └── database.md          # PostgreSQL and database guide
├── requirements.txt         # Pip dependency requirements for standard hosting
├── Dockerfile               # Production container definition
├── .dockerignore            # Container exclusion rules
├── .env.example             # Template for required environment variables
├── pyproject.toml           # Project dependencies and tool configuration
├── uv.lock                  # Pinned dependency lockfile
├── TODO.md                  # Project roadmap and completed tasks
└── README.md                # Project overview
```

### Architectural Principles

* **Keep Cogs focused**: Feature Cogs (`commands.py`) handle Discord interactions (slash commands, buttons, listeners) and delegate business logic to clean helper functions.
* **Avoid unnecessary abstractions**: Prefer straightforward, readable Python over clever Python. Do not introduce complex multi-layer abstractions (factories, unit of work, repository patterns) unless the codebase genuinely demands them.
* **Keep features independent**: Features should remain decoupled from one another. Shared functionality belongs in `src/core/` or `src/views/`.
* **Graceful degradation**: Features that interact with external services (database, AI APIs, voice) should fail safely and inform the user with friendly messages rather than crashing the bot.

---

## Development Setup

### Prerequisites

Ensure you have the following installed on your machine:

* **Python >= 3.11** (Python 3.13 recommended)
* [**uv**](https://docs.astral.sh/uv/) (recommended) or standard `pip`
* [**FFmpeg**](https://ffmpeg.org/) (required for voice and music features)
* **Git**
* **PostgreSQL** (optional; required only if developing or testing database persistence features)

### Step 1: Clone the Repository

Fork the repository on GitHub, then clone your fork locally:

```bash
git clone https://github.com/<your-username>/DC-custom-bot-setup.git
cd DC-custom-bot-setup
```

### Step 2: Install Dependencies

#### Option A: Using `uv` (Recommended)
```bash
uv sync
```

#### Option B: Using standard Python `venv` and `pip`
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create your local `.env` file from the example template:

```bash
cp .env.example .env
```

Open `.env` and fill in your development credentials:

* `DISCORD_TOKEN`: Your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
* `APPLICATION_ID`: Your Discord application/client ID.
* `DATABASE_URL`: (Optional) PostgreSQL connection string (`postgresql+asyncpg://...`). If omitted, the bot runs without database persistence. See [docs/database.md](docs/database.md) for details.
* `OPENAI_API_KEY`: (Optional) OpenAI API key for testing AI commands.
* `GEMINI_API_KEY`: (Optional) Google Gemini API key for testing AI fallback.

> [!WARNING]
> Never commit your `.env` file or credentials to Git.

### Step 4: Apply Database Migrations (Optional)

If you configured `DATABASE_URL` for persistent leveling:

* Using `uv`:
  ```bash
  uv run alembic upgrade head
  ```
* Using standard Python:
  ```bash
  alembic upgrade head
  ```

### Step 5: Run the Bot

Start the bot locally:

* Using `uv`:
  ```bash
  uv run python src/main.py
  ```
* Using standard Python:
  ```bash
  python src/main.py
  ```

---

## Coding Conventions & Standards

To ensure the codebase remains readable, beginner-friendly, and maintainable, please adhere strictly to these conventions:

### 1. Import Organization
* Put all imports at the top of the file:
  1. Standard library imports first.
  2. Third-party imports second.
  3. Local project imports last.
* Remove unused imports.
* Do not put imports inside functions unless technically necessary.

### 2. Constants
* Place constants immediately below imports.
* Use clear `UPPERCASE` names (e.g., `COMMAND_PREFIX = "!"`, `COLOR_PRIMARY = 0x5865F2`).
* Move repeated values into constants where it improves readability; avoid pointless constants for one-off values.

### 3. Variable Scoping
* Keep instance state in `__init__`.
* Keep local values inside functions.
* Avoid unnecessary globals.

### 4. Layout & Spacing
* Standard Python spacing:
  * 2 blank lines between top-level functions and classes.
  * 1 blank line between methods inside a class.
* Keep function interiors compact and readable. Avoid sprawling vertical whitespace or scattered empty lines.

### 5. Natural Human Style
* Write clear, pragmatic Python.
* Avoid overengineering, deep inheritance hierarchies, and premature abstractions.
* Add concise comments that explain *why* something is done when non-obvious, rather than restating the syntax.

---

## Verification & Testing

Before opening a pull request, verify that all Python source files compile cleanly without syntax errors:

* Using `uv`:
  ```bash
  uv run python -m compileall -q src
  ```
* Using standard Python:
  ```bash
  python -m compileall -q src
  ```

Ensure that:
* Code compiles cleanly without errors.
* No temporary files, credentials, or `.env` files are tracked in Git.
* Slash commands and interactive views function as expected in your test Discord server.

---

## Commit Guidelines

We encourage clear, descriptive commit messages adhering to the Conventional Commits format:

```text
<type>: <short description in present tense>
```

Common types:
* `feat`: A new feature or command
* `fix`: A bug fix
* `docs`: Documentation updates
* `refactor`: Code refactoring without changing functionality
* `test`: Adding or updating tests
* `chore`: Dependency updates, tooling, or repository maintenance

**Example Commits**:
* `feat: add reason parameter to timeout command`
* `fix: prevent bot from attempting to ban guild owner`
* `docs: update setup steps in README`
* `refactor: standardize imports and constants in music cog`

---

## Pull Request Process

When your changes are ready, open a Pull Request (PR):

1. **Pre-PR Checklist**:
   - [ ] Code compiles cleanly: `uv run python -m compileall -q src` or `python -m compileall -q src`
   - [ ] No secrets or `.env` files are tracked in Git.
   - [ ] Documentation is updated if commands or configurations changed.
2. **Open the PR**:
   * Use a concise, descriptive title matching your commit format.
   * Describe the problem being solved or the feature added.
   * Reference any relevant issue numbers (e.g., `Closes #12`).
3. **Review**:
   * Maintainers will review your PR and may request adjustments.
   * Address feedback promptly by pushing updates to your branch.

---

## Reporting Issues

* **Bug Reports**: Open an issue describing the problem, reproduction steps, expected behavior, and relevant logs (with secrets removed).
* **Feature Requests**: Open an issue detailing the proposal, use cases, and how it aligns with the bot's roadmap.
* **Security Vulnerabilities**: Do **not** use public issues for security concerns. Please refer to [`SECURITY.md`](SECURITY.md) for private reporting procedures.
