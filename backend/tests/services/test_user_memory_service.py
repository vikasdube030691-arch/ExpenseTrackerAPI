from app.core.exceptions import DocumentNotFoundError
from app.services.user_memory_service import UserMemoryService

USER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439099"


async def test_remember_and_recall(database):
    service = UserMemoryService(database)
    await service.remember(USER_ID, "Prefers budgets tracked in EUR")

    memories = await service.recall(USER_ID)

    assert len(memories) == 1
    assert memories[0].content == "Prefers budgets tracked in EUR"


async def test_recall_with_query_filters_by_keyword(database):
    service = UserMemoryService(database)
    await service.remember(USER_ID, "Rent is paid on the 1st")
    await service.remember(USER_ID, "Prefers budgets tracked in EUR")

    results = await service.recall(USER_ID, query="rent")

    assert len(results) == 1
    assert "Rent" in results[0].content


async def test_memories_are_isolated_between_users(database):
    service = UserMemoryService(database)
    await service.remember(USER_ID, "Only visible to user")

    other_memories = await service.recall(OTHER_USER_ID)

    assert other_memories == []


async def test_update_memory(database):
    service = UserMemoryService(database)
    created = await service.remember(USER_ID, "Old content")

    updated = await service.update_memory(USER_ID, created.id, "New content")

    assert updated.content == "New content"


async def test_update_memory_from_another_user_raises_not_found(database):
    service = UserMemoryService(database)
    created = await service.remember(USER_ID, "Belongs to user A")

    try:
        await service.update_memory(OTHER_USER_ID, created.id, "Hijacked")
        assert False, "expected DocumentNotFoundError"
    except DocumentNotFoundError:
        pass


async def test_forget_deletes_the_memory(database):
    service = UserMemoryService(database)
    created = await service.remember(USER_ID, "Temporary")

    deleted = await service.forget(USER_ID, created.id)
    remaining = await service.recall(USER_ID)

    assert deleted is True
    assert remaining == []


async def test_forget_from_another_user_does_not_delete(database):
    service = UserMemoryService(database)
    created = await service.remember(USER_ID, "Belongs to user A")

    deleted = await service.forget(OTHER_USER_ID, created.id)
    remaining = await service.recall(USER_ID)

    assert deleted is False
    assert len(remaining) == 1
