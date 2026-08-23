"""A minimal fake chat model for testing `app/agents/tool_loop.py`'s loop
mechanics (execute a tool call, feed the result back, terminate on a
plain-text answer) without a real Anthropic API key. `FakeMessagesListChatModel`
already cycles through a scripted list of responses; the only gap is
`bind_tools`, which the base class deliberately leaves unimplemented since
the real signature is provider-specific — here it's a no-op because the
scripted `AIMessage`s already carry whatever `tool_calls` the test wants.
"""

from typing import Any

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.runnables import Runnable


class FakeToolCallingChatModel(FakeMessagesListChatModel):
    def bind_tools(self, tools: Any, *, tool_choice: str | None = None, **kwargs: Any) -> Runnable:
        return self
