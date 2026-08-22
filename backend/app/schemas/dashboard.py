from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.models.enums import BudgetPeriod
from app.schemas.transaction import TransactionResponse


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


class DashboardSummaryResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    total_income: float
    total_expense: float
    net: float
    transaction_count: int


class CategoryBreakdownItem(BaseModel):
    category_id: str
    total: float
    count: int


class CategoryAnalysisResponse(BaseModel):
    period_start: datetime
    period_end: datetime
    breakdown: list[CategoryBreakdownItem]


class TrendPoint(BaseModel):
    period: str
    income: float
    expense: float


class TrendsResponse(BaseModel):
    granularity: Literal["day", "month"]
    period_start: datetime
    period_end: datetime
    points: list[TrendPoint]


class BudgetProgressItem(BaseModel):
    budget_id: str
    category_id: str | None
    name: str | None
    amount: float
    spent: float
    remaining: float
    period: BudgetPeriod


class DashboardOverviewResponse(BaseModel):
    summary: DashboardSummaryResponse
    recent_transactions: list[TransactionResponse]
    budget_progress: list[BudgetProgressItem]
