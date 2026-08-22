from bson import ObjectId

from app.db.collections import Collections
from app.models.budget import BudgetModel
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[BudgetModel]):
    collection_name = Collections.BUDGETS
    model = BudgetModel
    reference_fields = ("user_id", "category_id")

    async def get_by_id_for_user(self, budget_id: str, user_id: str) -> BudgetModel | None:
        if not ObjectId.is_valid(budget_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(budget_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    async def list_for_user(self, user_id: str) -> list[BudgetModel]:
        return await self.find_many({"user_id": ObjectId(user_id), "is_deleted": False}, sort=[("start_date", -1)])
