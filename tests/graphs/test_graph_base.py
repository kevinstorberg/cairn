import pytest

from config.models import GraphConfig, LLMConfig
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

        result = graph.invoke({"messages": []})
        assert result["graph_config"]["name"] == "default"
        assert result["graph_config"]["tools"] == []

    def test_build_graph_from_config_unknown_graph_still_works(self):
        graph = build_graph_from_config("nonexistent")
        assert graph is not None
        result = graph.invoke({"messages": []})
        assert result["graph_config"]["name"] == "nonexistent"

    def test_build_graph_from_config_loads_requested_graph_config(self, monkeypatch):
        import src.graphs.base as graph_base

        loaded_graphs = []

        def fake_load_graph_config(graph_name: str):
            loaded_graphs.append(graph_name)
            return GraphConfig(
                name=graph_name,
                llm=LLMConfig(provider="openai", model="model-a", max_tokens=123),
                tools=["tool-a"],
                checkpointing=True,
                validation={"mode": "strict"},
            )

        monkeypatch.setattr(graph_base, "load_graph_config", fake_load_graph_config)

        graph = build_graph_from_config("workflow-a", model_override="model-b")
        result = graph.invoke({"messages": []})

        assert loaded_graphs == ["workflow-a"]
        assert hasattr(graph, "invoke")
        assert result["graph_config"] == {
            "name": "workflow-a",
            "llm": {"provider": "openai", "model": "model-b", "max_tokens": 123},
            "tools": ["tool-a"],
            "checkpointing": True,
            "validation": {"mode": "strict"},
        }


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
