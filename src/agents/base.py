from typing import Any

from langchain_core.tools import BaseTool


def _resolve_create_react_agent():
    try:
        from langgraph.prebuilt import create_react_agent
    except ImportError:
        from langgraph.prebuilt.chat_agent_executor import create_react_agent

    return create_react_agent


async def build_react_agent(llm: Any, tools: list[BaseTool], *, system_prompt: str = "", recursion_limit: int = 25):
    kwargs: dict[str, Any] = {}
    if system_prompt:
        kwargs["prompt"] = system_prompt

    create_react_agent = _resolve_create_react_agent()
    agent = create_react_agent(llm, tools, **kwargs)
    return agent
