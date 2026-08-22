from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.recurring_transaction import RecurringTransactionModel
from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.recurring_transaction_repository import RecurringTransactionRepository
from app.schemas.recurring_transaction import RecurringTransactionCreate, RecurringTransactionUpdate


class RecurringTransactionService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._recurring = RecurringTransactionRepository(database)
        self._accounts = AccountRepository(database)
        self._categories = CategoryRepository(database)

    async def create_recurring_transaction(
        self, user_id: str, payload: RecurringTransactionCreate
    ) -> RecurringTransactionModel:
        if await self._accounts.get_by_id_for_user(payload.account_id, user_id) is None:
            raise DocumentNotFoundError("accounts", payload.account_id)
        if await self._categories.get_by_id_for_user(payload.category_id, user_id) is None:
            raise DocumentNotFoundError("categories", payload.category_id)
        recurring = RecurringTransactionModel(
            user_id=user_id, next_run_date=payload.start_date, **payload.model_dump()
        )
        return await self._recurring.create(recurring)

    async def list_recurring_transactions(
        self, user_id: str, *, active_only: bool = True
    ) -> list[RecurringTransactionModel]:
        return await self._recurring.list_for_user(user_id, active_only=active_only)

    async def get_recurring_transaction(self, user_id: str, recurring_id: str) -> RecurringTransactionModel:
        recurring = await self._recurring.get_by_id_for_user(recurring_id, user_id)
        if recurring is None:
            raise DocumentNotFoundError("recurring_transactions", recurring_id)
        return recurring

    async def update_recurring_transaction(
        self, user_id: str, recurring_id: str, payload: RecurringTransactionUpdate
    ) -> RecurringTransactionModel:
        await self.get_recurring_transaction(user_id, recurring_id)
        updated = await self._recurring.update_by_id(recurring_id, payload.model_dump(exclude_unset=True))
        if updated is None:
            raise DocumentNotFoundError("recurring_transactions", recurring_id)
        return updated

    async def delete_recurring_transaction(self, user_id: str, recurring_id: str) -> None:
        await self.get_recurring_transaction(user_id, recurring_id)
        await self._recurring.soft_delete(recurring_id)
