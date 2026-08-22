from bson import ObjectId

from app.db.collections import Collections
from app.models.common import utcnow
from app.models.refresh_token import RefreshTokenModel
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshTokenModel]):
    collection_name = Collections.REFRESH_TOKENS
    model = RefreshTokenModel
    reference_fields = ("user_id",)

    async def get_by_token_hash(self, token_hash: str) -> RefreshTokenModel | None:
        return await self.find_one({"token_hash": token_hash, "revoked": False})

    async def revoke(self, document_id: str) -> RefreshTokenModel | None:
        return await self.update_by_id(document_id, {"revoked": True, "revoked_at": utcnow()})

    async def revoke_all_for_user(self, user_id: str) -> int:
        result = await self.collection.update_many(
            {"user_id": ObjectId(user_id), "revoked": False},
            {"$set": {"revoked": True, "revoked_at": utcnow()}},
        )
        return result.modified_count
