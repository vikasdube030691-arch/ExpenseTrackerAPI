from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.enums import ReportStatus
from app.models.report import GeneratedReportModel
from app.repositories.report_repository import ReportRepository
from app.schemas.report import ReportCreate


class ReportService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._reports = ReportRepository(database)

    async def request_report(self, user_id: str, payload: ReportCreate) -> GeneratedReportModel:
        report = GeneratedReportModel(user_id=user_id, status=ReportStatus.PENDING, **payload.model_dump())
        return await self._reports.create(report)

    async def list_reports(
        self, user_id: str, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[GeneratedReportModel], int]:
        skip = (page - 1) * page_size
        return await self._reports.list_for_user(user_id, skip=skip, limit=page_size)

    async def get_report(self, user_id: str, report_id: str) -> GeneratedReportModel:
        report = await self._reports.get_by_id_for_user(report_id, user_id)
        if report is None:
            raise DocumentNotFoundError("generated_reports", report_id)
        return report

    async def delete_report(self, user_id: str, report_id: str) -> None:
        await self.get_report(user_id, report_id)
        await self._reports.soft_delete(report_id)
