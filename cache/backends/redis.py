

class RedisCacheBackend:
    async def get(self, key: str) -> str | None:
        raise NotImplementedError("RedisCacheBackend requires `poetry install --with redis`")

    async def set(self, key: str, value: str, ttl: float | None = None) -> None:
        raise NotImplementedError("RedisCacheBackend requires `poetry install --with redis`")

    async def delete(self, key: str) -> None:
        raise NotImplementedError("RedisCacheBackend requires `poetry install --with redis`")

    async def exists(self, key: str) -> bool:
        raise NotImplementedError("RedisCacheBackend requires `poetry install --with redis`")
