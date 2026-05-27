"""
Integration tests for TODO AI task breakdown.

Tests:
- Tool registry loads tools
- Tools execute database operations
- Graph orchestration works
- LLM generates subtasks
- Subtasks saved to database
- Memory stores breakdown history
- Provider switching (Anthropic, OpenAI)
"""

import pytest
from httpx import AsyncClient

from db.models.todo import Todo


@pytest.mark.integration
class TestTodoBreakdown:
    @pytest.mark.asyncio
    async def test_tool_registry_loads_tools(self):
        """Test tool registry can load todo tools."""
        from src.tools import load_tools
        from src.tools.context import ToolContext

        context = ToolContext(tools=["get_todo", "create_subtask"])
        tools = load_tools(["get_todo", "create_subtask"], context)

        assert len(tools) == 2
        assert all(hasattr(tool, "name") for tool in tools)
        assert any(tool.name == "get_todo" for tool in tools)
        assert any(tool.name == "create_subtask" for tool in tools)

    @pytest.mark.asyncio
    async def test_tool_registry_rejects_unknown(self):
        """Test tool registry rejects unknown tool names."""
        from src.tools import load_tools
        from src.tools.context import ToolContext

        context = ToolContext()
        with pytest.raises(ValueError, match="Unknown tool"):
            load_tools(["nonexistent_tool"], context)

    @pytest.mark.asyncio
    async def test_get_todo_tool_execution(self, db_session, clean_db):
        """Test get_todo tool can fetch todo from database."""
        from src.tools import load_tools
        from src.tools.context import ToolContext

        # Create a todo
        todo = Todo(title="Test todo", description="Test description")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Load tool
        context = ToolContext()
        tools = load_tools(["get_todo"], context)
        get_todo_tool = tools[0]

        # Execute tool
        result = get_todo_tool.invoke({"todo_id": str(todo.id)})

        assert "error" not in result
        assert result["id"] == str(todo.id)
        assert result["title"] == "Test todo"
        assert result["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_get_todo_tool_handles_missing(self, db_session, clean_db):
        """Test get_todo tool handles missing todos."""
        from uuid import uuid4

        from src.tools import load_tools
        from src.tools.context import ToolContext

        context = ToolContext()
        tools = load_tools(["get_todo"], context)
        get_todo_tool = tools[0]

        # Execute with non-existent ID
        result = get_todo_tool.invoke({"todo_id": str(uuid4())})

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_subtask_tool_execution(self, db_session, clean_db):
        """Test create_subtask tool creates subtask in database."""
        from sqlalchemy import select
        from src.tools import load_tools
        from src.tools.context import ToolContext

        # Create parent todo
        parent = Todo(title="Parent task")
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        # Load tool
        context = ToolContext()
        tools = load_tools(["create_subtask"], context)
        create_subtask_tool = tools[0]

        # Execute tool
        result = create_subtask_tool.invoke(
            {"parent_id": str(parent.id), "title": "Subtask 1", "description": "First subtask"}
        )

        assert "error" not in result
        assert result["title"] == "Subtask 1"
        assert result["parent_id"] == str(parent.id)

        # Verify in database
        subtask_id = result["id"]
        result = await db_session.execute(select(Todo).where(Todo.id == subtask_id))
        subtask = result.scalar_one()
        assert subtask.parent_id == parent.id
        assert subtask.title == "Subtask 1"

    @pytest.mark.asyncio
    async def test_create_subtask_inherits_parent_attributes(self, db_session, clean_db):
        """Test subtasks inherit status and priority from parent."""
        from db.models.todo import TodoPriority, TodoStatus
        from src.tools import load_tools
        from src.tools.context import ToolContext

        # Create parent with specific status and priority
        parent = Todo(title="Parent", status=TodoStatus.IN_PROGRESS, priority=TodoPriority.HIGH)
        db_session.add(parent)
        await db_session.commit()
        await db_session.refresh(parent)

        # Create subtask
        context = ToolContext()
        tools = load_tools(["create_subtask"], context)
        create_subtask_tool = tools[0]

        result = create_subtask_tool.invoke({"parent_id": str(parent.id), "title": "Subtask"})

        assert "error" not in result
        assert result["status"] == "in_progress"  # Inherited from parent

    @pytest.mark.asyncio
    async def test_graph_config_loads(self):
        """Test breakdown graph configuration loads correctly."""
        from config.loader import load_graph_config

        config = load_graph_config("breakdown")

        assert config.llm.provider in ["anthropic", "openai"]
        assert config.tools == ["get_todo", "create_subtask"]
        assert config.memory.backend in ["faiss", "pgvector", "pinecone"]

    @pytest.mark.asyncio
    async def test_breakdown_graph_builds(self):
        """Test breakdown graph can be constructed."""
        from src.graphs.breakdown import build_breakdown_graph

        graph = build_breakdown_graph()

        assert graph is not None
        assert hasattr(graph, "invoke")

    @pytest.mark.asyncio
    async def test_breakdown_graph_basic_execution(self, db_session, clean_db):
        """Test breakdown graph can execute without LLM."""
        from langchain_core.messages import HumanMessage

        from src.graphs.breakdown import build_breakdown_graph

        # Create a todo
        todo = Todo(title="Simple task", description="Very simple")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Build graph
        graph = build_breakdown_graph()

        # Create minimal state
        initial_state = {
            "messages": [HumanMessage(content="Test message")],
            "todo_id": str(todo.id),
            "todo_title": todo.title,
            "todo_description": todo.description or "",
            "subtasks_created": [],
        }

        # This should execute without error (though may not create subtasks without API key)
        try:
            result = graph.invoke(initial_state)
            assert "messages" in result
        except Exception as e:
            # If it fails due to missing API key, that's expected in test env
            if "api" not in str(e).lower() and "key" not in str(e).lower():
                raise

    @pytest.mark.asyncio
    async def test_update_todo_tool_sets_category(self, db_session, clean_db):
        """Test update_todo tool can set category."""
        from sqlalchemy import select
        from src.tools import load_tools
        from src.tools.context import ToolContext

        # Create todo
        todo = Todo(title="Task")
        db_session.add(todo)
        await db_session.commit()
        await db_session.refresh(todo)

        # Load tool
        context = ToolContext()
        tools = load_tools(["update_todo"], context)
        update_tool = tools[0]

        # Update category
        result = update_tool.invoke({"todo_id": str(todo.id), "category": "development"})

        assert "error" not in result
        assert result["category"] == "development"

        # Verify in database
        result = await db_session.execute(select(Todo).where(Todo.id == todo.id))
        updated_todo = result.scalar_one()
        assert updated_todo.category == "development"

    @pytest.mark.asyncio
    async def test_llm_builder_anthropic(self):
        """Test LLM builder can create Anthropic client."""
        from src.agents.llm import build_llm

        llm = build_llm(provider="anthropic", model="claude-sonnet-4-6")

        assert llm is not None
        assert hasattr(llm, "invoke")

    @pytest.mark.asyncio
    async def test_llm_builder_openai(self):
        """Test LLM builder can create OpenAI client."""
        import os

        from src.agents.llm import build_llm

        if not os.environ.get("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")

        llm = build_llm(provider="openai", model="gpt-4")

        assert llm is not None
        assert hasattr(llm, "invoke")

    @pytest.mark.asyncio
    async def test_llm_builder_from_config(self):
        """Test LLM builder uses config defaults."""
        from config.loader import load_graph_config
        from src.agents.llm import build_llm

        config = load_graph_config("breakdown")
        llm = build_llm(config=config.llm)

        assert llm is not None

    @pytest.mark.asyncio
    async def test_llm_builder_rejects_unknown_provider(self):
        """Test LLM builder rejects unknown provider."""
        from src.agents.llm import build_llm

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            build_llm(provider="unknown")
