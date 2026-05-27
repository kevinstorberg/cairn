import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.base import Base
from src.settings import get_settings


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine for each test."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create a database session for tests."""
    async_session_maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def clean_db(test_engine):
    """Clean database before each test."""
    async with test_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE todo_embeddings, todos RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing endpoints."""
    from src.app import create_app

    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
