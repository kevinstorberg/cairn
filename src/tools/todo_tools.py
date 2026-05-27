"""Tools for todo operations in graphs."""

import asyncio
from typing import Annotated
from uuid import UUID

import nest_asyncio
from langchain_core.tools import tool
from pydantic import Field

from src.tools import register_tool
from src.tools.context import ToolContext

# Allow nested event loops
nest_asyncio.apply()


@register_tool("get_todo")
def create_get_todo_tool(context: ToolContext):
    """Create a tool for fetching todo by ID."""

    @tool
    def get_todo(
        todo_id: Annotated[str, Field(description="UUID of the todo to fetch")]
    ) -> dict:
        """Fetch a todo by its ID. Returns todo data or error."""
        from db.connection import get_session_factory
        from db.models.todo import Todo
        from sqlalchemy import select

        # Parse UUID
        try:
            parsed_id = UUID(todo_id)
        except ValueError:
            return {"error": f"Invalid UUID: {todo_id}"}

        # Query database (sync wrapper for async)
        async def _fetch():
            factory = get_session_factory()
            async with factory() as session:
                result = await session.execute(select(Todo).where(Todo.id == parsed_id))
                todo = result.scalar_one_or_none()

                if not todo:
                    return {"error": f"Todo not found: {todo_id}"}

                return {
                    "id": str(todo.id),
                    "title": todo.title,
                    "description": todo.description or "",
                    "status": todo.status.value if todo.status else "pending",
                    "priority": todo.priority.value if todo.priority else "medium",
                }

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_fetch())

    return get_todo


@register_tool("create_subtask")
def create_subtask_tool(context: ToolContext):
    """Create a tool for creating subtasks."""

    @tool
    def create_subtask(
        parent_id: Annotated[str, Field(description="UUID of the parent todo")],
        title: Annotated[str, Field(description="Title of the subtask")],
        description: Annotated[str, Field(description="Description of the subtask")] = "",
    ) -> dict:
        """Create a subtask for a parent todo. Returns created subtask data."""
        from db.connection import get_session_factory
        from db.models.todo import Todo

        # Parse UUID
        try:
            parsed_parent_id = UUID(parent_id)
        except ValueError:
            return {"error": f"Invalid UUID: {parent_id}"}

        # Create subtask (sync wrapper for async)
        async def _create():
            factory = get_session_factory()
            async with factory() as session:
                # Verify parent exists
                parent = await session.get(Todo, parsed_parent_id)
                if not parent:
                    return {"error": f"Parent todo not found: {parent_id}"}

                # Create subtask
                subtask = Todo(
                    title=title,
                    description=description,
                    parent_id=parsed_parent_id,
                    status=parent.status,  # Inherit status
                    priority=parent.priority,  # Inherit priority
                )
                session.add(subtask)
                await session.commit()
                await session.refresh(subtask)

                return {
                    "id": str(subtask.id),
                    "title": subtask.title,
                    "description": subtask.description or "",
                    "parent_id": str(subtask.parent_id),
                    "status": subtask.status.value,
                }

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_create())

    return create_subtask


@register_tool("update_todo")
def create_update_todo_tool(context: ToolContext):
    """Create a tool for updating todos."""

    @tool
    def update_todo(
        todo_id: Annotated[str, Field(description="UUID of the todo to update")],
        category: Annotated[str | None, Field(description="Category to set")] = None,
        status: Annotated[str | None, Field(description="Status to set (pending, in_progress, completed)")] = None,
    ) -> dict:
        """Update a todo's fields. Returns updated todo data."""
        from db.connection import get_session_factory
        from db.models.todo import Todo, TodoStatus

        # Parse UUID
        try:
            parsed_id = UUID(todo_id)
        except ValueError:
            return {"error": f"Invalid UUID: {todo_id}"}

        # Update todo (sync wrapper for async)
        async def _update():
            factory = get_session_factory()
            async with factory() as session:
                todo = await session.get(Todo, parsed_id)
                if not todo:
                    return {"error": f"Todo not found: {todo_id}"}

                if category is not None:
                    todo.category = category

                if status is not None:
                    try:
                        todo.status = TodoStatus(status)
                    except ValueError:
                        return {"error": f"Invalid status: {status}"}

                await session.commit()
                await session.refresh(todo)

                return {
                    "id": str(todo.id),
                    "title": todo.title,
                    "category": todo.category,
                    "status": todo.status.value,
                }

        # Run in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_update())

    return update_todo
