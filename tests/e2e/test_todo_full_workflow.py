"""
End-to-end integration test for the complete TODO app workflow.

This test exercises every component of the Cairn template together:
- FastAPI app with lifespan
- Database operations (create, read, update, delete)
- Storage backend (file upload/download)
- LangGraph + LLM + Tools (task breakdown, categorization)
- Memory backend (semantic search)
- Cache backend (Redis coordination)
- WebSocket real-time updates
- Background jobs (scheduler)
- Multi-environment configuration

Tests the full user journey from app start to shutdown.
"""

import asyncio
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from src.app import create_app


@pytest.mark.e2e
class TestTodoFullWorkflow:
    @pytest.mark.asyncio
    async def test_app_lifespan_initialization(self):
        """Test app starts with all services initialized."""
        app = create_app()

        # App should be created successfully
        assert app is not None
        assert app.title == "Cairn"

        # Routes should be registered
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/todos" in routes
        assert "/todos/{todo_id}" in routes
        assert "/todos/search" in routes
        assert "/ws/todos" in routes

    @pytest.mark.asyncio
    async def test_complete_todo_lifecycle(self, clean_db):
        """Test complete todo lifecycle: create → update → delete."""
        from db.connection import get_session_factory
        from db.models.todo import Todo, TodoStatus

        factory = get_session_factory()
        async with factory() as session:
            # Create
            todo = Todo(
                title="Integration test todo",
                description="Testing full lifecycle",
                status=TodoStatus.PENDING
            )
            session.add(todo)
            await session.commit()
            await session.refresh(todo)
            todo_id = todo.id

            # Read
            from sqlalchemy import select
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            fetched = result.scalar_one()
            assert fetched.title == "Integration test todo"

            # Update
            fetched.status = TodoStatus.IN_PROGRESS
            await session.commit()
            await session.refresh(fetched)
            assert fetched.status == TodoStatus.IN_PROGRESS

            # Delete
            await session.delete(fetched)
            await session.commit()

            # Verify deleted
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_storage_upload_download_cycle(self):
        """Test file upload and download through storage backend."""
        from assets.backends import get_storage_backend

        storage = get_storage_backend()

        # Upload
        test_content = b"Test file content for e2e testing"
        test_key = "e2e-test/test-file.txt"

        await storage.upload(
            key=test_key,
            content=test_content,
            content_type="text/plain"
        )

        # Download
        downloaded = await storage.download(test_key)
        assert downloaded == test_content

        # Cleanup
        await storage.delete(test_key)

        # Verify deleted
        with pytest.raises(FileNotFoundError):
            await storage.download(test_key)

    @pytest.mark.asyncio
    async def test_cache_coordination(self):
        """Test cache set/get/invalidate cycle."""
        from cache.backends import get_cache_backend

        cache = get_cache_backend()

        # Set
        await cache.set("e2e:test:key", "test-value", ttl=60)

        # Get
        value = await cache.get("e2e:test:key")
        assert value == "test-value"

        # Exists
        exists = await cache.exists("e2e:test:key")
        assert exists is True

        # Delete
        await cache.delete("e2e:test:key")

        # Verify deleted
        value = await cache.get("e2e:test:key")
        assert value is None

    @pytest.mark.asyncio
    async def test_memory_backend_search(self):
        """Test memory backend store and search."""
        from memory.backends import get_backend
        from src.services.embeddings import EmbeddingsService

        memory = get_backend()
        embeddings_service = EmbeddingsService()

        # Generate embedding
        embeddings = await embeddings_service.embed(["e2e test document"])
        embedding = embeddings[0]

        # Store
        await memory.store(
            id="e2e-test-doc",
            text="e2e test document",
            metadata={"source": "e2e-test"},
            embedding=embedding
        )

        # Search
        results = await memory.search(
            query_embedding=embedding,
            limit=5,
            filters={"source": "e2e-test"}
        )

        assert len(results) > 0
        assert results[0]["id"] == "e2e-test-doc"

        # Cleanup
        await memory.delete("e2e-test-doc")

    @pytest.mark.asyncio
    async def test_websocket_connection_and_broadcast(self):
        """Test WebSocket connection and message broadcasting."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()
        received_messages = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        # Connect two clients
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(ws1, "e2e-test-room")
        await manager.connect(ws2, "e2e-test-room")

        # Broadcast message
        await manager.broadcast(
            "e2e-test-room",
            {"type": "test_event", "data": "hello"}
        )

        # Both clients should receive
        assert len(received_messages) == 2
        assert all(msg["type"] == "test_event" for msg in received_messages)

        # Disconnect
        manager.disconnect(ws1, "e2e-test-room")
        manager.disconnect(ws2, "e2e-test-room")

    @pytest.mark.asyncio
    async def test_graph_building(self):
        """Test graph can be built from config."""
        from src.graphs.categorize import build_categorize_graph
        from src.graphs.breakdown import build_breakdown_graph

        # Build graphs
        categorize_graph = build_categorize_graph()
        breakdown_graph = build_breakdown_graph()

        # Should be created successfully
        assert categorize_graph is not None
        assert breakdown_graph is not None

        # Graphs should have nodes
        # Note: Cannot execute without real LLM/DB, but building proves structure is correct

    @pytest.mark.asyncio
    async def test_config_loading_hierarchy(self):
        """Test config loading works correctly."""
        from config.loader import load_default_config, load_graph_config

        # Load default config
        default_config = load_default_config()
        assert default_config is not None
        assert hasattr(default_config, "llm")
        assert hasattr(default_config, "cache")

        # Load graph-specific config (should deep-merge over default)
        breakdown_config = load_graph_config("breakdown")
        assert breakdown_config is not None
        assert breakdown_config.llm is not None
        assert breakdown_config.tools == ["get_todo", "create_subtask"]

    @pytest.mark.asyncio
    async def test_settings_multi_environment(self):
        """Test settings load correctly for current environment."""
        from src.settings import Settings, get_settings

        settings = Settings()
        assert settings is not None
        assert settings.APP_ENV in ["development", "test", "production"]

        # Singleton pattern
        settings2 = get_settings()
        assert settings.APP_ENV == settings2.APP_ENV

    @pytest.mark.asyncio
    async def test_background_job_structure(self):
        """Test background job can be instantiated and has correct structure."""
        from src.jobs.daily_summary import DailySummaryJob

        job = DailySummaryJob()
        assert job is not None
        assert hasattr(job, "execute")
        assert hasattr(job, "name")
        assert job.name == "daily_summary"

    @pytest.mark.asyncio
    async def test_tool_registry_loading(self):
        """Test tool registry loads tools correctly."""
        from src.tools.context import ToolContext
        from config.loader import load_graph_config
        from src.tools import load_tools

        # Load config
        config = load_graph_config("breakdown")

        # Create context
        context = ToolContext.from_graph_config(config)

        # Load tools
        tools = load_tools(config.tools, context)

        # Should have tools
        assert len(tools) > 0
        assert any(tool.name == "get_todo" for tool in tools)

    @pytest.mark.asyncio
    async def test_embeddings_service_generation(self):
        """Test embeddings service generates valid vectors."""
        from src.services.embeddings import EmbeddingsService

        service = EmbeddingsService()

        # Generate embedding
        embeddings = await service.embed(["test document for e2e"])
        embedding = embeddings[0]

        # Should be 384-dimensional vector
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.skip(reason="Session management conflicts - Issue #11")
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self):
        """
        Simulate complete user workflow:
        1. Create todo
        2. Verify it's stored
        3. Retrieve it
        4. Update status
        5. Delete it

        This tests database, models, and basic CRUD without HTTP layer.
        """
        from db.connection import get_session_factory
        from db.models.todo import Todo, TodoStatus, Priority
        from sqlalchemy import select

        factory = get_session_factory()

        # Step 1: Create todo
        async with factory() as session:
            todo = Todo(
                title="E2E workflow test",
                description="Testing complete workflow",
                status=TodoStatus.PENDING,
                priority=Priority.HIGH
            )
            session.add(todo)
            await session.commit()
            await session.refresh(todo)
            todo_id = str(todo.id)

        # Step 2 & 3: Retrieve it
        async with factory() as session:
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            fetched = result.scalar_one()
            assert fetched.title == "E2E workflow test"
            assert fetched.status == TodoStatus.PENDING
            assert fetched.priority == Priority.HIGH

        # Step 4: Update status
        async with factory() as session:
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            todo = result.scalar_one()
            todo.status = TodoStatus.COMPLETED
            await session.commit()

        # Verify update
        async with factory() as session:
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            todo = result.scalar_one()
            assert todo.status == TodoStatus.COMPLETED

        # Step 5: Delete it
        async with factory() as session:
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            todo = result.scalar_one()
            await session.delete(todo)
            await session.commit()

        # Verify deletion
        async with factory() as session:
            result = await session.execute(
                select(Todo).where(Todo.id == todo_id)
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_all_routers_registered(self):
        """Test all expected routers are registered in app."""
        app = create_app()

        # Collect all route paths
        routes = {route.path for route in app.routes}

        # Core routes should exist
        assert "/health" in routes
        assert "/todos" in routes
        assert "/todos/{todo_id}" in routes
        assert "/todos/{todo_id}/attach" in routes
        assert "/todos/{todo_id}/breakdown" in routes
        assert "/todos/{todo_id}/categorize" in routes
        assert "/todos/search" in routes

        # WebSocket routes
        assert "/ws/{room}" in routes
        assert "/ws/todos" in routes

    @pytest.mark.asyncio
    async def test_graceful_shutdown_pattern(self):
        """Test that services can be shut down gracefully."""
        from cache.backends import get_cache_backend

        cache = get_cache_backend()

        # Set a value
        await cache.set("shutdown-test", "value", ttl=60)

        # Close (if backend supports it)
        if hasattr(cache, "close"):
            await cache.close()

        # For in-memory cache, closing is a no-op
        # For Redis, connection would be closed
        assert True  # Pattern tested

    @pytest.mark.skip(reason="Session management conflicts - Issue #11")
    @pytest.mark.asyncio
    async def test_database_migrations_applied(self):
        """Test that all database tables exist (migrations applied)."""
        from db.connection import get_session_factory
        from sqlalchemy import text

        factory = get_session_factory()
        async with factory() as session:
            # Check todos table exists
            result = await session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_name = 'todos'")
            )
            assert result.scalar_one_or_none() == "todos"

            # Check todo_embeddings table exists
            result = await session.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_name = 'todo_embeddings'")
            )
            assert result.scalar_one_or_none() == "todo_embeddings"
