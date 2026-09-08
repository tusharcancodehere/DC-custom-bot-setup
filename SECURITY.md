# Security Policy

The security of **DC Custom Bot** and its users is a top priority. Because the bot handles Discord interactions, external API integrations, and environment credentials (with database persistence planned), maintaining robust security practices is critical for all contributors and server administrators.

---

## Supported Versions

Security updates are actively maintained for the following versions:

| Version | Supported |
| :--- | :--- |
| `main` (active development) | :white_check_mark: |
| Latest release | :white_check_mark: |
| Older releases | :x: |

---

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

> [!IMPORTANT]
> **Do NOT disclose vulnerabilities publicly** via GitHub Issues, Discussions, or public Discord servers.

### How to Report Privately

1. **GitHub Security Advisories (Preferred)**: Navigate to the [GitHub Security Advisories](https://github.com/tusharcancodehere/DC-custom-bot-setup/security/advisories) tab and click **Report a vulnerability**.
2. **Email**: If private vulnerability reporting is unavailable, email the maintainer directly at [thetusharverma2505@gmail.com](mailto:thetusharverma2505@gmail.com) with the subject `[SECURITY] DC Custom Bot Vulnerability Report`.

### What to Include in Your Report

To help us investigate and resolve the issue quickly, please include:

* A clear description of the vulnerability and its potential security impact.
* The specific file, feature, or command affected (e.g., [`src/features/moderation/commands.py`](src/features/moderation/commands.py)).
* Step-by-step reproduction instructions or a minimal proof of concept.
* Any proposed mitigations or fixes, if available.

### What to Avoid

* Do **not** include real credentials, Discord bot tokens, server IDs, database passwords, or API keys in your report.
* Please allow maintainers reasonable time to investigate and patch the issue before disclosing it publicly.

---

## Security Best Practices

### 1. Keeping Secrets Out of Git

* **Never commit secrets to version control.** This includes Discord bot tokens, database connection strings (`DATABASE_URL`), OpenAI API keys, Google Gemini API keys, and webhook URLs.
* Ensure `.env` is listed in [`.gitignore`](.gitignore) and never staged for commit.
* Use [`.env.example`](.env.example) as a template containing placeholder values only.
* If a secret is accidentally committed to Git:
  1. Revoke and rotate the exposed token, password, or API key immediately.
  2. Treat any compromised credential as publicly exposed regardless of whether the commit is subsequently removed from Git history.

### 2. Environment Variables (`.env` Usage)

* All runtime credentials and configuration must be loaded through environment variables using `dotenv` and `os.getenv`.
* Never hardcode sensitive values directly into source code, test files, or default parameter values.
* Ensure loggers do not print environment variables, request headers, database connection strings, or config structures that could contain secrets.

### 3. Database Security & Credentials (Planned Persistence)

If configuring the optional `DATABASE_URL` for planned persistent storage:
* **Connection Strings**: `DATABASE_URL` contains database credentials. Never hardcode fallback credentials or database passwords directly in Python code or configuration defaults. See [docs/database.md](docs/database.md) for details.
* **Network Isolation**: When using PostgreSQL, bind it to local loopback (`127.0.0.1`) or private container networks; avoid exposing PostgreSQL port `5432` to the public internet without SSL and strict firewall rules.
* **SQL Injection Prevention**: Always use SQLAlchemy ORM or parameterized queries via `asyncpg`. Never concatenate raw user input strings directly into SQL statements.

### 4. Discord Permissions and Gateway Intents

* Follow the **principle of least privilege**: request only the Discord permissions and Gateway Intents required for enabled features.
* Enforce **server-side permission checks** using `@app_commands.checks.has_permissions` and explicit role hierarchy validations. Never rely solely on client-side Discord UI restrictions.
* Maintain **guild isolation**: ensure all commands and data lookups operate strictly within the context of the calling guild (`interaction.guild`), preventing unauthorized cross-server access.

### 5. API Keys and External Providers

* Safeguard all third-party API credentials (such as OpenAI and Google Gemini).
* Sanitize and validate external API responses before sending them to Discord channels.
* Avoid forwarding private channel messages, ticket contents, or personal data to external AI models unless explicitly requested by the user.
* Implement structured error handling to ensure API downtime or provider failures fail gracefully without exposing sensitive error logs or keys in Discord chat.

### 6. Dependency Management

* Manage dependencies using [**uv**](https://docs.astral.sh/uv/) with reproducible locks in [`uv.lock`](uv.lock) or standard dependencies in [`requirements.txt`](requirements.txt).
* Regularly audit and update project dependencies to resolve known vulnerabilities in upstream packages (`discord.py`, `aiohttp`, `cryptography`, etc.).
* Review new dependencies carefully before adding them to avoid unmaintained or insecure third-party code.

