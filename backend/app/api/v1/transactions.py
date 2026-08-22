from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_current_user, get_db, make_sort_dependency, pagination_params
from app.models.enums import TransactionType
from app.models.transaction import TransactionModel
from app.models.user import UserModel
from app.schemas.common import PaginatedResponse, PaginationParams
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionResponse, TransactionUpdate
from app.services.transaction_service import TransactionService

router = APIRouter()

_SORT_FIELDS = {"transaction_date", "amount", "created_at"}
_sort_dependency = make_sort_dependency(_SORT_FIELDS, default="-transaction_date")


def _to_response(transaction: TransactionModel) -> TransactionResponse:
    return TransactionResponse(**transaction.model_dump())


@router.get("/", response_model=PaginatedResponse[TransactionResponse], summary="List transactions")
async def list_transactions(
    transaction_type: TransactionType | None = None,
    account_id: str | None = None,
    category_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    min_amount: float | None = Query(default=None, ge=0),
    max_amount: float | None = None,
    tags: list[str] | None = Query(default=None),
    search: str | None = Query(default=None, description="Matches against merchant or description"),
    sort: list[tuple[str, int]] = Depends(_sort_dependency),
    pagination: PaginationParams = Depends(pagination_params),
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> PaginatedResponse[TransactionResponse]:
    """Supports pagination, sorting, and filtering by type, account, category, date
    range, amount range, tags, and free-text search over merchant/description."""
    filters = TransactionFilter(
        transaction_type=transaction_type,
        account_id=account_id,
        category_id=category_id,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        tags=tags,
        search=search,
    )
    service = TransactionService(database)
    items, total = await service.list_transactions(
        current_user.id, filters, page=pagination.page, page_size=pagination.page_size, sort=sort
    )
    return PaginatedResponse(
        items=[_to_response(t) for t in items], total=total, page=pagination.page, page_size=pagination.page_size
    )


@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get a transaction")
async def get_transaction(
    transaction_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> TransactionResponse:
    service = TransactionService(database)
    transaction = await service.get_transaction(current_user.id, transaction_id)
    return _to_response(transaction)


@router.post(
    "/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Create a transaction"
)
async def create_transaction(
    payload: TransactionCreate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> TransactionResponse:
    service = TransactionService(database)
    transaction = await service.create_transaction(current_user.id, payload)
    return _to_response(transaction)


@router.put("/{transaction_id}", response_model=TransactionResponse, summary="Update a transaction")
async def update_transaction(
    transaction_id: str,
    payload: TransactionUpdate,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> TransactionResponse:
    """All fields are optional — only the fields present in the request body are
    changed. Changing `account_id`/`category_id` re-validates ownership of the new
    references the same way creation does."""
    service = TransactionService(database)
    transaction = await service.update_transaction(current_user.id, transaction_id, payload)
    return _to_response(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a transaction")
async def delete_transaction(
    transaction_id: str,
    current_user: UserModel = Depends(get_current_user),
    database: AsyncIOMotorDatabase = Depends(get_db),
) -> None:
    """Soft-deletes the transaction and reverses its effect on the account balance."""
    service = TransactionService(database)
    await service.delete_transaction(current_user.id, transaction_id)
