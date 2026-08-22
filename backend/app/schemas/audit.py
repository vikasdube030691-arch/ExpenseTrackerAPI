from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
