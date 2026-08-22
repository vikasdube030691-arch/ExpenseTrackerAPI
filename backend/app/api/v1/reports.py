from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db, pagination_params
from app.models.report import GeneratedReportModel
from app.models.user import UserModel
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()


def _to_response(report: GeneratedReportModel) -> ReportResponse:
    return ReportResponse(**report.model_dump())


@router.post("/generate", response_model=ReportResponse, status_code=status.HTTP_201_CREATED, summary="Generate a report")
async def generate_report(
    payload: ReportCreate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> ReportResponse:
    """Runs synchronously and returns the completed report — there's no background
    worker in this version, so the request blocks for the duration of the aggregation."""
    service = ReportService(database)
    report = await service.generate_report(current_user.id, payload)
    return _to_response(report)


@router.get("/", response_model=PaginatedResponse[ReportResponse], summary="List generated reports")
async def list_reports(
    pagination: PaginationParams = Depends(pagination_params),
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> PaginatedResponse[ReportResponse]:
    service = ReportService(database)
    items, total = await service.list_reports(current_user.id, page=pagination.page, page_size=pagination.page_size)
    return PaginatedResponse(
        items=[_to_response(r) for r in items], total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/{report_id}", response_model=ReportResponse, summary="Get a generated report")
async def get_report(
    report_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> ReportResponse:
    service = ReportService(database)
    report = await service.get_report(current_user.id, report_id)
    return _to_response(report)
