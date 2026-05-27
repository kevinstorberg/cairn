from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.websockets.manager import ConnectionManager
from src.websockets.todo_events import get_todo_manager

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room)


@router.websocket("/ws/todos")
async def todo_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for todo real-time updates."""
    todo_manager = get_todo_manager()
    await todo_manager.connect(websocket, "todos")

    try:
        while True:
            # Keep connection alive and handle pings
            data = await websocket.receive_json()
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        todo_manager.disconnect(websocket, "todos")
