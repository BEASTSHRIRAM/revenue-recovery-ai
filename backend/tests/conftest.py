"""Shared pytest fixtures: an isolated in-memory DB per test and an ASGI client."""

from __future__ import annotations

import os
import tempfile
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base


@pytest_asyncio.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    import app.models  # noqa: F401  populate metadata

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as s:
        yield s


@pytest.fixture
def checkpoint_db_path(tmp_path):
    return str(tmp_path / "checkpoints.sqlite")


@pytest_asyncio.fixture
async def client(engine, monkeypatch) -> AsyncIterator[AsyncClient]:
    """ASGI test client wired to the same in-memory engine as `session`."""
    checkpoint_fd, checkpoint_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(checkpoint_fd)
    monkeypatch.setattr("app.core.config.settings.checkpoint_db", checkpoint_path)

    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.db import session as session_module
    from app.main import app

    factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def _get_session_override():
        async with factory() as s:
            yield s

    app.dependency_overrides[session_module.get_session] = _get_session_override

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    os.remove(checkpoint_path)
