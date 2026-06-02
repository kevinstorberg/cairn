from typing import Any, Protocol, runtime_checkable

from langgraph.graph import StateGraph

from config.loader import load_graph_config
from config.models import GraphConfig
from src.models.state import BaseState


@runtime_checkable
class GraphFactory(Protocol):
    def build(self, graph_name: str, **kwargs) -> object: ...


def _graph_config_summary(config: GraphConfig, model_override: str | None) -> dict[str, Any]:
    return {
        "name": config.name,
        "llm": {
            "provider": config.llm.provider,
            "model": model_override or config.llm.model,
            "max_tokens": config.llm.max_tokens,
        },
        "tools": list(config.tools),
        "checkpointing": config.checkpointing,
        "validation": dict(config.validation),
    }


def _with_graph_config(state: BaseState, config: GraphConfig, model_override: str | None) -> BaseState:
    return {
        **state,
        "graph_config": _graph_config_summary(config, model_override),
    }


def build_graph_from_config(graph_name: str, *, model_override: str | None = None):
    """Build a minimal graph that exposes resolved graph configuration.

    SCAFFOLD: This keeps fresh clones deterministic and credential-free while
    proving graph-specific YAML is loaded and carried through graph state. To
    build a real agent graph, create your own builder function:

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

    graph = StateGraph(BaseState)
    graph.add_node("process", lambda state: _with_graph_config(state, config, model_override))
    graph.set_entry_point("process")
    graph.set_finish_point("process")
    return graph.compile()
