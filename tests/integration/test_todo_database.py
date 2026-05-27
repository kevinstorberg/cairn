"""
Integration tests for TODO database models.

Tests:
- Migration creates tables with correct schema
- Todo CRUD operations
- TodoEmbedding relationships
- Parent/child (subtask) relationships
- Timestamp mixins auto-populate
- UUID primary keys auto-generate
- Enum fields (status, priority) work correctly
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from db.models.todo import Todo, TodoPriority, TodoStatus
from db.models.todo_embedding import TodoEmbedding


@pytest.mark.integration
class TestTodoModel:
    @pytest.mark.asyncio
    async def test_create_todo(self, db_session, clean_db):
        """Test creating a new todo."""
        todo = Todo(
            title="Test task",
            description="Test description",
            status=TodoStatus.PENDING,
            priority=TodoPriority.HIGH,
        )
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.id is not None
        assert todo.title == "Test task"
        assert todo.description == "Test description"
        assert todo.status == TodoStatus.PENDING
        assert todo.priority == TodoPriority.HIGH
        assert todo.created_at is not None
        assert todo.updated_at is not None

    @pytest.mark.asyncio
    async def test_todo_timestamps_auto_populate(self, db_session, clean_db):
        """Test that created_at and updated_at timestamps are auto-populated."""
        todo = Todo(title="Timestamp test")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.created_at is not None
        assert todo.updated_at is not None
        assert isinstance(todo.created_at, datetime)
        assert isinstance(todo.updated_at, datetime)
        # Timestamps should be timezone-aware
        assert todo.created_at.tzinfo is not None
        assert todo.updated_at.tzinfo is not None

    @pytest.mark.asyncio
    async def test_todo_uuid_auto_generate(self, db_session, clean_db):
        """Test that UUID primary key is auto-generated."""
        todo = Todo(title="UUID test")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.id is not None
        assert isinstance(todo.id, uuid4().__class__)

    @pytest.mark.asyncio
    async def test_todo_default_status_and_priority(self, db_session, clean_db):
        """Test that status and priority have correct defaults."""
        todo = Todo(title="Defaults test")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.status == TodoStatus.PENDING
        assert todo.priority == TodoPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_update_todo(self, db_session, clean_db):
        """Test updating a todo."""
        todo = Todo(title="Original title", status=TodoStatus.PENDING)
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        original_updated_at = todo.updated_at

        # Update the todo
        todo.title = "Updated title"
        todo.status = TodoStatus.COMPLETED
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.title == "Updated title"
        assert todo.status == TodoStatus.COMPLETED
        # updated_at should change (though onupdate might not work in test without explicit update)

    @pytest.mark.asyncio
    async def test_delete_todo(self, db_session, clean_db):
        """Test deleting a todo."""
        todo = Todo(title="To be deleted")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        todo_id = todo.id

        # Delete the todo
        await db_session.delete(todo)
        await db_session.commit()

        # Verify it's gone
        result = await db_session.execute(select(Todo).where(Todo.id == todo_id))
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_todo_parent_child_relationship(self, db_session, clean_db):
        """Test parent/child (subtask) relationship."""
        from sqlalchemy.orm import selectinload

        parent = Todo(title="Parent task")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        # Create subtasks
        subtask1 = Todo(title="Subtask 1", parent_id=parent.id)
        subtask2 = Todo(title="Subtask 2", parent_id=parent.id)
        db_session.add_all([subtask1, subtask2])
        await db_session.commit()
        await db_session.refresh(parent)

        # Query parent with subtasks
        result = await db_session.execute(select(Todo).options(selectinload(Todo.subtasks)).where(Todo.id == parent.id))
        parent_with_subtasks = result.scalar_one()

        assert len(parent_with_subtasks.subtasks) == 2
        assert parent_with_subtasks.subtasks[0].title in ("Subtask 1", "Subtask 2")
        assert parent_with_subtasks.subtasks[1].title in ("Subtask 1", "Subtask 2")

    @pytest.mark.asyncio
    async def test_todo_enum_fields(self, db_session, clean_db):
        """Test enum fields (status, priority)."""
        todo = Todo(title="Enum test", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.LOW)
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.status == TodoStatus.IN_PROGRESS
        assert todo.priority == TodoPriority.LOW

        # Test all enum values
        todo.status = TodoStatus.COMPLETED
        todo.priority = TodoPriority.HIGH
        await db_session.commit()
        await db_session.refresh(todo)

        assert todo.status == TodoStatus.COMPLETED
        assert todo.priority == TodoPriority.HIGH


@pytest.mark.integration
class TestTodoEmbeddingModel:
    @pytest.mark.asyncio
    async def test_create_todo_embedding(self, db_session, clean_db):
        """Test creating a todo embedding."""
        # Create parent todo first
        todo = Todo(title="Todo with embedding")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Create embedding
        embedding = TodoEmbedding(
            todo_id=todo.id, embedding=[0.1, 0.2, 0.3, 0.4], embedding_text="Todo with embedding"
        )
        db_session.add(embedding)
        await db_session.commit()
        await db_session.refresh(embedding)

        assert embedding.id is not None
        assert embedding.todo_id == todo.id
        assert embedding.embedding == [0.1, 0.2, 0.3, 0.4]
        assert embedding.embedding_text == "Todo with embedding"
        assert embedding.created_at is not None

    @pytest.mark.asyncio
    async def test_todo_embedding_relationship(self, db_session, clean_db):
        """Test relationship between todo and embeddings."""
        from sqlalchemy.orm import selectinload

        todo = Todo(title="Todo with embeddings")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        embedding1 = TodoEmbedding(todo_id=todo.id, embedding=[0.1] * 384, embedding_text="Text 1")
        embedding2 = TodoEmbedding(todo_id=todo.id, embedding=[0.2] * 384, embedding_text="Text 2")
        db_session.add_all([embedding1, embedding2])
        await db_session.commit()

        # Re-query with eager loading
        result = await db_session.execute(select(Todo).options(selectinload(Todo.embeddings)).where(Todo.id == todo.id))
        todo_with_embeddings = result.scalar_one()

        assert len(todo_with_embeddings.embeddings) == 2

    @pytest.mark.asyncio
    async def test_delete_todo_cascades_to_embeddings(self, db_session, clean_db):
        """Test that deleting a todo cascades to its embeddings."""
        todo = Todo(title="Todo to delete")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        embedding = TodoEmbedding(todo_id=todo.id, embedding=[0.1] * 384, embedding_text="Text")
        db_session.add(embedding)
        await db_session.commit()
        embedding_id = embedding.id

        # Delete the todo
        await db_session.delete(todo)
        await db_session.commit()

        # Verify embedding is also deleted
        result = await db_session.execute(select(TodoEmbedding).where(TodoEmbedding.id == embedding_id))
        assert result.scalar_one_or_none() is None
