"""Todo event broadcasting via WebSocket."""

from typing import Any

from src.websockets.manager import ConnectionManager

# Global manager instance for todo events
_todo_manager = ConnectionManager()


def get_todo_manager() -> ConnectionManager:
    """Get the global todo WebSocket manager."""
    return _todo_manager


async def broadcast_todo_created(todo_data: dict[str, Any]) -> None:
    """Broadcast todo creation event to all connected clients."""
    await _todo_manager.broadcast(
        room="todos",
        message={
            "type": "todo_created",
            "data": todo_data,
        },
    )


async def broadcast_todo_updated(todo_data: dict[str, Any]) -> None:
    """Broadcast todo update event to all connected clients."""
    await _todo_manager.broadcast(
        room="todos",
        message={
            "type": "todo_updated",
            "data": todo_data,
        },
    )


async def broadcast_todo_deleted(todo_id: str) -> None:
    """Broadcast todo deletion event to all connected clients."""
    await _todo_manager.broadcast(
        room="todos",
        message={
            "type": "todo_deleted",
            "data": {"id": todo_id},
        },
    )
