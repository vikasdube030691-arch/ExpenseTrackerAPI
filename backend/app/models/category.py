from pydantic import Field

from app.models.common import MongoDocument, PyObjectId, SoftDeleteMixin
from app.models.enums import CategoryType


class CategoryModel(MongoDocument, SoftDeleteMixin):
    user_id: PyObjectId | None = None
    """None for built-in system categories shared across all users."""
    name: str = Field(min_length=1, max_length=100)
    type: CategoryType
    icon: str | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_system: bool = False
