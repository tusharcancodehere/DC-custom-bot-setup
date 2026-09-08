import asyncio
import signal
import sys

from core.bot import CustomBot
from core.config import validate_startup_config

async def main():
    validate_startup_config()
    bot = CustomBot()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))
        except (NotImplementedError, RuntimeError):
            pass

    try:
        await bot.start(bot.token)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)