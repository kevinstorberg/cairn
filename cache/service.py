from cache.base import CacheBackend


class CacheService:
    def __init__(self, backend: CacheBackend) -> None:
        self._backend = backend

    async def get(self, key: str) -> str | None:
        return await self._backend.get(key)

    async def set(self, key: str, value: str, ttl: float | None = None) -> None:
        await self._backend.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        await self._backend.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._backend.exists(key)
