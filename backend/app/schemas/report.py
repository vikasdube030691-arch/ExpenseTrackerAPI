from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

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

    @model_validator(mode="after")
    def _validate_period(self) -> "ReportCreate":
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        return self


class ReportResponse(BaseModel):
    id: str
    user_id: str
    report_type: ReportType
    format: ReportFormat
    status: ReportStatus
    period_start: datetime
    period_end: datetime
    file: ReportFileSchema | None
    data: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
