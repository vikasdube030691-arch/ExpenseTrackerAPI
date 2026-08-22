from app.models.account import AccountModel
from app.repositories.account_repository import AccountRepository

OWNER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439012"


async def test_create_normalizes_currency_and_lists_for_user(database):
    repo = AccountRepository(database)

    created = await repo.create(AccountModel(user_id=OWNER_ID, name="Checking", currency="usd", balance=100.0))
    accounts = await repo.list_for_user(OWNER_ID)

    assert created.currency == "USD"
    assert len(accounts) == 1
    assert accounts[0].id == created.id


async def test_get_by_id_for_user_enforces_isolation(database):
    repo = AccountRepository(database)
    created = await repo.create(AccountModel(user_id=OWNER_ID, name="Savings", currency="USD"))

    assert await repo.get_by_id_for_user(created.id, OWNER_ID) is not None
    assert await repo.get_by_id_for_user(created.id, OTHER_USER_ID) is None


async def test_adjust_balance(database):
    repo = AccountRepository(database)
    created = await repo.create(AccountModel(user_id=OWNER_ID, name="Wallet", currency="USD", balance=50.0))

    updated = await repo.adjust_balance(created.id, -20.0)

    assert updated is not None
    assert updated.balance == 30.0


async def test_list_for_user_excludes_inactive_by_default(database):
    repo = AccountRepository(database)
    await repo.create(AccountModel(user_id=OWNER_ID, name="Active", currency="USD", is_active=True))
    await repo.create(AccountModel(user_id=OWNER_ID, name="Inactive", currency="USD", is_active=False))

    active_only = await repo.list_for_user(OWNER_ID)
    all_accounts = await repo.list_for_user(OWNER_ID, include_inactive=True)

    assert len(active_only) == 1
    assert len(all_accounts) == 2
