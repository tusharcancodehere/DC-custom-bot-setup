git add . && git commit -m "fix: simplify YouTube music extraction" && git pushimport logging
import os
import shutil
import sys
from dotenv import load_dotenv

PRIMARY_COLOR = 0x5865F2
SUCCESS_COLOR = 0x57F287
WARNING_COLOR = 0xFEE75C
ERROR_COLOR = 0xED4245
INFO_COLOR = 0x5865F2
MUSIC_COLOR = 0x9B59B6

def load_environment():
    load_dotenv(".env.local")
    load_dotenv(".env")

    # Sanitize environment variables (e.g. when passed with literal quotes via Docker --env-file)
    for key, value in list(os.environ.items()):
        if value:
            stripped = value.strip()
            if len(stripped) >= 2 and (
                (stripped.startswith('"') and stripped.endswith('"')) or
                (stripped.startswith("'") and stripped.endswith("'"))
            ):
                os.environ[key] = stripped[1:-1]

def validate_startup_config():
    load_environment()
    print("Starting DC-custom-bot-setup...")
    print("Loading configuration...")

    token = os.getenv("DISCORD_TOKEN")
    if not token or not token.strip():
        print("DISCORD_TOKEN is not configured.")
        sys.exit(1)

    app_id = os.getenv("APPLICATION_ID")
    if not app_id or not app_id.strip():
        print("APPLICATION_ID is not configured.")
        sys.exit(1)

    try:
        int(app_id.strip())
    except ValueError:
        print("APPLICATION_ID must be a valid integer.")
        sys.exit(1)

    if not shutil.which("ffmpeg"):
        logging.warning("FFmpeg was not found on PATH. Music commands cannot play audio.")
        print("Warning: FFmpeg was not found on PATH. Music commands cannot play audio.")

