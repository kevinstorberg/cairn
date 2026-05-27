"""
Integration tests for TODO CRUD endpoints.

Tests:
- POST /todos creates todo
- GET /todos lists todos with pagination
- GET /todos/{id} retrieves specific todo
- PATCH /todos/{id} updates todo
- DELETE /todos/{id} deletes todo
- Validation errors (invalid status, priority)
- 404 on missing todo
- Timestamps auto-populate
"""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.app import create_app
from src.models.todo import TodoPriority, TodoStatus


@pytest.mark.integration
class TestTodoCRUDEndpoints:
    @pytest.fixture
    def client(self):
        """Create test client."""
        app = create_app()
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    @pytest.mark.asyncio
    async def test_create_todo(self, client, clean_db):
        """Test POST /todos creates a new todo."""
        async with client:
            response = await client.post(
                "/todos",
                json={"title": "Test task", "description": "Test description", "status": "pending", "priority": "high"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test task"
        assert data["description"] == "Test description"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_todo_minimal(self, client, clean_db):
        """Test creating todo with only required fields."""
        async with client:
            response = await client.post("/todos", json={"title": "Minimal task"})

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal task"
        assert data["description"] is None
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_list_todos(self, client, clean_db):
        """Test GET /todos lists all todos."""
        async with client:
            # Create multiple todos
            await client.post("/todos", json={"title": "Task 1"})
            await client.post("/todos", json={"title": "Task 2"})
            await client.post("/todos", json={"title": "Task 3"})

            # List all
            response = await client.get("/todos")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Task 1"
        assert data[1]["title"] == "Task 2"
        assert data[2]["title"] == "Task 3"

    @pytest.mark.asyncio
    async def test_list_todos_pagination(self, client, clean_db):
        """Test pagination works."""
        async with client:
            # Create 5 todos
            for i in range(5):
                await client.post("/todos", json={"title": f"Task {i+1}"})

            # Get first page
            response = await client.get("/todos?skip=0&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # Get second page
            response = await client.get("/todos?skip=2&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # Get third page
            response = await client.get("/todos?skip=4&limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1

    @pytest.mark.asyncio
    async def test_get_todo_by_id(self, client, clean_db):
        """Test GET /todos/{id} retrieves specific todo."""
        async with client:
            # Create a todo
            create_response = await client.post("/todos", json={"title": "Specific task"})
            todo_id = create_response.json()["id"]

            # Retrieve it
            response = await client.get(f"/todos/{todo_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Specific task"

    @pytest.mark.asyncio
    async def test_get_todo_not_found(self, client, clean_db):
        """Test 404 when todo doesn't exist."""
        async with client:
            fake_id = str(uuid4())
            response = await client.get(f"/todos/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    @pytest.mark.asyncio
    async def test_update_todo(self, client, clean_db):
        """Test PATCH /todos/{id} updates todo."""
        async with client:
            # Create a todo
            create_response = await client.post(
                "/todos", json={"title": "Original title", "status": "pending", "priority": "low"}
            )
            todo_id = create_response.json()["id"]

            # Update it
            response = await client.patch(
                f"/todos/{todo_id}", json={"title": "Updated title", "status": "completed", "priority": "high"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated title"
        assert data["status"] == "completed"
        assert data["priority"] == "high"

    @pytest.mark.asyncio
    async def test_update_todo_partial(self, client, clean_db):
        """Test partial update only changes specified fields."""
        async with client:
            # Create a todo
            create_response = await client.post(
                "/todos", json={"title": "Original", "description": "Original desc", "status": "pending"}
            )
            todo_id = create_response.json()["id"]

            # Update only title
            response = await client.patch(f"/todos/{todo_id}", json={"title": "New title"})

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New title"
        assert data["description"] == "Original desc"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_update_todo_not_found(self, client, clean_db):
        """Test 404 when updating non-existent todo."""
        async with client:
            fake_id = str(uuid4())
            response = await client.patch(f"/todos/{fake_id}", json={"title": "Updated"})

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    @pytest.mark.asyncio
    async def test_delete_todo(self, client, clean_db):
        """Test DELETE /todos/{id} deletes todo."""
        async with client:
            # Create a todo
            create_response = await client.post("/todos", json={"title": "To be deleted"})
            todo_id = create_response.json()["id"]

            # Delete it
            response = await client.delete(f"/todos/{todo_id}")
            assert response.status_code == 204

            # Verify it's gone
            get_response = await client.get(f"/todos/{todo_id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_todo_not_found(self, client, clean_db):
        """Test 404 when deleting non-existent todo."""
        async with client:
            fake_id = str(uuid4())
            response = await client.delete(f"/todos/{fake_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Todo not found"

    @pytest.mark.asyncio
    async def test_create_todo_validation_invalid_status(self, client, clean_db):
        """Test validation rejects invalid status."""
        async with client:
            response = await client.post("/todos", json={"title": "Test", "status": "invalid_status"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_todo_validation_invalid_priority(self, client, clean_db):
        """Test validation rejects invalid priority."""
        async with client:
            response = await client.post("/todos", json={"title": "Test", "priority": "invalid_priority"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_todo_validation_title_required(self, client, clean_db):
        """Test validation requires title."""
        async with client:
            response = await client.post("/todos", json={})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_timestamps_auto_populate(self, client, clean_db):
        """Test created_at and updated_at are auto-populated."""
        async with client:
            response = await client.post("/todos", json={"title": "Timestamp test"})

        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        assert "updated_at" in data
        assert data["created_at"] is not None
        assert data["updated_at"] is not None
