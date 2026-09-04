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
│   │   ├── config.py        # Configuration management
│   │   ├── errors.py        # Custom exceptions and error handlers
│   │   ├── loader.py        # Dynamic feature/cog loader
│   │   ├── logging.py       # Centralized application logging
│   │   └── permissions.py   # Reusable permission and authorization checks
│   ├── features/            # Independent, modular bot features
│   │   ├── admin/           # Server administration commands
│   │   ├── ai/              # AI conversation commands (/ask, /clear)
│   │   ├── games/           # Mini-games and entertainment
│   │   ├── general/         # General utility commands (/ping)
│   │   ├── levels/          # XP tracking and rank cards (/level, /show_xp)
│   │   ├── moderation/      # Moderation tools (/kick, /ban, /timeout, etc.)
│   │   ├── music/           # Voice and music playback
│   │   ├── tickets/         # Support ticket system
│   │   └── welcome/         # Join/leave messages and embeds (/welcome)
│   ├── views/               # Shared Discord UI components (buttons, modals)
│   │   └── common.py
│   └── database/            # Database engine and connection utilities
│       └── database.py
├── alembic/                 # Database schema migrations
├── docs/                    # Extended documentation guides
├── scripts/                 # Maintenance and utility scripts
├── tests/                   # Automated test suite
├── .env.example             # Template for required environment variables
├── pyproject.toml           # Project dependencies and tool configuration
├── uv.lock                  # Pinned dependency lockfile
└── mise.toml                # Development tool version definitions
```

### Architectural Principles

* **Keep Cogs focused**: Feature Cogs (`commands.py`) should handle Discord interactions (slash commands, buttons, listeners) and delegate business logic to clean helper functions or services when logic grows complex.
* **Avoid unnecessary abstractions**: Do not introduce complex multi-layer abstractions (factories, unit of work, repository patterns) unless the codebase genuinely demands them.
* **Keep features independent**: Features should remain decoupled from one another. Shared functionality belongs in `src/core/` or `src/views/`.

---

## Development Setup

### Prerequisites

Ensure you have the following installed on your machine:

* **Python 3.13+**
* [**uv**](https://docs.astral.sh/uv/) (Python package and project manager)
* [**mise**](https://mise.jdx.dev/) (optional, recommended tool version manager)
* **Git**
* **PostgreSQL** (required when running database migrations or persistence features)

### Step 1: Clone the Repository

Fork the repository on GitHub, then clone your fork locally:

```bash
git clone https://github.com/<your-username>/DC-custom-bot-setup.git
cd DC-custom-bot-setup
```

### Step 2: Install Development Tools and Dependencies

Using `mise` (if installed):

```bash
mise install
```

Synchronize the virtual environment and install all dependencies (including development tools):

```bash
uv sync --dev
```

### Step 3: Configure Environment Variables

Create your local `.env` file from the example template:

```bash
cp .env.example .env
```

Open `.env` and fill in your development credentials:

* `DISCORD_TOKEN`: Your bot token from the [Discord Developer Portal](https://discord.com/developers/applications).
* `APPLICATION_ID`: Your Discord application/client ID.
* `SERVER_ID`: The ID of your private test Discord server (used for fast slash command syncing).
* `OPENAI_API_KEY`: (Optional) OpenAI API key for testing AI commands.
* `GEMINI_API_KEY`: (Optional) Google Gemini API key for testing AI fallback.

> [!WARNING]
> Never commit your `.env` file or credentials to Git.

### Step 4: Run the Bot

Start the bot locally:

```bash
uv run python -m src.main
```

---

## Coding Conventions

Please follow these coding practices across the repository:

* **Python Standard**: Target Python 3.13+ idioms. Use modern type hints (`str | None`, `list[str]`, etc.) where helpful.
* **Formatting and Linting**: We use [Ruff](https://docs.astral.sh/ruff/) to format and lint the code.
  * Check code:
    ```bash
    uv run ruff check .
    ```
  * Auto-format code:
    ```bash
    uv run ruff format .
    ```
* **Async/Await**: Ensure asynchronous operations (Discord API calls, HTTP requests, database queries) properly use `await` and non-blocking libraries (`aiohttp`, `asyncpg`).
* **Error Handling**: Catch specific exceptions and provide friendly error messages to users rather than letting commands fail silently.
* **Permissions**: Protect administrative and moderation commands with appropriate Discord permission checks (`@app_commands.checks.has_permissions`) and role hierarchy validation.

---

## Contributing Features and Changes

1. **Check Existing Issues**: Search [GitHub Issues](https://github.com/tusharcancodehere/DC-custom-bot-setup/issues) and [`TODO.md`](TODO.md) to see if the feature or bug is already tracked.
2. **Create a Topic Branch**:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Implement Your Changes**:
   * Add new command logic inside `src/features/<feature>/commands.py`.
   * If creating a new feature module, ensure it is registered in `setup_hook` in `src/core/bot.py`.
   * If your changes alter the database schema, generate a new migration:
     ```bash
     uv run alembic revision --autogenerate -m "Add new table"
     ```
4. **Write Tests**: Add unit tests in `tests/` to verify logic and prevent regressions.

---

## Testing

Run the automated test suite before committing:

```bash
uv run pytest
```

Ensure that:
* All existing and new tests pass.
* Tests focus on deterministic business logic, calculations, and input validation without requiring a live Discord gateway connection.

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
* `test: add unit test for XP calculation logic`

---

## Pull Request Process

When your changes are ready, open a Pull Request (PR):

1. **Pre-PR Checklist**:
   - [ ] Code passes linting: `uv run ruff check .`
   - [ ] Code is formatted: `uv run ruff format .`
   - [ ] Tests pass: `uv run pytest`
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
