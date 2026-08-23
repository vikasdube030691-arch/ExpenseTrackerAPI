from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from app.core.config import settings

_MAX_TOKENS = 2048


class AiNotConfiguredError(RuntimeError):
    """Raised when the agent layer is invoked without ANTHROPIC_API_KEY set.
    `ChatService` checks `is_ai_configured()` up front and falls back to the
    placeholder responder, so callers should not normally hit this — it's a
    guard against calling into `app/agents` from somewhere that skipped that
    check."""


def is_ai_configured() -> bool:
    return bool(settings.anthropic_api_key)


@lru_cache
def get_chat_model() -> ChatAnthropic:
    if not settings.anthropic_api_key:
        raise AiNotConfiguredError("ANTHROPIC_API_KEY is not set")
    return ChatAnthropic(
        model=settings.ai_model,
        api_key=settings.anthropic_api_key,
        max_tokens=_MAX_TOKENS,
        timeout=60,
        max_retries=2,
    )
