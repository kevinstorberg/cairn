from typing import Any

from langchain_core.tools import BaseTool


async def build_react_agent(llm: Any, tools: list[BaseTool], *, system_prompt: str = "", recursion_limit: int = 25):
    from langgraph.prebuilt import create_react_agent

    kwargs: dict[str, Any] = {}
    if system_prompt:
        kwargs["prompt"] = system_prompt

    agent = create_react_agent(llm, tools, **kwargs)
    return agent
