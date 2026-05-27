import importlib
import logging
import pkgutil
from typing import Any, Callable

import nest_asyncio

from lib.cairn.paths import get_module_dir
from src.tools.context import ToolContext

# Allow nested event loops for tools that need to run async code synchronously
nest_asyncio.apply()

logger = logging.getLogger(__name__)

TOOL_FACTORY: dict[str, Callable[[ToolContext], Any]] = {}


def register_tool(name: str):
    """Register a tool factory function.

    Args:
        name: Unique name for the tool

    Returns:
        Decorator that registers the factory function
    """
    def decorator(fn: Callable[[ToolContext], Any]):
        TOOL_FACTORY[name] = fn
        return fn

    return decorator


def _auto_import_tools():
    """Auto-import all tool modules to trigger @register_tool decorators."""
    tools_dir = get_module_dir(__file__)

    for _, module_name, _ in pkgutil.iter_modules([str(tools_dir)]):
        # Skip private/special modules
        if module_name.startswith('_') or module_name == 'context':
            continue
        try:
            importlib.import_module(f'src.tools.{module_name}')
            logger.debug(f"Auto-imported tool module: {module_name}")
        except ImportError as e:
            logger.warning(f"Failed to import tool module {module_name}: {e}")


def load_tools(tool_names: list[str], context: ToolContext) -> list[Any]:
    """Load tools by name using registered factories.

    Args:
        tool_names: List of tool names to load
        context: Tool context with config and settings

    Returns:
        List of instantiated tool objects (None tools filtered out)
    """
    tools = []
    for name in tool_names:
        if name not in TOOL_FACTORY:
            available = ", ".join(sorted(TOOL_FACTORY.keys()))
            raise ValueError(f"Unknown tool '{name}'. Available: {available}")
        tool = TOOL_FACTORY[name](context)
        if tool is not None:
            tools.append(tool)
    return tools


# Call auto-import after all functions are defined
_auto_import_tools()
