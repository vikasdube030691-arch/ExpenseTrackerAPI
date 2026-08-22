from pydantic import Field, field_validator

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, normalize_currency
from app.models.enums import AccountType


class AccountModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    name: str = Field(min_length=1, max_length=255)
    account_type: AccountType = AccountType.BANK
    currency: str = Field(min_length=3, max_length=3)
    balance: float = 0.0
    is_active: bool = True

    @field_validator("currency")
    @classmethod
    def _normalize_currency(cls, value: str) -> str:
        return normalize_currency(value)
