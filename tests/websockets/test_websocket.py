import pytest
from starlette.testclient import TestClient

from src.app import create_app
from src.websockets.manager import ConnectionManager


class TestConnectionManager:
    def test_manager_starts_empty(self):
        manager = ConnectionManager()
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_manager_tracks_rooms(self):
        manager = ConnectionManager()
        assert manager.get_room_connections("test-room") == []


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
