from app.core.security import hash_password, hash_token, verify_password


def test_hash_password_is_not_plaintext_and_verifies():
    hashed = hash_password("correct horse battery staple")

    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_hash_password_is_salted_differently_each_time():
    first = hash_password("same password")
    second = hash_password("same password")

    assert first != second


def test_hash_token_is_deterministic():
    assert hash_token("raw-refresh-token") == hash_token("raw-refresh-token")
    assert hash_token("raw-refresh-token") != "raw-refresh-token"
