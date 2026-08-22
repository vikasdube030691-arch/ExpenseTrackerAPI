from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.audit_log import AuditLogModel
from app.models.enums import TransactionType
from app.models.transaction import TransactionModel
from app.repositories.account_repository import AccountRepository
from app.repositories.audit_repository import AuditLogRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionFilter, TransactionUpdate

# NOTE: account balance adjustments below are best-effort sequential writes, not wrapped
# in a MongoDB multi-document transaction. Multi-document ACID transactions require a
# replica set / mongos deployment; a standalone `mongod` (the default local dev setup)
# rejects `session.start_transaction()`. Deploy MongoDB as a (single-node) replica set
# and wrap these calls in a client session transaction before relying on this for
# strict atomicity in production.


class TransactionService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._transactions = TransactionRepository(database)
        self._accounts = AccountRepository(database)
        self._categories = CategoryRepository(database)
        self._audit_logs = AuditLogRepository(database)

    async def _assert_account_and_category(self, user_id: str, account_id: str, category_id: str) -> None:
        if await self._accounts.get_by_id_for_user(account_id, user_id) is None:
            raise DocumentNotFoundError("accounts", account_id)
        if await self._categories.get_by_id_for_user(category_id, user_id) is None:
            raise DocumentNotFoundError("categories", category_id)

    async def create_transaction(self, user_id: str, payload: TransactionCreate) -> TransactionModel:
        await self._assert_account_and_category(user_id, payload.account_id, payload.category_id)
        transaction = TransactionModel(user_id=user_id, **payload.model_dump())
        created = await self._transactions.create(transaction)

        signed_amount = created.amount if created.transaction_type == TransactionType.INCOME else -created.amount
        await self._accounts.adjust_balance(created.account_id, signed_amount)

        await self._audit_logs.create(
            AuditLogModel(
                user_id=user_id,
                action="transaction.create",
                resource_type="transaction",
                resource_id=created.id,
                metadata={"amount": created.amount, "transaction_type": created.transaction_type.value},
            )
        )
        return created

    async def get_transaction(self, user_id: str, transaction_id: str) -> TransactionModel:
        transaction = await self._transactions.get_by_id_for_user(transaction_id, user_id)
        if transaction is None:
            raise DocumentNotFoundError("transactions", transaction_id)
        return transaction

    async def list_transactions(
        self, user_id: str, filters: TransactionFilter, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[TransactionModel], int]:
        skip = (page - 1) * page_size
        return await self._transactions.search(
            user_id, skip=skip, limit=page_size, **filters.model_dump(exclude_none=True)
        )

    async def update_transaction(
        self, user_id: str, transaction_id: str, payload: TransactionUpdate
    ) -> TransactionModel:
        existing = await self.get_transaction(user_id, transaction_id)
        update_fields = payload.model_dump(exclude_unset=True)
        if "account_id" in update_fields or "category_id" in update_fields:
            await self._assert_account_and_category(
                user_id,
                update_fields.get("account_id", existing.account_id),
                update_fields.get("category_id", existing.category_id),
            )
        updated = await self._transactions.update_by_id(transaction_id, update_fields)
        if updated is None:
            raise DocumentNotFoundError("transactions", transaction_id)
        return updated

    async def delete_transaction(self, user_id: str, transaction_id: str) -> None:
        transaction = await self.get_transaction(user_id, transaction_id)
        await self._transactions.soft_delete(transaction_id)

        reversal = transaction.amount if transaction.transaction_type == TransactionType.EXPENSE else -transaction.amount
        await self._accounts.adjust_balance(transaction.account_id, reversal)

        await self._audit_logs.create(
            AuditLogModel(
                user_id=user_id,
                action="transaction.delete",
                resource_type="transaction",
                resource_id=transaction.id,
            )
        )

    async def spending_by_category(self, user_id: str, start_date, end_date) -> list[dict]:
        return await self._transactions.sum_by_category(user_id, start_date, end_date)

    async def total_by_type(self, user_id: str, transaction_type: str, start_date, end_date) -> float:
        return await self._transactions.sum_by_type(user_id, transaction_type, start_date, end_date)
