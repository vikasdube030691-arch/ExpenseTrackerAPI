from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DashboardPreferenceUpdate(BaseModel):
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    theme: str | None = None
    widgets: list[str] | None = None
    settings: dict[str, Any] | None = None


class DashboardPreferenceResponse(BaseModel):
    id: str
    user_id: str
    default_currency: str
    theme: str
    widgets: list[str]
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
