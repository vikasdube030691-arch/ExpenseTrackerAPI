from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.audit_log import AuditLogModel
from app.repositories.audit_repository import AuditLogRepository


class AuditService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._audit_logs = AuditLogRepository(database)

    async def log(
        self,
        *,
        user_id: str | None,
        action: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLogModel:
        entry = AuditLogModel(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return await self._audit_logs.create(entry)

    async def list_for_user(
        self, user_id: str, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[AuditLogModel], int]:
        skip = (page - 1) * page_size
        return await self._audit_logs.list_for_user(user_id, skip=skip, limit=page_size)
