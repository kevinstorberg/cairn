"""
Integration tests for WebSocket real-time updates.

Tests:
- WebSocket connection
- Multiple clients connect
- Broadcasting to all clients
- Todo create/update/delete events
- Client disconnect
- Room-based routing
"""

import asyncio

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestWebSocketUpdates:
    @pytest.mark.asyncio
    async def test_connection_manager_initialization(self):
        """Test ConnectionManager can be initialized."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()
        assert manager is not None
        assert manager.active_connections == {}

    @pytest.mark.asyncio
    async def test_connection_manager_rooms(self):
        """Test ConnectionManager manages rooms correctly."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()

        # Mock websocket
        class MockWebSocket:
            async def accept(self):
                pass

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(ws1, "room1")
        await manager.connect(ws2, "room2")

        assert "room1" in manager.active_connections
        assert "room2" in manager.active_connections
        assert len(manager.get_room_connections("room1")) == 1
        assert len(manager.get_room_connections("room2")) == 1

    @pytest.mark.asyncio
    async def test_connection_manager_multiple_clients_same_room(self):
        """Test multiple clients can join same room."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(ws1, "todos")
        await manager.connect(ws2, "todos")

        assert len(manager.get_room_connections("todos")) == 2

    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self):
        """Test disconnect removes client from room."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        ws = MockWebSocket()
        await manager.connect(ws, "room1")
        assert len(manager.get_room_connections("room1")) == 1

        manager.disconnect(ws, "room1")
        assert len(manager.get_room_connections("room1")) == 0
        assert "room1" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test broadcast sends to all clients in room."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()
        received_messages = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(ws1, "todos")
        await manager.connect(ws2, "todos")

        await manager.broadcast("todos", {"type": "test", "data": "hello"})

        assert len(received_messages) == 2
        assert all(msg["type"] == "test" for msg in received_messages)

    @pytest.mark.asyncio
    async def test_todo_events_module_structure(self):
        """Test todo events module has correct exports."""
        from src.websockets import todo_events

        assert hasattr(todo_events, "broadcast_todo_created")
        assert hasattr(todo_events, "broadcast_todo_updated")
        assert hasattr(todo_events, "broadcast_todo_deleted")
        assert hasattr(todo_events, "get_todo_manager")

    @pytest.mark.asyncio
    async def test_broadcast_functions_callable(self):
        """Test broadcast functions are async callables."""
        from src.websockets.todo_events import (
            broadcast_todo_created,
            broadcast_todo_deleted,
            broadcast_todo_updated,
        )

        assert callable(broadcast_todo_created)
        assert callable(broadcast_todo_updated)
        assert callable(broadcast_todo_deleted)

    @pytest.mark.asyncio
    async def test_broadcast_todo_created_format(self):
        """Test broadcast_todo_created sends correct message format."""
        from src.websockets.todo_events import broadcast_todo_created, get_todo_manager

        manager = get_todo_manager()
        received_messages = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        ws = MockWebSocket()
        await manager.connect(ws, "todos")

        await broadcast_todo_created({"id": "123", "title": "Test"})

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "todo_created"
        assert received_messages[0]["data"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_broadcast_todo_updated_format(self):
        """Test broadcast_todo_updated sends correct message format."""
        from src.websockets.todo_events import broadcast_todo_updated, get_todo_manager

        manager = get_todo_manager()
        received_messages = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        ws = MockWebSocket()
        await manager.connect(ws, "todos")

        await broadcast_todo_updated({"id": "123", "title": "Updated"})

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "todo_updated"
        assert received_messages[0]["data"]["title"] == "Updated"

    @pytest.mark.asyncio
    async def test_broadcast_todo_deleted_format(self):
        """Test broadcast_todo_deleted sends correct message format."""
        from src.websockets.todo_events import broadcast_todo_deleted, get_todo_manager

        manager = get_todo_manager()
        received_messages = []

        class MockWebSocket:
            async def accept(self):
                pass

            async def send_json(self, data):
                received_messages.append(data)

        ws = MockWebSocket()
        await manager.connect(ws, "todos")

        await broadcast_todo_deleted("123")

        assert len(received_messages) == 1
        assert received_messages[0]["type"] == "todo_deleted"
        assert received_messages[0]["data"]["id"] == "123"

    @pytest.mark.asyncio
    async def test_multiple_rooms_isolated(self):
        """Test rooms are isolated from each other."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()
        room1_messages = []
        room2_messages = []

        class MockWebSocket1:
            async def accept(self):
                pass

            async def send_json(self, data):
                room1_messages.append(data)

        class MockWebSocket2:
            async def accept(self):
                pass

            async def send_json(self, data):
                room2_messages.append(data)

        ws1 = MockWebSocket1()
        ws2 = MockWebSocket2()

        await manager.connect(ws1, "room1")
        await manager.connect(ws2, "room2")

        await manager.broadcast("room1", {"type": "test1"})
        await manager.broadcast("room2", {"type": "test2"})

        assert len(room1_messages) == 1
        assert len(room2_messages) == 1
        assert room1_messages[0]["type"] == "test1"
        assert room2_messages[0]["type"] == "test2"

    @pytest.mark.asyncio
    async def test_disconnect_one_client_doesnt_affect_others(self):
        """Test disconnecting one client doesn't affect others."""
        from src.websockets.manager import ConnectionManager

        manager = ConnectionManager()

        class MockWebSocket:
            async def accept(self):
                pass

        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await manager.connect(ws1, "todos")
        await manager.connect(ws2, "todos")
        assert len(manager.get_room_connections("todos")) == 2

        manager.disconnect(ws1, "todos")
        assert len(manager.get_room_connections("todos")) == 1

    @pytest.mark.asyncio
    async def test_websocket_router_has_endpoints(self):
        """Test WebSocket router has correct endpoints."""
        from src.websockets.router import router

        # Router should have WebSocket routes
        assert router is not None
        assert len(router.routes) >= 2  # Generic /ws/{room} and /ws/todos
