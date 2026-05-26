from typing import Any

from config.models import LLMConfig


def build_llm(
    *,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    config: LLMConfig | None = None,
) -> Any:
    from src.settings import get_settings

    settings = get_settings()

    resolved_provider = provider or (config.provider if config else None) or settings.LLM_PROVIDER
    resolved_model = model or (config.model if config else None) or settings.LLM_MODEL
    resolved_max_tokens = max_tokens or (config.max_tokens if config else None) or 4096

    if resolved_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=resolved_model, max_tokens=resolved_max_tokens)

    if resolved_provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=resolved_model, max_tokens=resolved_max_tokens)

    raise ValueError(f"Unknown LLM provider: {resolved_provider!r}. Available: anthropic, openai")
