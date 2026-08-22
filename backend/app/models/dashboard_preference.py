from typing import Any

from pydantic import Field

from app.models.common import MongoDocument, PyObjectId


class DashboardPreferenceModel(MongoDocument):
    user_id: PyObjectId
    default_currency: str = Field(default="USD", min_length=3, max_length=3)
    theme: str = Field(default="system")
    widgets: list[str] = Field(
        default_factory=lambda: ["spending_by_category", "monthly_trend", "budget_progress"]
    )
    settings: dict[str, Any] = Field(default_factory=dict)
