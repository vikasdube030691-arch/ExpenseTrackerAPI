from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.chat_message import ChatMessageModel
from app.models.chat_session import ChatSessionModel
from app.repositories.chat_repository import ChatMessageRepository, ChatSessionRepository
from app.schemas.chat import ChatMessageCreate, ChatSessionCreate


class ChatService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._sessions = ChatSessionRepository(database)
        self._messages = ChatMessageRepository(database)

    async def create_session(self, user_id: str, payload: ChatSessionCreate) -> ChatSessionModel:
        session = ChatSessionModel(user_id=user_id, title=payload.title)
        return await self._sessions.create(session)

    async def list_sessions(
        self, user_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[ChatSessionModel], int]:
        skip = (page - 1) * page_size
        return await self._sessions.list_for_user(user_id, skip=skip, limit=page_size)

    async def get_session(self, user_id: str, session_id: str) -> ChatSessionModel:
        session = await self._sessions.get_by_id_for_user(session_id, user_id)
        if session is None:
            raise DocumentNotFoundError("chat_sessions", session_id)
        return session

    async def add_message(
        self, user_id: str, session_id: str, payload: ChatMessageCreate
    ) -> ChatMessageModel:
        await self.get_session(user_id, session_id)
        message = ChatMessageModel(session_id=session_id, user_id=user_id, **payload.model_dump())
        created = await self._messages.create(message)
        await self._sessions.touch(session_id)
        return created

    async def list_messages(
        self, user_id: str, session_id: str, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[ChatMessageModel], int]:
        await self.get_session(user_id, session_id)
        skip = (page - 1) * page_size
        return await self._messages.list_for_session(session_id, user_id, skip=skip, limit=page_size)

    async def delete_session(self, user_id: str, session_id: str) -> None:
        await self.get_session(user_id, session_id)
        await self._sessions.soft_delete(session_id)
