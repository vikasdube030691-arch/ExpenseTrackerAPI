from bson import ObjectId
from pymongo import ReturnDocument

from app.db.collections import Collections
from app.models.common import utcnow
from app.models.dashboard_preference import DashboardPreferenceModel
from app.repositories.base import BaseRepository


class DashboardPreferenceRepository(BaseRepository[DashboardPreferenceModel]):
    collection_name = Collections.DASHBOARD_PREFERENCES
    model = DashboardPreferenceModel
    reference_fields = ("user_id",)

    async def get_by_user(self, user_id: str) -> DashboardPreferenceModel | None:
        return await self.find_one({"user_id": ObjectId(user_id)})

    async def upsert_for_user(self, user_id: str, update_fields: dict) -> DashboardPreferenceModel:
        now = utcnow()
        payload = dict(update_fields)
        payload["updated_at"] = now
        document = await self.collection.find_one_and_update(
            {"user_id": ObjectId(user_id)},
            {"$set": payload, "$setOnInsert": {"user_id": ObjectId(user_id), "created_at": now}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(document)
