from pydantic import Field

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, UTCDatetime, utcnow


class ChatSessionModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    title: str = Field(default="New conversation", max_length=255)
    is_archived: bool = False
    last_message_at: UTCDatetime = Field(default_factory=utcnow)
