"""Todo embeddings service for semantic search."""

from uuid import UUID

from memory.backends import get_backend
from memory.base import MemoryBackend
from src.services.embeddings import EmbeddingsService


class TodoEmbeddingsService:
    """Service for managing todo embeddings and semantic search."""

    def __init__(self, embeddings_service: EmbeddingsService, memory_backend: MemoryBackend):
        self.embeddings = embeddings_service
        self.memory = memory_backend

    async def embed_todo(self, todo_id: UUID, title: str, description: str | None = None) -> None:
        """Generate and store embedding for a todo."""
        # Combine title and description for embedding
        text = title
        if description:
            text = f"{title}\n{description}"

        # Generate embedding
        embeddings = await self.embeddings.embed([text])
        embedding = embeddings[0]

        # Store in memory backend
        await self.memory.store(
            id=str(todo_id), text=text, metadata={"title": title, "description": description or ""}, embedding=embedding
        )

    async def search_todos(
        self, query: str, limit: int = 10, filters: dict | None = None
    ) -> list[dict[str, str | float]]:
        """Semantic search for todos."""
        # Generate query embedding
        embeddings = await self.embeddings.embed([query])
        query_embedding = embeddings[0]

        # Search memory backend
        results = await self.memory.search(query_embedding, limit=limit, filters=filters)

        return results

    async def delete_todo_embedding(self, todo_id: UUID) -> None:
        """Delete todo embedding from memory backend."""
        await self.memory.delete(str(todo_id))
