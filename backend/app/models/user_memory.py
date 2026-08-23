from pydantic import Field

from app.models.common import MongoDocument, PyObjectId


class UserMemoryModel(MongoDocument):
    """A single long-term memory the AI layer's Memory Manager agent has
    chosen to keep about a user (a stated preference, a recurring fact, a
    standing instruction) — separate from chat history, which is the
    conversation transcript itself. Deliberately hard-deletable (no
    `is_deleted` flag): forgetting something on request should actually
    remove it, not just hide it, since this collection exists to hold
    personal context a user may want fully erased."""

    user_id: PyObjectId
    content: str = Field(min_length=1, max_length=1000)
