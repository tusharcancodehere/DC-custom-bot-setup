# Security Policy

## Overview

Security is an important part of DC Custom Bot.

Because the project interacts with Discord, external APIs, and a PostgreSQL database, security issues may affect bot accounts, Discord servers, user data, credentials, or project infrastructure.

Please report security vulnerabilities responsibly.

---

## Supported Versions

Security fixes are primarily provided for the latest development version and the latest stable release.

| Version               | Supported |
| --------------------- | --------- |
| Latest stable         | ✅         |
| Development branch    | ✅         |
| Older releases        | ⚠️        |
| Unmaintained releases | ❌         |

Support status may change as the project develops.

---

## Reporting a Vulnerability

**Do not publicly disclose a security vulnerability through a GitHub issue, pull request, discussion, or public Discord channel.**

Instead, report the vulnerability privately through the security contact or private reporting mechanism specified by the project maintainers.

Include as much of the following information as possible:

* A clear description of the vulnerability.
* The affected component or feature.
* Steps required to reproduce the issue.
* The potential impact.
* Relevant logs, screenshots, or proof of concept where appropriate.
* A suggested fix, if you have one.

Please avoid including real credentials, tokens, personal information, or other sensitive data in the report.

---

## What Should Be Reported?

Examples of security issues include:

### Discord Permissions

* A user can execute a command without the required permission.
* A moderation command can be bypassed.
* A normal member can gain administrative functionality.
* Bot permission checks can be circumvented.

### Authentication and Credentials

* Discord bot token exposure.
* Database credential exposure.
* API key exposure.
* Credentials accidentally committed to the repository.
* Authentication bypasses.

### Database Security

* SQL injection.
* Unauthorized database access.
* Access to another guild's data.
* Missing guild/user authorization checks.
* Unsafe handling of user-controlled database input.

### Data Exposure

* Private ticket contents exposed to unauthorized users.
* Sensitive moderation information exposed.
* AI conversation data accessible to unintended users.
* Server configuration data exposed across guilds.

### Application Security

* Remote code execution.
* Arbitrary file access.
* Unsafe command execution.
* Path traversal.
* Denial-of-service vulnerabilities.
* Unsafe handling of external API responses.
* Vulnerabilities caused by untrusted user input.

---

## Discord Bot Security

DC Custom Bot should follow the principle of least privilege.

The bot should request only the Discord permissions and Gateway Intents required by the enabled functionality.

Do not grant administrator permissions when narrower permissions are sufficient.

Feature implementations should verify permissions on the server side rather than relying only on Discord's command interface.

---

## Secrets

Never commit secrets to the repository.

This includes:

```text
Discord bot tokens
Database passwords
API keys
OAuth secrets
Webhook credentials
Private keys
```

Store local development secrets in `.env` or another appropriate secret-management system.

The repository should contain `.env.example` with empty or placeholder values instead.

---

## If a Secret Is Leaked

If a Discord bot token, API key, database password, or other credential is accidentally exposed:

1. Revoke or rotate the credential immediately.
2. Remove the secret from the source repository where appropriate.
3. Check whether the credential was accessed or abused.
4. Review relevant logs.
5. Notify the maintainers if the exposure affects the project.

**Do not assume that deleting the file or commit is sufficient.**

Credentials exposed in Git history may remain accessible until properly removed and rotated.

---

## User and Server Data

The bot may process data required for its features, such as:

* Discord user IDs.
* Discord guild IDs.
* Channel IDs.
* Roles and permissions.
* Moderation records.
* Ticket information.
* Level and XP data.
* Configuration settings.
* Game-related data.
* AI conversation data, when enabled.

Only collect and store data that is necessary for the feature being provided.

Features should not access data belonging to another Discord server unless explicitly authorized by the application's design.

---

## Multi-Guild Isolation

The bot is designed to operate across multiple Discord servers.

Guild-specific data must remain isolated.

Database queries involving guild-specific information should validate the relevant `guild_id` and user permissions where applicable.

A feature must never assume that a Discord user, channel, role, ticket, or configuration record belongs to the current guild without verification.

---

## Third-Party Services

Some features may communicate with external services, including AI providers and other APIs.

Contributors should:

* Avoid sending unnecessary user data to external services.
* Avoid placing secrets in URLs or logs.
* Validate external responses.
* Handle API failures safely.
* Respect the terms and security requirements of external providers.

For AI functionality, contributors should be especially careful about sending private server content, ticket contents, or user-provided sensitive information to external providers.

---

## Dependency Security

Dependencies should be kept reasonably up to date.

When adding a new dependency:

* Use a well-maintained package when possible.
* Avoid unnecessary dependencies.
* Check the package's maintenance status and reputation.
* Understand what permissions or system access the dependency requires.
* Keep `uv.lock` updated.

Security-related dependency updates should be prioritized.

---

## Logging

Logs must not contain sensitive credentials or secrets.

Never log:

```text
Discord tokens
API keys
Database passwords
Authorization headers
Private keys
```

Be careful when logging user-provided content, ticket messages, moderation records, or AI conversations.

Debug information should not accidentally become a source of sensitive data exposure.

---

## Pull Requests and Security Review

Contributors should consider security implications when modifying:

* Permissions.
* Authentication.
* Database queries.
* Ticket access.
* Moderation commands.
* File operations.
* External API integrations.
* AI context handling.
* Webhooks.
* Configuration handling.

Changes involving security-sensitive functionality may require additional maintainer review.

---

## Responsible Disclosure

When a vulnerability is reported privately, maintainers will investigate it and determine an appropriate response.

Depending on the severity, the response may include:

* Fixing the vulnerability.
* Releasing a patched version.
* Rotating affected credentials.
* Updating documentation.
* Notifying affected users or maintainers.

Please allow reasonable time for the issue to be investigated and fixed before publicly disclosing the vulnerability.

---

## Security Best Practices for Contributors

Before submitting code, check that:

* No secrets are included.
* User input is validated.
* Permissions are explicitly checked.
* Guild boundaries are respected.
* Database queries are parameterized through the project's database layer.
* External API responses are treated as untrusted input.
* Errors do not expose sensitive implementation details.
* Logs do not contain credentials or unnecessary private information.
* New dependencies are justified.

---

## Security Contact

For security reports, use the private security contact or reporting mechanism provided by the repository maintainers.

Do not use public GitHub issues for vulnerabilities.

The project's security contact will be documented here once the official reporting channel has been established.
