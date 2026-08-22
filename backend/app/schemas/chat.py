from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ChatRole
from app.schemas.generative_ui import UIComponent


class ChatSessionCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=255)


class ChatSessionResponse(BaseModel):
    id: str
    user_id: str
    title: str
    is_archived: bool
    last_message_at: datetime
    created_at: datetime
    updated_at: datetime


class ChatMessageCreate(BaseModel):
    role: ChatRole
    content: str = Field(min_length=1, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    role: ChatRole
    content: str
    metadata: dict[str, Any]
    created_at: datetime
    ui_blocks: list[UIComponent] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, description="Omit to start a new session")
    message: str = Field(min_length=1, max_length=10000)


class ChatResponse(BaseModel):
    session_id: str
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatSessionDetailResponse(BaseModel):
    session: ChatSessionResponse
    messages: list[ChatMessageResponse]
