from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field


def _validate_object_id(value: Any) -> str:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, str) and ObjectId.is_valid(value):
        return value
    raise ValueError(f"'{value}' is not a valid ObjectId")


PyObjectId = Annotated[str, BeforeValidator(_validate_object_id)]


def _ensure_utc(value: datetime) -> datetime:
    # MongoDB drivers (and mongomock) commonly round-trip datetimes as naive UTC
    # regardless of how they were written; normalize on read so every datetime this
    # app touches is tz-aware and safely comparable to datetime.now(timezone.utc).
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


UTCDatetime = Annotated[datetime, AfterValidator(_ensure_utc)]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_currency(value: str) -> str:
    return value.upper()


class MongoBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)


class SoftDeleteMixin(BaseModel):
    is_deleted: bool = False
    deleted_at: UTCDatetime | None = None


class CreatedAtDocument(MongoBaseModel):
    """Base for append-only documents that are never updated (e.g. chat messages, audit logs)."""

    id: PyObjectId = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    created_at: UTCDatetime = Field(default_factory=utcnow)


class MongoDocument(CreatedAtDocument):
    """Base for mutable documents; adds updated_at on top of CreatedAtDocument."""

    updated_at: UTCDatetime = Field(default_factory=utcnow)
