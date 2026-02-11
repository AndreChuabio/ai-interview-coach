"""
SQLAlchemy async engine and session factory.

Uses the DATABASE_URL from .env:
  - sqlite+aiosqlite:///./interview_coach.db   (local dev)
  - postgresql+asyncpg://user:pass@host/db      (production)
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


async def init_db() -> None:
    """Create all tables that do not exist yet. Safe to call on every startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Yield an async database session (for FastAPI dependency injection)."""
    async with async_session_factory() as session:
        yield session
