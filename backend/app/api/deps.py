from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.core.jwt import ExpiredTokenError, InvalidTokenError, decode_access_token
from app.db.mongodb import get_database
from app.models.user import UserModel
from app.schemas.common import PaginationParams
from app.services.authentication_service import AuthenticationService
from app.services.user_service import UserService

_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_db() -> AsyncIOMotorDatabase:
    return get_database()


def get_authentication_service(database: AsyncIOMotorDatabase = Depends(get_db)) -> AuthenticationService:
    return AuthenticationService(database)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> UserModel:
    if credentials is None:
        raise _CREDENTIALS_ERROR

    try:
        payload = decode_access_token(credentials.credentials)
    except (ExpiredTokenError, InvalidTokenError):
        raise _CREDENTIALS_ERROR

    try:
        user = await UserService(database).get_by_id(payload.sub)
    except DocumentNotFoundError:
        raise _CREDENTIALS_ERROR

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")

    return user


def pagination_params(
    page: int = Query(default=1, ge=1, description="1-indexed page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page (max 100)"),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def make_sort_dependency(allowed_fields: set[str], default: str):
    """Builds a FastAPI dependency that parses a `sort=-field,other_field` query
    param into a MongoDB sort spec. `allowed_fields` is a whitelist — sorting by an
    arbitrary/unindexed field isn't just a correctness footgun, it's also how an
    attacker could force an expensive collection scan, so unknown fields are rejected
    with a 422 rather than silently ignored."""

    default_field = default.lstrip("-")
    default_direction = -1 if default.startswith("-") else 1

    def _dependency(
        sort: str = Query(
            default=default,
            description=f"Comma-separated fields, prefix '-' for descending. Allowed: {', '.join(sorted(allowed_fields))}",
        ),
    ) -> list[tuple[str, int]]:
        sort_spec: list[tuple[str, int]] = []
        for raw_field in sort.split(","):
            raw_field = raw_field.strip()
            if not raw_field:
                continue
            direction = -1 if raw_field.startswith("-") else 1
            field = raw_field.lstrip("-")
            if field not in allowed_fields:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Cannot sort by '{field}'. Allowed fields: {', '.join(sorted(allowed_fields))}",
                )
            sort_spec.append((field, direction))
        return sort_spec or [(default_field, default_direction)]

    return _dependency
