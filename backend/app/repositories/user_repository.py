from app.db.collections import Collections
from app.models.user import UserModel
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    collection_name = Collections.USERS
    model = UserModel

    async def get_by_email(self, email: str) -> UserModel | None:
        return await self.find_one({"email": email.lower(), "is_deleted": False})

    async def email_exists(self, email: str) -> bool:
        count = await self.count({"email": email.lower()})
        return count > 0
