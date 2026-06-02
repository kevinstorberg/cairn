import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.tools import TOOL_FACTORY, load_tools, register_tool
from src.tools.context import ToolContext


@pytest.mark.unit
class TestToolRegistry:
    def test_auto_import_registers_example_tool(self):
        assert "test_auto" in TOOL_FACTORY

    def test_imports_with_uvloop_event_loop(self):
        code = """
import asyncio
import uvloop

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)
try:
    import src.tools as tools
    assert "test_auto" in tools.TOOL_FACTORY
finally:
    loop.close()
"""
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)

        assert result.returncode == 0, result.stderr

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

    def test_tool_context_from_graph_config_copies_graph_name_and_tools(self):
        graph_config = SimpleNamespace(name="workflow-a", tools=["tool-a", "tool-b"])

        context = ToolContext.from_graph_config(graph_config)

        assert context.graph_name == "workflow-a"
        assert context.tools == ["tool-a", "tool-b"]
        assert context.enabled_sources == []
        assert context.source_limits == {}
        assert context.scope is None
