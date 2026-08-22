from typing import Any, Generic, TypeVar

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError as MongoDuplicateKeyError

from app.core.exceptions import DocumentNotFoundError, DuplicateDocumentError
from app.models.common import utcnow

ModelT = TypeVar("ModelT", bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    """Generic MongoDB CRUD repository. Subclasses declare `collection_name`, `model`,
    and `reference_fields` (ObjectId-valued fields besides `_id` that must be stored
    as BSON ObjectId rather than string)."""

    collection_name: str
    model: type[ModelT]
    reference_fields: tuple[str, ...] = ()

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self.collection: AsyncIOMotorCollection = database[self.collection_name]

    def _to_model(self, document: dict[str, Any]) -> ModelT:
        return self.model.model_validate(document)

    def _supports_soft_delete(self) -> bool:
        return "is_deleted" in self.model.model_fields

    def _serialize(self, document: ModelT) -> dict[str, Any]:
        payload = document.model_dump(by_alias=True)
        payload["_id"] = ObjectId(payload["_id"])
        for field in self.reference_fields:
            if payload.get(field) is not None:
                payload[field] = ObjectId(payload[field])
        return payload

    async def create(self, document: ModelT) -> ModelT:
        payload = self._serialize(document)
        try:
            await self.collection.insert_one(payload)
        except MongoDuplicateKeyError as exc:
            raise DuplicateDocumentError(self.collection_name, str(exc)) from exc
        return document

    async def get_by_id(self, document_id: str, *, include_deleted: bool = False) -> ModelT | None:
        if not ObjectId.is_valid(document_id):
            return None
        query: dict[str, Any] = {"_id": ObjectId(document_id)}
        if self._supports_soft_delete() and not include_deleted:
            query["is_deleted"] = False
        document = await self.collection.find_one(query)
        return self._to_model(document) if document else None

    async def require_by_id(self, document_id: str, *, include_deleted: bool = False) -> ModelT:
        document = await self.get_by_id(document_id, include_deleted=include_deleted)
        if document is None:
            raise DocumentNotFoundError(self.collection_name, document_id)
        return document

    async def find_one(self, query: dict[str, Any]) -> ModelT | None:
        document = await self.collection.find_one(query)
        return self._to_model(document) if document else None

    async def find_many(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 20,
        sort: list[tuple[str, int]] | None = None,
    ) -> list[ModelT]:
        cursor = self.collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        cursor = cursor.skip(skip).limit(limit)
        return [self._to_model(document) async for document in cursor]

    async def count(self, query: dict[str, Any]) -> int:
        return await self.collection.count_documents(query)

    async def paginate(
        self,
        query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 20,
        sort: list[tuple[str, int]] | None = None,
    ) -> tuple[list[ModelT], int]:
        items = await self.find_many(query, skip=skip, limit=limit, sort=sort)
        total = await self.count(query)
        return items, total

    async def update_by_id(self, document_id: str, update_fields: dict[str, Any]) -> ModelT | None:
        if not ObjectId.is_valid(document_id):
            return None
        set_fields = dict(update_fields)
        if "updated_at" in self.model.model_fields:
            set_fields["updated_at"] = utcnow()
        document = await self.collection.find_one_and_update(
            {"_id": ObjectId(document_id)},
            {"$set": set_fields},
            return_document=ReturnDocument.AFTER,
        )
        return self._to_model(document) if document else None

    async def soft_delete(self, document_id: str) -> ModelT | None:
        if not self._supports_soft_delete():
            raise NotImplementedError(f"{self.collection_name} does not support soft delete")
        return await self.update_by_id(document_id, {"is_deleted": True, "deleted_at": utcnow()})

    async def hard_delete(self, document_id: str) -> bool:
        if not ObjectId.is_valid(document_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0
