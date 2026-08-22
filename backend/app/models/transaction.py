from pydantic import BaseModel, Field, field_validator

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, UTCDatetime, normalize_currency, utcnow
from app.models.enums import TransactionType


class ReceiptReference(BaseModel):
    url: str
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    uploaded_at: UTCDatetime = Field(default_factory=utcnow)


class TransactionModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    account_id: PyObjectId
    transaction_type: TransactionType
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category_id: PyObjectId
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    transaction_date: UTCDatetime
    tags: list[str] = Field(default_factory=list)
    receipt: ReceiptReference | None = None

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str]) -> list[str]:
        return sorted({tag.strip().lower() for tag in value if tag.strip()})
