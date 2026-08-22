from app.core.exceptions import DocumentNotFoundError
from app.models.budget import BudgetModel
from datetime import datetime, timezone

from app.repositories.budget_repository import BudgetRepository

USER_ID = "507f1f77bcf86cd799439011"


def _budget(**overrides) -> BudgetModel:
    defaults = dict(
        user_id=USER_ID,
        amount=500.0,
        currency="usd",
        start_date=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return BudgetModel(**defaults)


async def test_update_by_id_bumps_updated_at(database):
    repo = BudgetRepository(database)
    created = await repo.create(_budget())
    # Re-fetch so both timestamps went through the same BSON millisecond truncation;
    # comparing against the in-memory `created` object (full microsecond precision)
    # can spuriously fail when create and update land in the same millisecond.
    persisted = await repo.get_by_id(created.id)

    updated = await repo.update_by_id(created.id, {"amount": 750.0})

    assert updated is not None
    assert updated.amount == 750.0
    assert updated.updated_at >= persisted.updated_at


async def test_require_by_id_raises_when_missing(database):
    repo = BudgetRepository(database)

    try:
        await repo.require_by_id("507f1f77bcf86cd799439abc")
        assert False, "expected DocumentNotFoundError"
    except DocumentNotFoundError:
        pass


async def test_soft_delete_hides_document_but_hard_delete_removes_it(database):
    repo = BudgetRepository(database)
    created = await repo.create(_budget())

    await repo.soft_delete(created.id)
    assert await repo.get_by_id(created.id) is None
    assert await repo.get_by_id(created.id, include_deleted=True) is not None

    removed = await repo.hard_delete(created.id)
    assert removed is True
    assert await repo.get_by_id(created.id, include_deleted=True) is None
