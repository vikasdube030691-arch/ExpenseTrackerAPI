"""A bounded ReAct-style tool-calling loop shared by every domain agent
(expense, analytics, budget, report, memory). Each agent only differs by its
system prompt and its toolset — the loop mechanics (invoke, execute tool
calls, feed results back, repeat until a plain-text answer) are identical, so
they live here once instead of five times.
"""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.agents.llm import get_chat_model
from app.core.config import settings


def extract_text(content: Any) -> str:
    """Anthropic content can arrive as a plain string or a list of content
    blocks (`{"type": "text", "text": "..."}` among others, e.g. tool_use
    blocks which carry no display text); this normalizes both to a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return ""


async def _execute_tool_call(tools_by_name: dict[str, BaseTool], call: dict[str, Any]) -> ToolMessage:
    tool = tools_by_name.get(call["name"])
    if tool is None:
        result: Any = {"error": f"Unknown tool '{call['name']}'"}
    else:
        try:
            result = await tool.ainvoke(call["args"])
        except Exception as exc:  # noqa: BLE001 - surfaced to the model, never raised into the graph
            result = {"error": str(exc)}
    return ToolMessage(content=str(result), tool_call_id=call["id"])


async def run_tool_calling_agent(
    system_prompt: str,
    tools: list[BaseTool],
    messages: list[BaseMessage],
    *,
    tags: list[str] | None = None,
) -> tuple[AIMessage, list[ToolMessage]]:
    """Non-streaming path (used by the plain `/chat` endpoint): runs the loop
    to completion and returns the final AIMessage plus every ToolMessage
    produced along the way (the Generative UI Agent reads these for real
    numbers instead of re-parsing them out of the reply text)."""
    model = get_chat_model().bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}
    conversation: list[BaseMessage] = [SystemMessage(content=system_prompt), *messages]
    config = {"tags": tags} if tags else None
    tool_messages: list[ToolMessage] = []

    for _ in range(settings.ai_max_tool_iterations):
        response = await model.ainvoke(conversation, config=config)
        conversation.append(response)
        if not response.tool_calls:
            return response, tool_messages
        for call in response.tool_calls:
            tool_message = await _execute_tool_call(tools_by_name, call)
            tool_messages.append(tool_message)
            conversation.append(tool_message)

    # Iteration cap reached without a plain-text answer: ask once more with
    # tools unavailable so the loop always terminates with something to show.
    final = await get_chat_model().ainvoke(conversation, config=config)
    return final, tool_messages


async def stream_tool_calling_agent(
    system_prompt: str,
    tools: list[BaseTool],
    messages: list[BaseMessage],
    *,
    tags: list[str] | None = None,
    collected_tool_messages: list[ToolMessage] | None = None,
) -> AsyncIterator[str]:
    """Streaming path (used by `/chat/stream`): yields text deltas as the
    model generates them. A turn where the model decides to call a tool
    normally carries no text content blocks, so in practice only the final,
    plain-text turn produces visible output — tool-calling turns happen
    silently in between deltas. If given, `collected_tool_messages` is
    appended to in place so the caller can inspect gathered tool data once
    the stream is exhausted (an async generator can't also `return` a value)."""
    model = get_chat_model().bind_tools(tools)
    tools_by_name = {t.name: t for t in tools}
    conversation: list[BaseMessage] = [SystemMessage(content=system_prompt), *messages]
    config = {"tags": tags} if tags else None

    for _ in range(settings.ai_max_tool_iterations):
        accumulated: AIMessageChunk | None = None
        async for chunk in model.astream(conversation, config=config):
            text = extract_text(chunk.content)
            if text:
                yield text
            accumulated = chunk if accumulated is None else accumulated + chunk

        if accumulated is None:
            return
        conversation.append(accumulated)
        if not accumulated.tool_calls:
            return
        for call in accumulated.tool_calls:
            tool_message = await _execute_tool_call(tools_by_name, call)
            if collected_tool_messages is not None:
                collected_tool_messages.append(tool_message)
            conversation.append(tool_message)
