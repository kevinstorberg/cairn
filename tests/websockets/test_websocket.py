import pytest
from starlette.testclient import TestClient

from src.app import create_app
from src.websockets.manager import ConnectionManager


class FakeWebSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, message: dict) -> None:
        self.sent_messages.append(message)


class TestConnectionManager:
    def test_manager_starts_empty(self):
        manager = ConnectionManager()
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_manager_tracks_rooms(self):
        manager = ConnectionManager()
        assert manager.get_room_connections("test-room") == []

    @pytest.mark.asyncio
    async def test_connect_tracks_websocket_by_room(self):
        manager = ConnectionManager()
        websocket = FakeWebSocket()

        await manager.connect(websocket, "room-a")

        assert websocket.accepted is True
        assert manager.get_room_connections("room-a") == [websocket]

    @pytest.mark.asyncio
    async def test_broadcast_sends_only_to_room_connections(self):
        manager = ConnectionManager()
        room_a = FakeWebSocket()
        room_b = FakeWebSocket()

        await manager.connect(room_a, "room-a")
        await manager.connect(room_b, "room-b")

        await manager.broadcast("room-a", {"type": "event"})

        assert room_a.sent_messages == [{"type": "event"}]
        assert room_b.sent_messages == []

    @pytest.mark.asyncio
    async def test_disconnect_removes_empty_room(self):
        manager = ConnectionManager()
        websocket = FakeWebSocket()

        await manager.connect(websocket, "room-a")
        manager.disconnect(websocket, "room-a")

        assert manager.active_connections == {}


class TestWebSocketEndpoint:
    def test_websocket_connect_and_ping(self):
        app = create_app()
        client = TestClient(app)
        with client.websocket_connect("/ws/test-room") as ws:
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"

    def test_websocket_echo(self):
        app = create_app()
        client = TestClient(app)
        with client.websocket_connect("/ws/test-room") as ws:
            ws.send_json({"type": "message", "content": "hello"})
            response = ws.receive_json()
            assert response["type"] == "message"
            assert response["content"] == "hello"
