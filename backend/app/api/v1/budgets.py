from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.models.budget import BudgetModel
from app.models.user import UserModel
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from app.services.budget_service import BudgetService

router = APIRouter()


def _to_response(budget: BudgetModel) -> BudgetResponse:
    return BudgetResponse(**budget.model_dump())


@router.get("/", response_model=list[BudgetResponse], summary="List budgets")
async def list_budgets(
    current_user: UserModel = Depends(get_current_user), database: AsyncIOMotorDatabase = Depends(get_db)
) -> list[BudgetResponse]:
    service = BudgetService(database)
    budgets = await service.list_budgets(current_user.id)
    return [_to_response(b) for b in budgets]


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED, summary="Create a budget")
async def create_budget(
    payload: BudgetCreate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> BudgetResponse:
    service = BudgetService(database)
    budget = await service.create_budget(current_user.id, payload)
    return _to_response(budget)


@router.put("/{budget_id}", response_model=BudgetResponse, summary="Update a budget")
async def update_budget(
    budget_id: str,
    payload: BudgetUpdate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> BudgetResponse:
    service = BudgetService(database)
    budget = await service.update_budget(current_user.id, budget_id, payload)
    return _to_response(budget)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a budget")
async def delete_budget(
    budget_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    service = BudgetService(database)
    await service.delete_budget(current_user.id, budget_id)
