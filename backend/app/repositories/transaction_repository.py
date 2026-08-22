from datetime import datetime
from typing import Any

from bson import ObjectId

from app.db.collections import Collections
from app.models.transaction import TransactionModel
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[TransactionModel]):
    collection_name = Collections.TRANSACTIONS
    model = TransactionModel
    reference_fields = ("user_id", "account_id", "category_id")

    async def get_by_id_for_user(self, transaction_id: str, user_id: str) -> TransactionModel | None:
        if not ObjectId.is_valid(transaction_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(transaction_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    def _build_filter_query(
        self,
        user_id: str,
        *,
        transaction_type: str | None = None,
        account_id: str | None = None,
        category_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"user_id": ObjectId(user_id), "is_deleted": False}
        if transaction_type:
            query["transaction_type"] = transaction_type
        if account_id:
            query["account_id"] = ObjectId(account_id)
        if category_id:
            query["category_id"] = ObjectId(category_id)
        if start_date or end_date:
            date_query: dict[str, Any] = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["transaction_date"] = date_query
        if min_amount is not None or max_amount is not None:
            amount_query: dict[str, Any] = {}
            if min_amount is not None:
                amount_query["$gte"] = min_amount
            if max_amount is not None:
                amount_query["$lte"] = max_amount
            query["amount"] = amount_query
        if tags:
            query["tags"] = {"$in": tags}
        if search:
            query["$or"] = [
                {"merchant": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}},
            ]
        return query

    async def search(
        self, user_id: str, *, skip: int = 0, limit: int = 20, **filters: Any
    ) -> tuple[list[TransactionModel], int]:
        query = self._build_filter_query(user_id, **filters)
        return await self.paginate(query, skip=skip, limit=limit, sort=[("transaction_date", -1)])

    async def sum_by_type(
        self, user_id: str, transaction_type: str, start_date: datetime, end_date: datetime
    ) -> float:
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "transaction_type": transaction_type,
                    "transaction_date": {"$gte": start_date, "$lte": end_date},
                    "is_deleted": False,
                }
            },
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        return result[0]["total"] if result else 0.0

    async def sum_by_category(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        pipeline = [
            {
                "$match": {
                    "user_id": ObjectId(user_id),
                    "transaction_date": {"$gte": start_date, "$lte": end_date},
                    "is_deleted": False,
                }
            },
            {"$group": {"_id": "$category_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        return await self.collection.aggregate(pipeline).to_list(length=None)
