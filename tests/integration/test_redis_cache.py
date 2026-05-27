"""
Integration tests for Redis cache backend.

Tests:
- Redis connection
- Basic operations (get, set, delete, exists)
- TTL expiration
- Connection cleanup
"""

import asyncio

import pytest

try:
    from cache.backends.redis import RedisCacheBackend

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not installed")
@pytest.mark.integration
class TestRedisCacheBackend:
    @pytest.mark.asyncio
    async def test_redis_connection(self):
        """Test Redis backend can connect."""
        cache = RedisCacheBackend()
        # Should not raise
        await cache.set("test_connection", "ok")
        value = await cache.get("test_connection")
        assert value == "ok"
        await cache.delete("test_connection")
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_set_and_get(self):
        """Test Redis set and get operations."""
        cache = RedisCacheBackend()

        await cache.set("test_key", "test_value")
        value = await cache.get("test_key")
        assert value == "test_value"

        await cache.delete("test_key")
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_exists(self):
        """Test Redis exists operation."""
        cache = RedisCacheBackend()

        await cache.set("exists_key", "value")
        assert await cache.exists("exists_key") is True
        assert await cache.exists("nonexistent") is False

        await cache.delete("exists_key")
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_delete(self):
        """Test Redis delete operation."""
        cache = RedisCacheBackend()

        await cache.set("delete_key", "value")
        assert await cache.exists("delete_key") is True

        await cache.delete("delete_key")
        assert await cache.exists("delete_key") is False

        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_ttl_expiration(self):
        """Test Redis TTL expiration."""
        cache = RedisCacheBackend()

        # Set with 1 second TTL
        await cache.set("ttl_key", "expires", ttl=1)
        assert await cache.exists("ttl_key") is True

        # Wait for expiration
        await asyncio.sleep(1.2)

        # Should be expired
        assert await cache.exists("ttl_key") is False
        value = await cache.get("ttl_key")
        assert value is None

        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_no_ttl_persists(self):
        """Test Redis values without TTL persist."""
        cache = RedisCacheBackend()

        await cache.set("persist_key", "forever")
        await asyncio.sleep(0.5)

        # Should still exist
        assert await cache.exists("persist_key") is True
        value = await cache.get("persist_key")
        assert value == "forever"

        # Cleanup
        await cache.delete("persist_key")
        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_get_nonexistent(self):
        """Test getting nonexistent key returns None."""
        cache = RedisCacheBackend()

        value = await cache.get("never_set_key")
        assert value is None

        await cache.close()

    @pytest.mark.asyncio
    async def test_redis_multiple_keys(self):
        """Test multiple keys don't interfere."""
        cache = RedisCacheBackend()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"

        # Cleanup
        await cache.delete("key1")
        await cache.delete("key2")
        await cache.delete("key3")
        await cache.close()
