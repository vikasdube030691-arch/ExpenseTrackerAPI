from typing import Any

from pydantic import Field

from app.models.common import CreatedAtDocument, PyObjectId


class AuditLogModel(CreatedAtDocument):
    user_id: PyObjectId | None = None
    """None for system-initiated events with no acting user."""
    action: str = Field(min_length=1, max_length=100)
    resource_type: str | None = Field(default=None, max_length=100)
    resource_id: PyObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
