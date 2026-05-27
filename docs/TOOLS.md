# Tool Development Guide

Tools are the building blocks of LangGraph agents in Cairn. This guide covers how to create, register, and test tools.

## Table of Contents

- [Quick Start](#quick-start)
- [Tool Registration](#tool-registration)
- [Tool Context](#tool-context)
- [Database Access in Tools](#database-access-in-tools)
- [Error Handling](#error-handling)
- [Testing Tools](#testing-tools)
- [Best Practices](#best-practices)

---

## Quick Start

Create a new tool in 3 steps:

1. **Create file**: `src/tools/my_tool.py`
2. **Register tool**: Use `@register_tool` decorator
3. **Done**: Auto-imported automatically!

```python
# src/tools/my_tool.py
from langchain_core.tools import tool
from src.tools import register_tool
from src.tools.context import ToolContext


@register_tool("get_user")
def create_get_user_tool(context: ToolContext):
    """Create a tool that fetches user information."""
    
    @tool
    def get_user(user_id: str) -> dict:
        """Get user by ID.
        
        Args:
            user_id: The user ID to fetch
            
        Returns:
            User information dictionary
        """
        # Tool implementation here
        return {"id": user_id, "name": "John Doe"}
    
    return get_user
```

That's it! The tool is automatically registered and available for use in graphs.

---

## Tool Registration

### Auto-Import Mechanism

Cairn automatically imports all tool modules when `src.tools` is loaded. This triggers `@register_tool` decorators without manual imports.

**How it works**:
```python
# In src/tools/__init__.py
def _auto_import_tools():
    """Auto-import all tool modules to trigger @register_tool decorators."""
    tools_dir = Path(__file__).parent
    for _, module_name, _ in pkgutil.iter_modules([str(tools_dir)]):
        if module_name.startswith('_') or module_name == 'context':
            continue
        importlib.import_module(f'src.tools.{module_name}')
```

**What gets imported**:
- ✅ `src/tools/my_tool.py` → Imported
- ✅ `src/tools/nested/tool.py` → Imported
- ❌ `src/tools/_private.py` → Skipped (starts with `_`)
- ❌ `src/tools/context.py` → Skipped (reserved)

### Registration Pattern

```python
from src.tools import register_tool
from src.tools.context import ToolContext

@register_tool("tool_name")
def create_tool(context: ToolContext):
    """Factory function that creates the tool."""
    # Access context
    config = context.config
    settings = context.settings
    
    # Define the actual tool
    @tool
    def tool_name(arg: str) -> str:
        """Tool description for LLM."""
        return f"Result: {arg}"
    
    return tool_name
```

**Key points**:
- Factory function receives `ToolContext`
- Returns a LangChain `@tool` decorated function
- Tool name in decorator must match factory function name convention
- Factory can return `None` to disable tool conditionally

### Conditional Tool Registration

```python
@register_tool("premium_feature")
def create_premium_tool(context: ToolContext):
    """Only available for premium users."""
    if not context.config.get("enable_premium_features"):
        return None  # Tool disabled
    
    @tool
    def premium_feature() -> str:
        """Premium feature."""
        return "Premium result"
    
    return premium_feature
```

---

## Tool Context

`ToolContext` provides access to configuration, settings, and state.

### Available Fields

```python
@dataclass
class ToolContext:
    config: DefaultConfig          # Loaded from YAML
    settings: Settings | None      # Pydantic settings
    user_id: str | None           # Current user (if applicable)
    metadata: dict[str, Any]      # Additional context
```

### Usage Example

```python
from src.tools import register_tool
from src.tools.context import ToolContext

@register_tool("smart_search")
def create_search_tool(context: ToolContext):
    """Create search tool with config-based settings."""
    
    # Access configuration
    max_results = context.config.tools_config.get("max_results", 10)
    
    # Access settings
    api_key = context.settings.ANTHROPIC_API_KEY if context.settings else None
    
    @tool
    def smart_search(query: str) -> list[dict]:
        """Search with smart ranking."""
        # Use config values
        return search_with_limit(query, limit=max_results)
    
    return smart_search
```

### Creating Context

```python
from config.loader import load_graph_config
from src.tools.context import ToolContext

# Load graph-specific config
config = load_graph_config("my_graph")

# Create context
context = ToolContext.from_graph_config(config)

# Or with additional metadata
context = ToolContext(
    config=config,
    settings=get_settings(),
    user_id="user123",
    metadata={"session_id": "abc"}
)
```

---

## Database Access in Tools

Tools are **synchronous** (LangChain requirement) but Cairn uses **async** database. Use `nest_asyncio` to bridge the gap.

### Pattern: Async DB in Sync Tool

```python
import asyncio
from langchain_core.tools import tool
from src.tools import register_tool
from db.connection import get_session_factory

@register_tool("get_todo")
def create_get_todo_tool(context: ToolContext):
    """Create tool that fetches todo from database."""
    
    @tool
    def get_todo(todo_id: str) -> dict:
        """Get todo by ID from database.
        
        Args:
            todo_id: The todo ID to fetch
            
        Returns:
            Todo information dictionary
        """
        async def _fetch():
            from sqlalchemy import select
            from db.models.todo import Todo
            
            factory = get_session_factory()
            async with factory() as session:
                result = await session.execute(
                    select(Todo).where(Todo.id == todo_id)
                )
                todo = result.scalar_one_or_none()
                
                if not todo:
                    return {"error": "Todo not found"}
                
                return {
                    "id": str(todo.id),
                    "title": todo.title,
                    "status": todo.status.value
                }
        
        # Run async code in sync context
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_fetch())
    
    return get_todo
```

**Why it works**: Cairn applies `nest_asyncio.apply()` in `src/tools/__init__.py`, allowing `run_until_complete()` inside an already-running loop.

### Pattern: Database Write Operations

```python
@register_tool("create_todo")
def create_create_todo_tool(context: ToolContext):
    """Create tool that adds todo to database."""
    
    @tool
    def create_todo(title: str, description: str = "") -> dict:
        """Create a new todo.
        
        Args:
            title: Todo title
            description: Optional description
            
        Returns:
            Created todo information
        """
        async def _create():
            from db.models.todo import Todo, TodoStatus
            
            factory = get_session_factory()
            async with factory() as session:
                todo = Todo(
                    title=title,
                    description=description,
                    status=TodoStatus.PENDING
                )
                session.add(todo)
                await session.commit()
                await session.refresh(todo)
                
                return {
                    "id": str(todo.id),
                    "title": todo.title,
                    "status": todo.status.value
                }
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_create())
    
    return create_todo
```

---

## Error Handling

### Pattern: Try-Catch in Tools

```python
@tool
def risky_operation(input: str) -> dict:
    """Operation that might fail."""
    try:
        result = do_something(input)
        return {"success": True, "result": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

### Pattern: Validation

```python
@tool
def validated_tool(user_id: str, amount: float) -> dict:
    """Tool with input validation."""
    
    # Validate inputs
    if not user_id:
        return {"error": "user_id is required"}
    
    if amount <= 0:
        return {"error": "amount must be positive"}
    
    # Process
    try:
        result = process_payment(user_id, amount)
        return {"success": True, "transaction_id": result}
    except Exception as e:
        return {"error": str(e)}
```

### Pattern: Logging

```python
import logging

logger = logging.getLogger(__name__)

@register_tool("logged_tool")
def create_logged_tool(context: ToolContext):
    """Tool with logging."""
    
    @tool
    def logged_tool(input: str) -> dict:
        """Tool that logs execution."""
        logger.info(f"Tool called with input: {input}")
        
        try:
            result = process(input)
            logger.info(f"Tool succeeded: {result}")
            return {"result": result}
        except Exception as e:
            logger.error(f"Tool failed: {e}", exc_info=True)
            return {"error": str(e)}
    
    return logged_tool
```

---

## Testing Tools

### Unit Test Pattern

```python
import pytest
from src.tools import load_tools
from src.tools.context import ToolContext
from config.loader import load_default_config

def test_get_user_tool():
    # Setup
    config = load_default_config()
    context = ToolContext.from_graph_config(config)
    
    # Load tool
    tools = load_tools(["get_user"], context)
    assert len(tools) == 1
    
    get_user_tool = tools[0]
    
    # Execute
    result = get_user_tool.invoke({"user_id": "123"})
    
    # Assert
    assert result["id"] == "123"
    assert "name" in result
```

### Integration Test with Database

```python
@pytest.mark.asyncio
async def test_create_todo_tool(test_session, clean_db):
    from src.tools import load_tools
    from src.tools.context import ToolContext
    from config.loader import load_default_config
    from sqlalchemy import select
    from db.models.todo import Todo
    
    # Setup
    config = load_default_config()
    context = ToolContext.from_graph_config(config)
    
    # Load tool
    tools = load_tools(["create_todo"], context)
    create_todo = tools[0]
    
    # Execute
    result = create_todo.invoke({
        "title": "Test Todo",
        "description": "Test description"
    })
    
    # Assert result
    assert result["title"] == "Test Todo"
    todo_id = result["id"]
    
    # Verify in database
    db_result = await test_session.execute(
        select(Todo).where(Todo.id == todo_id)
    )
    todo = db_result.scalar_one()
    assert todo.title == "Test Todo"
```

### Mocking Dependencies

```python
from unittest.mock import patch, AsyncMock

def test_tool_with_mocked_service():
    from src.tools import load_tools
    from src.tools.context import ToolContext
    from config.loader import load_default_config
    
    # Setup
    config = load_default_config()
    context = ToolContext.from_graph_config(config)
    
    # Mock external service
    with patch("src.services.external.call_api") as mock_api:
        mock_api.return_value = {"data": "mocked"}
        
        # Load and execute tool
        tools = load_tools(["external_tool"], context)
        result = tools[0].invoke({"param": "value"})
        
        # Verify
        assert result["data"] == "mocked"
        mock_api.assert_called_once()
```

---

## Best Practices

### ✅ Do

- **Name tools clearly**: Use descriptive names like `get_user`, `create_todo`
- **Document parameters**: LLM uses docstrings to understand tools
- **Return structured data**: Use dicts with consistent keys
- **Handle errors gracefully**: Return error dicts instead of raising
- **Validate inputs**: Check required fields and types
- **Log important events**: Help debugging in production
- **Keep tools focused**: One tool = one action
- **Use type hints**: Helps LLM understand parameters

### ❌ Don't

- **Don't use complex return types**: Stick to dicts, lists, strings, numbers
- **Don't raise exceptions**: Return error dicts instead
- **Don't make tools do multiple things**: Split into separate tools
- **Don't forget docstrings**: LLM needs them to use tools correctly
- **Don't use mutable defaults**: `def tool(items: list = [])` is bad
- **Don't access global state**: Use ToolContext instead
- **Don't make synchronous blocking calls**: Use async patterns

### Naming Conventions

```python
# Good
@register_tool("get_user")
def create_get_user_tool(context):
    ...

@register_tool("create_todo")
def create_create_todo_tool(context):
    ...

# Bad
@register_tool("user")  # Too vague
def make_tool(context):  # Doesn't match tool name
    ...
```

### Docstring Format

```python
@tool
def example_tool(param1: str, param2: int = 10) -> dict:
    """Brief description of what the tool does.
    
    Longer explanation if needed. This helps the LLM understand
    when and how to use this tool.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (optional)
        
    Returns:
        Description of return value structure
        
    Example:
        >>> example_tool("value", param2=20)
        {"result": "success"}
    """
    pass
```

---

## Advanced Patterns

### Tool with Cache

```python
@register_tool("cached_lookup")
def create_cached_tool(context: ToolContext):
    """Tool that caches results."""
    
    @tool
    async def cached_lookup(query: str) -> dict:
        """Lookup with caching."""
        from cache.backends import get_cache_backend
        
        cache = get_cache_backend()
        cache_key = f"lookup:{query}"
        
        # Check cache
        cached = await cache.get(cache_key)
        if cached:
            return {"result": cached, "from_cache": True}
        
        # Compute result
        result = expensive_operation(query)
        
        # Cache it
        await cache.set(cache_key, result, ttl=3600)
        
        return {"result": result, "from_cache": False}
    
    return cached_lookup
```

### Tool with Memory Backend

```python
@register_tool("semantic_search")
def create_search_tool(context: ToolContext):
    """Tool that searches vector embeddings."""
    
    @tool
    def semantic_search(query: str, limit: int = 5) -> list[dict]:
        """Search using semantic similarity."""
        from memory.backends import get_backend
        from src.services.embeddings import EmbeddingsService
        
        async def _search():
            # Generate query embedding
            embeddings = EmbeddingsService()
            query_embedding = (await embeddings.embed([query]))[0]
            
            # Search
            backend = get_backend()
            results = await backend.search(query_embedding, limit=limit)
            
            return results
        
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(_search())
    
    return semantic_search
```

---

## Troubleshooting

### "Unknown tool" error

**Problem**: Tool not registered.

**Solution**: Make sure file is in `src/tools/` and doesn't start with `_`:
```bash
# Check auto-import
ls src/tools/*.py | grep -v __pycache__ | grep -v context.py
```

### "Event loop already running" error

**Problem**: Using `asyncio.run()` instead of `run_until_complete()`.

**Solution**: Use `loop.run_until_complete()`:
```python
# Wrong
result = asyncio.run(async_func())

# Correct
loop = asyncio.get_event_loop()
result = loop.run_until_complete(async_func())
```

### Tool returns None

**Problem**: Factory function returns None (tool disabled).

**Solution**: Check conditional logic in factory:
```python
@register_tool("my_tool")
def create_tool(context: ToolContext):
    if some_condition:
        return None  # Tool disabled
    # Make sure this branch returns a tool
    @tool
    def my_tool():
        pass
    return my_tool
```

---

## Further Reading

- [LangChain Tools Documentation](https://python.langchain.com/docs/modules/agents/tools/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Async SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [nest_asyncio Documentation](https://github.com/erdewit/nest_asyncio)
