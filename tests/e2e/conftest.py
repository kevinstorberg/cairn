"""E2E test fixtures."""

import pytest
from sqlalchemy import text

from db.connection import get_session_factory


@pytest.fixture
async def clean_db():
    """Clean database before each test."""
    factory = get_session_factory()
    async with factory() as session:
        # Clean all test data
        await session.execute(text("DELETE FROM todo_embeddings"))
        await session.execute(text("DELETE FROM todos"))
        await session.commit()

    yield

    # Cleanup after test
    async with factory() as session:
        await session.execute(text("DELETE FROM todo_embeddings"))
        await session.execute(text("DELETE FROM todos"))
        await session.commit()
