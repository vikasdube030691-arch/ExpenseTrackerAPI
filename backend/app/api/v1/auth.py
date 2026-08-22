from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import DuplicateDocumentError, UnauthorizedAccessError
from app.core.rate_limit import limiter
from app.models.user import UserModel
from app.schemas.auth import AccessTokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.services.authentication_service import AuthenticationService

router = APIRouter()

# The refresh token is a bearer credential for obtaining new access tokens, so it is
# never put in a JSON response body or read into JS: it lives only in an HttpOnly
# cookie scoped to this router's own path, invisible to (and unstealable by) frontend
# JavaScript even in the presence of an XSS bug.
_REFRESH_COOKIE_NAME = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE_NAME, path=_REFRESH_COOKIE_PATH)


def _user_response(user: UserModel) -> UserResponse:
    return UserResponse(**user.model_dump())


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, database: AsyncIOMotorDatabase = Depends(get_db)) -> UserResponse:
    service = AuthenticationService(database)
    try:
        user = await service.register(payload)
    except DuplicateDocumentError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")
    return _user_response(user)


@router.post("/login", response_model=AccessTokenResponse)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request,
    response: Response,
    payload: UserLogin,
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> AccessTokenResponse:
    service = AuthenticationService(database)
    try:
        _, access_token, refresh_token = await service.login(
            payload.email,
            payload.password,
            user_agent=request.headers.get("user-agent"),
            ip_address=_client_ip(request),
        )
    except UnauthorizedAccessError:
        # Deliberately identical whether the email doesn't exist or the password is
        # wrong, so the response never leaks which email addresses are registered.
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    _set_refresh_cookie(response, refresh_token)
    return AccessTokenResponse(access_token=access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request, response: Response, database: AsyncIOMotorDatabase = Depends(get_db)
) -> AccessTokenResponse:
    raw_token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if raw_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    service = AuthenticationService(database)
    try:
        access_token, new_refresh_token = await service.refresh(
            raw_token, user_agent=request.headers.get("user-agent"), ip_address=_client_ip(request)
        )
    except UnauthorizedAccessError:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired, please log in again")

    _set_refresh_cookie(response, new_refresh_token)
    return AccessTokenResponse(access_token=access_token, expires_in=settings.access_token_expire_minutes * 60)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response, database: AsyncIOMotorDatabase = Depends(get_db)) -> None:
    raw_token = request.cookies.get(_REFRESH_COOKIE_NAME)
    if raw_token:
        await AuthenticationService(database).logout(raw_token)
    _clear_refresh_cookie(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    response: Response,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    await AuthenticationService(database).logout_all(current_user.id)
    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserModel = Depends(get_current_user)) -> UserResponse:
    return _user_response(current_user)
