import pytest

from src.tools import TOOL_FACTORY, load_tools, register_tool
from src.tools.context import ToolContext


@pytest.mark.unit
class TestToolRegistry:
    def test_register_tool_adds_to_factory(self):
        @register_tool("test_tool_reg")
        def create_test_tool(context):
            return None

        assert "test_tool_reg" in TOOL_FACTORY

    def test_load_tools_unknown_raises(self):
        ctx = ToolContext(enabled_sources=[], source_limits={})
        with pytest.raises(ValueError, match="Unknown tool"):
            load_tools(["nonexistent_tool_xyz_99"], ctx)

    def test_load_tools_filters_none(self):
        @register_tool("disabled_tool_test")
        def create_disabled(context):
            return None

        ctx = ToolContext(enabled_sources=[], source_limits={})
        tools = load_tools(["disabled_tool_test"], ctx)
        assert tools == []

    def test_load_tools_includes_non_none(self):
        class FakeTool:
            name = "fake"

        @register_tool("enabled_tool_test")
        def create_enabled(context):
            return FakeTool()

        ctx = ToolContext(enabled_sources=[], source_limits={})
        tools = load_tools(["enabled_tool_test"], ctx)
        assert len(tools) == 1
        assert tools[0].name == "fake"
