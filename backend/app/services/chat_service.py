import logging
from collections.abc import AsyncIterator
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.agents.llm import is_ai_configured
from app.agents.runner import run_agent_turn, stream_agent_turn
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError
from app.models.chat_message import ChatMessageModel
from app.models.chat_session import ChatSessionModel
from app.models.enums import ChatRole
from app.repositories.chat_repository import ChatMessageRepository, ChatSessionRepository
from app.schemas.chat import ChatMessageCreate, ChatRequest, ChatSessionCreate
from app.schemas.generative_ui import validate_ui_blocks
from app.services.ai.chat_completion import generate_reply, stream_reply
from app.services.ai.generative_ui_builder import build_ui_blocks

logger = logging.getLogger(__name__)

# The LangChain/LangGraph agent layer (app/agents, app/tools) only runs when
# ANTHROPIC_API_KEY is configured; otherwise every method below falls back to
# the placeholder responder + rule-based UI builder used before that layer
# existed, so local dev and the test suite never need a live Anthropic key.


def _session_title_from(message: str) -> str:
    trimmed = message.strip()
    return (trimmed[:60] or "New conversation") if trimmed else "New conversation"


async def _build_assistant_metadata(database: AsyncIOMotorDatabase, user_id: str, user_message: str) -> dict[str, Any]:
    """Builds the AI's structured UI payload for one reply, validating it
    exactly as untrusted LLM output before it can be persisted or returned —
    see `app/schemas/generative_ui.py`. Never raises: a validation failure
    just means no UI blocks are attached, not a broken chat response."""
    raw_blocks = await build_ui_blocks(database, user_id, user_message)
    if not raw_blocks:
        return {}

    result = validate_ui_blocks(raw_blocks)
    if result.rejected:
        logger.warning("generative UI validation rejected %d block(s): %s", len(result.rejected), result.rejected)
    if not result.blocks:
        return {}
    return {"ui_blocks": [block.model_dump(mode="json") for block in result.blocks]}


class ChatService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._database = database
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

    async def _resolve_session(self, user_id: str, payload: ChatRequest) -> ChatSessionModel:
        if payload.session_id:
            return await self.get_session(user_id, payload.session_id)
        return await self.create_session(user_id, ChatSessionCreate(title=_session_title_from(payload.message)))

    async def _recent_history(self, user_id: str, session_id: str) -> list[ChatMessageModel]:
        messages, _ = await self._messages.list_for_session(session_id, user_id, limit=200)
        return messages[-settings.ai_history_message_limit :]

    async def send_message(
        self, user_id: str, payload: ChatRequest
    ) -> tuple[ChatSessionModel, ChatMessageModel, ChatMessageModel]:
        session = await self._resolve_session(user_id, payload)
        history = await self._recent_history(user_id, session.id)
        user_message = await self._messages.create(
            ChatMessageModel(session_id=session.id, user_id=user_id, role=ChatRole.USER, content=payload.message)
        )

        if is_ai_configured():
            reply_text, ui_blocks = await run_agent_turn(self._database, user_id, payload.message, history)
            metadata: dict[str, Any] = {"ui_blocks": ui_blocks} if ui_blocks else {}
        else:
            reply_text = generate_reply(payload.message)
            metadata = await _build_assistant_metadata(self._database, user_id, payload.message)

        assistant_message = await self._messages.create(
            ChatMessageModel(
                session_id=session.id, user_id=user_id, role=ChatRole.ASSISTANT, content=reply_text, metadata=metadata
            )
        )
        await self._sessions.touch(session.id)
        return session, user_message, assistant_message

    async def start_stream(
        self, user_id: str, payload: ChatRequest
    ) -> tuple[ChatSessionModel, AsyncIterator[str]]:
        """Resolves/creates the session and persists the user's message up front
        (so it's on the record even if the client disconnects mid-stream), then
        returns an async generator that yields assistant reply chunks and persists
        the full assistant message once streaming completes."""
        session = await self._resolve_session(user_id, payload)
        history = await self._recent_history(user_id, session.id)
        await self._messages.create(
            ChatMessageModel(session_id=session.id, user_id=user_id, role=ChatRole.USER, content=payload.message)
        )

        async def _generate_with_agents() -> AsyncIterator[str]:
            result: dict[str, Any] = {}
            async for chunk in stream_agent_turn(self._database, user_id, payload.message, history, result=result):
                yield chunk
            ui_blocks = result.get("ui_blocks", [])
            await self._messages.create(
                ChatMessageModel(
                    session_id=session.id,
                    user_id=user_id,
                    role=ChatRole.ASSISTANT,
                    content=result.get("reply_text", ""),
                    metadata={"ui_blocks": ui_blocks} if ui_blocks else {},
                )
            )
            await self._sessions.touch(session.id)

        async def _generate_placeholder() -> AsyncIterator[str]:
            chunks: list[str] = []
            async for chunk in stream_reply(payload.message):
                chunks.append(chunk)
                yield chunk
            metadata = await _build_assistant_metadata(self._database, user_id, payload.message)
            await self._messages.create(
                ChatMessageModel(
                    session_id=session.id,
                    user_id=user_id,
                    role=ChatRole.ASSISTANT,
                    content="".join(chunks),
                    metadata=metadata,
                )
            )
            await self._sessions.touch(session.id)

        return session, (_generate_with_agents() if is_ai_configured() else _generate_placeholder())
