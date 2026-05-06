"""
SQLAlchemy async engine and session factory.

Uses the DATABASE_URL from .env:
  - sqlite+aiosqlite:///./interview_coach.db   (local dev)
  - postgresql+asyncpg://user:pass@host/db      (production)

Note: asyncpg does not support the 'sslmode' query parameter that
psycopg2/libpq use. When the URL contains sslmode=require (e.g. Neon),
we strip it from the URL and pass ssl=True via connect_args instead.
"""

import ssl as _ssl
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings


def _build_engine_kwargs(url: str) -> dict:
    """
    Parse DATABASE_URL and return (clean_url, engine_kwargs).
    Handles the asyncpg sslmode incompatibility by converting
    sslmode=require into connect_args={'ssl': True}.
    """
    kwargs: dict = {}

    if "asyncpg" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)

        if "sslmode" in qs:
            qs.pop("sslmode")
            clean_query = urlencode(qs, doseq=True)
            url = urlunparse(parsed._replace(query=clean_query))
            # Create a permissive SSL context for Neon (they use valid certs)
            ctx = _ssl.create_default_context()
            kwargs["connect_args"] = {"ssl": ctx}

    return {"url": url, **kwargs}


_engine_kwargs = _build_engine_kwargs(settings.database_url)

engine = create_async_engine(
    _engine_kwargs.pop("url"),
    echo=settings.debug,
    future=True,
    **_engine_kwargs,
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
    """Create all tables that do not exist yet, and apply lightweight migrations.

    Since the project does not use Alembic, new columns on existing tables
    are added here via ALTER TABLE when missing. This keeps existing data
    intact while evolving the schema incrementally.
    """
    from sqlalchemy import inspect as sa_inspect, text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Lightweight migration: add agent_messages_json to sessions if missing.
        def _check_column(sync_conn):
            inspector = sa_inspect(sync_conn)
            columns = [c["name"] for c in inspector.get_columns("sessions")]
            return "agent_messages_json" in columns

        has_column = await conn.run_sync(_check_column)
        if not has_column:
            await conn.execute(
                text(
                    "ALTER TABLE sessions ADD COLUMN agent_messages_json TEXT DEFAULT '[]'")
            )

        # Add practice_mode and topic for quick-practice (Duo-style) feature.
        def _check_sessions_columns(sync_conn):
            inspector = sa_inspect(sync_conn)
            cols = [c["name"] for c in inspector.get_columns("sessions")]
            return "practice_mode" in cols, "topic" in cols

        has_practice_mode, has_topic = await conn.run_sync(_check_sessions_columns)
        if not has_practice_mode:
            await conn.execute(
                text("ALTER TABLE sessions ADD COLUMN practice_mode VARCHAR(16) DEFAULT ''")
            )
        if not has_topic:
            await conn.execute(
                text("ALTER TABLE sessions ADD COLUMN topic VARCHAR(256) DEFAULT ''")
            )

    # user_progress: add sessions_today if table exists but column missing
    try:
        def _check_user_progress_columns(sync_conn):
            inspector = sa_inspect(sync_conn)
            if "user_progress" not in inspector.get_table_names():
                return False
            cols = [c["name"] for c in inspector.get_columns("user_progress")]
            return "sessions_today" in cols

        has_sessions_today = await conn.run_sync(_check_user_progress_columns)
        if not has_sessions_today:
            await conn.execute(
                text("ALTER TABLE user_progress ADD COLUMN sessions_today INTEGER DEFAULT 0")
            )
    except Exception:
        pass


async def get_db() -> AsyncSession:
    """Yield an async database session (for FastAPI dependency injection)."""
    async with async_session_factory() as session:
        yield session
