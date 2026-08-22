from datetime import datetime, timezone

from app.repositories.account_repository import AccountRepository
from app.schemas.account import AccountCreate
from app.schemas.category import CategoryCreate
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.account_service import AccountService
from app.services.category_service import CategoryService
from app.services.transaction_service import TransactionService

USER_ID = "507f1f77bcf86cd799439011"


async def _setup(database):
    account = await AccountService(database).create_account(
        USER_ID, AccountCreate(name="Checking", currency="USD", balance=0.0)
    )
    category = await CategoryService(database).create_category(
        USER_ID, CategoryCreate(name="Groceries", type="expense")
    )
    return account, category


async def test_create_transaction_debits_the_account(database):
    account, category = await _setup(database)
    service = TransactionService(database)

    await service.create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
        ),
    )

    refreshed = await AccountRepository(database).get_by_id_for_user(account.id, USER_ID)
    assert refreshed.balance == -50.0


async def test_updating_amount_reconciles_the_balance(database):
    account, category = await _setup(database)
    service = TransactionService(database)
    created = await service.create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
        ),
    )

    await service.update_transaction(USER_ID, created.id, TransactionUpdate(amount=80.0))

    refreshed = await AccountRepository(database).get_by_id_for_user(account.id, USER_ID)
    assert refreshed.balance == -80.0


async def test_updating_transaction_type_flips_the_balance_sign(database):
    account, category = await _setup(database)
    income_category = await CategoryService(database).create_category(
        USER_ID, CategoryCreate(name="Refund", type="income")
    )
    service = TransactionService(database)
    created = await service.create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
        ),
    )

    await service.update_transaction(
        USER_ID, created.id, TransactionUpdate(transaction_type="income", category_id=income_category.id)
    )

    refreshed = await AccountRepository(database).get_by_id_for_user(account.id, USER_ID)
    assert refreshed.balance == 50.0


async def test_moving_transaction_to_another_account_moves_the_balance_effect(database):
    account, category = await _setup(database)
    other_account = await AccountService(database).create_account(
        USER_ID, AccountCreate(name="Savings", currency="USD", balance=0.0)
    )
    service = TransactionService(database)
    created = await service.create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
        ),
    )

    await service.update_transaction(USER_ID, created.id, TransactionUpdate(account_id=other_account.id))

    repo = AccountRepository(database)
    original = await repo.get_by_id_for_user(account.id, USER_ID)
    moved_to = await repo.get_by_id_for_user(other_account.id, USER_ID)
    assert original.balance == 0.0
    assert moved_to.balance == -50.0


async def test_deleting_transaction_reverts_the_balance(database):
    account, category = await _setup(database)
    service = TransactionService(database)
    created = await service.create_transaction(
        USER_ID,
        TransactionCreate(
            account_id=account.id,
            transaction_type="expense",
            amount=50.0,
            currency="USD",
            category_id=category.id,
            transaction_date=datetime.now(timezone.utc),
        ),
    )

    await service.delete_transaction(USER_ID, created.id)

    refreshed = await AccountRepository(database).get_by_id_for_user(account.id, USER_ID)
    assert refreshed.balance == 0.0
