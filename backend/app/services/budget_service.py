from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.budget import BudgetModel
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.budget import BudgetCreate, BudgetUpdate


class BudgetService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._budgets = BudgetRepository(database)
        self._categories = CategoryRepository(database)

    async def create_budget(self, user_id: str, payload: BudgetCreate) -> BudgetModel:
        if payload.category_id and await self._categories.get_by_id_for_user(payload.category_id, user_id) is None:
            raise DocumentNotFoundError("categories", payload.category_id)
        budget = BudgetModel(user_id=user_id, **payload.model_dump())
        return await self._budgets.create(budget)

    async def list_budgets(self, user_id: str) -> list[BudgetModel]:
        return await self._budgets.list_for_user(user_id)

    async def get_budget(self, user_id: str, budget_id: str) -> BudgetModel:
        budget = await self._budgets.get_by_id_for_user(budget_id, user_id)
        if budget is None:
            raise DocumentNotFoundError("budgets", budget_id)
        return budget

    async def update_budget(self, user_id: str, budget_id: str, payload: BudgetUpdate) -> BudgetModel:
        await self.get_budget(user_id, budget_id)
        updated = await self._budgets.update_by_id(budget_id, payload.model_dump(exclude_unset=True))
        if updated is None:
            raise DocumentNotFoundError("budgets", budget_id)
        return updated

    async def delete_budget(self, user_id: str, budget_id: str) -> None:
        await self.get_budget(user_id, budget_id)
        await self._budgets.soft_delete(budget_id)
