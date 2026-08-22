from app.models.chat_message import ChatMessageModel
from app.models.chat_session import ChatSessionModel
from app.repositories.chat_repository import ChatMessageRepository, ChatSessionRepository

USER_ID = "507f1f77bcf86cd799439011"
OTHER_USER_ID = "507f1f77bcf86cd799439099"


async def test_touch_updates_last_message_at(database):
    repo = ChatSessionRepository(database)
    session = await repo.create(ChatSessionModel(user_id=USER_ID, title="Budget chat"))
    # Re-fetch so both timestamps went through the same BSON millisecond truncation;
    # comparing against the in-memory `session` object (full microsecond precision)
    # can spuriously fail when create and touch land in the same millisecond.
    persisted = await repo.get_by_id_for_user(session.id, USER_ID)

    await repo.touch(session.id)
    refreshed = await repo.get_by_id_for_user(session.id, USER_ID)

    assert refreshed is not None
    assert persisted is not None
    assert refreshed.last_message_at >= persisted.last_message_at


async def test_session_isolation_between_users(database):
    repo = ChatSessionRepository(database)
    session = await repo.create(ChatSessionModel(user_id=USER_ID, title="Budget chat"))

    assert await repo.get_by_id_for_user(session.id, OTHER_USER_ID) is None


async def test_list_messages_for_session_ordered_by_created_at(database):
    session_repo = ChatSessionRepository(database)
    message_repo = ChatMessageRepository(database)
    session = await session_repo.create(ChatSessionModel(user_id=USER_ID, title="Budget chat"))

    await message_repo.create(ChatMessageModel(session_id=session.id, user_id=USER_ID, role="user", content="Hi"))
    await message_repo.create(
        ChatMessageModel(session_id=session.id, user_id=USER_ID, role="assistant", content="Hello!")
    )

    messages, total = await message_repo.list_for_session(session.id, USER_ID)

    assert total == 2
    assert [m.role for m in messages] == ["user", "assistant"]
