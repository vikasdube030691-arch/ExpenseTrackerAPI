from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import UnauthorizedAccessError
from app.core.jwt import create_access_token
from app.models.common import utcnow
from app.models.user import UserModel
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService
from app.services.user_service import UserService


class AuthenticationService:
    """Orchestrates registration/login/logout/refresh by composing UserService
    (identity + password verification) with AuthService (refresh-token/session
    persistence) and app.core.jwt (stateless access tokens). This is the only
    service route handlers under /api/v1/auth should call."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._users = UserService(database)
        self._sessions = AuthService(database)

    async def register(self, payload: UserCreate) -> UserModel:
        return await self._users.register(payload)

    async def login(
        self, email: str, password: str, *, user_agent: str | None = None, ip_address: str | None = None
    ) -> tuple[UserModel, str, str]:
        user = await self._users.authenticate(email, password)
        access_token = create_access_token(subject=user.id)
        refresh_token = await self._sessions.issue_refresh_token(
            user.id, user_agent=user_agent, ip_address=ip_address
        )
        return user, access_token, refresh_token

    async def refresh(
        self, raw_refresh_token: str, *, user_agent: str | None = None, ip_address: str | None = None
    ) -> tuple[str, str]:
        user_id, new_refresh_token = await self._sessions.rotate_refresh_token(
            raw_refresh_token, user_agent=user_agent, ip_address=ip_address
        )
        user = await self._users.get_by_id(user_id)
        if not user.is_active:
            raise UnauthorizedAccessError("Account is disabled")
        access_token = create_access_token(subject=user.id)
        return access_token, new_refresh_token

    async def logout(self, raw_refresh_token: str) -> None:
        session = await self._sessions.get_session_by_raw_token(raw_refresh_token)
        if session is not None:
            await self._sessions.revoke_session(session.id)

    async def logout_all(self, user_id: str) -> int:
        return await self._sessions.revoke_all_sessions(user_id)
