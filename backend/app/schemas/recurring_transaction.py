from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import RecurringFrequency, TransactionType


class RecurringTransactionCreate(BaseModel):
    account_id: str
    category_id: str
    transaction_type: TransactionType
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    merchant: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    frequency: RecurringFrequency
    interval: int = Field(default=1, ge=1)
    start_date: datetime
    end_date: datetime | None = None


class RecurringTransactionUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    is_active: bool | None = None
    end_date: datetime | None = None


class RecurringTransactionResponse(BaseModel):
    id: str
    user_id: str
    account_id: str
    category_id: str
    transaction_type: TransactionType
    amount: float
    currency: str
    merchant: str | None
    description: str | None
    frequency: RecurringFrequency
    interval: int
    start_date: datetime
    end_date: datetime | None
    next_run_date: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime
