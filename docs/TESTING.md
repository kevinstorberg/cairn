# Testing Guide for Cairn

This guide covers testing patterns and best practices for applications built with Cairn.

## Table of Contents

- [Test Structure](#test-structure)
- [Fixtures Overview](#fixtures-overview)
- [Testing FastAPI Endpoints](#testing-fastapi-endpoints)
- [Database Testing](#database-testing)
- [Running Tests](#running-tests)
- [Mocking External Services](#mocking-external-services)
- [Common Patterns](#common-patterns)

---

## Test Structure

Cairn uses pytest with async support. Tests are organized by type:

```
tests/
├── conftest.py          # Global fixtures
├── unit/                # Unit tests (no external deps)
├── integration/         # Integration tests (DB, cache, etc.)
└── e2e/                 # End-to-end tests (full stack)
```

**Test markers**:
- `@pytest.mark.unit` - Fast, no external dependencies
- `@pytest.mark.integration` - Needs database, cache, etc.
- `@pytest.mark.e2e` - Full application tests
- `@pytest.mark.eval` - LLM evaluation tests (expensive, skip by default)

---

## Fixtures Overview

Cairn provides several fixtures in `tests/conftest.py`:

### `app` - Basic FastAPI app
```python
def test_app_creation(app):
    assert app.title == "Cairn"
```

### `test_engine` - Isolated test database engine
```python
def test_with_engine(test_engine):
    # Uses NullPool for test isolation
    pass
```

### `test_session` - Async database session
```python
@pytest.mark.asyncio
async def test_with_session(test_session):
    result = await test_session.execute(select(Todo))
    todos = result.scalars().all()
```

### `app_with_test_db` - App with overridden database dependency
```python
@pytest.mark.asyncio
async def test_endpoint(app_with_test_db):
    # App uses test_engine instead of production DB
    pass
```

### `client` - Async HTTP client
```python
@pytest.mark.asyncio
async def test_api_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
```

### `clean_db` - Automatic database cleanup
```python
@pytest.mark.asyncio
async def test_with_clean_db(client, clean_db):
    # Database is clean before and after test
    response = await client.post("/todos", json={"title": "Test"})
    assert response.status_code == 200
```

---

## Testing FastAPI Endpoints

### Basic Endpoint Test

```python
import pytest

@pytest.mark.asyncio
async def test_create_todo(client, clean_db):
    # Arrange
    todo_data = {
        "title": "Test Todo",
        "description": "Test description"
    }

    # Act
    response = await client.post("/todos", json=todo_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Todo"
    assert "id" in data
```

### Testing with Database Verification

```python
@pytest.mark.asyncio
async def test_todo_persisted_to_db(client, test_session, clean_db):
    # Create via API
    response = await client.post("/todos", json={"title": "Test"})
    todo_id = response.json()["id"]

    # Verify in database
    from sqlalchemy import select
    from db.models.todo import Todo

    result = await test_session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    todo = result.scalar_one()
    assert todo.title == "Test"
```

### Testing Validation Errors

```python
@pytest.mark.asyncio
async def test_validation_error(client):
    response = await client.post("/todos", json={"invalid": "data"})
    assert response.status_code == 422
    error = response.json()
    assert "detail" in error
```

---

## Database Testing

### Direct Database Operations

```python
@pytest.mark.asyncio
async def test_database_operations(test_session, clean_db):
    from db.models.todo import Todo, TodoStatus

    # Create
    todo = Todo(title="Test", status=TodoStatus.PENDING)
    test_session.add(todo)
    await test_session.commit()
    await test_session.refresh(todo)

    # Read
    from sqlalchemy import select
    result = await test_session.execute(
        select(Todo).where(Todo.id == todo.id)
    )
    fetched = result.scalar_one()
    assert fetched.title == "Test"

    # Update
    fetched.status = TodoStatus.COMPLETED
    await test_session.commit()

    # Delete
    await test_session.delete(fetched)
    await test_session.commit()
```

### Testing Relationships

```python
@pytest.mark.asyncio
async def test_parent_child_relationship(test_session, clean_db):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from db.models.todo import Todo

    # Create parent and children
    parent = Todo(title="Parent")
    child1 = Todo(title="Child 1", parent_id=parent.id)
    child2 = Todo(title="Child 2", parent_id=parent.id)

    test_session.add_all([parent, child1, child2])
    await test_session.commit()

    # Query with eager loading
    result = await test_session.execute(
        select(Todo)
        .where(Todo.id == parent.id)
        .options(selectinload(Todo.subtasks))
    )
    fetched_parent = result.scalar_one()

    assert len(fetched_parent.subtasks) == 2
```

---

## Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run specific test types
```bash
# Unit tests only (fast)
poetry run pytest -m unit

# Integration tests (needs DB)
poetry run pytest -m integration

# End-to-end tests
poetry run pytest -m e2e

# Skip expensive evaluation tests
poetry run pytest -m "not eval"
```

### Run tests in parallel
```bash
# Install pytest-xdist
poetry add --group dev pytest-xdist

# Run with 4 workers
poetry run pytest -n 4
```

### Run with coverage
```bash
poetry run pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### Run specific test file
```bash
poetry run pytest tests/integration/test_todos.py -v
```

### Run specific test function
```bash
poetry run pytest tests/integration/test_todos.py::test_create_todo -v
```

---

## Mocking External Services

### Mocking LLM Calls

```python
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_with_mocked_llm(client):
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = AIMessage(content="Mocked response")

    with patch("src.graphs.breakdown.build_llm", return_value=mock_llm):
        response = await client.post("/todos/123/breakdown")
        assert response.status_code == 200
```

### Mocking Memory Backend

```python
@pytest.mark.asyncio
async def test_with_mocked_memory():
    from memory.backends import reset_backend
    from unittest.mock import AsyncMock

    # Reset singleton
    reset_backend()

    # Mock the backend
    mock_backend = AsyncMock()
    mock_backend.search.return_value = [
        {"id": "1", "text": "test", "score": 0.9}
    ]

    with patch("memory.backends.get_backend", return_value=mock_backend):
        # Your test here
        pass
```

### Mocking S3 Storage

```python
@pytest.mark.asyncio
async def test_with_mocked_s3():
    from unittest.mock import AsyncMock

    mock_storage = AsyncMock()
    mock_storage.upload.return_value = None
    mock_storage.download.return_value = b"test content"

    with patch("assets.backends.get_storage_backend", return_value=mock_storage):
        # Your test here
        pass
```

### Mocking Redis Cache

```python
@pytest.mark.asyncio
async def test_with_mocked_cache():
    from unittest.mock import AsyncMock

    mock_cache = AsyncMock()
    mock_cache.get.return_value = "cached_value"

    with patch("cache.backends.get_cache_backend", return_value=mock_cache):
        # Your test here
        pass
```

---

## Common Patterns

### Testing Environment-Specific Behavior

```python
import os
from src.settings import get_settings, reset_settings

def test_production_settings():
    # Save original
    original_env = os.environ.get("APP_ENV")

    try:
        # Change environment
        os.environ["APP_ENV"] = "production"
        os.environ["DATABASE_URL_PRODUCTION"] = "postgresql://..."

        # Reset settings cache
        reset_settings()

        # Test
        settings = get_settings()
        assert settings.APP_ENV == "production"

    finally:
        # Restore
        if original_env:
            os.environ["APP_ENV"] = original_env
        else:
            os.environ.pop("APP_ENV", None)
        reset_settings()
```

### Testing Background Jobs

```python
@pytest.mark.asyncio
async def test_background_job():
    from src.jobs.daily_summary import DailySummaryJob

    job = DailySummaryJob()

    # Execute job
    await job.execute()

    # Verify results
    # ...
```

### Testing WebSocket Connections

```python
@pytest.mark.asyncio
async def test_websocket_connection():
    from src.websockets.manager import ConnectionManager

    manager = ConnectionManager()

    class MockWebSocket:
        async def accept(self):
            pass

        async def send_json(self, data):
            self.last_message = data

    ws = MockWebSocket()
    await manager.connect(ws, "test_room")

    # Broadcast message
    await manager.broadcast("test_room", {"type": "test", "data": "hello"})

    assert ws.last_message["type"] == "test"

    # Cleanup
    manager.disconnect(ws, "test_room")
```

### Testing with Fixtures Cleanup

```python
@pytest.fixture
async def sample_todos(test_session):
    """Create sample todos for testing."""
    from db.models.todo import Todo

    todos = [
        Todo(title=f"Todo {i}") for i in range(3)
    ]
    test_session.add_all(todos)
    await test_session.commit()

    yield todos

    # Cleanup happens automatically via clean_db fixture
```

---

## Best Practices

### ✅ Do

- Use `@pytest.mark.asyncio` for async tests
- Use `clean_db` fixture for tests that modify database
- Mock external services (LLM, S3, etc.) in unit tests
- Use descriptive test names: `test_create_todo_with_valid_data`
- Test happy path AND error cases
- Use `test_session` for database operations
- Use `client` for API testing with dependency overrides
- Reset singletons between tests (`reset_backend()`, `reset_settings()`)

### ❌ Don't

- Don't use `app` fixture for database tests (use `app_with_test_db`)
- Don't forget `await` on async operations
- Don't share state between tests
- Don't use production credentials in tests
- Don't skip cleanup (use fixtures properly)
- Don't use `loop.run_until_complete()` in async tests (use `await`)

---

## Troubleshooting

### "Operation in progress" errors

**Problem**: Multiple database engines conflict.

**Solution**: Use `app_with_test_db` fixture instead of `app`:
```python
# Wrong
async def test_endpoint(app, test_session):
    client = AsyncClient(app=app, base_url="http://test")

# Correct
async def test_endpoint(client, clean_db):
    # client fixture already uses app_with_test_db
```

### "Event loop already running" errors

**Problem**: Using `loop.run_until_complete()` in async context.

**Solution**: Use `await` instead:
```python
# Wrong
loop = asyncio.get_event_loop()
result = loop.run_until_complete(some_async_func())

# Correct
result = await some_async_func()
```

### Stale settings in tests

**Problem**: Settings don't reflect environment changes.

**Solution**: Call `reset_settings()`:
```python
from src.settings import reset_settings

os.environ["APP_ENV"] = "test"
reset_settings()  # Clear cache
settings = get_settings()  # Fresh settings
```

### Memory backend not persisting

**Problem**: `get_backend()` returns new instance each time.

**Solution**: Already fixed in template! But if you need to reset:
```python
from memory.backends import reset_backend

reset_backend()  # Clear singleton
backend = get_backend()  # Fresh instance
```

---

## Further Reading

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
- [FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy async testing](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
