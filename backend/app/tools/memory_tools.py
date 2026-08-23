"""Tools for the Memory Manager agent: retrieve, store, update, and delete
per-user long-term memories, backed by `UserMemoryService`.
"""

from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.user_memory_service import UserMemoryService
from app.tools._helpers import as_tool_error, to_json


def build_memory_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
    memories = UserMemoryService(database)

    @tool
    async def recall_memories(query: Annotated[str | None, "keyword to search for, or omit to list recent memories"] = None) -> Any:
        """Retrieves the user's stored long-term memories (preferences,
        recurring facts, standing instructions), optionally filtered by a
        keyword."""
        return to_json(await memories.recall(user_id, query=query))

    @tool
    async def remember(
        content: Annotated[str, "a short, self-contained fact or preference, e.g. 'Prefers budgets tracked in EUR'"],
    ) -> Any:
        """Stores a new long-term memory about the user. Only call this for
        things worth remembering across conversations (stated preferences,
        recurring facts) — not for one-off details already in this
        conversation's history."""
        try:
            return to_json(await memories.remember(user_id, content))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def update_memory(memory_id: str, content: str) -> Any:
        """Updates the text of an existing memory."""
        try:
            return to_json(await memories.update_memory(user_id, memory_id, content))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def forget_memory(memory_id: str) -> Any:
        """Permanently deletes a stored memory, e.g. when the user asks you
        to forget something."""
        deleted = await memories.forget(user_id, memory_id)
        return {"deleted": deleted, "memory_id": memory_id}

    return [recall_memories, remember, update_memory, forget_memory]
