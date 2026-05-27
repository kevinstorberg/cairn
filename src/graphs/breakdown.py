"""Task breakdown graph for breaking complex todos into subtasks."""

from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from config.loader import load_graph_config
from src.agents.llm import build_llm
from src.models.state import TodoBreakdownState
from src.tools import load_tools
from src.tools.context import ToolContext


def build_breakdown_graph():
    """Build a graph that breaks down a todo into subtasks."""
    # Load config
    config = load_graph_config("breakdown")

    # Create tool context and load tools
    context = ToolContext.from_graph_config(config)
    tools = load_tools(config.tools, context)

    # Build LLM with tools
    llm = build_llm(config=config.llm)
    llm_with_tools = llm.bind_tools(tools)

    # Define nodes
    def call_model(state: TodoBreakdownState):
        """Call LLM to generate subtasks."""
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: TodoBreakdownState):
        """Determine if we should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        # If LLM called tools, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        # Otherwise, we're done
        return END

    # Build graph
    graph = StateGraph(TodoBreakdownState)

    # Add nodes
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(tools))

    # Add edges
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
