from pydantic import BaseModel, Field

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin, UTCDatetime
from app.models.enums import ReportFormat, ReportStatus, ReportType


class ReportFile(BaseModel):
    url: str
    filename: str
    size_bytes: int | None = Field(default=None, ge=0)


class GeneratedReportModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId
    report_type: ReportType
    format: ReportFormat = ReportFormat.PDF
    status: ReportStatus = ReportStatus.PENDING
    period_start: UTCDatetime
    period_end: UTCDatetime
    file: ReportFile | None = None
    error_message: str | None = None
