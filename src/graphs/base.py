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
    """Build a minimal passthrough graph from config.

    SCAFFOLD: This loads config but builds a simple passthrough graph.
    To build a real agent graph, create your own builder function:

        from config.loader import load_graph_config
        from src.tools import load_tools
        from src.tools.context import ToolContext

        def build_my_graph(graph_name: str):
            config = load_graph_config(graph_name)
            context = ToolContext.from_graph_config(config)
            tools = load_tools(config.tools, context)
            # Build LLM, define nodes, wire edges...

    See docs/GRAPHS.md for complete patterns.
    """
    config = load_graph_config(graph_name)
    _ = config
    _ = model_override

    graph = StateGraph(BaseState)
    graph.add_node("process", _passthrough)
    graph.set_entry_point("process")
    graph.set_finish_point("process")
    return graph.compile()
