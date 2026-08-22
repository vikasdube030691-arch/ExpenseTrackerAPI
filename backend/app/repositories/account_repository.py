from bson import ObjectId
from pymongo import ReturnDocument

from app.db.collections import Collections
from app.models.account import AccountModel
from app.models.common import utcnow
from app.repositories.base import BaseRepository


class AccountRepository(BaseRepository[AccountModel]):
    collection_name = Collections.ACCOUNTS
    model = AccountModel
    reference_fields = ("user_id",)

    async def get_by_id_for_user(self, account_id: str, user_id: str) -> AccountModel | None:
        if not ObjectId.is_valid(account_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(account_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    async def list_for_user(self, user_id: str, *, include_inactive: bool = False) -> list[AccountModel]:
        query: dict = {"user_id": ObjectId(user_id), "is_deleted": False}
        if not include_inactive:
            query["is_active"] = True
        return await self.find_many(query, sort=[("created_at", -1)])

    async def adjust_balance(self, account_id: str, delta: float) -> AccountModel | None:
        document = await self.collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$inc": {"balance": delta}, "$set": {"updated_at": utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(document) if document else None
