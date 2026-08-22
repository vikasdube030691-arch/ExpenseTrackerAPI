from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError, DuplicateDocumentError
from app.models.category import CategoryModel
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._categories = CategoryRepository(database)

    async def create_category(self, user_id: str, payload: CategoryCreate) -> CategoryModel:
        if await self._categories.name_exists_for_user(user_id, payload.name, payload.type.value):
            raise DuplicateDocumentError("categories", f"'{payload.name}' already exists for this user")
        category = CategoryModel(user_id=user_id, **payload.model_dump())
        return await self._categories.create(category)

    async def list_categories(self, user_id: str, *, category_type: str | None = None) -> list[CategoryModel]:
        return await self._categories.list_for_user(user_id, category_type=category_type)

    async def get_category(self, user_id: str, category_id: str) -> CategoryModel:
        category = await self._categories.get_by_id_for_user(category_id, user_id)
        if category is None:
            raise DocumentNotFoundError("categories", category_id)
        return category

    async def update_category(self, user_id: str, category_id: str, payload: CategoryUpdate) -> CategoryModel:
        existing = await self.get_category(user_id, category_id)
        if existing.is_system:
            raise DocumentNotFoundError("categories", category_id)
        updated = await self._categories.update_by_id(category_id, payload.model_dump(exclude_unset=True))
        if updated is None:
            raise DocumentNotFoundError("categories", category_id)
        return updated

    async def delete_category(self, user_id: str, category_id: str) -> None:
        existing = await self.get_category(user_id, category_id)
        if existing.is_system:
            raise DocumentNotFoundError("categories", category_id)
        await self._categories.soft_delete(category_id)
