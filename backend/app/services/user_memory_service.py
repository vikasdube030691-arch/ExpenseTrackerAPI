from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.user_memory import UserMemoryModel
from app.repositories.user_memory_repository import UserMemoryRepository


class UserMemoryService:
    """Backs the Memory Manager agent's tools. Every method takes `user_id`
    as an explicit parameter supplied by the caller (never by the LLM) — see
    `app/tools/memory_tools.py` for where that boundary is enforced."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._memories = UserMemoryRepository(database)

    async def remember(self, user_id: str, content: str) -> UserMemoryModel:
        return await self._memories.create(UserMemoryModel(user_id=user_id, content=content))

    async def recall(self, user_id: str, *, query: str | None = None, limit: int = 10) -> list[UserMemoryModel]:
        if query:
            return await self._memories.search_for_user(user_id, query, limit=limit)
        return await self._memories.list_for_user(user_id, limit=limit)

    async def update_memory(self, user_id: str, memory_id: str, content: str) -> UserMemoryModel:
        existing = await self._memories.get_by_id_for_user(memory_id, user_id)
        if existing is None:
            raise DocumentNotFoundError("user_memories", memory_id)
        updated = await self._memories.update_by_id(memory_id, {"content": content})
        if updated is None:
            raise DocumentNotFoundError("user_memories", memory_id)
        return updated

    async def forget(self, user_id: str, memory_id: str) -> bool:
        return await self._memories.delete_for_user(memory_id, user_id)
