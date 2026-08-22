from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    account_type: AccountType = AccountType.BANK
    currency: str = Field(min_length=3, max_length=3)
    balance: float = 0.0


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    account_type: AccountType | None = None
    is_active: bool | None = None


class AccountResponse(BaseModel):
    id: str
    user_id: str
    name: str
    account_type: AccountType
    currency: str
    balance: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
