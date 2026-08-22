from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.models.category import CategoryModel
from app.models.enums import CategoryType
from app.models.user import UserModel
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import CategoryService

router = APIRouter()


def _to_response(category: CategoryModel) -> CategoryResponse:
    return CategoryResponse(**category.model_dump())


@router.get("/", response_model=list[CategoryResponse], summary="List categories")
async def list_categories(
    category_type: CategoryType | None = Query(default=None, alias="type"),
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> list[CategoryResponse]:
    """Returns the user's own categories plus shared system categories (`is_system: true`)."""
    service = CategoryService(database)
    categories = await service.list_categories(
        current_user.id, category_type=category_type.value if category_type else None
    )
    return [_to_response(c) for c in categories]


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED, summary="Create a category")
async def create_category(
    payload: CategoryCreate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> CategoryResponse:
    service = CategoryService(database)
    category = await service.create_category(current_user.id, payload)
    return _to_response(category)


@router.put("/{category_id}", response_model=CategoryResponse, summary="Update a category")
async def update_category(
    category_id: str,
    payload: CategoryUpdate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> CategoryResponse:
    """System categories can't be modified — attempting to returns 404, the same as
    a category that doesn't exist or belongs to another user."""
    service = CategoryService(database)
    category = await service.update_category(current_user.id, category_id, payload)
    return _to_response(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a category")
async def delete_category(
    category_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    service = CategoryService(database)
    await service.delete_category(current_user.id, category_id)
