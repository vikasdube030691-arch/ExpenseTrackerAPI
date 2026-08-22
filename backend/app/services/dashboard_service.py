from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.common import utcnow
from app.models.dashboard_preference import DashboardPreferenceModel
from app.models.enums import TransactionType
from app.repositories.budget_repository import BudgetRepository
from app.repositories.dashboard_repository import DashboardPreferenceRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.dashboard import DashboardPreferenceUpdate


class DashboardService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._preferences = DashboardPreferenceRepository(database)
        self._transactions = TransactionRepository(database)
        self._budgets = BudgetRepository(database)

    async def get_preferences(self, user_id: str) -> DashboardPreferenceModel:
        existing = await self._preferences.get_by_user(user_id)
        if existing is not None:
            return existing
        return await self._preferences.upsert_for_user(user_id, {})

    async def update_preferences(
        self, user_id: str, payload: DashboardPreferenceUpdate
    ) -> DashboardPreferenceModel:
        return await self._preferences.upsert_for_user(user_id, payload.model_dump(exclude_unset=True))

    async def get_summary(self, user_id: str, start_date: datetime, end_date: datetime) -> dict:
        income = await self._transactions.sum_by_type(user_id, TransactionType.INCOME.value, start_date, end_date)
        expense = await self._transactions.sum_by_type(user_id, TransactionType.EXPENSE.value, start_date, end_date)
        count = await self._transactions.count_filtered(user_id, start_date=start_date, end_date=end_date)
        return {
            "period_start": start_date,
            "period_end": end_date,
            "total_income": income,
            "total_expense": expense,
            "net": income - expense,
            "transaction_count": count,
        }

    async def get_category_analysis(self, user_id: str, start_date: datetime, end_date: datetime) -> dict:
        breakdown = await self._transactions.sum_by_category(user_id, start_date, end_date)
        return {"period_start": start_date, "period_end": end_date, "breakdown": breakdown}

    async def get_trends(
        self, user_id: str, start_date: datetime, end_date: datetime, granularity: str = "month"
    ) -> dict:
        points = await self._transactions.trends(user_id, start_date, end_date, granularity)
        return {"granularity": granularity, "period_start": start_date, "period_end": end_date, "points": points}

    async def get_overview(self, user_id: str) -> dict:
        now = utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        summary = await self.get_summary(user_id, start_of_month, now)
        recent_transactions, _ = await self._transactions.search(user_id, skip=0, limit=5)
        budgets = await self._budgets.list_for_user(user_id)

        budget_progress = []
        for budget in budgets:
            spent = await self._transactions.sum_amount(
                user_id,
                category_id=budget.category_id,
                transaction_type=TransactionType.EXPENSE.value,
                start_date=budget.start_date,
                end_date=budget.end_date or now,
            )
            budget_progress.append(
                {
                    "budget_id": budget.id,
                    "category_id": budget.category_id,
                    "name": budget.name,
                    "amount": budget.amount,
                    "spent": spent,
                    "remaining": budget.amount - spent,
                    "period": budget.period,
                }
            )

        return {
            "summary": summary,
            "recent_transactions": [t.model_dump() for t in recent_transactions],
            "budget_progress": budget_progress,
        }
