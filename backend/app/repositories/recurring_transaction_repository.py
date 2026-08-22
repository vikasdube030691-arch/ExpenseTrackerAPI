from datetime import datetime

from bson import ObjectId

from app.db.collections import Collections
from app.models.recurring_transaction import RecurringTransactionModel
from app.repositories.base import BaseRepository


class RecurringTransactionRepository(BaseRepository[RecurringTransactionModel]):
    collection_name = Collections.RECURRING_TRANSACTIONS
    model = RecurringTransactionModel
    reference_fields = ("user_id", "account_id", "category_id")

    async def get_by_id_for_user(self, recurring_id: str, user_id: str) -> RecurringTransactionModel | None:
        if not ObjectId.is_valid(recurring_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(recurring_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    async def list_for_user(self, user_id: str, *, active_only: bool = True) -> list[RecurringTransactionModel]:
        query: dict = {"user_id": ObjectId(user_id), "is_deleted": False}
        if active_only:
            query["is_active"] = True
        return await self.find_many(query, sort=[("next_run_date", 1)])

    async def list_due(self, as_of: datetime) -> list[RecurringTransactionModel]:
        return await self.find_many(
            {"is_active": True, "is_deleted": False, "next_run_date": {"$lte": as_of}},
            sort=[("next_run_date", 1)],
        )
