from bson import ObjectId

from app.db.collections import Collections
from app.models.category import CategoryModel
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[CategoryModel]):
    collection_name = Collections.CATEGORIES
    model = CategoryModel
    reference_fields = ("user_id",)

    async def get_by_id_for_user(self, category_id: str, user_id: str) -> CategoryModel | None:
        if not ObjectId.is_valid(category_id):
            return None
        return await self.find_one(
            {
                "_id": ObjectId(category_id),
                "$or": [{"user_id": ObjectId(user_id)}, {"is_system": True}],
                "is_deleted": False,
            }
        )

    async def list_for_user(self, user_id: str, *, category_type: str | None = None) -> list[CategoryModel]:
        query: dict = {"$or": [{"user_id": ObjectId(user_id)}, {"is_system": True}], "is_deleted": False}
        if category_type:
            query["type"] = category_type
        return await self.find_many(query, sort=[("name", 1)])

    async def name_exists_for_user(self, user_id: str, name: str, category_type: str) -> bool:
        count = await self.count(
            {"user_id": ObjectId(user_id), "name": name, "type": category_type, "is_deleted": False}
        )
        return count > 0
