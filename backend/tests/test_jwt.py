from datetime import timedelta

import pytest

from app.core.jwt import ExpiredTokenError, InvalidTokenError, create_access_token, decode_access_token


def test_create_and_decode_round_trip():
    token = create_access_token(subject="507f1f77bcf86cd799439011")

    payload = decode_access_token(token)

    assert payload.sub == "507f1f77bcf86cd799439011"
    assert payload.type == "access"
    assert payload.exp > payload.iat


def test_expired_token_is_rejected():
    token = create_access_token(subject="507f1f77bcf86cd799439011", expires_delta=timedelta(seconds=-1))

    with pytest.raises(ExpiredTokenError):
        decode_access_token(token)


def test_tampered_token_is_rejected():
    token = create_access_token(subject="507f1f77bcf86cd799439011")

    with pytest.raises(InvalidTokenError):
        decode_access_token(token + "tampered")


def test_garbage_token_is_rejected():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-jwt-at-all")
