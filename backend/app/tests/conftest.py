"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.session import get_db
from app.main import app as fastapi_app
from app.services.factory import get_provider
from app.services.mock_provider import MockProvider

# ── Use SQLite for tests (no Postgres required) ───────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(scope="session", autouse=True)  # type: ignore[misc]
async def create_test_db() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture  # type: ignore[misc]
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture  # type: ignore[misc]
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Return an HTTPX async client with DB and provider overridden."""

    async def _override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    fastapi_app.dependency_overrides[get_db] = _override_db
    fastapi_app.dependency_overrides[get_provider] = lambda: MockProvider()

    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as c:
        yield c

    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def mock_provider() -> MockProvider:
    return MockProvider()
