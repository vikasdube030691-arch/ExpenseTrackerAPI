from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.models.common import utcnow
from app.models.user import UserModel
from app.schemas.dashboard import (
    CategoryAnalysisResponse,
    DashboardOverviewResponse,
    DashboardSummaryResponse,
    TrendsResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


def _default_range(start_date: datetime | None, end_date: datetime | None) -> tuple[datetime, datetime]:
    """Defaults to the current calendar month when no range is given."""
    now = utcnow()
    start = start_date or now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    end = end_date or now
    return start, end


@router.get("/", response_model=DashboardOverviewResponse, summary="Dashboard overview")
async def get_overview(
    current_user: UserModel = Depends(get_current_user), database: AsyncIOMotorDatabase = Depends(get_db)
) -> DashboardOverviewResponse:
    """Current-month income/expense summary, the 5 most recent transactions, and
    spent-vs-budget progress for every active budget."""
    service = DashboardService(database)
    data = await service.get_overview(current_user.id)
    return DashboardOverviewResponse(**data)


@router.get("/summary", response_model=DashboardSummaryResponse, summary="Income/expense summary")
async def get_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> DashboardSummaryResponse:
    """Defaults to the current calendar month when `start_date`/`end_date` are omitted."""
    start, end = _default_range(start_date, end_date)
    service = DashboardService(database)
    data = await service.get_summary(current_user.id, start, end)
    return DashboardSummaryResponse(**data)


@router.get("/category-analysis", response_model=CategoryAnalysisResponse, summary="Spending by category")
async def get_category_analysis(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> CategoryAnalysisResponse:
    start, end = _default_range(start_date, end_date)
    service = DashboardService(database)
    data = await service.get_category_analysis(current_user.id, start, end)
    return CategoryAnalysisResponse(**data)


@router.get("/trends", response_model=TrendsResponse, summary="Income/expense trend over time")
async def get_trends(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    granularity: Literal["day", "month"] = Query(default="month"),
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> TrendsResponse:
    start, end = _default_range(start_date, end_date)
    service = DashboardService(database)
    data = await service.get_trends(current_user.id, start, end, granularity)
    return TrendsResponse(**data)
