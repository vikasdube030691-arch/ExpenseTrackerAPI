from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DuplicateDocumentError, UnauthorizedAccessError
from app.core.security import hash_password, verify_password
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._users = UserRepository(database)

    async def register(self, payload: UserCreate) -> UserModel:
        if await self._users.email_exists(payload.email):
            raise DuplicateDocumentError("users", f"email '{payload.email}' is already registered")
        user = UserModel(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        return await self._users.create(user)

    async def authenticate(self, email: str, password: str) -> UserModel:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedAccessError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedAccessError("Account is disabled")
        return user

    async def get_by_id(self, user_id: str) -> UserModel:
        return await self._users.require_by_id(user_id)
