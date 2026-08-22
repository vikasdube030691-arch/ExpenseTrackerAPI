import pytest

from app.core.exceptions import DuplicateDocumentError, UnauthorizedAccessError
from app.core.jwt import decode_access_token
from app.schemas.user import UserCreate
from app.services.authentication_service import AuthenticationService


def _registration(email: str = "jane@example.com", password: str = "correct-horse-battery") -> UserCreate:
    return UserCreate(email=email, password=password, full_name="Jane Doe")


async def test_register_creates_user_with_hashed_password(database):
    service = AuthenticationService(database)

    user = await service.register(_registration())

    assert user.email == "jane@example.com"
    assert user.hashed_password != "correct-horse-battery"


async def test_register_rejects_duplicate_email(database):
    service = AuthenticationService(database)
    await service.register(_registration())

    with pytest.raises(DuplicateDocumentError):
        await service.register(_registration())


async def test_login_returns_valid_access_and_refresh_tokens(database):
    service = AuthenticationService(database)
    await service.register(_registration())

    user, access_token, refresh_token = await service.login("jane@example.com", "correct-horse-battery")

    assert user.email == "jane@example.com"
    assert decode_access_token(access_token).sub == user.id
    assert isinstance(refresh_token, str) and len(refresh_token) > 20


async def test_login_with_wrong_password_raises_generic_error(database):
    service = AuthenticationService(database)
    await service.register(_registration())

    with pytest.raises(UnauthorizedAccessError):
        await service.login("jane@example.com", "wrong-password")


async def test_login_with_unknown_email_raises_same_generic_error(database):
    service = AuthenticationService(database)

    with pytest.raises(UnauthorizedAccessError):
        await service.login("nobody@example.com", "whatever")


async def test_refresh_rotates_token_and_invalidates_the_old_one(database):
    service = AuthenticationService(database)
    await service.register(_registration())
    _, _, refresh_token = await service.login("jane@example.com", "correct-horse-battery")

    new_access_token, new_refresh_token = await service.refresh(refresh_token)

    assert new_refresh_token != refresh_token
    assert decode_access_token(new_access_token).sub is not None

    with pytest.raises(UnauthorizedAccessError):
        await service.refresh(refresh_token)


async def test_logout_revokes_the_session_so_refresh_fails_afterwards(database):
    service = AuthenticationService(database)
    await service.register(_registration())
    _, _, refresh_token = await service.login("jane@example.com", "correct-horse-battery")

    await service.logout(refresh_token)

    with pytest.raises(UnauthorizedAccessError):
        await service.refresh(refresh_token)


async def test_logout_all_revokes_every_session_for_the_user(database):
    service = AuthenticationService(database)
    user = await service.register(_registration())
    _, _, refresh_token_1 = await service.login("jane@example.com", "correct-horse-battery")
    _, _, refresh_token_2 = await service.login("jane@example.com", "correct-horse-battery")

    revoked_count = await service.logout_all(user.id)

    assert revoked_count == 2
    with pytest.raises(UnauthorizedAccessError):
        await service.refresh(refresh_token_1)
    with pytest.raises(UnauthorizedAccessError):
        await service.refresh(refresh_token_2)
