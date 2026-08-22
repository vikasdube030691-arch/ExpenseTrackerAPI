from datetime import datetime, timedelta, timezone

from app.models.transaction import TransactionModel
from app.repositories.transaction_repository import TransactionRepository

USER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439099"
ACCOUNT_ID = "507f1f77bcf86cd799439012"
CATEGORY_ID = "507f1f77bcf86cd799439013"


def _txn(**overrides) -> TransactionModel:
    defaults = dict(
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        transaction_type="expense",
        amount=25.0,
        currency="usd",
        category_id=CATEGORY_ID,
        transaction_date=datetime.now(timezone.utc),
        tags=["Food "],
    )
    defaults.update(overrides)
    return TransactionModel(**defaults)


async def test_currency_and_tags_are_normalized(database):
    repo = TransactionRepository(database)

    created = await repo.create(_txn())

    assert created.currency == "USD"
    assert created.tags == ["food"]


async def test_search_enforces_user_isolation(database):
    repo = TransactionRepository(database)
    await repo.create(_txn())
    await repo.create(_txn(user_id=OTHER_USER_ID))

    items, total = await repo.search(USER_ID)

    assert total == 1
    assert all(item.user_id == USER_ID for item in items)


async def test_search_filters_by_type_and_amount_range(database):
    repo = TransactionRepository(database)
    await repo.create(_txn(transaction_type="income", amount=1000.0))
    await repo.create(_txn(transaction_type="expense", amount=25.0))

    items, total = await repo.search(USER_ID, transaction_type="expense", min_amount=10, max_amount=50)

    assert total == 1
    assert items[0].transaction_type == "expense"


async def test_soft_deleted_transactions_are_excluded_from_search(database):
    repo = TransactionRepository(database)
    created = await repo.create(_txn())

    await repo.soft_delete(created.id)
    items, total = await repo.search(USER_ID)

    assert total == 0
    assert items == []


async def test_sum_by_type(database):
    repo = TransactionRepository(database)
    now = datetime.now(timezone.utc)
    await repo.create(_txn(amount=25.0, transaction_date=now))
    await repo.create(_txn(amount=75.0, transaction_date=now))

    total = await repo.sum_by_type(USER_ID, "expense", now - timedelta(days=1), now + timedelta(days=1))

    assert total == 100.0


async def test_sum_by_category_groups_and_sorts_descending(database):
    repo = TransactionRepository(database)
    now = datetime.now(timezone.utc)
    other_category_id = "507f1f77bcf86cd799439099"
    await repo.create(_txn(amount=20.0, category_id=CATEGORY_ID, transaction_date=now))
    await repo.create(_txn(amount=90.0, category_id=other_category_id, transaction_date=now))

    breakdown = await repo.sum_by_category(USER_ID, now - timedelta(days=1), now + timedelta(days=1))

    assert breakdown[0]["total"] == 90.0
    assert breakdown[1]["total"] == 20.0
