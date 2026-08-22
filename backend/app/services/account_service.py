from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import DocumentNotFoundError
from app.models.account import AccountModel
from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._accounts = AccountRepository(database)

    async def create_account(self, user_id: str, payload: AccountCreate) -> AccountModel:
        account = AccountModel(user_id=user_id, **payload.model_dump())
        return await self._accounts.create(account)

    async def list_accounts(self, user_id: str, *, include_inactive: bool = False) -> list[AccountModel]:
        return await self._accounts.list_for_user(user_id, include_inactive=include_inactive)

    async def get_account(self, user_id: str, account_id: str) -> AccountModel:
        account = await self._accounts.get_by_id_for_user(account_id, user_id)
        if account is None:
            raise DocumentNotFoundError("accounts", account_id)
        return account

    async def update_account(self, user_id: str, account_id: str, payload: AccountUpdate) -> AccountModel:
        await self.get_account(user_id, account_id)
        updated = await self._accounts.update_by_id(account_id, payload.model_dump(exclude_unset=True))
        if updated is None:
            raise DocumentNotFoundError("accounts", account_id)
        return updated

    async def delete_account(self, user_id: str, account_id: str) -> None:
        await self.get_account(user_id, account_id)
        await self._accounts.soft_delete(account_id)
