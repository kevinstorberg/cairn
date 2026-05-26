from memory.base import MemoryBackend


class MemoryService:
    def __init__(self, backend: MemoryBackend):
        self._backend = backend

    async def store(self, id: str, text: str, metadata: dict, embedding: list[float]) -> None:
        await self._backend.store(id, text, metadata, embedding)

    async def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict]:
        return await self._backend.search(query_embedding, limit=limit, filters=filters)

    async def delete(self, id: str) -> None:
        await self._backend.delete(id)
