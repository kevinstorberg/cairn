# Graph Development Guide

LangGraph agents are the core of Cairn applications. This guide covers how to create, configure, and test graphs using Cairn's config-driven architecture.

## Table of Contents

- [Quick Start](#quick-start)
- [Graph Configuration](#graph-configuration)
- [Building Graphs](#building-graphs)
- [State Management](#state-management)
- [Node Patterns](#node-patterns)
- [Tool Integration](#tool-integration)
- [Testing Graphs](#testing-graphs)
- [Best Practices](#best-practices)

---

## Quick Start

Create a new graph in 3 steps:

1. **Create config**: `config/graphs/my_graph.yaml`
2. **Create builder**: `src/graphs/my_graph.py`
3. **Register route**: Add to `src/routes/`

```python
# 1. config/graphs/my_graph.yaml
graph_name: my_graph
model: claude-3-5-sonnet-20241022
tools:
  - example_tool

# 2. src/graphs/my_graph.py
from langgraph.graph import StateGraph, END
from src.graphs.base import BaseGraphState
from config.loader import load_graph_config

class MyGraphState(BaseGraphState):
    result: str = ""

def build_my_graph():
    config = load_graph_config("my_graph")
    tools = load_tools(config.tools, ToolContext.from_graph_config(config))
    llm = build_llm(config.model, tools)

    def process(state: MyGraphState):
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MyGraphState)
    graph.add_node("process", process)
    graph.set_entry_point("process")
    graph.add_edge("process", END)

    return graph.compile()

# 3. src/routes/my_graph.py
from fastapi import APIRouter
from src.graphs.my_graph import build_my_graph

router = APIRouter(prefix="/my-graph", tags=["my-graph"])

@router.post("/run")
async def run(request: MyRequest):
    graph = build_my_graph()
    result = await graph.ainvoke({"messages": [HumanMessage(content=request.input)]})
    return {"result": result["result"]}
```

---

## Graph Configuration

### Configuration Files

Each graph has a YAML configuration file in `config/graphs/`:

```yaml
# config/graphs/my_graph.yaml
graph_name: my_graph
description: "Description of what this graph does"

# Model configuration
model: claude-3-5-sonnet-20241022
temperature: 0.7
max_tokens: 4000

# Tools this graph can use
tools:
  - get_user
  - create_todo
  - search_documents

# Graph-specific settings
settings:
  max_retries: 3
  timeout: 120
  enable_streaming: true

# Custom configuration (accessed via config.custom)
custom:
  specialized_setting: "value"
  feature_flags:
    enable_caching: true
    use_memory: false
```

### Loading Configuration

```python
from config.loader import load_graph_config

# Load graph-specific config
config = load_graph_config("my_graph")

# Access fields
model_name = config.model  # "claude-3-5-sonnet-20241022"
tools_list = config.tools  # ["get_user", "create_todo", ...]
timeout = config.settings.get("timeout", 60)  # 120

# Access custom settings
specialized = config.custom.get("specialized_setting")  # "value"
use_caching = config.custom.get("feature_flags", {}).get("enable_caching")  # True
```

### Default Configuration

**File**: `config/default.yaml`

Contains defaults inherited by all graphs:

```yaml
# Default model
model: claude-3-5-sonnet-20241022
temperature: 0.7
max_tokens: 2000

# Default tools (all graphs have access)
tools: []

# Common settings
settings:
  max_retries: 2
  timeout: 60

# Tools configuration (shared across graphs)
tools_config:
  max_results: 10
  search_depth: 5
```

Graph-specific configs override these defaults.

---

## Building Graphs

### State Definition

**Pattern**: Extend `BaseGraphState` for type safety

```python
from typing import Annotated
from langgraph.graph import add_messages
from src.graphs.base import BaseGraphState

class MyGraphState(BaseGraphState):
    """State for my_graph."""

    # Messages (inherited from BaseGraphState)
    # messages: Annotated[list[BaseMessage], add_messages]

    # Custom fields
    user_id: str = ""
    query: str = ""
    results: list[dict] = []
    metadata: dict = {}
```

**Why extend BaseGraphState?**
- Inherits `messages` field with proper reducer
- Type hints for IDE autocomplete
- Consistent structure across graphs

### Basic Graph Pattern

```python
from langgraph.graph import StateGraph, END
from src.graphs.base import build_llm
from src.tools import load_tools
from src.tools.context import ToolContext

def build_my_graph():
    # 1. Load configuration
    config = load_graph_config("my_graph")

    # 2. Load tools
    context = ToolContext.from_graph_config(config)
    tools = load_tools(config.tools, context)

    # 3. Build LLM
    llm = build_llm(config.model, tools)

    # 4. Define nodes
    def process_node(state: MyGraphState):
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # 5. Build graph
    graph = StateGraph(MyGraphState)
    graph.add_node("process", process_node)
    graph.set_entry_point("process")
    graph.add_edge("process", END)

    return graph.compile()
```

### Multi-Node Graph Pattern

```python
def build_complex_graph():
    config = load_graph_config("complex_graph")
    tools = load_tools(config.tools, ToolContext.from_graph_config(config))
    llm = build_llm(config.model, tools)

    # Node 1: Validate input
    def validate(state: ComplexState):
        if not state["query"]:
            return {"error": "Query is required"}
        return {"validated": True}

    # Node 2: Search
    def search(state: ComplexState):
        # Use tools directly or via LLM
        results = perform_search(state["query"])
        return {"results": results}

    # Node 3: Summarize with LLM
    def summarize(state: ComplexState):
        prompt = f"Summarize these results: {state['results']}"
        response = llm.invoke([HumanMessage(content=prompt)])
        return {"summary": response.content}

    # Conditional edge
    def should_search(state: ComplexState):
        if state.get("error"):
            return "end"
        return "search"

    # Build graph
    graph = StateGraph(ComplexState)
    graph.add_node("validate", validate)
    graph.add_node("search", search)
    graph.add_node("summarize", summarize)

    graph.set_entry_point("validate")
    graph.add_conditional_edges("validate", should_search, {
        "search": "search",
        "end": END
    })
    graph.add_edge("search", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()
```

---

## State Management

### State Updates

**Pattern**: Return dict with fields to update

```python
def my_node(state: MyGraphState):
    # Read from state
    current_count = state.get("count", 0)

    # Update state
    return {
        "count": current_count + 1,
        "last_updated": "2024-01-01"
    }
```

### Message Handling

**Pattern**: Use `add_messages` reducer for message field

```python
from langchain_core.messages import HumanMessage, AIMessage

def my_node(state: MyGraphState):
    messages = state["messages"]

    # Add new message
    return {
        "messages": [AIMessage(content="Response")]
    }
```

**Why `add_messages`?** It appends to the list instead of replacing it.

### State Reducers

**Pattern**: Custom reducers for complex updates

```python
from typing import Annotated
from operator import add

def merge_dicts(current: dict, update: dict) -> dict:
    """Merge two dicts, preferring update values."""
    return {**current, **update}

class MyGraphState(BaseGraphState):
    # List: append
    results: Annotated[list[dict], add] = []

    # Dict: merge
    metadata: Annotated[dict, merge_dicts] = {}

    # Replace (default)
    count: int = 0
```

---

## Node Patterns

### LLM Node

**Pattern**: Invoke LLM with messages

```python
def llm_node(state: MyGraphState):
    llm = build_llm(config.model, tools)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
```

### Tool-Calling Node

**Pattern**: Let LLM decide which tools to call

```python
def agent_node(state: MyGraphState):
    llm = build_llm(config.model, tools)  # Tools bound to LLM
    response = llm.invoke(state["messages"])

    # If LLM called tools, response includes tool_calls
    if response.tool_calls:
        # Execute tools and add results to messages
        tool_messages = execute_tools(response.tool_calls, tools)
        return {"messages": [response] + tool_messages}

    return {"messages": [response]}
```

### Database Node

**Pattern**: Async DB operations with event loop

```python
import asyncio
from db.connection import get_session_factory

def db_node(state: MyGraphState):
    async def _query():
        factory = get_session_factory()
        async with factory() as session:
            result = await session.execute(select(User).where(User.id == state["user_id"]))
            user = result.scalar_one_or_none()
            return {"user": user.to_dict() if user else None}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_query())
```

### Cache Node

**Pattern**: Check cache before expensive operation

```python
import asyncio
from cache.backends import get_cache_backend

def cached_node(state: MyGraphState):
    async def _cached():
        cache = get_cache_backend()
        cache_key = f"result:{state['query']}"

        # Check cache
        cached = await cache.get(cache_key)
        if cached:
            return {"result": cached, "from_cache": True}

        # Compute result
        result = expensive_operation(state["query"])

        # Cache it
        await cache.set(cache_key, result, ttl=3600)

        return {"result": result, "from_cache": False}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_cached())
```

### Error Handling Node

**Pattern**: Catch errors and set error state

```python
def safe_node(state: MyGraphState):
    try:
        result = risky_operation(state["input"])
        return {"result": result, "error": None}
    except ValueError as e:
        return {"error": f"Validation error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
```

---

## Tool Integration

### Loading Tools

**Pattern**: Load from config, bind to LLM

```python
from src.tools import load_tools
from src.tools.context import ToolContext

def build_my_graph():
    config = load_graph_config("my_graph")

    # Create tool context
    context = ToolContext.from_graph_config(config)

    # Load tools specified in config
    tools = load_tools(config.tools, context)

    # Bind to LLM
    llm = build_llm(config.model, tools)

    # Now LLM can call tools
    ...
```

### Dynamic Tool Selection

**Pattern**: Load different tools based on state

```python
def build_conditional_graph():
    config = load_graph_config("conditional")
    context = ToolContext.from_graph_config(config)

    def agent_node(state: ConditionalState):
        # Select tools based on state
        if state["mode"] == "search":
            tools = load_tools(["search_documents"], context)
        else:
            tools = load_tools(["create_todo"], context)

        llm = build_llm(config.model, tools)
        response = llm.invoke(state["messages"])
        return {"messages": [response]}

    ...
```

### Tool Results in State

**Pattern**: Store tool results for later use

```python
def process_tools(state: MyGraphState):
    llm = build_llm(config.model, tools)
    response = llm.invoke(state["messages"])

    tool_results = []
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call, tools)
            tool_results.append({
                "tool": tool_call["name"],
                "result": result
            })

    return {
        "messages": [response],
        "tool_results": tool_results
    }
```

---

## Testing Graphs

### Unit Test Pattern

```python
import pytest
from src.graphs.my_graph import build_my_graph, MyGraphState
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_my_graph():
    # Build graph
    graph = build_my_graph()

    # Prepare input
    initial_state = {
        "messages": [HumanMessage(content="Test input")],
        "user_id": "user123"
    }

    # Execute
    result = await graph.ainvoke(initial_state)

    # Assert
    assert "result" in result
    assert result["result"] is not None
```

### Mocking LLM

```python
from unittest.mock import patch, AsyncMock
from langchain_core.messages import AIMessage

@pytest.mark.asyncio
async def test_with_mocked_llm():
    # Mock LLM response
    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = AIMessage(content="Mocked response")

    with patch("src.graphs.my_graph.build_llm", return_value=mock_llm):
        graph = build_my_graph()
        result = await graph.ainvoke({
            "messages": [HumanMessage(content="Test")]
        })

        assert result["messages"][-1].content == "Mocked response"
```

### Testing Individual Nodes

```python
def test_validate_node():
    from src.graphs.complex_graph import validate

    # Test valid input
    state = {"query": "test query"}
    result = validate(state)
    assert result["validated"] is True

    # Test invalid input
    state = {"query": ""}
    result = validate(state)
    assert "error" in result
```

### Integration Test with Database

```python
@pytest.mark.asyncio
async def test_graph_with_db(test_session, clean_db):
    from db.models.todo import Todo

    # Setup test data
    todo = Todo(title="Test", user_id="user123")
    test_session.add(todo)
    await test_session.commit()

    # Run graph
    graph = build_my_graph()
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="Get todos")],
        "user_id": "user123"
    })

    # Assert
    assert "todos" in result
    assert len(result["todos"]) > 0
```

---

## Best Practices

### ✅ Do

- **Use config-driven architecture**: Keep model/tool configs in YAML
- **Extend BaseGraphState**: Inherit messages field with reducer
- **Type your state**: Use TypedDict or dataclass for IDE support
- **Make nodes pure**: Given same state, return same output
- **Handle errors in nodes**: Return error state instead of raising
- **Test nodes independently**: Unit test before integration
- **Use meaningful state keys**: `user_id` not `uid`, `query` not `q`
- **Cache expensive operations**: Use cache backend for repeated queries
- **Log important events**: Help debugging in production

### ❌ Don't

- **Don't mutate state**: Return new dict, don't modify state parameter
- **Don't use global state**: Pass everything through state
- **Don't make nodes async**: LangGraph nodes are synchronous functions
- **Don't call database directly in nodes**: Use event loop pattern
- **Don't hardcode model names**: Use config files
- **Don't forget message reducers**: Use `add_messages` for message field
- **Don't skip error handling**: Always return error state on failure
- **Don't use bare `except`**: Catch specific exceptions

### Node Design

```python
# Good
def clear_node(state: MyGraphState) -> dict:
    """Node that processes data and returns update."""
    try:
        result = process(state["input"])
        return {"result": result, "error": None}
    except ValueError as e:
        return {"error": str(e), "result": None}

# Bad
def unclear_node(s):  # No types
    global some_var  # Global state
    s["result"] = process(s["i"])  # Mutates state, unclear key
    return s  # Returns modified state
```

### State Design

```python
# Good
class ClearState(BaseGraphState):
    """State for my_graph."""
    user_id: str = ""
    query: str = ""
    results: list[dict] = []

# Bad
class UnclearState(BaseGraphState):
    uid: str = ""  # Unclear abbreviation
    q: str = ""  # Too short
    data: Any = None  # Too vague
```

### Configuration

```yaml
# Good
graph_name: user_search
model: claude-3-5-sonnet-20241022
tools:
  - search_users
  - get_user_details
settings:
  max_results: 10
  timeout: 30

# Bad
graph_name: graph1  # Unclear name
model: gpt-4  # Hardcoded in code instead
# No tools listed
# No settings
```

---

## Advanced Patterns

### Streaming Support

**Pattern**: Stream LLM responses chunk by chunk

```python
from langgraph.graph import StateGraph

def build_streaming_graph():
    config = load_graph_config("streaming")
    tools = load_tools(config.tools, ToolContext.from_graph_config(config))
    llm = build_llm(config.model, tools)

    async def stream_node(state: StreamingState):
        messages = state["messages"]
        chunks = []

        async for chunk in llm.astream(messages):
            chunks.append(chunk.content)
            yield {"chunk": chunk.content}

        # Final state
        return {"messages": [AIMessage(content="".join(chunks))]}

    graph = StateGraph(StreamingState)
    graph.add_node("stream", stream_node)
    graph.set_entry_point("stream")
    graph.add_edge("stream", END)

    return graph.compile()
```

### Subgraph Pattern

**Pattern**: Compose graphs from smaller graphs

```python
def build_subgraph():
    # Build reusable subgraph
    subgraph = StateGraph(SubState)
    subgraph.add_node("process", process_node)
    subgraph.set_entry_point("process")
    subgraph.add_edge("process", END)
    compiled_sub = subgraph.compile()

    # Use in main graph
    def call_subgraph(state: MainState):
        result = compiled_sub.invoke({"input": state["input"]})
        return {"subgraph_result": result}

    main = StateGraph(MainState)
    main.add_node("subgraph", call_subgraph)
    # ... rest of main graph
```

### Checkpoint Pattern

**Pattern**: Save/restore graph state for long-running operations

```python
from langgraph.checkpoint import MemorySaver

def build_checkpointed_graph():
    config = load_graph_config("checkpointed")

    # ... define nodes ...

    graph = StateGraph(CheckpointedState)
    # ... add nodes and edges ...

    # Compile with checkpointer
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# Usage with thread ID for resuming
graph = build_checkpointed_graph()
thread_config = {"configurable": {"thread_id": "user123"}}

# First invocation
result1 = await graph.ainvoke(initial_state, config=thread_config)

# Resume from checkpoint
result2 = await graph.ainvoke({"messages": [HumanMessage("Continue")]}, config=thread_config)
```

---

## Troubleshooting

### "Node returned None"

**Problem**: Node didn't return a state update dict.

**Solution**: Always return a dict:
```python
# Wrong
def bad_node(state):
    process(state)
    # Returns None implicitly

# Correct
def good_node(state):
    process(state)
    return {}  # Or return state updates
```

---

### "Async node not supported"

**Problem**: Tried to make node async.

**Solution**: Use event loop pattern:
```python
# Wrong
async def async_node(state):
    result = await async_operation()
    return {"result": result}

# Correct
def sync_node(state):
    async def _async():
        result = await async_operation()
        return {"result": result}

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_async())
```

---

### "Messages not accumulating"

**Problem**: Message field not using `add_messages` reducer.

**Solution**: Use proper annotation:
```python
# Wrong
class BadState(BaseGraphState):
    messages: list[BaseMessage] = []

# Correct
from typing import Annotated
from langgraph.graph import add_messages

class GoodState(BaseGraphState):
    messages: Annotated[list[BaseMessage], add_messages]
```

---

### "Tool not found"

**Problem**: Tool not loaded or not registered.

**Solution**: Check registration and config:
```bash
# Verify tool is registered
poetry run python -c "from src.tools import load_tools, ToolContext; print(load_tools(['my_tool'], ToolContext()))"

# Check config includes tool
cat config/graphs/my_graph.yaml | grep my_tool
```

---

## Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Tools](https://python.langchain.com/docs/modules/agents/tools/)
- [State Management in LangGraph](https://langchain-ai.github.io/langgraph/concepts/low_level/)
- [Checkpointing & Memory](https://langchain-ai.github.io/langgraph/concepts/persistence/)
