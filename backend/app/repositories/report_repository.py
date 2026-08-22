from bson import ObjectId

from app.db.collections import Collections
from app.models.report import GeneratedReportModel
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[GeneratedReportModel]):
    collection_name = Collections.GENERATED_REPORTS
    model = GeneratedReportModel
    reference_fields = ("user_id",)

    async def get_by_id_for_user(self, report_id: str, user_id: str) -> GeneratedReportModel | None:
        if not ObjectId.is_valid(report_id):
            return None
        return await self.find_one(
            {"_id": ObjectId(report_id), "user_id": ObjectId(user_id), "is_deleted": False}
        )

    async def list_for_user(
        self, user_id: str, *, skip: int = 0, limit: int = 20
    ) -> tuple[list[GeneratedReportModel], int]:
        query = {"user_id": ObjectId(user_id), "is_deleted": False}
        return await self.paginate(query, skip=skip, limit=limit, sort=[("created_at", -1)])
