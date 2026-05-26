from memory.base import MemoryBackend


class PineconeBackend(MemoryBackend):
    async def store(self, id: str, text: str, metadata: dict, embedding: list[float]) -> None:
        raise NotImplementedError("PineconeBackend requires `poetry install --with pinecone`")

    async def search(self, query_embedding: list[float], limit: int = 10, filters: dict | None = None) -> list[dict]:
        raise NotImplementedError("PineconeBackend requires `poetry install --with pinecone`")

    async def delete(self, id: str) -> None:
        raise NotImplementedError("PineconeBackend requires `poetry install --with pinecone`")
