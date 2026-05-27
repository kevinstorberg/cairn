import os

try:
    import redis.asyncio as redis
except ImportError:
    redis = None  # type: ignore


class RedisCacheBackend:
    def __init__(self):
        if redis is None:
            raise ImportError("RedisCacheBackend requires `poetry install --with redis`")

        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def set(self, key: str, value: str, ttl: float | None = None) -> None:
        if ttl is not None:
            await self._client.setex(key, int(ttl), value)
        else:
            await self._client.set(key, value)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._client.exists(key))

    async def close(self) -> None:
        """Close Redis connection."""
        await self._client.aclose()
