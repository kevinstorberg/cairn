import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from db.connection import get_session
from src.app import create_app


@pytest.fixture
def app():
    """Create FastAPI app instance."""
    return create_app()


@pytest.fixture(scope="function")
def test_engine():
    """Create test database engine with no connection pooling."""
    engine = create_async_engine(
        "postgresql+asyncpg://localhost:5432/cairn_test",
        echo=False,
        poolclass=NullPool  # Critical: No pooling in tests
    )
    yield engine
    # Cleanup
    engine.sync_engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test session with rollback after each test."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
def app_with_test_db(test_engine):
    """Create app with overridden database dependency."""
    app = create_app()

    async def override_get_session():
        """Override get_session to use test engine."""
        async_session_maker = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session_maker() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session

    return app


@pytest_asyncio.fixture
async def client(app_with_test_db):
    """Create async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_test_db),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def clean_db(test_session):
    """Clean database before and after each test."""
    from sqlalchemy import text

    # Cleanup before test
    await test_session.execute(text("TRUNCATE TABLE todos CASCADE"))
    await test_session.commit()

    yield

    # Cleanup after test
    await test_session.execute(text("TRUNCATE TABLE todos CASCADE"))
    await test_session.commit()
