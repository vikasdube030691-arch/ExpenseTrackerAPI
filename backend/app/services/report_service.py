from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.enums import ReportStatus, ReportType, TransactionType
from app.models.report import GeneratedReportModel
from app.repositories.report_repository import ReportRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.report import ReportCreate

# No PDF/CSV writer or object storage exists yet, so `file` stays unset — the
# computed numbers are returned directly in `data`, which every report_type
# populates regardless of the requested `format`. Swap in a real writer here
# (and set `file`) without touching the router or the report schema.


class ReportService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._reports = ReportRepository(database)
        self._transactions = TransactionRepository(database)

    async def _compute(self, user_id: str, payload: ReportCreate) -> dict:
        if payload.report_type == ReportType.CATEGORY_BREAKDOWN:
            breakdown = await self._transactions.sum_by_category(user_id, payload.period_start, payload.period_end)
            return {"category_breakdown": breakdown}

        income = await self._transactions.sum_by_type(
            user_id, TransactionType.INCOME.value, payload.period_start, payload.period_end
        )
        expense = await self._transactions.sum_by_type(
            user_id, TransactionType.EXPENSE.value, payload.period_start, payload.period_end
        )
        return {"total_income": income, "total_expense": expense, "net": income - expense}

    async def generate_report(self, user_id: str, payload: ReportCreate) -> GeneratedReportModel:
        report = GeneratedReportModel(user_id=user_id, status=ReportStatus.PROCESSING, **payload.model_dump())
        created = await self._reports.create(report)

        try:
            data = await self._compute(user_id, payload)
        except Exception:
            failed = await self._reports.update_by_id(
                created.id, {"status": ReportStatus.FAILED, "error_message": "Report generation failed"}
            )
            return failed if failed is not None else created

        completed = await self._reports.update_by_id(created.id, {"status": ReportStatus.COMPLETED, "data": data})
        return completed if completed is not None else created

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
