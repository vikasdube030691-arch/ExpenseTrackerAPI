"""Tools for the Report Agent: generate and retrieve monthly/category
reports and period comparisons, backed by `ReportService`.
"""

from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.enums import ReportFormat, ReportType
from app.schemas.report import ReportCreate
from app.services.report_service import ReportService
from app.tools._helpers import as_tool_error, parse_date, to_json


def build_report_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
    reports = ReportService(database)

    @tool
    async def generate_report(
        report_type: Annotated[str, "'monthly_summary', 'category_breakdown', 'tax_summary', or 'custom'"],
        period_start: Annotated[str, "ISO date"],
        period_end: Annotated[str, "ISO date"],
    ) -> Any:
        """Generates a report for a period and returns its computed data
        immediately (report generation is synchronous)."""
        try:
            start, end = parse_date(period_start), parse_date(period_end)
            if not (start and end):
                return {"error": "period_start and period_end are required"}
            payload = ReportCreate(report_type=ReportType(report_type), format=ReportFormat.JSON, period_start=start, period_end=end)
            return to_json(await reports.generate_report(user_id, payload))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def list_reports(page: int = 1, page_size: Annotated[int, "max 20"] = 10) -> Any:
        """Lists previously generated reports, most recent first."""
        try:
            items, total = await reports.list_reports(user_id, page=page, page_size=min(page_size, 20))
            return {"items": to_json(items), "total": total}
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    @tool
    async def get_report(report_id: str) -> Any:
        """Fetches one previously generated report by id."""
        try:
            return to_json(await reports.get_report(user_id, report_id))
        except Exception as exc:  # noqa: BLE001
            return as_tool_error(exc)

    return [generate_report, list_reports, get_report]
