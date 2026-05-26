from memory.base import MemoryBackend


class PGVectorBackend(MemoryBackend):
    async def store(self, id: str, text: str, metadata: dict, embedding: list[float]) -> None:
        raise NotImplementedError("PGVectorBackend requires `poetry install --with pgvector`")

    async def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict]:
        raise NotImplementedError("PGVectorBackend requires `poetry install --with pgvector`")

    async def delete(self, id: str) -> None:
        raise NotImplementedError("PGVectorBackend requires `poetry install --with pgvector`")
