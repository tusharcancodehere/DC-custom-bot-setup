import logging
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

load_dotenv(".env.local")
load_dotenv(".env")

DATABASE_URL = os.getenv("DATABASE_URL")

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=False) if DATABASE_URL else None
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

async def init_db() -> bool:
    global engine, async_session
    if not engine or not DATABASE_URL:
        logging.info("Database: unavailable (DATABASE_URL not configured)")
        print("Database: unavailable (DATABASE_URL not configured)")
        return False

    try:
        import database.models
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.run_sync(Base.metadata.create_all)
        logging.info("Database: connected")
        print("Database: connected")
        return True
    except Exception as error:
        logging.error(f"Database: unavailable (PostgreSQL connection failed: {error})")
        print(f"Database: unavailable (PostgreSQL connection failed: {error})")
        async_session = None
        return False

async def close_db():
    global engine
    if engine:
        await engine.dispose()
        logging.info("Database engine disposed.")

async def get_session():
    if not async_session:
        raise RuntimeError("DATABASE_URL is not configured.")
    async with async_session() as session:
        yield session

