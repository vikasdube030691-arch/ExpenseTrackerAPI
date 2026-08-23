"""Shared helpers for every tool module in this package.

Every tool factory in `app/tools/*.py` follows the same shape:

    def build_xxx_tools(database: AsyncIOMotorDatabase, user_id: str) -> list[BaseTool]:
        ...

`user_id` is supplied by `ChatService` from the authenticated request's JWT —
never by the LLM. It is closed over when the tool is built and does not
appear anywhere in a tool's `args_schema`, so there is no argument an AI
response could set to read or modify another user's data. This is the
concrete mechanism behind the "LLM never directly queries MongoDB, all data
access goes through controlled tools that enforce the authenticated user
context" rule: a tool is a plain async function wrapping one of the existing
`app/services/*.py` classes (which already scope every query by `user_id`
at the repository layer), never a raw database handle.
"""

from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import DocumentNotFoundError, DuplicateDocumentError
from pydantic import ValidationError


def parse_date(value: str | None, *, default: datetime | None = None) -> datetime | None:
    """Parses an ISO-8601 date/datetime string (e.g. "2026-08-01" or
    "2026-08-01T00:00:00Z") as supplied by the LLM. Returns `default` (often
    `None`, meaning "no filter") when `value` is falsy; raises `ValueError`
    with a message safe to hand back to the model on anything unparsable."""
    if not value:
        return default
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"'{value}' is not a valid ISO-8601 date, e.g. '2026-08-01'") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def current_month_range(now: datetime | None = None) -> tuple[datetime, datetime]:
    reference = now or datetime.now(timezone.utc)
    start = reference.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start, reference


def to_json(value: Any) -> Any:
    """Recursively converts Pydantic models / lists of models returned by a
    service into plain JSON-safe data before it becomes tool output text."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_json(item) for item in value]
    if isinstance(value, dict):
        return {key: to_json(item) for key, item in value.items()}
    return value


def as_tool_error(exc: Exception) -> dict[str, str]:
    """Converts an expected failure (not found, duplicate, bad input) into a
    plain result the LLM can read and react to, instead of letting the
    exception blow up the tool-calling loop for one bad argument."""
    if isinstance(exc, DocumentNotFoundError):
        return {"error": f"No {exc.collection.rstrip('s')} found with id '{exc.identifier}'."}
    if isinstance(exc, DuplicateDocumentError):
        return {"error": str(exc)}
    if isinstance(exc, (ValueError, ValidationError)):
        return {"error": str(exc)}
    raise exc
