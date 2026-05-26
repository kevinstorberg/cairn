import pytest

from src.graphs.base import GraphFactory, build_graph_from_config
from src.graphs.checkpointing import CheckpointBackend, InMemoryCheckpointer
from src.models.state import BaseState, add_messages_reducer


class TestBaseState:
    def test_base_state_has_messages(self):
        state = BaseState(messages=[])
        assert state["messages"] == []

    def test_add_messages_reducer_appends(self):
        existing = ["hello"]
        new = ["world"]
        result = add_messages_reducer(existing, new)
        assert result == ["hello", "world"]

    def test_add_messages_reducer_empty(self):
        result = add_messages_reducer([], ["first"])
        assert result == ["first"]


class TestGraphFactory:
    def test_graph_factory_protocol(self):
        assert hasattr(GraphFactory, "build")

    def test_build_graph_from_config_returns_compiled(self):
        graph = build_graph_from_config("default")
        assert graph is not None
        assert hasattr(graph, "invoke")

    def test_build_graph_from_config_unknown_graph_still_works(self):
        graph = build_graph_from_config("nonexistent")
        assert graph is not None


class TestCheckpointing:
    @pytest.mark.asyncio
    async def test_in_memory_checkpointer_save_and_get(self):
        cp = InMemoryCheckpointer()
        await cp.save("thread-1", {"messages": ["hi"]})
        result = await cp.get("thread-1")
        assert result == {"messages": ["hi"]}

    @pytest.mark.asyncio
    async def test_in_memory_checkpointer_get_missing_returns_none(self):
        cp = InMemoryCheckpointer()
        result = await cp.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_in_memory_checkpointer_delete(self):
        cp = InMemoryCheckpointer()
        await cp.save("thread-1", {"messages": ["hi"]})
        await cp.delete("thread-1")
        result = await cp.get("thread-1")
        assert result is None

    def test_implements_protocol(self):
        cp = InMemoryCheckpointer()
        assert isinstance(cp, CheckpointBackend)
