from typing import Protocol, runtime_checkable

from langgraph.graph import StateGraph

from config.loader import load_graph_config
from src.models.state import BaseState


@runtime_checkable
class GraphFactory(Protocol):
    def build(self, graph_name: str, **kwargs) -> object: ...


def _passthrough(state: BaseState) -> BaseState:
    return state


def build_graph_from_config(graph_name: str, *, model_override: str | None = None):
    load_graph_config(graph_name)
    graph = StateGraph(BaseState)
    graph.add_node("process", _passthrough)
    graph.set_entry_point("process")
    graph.set_finish_point("process")
    return graph.compile()
