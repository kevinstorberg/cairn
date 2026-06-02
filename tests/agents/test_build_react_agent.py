import pytest

from src.agents.base import build_react_agent


@pytest.mark.asyncio
async def test_build_react_agent_passes_prompt_to_langgraph(monkeypatch):
    import langgraph.prebuilt

    calls = []

    def fake_create_react_agent(llm, tools, **kwargs):
        calls.append({"llm": llm, "tools": tools, "kwargs": kwargs})
        return "agent"

    monkeypatch.setattr(langgraph.prebuilt, "create_react_agent", fake_create_react_agent)

    result = await build_react_agent("llm", ["tool"], system_prompt="Follow the system prompt.")

    assert result == "agent"
    assert calls == [
        {
            "llm": "llm",
            "tools": ["tool"],
            "kwargs": {"prompt": "Follow the system prompt."},
        }
    ]


@pytest.mark.asyncio
async def test_build_react_agent_omits_empty_prompt(monkeypatch):
    import langgraph.prebuilt

    calls = []

    def fake_create_react_agent(llm, tools, **kwargs):
        calls.append(kwargs)
        return "agent"

    monkeypatch.setattr(langgraph.prebuilt, "create_react_agent", fake_create_react_agent)

    await build_react_agent("llm", [])

    assert calls == [{}]
