from typing import Any, Callable

from src.tools.context import ToolContext

TOOL_FACTORY: dict[str, Callable[[ToolContext], Any]] = {}


def register_tool(name: str):
    def decorator(fn: Callable[[ToolContext], Any]):
        TOOL_FACTORY[name] = fn
        return fn

    return decorator


def load_tools(tool_names: list[str], context: ToolContext) -> list[Any]:
    # Import tools to register them
    from src.tools import todo_tools  # noqa: F401

    tools = []
    for name in tool_names:
        if name not in TOOL_FACTORY:
            available = ", ".join(sorted(TOOL_FACTORY.keys()))
            raise ValueError(f"Unknown tool '{name}'. Available: {available}")
        tool = TOOL_FACTORY[name](context)
        if tool is not None:
            tools.append(tool)
    return tools
