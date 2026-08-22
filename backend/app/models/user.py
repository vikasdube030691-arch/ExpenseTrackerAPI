from pydantic import EmailStr, Field, field_validator

from app.models.common import MongoDocument, SoftDeleteMixin
from app.models.enums import UserRole


class UserModel(MongoDocument, SoftDeleteMixin):
    email: EmailStr
    hashed_password: str
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False

    @field_validator("email")
    @classmethod
    def _lowercase_email(cls, value: str) -> str:
        return value.lower()
