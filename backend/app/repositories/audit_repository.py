from bson import ObjectId

from app.db.collections import Collections
from app.models.audit_log import AuditLogModel
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLogModel]):
    collection_name = Collections.AUDIT_LOGS
    model = AuditLogModel
    reference_fields = ("user_id", "resource_id")

    async def list_for_user(
        self, user_id: str, *, skip: int = 0, limit: int = 50
    ) -> tuple[list[AuditLogModel], int]:
        query = {"user_id": ObjectId(user_id)}
        return await self.paginate(query, skip=skip, limit=limit, sort=[("created_at", -1)])
