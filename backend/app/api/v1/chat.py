import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db, pagination_params
from app.models.chat_message import ChatMessageModel
from app.models.chat_session import ChatSessionModel
from app.models.user import UserModel
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionDetailResponse,
    ChatSessionResponse,
)
from app.schemas.common import PaginatedResponse, PaginationParams
from app.services.chat_service import ChatService

router = APIRouter()


def _session_response(session: ChatSessionModel) -> ChatSessionResponse:
    return ChatSessionResponse(**session.model_dump())


def _message_response(message: ChatMessageModel) -> ChatMessageResponse:
    return ChatMessageResponse(**message.model_dump())


@router.post("/", response_model=ChatResponse, summary="Send a chat message")
async def send_message(
    payload: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> ChatResponse:
    """Omit `session_id` to start a new conversation. Returns the persisted user
    message alongside the assistant's (non-streamed) reply."""
    service = ChatService(database)
    session, user_message, assistant_message = await service.send_message(current_user.id, payload)
    return ChatResponse(
        session_id=session.id,
        user_message=_message_response(user_message),
        assistant_message=_message_response(assistant_message),
    )


@router.post("/stream", summary="Send a chat message and stream the reply")
async def stream_message(
    payload: ChatRequest,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> StreamingResponse:
    """Server-Sent Events: a `session` event first (so a caller starting a new
    conversation learns its id), then one `delta` event per reply chunk, then `done`."""
    service = ChatService(database)
    session, chunks = await service.start_stream(current_user.id, payload)

    async def event_source():
        yield f"event: session\ndata: {json.dumps({'session_id': session.id})}\n\n"
        async for chunk in chunks:
            yield f"event: delta\ndata: {json.dumps({'delta': chunk})}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")


@router.get("/sessions", response_model=PaginatedResponse[ChatSessionResponse], summary="List chat sessions")
async def list_sessions(
    pagination: PaginationParams = Depends(pagination_params),
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> PaginatedResponse[ChatSessionResponse]:
    service = ChatService(database)
    items, total = await service.list_sessions(current_user.id, page=pagination.page, page_size=pagination.page_size)
    return PaginatedResponse(
        items=[_session_response(s) for s in items], total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse, summary="Get a chat session")
async def get_session(
    session_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> ChatSessionDetailResponse:
    service = ChatService(database)
    session = await service.get_session(current_user.id, session_id)
    messages, _ = await service.list_messages(current_user.id, session_id, page=1, page_size=200)
    return ChatSessionDetailResponse(
        session=_session_response(session), messages=[_message_response(m) for m in messages]
    )
