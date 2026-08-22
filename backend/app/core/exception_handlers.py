from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    DocumentNotFoundError,
    DuplicateDocumentError,
    UnauthorizedAccessError,
    ValidationFailedError,
)
from app.core.logging import get_logger, request_id_var
from app.schemas.error import ErrorDetail, ErrorResponse

logger = get_logger("app.errors")


def _error_response(status_code: int, code: str, message: str, details: Any = None) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, request_id=request_id_var.get(), details=details)
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Every error response, regardless of source (our own domain exceptions, FastAPI's
    request validation, an arbitrary HTTPException, the rate limiter, or an unhandled
    bug), comes back in the same `{"error": {code, message, request_id, details}}` shape."""

    @app.exception_handler(DocumentNotFoundError)
    async def handle_not_found(request: Request, exc: DocumentNotFoundError) -> JSONResponse:
        return _error_response(status.HTTP_404_NOT_FOUND, "not_found", str(exc))

    @app.exception_handler(DuplicateDocumentError)
    async def handle_duplicate(request: Request, exc: DuplicateDocumentError) -> JSONResponse:
        return _error_response(status.HTTP_409_CONFLICT, "conflict", str(exc))

    @app.exception_handler(UnauthorizedAccessError)
    async def handle_unauthorized(request: Request, exc: UnauthorizedAccessError) -> JSONResponse:
        return _error_response(status.HTTP_401_UNAUTHORIZED, "unauthorized", str(exc))

    @app.exception_handler(ValidationFailedError)
    async def handle_validation_failed(request: Request, exc: ValidationFailedError) -> JSONResponse:
        return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", str(exc))

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic's error list can embed the raw exception object (e.g. in `ctx.error`
        # for a failed @model_validator), which plain json.dumps can't serialize —
        # jsonable_encoder is what FastAPI's own default handler uses to sanitize it.
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "validation_error",
            "Request validation failed",
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _error_response(
            status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited", "Too many requests. Please try again later."
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _error_response(exc.status_code, "http_error", str(exc.detail))

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error", "An unexpected error occurred"
        )
