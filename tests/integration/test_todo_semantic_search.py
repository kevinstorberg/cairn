"""
Integration tests for TODO semantic search.

Tests:
- Embedding generation on todo creation
- Semantic search returns relevant todos
- Search with filters
- Embedding deletion on todo deletion
- Memory backend switching (FAISS, pgvector, pinecone)
"""

import pytest
from httpx import AsyncClient

from db.models.todo import Todo


@pytest.mark.integration
class TestTodoSemanticSearch:
    @pytest.mark.asyncio
    async def test_embedding_generated_on_create(self, client: AsyncClient, db_session, clean_db):
        """Test embedding is generated when todo is created."""
        # Create a todo
        response = await client.post("/todos", json={"title": "Deploy to production", "description": "Deploy v2.0 to prod"})
        assert response.status_code == 201
        todo = response.json()
        todo_id = todo["id"]

        # Verify embedding exists in memory backend
        from memory.backends import get_backend

        memory = get_backend()
        results = await memory.search(query_embedding=[0.0] * 384, limit=1)
        assert len(results) >= 1
        assert any(r["id"] == todo_id for r in results)

    @pytest.mark.asyncio
    async def test_semantic_search_finds_similar(self, client: AsyncClient, db_session, clean_db):
        """Test semantic search returns similar todos."""
        # Create several todos with different topics
        todos = [
            {"title": "Deploy to production", "description": "Release v2.0"},
            {"title": "Fix login bug", "description": "Users can't sign in"},
            {"title": "Update deployment scripts", "description": "Improve CI/CD pipeline"},
            {"title": "Write unit tests", "description": "Add tests for auth module"},
        ]

        for todo_data in todos:
            response = await client.post("/todos", json=todo_data)
            assert response.status_code == 201

        # Search for deployment-related todos
        response = await client.post("/todos/search?query=deployment%20production%20release&limit=3")
        assert response.status_code == 200
        results = response.json()

        # Should find deployment-related todos at the top
        assert len(results) > 0
        # Top results should be about deployment
        top_titles = [r["todo"]["title"] for r in results[:2]]
        assert any("Deploy" in t or "deployment" in t for t in top_titles)

    @pytest.mark.asyncio
    async def test_semantic_search_ranking(self, client: AsyncClient, db_session, clean_db):
        """Test semantic search ranks by relevance."""
        # Create todos
        todos = [
            {"title": "Fix critical production bug", "description": "Server crashes on startup"},
            {"title": "Production deployment checklist", "description": "Steps for deploying to prod"},
            {"title": "Buy groceries", "description": "Milk, eggs, bread"},
        ]

        for todo_data in todos:
            response = await client.post("/todos", json=todo_data)
            assert response.status_code == 201

        # Search for production
        response = await client.post("/todos/search?query=production&limit=3")
        assert response.status_code == 200
        results = response.json()

        # Scores should be descending
        assert len(results) >= 2
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

        # "Buy groceries" should have lowest score
        titles = [r["todo"]["title"] for r in results]
        if "Buy groceries" in titles:
            groceries_idx = titles.index("Buy groceries")
            assert groceries_idx == len(results) - 1  # Last result

    @pytest.mark.asyncio
    async def test_embedding_deleted_on_todo_delete(self, client: AsyncClient, db_session, clean_db):
        """Test embedding is deleted when todo is deleted."""
        # Create a todo
        response = await client.post("/todos", json={"title": "Test todo", "description": "Will be deleted"})
        assert response.status_code == 201
        todo_id = response.json()["id"]

        # Verify embedding exists
        from memory.backends import get_backend

        memory = get_backend()
        results = await memory.search(query_embedding=[0.0] * 384, limit=100)
        assert any(r["id"] == todo_id for r in results)

        # Delete todo
        response = await client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204

        # Verify embedding is gone
        results = await memory.search(query_embedding=[0.0] * 384, limit=100)
        assert not any(r["id"] == todo_id for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_results(self, client: AsyncClient, db_session, clean_db):
        """Test search with no todos returns empty list."""
        response = await client.post("/todos/search?query=anything&limit=10")
        assert response.status_code == 200
        results = response.json()
        assert results == []

    @pytest.mark.asyncio
    async def test_search_limit_respected(self, client: AsyncClient, db_session, clean_db):
        """Test search respects limit parameter."""
        # Create 10 todos
        for i in range(10):
            response = await client.post("/todos", json={"title": f"Todo {i}", "description": f"Description {i}"})
            assert response.status_code == 201

        # Search with limit=3
        response = await client.post("/todos/search?query=todo&limit=3")
        assert response.status_code == 200
        results = response.json()
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_includes_matched_text(self, client: AsyncClient, db_session, clean_db):
        """Test search results include matched text."""
        response = await client.post("/todos", json={"title": "Test task", "description": "With description"})
        assert response.status_code == 201

        response = await client.post("/todos/search?query=test&limit=1")
        assert response.status_code == 200
        results = response.json()

        assert len(results) > 0
        result = results[0]
        assert "todo" in result
        assert "score" in result
        assert "matched_text" in result
        assert result["matched_text"]  # Not empty

    @pytest.mark.asyncio
    async def test_embeddings_service_initialization(self):
        """Test embeddings service can be initialized."""
        from src.services.embeddings import EmbeddingsService

        service = EmbeddingsService()
        texts = ["test embedding"]
        embeddings = await service.embed(texts)

        assert len(embeddings) == 1
        assert len(embeddings[0]) == 384  # all-MiniLM-L6-v2 dimension

    @pytest.mark.asyncio
    async def test_faiss_backend_store_and_search(self):
        """Test FAISS backend directly."""
        from memory.backends.faiss import FAISSBackend

        backend = FAISSBackend()

        # Store a few entries
        await backend.store(
            id="1", text="Deploy to production", metadata={"title": "Deploy"}, embedding=[0.1] * 384
        )
        await backend.store(
            id="2", text="Fix login bug", metadata={"title": "Fix bug"}, embedding=[0.2] * 384
        )

        # Search
        results = await backend.search(query_embedding=[0.15] * 384, limit=2)
        assert len(results) == 2
        assert all("id" in r and "text" in r and "score" in r for r in results)

        # Delete
        await backend.delete("1")
        results = await backend.search(query_embedding=[0.1] * 384, limit=2)
        assert len(results) == 1
        assert results[0]["id"] == "2"

    @pytest.mark.asyncio
    async def test_todo_embeddings_service(self, db_session, clean_db):
        """Test TodoEmbeddingsService operations."""
        from uuid import uuid4

        from memory.backends import get_backend
        from src.services.embeddings import EmbeddingsService
        from src.services.todo_embeddings import TodoEmbeddingsService

        embeddings = EmbeddingsService()
        memory = get_backend()
        service = TodoEmbeddingsService(embeddings, memory)

        todo_id = uuid4()
        await service.embed_todo(todo_id, "Test title", "Test description")

        # Search for it
        results = await service.search_todos("test", limit=1)
        assert len(results) >= 1
        assert any(r["id"] == str(todo_id) for r in results)

        # Delete it
        await service.delete_todo_embedding(todo_id)
        results = await service.search_todos("test", limit=10)
        assert not any(r["id"] == str(todo_id) for r in results)
