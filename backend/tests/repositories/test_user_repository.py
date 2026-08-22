from app.models.user import UserModel
from app.repositories.user_repository import UserRepository


def _make_user(email: str = "jane@example.com") -> UserModel:
    return UserModel(email=email, hashed_password="hashed", full_name="Jane Doe")


async def test_create_and_get_user(database):
    repo = UserRepository(database)

    created = await repo.create(_make_user())
    fetched = await repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.email == "jane@example.com"
    assert fetched.created_at is not None
    assert fetched.updated_at is not None


async def test_email_is_lowercased(database):
    repo = UserRepository(database)

    created = await repo.create(_make_user(email="Jane@Example.COM"))

    assert created.email == "jane@example.com"


async def test_email_exists_checks_case_insensitively(database):
    repo = UserRepository(database)
    await repo.create(_make_user())

    assert await repo.email_exists("jane@example.com") is True
    assert await repo.email_exists("JANE@EXAMPLE.COM") is True
    assert await repo.email_exists("someoneelse@example.com") is False


async def test_get_by_email_excludes_soft_deleted(database):
    repo = UserRepository(database)
    created = await repo.create(_make_user())

    await repo.soft_delete(created.id)

    assert await repo.get_by_email("jane@example.com") is None
    assert await repo.get_by_id(created.id) is None
    assert await repo.get_by_id(created.id, include_deleted=True) is not None
