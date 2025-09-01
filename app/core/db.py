from __future__ import annotations

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os

DATABASE_URL: str = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@db:5432/codereview"
)


engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True, future=True)

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://mongo:27017")
MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "codereview")

mongo_client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
mongo_db: AsyncIOMotorDatabase = mongo_client[MONGO_DB_NAME]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield mongo_db
