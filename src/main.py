import asyncio
from core.bot import CustomBot

async def main():
    bot = CustomBot()
    await bot.start(bot.token)

if __name__ == "__main__":
    asyncio.run(main())