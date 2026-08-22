from typing import Self

from pydantic import Field, field_validator, model_validator

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, UTCDatetime, normalize_currency
from app.models.enums import BudgetPeriod


class BudgetModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    category_id: PyObjectId | None = None
    """None means the budget applies across all categories."""
    name: str | None = Field(default=None, max_length=255)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    start_date: UTCDatetime
    end_date: UTCDatetime | None = None

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @model_validator(mode="after")
    def _validate_date_range(self) -> Self:
        if self.end_date and self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
