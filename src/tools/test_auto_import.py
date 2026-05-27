"""Test tool to verify auto-import mechanism."""
from langchain_core.tools import tool
from src.tools import register_tool
from src.tools.context import ToolContext


@register_tool("test_auto")
def create_test_auto_tool(context: ToolContext):
    """Test tool for verifying auto-import works."""

    @tool
    def test_auto() -> str:
        """Test tool that returns success message.

        Returns:
            Success message
        """
        return "Auto-import works!"

    return test_auto
