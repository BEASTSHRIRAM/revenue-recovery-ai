"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_connect_args = {"check_same_thread": False} if settings.is_sqlite else {}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=_connect_args,
)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: one session per request, always closed."""
    async with SessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables directly from ORM metadata.

    Used for the SQLite dev path and tests. Postgres deployments should run
    Alembic migrations (`alembic upgrade head`) instead of calling this.
    """
    from app.db.base import Base
    import app.models  # noqa: F401  (populate Base.metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
