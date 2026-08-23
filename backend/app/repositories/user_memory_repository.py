import re

from bson import ObjectId

from app.db.collections import Collections
from app.models.user_memory import UserMemoryModel
from app.repositories.base import BaseRepository


class UserMemoryRepository(BaseRepository[UserMemoryModel]):
    collection_name = Collections.USER_MEMORIES
    model = UserMemoryModel
    reference_fields = ("user_id",)

    async def get_by_id_for_user(self, memory_id: str, user_id: str) -> UserMemoryModel | None:
        if not ObjectId.is_valid(memory_id):
            return None
        return await self.find_one({"_id": ObjectId(memory_id), "user_id": ObjectId(user_id)})

    async def list_for_user(self, user_id: str, *, limit: int = 20) -> list[UserMemoryModel]:
        return await self.find_many({"user_id": ObjectId(user_id)}, limit=limit, sort=[("created_at", -1)])

    async def search_for_user(self, user_id: str, query: str, *, limit: int = 10) -> list[UserMemoryModel]:
        """Substring/keyword search over a user's memories. There is no
        embedding/vector store in this version, so this is deliberately a
        plain case-insensitive regex match rather than semantic search —
        adequate for the small number of memories a single user is expected
        to accumulate; swap for a vector-backed lookup if that stops holding."""
        pattern = re.escape(query.strip())
        if not pattern:
            return await self.list_for_user(user_id, limit=limit)
        return await self.find_many(
            {"user_id": ObjectId(user_id), "content": {"$regex": pattern, "$options": "i"}},
            limit=limit,
            sort=[("created_at", -1)],
        )

    async def delete_for_user(self, memory_id: str, user_id: str) -> bool:
        existing = await self.get_by_id_for_user(memory_id, user_id)
        if existing is None:
            return False
        return await self.hard_delete(memory_id)
