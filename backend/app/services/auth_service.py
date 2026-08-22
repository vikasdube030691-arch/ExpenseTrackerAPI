import secrets
from datetime import timedelta

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.exceptions import UnauthorizedAccessError
from app.core.security import hash_token
from app.models.common import utcnow
from app.models.refresh_token import RefreshTokenModel
from app.repositories.refresh_token_repository import RefreshTokenRepository

# NOTE: This service persists opaque refresh tokens (the `refresh_tokens` collection).
# Access-token issuance (JWT signing) is an application/auth-layer concern that sits on
# top of this DB layer and is intentionally out of scope here.


class AuthService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._refresh_tokens = RefreshTokenRepository(database)

    async def issue_refresh_token(
        self, user_id: str, *, user_agent: str | None = None, ip_address: str | None = None
    ) -> str:
        raw_token = secrets.token_urlsafe(48)
        token = RefreshTokenModel(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
        )
        await self._refresh_tokens.create(token)
        return raw_token

    async def rotate_refresh_token(
        self, raw_token: str, *, user_agent: str | None = None, ip_address: str | None = None
    ) -> tuple[str, str]:
        existing = await self._refresh_tokens.get_by_token_hash(hash_token(raw_token))
        if existing is None or existing.expires_at < utcnow():
            raise UnauthorizedAccessError("Refresh token is invalid or expired")
        await self._refresh_tokens.revoke(existing.id)
        new_token = await self.issue_refresh_token(existing.user_id, user_agent=user_agent, ip_address=ip_address)
        return existing.user_id, new_token

    async def revoke_all_sessions(self, user_id: str) -> int:
        return await self._refresh_tokens.revoke_all_for_user(user_id)
