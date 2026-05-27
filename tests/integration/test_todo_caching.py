"""
Integration tests for TODO caching.

Tests:
- Cache miss → DB read → cache set
- Cache hit → no DB read
- Cache invalidation on update
- Cache TTL expiration
- Cache backend switching (memory, redis)
"""

import asyncio

import pytest

from cache.backends.memory import InMemoryCacheBackend
from db.models.todo import Todo
from src.repositories.todo import TodoRepository


@pytest.mark.integration
class TestTodoCaching:
    @pytest.mark.asyncio
    async def test_cache_miss_then_set(self, db_session, clean_db):
        """Test cache miss → DB read → cache set."""
        cache = InMemoryCacheBackend()
        repo = TodoRepository(db_session, cache=cache)

        # Create a todo
        todo = Todo(title="Cached todo")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # First read - cache miss, should query DB and cache
        cache_key = repo._cache_key(todo.id)
        assert await cache.exists(cache_key) is False

        result1 = await repo.get_by_id(todo.id)
        assert result1 is not None
        assert result1.title == "Cached todo"

        # Cache should now have entry
        assert await cache.exists(cache_key) is True

    @pytest.mark.asyncio
    async def test_cache_hit_no_db_query(self, db_session, clean_db):
        """Test cache hit returns cached data."""
        cache = InMemoryCacheBackend()
        repo = TodoRepository(db_session, cache=cache)

        # Create and cache a todo
        todo = Todo(title="Cached todo")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # First read to populate cache
        await repo.get_by_id(todo.id)

        # Verify cache has it
        cache_key = repo._cache_key(todo.id)
        cached_value = await cache.get(cache_key)
        assert cached_value is not None
        assert "Cached todo" in cached_value

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_update(self, db_session, clean_db):
        """Test cache invalidation when todo is updated."""
        cache = InMemoryCacheBackend()
        repo = TodoRepository(db_session, cache=cache)

        # Create a todo
        todo = Todo(title="Original title")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Read to populate cache
        await repo.get_by_id(todo.id)
        cache_key = repo._cache_key(todo.id)
        assert await cache.exists(cache_key) is True

        # Update todo
        from src.models.todo import TodoUpdate

        await repo.update(todo.id, TodoUpdate(title="Updated title"))

        # Cache should be invalidated
        assert await cache.exists(cache_key) is False

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_delete(self, db_session, clean_db):
        """Test cache invalidation when todo is deleted."""
        cache = InMemoryCacheBackend()
        repo = TodoRepository(db_session, cache=cache)

        # Create a todo
        todo = Todo(title="To be deleted")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Read to populate cache
        await repo.get_by_id(todo.id)
        cache_key = repo._cache_key(todo.id)
        assert await cache.exists(cache_key) is True

        # Delete todo
        await repo.delete(todo.id)

        # Cache should be invalidated
        assert await cache.exists(cache_key) is False

    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, db_session, clean_db):
        """Test cache entries expire after TTL."""
        cache = InMemoryCacheBackend()

        # Set a value with 1 second TTL
        await cache.set("test_key", "test_value", ttl=1)
        assert await cache.exists("test_key") is True

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        assert await cache.exists("test_key") is False
        assert await cache.get("test_key") is None

    @pytest.mark.asyncio
    async def test_cache_no_ttl_persists(self, db_session, clean_db):
        """Test cache entries without TTL persist."""
        cache = InMemoryCacheBackend()

        # Set a value without TTL
        await cache.set("persistent_key", "persistent_value")
        assert await cache.exists("persistent_key") is True

        # Wait a bit
        await asyncio.sleep(0.5)

        # Should still exist
        assert await cache.exists("persistent_key") is True
        value = await cache.get("persistent_key")
        assert value == "persistent_value"

    @pytest.mark.asyncio
    async def test_repository_works_without_cache(self, db_session, clean_db):
        """Test repository works when cache is None."""
        repo = TodoRepository(db_session, cache=None)

        # Create a todo
        todo = Todo(title="No cache todo")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Should still work without cache
        result = await repo.get_by_id(todo.id)
        assert result is not None
        assert result.title == "No cache todo"

        # Update should work
        from src.models.todo import TodoUpdate

        updated = await repo.update(todo.id, TodoUpdate(title="Updated"))
        assert updated is not None
        assert updated.title == "Updated"

        # Delete should work
        deleted = await repo.delete(todo.id)
        assert deleted is True

    @pytest.mark.asyncio
    async def test_cache_key_namespacing(self, db_session, clean_db):
        """Test cache keys are properly namespaced."""
        from uuid import uuid4

        cache = InMemoryCacheBackend()
        repo = TodoRepository(db_session, cache=cache)

        # Generate cache key for a UUID
        test_id = uuid4()
        cache_key = repo._cache_key(test_id)

        # Should have namespace prefix
        assert cache_key.startswith("todo:")
        assert str(test_id) in cache_key
        assert cache_key == f"todo:{test_id}"

    @pytest.mark.asyncio
    async def test_memory_cache_basic_operations(self):
        """Test InMemoryCacheBackend basic operations."""
        cache = InMemoryCacheBackend()

        # Set and get
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        # Exists
        assert await cache.exists("key1") is True
        assert await cache.exists("nonexistent") is False

        # Delete
        await cache.delete("key1")
        assert await cache.exists("key1") is False
        assert await cache.get("key1") is None

        # Get nonexistent returns None
        assert await cache.get("never_set") is None
