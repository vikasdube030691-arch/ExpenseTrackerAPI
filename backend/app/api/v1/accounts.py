from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db
from app.models.account import AccountModel
from app.models.user import UserModel
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import AccountService

# Not one of the originally-listed "Required Modules" — added anyway because
# Transactions requires an owned account_id and there is otherwise no way to
# obtain one through the API. Mirrors the categories/budgets router shape.
router = APIRouter()


def _to_response(account: AccountModel) -> AccountResponse:
    return AccountResponse(**account.model_dump())


@router.get("/", response_model=list[AccountResponse], summary="List accounts")
async def list_accounts(
    include_inactive: bool = False,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> list[AccountResponse]:
    service = AccountService(database)
    accounts = await service.list_accounts(current_user.id, include_inactive=include_inactive)
    return [_to_response(a) for a in accounts]


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED, summary="Create an account")
async def create_account(
    payload: AccountCreate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountResponse:
    service = AccountService(database)
    account = await service.create_account(current_user.id, payload)
    return _to_response(account)


@router.put("/{account_id}", response_model=AccountResponse, summary="Update an account")
async def update_account(
    account_id: str,
    payload: AccountUpdate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> AccountResponse:
    service = AccountService(database)
    account = await service.update_account(current_user.id, account_id, payload)
    return _to_response(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an account")
async def delete_account(
    account_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    service = AccountService(database)
    await service.delete_account(current_user.id, account_id)
