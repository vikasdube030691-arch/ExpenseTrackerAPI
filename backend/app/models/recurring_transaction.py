from pydantic import Field, field_validator

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, UTCDatetime, normalize_currency
from app.models.enums import RecurringFrequency, TransactionType


class RecurringTransactionModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    account_id: PyObjectId
    category_id: PyObjectId
    transaction_type: TransactionType
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    frequency: RecurringFrequency
    interval: int = Field(default=1, ge=1)
    start_date: UTCDatetime
    end_date: UTCDatetime | None = None
    next_run_date: UTCDatetime
    is_active: bool = True

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)
