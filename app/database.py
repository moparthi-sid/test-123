import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Database URL, using sqlite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./taskmanager.db")

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True, future=True)


# Function to create all tables
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# Async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Dependency for database session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()