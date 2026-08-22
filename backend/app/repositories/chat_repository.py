from bson import ObjectId

from app.db.collections import Collections
from app.models.chat_message import ChatMessageModel
from app.models.chat_session import ChatSessionModel
from app.models.common import utcnow
from app.repositories.base import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSessionModel]):
    collection_name = Collections.CHAT_SESSIONS
    model = ChatSessionModel
    reference_fields = ("user_id",)

    async def get_by_id_for_user(self, session_id: str, user_id: str) -> ChatSessionModel | None:
        if not ObjectId.is_valid(session_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(session_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    async def list_for_user(
        self, user_id: str, *, skip: int = 0, limit: int = 20
    ) -> tuple[list[ChatSessionModel], int]:
        query = {"user_id": ObjectId(user_id), "is_deleted": False}
        return await self.paginate(query, skip=skip, limit=limit, sort=[("last_message_at", -1)])

    async def touch(self, session_id: str) -> None:
        now = utcnow()
        await self.collection.update_one(
            {"_id": ObjectId(session_id)}, {"$set": {"last_message_at": now, "updated_at": now}}
        )


class ChatMessageRepository(BaseRepository[ChatMessageModel]):
    collection_name = Collections.CHAT_MESSAGES
    model = ChatMessageModel
    reference_fields = ("session_id", "user_id")

    async def list_for_session(
        self, session_id: str, user_id: str, *, skip: int = 0, limit: int = 50
    ) -> tuple[list[ChatMessageModel], int]:
        query = {"session_id": ObjectId(session_id), "user_id": ObjectId(user_id)}
        return await self.paginate(query, skip=skip, limit=limit, sort=[("created_at", 1)])
