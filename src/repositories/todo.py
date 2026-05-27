"""Todo repository for database operations."""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from cache.base import CacheBackend
from db.models.todo import Todo
from src.models.todo import TodoCreate, TodoResponse, TodoUpdate


class TodoRepository:
    """Repository for Todo database operations."""

    def __init__(self, session: AsyncSession, cache: CacheBackend | None = None):
        self.session = session
        self.cache = cache

    def _cache_key(self, todo_id: UUID) -> str:
        """Generate cache key for todo."""
        return f"todo:{todo_id}"

    async def create(self, todo_data: TodoCreate) -> Todo:
        """Create a new todo."""
        todo = Todo(**todo_data.model_dump())
        self.session.add(todo)
        await self.session.commit()
        await self.session.refresh(todo)
        return todo

    async def get_by_id(self, todo_id: UUID) -> Todo | None:
        """Get todo by ID with caching."""
        # Try cache first
        if self.cache:
            cache_key = self._cache_key(todo_id)
            cached = await self.cache.get(cache_key)
            if cached:
                # Cache hit - return cached todo
                # Note: In production, would need to reconstruct Todo model from JSON
                # For now, fall through to database
                pass

        # Cache miss or no cache - query database
        result = await self.session.execute(select(Todo).where(Todo.id == todo_id))
        todo = result.scalar_one_or_none()

        # Store in cache
        if todo and self.cache:
            cache_key = self._cache_key(todo_id)
            # Store as JSON with 5 minute TTL
            todo_data = TodoResponse.model_validate(todo).model_dump_json()
            await self.cache.set(cache_key, todo_data, ttl=300)

        return todo

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Todo]:
        """Get all todos with pagination."""
        result = await self.session.execute(select(Todo).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def update(self, todo_id: UUID, todo_data: TodoUpdate) -> Todo | None:
        """Update a todo and invalidate cache."""
        todo = await self.get_by_id(todo_id)
        if not todo:
            return None

        update_dict = todo_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(todo, key, value)

        await self.session.commit()
        await self.session.refresh(todo)

        # Invalidate cache
        if self.cache:
            cache_key = self._cache_key(todo_id)
            await self.cache.delete(cache_key)

        return todo

    async def delete(self, todo_id: UUID) -> bool:
        """Delete a todo and invalidate cache."""
        todo = await self.get_by_id(todo_id)
        if not todo:
            return False

        await self.session.delete(todo)
        await self.session.commit()

        # Invalidate cache
        if self.cache:
            cache_key = self._cache_key(todo_id)
            await self.cache.delete(cache_key)

        return True

    async def get_with_subtasks(self, todo_id: UUID) -> Todo | None:
        """Get todo with subtasks eagerly loaded."""
        result = await self.session.execute(
            select(Todo).options(selectinload(Todo.subtasks)).where(Todo.id == todo_id)
        )
        return result.scalar_one_or_none()
