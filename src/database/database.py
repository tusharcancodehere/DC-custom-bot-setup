import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL")

class Base(DeclarativeBase):
    pass

engine = create_async_engine(DATABASE_URL, echo=False) if DATABASE_URL else None
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False) if engine else None

async def get_session():
    if not async_session:
        raise RuntimeError("DATABASE_URL is not configured.")
    async with async_session() as session:
        yield session
