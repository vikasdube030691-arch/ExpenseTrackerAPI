from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import TransactionType


class ReceiptReferenceSchema(BaseModel):
    url: str
    filename: str | None = None
    content_type: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)


class TransactionCreate(BaseModel):
    account_id: str
    transaction_type: TransactionType
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    category_id: str
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    transaction_date: datetime
    tags: list[str] = Field(default_factory=list)
    receipt: ReceiptReferenceSchema | None = None


class TransactionUpdate(BaseModel):
    account_id: str | None = None
    transaction_type: TransactionType | None = None
    amount: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    category_id: str | None = None
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    transaction_date: datetime | None = None
    tags: list[str] | None = None
    receipt: ReceiptReferenceSchema | None = None


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    account_id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    category_id: str
    merchant: str | None
    description: str | None
    transaction_date: datetime
    tags: list[str]
    receipt: ReceiptReferenceSchema | None
    created_at: datetime
    updated_at: datetime


class TransactionFilter(BaseModel):
    transaction_type: TransactionType | None = None
    account_id: str | None = None
    category_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = None
    tags: list[str] | None = None
    search: str | None = None
