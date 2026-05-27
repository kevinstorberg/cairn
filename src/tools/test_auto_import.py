"""Example tool demonstrating the tool registration pattern.

TEMPLATE EXAMPLE: This file shows template users how to create and register tools
using the @register_tool decorator and auto-import system. When you add a new tool
file to src/tools/, it will be automatically discovered and loaded.

To create your own tool:
1. Create a new .py file in src/tools/ (e.g., my_tool.py)
2. Use @register_tool("my_tool_key") decorator
3. Define a factory function that takes ToolContext
4. Return a LangChain tool instance

This example can be deleted once you understand the pattern.
"""
from langchain_core.tools import tool
from src.tools import register_tool
from src.tools.context import ToolContext


@register_tool("test_auto")
def create_test_auto_tool(context: ToolContext):
    """Example tool factory demonstrating the registration pattern.

    Template example: Shows how to create a tool that gets auto-imported.
    The @register_tool decorator adds this to the TOOL_FACTORY registry.

    Args:
        context: ToolContext with graph name and configuration

    Returns:
        A LangChain tool instance
    """

    @tool
    def test_auto() -> str:
        """Example tool that returns a success message.

        This is the actual tool that LangChain will call. Keep the docstring
        descriptive - it's used by the LLM to understand what the tool does.

        Returns:
            Success message confirming the tool works
        """
        return "Auto-import works!"

    return test_auto
