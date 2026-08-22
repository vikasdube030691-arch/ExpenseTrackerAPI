from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ReportFormat, ReportStatus, ReportType


class ReportFileSchema(BaseModel):
    url: str
    filename: str
    size_bytes: int | None = Field(default=None, ge=0)


class ReportCreate(BaseModel):
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    period_start: datetime
    period_end: datetime


class ReportResponse(BaseModel):
    id: str
    user_id: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    period_start: datetime
    period_end: datetime
    file: ReportFileSchema | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
