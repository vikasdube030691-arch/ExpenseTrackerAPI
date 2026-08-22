import asyncio
from collections.abc import AsyncIterator

# Placeholder chat-completion provider — no LLM is wired up. It exists so the
# /chat and /chat/stream endpoints, session persistence, and the SSE streaming
# contract can be built and tested end-to-end. Swap `generate_reply`/`stream_reply`
# for a real call (e.g. the Claude API) without touching ChatService or the routers,
# since both only depend on these two function signatures.


def generate_reply(user_message: str) -> str:
    return (
        "This is a placeholder response from the AI Expense Tracker assistant. "
        f'You said: "{user_message.strip()}". Wire a real LLM provider into '
        "app/services/ai/chat_completion.py to generate real answers."
    )


async def stream_reply(user_message: str) -> AsyncIterator[str]:
    for word in generate_reply(user_message).split(" "):
        yield word + " "
        await asyncio.sleep(0.02)
