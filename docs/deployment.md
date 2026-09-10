# Render Web Service Deployment & Monitoring Guide

This guide provides complete, beginner-friendly instructions for deploying **DC Custom Bot** to [Render](https://render.com/) as a **Web Service** with automated uptime monitoring via [UptimeRobot](https://uptimerobot.com/).

---

## 1. Architecture Overview

### Why Render Web Service instead of Background Worker?

* **Free Tier Availability**: Render provides a generous free tier for **Web Services**, whereas **Background Workers** require a paid plan.
* **Port Binding Requirement**: Render Web Services expect a listening HTTP server bound to `0.0.0.0` on the port assigned by the `$PORT` environment variable (defaults to `10000`). If no service listens on `$PORT`, Render fails the deployment with `"No open ports detected"`.
* **Integrated Health Server**: DC Custom Bot includes a built-in, lightweight [`aiohttp`](../src/core/health.py) HTTP server that starts concurrently inside the Python process without delaying Discord Gateway login or slash command synchronization.

### Deployment Flow Diagram

```text
GitHub Repository ──> Render Web Service (Build & Deploy) ──> Single Python Process (src/main.py)
                                                               ├── Discord Bot (Outbound Gateway WebSocket)
                                                               └── aiohttp HTTP Server (0.0.0.0:$PORT)
                                                                     ├── GET /       -> {"status": "ok"}
                                                                     └── GET /health -> {"status": "ok"}
                                                                            ▲
                                                                            │
                                                        UptimeRobot Monitor (Every 5–10 mins)
                                                        URL: https://<your-service>.onrender.com/health
```

---

## 2. HTTP Health Endpoints

The embedded HTTP server exposes two public, read-only health check routes:

| Route | Method | Success Response | Description |
| :--- | :---: | :---: | :--- |
| `/` | `GET` | `200 OK` `{"status": "ok"}` | Root health check for Render port detection. |
| `/health` | `GET` | `200 OK` `{"status": "ok"}` | Standard health check endpoint for external uptime monitors. |

### Crucial Note on Health Check Scope

> [!IMPORTANT]
> **What `/health` checks**:
> The `/health` endpoint strictly verifies that the **Render web process, Python runtime, and asyncio event loop are alive and responding to inbound HTTP requests**.
>
> **What `/health` does NOT check**:
> * It does **NOT** verify whether the bot is actively connected to the Discord Gateway WebSocket.
> * It does **NOT** verify whether external APIs (OpenAI or Google Gemini) are available or have quota remaining.
>
> If Discord experiences an API outage or your bot token is rotated, `/health` will continue returning HTTP 200 as long as the Python process is alive. Always inspect Render logs or test commands in Discord to verify gateway status.

---

## 3. Environment Variables Reference

Configure these variables in the **Environment Variables** tab of your Render Web Service:

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `DISCORD_TOKEN` | **Yes** | — | Bot token from the [Discord Developer Portal](https://discord.com/developers/applications). |
| `APPLICATION_ID` | **Yes** | — | Application / Client ID from the Discord Developer Portal. |
| `PORT` | Optional | `10000` | Port for the HTTP health server. Automatically assigned and set by Render as `$PORT`. |
| `SERVER_ID` | Optional | — | Target Discord guild ID for instant testing of slash commands during development. |
| `DATABASE_URL` | Optional | `""` | PostgreSQL connection string (`postgresql+asyncpg://...`). If empty, SQLite or in-memory mode is used automatically. |
| `OPENAI_API_KEY` | Optional | — | API key for OpenAI assistant (`gpt-5-mini`). |
| `GEMINI_API_KEY` | Optional | — | API key for Google Gemini fallback (`gemini-2.5-flash`). |

> [!WARNING]
> Never commit actual credentials or your `.env` file to GitHub. Add them exclusively through the Render dashboard.

---

## 4. Step-by-Step Render Deployment

### Step 1: Push Your Code to GitHub
Ensure your latest code is pushed to your GitHub repository (either `main` or your deployment branch).

### Step 2: Create a New Web Service on Render
1. Log in to your [Render Dashboard](https://dashboard.render.com/).
2. Click the blue **New +** button in the top right and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and click **Next**.
4. Select your `DC-custom-bot-setup` repository.

### Step 3: Configure Service Settings
Fill in the deployment settings:

* **Name**: `dc-custom-bot` (or your chosen name)
* **Region**: Select a region close to your user base (e.g., Oregon, Frankfurt, Singapore).
* **Branch**: `main`
* **Root Directory**: Leave blank (root of the repo).
* **Runtime**: `Python 3`
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**: `python src/main.py`
* **Instance Type**: `Free`

*(Alternatively, you can select the **Docker** runtime to build directly from the included [`Dockerfile`](../Dockerfile).)*

### Step 4: Add Environment Variables
Scroll down to the **Environment Variables** section and add:
* `DISCORD_TOKEN`: `<your-bot-token>`
* `APPLICATION_ID`: `<your-application-id>`
* `PORT`: `10000`
* Add any optional variables (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, `SERVER_ID`).

### Step 5: Deploy
Click **Create Web Service**.
* Render will clone your code, install dependencies, execute `python src/main.py`, and detect port `10000`.
* Your service URL will look like: `https://<your-render-service>.onrender.com`.

---

## 5. UptimeRobot Keep-Alive Setup

On Render's free tier, Web Services automatically spin down after 15 minutes without inbound HTTP traffic. To keep your Discord bot online 24/7 without interruption:

1. Create a free account at [UptimeRobot](https://uptimerobot.com/).
2. On your UptimeRobot dashboard, click **+ Add New Monitor**.
3. Fill out the monitor configuration:
   * **Monitor Type**: `HTTP(s)`
   * **Friendly Name**: `DC Custom Bot Keep-Alive`
   * **URL (or IP)**: `https://<your-render-service>.onrender.com/health` (replace with your actual Render service hostname)
   * **Monitoring Interval**: `5 minutes` (or `10 minutes`)
   * **Monitor Timeout**: `30 seconds`
4. Click **Create Monitor**.

UptimeRobot will now send an HTTP GET request to `/health` every 5 minutes, keeping the Render free container warm and running continuously.

---

## 6. Troubleshooting Guide

### Issue 1: "No open ports detected"
* **Error**: Render deploy log displays `==> No open ports detected on 0.0.0.0, continuing to scan...` followed by deploy failure.
* **Why it happens**: Render requires an active TCP socket bound to `0.0.0.0` on the port specified by `$PORT`. If your Start Command bypasses `src/main.py`, or if the server binds only to `127.0.0.1`, Render cannot detect the open port.
* **Fix**:
  1. Confirm your Start Command is exactly `python src/main.py`.
  2. Confirm `src/core/health.py` uses host `0.0.0.0`.
  3. Verify that `PORT` is either set to `10000` or left to Render's default assignment.

### Issue 2: "503 Service Unavailable"
* **Error**: Visiting `https://<your-render-service>.onrender.com/health` returns `503 Service Unavailable`.
* **Why it happens**: The container is still initializing, or the application crashed immediately upon startup.
* **Fix**:
  1. Check the Render service **Logs** tab.
  2. Ensure `DISCORD_TOKEN` and `APPLICATION_ID` are configured in Render environment variables. If either is missing, `validate_startup_config()` exits the process with code 1.
  3. Wait 30 seconds after a fresh build for the container to finish starting.

### Issue 3: "Discord bot is online but health monitor fails"
* **Error**: Bot works in Discord, but UptimeRobot marks the monitor as DOWN (red status).
* **Why it happens**: The monitor URL is configured incorrectly (e.g. `http://` instead of `https://`, incorrect hostname, or pointing to a non-existent path).
* **Fix**:
  1. Test the endpoint manually in your browser or with curl:
     ```bash
     curl -i https://<your-render-service>.onrender.com/health
     ```
  2. Ensure the response returns HTTP 200 with `{"status": "ok"}`.
  3. Update UptimeRobot monitor URL to match your exact Render service URL.

### Issue 4: "Database unavailable"
* **Error**: Logs state `Database connection failed... Operating in-memory` or SQLite connection errors.
* **Why it happens**: The remote PostgreSQL instance in `DATABASE_URL` is unreachable, credentials expired, or firewall blocks inbound traffic.
* **Fix**:
  1. DC Custom Bot uses **graceful degradation**: all commands (moderation, music, welcome, tickets, AI) continue working normally in-memory.
  2. To restore persistent PostgreSQL storage, verify credentials and SSL settings in `DATABASE_URL`. See [docs/database.md](database.md) for details.

### Issue 5: YouTube "Sign in to confirm you're not a bot"
* **Error**: Music commands report `Sign in to confirm you're not a bot` or `automated queries`.
* **Why it happens**: YouTube flags shared hosting and datacenter IP ranges (including Render) to block automated scrapers.
* **Fix & Architecture**:
  1. **Automatic Skip & Queue Continuation**: The bot automatically catches bot-detection errors, sends a clear warning message to the channel, and continues playing the next track in the queue without stalling.
