from typing import Any

from pydantic import Field

from app.models.common import CreatedAtDocument, PyObjectId
from app.models.enums import ChatRole


class ChatMessageModel(CreatedAtDocument):
    session_id: PyObjectId
    user_id: PyObjectId
    role: ChatRole
    content: str = Field(min_length=1, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)
