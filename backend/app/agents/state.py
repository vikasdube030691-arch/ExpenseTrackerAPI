"""Shared LangGraph state for one chat turn.

`user_id` travels through the graph state for convenience (routing functions
read it to log/tag), but it is never the source of authorization — every node
that needs to touch data builds its tools via `app/tools/*.py`'s
`build_xxx_tools(database, user_id)` factories using the `user_id` the graph
was constructed with in `app/agents/graph.py`, which comes from the
authenticated request in `ChatService`, not from anything an LLM produced.
"""

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph.message import add_messages

Intent = Literal["expense", "analytics", "budget", "report", "memory", "general"]


class AgentState(TypedDict, total=False):
    user_id: str
    messages: Annotated[list[BaseMessage], add_messages]
    memories: list[str]
    intent: Intent
    agent_reply: str
    tool_messages: list[ToolMessage]
    ui_blocks: list[dict[str, Any]]
