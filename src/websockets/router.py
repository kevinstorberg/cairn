from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.websockets.manager import ConnectionManager

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
