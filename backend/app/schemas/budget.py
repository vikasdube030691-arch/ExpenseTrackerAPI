from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import BudgetPeriod


class BudgetCreate(BaseModel):
    category_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    period: BudgetPeriod = BudgetPeriod.MONTHLY
    start_date: datetime
    end_date: datetime | None = None


class BudgetUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    amount: float | None = Field(default=None, gt=0)
    end_date: datetime | None = None


class BudgetResponse(BaseModel):
    id: str
    user_id: str
    category_id: str | None
    name: str | None
    amount: float
    currency: str
    period: BudgetPeriod
    start_date: datetime
    end_date: datetime | None
    created_at: datetime
    updated_at: datetime
