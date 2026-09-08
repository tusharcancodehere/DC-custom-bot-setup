import logging
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import load_environment

load_environment()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.strip().strip("'\"")
    if not DATABASE_URL:
        DATABASE_URL = None

class Base(DeclarativeBase):
    pass

engine = None
async_session = None

from sqlalchemy.pool import NullPool

if DATABASE_URL:
    try:
        engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    except Exception as error:
        logging.warning("Database engine initialization failed: %s", error, exc_info=True)
        DATABASE_URL = None

def is_db_connected() -> bool:
    """Return True if the database engine and sessionmaker are configured and active."""
    return engine is not None and async_session is not None

def set_database_url(url: str | None, use_null_pool: bool = False):
    """Set or update the database URL and initialize engine and sessionmaker."""
    global DATABASE_URL, engine, async_session
    DATABASE_URL = url.strip().strip("'\"") if url else None
    if DATABASE_URL:
        try:
            kwargs = {"echo": False, "pool_pre_ping": True}
            if use_null_pool:
                kwargs["poolclass"] = NullPool
            engine = create_async_engine(DATABASE_URL, **kwargs)
            async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        except Exception as error:
            logging.warning("Database engine initialization failed: %s", error)
            DATABASE_URL = None
            engine = None
            async_session = None
    else:
        engine = None
        async_session = None


async def init_db() -> bool:
    global engine, async_session
    if not DATABASE_URL:
        logging.info("Database: unavailable (DATABASE_URL not configured)")
        print("Database: unavailable (DATABASE_URL not configured)")
        return False

    if not engine:
        logging.warning("Database: unavailable (database engine could not be initialized)")
        print("Database: unavailable (database engine could not be initialized)")
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

