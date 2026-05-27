"""Categorization graph for assigning categories to todos using AI."""

import hashlib

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from cache.backends import get_cache_backend
from config.loader import load_graph_config
from src.agents.llm import build_llm
from src.models.state import TodoCategorizeState
from src.tools import load_tools
from src.tools.context import ToolContext


def _text_hash(text: str) -> str:
    """Generate hash for caching category by text."""
    return hashlib.md5(text.encode()).hexdigest()[:16]


def build_categorize_graph():
    """Build a graph that categorizes a todo using AI."""
    # Load config
    config = load_graph_config("categorize")

    # Create tool context and load tools
    context = ToolContext.from_graph_config(config)
    tools = load_tools(config.tools, context)

    # Build LLM with tools
    llm = build_llm(config=config.llm)
    llm_with_tools = llm.bind_tools(tools)

    # Get cache backend
    cache = get_cache_backend()

    # Define nodes
    async def check_cache(state: TodoCategorizeState):
        """Check if category is cached."""
        todo_text = state["todo_text"]
        cache_key = f"category:hash:{_text_hash(todo_text)}"

        if cache:
            try:
                cached = await cache.get(cache_key)
                if cached:
                    return {"category": cached}
            except Exception:
                pass  # Cache miss or error, continue to LLM

        return state

    def call_model(state: TodoCategorizeState):
        """Call LLM to categorize todo."""
        # Skip if already categorized from cache
        if state.get("category"):
            return state

        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: TodoCategorizeState):
        """Determine if we should continue to tools or end."""
        # If already categorized from cache, skip everything
        if state.get("category"):
            return END

        messages = state["messages"]
        last_message = messages[-1]

        # If LLM called tools, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, we're done
        return END

    async def save_to_cache(state: TodoCategorizeState):
        """Save category to cache."""
        # Extract category from tool calls or final message
        category = state.get("category")
        todo_text = state["todo_text"]

        # Try to extract category from messages if not in state
        if not category:
            for message in reversed(state["messages"]):
                if hasattr(message, "tool_calls"):
                    for tool_call in message.tool_calls:
                        if tool_call.get("name") == "update_todo":
                            category = tool_call.get("args", {}).get("category")
                            if category:
                                break

        # Cache it
        if category and cache and todo_text:
            cache_key = f"category:hash:{_text_hash(todo_text)}"
            try:
                await cache.set(cache_key, category, ttl=86400)  # 24 hours
            except Exception:
                pass  # Cache write failure shouldn't break the flow

        return {"category": category}

    # Build graph
    graph = StateGraph(TodoCategorizeState)

    # Add nodes
    graph.add_node("check_cache", check_cache)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("save_cache", save_to_cache)

    # Add edges
    graph.set_entry_point("check_cache")
    graph.add_edge("check_cache", "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: "save_cache"})
    graph.add_edge("tools", "agent")
    graph.add_edge("save_cache", END)

    return graph.compile()
