# Graph Development Guide

Graph behavior belongs in app-specific builder modules. YAML decides structural
settings such as model, tools, validation flags, and checkpointing; Python owns
state types, nodes, and edges.

## Built-In Config Smoke Graph

`build_graph_from_config(name)` is intentionally deterministic and credential-free.
It loads `config/default.yaml` plus `config/graphs/{name}.yaml`, applies
`model_override` when provided, and writes the resolved summary into
`state["graph_config"]`.

Use it to verify config loading in fresh clones. Do not treat it as a production
agent.

## Create A Graph

1. Add `config/graphs/{name}.yaml`.
2. Create `src/graphs/{name}.py`.
3. Add a route in `src/routers/` or call the graph from a service/job.

```yaml
# config/graphs/workflow.yaml
llm:
  model: claude-sonnet-4-6
tools:
  - lookup_record
checkpointing: false
```

```python
# src/graphs/workflow.py
from langgraph.graph import END, StateGraph

from config.loader import load_graph_config
from src.agents.llm import build_llm
from src.models.state import BaseState
from src.tools import load_tools
from src.tools.context import ToolContext


class WorkflowState(BaseState, total=False):
    result: str


def build_workflow():
    config = load_graph_config("workflow")
    context = ToolContext.from_graph_config(config)
    tools = load_tools(config.tools, context)
    llm = build_llm(config=config.llm).bind_tools(tools)

    async def process(state: WorkflowState):
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response], "result": response.content}

    graph = StateGraph(WorkflowState)
    graph.add_node("process", process)
    graph.set_entry_point("process")
    graph.add_edge("process", END)
    return graph.compile()
```

## State Rules

- Keep state small and explicit.
- Return partial state updates from nodes.
- Use reducers for fields that accumulate across nodes.
- Keep domain-specific state in the graph module that needs it.
- Keep shared state primitives in `src/models/state.py`.

`BaseState` includes LangGraph message accumulation. Extend it for application
fields instead of duplicating the message reducer.

## Tools

Load tools from graph config:

```python
config = load_graph_config("workflow")
context = ToolContext.from_graph_config(config)
tools = load_tools(config.tools, context)
```

Tool definitions and registration rules are documented in [TOOLS.md](TOOLS.md).

## Database And Cache Nodes

Prefer services or repositories for domain work. If a node needs infrastructure
directly, use the same factories as the rest of the app:

```python
from cache.backends import get_cache_backend
from db.connection import get_session_factory

factory = get_session_factory()
cache = get_cache_backend()
```

Nodes should fail loudly for broken assumptions and return structured error state
only when the graph is designed to recover.

## Testing

- Unit test pure node functions directly.
- Mock LLMs and provider calls at the graph-builder boundary.
- Use `build_graph_from_config()` only for config smoke tests.
- Use `ainvoke()` when the graph has async nodes.

```python
async def test_process_node(fake_llm):
    graph = build_workflow()
    result = await graph.ainvoke({"messages": []})
    assert "result" in result
```

## Troubleshooting

- Node returned `None`: every node must return a state update dict.
- Messages do not accumulate: extend `BaseState` or use LangGraph reducers.
- Tool not found: verify the tool module is public and the graph YAML includes
  the registered name.
- Event loop errors: use async nodes and `ainvoke()`.
