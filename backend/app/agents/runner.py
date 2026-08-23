"""Entry points `ChatService` calls into the agent layer.

`run_agent_turn` drives the full compiled LangGraph supervisor graph
(`app/agents/graph.py`) end to end — this is the "real" graph execution path,
used by the non-streaming `/chat` endpoint.

`stream_agent_turn` needs token-level streaming, which a compiled graph with
a mix of streaming and non-streaming nodes doesn't cleanly support (there is
no single place to say "stream only this node's model call"), so it reuses
the same routing table, intent classifier, and `DomainAgent` objects the
graph is built from directly, without going through `StateGraph.compile()`.
Both paths make the identical routing decision from the identical agents —
only how the final agent's answer is produced (all at once vs. token by
token) differs.
"""

from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.domain_agent import DomainAgent
from app.agents.generative_ui_agent import choose_ui_blocks
from app.agents.graph import AGENTS_BY_INTENT, build_graph
from app.agents.intent import classify_intent
from app.agents.state import AgentState
from app.models.chat_message import ChatMessageModel
from app.models.enums import ChatRole
from app.services.user_memory_service import UserMemoryService


def history_to_messages(history: list[ChatMessageModel]) -> list[BaseMessage]:
    """Converts persisted chat history (session-based conversation history,
    loaded from MongoDB by `ChatService`) into LangChain messages the agent
    layer understands. System-role messages aren't part of the visible
    conversation and are skipped."""
    converted: list[BaseMessage] = []
    for message in history:
        if message.role == ChatRole.USER:
            converted.append(HumanMessage(content=message.content))
        elif message.role == ChatRole.ASSISTANT:
            converted.append(AIMessage(content=message.content))
    return converted


async def run_agent_turn(
    database: AsyncIOMotorDatabase, user_id: str, message: str, history: list[ChatMessageModel]
) -> tuple[str, list[dict[str, Any]]]:
    """Non-streaming path: runs the full compiled supervisor graph and
    returns `(reply_text, ui_blocks)`."""
    graph = build_graph(database)
    initial_state: AgentState = {
        "user_id": user_id,
        "messages": [*history_to_messages(history), HumanMessage(content=message)],
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("agent_reply", ""), final_state.get("ui_blocks", [])


async def stream_agent_turn(
    database: AsyncIOMotorDatabase,
    user_id: str,
    message: str,
    history: list[ChatMessageModel],
    *,
    result: dict[str, Any],
) -> AsyncIterator[str]:
    """Streaming path: same intent-detection + routing + memory-loading as
    the graph, but streams the chosen agent's final answer token by token.
    Once the generator is exhausted, `result["reply_text"]` and
    `result["ui_blocks"]` are populated (an async generator can't also
    `return` a value) so the caller can persist the completed turn — mirrors
    `collected_tool_messages` in `app/agents/tool_loop.py` for the same
    reason."""
    memories = [memory.content for memory in await UserMemoryService(database).recall(user_id, limit=10)]
    classification = await classify_intent(message)
    agent: DomainAgent = AGENTS_BY_INTENT[classification.intent]

    messages = [*history_to_messages(history), HumanMessage(content=message)]
    tool_messages: list[ToolMessage] = []
    chunks: list[str] = []

    async for chunk in agent.stream(database, user_id, messages, memories, collected_tool_messages=tool_messages):
        chunks.append(chunk)
        yield chunk

    reply_text = "".join(chunks)
    result["reply_text"] = reply_text
    result["ui_blocks"] = await choose_ui_blocks(reply_text, tool_messages)
